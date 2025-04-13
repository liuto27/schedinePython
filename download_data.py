import os
import requests

# Define the season and championship mappings (including future seasons)
season_mapping = {
    "2223": "2022/2023",
    "2324": "2023/2024",
    "2425": "2024/2025",
    "2526": "2025/2026",
    "2627": "2026/2027",
    "2728": "2027/2028",
    "2829": "2028/2029"
}

championship_mapping = {
    "E0": "Premier League",
    "E1": "Championship",
    "E2": "League One",
    "E3": "League Two",
    "I1": "Serie A",
    "I2": "Serie B"
}

# Set the base URL for the CSV files
base_url = "https://www.football-data.co.uk/mmz4281/{season}/{championship}.csv"

# Create the "data" folder if it doesn't exist
data_dir = "./data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Find the latest season code that has already been downloaded
existing_files = [f.split('_')[0] for f in os.listdir(data_dir) if f.endswith(".csv")]
latest_season_code = max(existing_files) if existing_files else min(season_mapping.keys())

print(f"Latest season in local data: {latest_season_code}")

# Loop through each championship and attempt to download the latest season's file
for championship_code, championship_name in championship_mapping.items():
    # Construct the URL for the latest season file
    url = base_url.format(season=latest_season_code, championship=championship_code)
    filename = f"{latest_season_code}_{championship_code}.csv"
    file_path = os.path.join(data_dir, filename)

    try:
        # Fetch the file using an HTTP GET request
        print(f"Checking availability of {filename}...")
        response = requests.get(url)

        # Check if the file exists on the server
        if response.status_code == 200:
            # Save the file to the "data" directory
            print(f"Downloading {filename}...")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Saved: {file_path}")
        else:
            # Skip the file if it doesn't exist (e.g., HTTP 404 Not Found)
            print(f"{filename} not found (HTTP {response.status_code}). Skipping...")
    except Exception as e:
        # Handle other possible errors (e.g., network issues)
        print(f"Error downloading {filename}: {e}")

print("Latest season download process completed.")
