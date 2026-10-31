
import json
import urllib.request
import pandas as pd
import streamlit as st

from database import create_tables, save_symptoms

# Initialize database
create_tables()

st.set_page_config(
    page_title="Dengue AI Guardian",
    page_icon="🦟",
    layout="wide"
)

st.title("🦟 Dengue AI Guardian")
st.caption("Dengue awareness and symptom support system")

st.warning(
    "This application is not a medical diagnosis tool. "
    "Please consult a qualified healthcare professional."
)

# ---------------- WEATHER ----------------

def get_bengaluru_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=12.9716&longitude=77.5946"
        "&current=temperature_2m,relative_humidity_2m,precipitation"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "DengueAIGuardian/1.0"}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data.get("current", {})

    except Exception:
        return None


# ---------------- GOVERNMENT DATA ----------------

def get_official_dengue_data():
    url = (
        "https://ncvbdc.mohfw.gov.in/index4.php"
        "?Background=Light&lang=1&level=0"
        "&lid=3715&linkid=431"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read()

        tables = pd.read_html(html, header=None)

        for df in tables:
            for _, row in df.iterrows():
                if row.astype(str).str.fullmatch(
                    "Karnataka", case=False, na=False
                ).any():
                    return df, url

        return None, url

    except Exception:
        return None, url


# ---------------- WEATHER DASHBOARD ----------------

st.subheader("🌐 Live Bengaluru Weather")

weather = get_bengaluru_weather()

if weather:
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Temperature",
        f"{weather.get('temperature_2m', 'N/A')} °C"
    )
    col2.metric(
        "Humidity",
        f"{weather.get('relative_humidity_2m', 'N/A')}%"
    )
    col3.metric(
        "Precipitation",
        f"{weather.get('precipitation', 'N/A')} mm"
    )

    st.caption(f"Weather time: {weather.get('time', 'Unavailable')}")
else:
    st.info("Weather service is temporarily unavailable.")

st.divider()

# ---------------- SYMPTOM ASSESSMENT ----------------

st.subheader("🩺 Symptom Assessment")

with st.form("symptom_form"):
    fever = st.radio("Do you have fever?", ["No", "Yes"])
    pain = st.radio("Do you have body pain?", ["No", "Yes"])
    rash = st.radio("Do you have a skin rash?", ["No", "Yes"])

    submitted = st.form_submit_button("Submit Assessment")

if submitted:
    fever_value = 1 if fever == "Yes" else 0
    pain_value = 1 if pain == "Yes" else 0
    rash_value = 1 if rash == "Yes" else 0

    record_id = save_symptoms(
        fever_value,
        pain_value,
        rash_value
    )

    score = fever_value + pain_value + rash_value

    st.subheader("Assessment Result")
    st.metric("Symptoms reported", f"{score} / 3")

    st.success(f"Your responses were saved. Record ID: {record_id}")

    if fever_value:
        st.warning(
            "Fever can have many causes, including dengue. "
            "Please contact a healthcare professional for assessment."
        )
    else:
        st.info(
            "These answers cannot rule out dengue. "
            "Consult a healthcare professional if concerned."
        )

st.divider()

# ---------------- MEDICAL SAFETY ----------------

st.subheader("⚠️ Medical Safety Alert")

st.error(
    "Severe abdominal pain, persistent vomiting, bleeding, "
    "difficulty breathing, confusion, or cold/clammy skin "
    "need urgent medical evaluation. Do not wait for this app."
)

st.divider()

# ---------------- OFFICIAL DATA ----------------

st.subheader("🇮🇳 Official Dengue Data")

government_data, source_url = get_official_dengue_data()

if government_data is not None:
    st.dataframe(government_data, use_container_width=True)
else:
    st.info(
        "Official Karnataka dengue table could not be retrieved. "
        "Please check the government source."
    )

st.markdown(f"[NCVBDC Government Source]({source_url})")

st.caption(
    "This application counts reported symptoms. "
    "It does not currently use a trained machine-learning model "
    "and cannot diagnose dengue."
)
