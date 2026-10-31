import streamlit as st
import pandas as pd
import requests
from database import create_tables, save_symptoms, get_connection

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="Dengue AI Guardian",
    page_icon="🦟",
    layout="wide"
)

create_tables()

# ---------------- SIDEBAR ----------------
st.sidebar.title("🦟 Dengue AI Guardian")

page = st.sidebar.radio(
    "Select a Page",
    [
        "Dashboard",
        "Symptom Assessment",
        "Patient Records",
        "Live Weather",
        "Dengue Prevention",
        "Government Information",
        "About & Safety"
    ]
)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("🦟 Dengue AI Guardian")
    st.subheader("Dengue Awareness and Monitoring Dashboard")

    with get_connection() as conn:
        total_records = conn.execute(
            "SELECT COUNT(*) FROM patient_records"
        ).fetchone()[0]

    col1, col2 = st.columns(2)
    col1.metric("Total Patient Records", total_records)
    col2.metric("Monitoring Location", "Bengaluru")

    st.divider()
    st.subheader("Welcome!")
    st.write(
        "This application demonstrates symptom recording, "
        "patient history, live weather monitoring and dengue prevention."
    )

    st.info(
        "Use the sidebar to access the different features."
    )

# ---------------- SYMPTOM ASSESSMENT ----------------
elif page == "Symptom Assessment":
    st.title("🩺 Dengue Symptom Assessment")

    st.warning(
        "This is an educational symptom checklist. "
        "It is not an AI diagnosis or a clinically validated prediction."
    )

    with st.form("symptom_form"):
        fever = st.checkbox("Do you have fever?")
        body_pain = st.checkbox("Do you have body pain?")
        skin_rash = st.checkbox("Do you have skin rash?")

        submitted = st.form_submit_button("Submit Assessment")

    if submitted:
        record_id = save_symptoms(
            int(fever),
            int(body_pain),
            int(skin_rash)
        )

        score = int(fever) + int(body_pain) + int(skin_rash)

        st.success(f"Patient record saved. Record ID: {record_id}")
        st.metric("Symptoms Reported", f"{score} / 3")

        if fever:
            st.warning(
                "Fever can have many causes, including dengue. "
                "Please contact a healthcare professional."
            )
        else:
            st.info(
                "These answers cannot rule out dengue. "
                "Consult a healthcare professional if concerned."
            )

        st.error(
            "URGENT: Severe abdominal pain, persistent vomiting, "
            "bleeding, difficulty breathing, confusion, or cold/clammy "
            "skin require urgent medical evaluation. Do not wait for this app."
        )

# ---------------- PATIENT RECORDS ----------------
elif page == "Patient Records":
    st.title("📋 Patient Records")

    with get_connection() as conn:
        records = pd.read_sql_query(
            "SELECT * FROM patient_records ORDER BY id DESC",
            conn
        )

    if records.empty:
        st.info("No patient records available yet.")
    else:
        st.dataframe(records, use_container_width=True)

        csv = records.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Patient Records (CSV)",
            data=csv,
            file_name="dengue_patient_records.csv",
            mime="text/csv"
        )

# ---------------- LIVE WEATHER ----------------
elif page == "Live Weather":
    st.title("🌦️ Live Bengaluru Weather")

    st.write("Weather data provided by Open-Meteo.")

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

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Temperature",
                f'{current["temperature_2m"]} °C'
            )
            c2.metric(
                "Humidity",
                f'{current["relative_humidity_2m"]}%'
            )
            c3.metric(
                "Precipitation",
                f'{current["precipitation"]} mm'
            )

            st.caption(f'Weather time: {current["time"]}')

        except Exception as error:
            st.error(f"Weather API unavailable: {error}")

# ---------------- PREVENTION ----------------
elif page == "Dengue Prevention":
    st.title("🛡️ Dengue Prevention and Food Guidance")

    st.subheader("Prevent Mosquito Breeding")
    st.markdown("""
    - Remove stagnant water around your home.
    - Keep water storage containers covered.
    - Use mosquito nets and repellents.
    - Wear clothing that covers your arms and legs.
    """)

    st.divider()

    st.subheader("Food and Hydration")
    st.markdown("""
    - Drink adequate safe fluids.
    - Eat balanced meals that you can tolerate.
    - Include fruits and vegetables.
    - Follow your doctor's dietary advice.
    - Do not use food or home remedies as a substitute for medical care.
    """)

# ---------------- GOVERNMENT INFORMATION ----------------
elif page == "Government Information":
    st.title("🇮🇳 Official Dengue Information")

    st.write(
        "Refer to these official sources for verified health information."
    )

    st.markdown(
        "[NCVBDC – Government of India](https://ncvbdc.mohfw.gov.in/)"
    )
    st.markdown(
        "[Ministry of Health and Family Welfare](https://mohfw.gov.in/)"
    )
    st.markdown(
        "[WHO – Dengue Information](https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue)"
    )

    st.info(
        "These are official information links. "
        "This application does not currently fetch live government case figures."
    )

# ---------------- ABOUT AND SAFETY ----------------
elif page == "About & Safety":
    st.title("ℹ️ About Dengue AI Guardian")

    st.write("""
    Dengue AI Guardian is an educational project for demonstrating:

    - Symptom assessment and recording
    - Patient record history
    - Live Bengaluru weather
    - Dengue prevention information
    - Official health information links
    """)

    st.warning("""
    MEDICAL SAFETY NOTICE

    This application is not a medical device. It does not diagnose dengue
    or provide a clinically validated risk prediction.

    Always consult a qualified healthcare professional.
    Do not delay emergency medical care based on this application.
    """)

st.sidebar.divider()
st.sidebar.caption("Dengue AI Guardian | Educational Project")
