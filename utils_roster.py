"""EuroLeague roster data loading and player image utilities.

Provides helpers to fetch or load player biographical data (including image
URLs) and to download player headshots to a local path for use in the MkDocs
report and PDF export.
"""

import os
import urllib.request
from datetime import date
from typing import Optional

import pandas as pd
from euroleague_api.player_stats import PlayerStats

_REQUIRED_COLS = {"player_code", "player_name", "player_team_code", "player_image_url"}


def _calculate_age(birth_date_str: Optional[str]) -> Optional[int]:
    """Return age in whole years from an ISO-8601 birth-date string.

    Args:
        birth_date_str: Date string in ``YYYY-MM-DD`` format, or ``None``.

    Returns:
        Integer age, or ``None`` if the input cannot be parsed.
    """
    if not birth_date_str:
        return None
    try:
        bd = date.fromisoformat(str(birth_date_str)[:10])
        today = date.today()
        return today.year - bd.year - (
            (today.month, today.day) < (bd.month, bd.day)
        )
    except (ValueError, TypeError):
        return None


def fetch_or_load_rosters(
    season: int = 2025,
    cache_path: Optional[str] = None,
    competition_code: str = "E",
) -> pd.DataFrame:
    """Load EuroLeague roster data from cache or the player-stats API.

    The returned DataFrame always contains at minimum the columns
    ``player_code``, ``player_name``, ``player_team_code``, and
    ``player_image_url``.  If a cache file exists but is missing any of those
    columns (e.g. an older cache that predates image-URL support) it is
    silently regenerated.

    Args:
        season: Season start year (e.g. ``2025`` for 2025-26).
        cache_path: Optional path to a CSV cache file.
        competition_code: ``"E"`` for EuroLeague, ``"U"`` for EuroCup.

    Returns:
        DataFrame with one row per player and columns:
        ``player_code``, ``player_name``, ``player_team_code``,
        ``player_age``, ``player_image_url``.
    """
    if cache_path and os.path.exists(cache_path):
        cached = pd.read_csv(cache_path)
        if _REQUIRED_COLS.issubset(cached.columns):
            print(f"Loading rosters from cache: {cache_path}")
            return cached
        print(f"Cache {cache_path} is missing columns — re-fetching...")

    print(f"Fetching roster data for season {season}...")
    ps = PlayerStats(competition_code)
    df = ps.get_player_stats_single_season(
        endpoint="traditional",
        season=season,
        phase_type_code="RS",
        statistic_mode="PerGame",
    )

    rename = {
        "player.code":      "player_code",
        "player.name":      "player_name",
        "player.team.code": "player_team_code",
        "player.age":       "player_age",
        "player.imageUrl":  "player_image_url",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df = df.drop_duplicates(subset=["player_code"])

    desired = ["player_code", "player_name", "player_team_code",
               "player_age", "player_image_url"]
    rosters = df[[c for c in desired if c in df.columns]].reset_index(drop=True)

    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        rosters.to_csv(cache_path, index=False)
        print(f"Saved {len(rosters)} players -> {cache_path}")

    return rosters


def get_player_image_url(
    roster: pd.DataFrame,
    player_name: str,
    team_code: str,
) -> Optional[str]:
    """Look up a player's headshot URL from the roster DataFrame.

    Matching is done on both name and team code so that players on loan do
    not collide with identically-named players elsewhere.

    Args:
        roster: DataFrame returned by :func:`fetch_or_load_rosters`.
        player_name: Player name in ``"SURNAME, Firstname"`` format as
            returned by the boxscore API.
        team_code: Three-letter EuroLeague team code.

    Returns:
        CDN image URL string, or ``None`` if the player is not found.
    """
    if "player_image_url" not in roster.columns:
        return None
    mask = (roster["player_name"] == player_name) & (
        roster["player_team_code"] == team_code
    )
    matches = roster.loc[mask, "player_image_url"].dropna()
    return str(matches.iloc[0]) if not matches.empty else None


def download_player_image(url: str, dest_path: str) -> bool:
    """Download a player headshot from *url* and save it to *dest_path*.

    Skips the download if *dest_path* already exists (cache-on-disk).
    Creates any missing parent directories automatically.

    Args:
        url: Full HTTPS URL of the player image.
        dest_path: Local file path to write the image to.

    Returns:
        ``True`` if the image was downloaded or already present,
        ``False`` if the download failed.
    """
    if os.path.exists(dest_path):
        return True
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest_path)
        return True
    except OSError as exc:
        print(f"Failed to download player image {url}: {exc}")
        return False
