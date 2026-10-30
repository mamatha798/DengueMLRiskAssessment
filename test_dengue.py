import pandas as pd

url = (
    "https://ncvbdc.mohfw.gov.in/index4.php"
    "?Background=Light&lang=1&level=0"
    "&lid=3715&linkid=431"
)

try:
    df = pd.read_html(url, header=None)[0]

    # The state names are in the second column
    state_column = df.iloc[:, 1].astype(str).str.strip()
    karnataka = df[state_column.str.contains(
        "Karnataka", case=False, na=False
    )]

    if karnataka.empty:
        print("Karnataka row not found.")
        print(df.to_string(index=False, header=False))
    else:
        row = karnataka.iloc[0]

        years = [2021, 2022, 2023, 2024, 2025, 2026]

        print("\nOfficial Karnataka Dengue Data")
        print("--------------------------------")

        for i, year in enumerate(years):
            cases = row.iloc[2 + i * 2]
            deaths = row.iloc[3 + i * 2]
            print(f"{year}: Cases = {cases}, Deaths = {deaths}")

        print("\nSource: NCVBDC Government of India")
        print("2026 figures may be provisional.")

except Exception as error:
    print("Could not extract the data:", error)