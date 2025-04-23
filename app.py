from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

# ------------------------------
# Mappings for Seasons, Championships,
# and Parameter Friendly Names
# ------------------------------
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


# ------------------------------
# Function: load_all_matches()
# - For each season and championship, load the CSV file from GitHub.
# - Add Season and Championship columns.
# - Build a new DataFrame with one row per team per match.
# ------------------------------
def load_all_matches():
    dataframes = []
    for season_code, season_name in season_mapping.items():
        for championship_code, championship_name in championship_mapping.items():
            url = f"https://raw.githubusercontent.com/liuto27/schedinePython/refs/heads/main/data/{season_code}_{championship_code}.csv"
            try:
                df = pd.read_csv(url)
                df["Season"] = season_name
                df["Championship"] = championship_name
                dataframes.append(df)
            except Exception as e:
                print(f"Failed to load data for {season_name} - {championship_name}: {e}")
    df_matches = pd.concat(dataframes, ignore_index=True)
    try:
        df_matches["Date"] = pd.to_datetime(df_matches["Date"], errors="coerce", dayfirst=True)
    except Exception as e:
        print(f"Error converting Date column to datetime: {e}")
    df_matches = df_matches.drop_duplicates(subset=["Date", "Time", "HomeTeam", "AwayTeam"])

    # Build the home-team DataFrame.
    df_home = pd.DataFrame()
    df_home["Div"] = df_matches["Div"]
    df_home["Date"] = df_matches["Date"]
    df_home["Time"] = df_matches["Time"]
    df_home["Season"] = df_matches["Season"]
    df_home["Championship"] = df_matches["Championship"]
    df_home["Team"] = df_matches["HomeTeam"]
    df_home["OpponentTeam"] = df_matches["AwayTeam"]
    df_home["Home_Away"] = "H"

    # Build the away-team DataFrame.
    df_away = pd.DataFrame()
    df_away["Div"] = df_matches["Div"]
    df_away["Date"] = df_matches["Date"]
    df_away["Time"] = df_matches["Time"]
    df_away["Season"] = df_matches["Season"]
    df_away["Championship"] = df_matches["Championship"]
    df_away["Team"] = df_matches["AwayTeam"]
    df_away["OpponentTeam"] = df_matches["HomeTeam"]
    df_away["Home_Away"] = "A"

    # Mapping of statistic columns.
    stat_columns = {
        "HTG": {"home": "HTHG", "away": "HTAG"},
        "S": {"home": "HS", "away": "AS"},
        "ST": {"home": "HST", "away": "AST"},
        "F": {"home": "HF", "away": "AF"},
        "C": {"home": "HC", "away": "AC"},
        "Y": {"home": "HY", "away": "AY"},
        "R": {"home": "HR", "away": "AR"}
    }
    # For home rows: active stats from home; passive stats from away.
    for param, cols in stat_columns.items():
        df_home[param + "_a"] = df_matches[cols["home"]]
        df_home[param + "_p"] = df_matches[cols["away"]]
    # For away rows: active stats from away; passive stats from home.
    for param, cols in stat_columns.items():
        df_away[param + "_a"] = df_matches[cols["away"]]
        df_away[param + "_p"] = df_matches[cols["home"]]

    # Concatenate home and away data.
    df_final = pd.concat([df_home, df_away], ignore_index=True)
    df_final.sort_values(by=["Date", "Time", "Team"], ascending=[False, False, True], inplace=True)
    return df_final


# ------------------------------
# Helper: calculate_team_averages_from_df()
# - Given a filtered DataFrame for one team and a parameter such as "C",
#   sort matches chronologically and compute the average for the active
#   and passive columns over the last 7 games.
# ------------------------------
def calculate_team_averages_from_df(filtered_df, parameter):
    # Ensure Date is datetime.
    filtered_df["Date"] = pd.to_datetime(filtered_df["Date"], errors="coerce")
    df_sorted = filtered_df.sort_values(by="Date", ascending=True)
    last7 = df_sorted.tail(7)
    avg_active = last7[f"{parameter}_a"].mean()
    avg_passive = last7[f"{parameter}_p"].mean()
    return avg_active, avg_passive


# ------------------------------
# Global: Load all match data.
# ------------------------------
all_matches = load_all_matches()

# Define dropdown options.
championships = list(championship_mapping.values())
seasons = list(season_mapping.values())
parameters = list(parameter_mapping.items())
standard_columns = ['Div', 'Date', 'Time', 'OpponentTeam', 'Team', 'Season', 'Championship', 'Home_Away']


# ------------------------------
# Route: "/"
# - Displays the form and, on POST, filters data.
# - Calculates team averages over the last 7 games.
# - Computes a "Final <Parameter>" value as:
#      Final = [ (x-z)*|x-z| + (y+w)*|y+w| + (x+w)/2 + (3y-z)/2 ] / 2
#   where x = avg_active_team1, y = avg_passive_team1, z = avg_active_team2, w = avg_passive_team2.
# ------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    teams = []
    filtered_result_team1 = []
    filtered_result_team2 = []
    header_team1 = ""
    header_team2 = ""
    selected_parameter = None
    parameter_friendly_name = None
    final_value = None

    # Variables to hold team averages.
    avg_active_team1 = None
    avg_passive_team1 = None
    avg_active_team2 = None
    avg_passive_team2 = None

    team1 = None
    team2 = None

    if request.method == "POST":
        # Retrieve inputs from the form.
        selected_championship = request.form.get("championship")
        selected_season = request.form.get("season")
        team1 = request.form.get("team1")
        team2 = request.form.get("team2")
        selected_parameter = request.form.get("parameter")
        print(
            f"Inputs - Championship: {selected_championship}, Season: {selected_season}, Team 1: {team1}, Team 2: {team2}, Parameter: {selected_parameter}")

        if selected_parameter:
            parameter_friendly_name = parameter_mapping.get(selected_parameter, selected_parameter)

        # Define active and passive column names.
        parameter_active = f"{selected_parameter}_a"
        parameter_passive = f"{selected_parameter}_p"

        # Validate that the necessary columns exist.
        if parameter_active not in all_matches.columns or parameter_passive not in all_matches.columns:
            print(f"Missing columns for parameter: {selected_parameter}")
            return render_template("index.html",
                                   championships=championships,
                                   seasons=seasons,
                                   parameters=parameters,
                                   teams=teams,
                                   error=f"Columns for the parameter '{parameter_friendly_name}' are missing!",
                                   filtered_result_team1=[],
                                   filtered_result_team2=[],
                                   header_team1="",
                                   header_team2="",
                                   selected_parameter=selected_parameter,
                                   parameter_friendly_name=parameter_friendly_name,
                                   team1=team1,
                                   team2=team2,
                                   final_value=final_value)

        # Filter data for Team 1.
        filtered_data_team1 = all_matches[
            (all_matches["Championship"] == selected_championship) &
            (all_matches["Season"] == selected_season) &
            (all_matches["Team"] == team1)
            ][["Date", "OpponentTeam", "Home_Away", parameter_active, parameter_passive]]

        # Filter data for Team 2.
        filtered_data_team2 = all_matches[
            (all_matches["Championship"] == selected_championship) &
            (all_matches["Season"] == selected_season) &
            (all_matches["Team"] == team2)
            ][["Date", "OpponentTeam", "Home_Away", parameter_active, parameter_passive]]

        # Sort by Date descending and format the Date.
        filtered_data_team1 = filtered_data_team1.sort_values(by="Date", ascending=False)
        filtered_data_team2 = filtered_data_team2.sort_values(by="Date", ascending=False)
        filtered_data_team1["Date"] = filtered_data_team1["Date"].dt.strftime("%Y-%m-%d")
        filtered_data_team2["Date"] = filtered_data_team2["Date"].dt.strftime("%Y-%m-%d")

        # Convert to dictionaries for the template.
        filtered_result_team1 = filtered_data_team1.to_dict(orient="records")
        filtered_result_team2 = filtered_data_team2.to_dict(orient="records")

        # Calculate averages (last 7 matches) for both teams.
        avg_active_team1, avg_passive_team1 = calculate_team_averages_from_df(filtered_data_team1, selected_parameter)
        avg_active_team2, avg_passive_team2 = calculate_team_averages_from_df(filtered_data_team2, selected_parameter)

        # Compute the final value using the given formula:
        # Final = [ (x-z)*|x-z| + (y+w)*|y+w| + (x+w)/2 + (3y-z)/2 ] / 2
        # where x = avg_active_team1, y = avg_passive_team1, z = avg_active_team2, w = avg_passive_team2.
        if all(v is not None for v in [avg_active_team1, avg_passive_team1, avg_active_team2, avg_passive_team2]):
            final_value = (
                                  ( (avg_active_team1 + avg_active_team2) * abs(avg_active_team1 - avg_active_team2) +
                                  (avg_passive_team1 + avg_passive_team2) * abs(avg_passive_team1 - avg_passive_team2) ) /
                                  (abs(avg_active_team1 - avg_active_team2) + abs(avg_passive_team1 - avg_passive_team2)) +
                                  (avg_active_team1 + avg_passive_team2) / 2 +
                                  (3 * avg_passive_team1 - avg_active_team2) / 2
                          ) / 2

        header_team1 = f"Matches for {team1} in {selected_season} ({selected_championship})"
        header_team2 = f"Matches for {team2} in {selected_season} ({selected_championship})"

    return render_template("index.html",
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
                           team1=team1,
                           team2=team2,
                           avg_active_team1=avg_active_team1,
                           avg_passive_team1=avg_passive_team1,
                           avg_active_team2=avg_active_team2,
                           avg_passive_team2=avg_passive_team2,
                           final_value=final_value)


# ------------------------------
# Route: /get-teams
# - Receives a JSON payload containing the selected championship and season,
#   and returns a list of unique teams for that combination.
# ------------------------------
@app.route("/get-teams", methods=["POST"])
def get_teams():
    selected_championship = request.json.get("championship")
    selected_season = request.json.get("season")
    print(f"Selected Championship: {selected_championship}")
    print(f"Selected Season: {selected_season}")
    filtered_data = all_matches[
        (all_matches["Championship"] == selected_championship) &
        (all_matches["Season"] == selected_season)
        ]
    teams = filtered_data["Team"].drop_duplicates().sort_values().tolist()
    return {"teams": teams}


if __name__ == "__main__":
    app.run(debug=True)
