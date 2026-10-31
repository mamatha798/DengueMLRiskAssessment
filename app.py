
import streamlit as st
import pandas as pd
import requests
import sqlite3
from pathlib import Path
from datetime import datetime

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from database import create_tables, save_symptoms, get_connection

# ---------------- CONFIGURATION ----------------
st.set_page_config(
    page_title="Dengue AI Guardian",
    page_icon="🦟",
    layout="wide"
)

create_tables()

st.title("🦟 Dengue AI Guardian")
st.caption("Integrated Dengue Awareness and Monitoring Platform")

# ---------------- NAVIGATION ----------------
pages = [
    "Dashboard",
    "Symptom Assessment",
    "CBC Blood Report",
    "Patient Records",
    "Live Weather",
    "Dengue Prevention",
    "Food Guidance",
    "Government Information",
    "Medical Safety",
    "About Project"
]

page = st.sidebar.radio("Navigation", pages)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.header("Welcome to Dengue AI Guardian")

    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM patient_records"
        ).fetchone()[0]

    c1, c2 = st.columns(2)
    c1.metric("Patient Records", total)
    c2.metric("Location", "Bengaluru")

    st.subheader("Project Features")
    st.markdown("""
    - Symptom assessment and recording
    - CBC report upload and value entry
    - Patient record history
    - Live weather information
    - Dengue prevention and food guidance
    - Official government health resources
    - Medical warning signs
    """)

    st.info("Choose a feature from the sidebar.")

# ---------------- SYMPTOM ASSESSMENT ----------------
elif page == "Symptom Assessment":
    st.header("🩺 Symptom Assessment")

    st.warning(
        "This is a symptom checklist, not a trained ML model "
        "or a dengue diagnosis."
    )

    with st.form("symptom_form"):
        fever = st.checkbox("Fever")
        pain = st.checkbox("Body pain")
        rash = st.checkbox("Skin rash")
        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        record_id = save_symptoms(
            int(fever), int(pain), int(rash)
        )

        score = int(fever) + int(pain) + int(rash)

        st.success(f"Record saved. ID: {record_id}")
        st.metric("Symptoms reported", f"{score} / 3")

        if fever:
            st.warning(
                "Fever can have many causes, including dengue. "
                "Please seek medical assessment."
            )
        else:
            st.info(
                "These answers cannot rule out dengue."
            )

        st.error(
            "Seek urgent medical care for severe abdominal pain, "
            "persistent vomiting, bleeding, breathing difficulty, "
            "confusion, or cold/clammy skin."
        )

# ---------------- CBC REPORT ----------------
elif page == "CBC Blood Report":
    st.header("🩸 CBC Blood Report")

    st.write(
        "Upload a CBC PDF or enter values manually. "
        "This page does not diagnose dengue."
    )

    uploaded = st.file_uploader(
        "Upload CBC report (PDF)",
        type=["pdf"]
    )

    if uploaded:
        if PdfReader is None:
            st.error("PDF support missing. Install pypdf.")
        else:
            try:
                reader = PdfReader(uploaded)
                extracted = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )
                st.text_area(
                    "Extracted PDF text",
                    extracted,
                    height=220
                )
                if not extracted.strip():
                    st.info(
                        "No selectable text found. "
                        "Scanned PDF OCR is not implemented."
                    )
            except Exception as error:
                st.error(f"Could not read PDF: {error}")

    st.subheader("Enter CBC Values Manually")

    with st.form("cbc_form"):
        platelet = st.number_input(
            "Platelet count (cells/µL)",
            min_value=0,
            max_value=2000000,
            value=150000
        )
        hemoglobin = st.number_input(
            "Hemoglobin (g/dL)",
            min_value=0.0,
            max_value=30.0,
            value=12.0
        )
        wbc = st.number_input(
            "WBC count (cells/µL)",
            min_value=0,
            max_value=100000,
            value=7000
        )
        cbc_submit = st.form_submit_button("Review Entered Values")

    if cbc_submit:
        st.write("### Entered CBC values")
        st.write(f"Platelets: {platelet:,} cells/µL")
        st.write(f"Hemoglobin: {hemoglobin} g/dL")
        st.write(f"WBC: {wbc:,} cells/µL")

        st.warning(
            "These values are displayed for reference only. "
            "Interpretation depends on the laboratory range, "
            "clinical condition and trends over time. "
            "Please consult a doctor."
        )

# ---------------- PATIENT RECORDS ----------------
elif page == "Patient Records":
    st.header("📋 Patient Record History")

    with get_connection() as conn:
        records = pd.read_sql_query(
            "SELECT * FROM patient_records ORDER BY id DESC",
            conn
        )

    if records.empty:
        st.info("No patient records available.")
    else:
        st.dataframe(records, use_container_width=True)

        st.download_button(
            "Download Records CSV",
            records.to_csv(index=False).encode("utf-8"),
            "dengue_patient_records.csv",
            "text/csv"
        )

# ---------------- WEATHER ----------------
elif page == "Live Weather":
    st.header("🌦️ Live Bengaluru Weather")

    if st.button("Fetch Latest Weather"):
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=12.9716&longitude=77.5946"
            "&current=temperature_2m,relative_humidity_2m,precipitation"
        )

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            current = response.json()["current"]

            a, b, c = st.columns(3)
            a.metric("Temperature", f'{current["temperature_2m"]} °C')
            b.metric("Humidity", f'{current["relative_humidity_2m"]}%')
            c.metric("Precipitation", f'{current["precipitation"]} mm')

            st.caption(f'Weather time: {current["time"]}')
            st.caption("Source: Open-Meteo")

        except Exception as error:
            st.error(f"Weather service unavailable: {error}")

# ---------------- PREVENTION ----------------
elif page == "Dengue Prevention":
    st.header("🛡️ Dengue Prevention")

    st.markdown("""
    1. Remove stagnant water around the home.
    2. Keep water storage containers covered.
    3. Use mosquito nets and repellents.
    4. Wear clothing that covers arms and legs.
    5. Keep surroundings clean.
    6. Seek medical advice if symptoms develop.
    """)

# ---------------- FOOD GUIDANCE ----------------
elif page == "Food Guidance":
    st.header("🥗 Food and Hydration Guidance")

    st.subheader("General supportive guidance")
    st.markdown("""
    - Drink safe fluids regularly.
    - Eat balanced meals that you can tolerate.
    - Include fruits and vegetables.
    - Follow your doctor's dietary advice.
    """)

    st.warning(
        "Food cannot cure dengue. Avoid self-medication "
        "and seek professional medical advice."
    )

# ---------------- GOVERNMENT INFORMATION ----------------
elif page == "Government Information":
    st.header("🇮🇳 Official Dengue Information")

    st.markdown(
        "[NCVBDC – Government of India]"
        "(https://ncvbdc.mohfw.gov.in/)"
    )
    st.markdown(
        "[Ministry of Health and Family Welfare]"
        "(https://mohfw.gov.in/)"
    )
    st.markdown(
        "[WHO – Dengue Information]"
        "(https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue)"
    )

    st.info(
        "These are official information links. "
        "Live government case figures are not automatically retrieved."
    )

# ---------------- MEDICAL SAFETY ----------------
elif page == "Medical Safety":
    st.header("🚨 Medical Warning Signs")

    st.error("""
    Get urgent medical evaluation if any of these occur:

    - Severe abdominal pain
    - Persistent vomiting
    - Bleeding from nose or gums
    - Blood in vomit or stool
    - Difficulty breathing
    - Confusion or unusual drowsiness
    - Cold or clammy skin

    Do not wait for an app result before seeking care.
    """)

# ---------------- ABOUT ----------------
elif page == "About Project":
    st.header("ℹ️ About Dengue AI Guardian")

    st.write("""
    Dengue AI Guardian is an educational project that combines
    symptom recording, CBC report support, patient history,
    live weather information and dengue prevention resources.
    """)

    st.warning("""
    This application does not currently contain a clinically
    validated ML prediction model, medical diagnosis system,
    or live hospital availability service.
    """)

st.sidebar.divider()
st.sidebar.caption("Dengue AI Guardian | Educational Project")
