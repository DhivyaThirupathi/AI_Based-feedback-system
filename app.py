import streamlit as st
import json
import os
from backend.feedback_service import process_feedback

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Feedback Portal", layout="centered")

# ==========================================
# 🌐 LANGUAGE SETTINGS (Tamil & English)
# ==========================================

# 1. Sidebar Language Switcher
lang_choice = st.sidebar.radio("Select Language / மொழியைத் தேர்ந்தெடுக்கவும்:", ("English", "தமிழ்"))

# 2. Translations Dictionary
TEXT = {
    "English": {
        "title": "📝 Feedback Portal",
        "loc_header": "📍 Location",
        "district_label": "District *",
        "const_label": "Assembly Constituency *",
        "personal_header": "👤 Personal Details",
        "name_label": "Name (optional)",
        "age_label": "Age",
        "booth_label": "Mobile Number *",
        "feedback_header": "🗂️ Feedback Details",
        "type_label": "Type of Feedback *",
        "type_options": ["General feedback", "State policy", "Services", "Complaint"],
        "email_label": "Email (optional)",
        "rating_label": "Rating (1–5)",
        "text_label": "Your Feedback *",
        "sol_label": "Suggested Solution (optional)",
        "need_update_label": "Do you want updates on this feedback?",
        "submit_btn": "Submit Feedback",
        "warn_dist": "⚠️ Please select District",
        "warn_const": "⚠️ Please select Assembly Constituency",
        "warn_booth": "⚠️ Please enter Mobile Number",
        "warn_text": "⚠️ Please enter your Feedback",
        "success": "✅ Feedback submitted successfully!",
        "process_msg": "Processing feedback..."
    },
    "தமிழ்": {
        "title": "📝 கருத்துக்கணிப்பு தளம்",
        "loc_header": "📍 இருப்பிடம்",
        "district_label": "மாவட்டம் *",
        "const_label": "சட்டமன்ற தொகுதி *",
        "personal_header": "👤 தனிப்பட்ட விவரங்கள்",
        "name_label": "பெயர் (விருப்பமிருந்தால்)",
        "age_label": "வயது",
        "booth_label": "மொபைல் எண் *",
        "feedback_header": "🗂️ கருத்து விவரங்கள்",
        "type_label": "கருத்து வகை *",
        "type_options": ["பொதுவான கருத்து", "மாநில கொள்கை", "சேவைகள்", "புகார்"],
        "email_label": "மின்னஞ்சல் (விருப்பமிருந்தால்)",
        "rating_label": "மதிப்பீடு (1–5)",
        "text_label": "உங்கள் கருத்து *",
        "sol_label": "பரிந்துரைக்கப்படும் தீர்வு (விருப்பமிருந்தால்)",
        "need_update_label": "இந்த கருத்தின் நிலை குறித்து புதுப்பிப்பு வேண்டுமா?",
        "submit_btn": "கருத்தைச் சமர்ப்பிக்கவும்",
        "warn_dist": "⚠️ தயவுசெய்து மாவட்டத்தைத் தேர்ந்தெடுக்கவும்",
        "warn_const": "⚠️ தயவுசெய்து தொகுதியைத் தேர்ந்தெடுக்கவும்",
        "warn_booth": "⚠️ தயவுசெய்து மொபைல் எண்ணை உள்ளிடவும்",
        "warn_text": "⚠️ தயவுசெய்து உங்கள் கருத்தை உள்ளிடவும்",
        "success": "✅ கருத்து வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது!",
        "process_msg": "கருத்து செயலாக்கப்படுகிறது..."
    }
}

t = TEXT[lang_choice]

# ---------------- MAIN UI STARTS ----------------
st.title(t["title"])

# ---------------- LOAD TN DATA ----------------
@st.cache_data
def load_tn_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "TN_Assembly_Constituencies_FULL.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

TN_DATA = load_tn_data()
districts = sorted(TN_DATA.keys())

# ---------------- LOCATION ----------------
st.subheader(t["loc_header"])

district = st.selectbox(t["district_label"], districts, index=None)

if district:
    constituency_list = [c["en"] for c in TN_DATA[district]["constituencies"]]
else:
    constituency_list = []

constituency = st.selectbox(t["const_label"], constituency_list, index=None)

# ---------------- FORM START ----------------
with st.form("feedback_form"):

    st.subheader(t["personal_header"])
    name = st.text_input(t["name_label"])
    age = st.number_input(t["age_label"], min_value=1, max_value=120, value=18)
    mobile_no = st.text_input(t["booth_label"])

    st.subheader(t["feedback_header"])
    selected_type_display = st.selectbox(t["type_label"], t["type_options"])

    email = st.text_input(t["email_label"])
    rating = st.slider(t["rating_label"], 1, 5, 3)
    feedback_text = st.text_area(t["text_label"], height=140)
    solution = st.text_area(t["sol_label"], height=100)

    # ✅ ONLY NEW OPTION (YOUR IDEA)
    need_update = st.radio(
        t["need_update_label"],
        ("No", "Yes"),
        horizontal=True
    )

    submitted = st.form_submit_button(t["submit_btn"])

# ---------------- SUBMIT HANDLER ----------------
if submitted:
    if not district:
        st.warning(t["warn_dist"])
    elif not constituency:
        st.warning(t["warn_const"])
    elif not mobile_no.strip():
        st.warning(t["warn_booth"])
    elif not feedback_text.strip():
        st.warning(t["warn_text"])
    else:
        with st.spinner(t["process_msg"]):

            final_feedback_type = selected_type_display
            if lang_choice == "தமிழ்":
                idx = t["type_options"].index(selected_type_display)
                final_feedback_type = TEXT["English"]["type_options"][idx]

            # ✅ ONLY NEW LOGIC
            need_update_flag = True if need_update == "Yes" else False

            process_feedback({
                "district": district,
                "constituency": constituency,
                "name": name,
                "age": age,
                "mobile_no": mobile_no,
                "email": email,
                "type_of_feedback": final_feedback_type,
                "rating": rating,
                "feedback_text": feedback_text,
                "solution": solution,
                "need_update": need_update_flag   # ✅ NEW
            })

        st.success(t["success"])
