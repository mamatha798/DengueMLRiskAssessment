
import json
import sqlite3
import urllib.request
from html.parser import HTMLParser
from math import radians, sin, cos, sqrt, atan2

import pandas as pd
import requests
import folium
import streamlit as st
from streamlit_folium import st_folium

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


# ---------------- HTML TABLE PARSER ----------------

class TableParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = None
        self.current_row = None
        self.current_cell = None

    def handle_starttag(self, tag, attrs):

        if tag == "table":
            self.current_table = []

        elif tag == "tr" and self.current_table is not None:
            self.current_row = []

        elif tag in ("td", "th") and self.current_row is not None:
            self.current_cell = ""

    def handle_data(self, data):

        if self.current_cell is not None:
            self.current_cell += data

    def handle_endtag(self, tag):

        if tag in ("td", "th") and self.current_cell is not None:
            self.current_row.append(self.current_cell.strip())
            self.current_cell = None

        elif tag == "tr" and self.current_row is not None:
            if self.current_row:
                self.current_table.append(self.current_row)
            self.current_row = None

        elif tag == "table" and self.current_table is not None:
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = None


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

        with urllib.request.urlopen(request, timeout=15) as response:
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

        parser = TableParser()
        parser.feed(html)

        if not parser.tables:
            return None, url, "No HTML tables found on the government page."

        for table in parser.tables:

            max_columns = max(len(row) for row in table)

            rows = [
                row + [""] * (max_columns - len(row))
                for row in table
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

        return None, url, "Karnataka row was not found in government tables."

    except Exception as error:
        return None, url, f"{type(error).__name__}: {error}"


# ---------------- DISTANCE CALCULATION ----------------

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


# ---------------- LOCATION SEARCH ----------------

@st.cache_data(ttl=3600)
def get_location_coordinates(place):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "DengueAIGuardian/1.0 (hospital finder)"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=(10, 30)
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])


# ---------------- HOSPITAL DATA API ----------------

@st.cache_data(ttl=1800)
def get_nearby_hospitals(latitude, longitude, radius):

    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="hospital"](around:{radius},{latitude},{longitude});
      way["amenity"="hospital"](around:{radius},{latitude},{longitude});
      relation["amenity"="hospital"](around:{radius},{latitude},{longitude});
    );
    out center tags;
    """

    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]

    headers = {
        "User-Agent": "DengueAIGuardian/1.0 (hospital finder)",
        "Accept": "application/json"
    }

    errors = []

    for server in servers:

        for attempt in range(2):

            try:
                response = requests.post(
                    server,
                    data={"data": query},
                    headers=headers,
                    timeout=(15, 90)
                )

                response.raise_for_status()

                data = response.json()

                if "elements" not in data:
                    raise ValueError("Hospital data missing in API response.")

                return data.get("elements", [])

            except (requests.Timeout, requests.ConnectionError) as error:

                errors.append(
                    f"{server}, attempt {attempt + 1}: {error}"
                )

            except requests.RequestException as error:

                errors.append(f"{server}: {error}")
                break

            except ValueError as error:

                errors.append(f"{server}: {error}")
                break

    raise RuntimeError(
        "Hospital data servers are temporarily unavailable. "
        + " | ".join(errors[-3:])
    )


# ---------------- NEARBY HOSPITAL FINDER ----------------

def show_hospital_finder():

    st.subheader("🏥 Nearby Hospital Finder")

    st.write(
        "Search hospitals near your selected area "
        "and view their locations on an interactive map."
    )

    place = st.text_input(
        "Enter your area or location",
        value="Bengaluru, Karnataka, India",
        key="hospital_location"
    )

    radius_km = st.selectbox(
        "Search radius",
        [2, 5, 10, 15, 20],
        index=1,
        key="hospital_radius"
    )

    if st.button("🔍 Find Nearby Hospitals", key="find_hospitals"):

        if not place.strip():
            st.warning("Please enter a location.")
            return

        try:

            with st.spinner("Finding location..."):

                coordinates = get_location_coordinates(place)

            if coordinates is None:
                st.error(
                    "Location not found. "
                    "Try entering a nearby landmark or area name."
                )
                return

            user_lat, user_lon = coordinates

            st.success(
                f"Search location coordinates: "
                f"{user_lat:.5f}, {user_lon:.5f}"
            )

            with st.spinner(
                "Searching nearby hospitals. This may take a little time..."
            ):

                hospitals = get_nearby_hospitals(
                    user_lat,
                    user_lon,
                    radius_km * 1000
                )

            results = []

            for hospital in hospitals:

                tags = hospital.get("tags", {})

                hospital_lat = hospital.get(
                    "lat",
                    hospital.get("center", {}).get("lat")
                )

                hospital_lon = hospital.get(
                    "lon",
                    hospital.get("center", {}).get("lon")
                )

                if hospital_lat is None or hospital_lon is None:
                    continue

                hospital_lat = float(hospital_lat)
                hospital_lon = float(hospital_lon)

                distance = calculate_distance(
                    user_lat,
                    user_lon,
                    hospital_lat,
                    hospital_lon
                )

                name = tags.get("name", "Unnamed Hospital")

                address_parts = [
                    tags.get("addr:street"),
                    tags.get("addr:suburb"),
                    tags.get("addr:city")
                ]

                address = ", ".join(
                    part for part in address_parts if part
                )

                results.append({
                    "name": name,
                    "latitude": hospital_lat,
                    "longitude": hospital_lon,
                    "distance": distance,
                    "address": address,
                    "phone": tags.get(
                        "phone",
                        tags.get("contact:phone", "Not available")
                    )
                })

            results.sort(key=lambda item: item["distance"])

            if not results:
                st.warning(
                    "No hospitals were found in this radius. "
                    "Try increasing the search radius or another nearby area."
                )
                return

            st.success(f"Found {len(results)} hospital locations.")

            # Create interactive map

            hospital_map = folium.Map(
                location=[user_lat, user_lon],
                zoom_start=13
            )

            folium.Marker(
                [user_lat, user_lon],
                popup="Selected Search Location",
                tooltip="Search Location",
                icon=folium.Icon(
                    color="blue",
                    icon="home"
                )
            ).add_to(hospital_map)

            for hospital in results:

                folium.Marker(
                    [
                        hospital["latitude"],
                        hospital["longitude"]
                    ],
                    popup=(
                        f"{hospital['name']}<br>"
                        f"Distance: {hospital['distance']:.2f} km"
                    ),
                    tooltip=hospital["name"],
                    icon=folium.Icon(
                        color="red",
                        icon="plus-sign"
                    )
                ).add_to(hospital_map)

            st.subheader("🗺️ Hospital Location Map")

            st_folium(
                hospital_map,
                width=None,
                height=500,
                key="hospital_map"
            )

            # Hospital list

            st.subheader("📍 Hospital Suggestions")

            for index, hospital in enumerate(results, start=1):

                with st.container(border=True):

                    st.markdown(
                        f"**{index}. {hospital['name']}**"
                    )

                    st.write(
                        f"📏 Distance: {hospital['distance']:.2f} km"
                    )

                    if hospital["address"]:
                        st.write(f"📍 Address: {hospital['address']}")

                    st.write(f"☎️ Phone: {hospital['phone']}")

                    directions_url = (
                        "https://www.google.com/maps/dir/?api=1"
                        f"&destination={hospital['latitude']},"
                        f"{hospital['longitude']}"
                    )

                    st.link_button(
                        "Get Directions",
                        directions_url
                    )

            st.caption(
                "Source: OpenStreetMap contributors. "
                "Hospital listings and contact details may be incomplete. "
                "Verify information before visiting."
            )

        except requests.Timeout:

            st.error(
                "The location or hospital service took too long to respond. "
                "Please try again later or use a smaller search radius."
            )

        except requests.RequestException as error:

            st.error(
                "Unable to connect to the location or hospital service."
            )
            st.caption(str(error))

        except RuntimeError as error:

            st.error(
                "Hospital data is temporarily unavailable from OpenStreetMap."
            )
            st.info(
                "Please try again after some time. "
                "The rest of the Dengue AI Guardian application is available."
            )
            st.caption(str(error))

        except Exception as error:

            st.error("Hospital Finder encountered an error.")
            st.exception(error)


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

        st.metric(
            "Symptoms reported",
            f"{score} / 3"
        )

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

        st.metric("Total Patient Records", len(records))

    else:

        st.info("No patient records available yet.")

except Exception as error:

    st.error(f"Could not load patient records: {error}")


# ---------------- NEARBY HOSPITAL FINDER ----------------

st.divider()

show_hospital_finder()

st.divider()


# ---------------- FOOTER ----------------

st.caption(
    "This application currently counts reported symptoms. "
    "It does not use a trained machine-learning model and "
    "cannot diagnose dengue. Government and hospital data "
    "availability depends on external sources."
)
