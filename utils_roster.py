import os
import pandas as pd
from datetime import date
from typing import Optional
from euroleague_api.player_stats import PlayerStats


def _calculate_age(birth_date_str: Optional[str]) -> Optional[int]:
    if not birth_date_str:
        return None
    try:
        bd = date.fromisoformat(str(birth_date_str)[:10])
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except (ValueError, TypeError):
        return None


def fetch_or_load_rosters(
    season: int = 2025,
    cache_path: Optional[str] = None,
    competition_code: str = "E",
) -> pd.DataFrame:
    """Load EuroLeague roster data (name, team, position, height, weight, age)
    from cache if available, otherwise fetch via the player stats API.

    The returned DataFrame has one row per player, with columns:
        player_id, name, team_code, team_name, position,
        height_cm, weight_kg, birth_date, age, nationality

    Args:
        season: Season start year (e.g. 2025 for 2025-26).
        cache_path: Optional path to a CSV cache file.
        competition_code: "E" for EuroLeague, "U" for EuroCup.

    Returns:
        DataFrame of all players with biographical and physical attributes.
    """
    if cache_path and os.path.exists(cache_path):
        print(f"Loading rosters from cache: {cache_path}")
        return pd.read_csv(cache_path)

    print(f"Fetching roster data for season {season}...")
    ps = PlayerStats(competition_code)

    # This endpoint returns one row per player with height, weight,
    # birthDate, position, team — exactly what we need
    df = ps.get_player_stats_single_season(
        endpoint="traditional",
        season=season,
        phase_type_code="RS",
        statistic_mode="PerGame",
    )

    # Normalise to the columns we care about
    col_map = {
        # common names in the API response — handle both casing variants
        "player.code":     "player_code",
        "player.name":       "player_name",
        "player.team.code":     "player_team_code",
        "player.age":        "player_age",
        "player.imageUrl": "player_image_url",
    }

    # Only rename columns that actually exist
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Keep one row per player (deduplicate if player appears in multiple phases)
    id_col = "player_code"
    df = df.drop_duplicates(subset=[id_col])

    # Select and reorder only the columns that exist
    desired = ["player_code", "player_name", "player_team_code", "player_age"]
    final_cols = [c for c in desired if c in df.columns]
    rosters = df[final_cols].reset_index(drop=True)

    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        rosters.to_csv(cache_path, index=False)
        print(f"Saved {len(rosters)} players -> {cache_path}")

    return rosters

rosters = fetch_or_load_rosters(season=2025, cache_path="data/rosters_2025.csv")

# Filter to one team
mad = rosters[rosters["player_team_code"] == "MAD"]