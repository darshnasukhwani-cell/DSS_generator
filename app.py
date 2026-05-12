import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from streamlit.components.v1 import html

# ================= UI =================
st.set_page_config(page_title="DSS Auto Generator", layout="wide")

# ================= GOOGLE PLAY CONSOLE UI =================
    border: none;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 15px;
}

.stButton > button:hover {
    background-color: #1765cc;
    color: white;
}

.stSelectbox label,
.stTextInput label,
.stFileUploader label {
    font-weight: 600;
    color: #202124;
}

.play-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #dadce0;
    margin-bottom: 20px;
    box-shadow: 0 1px 2px rgba(60,64,67,.15);
}

.data-chip {
    display: inline-block;
    background: #e8f0fe;
    color: #1967d2;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 13px;
    margin-top: 6px;
    margin-bottom: 6px;
    font-weight: 500;
}

.section-title {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 15px;
    color: #202124;
}

.subtype-box {
    border: 1px solid #dadce0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    background: #fff;
}

.optional-tag {
    color: #137333;
    font-weight: 600;
}

.required-tag {
    color: #b3261e;
    font-weight: 600;
}

.common-tag {
    color: #9334e6;
    font-weight: 600;
}

.small-text {
    color: #5f6368;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class='play-card'>
    <h1>Google Play Data Safety Section Generator</h1>
    <p class='small-text'>
        Generate Google Play Data Safety Section using
        Android Manifest + Statistical Inference.
    </p>
</div>
""", unsafe_allow_html=True)



st.markdown("<div class='play-card'>", unsafe_allow_html=True)

manifest_file = st.file_uploader(
    "Upload ",
    type=["xml"]
)

category = st.selectbox(
    "Select Application Category",
    ["Shopping", "Communication", "Dating", "Gaming"]
)

st.markdown("</div>", unsafe_allow_html=True)



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

PURPOSES = [
    "App functionality",
    "Analytics",
    "Developer communications",
    "Advertising or marketing",
    "Fraud prevention, security, and compliance",
    "Personalization",
    "Account management"
]

selected_purposes = st.multiselect(
    "Select Purpose(s)",
    PURPOSES
)



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

    
for sec in ["collected", "shared"]:

    section_title = "📥 Data Collected" if sec == "collected" else "🔄 Data Shared"

    st.markdown(
        f"<div class='section-title'>{section_title}</div>",
        unsafe_allow_html=True
    )

    for dtype, items in result.get(sec, {}).items():

        st.markdown(f"""
        <div class='play-card'>
            <h3>{dtype}</h3>
        """, unsafe_allow_html=True)

        for item in items:

            label = item['label']

            if label == "Optional":
                label_html = f"<span class='optional-tag'>Optional</span>"
            elif label == "Required":
                label_html = f"<span class='required-tag'>Required</span>"
            else:
                label_html = f"<span class='common-tag'>Common</span>"

            st.markdown(f"""
            <div class='subtype-box'>
                <h4>{item['subtype']}</h4>

                <div class='data-chip'>
                    {sec.title()} • {label}
                </div>

                <p class='small-text'>
                    Optional Rate: {item['optional_score']}%
                </p>
if selected_purposes:
    purpose_text = ", ".join(selected_purposes)

    st.markdown(f"""
    <p class='small-text'>
        <b>Purpose:</b> {purpose_text}
    </p>
    """, unsafe_allow_html=True)
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)




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
