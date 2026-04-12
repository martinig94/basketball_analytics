"""
EuroLeague data loading and preparation utilities.

All functions are team/season-agnostic: pass ``team`` and ``season`` as
arguments so the same helpers can be reused across analyses.
"""

import os
from typing import Optional

import numpy as np
import pandas as pd

from zone_mapping import ZONE_LABELS, remap_zones
from euroleague_api.EuroLeagueData import EuroLeagueData
from euroleague_api.boxscore_data import BoxScoreData
from euroleague_api.shot_data import ShotData  # noqa: PLC0415
from euroleague_api.standings import Standings

# ── EuroLeague calendar constants ─────────────────────────────────────────────

QUARTER_MAP: dict[int, str] = {
    **{m: "Q1" for m in range(1, 11)},
    **{m: "Q2" for m in range(11, 21)},
    **{m: "Q3" for m in range(21, 31)},
    **{m: "Q4" for m in range(31, 41)},
}

EOQ_MINUTES: tuple[int, ...] = (10, 20, 30, 38, 39, 40)

EOQ_LABELS: dict[int, str] = {
    10: "End Q1",
    20: "End Q2",
    30: "End Q3",
    38: "End Q4",
    39: "End Q4",
    40: "End Q4",
}

# ── private helpers ────────────────────────────────────────────────────────────


def _minutes_to_float(m: object) -> float:
    """Convert a MM:SS string to fractional minutes.

    Args:
        m: Value to parse; expected format ``"MM:SS"``.

    Returns:
        Fractional minutes, or 0.0 on parse failure.
    """
    try:
        parts = str(m).split(":")
        return int(parts[0]) + int(parts[1]) / 60
    except (ValueError, IndexError):
        return 0.0


# ── data loading ──────────────────────────────────────────────────────────────


def load_gamecodes(season: int, team: Optional[str]= None) -> pd.DataFrame:
    """Return gamecodes for all games a team played in a given season.

    Args:
        team: Three-letter team code (e.g. ``"ULK"``).
        season: EuroLeague season start year (e.g. ``2025``).

    Returns:
        DataFrame of gamecodes filtered to the requested team.
    """
      # noqa: PLC0415

    base = EuroLeagueData()
    games = base.get_gamecodes_season(season)
    if team is not None:
        games = games[
            (games["homecode"] == team) | (games["awaycode"] == team)
            ].reset_index(drop=True)
    return games


def load_shot_data(
    games: pd.DataFrame,
    season: int,
    cache_path: str,
) -> pd.DataFrame:
    """Load all shot data for a set of games, using a local CSV cache.

    Fetches from the EuroLeague API only when the cache file does not exist,
    then saves the result for subsequent runs.

    Args:
        games: DataFrame containing a ``gameCode`` column.
        season: EuroLeague season start year passed to the shot API.
        cache_path: Path to the CSV cache file.

    Returns:
        DataFrame of raw shot data for all teams in the provided games.
    """
    if os.path.exists(cache_path):
        print(f"Loading shot data from cache: {cache_path}")
        return pd.read_csv(cache_path)


    print(f"Fetching shot data for {len(games)} games from API ...")
    sd = ShotData()
    frames = []
    for _, row in games.iterrows():
        gc = int(row["gameCode"])
        try:
            frames.append(sd.get_game_shot_data(season, gc))
        except Exception as exc:
            print(f"  WARNING game {gc}: {exc}")
    shots_all = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    shots_all.to_csv(cache_path, index=False)
    return shots_all


def load_shots(
    team: str,
    cache_path: str,
) -> pd.DataFrame:
    """Load team shot data from a CSV cache with analysis-ready columns.

    Adds ``made``, ``is_ft``, and ``quarter`` columns.  Free-throw placeholders
    (``COORD_X == -1``) are retained but flagged via ``is_ft``.

    Args:
        team: Three-letter team code used to filter the shot data.
        cache_path: Path to the CSV cache file.

    Returns:
        DataFrame of shots for *team* with extra computed columns.
    """
    shots = pd.read_csv(cache_path)
    fen = shots[shots["TEAM"] == team].copy()
    fen["made"] = fen["POINTS"] > 0
    fen["is_ft"] = fen["COORD_X"] == -1
    fen["quarter"] = fen["MINUTE"].map(QUARTER_MAP).fillna("OT")
    return fen

def load_or_fetch_shots(
    games: pd.DataFrame,
    season: int,
    cache_path: str,
    team: Optional[str] = None,
) -> pd.DataFrame:
    """Load shot data from cache if available, otherwise fetch from API and save.

    Adds ``made``, ``is_ft``, and ``quarter`` columns when ``team`` is provided.
    Free-throw placeholders (``COORD_X == -1``) are retained but flagged via ``is_ft``.

    Args:
        games: DataFrame containing a ``gameCode`` column.
        season: EuroLeague season start year passed to the shot API.
        cache_path: Path to the CSV cache file.
        team: Three-letter team code to filter by. When ``None`` all shots are returned
              without the extra computed columns.

    Returns:
        DataFrame of shot data, optionally filtered to ``team`` with extra computed columns.
    """
    if not os.path.exists(cache_path):
        print(f"Fetching shot data for {len(games)} games from API...")
        sd = ShotData()
        frames = []
        for _, row in games.iterrows():
            gc = int(row["gameCode"])
            try:
                frames.append(sd.get_game_shot_data(season, gc))
            except Exception as exc:
                print(f"  WARNING game {gc}: {exc}")
        shots = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if not shots.empty:
            os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
            shots.to_csv(cache_path, index=False)
            print(f"Saved {len(shots)} rows -> {cache_path}")
    else:
        print(f"Loading shot data from cache: {cache_path}")
        shots = pd.read_csv(cache_path)

    if team is not None:
        shots = shots[shots["TEAM"] == team].copy()
        shots["made"] = shots["POINTS"] > 0
        shots["is_ft"] = shots["COORD_X"] == -1
        shots["quarter"] = shots["MINUTE"].map(QUARTER_MAP).fillna("OT")

    return shots

def fetch_boxscores(gamecodes_df: pd.DataFrame, season: int , file_name: str, save: bool = True) -> pd.DataFrame:
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
    fen_season_boxscores = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not fen_season_boxscores.empty:
        if save:
            fen_season_boxscores.to_csv(file_name, index=False)
            print(f"\nSaved {len(fen_season_boxscores)} rows -> {file_name}")
    return fen_season_boxscores


def load_boxscore(
    path: str,
    team: Optional[str] = None,
) -> pd.DataFrame:
    """Load player boxscore rows, optionally filtered to a single team.

    Args:
        path: Path to the boxscore CSV file.
        team: Three-letter team code.  When ``None`` all teams are returned.

    Returns:
        DataFrame of per-player, per-game rows with a ``min_float`` column.
        Aggregate rows (``Player`` in ``{"Total", "Team"}``) are always removed.
    """
    box = pd.read_csv(path)
    mask = ~box["Player"].isin({"Total", "Team"})
    if team is not None:
        mask &= box["Team"] == team
    clean = box[mask].copy()
    clean["min_float"] = clean["Minutes"].apply(_minutes_to_float)
    return clean

def load_or_fetch_boxscores(
    gamecodes_df: pd.DataFrame,
    season: int,
    file_name: str,
    team: Optional[str] = None,
    save: bool = True,
) -> pd.DataFrame:
    """Load player boxscores from file if it exists, otherwise fetch and save it.

    Args:
        gamecodes_df: DataFrame with game codes and team info.
        season: Season year used when fetching from the API.
        file_name: Path to the CSV file to load from or save to.
        team: Three-letter team code to filter by. When ``None`` all teams are returned.
        save: Whether to save the fetched data to ``file_name``.

    Returns:
        DataFrame of per-player, per-game rows with a ``min_float`` column.
        Aggregate rows (``Player`` in ``{"Total", "Team"}``) are always removed.
    """
    if not os.path.exists(file_name):
        print(f"File not found — fetching season {season} boxscores...")
        bsd = BoxScoreData()
        frames = []
        for _, row in gamecodes_df.iterrows():
            gamecode = int(row["gameCode"])
            print(f"  Season {season} | Game {gamecode}: {row.get('hometeam', '')} vs {row.get('awayteam', '')}")
            try:
                df = bsd.get_players_boxscore_stats(season, gamecode)
                df.insert(0, "season", season)
                frames.append(df)
            except Exception as e:
                print(f"    WARNING: could not fetch gamecode {gamecode}: {e}")

        boxscores = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        if not boxscores.empty and save:
            os.makedirs(os.path.dirname(file_name) or ".", exist_ok=True)
            boxscores.to_csv(file_name, index=False)
            print(f"Saved {len(boxscores)} rows -> {file_name}")
    else:
        print(f"Loading from {file_name}...")
        boxscores = pd.read_csv(file_name)

    mask = ~boxscores["Player"].isin({"Total", "Team"})
    if team is not None:
        mask &= boxscores["Team"] == team
    clean = boxscores[mask].copy()
    clean["min_float"] = clean["Minutes"].apply(_minutes_to_float)
    return clean

# ── data preparation ──────────────────────────────────────────────────────────


def prepare_zone_stats(
    shots: pd.DataFrame,
    fen_qualified: pd.DataFrame,
) -> pd.DataFrame:
    """Compute FG% per zone plus free-throw rate from the boxscore.

    The shot API only logs made free throws; FT totals are taken from the
    boxscore so that attempts are counted correctly.

    Args:
        shots: Team shot DataFrame with a ``ZONE`` column (already remapped).
        fen_qualified: Boxscore rows with ``FreeThrowsMade`` and
            ``FreeThrowsAttempted`` columns.

    Returns:
        DataFrame with columns ``ZONE``, ``attempts``, ``makes``, ``FG%``,
        ``label``, sorted ascending by FG%.
    """
    fg = shots[shots["ZONE"].str.strip() != ""].copy()
    fg["made"] = fg["POINTS"] > 0

    zone_stats = (
        fg.groupby("ZONE")
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    zone_stats["FG%"] = zone_stats["makes"] / zone_stats["attempts"] * 100
    zone_stats["label"] = zone_stats["ZONE"].map(ZONE_LABELS).fillna(zone_stats["ZONE"])

    ftm = int(fen_qualified["FreeThrowsMade"].sum())
    fta = int(fen_qualified["FreeThrowsAttempted"].sum())
    ft_row = pd.DataFrame([{
        "ZONE":     "FT",
        "attempts": fta,
        "makes":    ftm,
        "FG%":      ftm / fta * 100 if fta > 0 else 0,
        "label":    "Free throws",
    }])
    return pd.concat([zone_stats, ft_row], ignore_index=True).sort_values("FG%")


def prepare_per_game(
    fen_qualified: pd.DataFrame,
    min_gp: int = 5,
) -> pd.DataFrame:
    """Aggregate per-player per-game averages and turnovers per 36 minutes.

    Args:
        fen_qualified: Filtered boxscore rows (e.g. min_float > 3).
        min_gp: Minimum games played threshold; players below are excluded.

    Returns:
        DataFrame with PPG, APG, PIR, and TO_per36 per player.
    """
    per_game = (
        fen_qualified.groupby("Player")
        .agg(
            GP=("Gamecode", "nunique"),
            PPG=("Points", "mean"),
            APG=("Assistances", "mean"),
            PIR=("Valuation", "mean"),
            total_to=("Turnovers", "sum"),
            total_min=("min_float", "sum"),
        )
        .reset_index()
    )
    per_game["TO_per36"] = per_game["total_to"] / per_game["total_min"] * 36
    return per_game[per_game["GP"] >= min_gp]


def prepare_shooting_efficiency(
    fen_qualified: pd.DataFrame,
    min_gp: int = 5,
) -> pd.DataFrame:
    """Compute eFG% and FT% per player from boxscore totals.

    Args:
        fen_qualified: Filtered boxscore rows.
        min_gp: Minimum games played threshold; players below are excluded.

    Returns:
        DataFrame with ``eFG%`` and ``FT%`` per player, sorted by eFG% desc.
    """
    eff = fen_qualified.groupby("Player").agg(
        GP=("Gamecode",               "nunique"),
        FGM2=("FieldGoalsMade2",      "sum"),
        FGA2=("FieldGoalsAttempted2", "sum"),
        FGM3=("FieldGoalsMade3",      "sum"),
        FGA3=("FieldGoalsAttempted3", "sum"),
        FTM=("FreeThrowsMade",        "sum"),
        FTA=("FreeThrowsAttempted",   "sum"),
    ).reset_index()
    eff = eff[eff["GP"] >= min_gp].copy()
    eff["FGA"] = eff["FGA2"] + eff["FGA3"]
    eff = eff[eff["FGA"] > 0]
    eff["eFG%"] = (eff["FGM2"] + eff["FGM3"] + 0.5 * eff["FGM3"]) / eff["FGA"] * 100
    eff["FT%"] = eff.apply(
        lambda r: r["FTM"] / r["FTA"] * 100 if r["FTA"] > 0 else 0, axis=1
    )
    return eff.sort_values("eFG%", ascending=False)


def prepare_eoq_stats(shots: pd.DataFrame) -> pd.DataFrame:
    """Compute end-of-quarter field goal stats per player.

    Uses the module-level ``EOQ_MINUTES`` and ``EOQ_LABELS`` constants.

    Args:
        shots: Shot DataFrame with ``MINUTE``, ``made``, ``is_ft``, and
            ``PLAYER`` columns.

    Returns:
        DataFrame with ``attempts``, ``makes``, and ``FG%`` per player,
        sorted by attempts descending.
    """
    eoq = shots[shots["MINUTE"].isin(EOQ_MINUTES) & ~shots["is_ft"]].copy()
    eoq["period"] = eoq["MINUTE"].map(EOQ_LABELS)

    stats = (
        eoq.groupby("PLAYER")
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    stats["FG%"] = stats["makes"] / stats["attempts"] * 100
    return stats.sort_values("attempts", ascending=False)


def prepare_eoq_by_period(shots: pd.DataFrame) -> pd.DataFrame:
    """Compute end-of-quarter attempts per player per period.

    Args:
        shots: Shot DataFrame with ``MINUTE``, ``made``, ``is_ft``, and
            ``PLAYER`` columns.

    Returns:
        DataFrame with ``attempts`` and ``makes`` per (PLAYER, period).
    """
    eoq = shots[shots["MINUTE"].isin(EOQ_MINUTES) & ~shots["is_ft"]].copy()
    eoq["period"] = eoq["MINUTE"].map(EOQ_LABELS)
    return (
        eoq.groupby(["PLAYER", "period"])
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )


def prepare_fastbreak_per_quarter(shots: pd.DataFrame) -> pd.DataFrame:
    """Compute average fast-break made field goals per game per quarter.

    The EuroLeague API only tags *made* fast-break shots; attempts are
    unavailable.

    Args:
        shots: Shot DataFrame with ``FASTBREAK``, ``is_ft``, ``Gamecode``,
            ``quarter``, and ``made`` columns.

    Returns:
        DataFrame with ``quarter`` and ``avg_makes`` reindexed to Q1–Q4.
    """
    fb = shots[(shots["FASTBREAK"] == 1) & ~shots["is_ft"]].copy()
    per_game_q = (
        fb.groupby(["Gamecode", "quarter"])
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    return (
        per_game_q.groupby("quarter")
        .agg(avg_makes=("makes", "mean"))
        .reindex(["Q1", "Q2", "Q3", "Q4"])
        .reset_index()
    )
# ── docs table helpers ────────────────────────────────────────────────────────


def _ordinal(n: int) -> str:
    """Return the ordinal string for *n* (e.g. 1 → '1st', 3 → '3rd').

    Args:
        n: Positive integer to convert.

    Returns:
        Ordinal string.
    """
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


def _league_rank(series: pd.Series, team: str, ascending: bool = False) -> str:
    """Return the ordinal rank of *team* within *series*.

    Args:
        series: Numeric Series indexed by team code.
        team: Team whose rank to look up.
        ascending: When ``True`` rank 1 = smallest value (e.g. fewest turnovers).
            When ``False`` rank 1 = largest value (e.g. most points).

    Returns:
        Ordinal string such as ``"3rd"``.
    """
    ranked = series.rank(ascending=ascending, method="min").astype(int)
    return _ordinal(int(ranked[team]))


def _team_offense_averages(box_all: pd.DataFrame) -> pd.DataFrame:
    """Compute per-team season offensive averages from an all-teams boxscore.

    Args:
        box_all: All-teams player boxscore (aggregate rows already removed).

    Returns:
        DataFrame indexed by team code with columns ``pts``, ``fg_pct``,
        ``fg3_pct``, ``ft_pct``, ``orb``, ``ast``, ``tov``.
    """
    per_game = box_all.groupby(["Team", "Gamecode"]).agg(
        pts=("Points", "sum"),
        fgm2=("FieldGoalsMade2", "sum"),
        fga2=("FieldGoalsAttempted2", "sum"),
        fgm3=("FieldGoalsMade3", "sum"),
        fga3=("FieldGoalsAttempted3", "sum"),
        ftm=("FreeThrowsMade", "sum"),
        fta=("FreeThrowsAttempted", "sum"),
        orb=("OffensiveRebounds", "sum"),
        ast=("Assistances", "sum"),
        tov=("Turnovers", "sum"),
    )
    avgs = per_game.groupby("Team").mean()
    avgs["fg_pct"] = (avgs["fgm2"] + avgs["fgm3"]) / (avgs["fga2"] + avgs["fga3"]) * 100
    avgs["fg3_pct"] = avgs["fgm3"] / avgs["fga3"] * 100
    avgs["ft_pct"] = avgs["ftm"] / avgs["fta"] * 100
    return avgs


def _team_defense_averages(
    games_all: pd.DataFrame, box_all: pd.DataFrame
) -> pd.DataFrame:
    """Compute per-team season defensive averages from all-league data.

    Args:
        games_all: Full-season gamecodes DataFrame (all teams, all games).
        box_all: All-teams player boxscore (aggregate rows already removed).

    Returns:
        DataFrame indexed by team code with columns ``opp_ppg``, ``drb``,
        ``stl``, ``blk``.
    """
    played = games_all[games_all["played"]]
    home = played[["gameCode", "homecode", "awayscore"]].rename(
        columns={"homecode": "Team", "awayscore": "opp_score"}
    )
    away = played[["gameCode", "awaycode", "homescore"]].rename(
        columns={"awaycode": "Team", "homescore": "opp_score"}
    )
    opp_ppg = (
        pd.concat([home, away])
        .groupby("Team")["opp_score"]
        .mean()
        .rename("opp_ppg")
    )

    per_game = box_all.groupby(["Team", "Gamecode"]).agg(
        drb=("DefensiveRebounds", "sum"),
        stl=("Steals", "sum"),
        blk=("BlocksFavour", "sum"),
    )
    avgs = per_game.groupby("Team").mean()
    return avgs.join(opp_ppg)


def _last_n_gamecodes(games: pd.DataFrame, n: Optional[int]) -> list[int]:
    """Return the game codes for the last *n* played games, most recent last.

    Args:
        games: DataFrame returned by :func:`load_gamecodes` (with ``played``
            and ``date`` columns).
        n: Number of most-recent games to select.

    Returns:
        List of integer game codes, chronologically ordered.
    """
    played = games[games["played"]].copy()
    played["_date"] = pd.to_datetime(played["date"])
    if n is None:
        return played.sort_values("_date")["gameCode"].tolist()
    else:
        return played.sort_values("_date").tail(n)["gameCode"].tolist()


def season_record_splits(games: pd.DataFrame, team: str) -> pd.DataFrame:
    """Compute overall, home, and away win/loss splits for a team.

    Args:
        games: DataFrame returned by :func:`load_gamecodes` with ``winner``,
            ``homecode``, ``awaycode``, and ``played`` columns.
        team: Three-letter team code.

    Returns:
        DataFrame with columns ``Split``, ``W``, ``L``, ``Win%``.
    """
    played = games[games["played"]]
    rows = []
    for label, mask in [
        ("Overall", played.index),
        ("Home", played[played["homecode"] == team].index),
        ("Away", played[played["awaycode"] == team].index),
    ]:
        subset = played.loc[mask]
        w = int((subset["winner"] == team).sum())
        l = len(subset) - w
        win_pct = (w / len(subset))*100 if len(subset) > 0 else 0.0
        rows.append({"Split": label, "W": w, "L": l, "Win%": f"{win_pct:.1f}"})
    return pd.DataFrame(rows)


def last_n_games(
    games: pd.DataFrame, team: str, n: int = 5
) -> pd.DataFrame:
    """Return a summary table for the last *n* played games.

    Args:
        games: DataFrame returned by :func:`load_gamecodes`.
        team: Three-letter team code.
        n: Number of most-recent games to return.

    Returns:
        DataFrame with columns ``#``, ``Date``, ``Opponent``, ``H/A``,
        ``Result``, ``Score``.
    """
    played = games[games["played"]].copy()
    played["_date"] = pd.to_datetime(played["date"])
    recent = played.sort_values("_date").tail(n).reset_index(drop=True)
    rows = []
    for i, row in recent.iterrows():
        is_home = row["homecode"] == team
        opponent = row["awayteam"] if is_home else row["hometeam"]
        ha = "H" if is_home else "A"
        home_score = row["homescore"]
        away_score = row["awayscore"]
        result = "W" if row["winner"] == team else "L"
        rows.append({
            "#": i + 1,
            "Date": row["date"],
            "Opponent": opponent,
            "H/A": ha,
            "Result": result,
            "Score": f"{int(home_score)} – {int(away_score)}",
        })
    return pd.DataFrame(rows).sort_index(ascending=False)


def team_offense_stats(
    box_all: pd.DataFrame, games_all: pd.DataFrame, team: str, n: int = 5
) -> pd.DataFrame:
    """Compute team offensive averages over the last *n* games with league rank.

    The **Value** column reflects the team's averages over their last *n* games.
    The **League Rank** column reflects the team's full-season standing among
    all league teams for each statistic.

    Args:
        box_all: All-teams player boxscore for the full season (no team filter,
            aggregate rows removed) from :func:`load_boxscore`.
        games_all: Full-season gamecodes DataFrame (all teams, all games) from
            :func:`load_gamecodes`.
        team: Three-letter team code.
        n: Number of most-recent games used for the Value column.

    Returns:
        DataFrame with columns ``Stat``, ``Value``, ``League Rank``.
    """
    team_games = games_all[
        (games_all["homecode"] == team) | (games_all["awaycode"] == team)
    ]
    gc_last_n = _last_n_gamecodes(team_games, n)
    recent = box_all[(box_all["Team"] == team) & box_all["Gamecode"].isin(gc_last_n)]

    per_game = recent.groupby("Gamecode").agg(
        pts=("Points", "sum"),
        fgm2=("FieldGoalsMade2", "sum"),
        fga2=("FieldGoalsAttempted2", "sum"),
        fgm3=("FieldGoalsMade3", "sum"),
        fga3=("FieldGoalsAttempted3", "sum"),
        ftm=("FreeThrowsMade", "sum"),
        fta=("FreeThrowsAttempted", "sum"),
        orb=("OffensiveRebounds", "sum"),
        ast=("Assistances", "sum"),
        tov=("Turnovers", "sum"),
    ).mean()

    fg_pct = (per_game["fgm2"] + per_game["fgm3"]) / (per_game["fga2"] + per_game["fga3"]) * 100
    fg3_pct = per_game["fgm3"] / per_game["fga3"] * 100 if per_game["fga3"] > 0 else 0.0
    ft_pct = per_game["ftm"] / per_game["fta"] * 100 if per_game["fta"] > 0 else 0.0

    league = _team_offense_averages(box_all)

    rows = [
        ("Points Per Game",    f"{per_game['pts']:.1f}",  _league_rank(league["pts"],     team, ascending=False)),
        ("Field Goal %",       f"{fg_pct:.1f}%",          _league_rank(league["fg_pct"],  team, ascending=False)),
        ("3-Point %",          f"{fg3_pct:.1f}%",         _league_rank(league["fg3_pct"], team, ascending=False)),
        ("Free Throw %",       f"{ft_pct:.1f}%",          _league_rank(league["ft_pct"],  team, ascending=False)),
        ("Offensive Rebounds", f"{per_game['orb']:.1f}",  _league_rank(league["orb"],     team, ascending=False)),
        ("Assists",            f"{per_game['ast']:.1f}",  _league_rank(league["ast"],     team, ascending=False)),
        ("Turnovers",          f"{per_game['tov']:.1f}",  _league_rank(league["tov"],     team, ascending=True)),
    ]
    return pd.DataFrame(rows, columns=["Stat", "Value", "League Rank"])


def team_defense_stats(
    games_all: pd.DataFrame, box_all: pd.DataFrame, team: str, n: int = 5
) -> pd.DataFrame:
    """Compute team defensive averages over the last *n* games with league rank.

    The **Value** column reflects the team's averages over their last *n* games.
    The **League Rank** column reflects the team's full-season standing among
    all league teams for each statistic.

    Args:
        games_all: Full-season gamecodes DataFrame (all teams, all games) from
            :func:`load_gamecodes`.
        box_all: All-teams player boxscore for the full season (no team filter,
            aggregate rows removed) from :func:`load_boxscore`.
        team: Three-letter team code.
        n: Number of most-recent games used for the Value column.

    Returns:
        DataFrame with columns ``Stat``, ``Value``, ``League Rank``.
    """
    team_games = games_all[
        (games_all["homecode"] == team) | (games_all["awaycode"] == team)
    ]
    played = team_games[team_games["played"]].copy()
    played["_date"] = pd.to_datetime(played["date"])
    recent = played.sort_values("_date").tail(n)

    opp_scores = recent.apply(
        lambda r: r["awayscore"] if r["homecode"] == team else r["homescore"],
        axis=1,
    )
    opp_ppg = float(opp_scores.mean())

    gc_last_n = recent["gameCode"].tolist()
    b = box_all[(box_all["Team"] == team) & box_all["Gamecode"].isin(gc_last_n)]
    per_game = b.groupby("Gamecode").agg(
        drb=("DefensiveRebounds", "sum"),
        stl=("Steals", "sum"),
        blk=("BlocksFavour", "sum"),
    ).mean()

    league = _team_defense_averages(games_all, box_all)

    rows = [
        ("Opp. Points Per Game", f"{opp_ppg:.1f}",          _league_rank(league["opp_ppg"], team, ascending=True)),
        ("Defensive Rebounds",   f"{per_game['drb']:.1f}",  _league_rank(league["drb"],     team, ascending=False)),
        ("Steals",               f"{per_game['stl']:.1f}",  _league_rank(league["stl"],     team, ascending=False)),
        ("Blocks",               f"{per_game['blk']:.1f}",  _league_rank(league["blk"],     team, ascending=False)),
    ]
    return pd.DataFrame(rows, columns=["Stat", "Value", "League Rank"])


def top_players_profile(
    box: pd.DataFrame, games: pd.DataFrame, team: str, top_n: int = 5
) -> list[dict]:
    """Return season and last-5 stats for the top *top_n* players by minutes.

    Args:
        box: DataFrame returned by :func:`load_boxscore`.
        games: DataFrame returned by :func:`load_gamecodes`.
        team: Three-letter team code.
        top_n: Number of players to return.

    Returns:
        List of dicts, each with keys ``name`` (str), ``dorsal`` (str), and
        ``stats_df`` (:class:`~pandas.DataFrame` with columns ``Stat``,
        ``Season Avg``, ``Last 5 Avg``).
    """
    gc_last5 = _last_n_gamecodes(games, 5)

    def _stats_for(subset: pd.DataFrame) -> dict:
        fgm = subset["FieldGoalsMade2"].sum() + subset["FieldGoalsMade3"].sum()
        fga = subset["FieldGoalsAttempted2"].sum() + subset["FieldGoalsAttempted3"].sum()
        ftm = subset["FreeThrowsMade"].sum()
        fta = subset["FreeThrowsAttempted"].sum()
        fgm3 = subset["FieldGoalsMade3"].sum()
        fga3 = subset["FieldGoalsAttempted3"].sum()
        gp = subset["Gamecode"].nunique()
        return {
            "pts": subset["Points"].sum() / gp,
            "reb": subset["TotalRebounds"].sum() / gp,
            "ast": subset["Assistances"].sum() / gp,
            "fg_pct": fgm / fga * 100 if fga > 0 else 0.0,
            "fg3_pct": fgm3 / fga3 * 100 if fga3 > 0 else 0.0,
            "ft_pct": ftm / fta * 100 if fta > 0 else 0.0,
            "min": subset["min_float"].sum() / gp,
        }

    by_min = (
        box.groupby("Player")["min_float"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index.tolist()
    )

    profiles = []
    for player in by_min:
        season_rows = box[box["Player"] == player]
        last5_rows = season_rows[season_rows["Gamecode"].isin(gc_last5)]
        s = _stats_for(season_rows)
        l5 = _stats_for(last5_rows) if not last5_rows.empty else s

        dorsal = str(int(season_rows["Dorsal"].iloc[0])) if not season_rows.empty else "—"
        stats_df = pd.DataFrame(
            [
                ("Points", f"{s['pts']:.1f}", f"{l5['pts']:.1f}"),
                ("Rebounds", f"{s['reb']:.1f}", f"{l5['reb']:.1f}"),
                ("Assists", f"{s['ast']:.1f}", f"{l5['ast']:.1f}"),
                ("FG%", f"{s['fg_pct']:.1f}%", f"{l5['fg_pct']:.1f}%"),
                ("3P%", f"{s['fg3_pct']:.1f}%", f"{l5['fg3_pct']:.1f}%"),
                ("Minutes", f"{s['min']:.1f}", f"{l5['min']:.1f}"),
            ],
            columns=["Stat", "Season Avg", "Last 5 Avg"],
        )
        profiles.append({"name": player, "dorsal": dorsal, "stats_df": stats_df})
    return profiles


def zone_distribution_table(shots: pd.DataFrame) -> pd.DataFrame:
    """Build a shot-distribution table by zone from remapped shot data.

    Args:
        shots: Shot DataFrame with ``ZONE`` already remapped via
            :func:`~zone_mapping.remap_zones` and a ``made`` boolean column.

    Returns:
        DataFrame with columns ``Zone``, ``Attempts``, ``% of Total``,
        ``FG%``, sorted by attempts descending.
    """
    fg = shots[shots["ZONE"].str.strip() != ""].copy()
    total = len(fg)
    grouped = (
        fg.groupby("ZONE")
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    grouped["Zone"] = grouped["ZONE"].map(ZONE_LABELS).fillna(grouped["ZONE"])
    grouped["% of Total"] = (grouped["attempts"] / total * 100).map("{:.1f}%".format)
    grouped["FG%"] = (grouped["makes"] / grouped["attempts"] * 100).map("{:.1f}%".format)
    return (
        grouped[["Zone", "attempts", "% of Total", "FG%"]]
        .rename(columns={"attempts": "Attempts"})
        .sort_values("Attempts", ascending=False)
        .reset_index(drop=True)
    )


def key_3p_shooters(
    shots: pd.DataFrame, box: pd.DataFrame, top_n: int = 3
) -> pd.DataFrame:
    """Return the top *top_n* three-point shooters by attempts per game.

    Args:
        shots: Shot DataFrame with ``ZONE`` remapped, ``made`` column, and
            ``Gamecode`` column.
        box: Boxscore DataFrame used to determine games played per player.
        top_n: Number of shooters to return.

    Returns:
        DataFrame with columns ``Player``, ``3PA/G``, ``3P%``,
        ``Primary Zone``.
    """
    threes = shots[shots["ZONE"].isin({"G", "H", "I"})].copy()
    gp_map = box.groupby("Player")["Gamecode"].nunique()

    agg = (
        threes.groupby("PLAYER")
        .agg(
            attempts=("made", "count"),
            makes=("made", "sum"),
        )
        .reset_index()
    )
    agg["GP"] = agg["PLAYER"].map(gp_map).fillna(1)
    agg["3PA/G"] = (agg["attempts"] / agg["GP"]).round(1)
    agg["3P%"] = (agg["makes"] / agg["attempts"] * 100).map("{:.1f}%".format)

    primary_zone = (
        threes.groupby(["PLAYER", "ZONE"])["made"]
        .count()
        .reset_index()
        .sort_values("made", ascending=False)
        .drop_duplicates("PLAYER")
        .set_index("PLAYER")["ZONE"]
        .map(ZONE_LABELS)
    )
    agg["Primary Zone"] = agg["PLAYER"].map(primary_zone)

    return (
        agg.sort_values("3PA/G", ascending=False)
        .head(top_n)
        .rename(columns={"PLAYER": "Player"})
        [["Player", "3PA/G", "3P%", "Primary Zone"]]
        .reset_index(drop=True)
    )


def fastbreak_stats(shots: pd.DataFrame) -> pd.DataFrame:
    """Compute fast-break statistics from shot data.

    The EuroLeague API only tags *made* fast-break shots; attempts are
    unavailable, so FG% cannot be computed.

    Args:
        shots: Shot DataFrame with ``FASTBREAK``, ``is_ft``, ``made``,
            ``POINTS``, and ``Gamecode`` columns.

    Returns:
        DataFrame with columns ``Stat`` and ``Value``.
    """
    fb = shots[(shots["FASTBREAK"] == 1) & ~shots["is_ft"]]
    n_games = shots["Gamecode"].nunique()
    fb_fgs_per_game = len(fb) / n_games
    fb_pts_per_game = fb["POINTS"].sum() / n_games
    rows = [
        ("Fast Break Points Per Game", f"{fb_pts_per_game:.1f}"),
        ("Fast Break FGs Per Game", f"{fb_fgs_per_game:.1f}"),
    ]
    return pd.DataFrame(rows, columns=["Stat", "Value"])


def last_n_game_sections(
    box: pd.DataFrame, games: pd.DataFrame, team: str, n: int = 5
) -> str:
    """Generate markdown for the last *n* game box-score sections.

    Each section contains an H2 heading with game metadata and a per-player
    stats table.

    Args:
        box: DataFrame returned by :func:`load_boxscore`.
        games: DataFrame returned by :func:`load_gamecodes` (with ``winner``
            column added by :func:`add_winner_team`).
        team: Three-letter team code.
        n: Number of most-recent games to include.

    Returns:
        Markdown string with *n* game sections separated by ``---``.
    """
    played = games[games["played"]].copy()
    played["_date"] = pd.to_datetime(played["date"])
    recent = played.sort_values("_date").tail(n).reset_index(drop=True)

    sections: list[str] = []
    for i, row in recent.iterrows():
        is_home = row["homecode"] == team
        opponent = row["awayteam"] if is_home else row["hometeam"]
        ha = "H" if is_home else "A"
        team_score = int(row["homescore"] if is_home else row["awayscore"])
        opp_score = int(row["awayscore"] if is_home else row["homescore"])
        result = "W" if row["winner"] == team else "L"
        heading = (
            f"## Game {i + 1} — {opponent} | {row['date']} "
            f"| {ha} | {result} {team_score}–{opp_score}"
        )

        gc = int(row["gameCode"])
        game_box = box[box["Gamecode"] == gc].copy()
        game_box = game_box.sort_values("min_float", ascending=False)

        fgm = game_box["FieldGoalsMade2"] + game_box["FieldGoalsMade3"]
        fga = game_box["FieldGoalsAttempted2"] + game_box["FieldGoalsAttempted3"]
        fg_pct = (fgm / fga * 100).fillna(0).map("{:.0f}%".format)
        fgm3_pct = (
            game_box["FieldGoalsMade3"] / game_box["FieldGoalsAttempted3"] * 100
        ).fillna(0).map("{:.0f}%".format)
        ft_pct = (
            game_box["FreeThrowsMade"] / game_box["FreeThrowsAttempted"] * 100
        ).fillna(0).map("{:.0f}%".format)

        table_df = pd.DataFrame({
            "Player": game_box["Player"].values,
            "#": game_box["Dorsal"].fillna(0).astype(int).values,
            "Min": game_box["Minutes"].values,
            "Pts": game_box["Points"].astype(int).values,
            "Reb": game_box["TotalRebounds"].astype(int).values,
            "Ast": game_box["Assistances"].astype(int).values,
            "FGM": fgm.astype(int).values,
            "FGA": fga.astype(int).values,
            "FG%": fg_pct.values,
            "3PM": game_box["FieldGoalsMade3"].astype(int).values,
            "3PA": game_box["FieldGoalsAttempted3"].astype(int).values,
            "3P%": fgm3_pct.values,
            "FTM": game_box["FreeThrowsMade"].astype(int).values,
            "FTA": game_box["FreeThrowsAttempted"].astype(int).values,
            "+/-": game_box["Plusminus"].map("{:+.0f}".format).values,
        })

        sections.append(f"{heading}\n\n{table_df.to_markdown(index=False)}")

    return "\n\n---\n\n".join(sections)


# ── index ──────────────────────────────────────────────────────────────
def add_winner_team(df: pd.DataFrame) -> pd.DataFrame:
    df['winner'] = np.where(
        df["homescore"] > df["awayscore"],
        df["homecode"],
        df["awaycode"]
    )
    return df


def points_per_game(df: pd.DataFrame, team) -> pd.DataFrame:
    scored_points_away = df.loc[(df['awaycode'] == team), "awayscore"].sum()
    scored_points_home = df.loc[(df['homecode'] == team), "homescore"].sum()
    num_games_home = len(df.loc[(df['homecode'] == team), :])
    num_games_away = len(df.loc[(df['awaycode'] == team), :])
    oppg = (scored_points_away + scored_points_home) / (num_games_away + num_games_home)
    ppg_home = scored_points_home / num_games_home
    oppg_away = scored_points_away / num_games_away

    #Defense
    d_scored_points_home = df.loc[(df['awaycode'] != team), "awayscore"].sum()
    d_scored_points_away = df.loc[(df['homecode'] != team), "homescore"].sum()
    dppg = (d_scored_points_away + d_scored_points_home) / (num_games_away + num_games_home)
    dppg_home = d_scored_points_home / num_games_home
    dppg_away = d_scored_points_away / num_games_away
    return pd.DataFrame([oppg, pg], index = ['Opponent Points per Game', 'Points per Game'], columns = ['Season statistics'])

def season_basic_stats(df: pd.DataFrame, team) -> pd.DataFrame:
    num_games = len(df)
    games_w = len(df[df['winner'] == team])
    home_wins = len(df.loc[(df['winner'] == team) & (df['homecode'] == team), :])

    return pd.DataFrame([num_games, games_w, home_wins], index = ['Games played', 'W', 'Home Wins'], columns = ['Season statistics'])

def get_ranking(season: int, team:str):
    stan = Standings("E")
    all_games = stan.get_gamecodes_season(season=season)
    last_round = all_games["Round"].max()
    ranking = stan.get_standings(season=season, round_number=last_round)
    ranking_team = ranking[ranking['club.code'] == team]
    return ranking_team[['position', 'positionChange', 'gamesPlayed',
       'qualified', 'pointsDifference', 'lastTenRecord', 'last5Form']]
