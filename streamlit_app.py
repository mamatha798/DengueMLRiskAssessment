
import json
import sqlite3
import urllib.request            
from io import StringIO

from bs4 import BeautifulSoup
import streamlit as st

from database import create_tables, save_symptoms


# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="Dengue AI Guardian",
    page_icon="🦟",
    layout="wide"
)

create_tables()

st.title("🦟 Dengue AI Guardian")
st.caption("Dengue awareness and symptom support system")

st.warning(
    "This application is not a medical diagnosis tool. "
    "Please consult a qualified healthcare professional."
)


# ---------------- WEATHER API ----------------

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

        return data.get("current", {}), None

    except Exception as error:
        return None, str(error)


# ---------------- OFFICIAL GOVERNMENT DATA ----------------


def get_official_dengue_data():

    url = (
        "https://ncvbdc.mohfw.gov.in/index4.php"
        "?Background=Light&lang=1&level=0"
        "&lid=3715&linkid=431"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 DengueAIGuardian/1.0",
                "Accept": "text/html,application/xhtml+xml"
            }
        )

        with urllib.request.urlopen(request, timeout=25) as response:
            html = response.read().decode("utf-8", errors="replace")

        # Use Python's built-in HTML parser
        soup = BeautifulSoup(html, "html.parser")

        for table in soup.find_all("table"):
            rows = []

            for tr in table.find_all("tr"):
                cells = tr.find_all(["th", "td"])
                row = [
                    cell.get_text(" ", strip=True)
                    for cell in cells
                ]

                if row:
                    rows.append(row)

            if not rows:
                continue

            # Make rows the same length
            max_columns = max(len(row) for row in rows)
            rows = [
                row + [""] * (max_columns - len(row))
                for row in rows
            ]

            df = pd.DataFrame(rows)

            has_karnataka = df.apply(
                lambda column: column.astype(str).str.fullmatch(
                    r"Karnataka",
                    case=False,
                    na=False
                ).any()
            ).any()

            if has_karnataka:
                return df, url, None

        return (
            None,
            url,
            "Karnataka row was not found in the government HTML tables."
        )

    except Exception as error:
        return None, url, f"{type(error).__name__}: {error}"


# ---------------- WEATHER DASHBOARD ----------------

st.subheader("🌐 Live Bengaluru Weather")

weather, weather_error = get_bengaluru_weather()

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

    st.caption(
        f"Weather time: {weather.get('time', 'Unavailable')}"
    )

else:
    st.warning("Weather service is temporarily unavailable.")
    st.caption(f"Details: {weather_error}")

st.divider()


# ---------------- SYMPTOM ASSESSMENT ----------------

st.subheader("🩺 Symptom Assessment")

with st.form("symptom_form"):

    fever = st.radio(
        "Do you have fever?",
        ["No", "Yes"],
        horizontal=True
    )

    pain = st.radio(
        "Do you have body pain?",
        ["No", "Yes"],
        horizontal=True
    )

    rash = st.radio(
        "Do you have a skin rash?",
        ["No", "Yes"],
        horizontal=True
    )

    submitted = st.form_submit_button("Submit Assessment")


if submitted:

    fever_value = 1 if fever == "Yes" else 0
    pain_value = 1 if pain == "Yes" else 0
    rash_value = 1 if rash == "Yes" else 0

    try:
        record_id = save_symptoms(
            fever_value,
            pain_value,
            rash_value
        )

        score = fever_value + pain_value + rash_value

        st.subheader("Assessment Result")

        st.metric("Symptoms reported", f"{score} / 3")

        st.success(
            f"Your responses were saved. Record ID: {record_id}"
        )

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

    except Exception as error:
        st.error(f"Could not save patient record: {error}")

st.divider()


# ---------------- MEDICAL SAFETY ----------------

st.subheader("⚠️ Medical Safety Alert")

st.error(
    "Severe abdominal pain, persistent vomiting, bleeding, "
    "difficulty breathing, confusion, or cold/clammy skin "
    "need urgent medical evaluation. Do not wait for this app."
)

st.divider()


# ---------------- OFFICIAL DENGUE DATA ----------------

st.subheader("🇮🇳 Official Dengue Data")

with st.spinner("Fetching official government dengue data..."):

    government_data, source_url, data_error = (
        get_official_dengue_data()
    )

if government_data is not None:

    st.success("Government data retrieved successfully.")

    st.dataframe(
        government_data,
        use_container_width=True
    )

else:

    st.warning(
        "Official Karnataka dengue table could not be retrieved."
    )

    st.error(f"Fetch details: {data_error}")

    st.info(
        "The government website may be temporarily unavailable "
        "or may have changed its table format. No figures have "
        "been invented or substituted."
    )

st.markdown(f"[NCVBDC Government Source]({source_url})")

st.divider()


# ---------------- PATIENT RECORD HISTORY ----------------

st.subheader("📋 Patient Records History")

try:

    connection = sqlite3.connect("dengue_guardian.db")

    records = pd.read_sql_query(
        """
        SELECT
            id AS 'Record ID',
            record_date AS 'Date',
            CASE fever WHEN 1 THEN 'Yes' ELSE 'No' END AS 'Fever',
            CASE body_pain WHEN 1 THEN 'Yes' ELSE 'No' END AS 'Body Pain',
            CASE skin_rash WHEN 1 THEN 'Yes' ELSE 'No' END AS 'Skin Rash'
        FROM patient_records
        ORDER BY id DESC
        """,
        connection
    )

    connection.close()

    if not records.empty:

        st.dataframe(
            records,
            use_container_width=True
        )

        st.metric(
            "Total Patient Records",
            len(records)
        )

    else:
        st.info("No patient records available yet.")

except Exception as error:
    st.error(f"Could not load patient records: {error}")


# ---------------- FOOTER ----------------

st.caption(
    "This application currently counts reported symptoms. "
    "It does not use a trained machine-learning model and "
    "cannot diagnose dengue. Government data availability "
    "depends on the external source."
)
