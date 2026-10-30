import json
import urllib.request
import pandas as pd

from database import create_tables, save_symptoms

# Initialize the database
create_tables()


def get_yes_no(question):
    while True:
        answer = input(question + " (yes/no): ").strip().lower()

        if answer in ("yes", "no"):
            return answer

        print("Please enter yes or no.")


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

        current = data.get("current", {})

        print("\n🌐 Live Bengaluru Weather")
        print("----------------------------")
        print("Temperature:", current.get("temperature_2m"), "°C")
        print("Humidity:", current.get("relative_humidity_2m"), "%")
        print("Precipitation:", current.get("precipitation"), "mm")
        print("Weather time:", current.get("time", "Not available"))

    except Exception as error:
        print("\nWeather API unavailable:", error)


def show_official_dengue_data():
    url = (
        "https://ncvbdc.mohfw.gov.in/index4.php"
        "?Background=Light&lang=1&level=0"
        "&lid=3715&linkid=431"
    )

    print("\n🇮🇳 Official Karnataka Dengue Data")
    print("----------------------------------")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 DengueAIGuardian/1.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read()

        tables = pd.read_html(html, header=None)

        if not tables:
            print("No tables found on the government page.")
            print("Source:", url)
            return

        df = tables[0]
        found = False

        for _, row in df.iterrows():
            row_text = row.astype(str).str.strip()

            if row_text.str.fullmatch(
                "Karnataka", case=False, na=False
            ).any():

                found = True
                years = [2021, 2022, 2023, 2024, 2025, 2026]

                for i, year in enumerate(years):
                    cases = row.iloc[2 + i * 2]
                    deaths = row.iloc[3 + i * 2]

                    print(
                        f"{year}: Cases = {cases}, "
                        f"Deaths = {deaths}"
                    )

                print("\nSource: NCVBDC, Government of India")
                print("2026 figures may be provisional.")
                break

        if not found:
            print("Karnataka row was not found in the table.")
            print("Please check the official source:", url)

    except Exception as error:
        print("Could not fetch official dengue data:", error)
        print("Please check the government source:", url)


def main():
    print("🦟 Dengue AI Guardian")
    print("============================")
    print("Symptom Assessment")
    print("This is not an AI diagnosis.")

    fever = get_yes_no("Do you have fever?")
    pain = get_yes_no("Do you have body pain?")
    rash = get_yes_no("Do you have a skin rash?")

    # Save symptoms in the local SQLite database
    record_id = save_symptoms(
        1 if fever == "yes" else 0,
        1 if pain == "yes" else 0,
        1 if rash == "yes" else 0
    )

    score = sum([
        fever == "yes",
        pain == "yes",
        rash == "yes"
    ])

    print("\n--- Assessment Result ---")
    print("Symptoms reported:", score, "out of 3")
    print("Record saved in local database. ID:", record_id)

    if fever == "yes":
        print(
            "Fever can have many causes, including dengue. "
            "Please contact a healthcare professional for assessment."
        )
    else:
        print(
            "These answers cannot rule out dengue. "
            "Consult a healthcare professional if you are concerned."
        )

    print("\n⚠️ Medical Safety")
    print(
        "Severe abdominal pain, persistent vomiting, bleeding, "
        "difficulty breathing, confusion, or cold/clammy skin "
        "need urgent medical evaluation. Do not wait for this app."
    )

    print(
        "\nNote: This program counts reported symptoms only. "
        "It is not a trained ML model and cannot diagnose dengue."
    )

    get_bengaluru_weather()
    show_official_dengue_data()


if __name__ == "__main__":
    main()