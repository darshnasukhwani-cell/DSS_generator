import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ================= UI =================
st.set_page_config(page_title="DSS Auto Generator", layout="wide")

st.title("DSS Auto Generator")
st.write("Data-driven DSS using Manifest + Statistical + Inference")

manifest_file = st.file_uploader("Upload Manifest file", type=["xml"])
category = st.selectbox("App Category", ["Shopping", "Communication", "Dating", "Gaming"])

# ================= PURPOSE OPTIONS =================
PURPOSE_OPTIONS = [
    "App functionality",
    "Analytics",
    "Developer communications",
    "Advertising or marketing",
    "Fraud prevention, security, and compliance",
    "Personalization",
    "Account management"
]

# ================= SESSION STATE =================
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "result" not in st.session_state:
    st.session_state.result = None

# ================= CATEGORY FILES =================
CATEGORY_FILES = {
    "Shopping": "data/Shopping_analysis.xlsx",
    "Communication": "data/Communication_analysis.xlsx",
    "Dating": "data/Dating_analysis.xlsx",
    "Gaming": "data/Gaming_analysis.xlsx"
}

# ================= PERMISSION MAP =================
PERMISSION_MAP = {
    "android.permission.ACCESS_FINE_LOCATION": ("Location", "Precise location", "collected"),
    "android.permission.ACCESS_COARSE_LOCATION": ("Location", "Approximate location", "collected"),
    "android.permission.ACCESS_BACKGROUND_LOCATION": ("Location", "Background location", "collected"),

    "android.permission.CAMERA": ("Photos and videos", "Photos", "collected"),
    "android.permission.READ_MEDIA_IMAGES": ("Photos and videos", "Photos", "collected"),
    "android.permission.READ_MEDIA_VIDEO": ("Photos and videos", "Videos", "collected"),
    "android.permission.READ_MEDIA_AUDIO": ("Audio", "Audio files", "collected"),

    "android.permission.RECORD_AUDIO": ("Audio", "Voice recordings", "collected"),

    "android.permission.READ_EXTERNAL_STORAGE": ("Files and docs", "Files", "collected"),
    "android.permission.WRITE_EXTERNAL_STORAGE": ("Files and docs", "Files", "collected"),
    "android.permission.MANAGE_EXTERNAL_STORAGE": ("Files and docs", "Files", "collected"),

    "android.permission.READ_CONTACTS": ("Contacts", "Contacts", "collected"),
    "android.permission.WRITE_CONTACTS": ("Contacts", "Contacts", "collected"),
    "android.permission.GET_ACCOUNTS": ("Personal info", "Email address", "collected"),

    "android.permission.READ_CALENDAR": ("Calendar", "Calendar events", "collected"),
    "android.permission.WRITE_CALENDAR": ("Calendar", "Calendar events", "collected"),

    "android.permission.READ_PHONE_STATE": ("Device or other IDs", "Device ID", "shared"),
    "android.permission.READ_PHONE_NUMBERS": ("Personal info", "Phone number", "collected"),
    "android.permission.CALL_PHONE": ("App activity", "In-app actions", "collected"),

    "android.permission.READ_SMS": ("Messages", "SMS messages", "collected"),
    "android.permission.RECEIVE_SMS": ("Messages", "SMS messages", "collected"),
    "android.permission.SEND_SMS": ("Messages", "SMS messages", "collected"),

    "android.permission.BLUETOOTH": ("Nearby devices", "Bluetooth devices", "collected"),
    "android.permission.BLUETOOTH_CONNECT": ("Nearby devices", "Bluetooth devices", "collected"),
    "android.permission.BLUETOOTH_SCAN": ("Nearby devices", "Nearby device scanning", "collected"),

    "android.permission.BODY_SENSORS": ("Health and fitness", "Health data", "collected"),
    "android.permission.ACTIVITY_RECOGNITION": ("Health and fitness", "Physical activity", "collected"),

    "android.permission.POST_NOTIFICATIONS": ("App activity", "User notifications", "collected"),

    "android.permission.INTERNET": ("App activity", "App interactions", "shared"),
    "android.permission.ACCESS_NETWORK_STATE": ("App activity", "App interactions", "shared"),
}


# ================= LOAD STATS =================
def load_stats(file):
    df1 = pd.read_excel(file, sheet_name="Collected - Subtype")
    df2 = pd.read_excel(file, sheet_name="Shared - Subtype")

    collected_opt, shared_opt = {}, {}

    for _, row in df1.iterrows():
        collected_opt[(row["Data Type"], row["Subtype"])] = row["Optional %"]

    for _, row in df2.iterrows():
        shared_opt[(row["Data Type"], row["Subtype"])] = row["Optional %"]

    return collected_opt, shared_opt

# ================= PARSE MANIFEST =================
def parse_manifest(file):
    tree = ET.parse(file)
    root = tree.getroot()
    permissions = []

    for perm in root.findall(".//uses-permission"):
        name = perm.get("{http://schemas.android.com/apk/res/android}name")
        if name:
            permissions.append(name)

    return permissions

# ================= MAP =================
def map_permissions(permissions):
    data = {"collected": {}, "shared": {}}

    for perm in permissions:
        if perm in PERMISSION_MAP:
            dtype, sub, section = PERMISSION_MAP[perm]

            data.setdefault(section, {})
            data[section].setdefault(dtype, [])

            if sub not in data[section][dtype]:
                data[section][dtype].append(sub)

    return data

# ================= CLASSIFY =================
def classify(optional):
    if optional >= 75:
        return "Optional"
    elif optional <= 25:
        return "Required"
    return "Optional"

# ================= DECISION =================
def decision_engine(data, collected_opt, shared_opt):
    result = {"collected": {}, "shared": {}}

    for section in ["collected", "shared"]:
        opt_stats = collected_opt if section == "collected" else shared_opt

        for dtype, detected in data.get(section, {}).items():
            result[section][dtype] = []

            for sub in detected:
                optional = opt_stats.get((dtype, sub), 50)
                label = classify(optional)

                result[section][dtype].append({
                    "subtype": sub,
                    "label": label,
                    "optional_score": optional,
                    "purpose": []  # NEW FIELD
                })

    return result

# ================= PDF =================
def generate_pdf(result):
    doc = SimpleDocTemplate("DSS_Output.pdf")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("GOOGLE PLAY DATA SAFETY SECTION", styles["Title"]))
    elements.append(Spacer(1, 12))

    for sec in ["collected", "shared"]:
        title = "Data Collected" if sec == "collected" else "Data Shared"
        elements.append(Paragraph(title, styles["Heading2"]))

        for dtype, items in result.get(sec, {}).items():
            elements.append(Paragraph(dtype, styles["Heading3"]))

            for item in items:
                purpose = ", ".join(item.get("purpose", [])) or "Not specified"
                text = f"- {item['subtype']} ({item['label']})<br/>Purpose: {purpose}"
                elements.append(Paragraph(text, styles["Normal"]))

    doc.build(elements)
    return "DSS_Output.pdf"

# ================= GENERATE DSS =================
if st.button("Generate DSS"):

    if not manifest_file:
        st.error("Upload manifest file")
    else:
        file_path = CATEGORY_FILES.get(category)

        if not file_path or not os.path.exists(file_path):
            st.error("Dataset missing")
            st.stop()

        collected_opt, shared_opt = load_stats(file_path)

        permissions = parse_manifest(manifest_file)
        data = map_permissions(permissions)

        st.session_state.result = decision_engine(data, collected_opt, shared_opt)
        st.session_state.analysis_done = True

# ================= SHOW RESULTS + PURPOSE =================
if st.session_state.analysis_done and st.session_state.result:

    result = st.session_state.result
    st.success("DSS Generated")

    for sec in result:
        st.markdown(f"### {sec.upper()}")

        for dtype, items in result[sec].items():
            st.markdown(f"**{dtype}**")

            for i, item in enumerate(items):

                key = f"{sec}_{dtype}_{i}"

                purpose = st.multiselect(
                    f"Select purpose for {item['subtype']}",
                    PURPOSE_OPTIONS,
                    key=key
                )

                item["purpose"] = purpose

                st.markdown(
                    f"- **{item['subtype']}** "
                    f"({item['label']} - Optional rate: {item['optional_score']}%)"
                )

# ================= FINAL DSS =================
if st.session_state.analysis_done and st.session_state.result:

    st.subheader("📄 GOOGLE PLAY FORMAT")

    for sec in ["collected", "shared"]:
        title = "📥 Data Collected" if sec == "collected" else "🔄 Data Shared"
        st.markdown(f"### {title}")

        for dtype, items in st.session_state.result.get(sec, {}).items():
            st.markdown(f"**{dtype}**")

            for item in items:
                purpose = ", ".join(item.get("purpose", [])) or "Not specified"
                st.markdown(f"- {item['subtype']} ({item['label']})")
                st.caption(f"Purpose: {purpose}")

# ================= PDF DOWNLOAD =================
if st.session_state.result:
    pdf_file = generate_pdf(st.session_state.result)

    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📥 Download DSS as PDF",
            data=f,
            file_name="DSS_Output.pdf",
            mime="application/pdf"
        )
