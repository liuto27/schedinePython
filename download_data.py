import os
import requests

# Define the season and championship mappings
season_mapping = {
    "2223": "2022/2023",
    "2324": "2023/2024",
    "2425": "2024/2025"
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

# Loop through each season and championship to download the files
for season_code, season_name in season_mapping.items():
    for championship_code, championship_name in championship_mapping.items():
        # Construct the file's URL
        url = base_url.format(season=season_code, championship=championship_code)
        filename = f"{season_code}_{championship_code}.csv"
        file_path = os.path.join(data_dir, filename)

        try:
            # Fetch the file using an HTTP GET request
            print(f"Downloading {filename}...")
            response = requests.get(url)

            # Check if the response is successful
            if response.status_code == 200:
                # Save the file to the "data" directory
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"Saved: {file_path}")
            else:
                print(f"Failed to download {filename}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

print("Download process completed.")
