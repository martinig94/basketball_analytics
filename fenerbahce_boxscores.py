"""
Fetch EuroLeague boxscore data for Fenerbahce:
  1. All games this season (2024-25)
  2. Games vs Real Madrid in the last 3 seasons (2022-23, 2023-24, 2024-25)
"""

import pandas as pd
from euroleague_api.boxscore_data import BoxScoreData
from euroleague_api.EuroLeagueData import EuroLeagueData

FENERBAHCE = "ULK"
REAL_MADRID = "MAD"
CURRENT_SEASON = 2025
LAST_3_SEASONS = [2023, 2024, 2025]


def get_team_gamecodes(season: int, team_code: str) -> pd.DataFrame:
    """Return gamecodes for all games involving a team in a season."""
    base = EuroLeagueData()
    games = base.get_gamecodes_season(season)
    mask = (games["homecode"] == team_code) | (games["awaycode"] == team_code)
    return games[mask].reset_index(drop=True)


def get_matchup_gamecodes(season: int, team_a: str, team_b: str) -> pd.DataFrame:
    """Return gamecodes for games between two specific teams in a season."""
    base = EuroLeagueData()
    games = base.get_gamecodes_season(season)
    mask = (
        ((games["homecode"] == team_a) & (games["awaycode"] == team_b)) |
        ((games["homecode"] == team_b) & (games["awaycode"] == team_a))
    )
    return games[mask].reset_index(drop=True)


def fetch_boxscores(gamecodes_df: pd.DataFrame, season: int) -> pd.DataFrame:
    """Fetch player boxscore stats for each gamecode and concatenate."""
    bsd = BoxScoreData()
    frames = []
    for _, row in gamecodes_df.iterrows():
        gamecode = int(row["gameCode"])
        print(f"  Season {season} | Game {gamecode}: {row.get('hometeam','')} vs {row.get('awayteam','')}")
        try:
            df = bsd.get_players_boxscore_stats(season, gamecode)
            df.insert(0, "season", season)
            frames.append(df)
        except Exception as e:
            print(f"    WARNING: could not fetch gamecode {gamecode}: {e}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# --- 1. Fenerbahce all games this season ---
print(f"\n=== Fenerbahce boxscores — {CURRENT_SEASON}-{str(CURRENT_SEASON+1)[2:]} season ===")
fen_games = get_team_gamecodes(CURRENT_SEASON, FENERBAHCE)
print(f"Found {len(fen_games)} Fenerbahce games")
fen_season_boxscores = fetch_boxscores(fen_games, CURRENT_SEASON)

if not fen_season_boxscores.empty:
    fen_season_boxscores.to_csv("fenerbahce_boxscores_2025_26.csv", index=False)
    print(f"\nSaved {len(fen_season_boxscores)} rows -> fenerbahce_boxscores_2025_26.csv")


# --- 2. Fenerbahce vs Real Madrid — last 3 seasons ---
print(f"\n=== Fenerbahce vs Real Madrid — last 3 seasons ===")
matchup_frames = []
for season in LAST_3_SEASONS:
    matchup = get_matchup_gamecodes(season, FENERBAHCE, REAL_MADRID)
    print(f"Season {season}: {len(matchup)} game(s) found")
    if not matchup.empty:
        df = fetch_boxscores(matchup, season)
        matchup_frames.append(df)

if matchup_frames:
    fen_vs_mad = pd.concat(matchup_frames, ignore_index=True)
    fen_vs_mad.to_csv("fenerbahce_vs_realmadrid_last3seasons.csv", index=False)
    print(f"\nSaved {len(fen_vs_mad)} rows -> fenerbahce_vs_realmadrid_last3seasons.csv")
else:
    print("No matchup data found.")
