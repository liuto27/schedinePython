from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

# Dictionaries for mapping seasons and championships
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
    "I1": "Serie A",
    "I2": "Serie B",
    "E0": "Premier League",
    "E1": "Championship",
    "E2": "League One",
    "E3": "League Two"
}

# Parameter mapping
parameter_mapping = {
    "S": "Shots",
    "ST": "Shots on Target",
    "C": "Corners",
    "F": "Fouls",
    "Y": "Yellow Cards",
    "R": "Red Cards",
    "FTG": "Full Time Goals",
    "HTG": "Half Time Goals"
}


# Function to dynamically create all_matches
def load_all_matches():
    dataframes = []
    for season_code, season_name in season_mapping.items():
        for championship_code, championship_name in championship_mapping.items():
            #  url = f"https://football-data.co.uk/mmz4281/{season_code}/{championship_code}.csv"
            url = f"https://raw.githubusercontent.com/liuto27/schedinePython/refs/heads/main/data/{season_code}_{championship_code}.csv"
            try:
                # Read the CSV file and add season and championship columns
                df = pd.read_csv(url)
                df["Season"] = season_name
                df["Championship"] = championship_name
                dataframes.append(df)
            except Exception as e:
                print(f"Failed to load data for {season_name} - {championship_name}: {e}")

    # Combine all DataFrames from all seasons and championships
    df_matches = pd.concat(dataframes, ignore_index=True)

    # Convert Date column to datetime (using dayfirst, as needed)
    try:
        df_matches["Date"] = pd.to_datetime(df_matches["Date"], errors="coerce", dayfirst=True)
    except Exception as e:
        print(f"Error converting Date column to datetime: {e}")

    # Remove duplicates based on key columns
    df_matches = df_matches.drop_duplicates(subset=["Date", "Time", "HomeTeam", "AwayTeam"])

    # ---- Build a new structure for matches ----
    # We want to get one row per team per match
    # Base columns to preserve from the original data:
    base_cols = ["Div", "Date", "Time", "Season", "Championship"]

    # Build home-team DataFrame
    df_home = pd.DataFrame()
    df_home["Div"] = df_matches["Div"]
    df_home["Date"] = df_matches["Date"]
    df_home["Time"] = df_matches["Time"]
    df_home["Season"] = df_matches["Season"]
    df_home["Championship"] = df_matches["Championship"]
    df_home["Team"] = df_matches["HomeTeam"]
    df_home["OpponentTeam"] = df_matches["AwayTeam"]
    df_home["Home_Away"] = "H"

    # Build away-team DataFrame
    df_away = pd.DataFrame()
    df_away["Div"] = df_matches["Div"]
    df_away["Date"] = df_matches["Date"]
    df_away["Time"] = df_matches["Time"]
    df_away["Season"] = df_matches["Season"]
    df_away["Championship"] = df_matches["Championship"]
    df_away["Team"] = df_matches["AwayTeam"]
    df_away["OpponentTeam"] = df_matches["HomeTeam"]
    df_away["Home_Away"] = "A"

    # Define the statistic columns mapping.
    # (For each parameter “X”, the original CSV columns are given by the home and away keys.)
    stat_columns = {
        "HTG": {"home": "HTHG", "away": "HTAG"},  # Use these for goals (half-time goals in your CSV)
        "S":   {"home": "HS",   "away": "AS"},
        "ST":  {"home": "HST",  "away": "AST"},
        "F":   {"home": "HF",   "away": "AF"},
        "C":   {"home": "HC",   "away": "AC"},
        "Y":   {"home": "HY",   "away": "AY"},
        "R":   {"home": "HR",   "away": "AR"}
    }
    # For home rows: active stats come from the home columns and passive from the away columns.
    for param, cols in stat_columns.items():
        df_home[param + "_a"] = df_matches[cols["home"]]
        df_home[param + "_p"] = df_matches[cols["away"]]

    # For away rows: active stats come from the away columns and passive from the home columns.
    for param, cols in stat_columns.items():
        df_away[param + "_a"] = df_matches[cols["away"]]
        df_away[param + "_p"] = df_matches[cols["home"]]

    # Concatenate both DataFrames to get one unified DataFrame with one row per team per match.
    df_final = pd.concat([df_home, df_away], ignore_index=True)

    # Optionally sort the results by Date (descending), Time, and Team.
    df_final.sort_values(by=["Date", "Time", "Team"], ascending=[False, False, True], inplace=True)

    return df_final



# Load all_matches when the app starts
all_matches = load_all_matches()

# Dropdown options
championships = list(championship_mapping.values())
seasons = list(season_mapping.values())
parameters = list(parameter_mapping.items())
standard_columns = ['Div', 'Date', 'Time', 'OpponentTeam', 'Team', 'Season', 'Championship', 'Home_Away', 'FT_WDL',
                    'HT_WDL']


@app.route("/", methods=["GET", "POST"])
def index():
    # Initialize variables
    teams = []
    filtered_result_team1 = []
    filtered_result_team2 = []
    header_team1 = ""
    header_team2 = ""
    selected_parameter = None
    parameter_friendly_name = None

    if request.method == "POST":
        # Get user inputs from form
        selected_championship = request.form.get("championship")
        selected_season = request.form.get("season")
        team1 = request.form.get("team1")
        team2 = request.form.get("team2")
        selected_parameter = request.form.get("parameter")

        # Debugging: Print the inputs
        print(f"Inputs - Championship: {selected_championship}, Season: {selected_season}, Team 1: {team1}, Team 2: {team2}, Parameter: {selected_parameter}")

        # Get friendly name for the selected parameter
        if selected_parameter:
            parameter_friendly_name = parameter_mapping.get(selected_parameter, selected_parameter)

        # Expand selected parameter to include '_a' and '_p'
        parameter_active = f"{selected_parameter}_a"
        parameter_passive = f"{selected_parameter}_p"

        # Validate columns
        if parameter_active not in all_matches.columns or parameter_passive not in all_matches.columns:
            print(f"Missing columns for parameter: {selected_parameter}")
            return render_template(
                "index.html",
                championships=championships,
                seasons=seasons,
                parameters=parameters,
                teams=teams,
                error=f"Columns for the selected parameter '{parameter_friendly_name}' are missing!",
                filtered_result_team1=[],
                filtered_result_team2=[],
                header_team1="",
                header_team2="",
                selected_parameter=selected_parameter,
                parameter_friendly_name=parameter_friendly_name,
            )

        # Filter all_matches for Team 1
        filtered_data_team1 = all_matches[
            (all_matches["Championship"] == selected_championship) &
            (all_matches["Season"] == selected_season) &
            (all_matches["Team"] == team1)
        ][["Date", "OpponentTeam", "Home_Away", parameter_active, parameter_passive]]

        # Filter all_matches for Team 2
        filtered_data_team2 = all_matches[
            (all_matches["Championship"] == selected_championship) &
            (all_matches["Season"] == selected_season) &
            (all_matches["Team"] == team2)
        ][["Date", "OpponentTeam", "Home_Away", parameter_active, parameter_passive]]

        # Debugging: Print filtered results
        print("Filtered Data Team 1:")
        print(filtered_data_team1.head())
        print("Filtered Data Team 2:")
        print(filtered_data_team2.head())

        # Sort data by Date (descending)
        filtered_data_team1 = filtered_data_team1.sort_values(by="Date", ascending=False)
        filtered_data_team2 = filtered_data_team2.sort_values(by="Date", ascending=False)

        # Format the Date column
        filtered_data_team1["Date"] = filtered_data_team1["Date"].dt.strftime("%Y-%m-%d")
        filtered_data_team2["Date"] = filtered_data_team2["Date"].dt.strftime("%Y-%m-%d")

        # Convert data to dictionaries
        filtered_result_team1 = filtered_data_team1.to_dict(orient="records")
        filtered_result_team2 = filtered_data_team2.to_dict(orient="records")

        # Debugging: Check final results
        print("Filtered Result Team 1:", filtered_result_team1)
        print("Filtered Result Team 2:", filtered_result_team2)

        # Dynamic headers
        header_team1 = f"Matches for {team1} in {selected_season} ({selected_championship})"
        header_team2 = f"Matches for {team2} in {selected_season} ({selected_championship})"

    return render_template(
        "index.html",
        championships=championships,
        seasons=seasons,
        parameters=parameters,
        teams=teams,
        filtered_result_team1=filtered_result_team1,
        filtered_result_team2=filtered_result_team2,
        header_team1=header_team1,
        header_team2=header_team2,
        selected_parameter=selected_parameter,
        parameter_friendly_name=parameter_friendly_name,
    )



@app.route("/get-teams", methods=["POST"])
def get_teams():
    # Get data from the AJAX request
    selected_championship = request.json.get("championship")
    selected_season = request.json.get("season")

    # Debugging: Print the received championship and season
    print(f"Selected Championship: {selected_championship}")
    print(f"Selected Season: {selected_season}")

    # Filter the all_matches DataFrame for teams
    filtered_data = all_matches[
        (all_matches["Championship"] == selected_championship) &
        (all_matches["Season"] == selected_season)
        ]

    # Debugging: Check the filtered data
    print(filtered_data[["Championship", "Season", "Team"]].head())

    # Get unique teams
    teams = filtered_data["Team"].drop_duplicates().sort_values().tolist()

    # Debugging: Print the teams list
    print(f"Teams: {teams}")

    return {"teams": teams}


if __name__ == "__main__":
    app.run(debug=True)
