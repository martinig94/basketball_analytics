"""Generate all data-driven tables in the MkDocs documentation.

Run this script before ``mkdocs build`` to populate the markdown files with
live data from the EuroLeague API and local CSV caches.
"""

from zone_mapping import remap_zones

from constants import SEASON, TEAM
from utils_euroleague import (
    add_winner_team,
    fastbreak_stats,
    fetch_boxscores,
    key_3p_shooters,
    last_n_game_sections,
    last_n_games,
    load_boxscore,
    load_gamecodes,
    load_shots,
    season_basic_stats,
    season_record_splits,
    team_defense_stats,
    team_offense_stats,
    top_players_profile,
    zone_distribution_table,
    get_ranking
)
from utils_markdown import update_content_in_file, update_table_in_file

# ── shared data ───────────────────────────────────────────────────────────────

games = load_gamecodes(SEASON, TEAM)
games_all = load_gamecodes(SEASON)
games = add_winner_team(games)
box = load_boxscore("fenerbahce_boxscores_2025_26.csv", TEAM)
box_all = load_boxscore("boxscore_2025.csv")
shots = remap_zones(load_shots(TEAM, "fenerbahce_shots_2025_26.csv"))

# ── index.md ──────────────────────────────────────────────────────────────────

#update_table_in_file("docs/index.md", season_basic_stats(games, TEAM), "SEASON-OVERVIEW")

# ── section-a-general-information.md ─────────────────────────────────────────
update_table_in_file(
    "docs/section-a-general-information.md",
    season_record_splits(games, TEAM),
    "SEASON-RECORD",
)
update_table_in_file(
    "docs/section-a-general-information.md",
   get_ranking(SEASON, TEAM),
    "RANKING",
)
update_table_in_file(
    "docs/section-a-general-information.md",
    last_n_games(games, TEAM),
    "SEASON-RECORD-5",
)
update_table_in_file(
    "docs/section-a-general-information.md",
    team_offense_stats(box_all, games_all, TEAM),
    "TEAM-STATS-OFFENSE",
)
update_table_in_file(
    "docs/section-a-general-information.md",
    team_defense_stats(games_all, box_all, TEAM),
    "TEAM-STATS-DIFENSE",
)

# ── section-b-roster-players.md ───────────────────────────────────────────────

for i, player in enumerate(top_players_profile(box, games, TEAM), start=1):
    update_content_in_file(
        "docs/section-b-roster-players.md",
        f"### {player['name']} — #{player['dorsal']}",
        f"PLAYER-{i}-HEADER",
    )
    update_table_in_file(
        "docs/section-b-roster-players.md",
        player["stats_df"],
        f"PLAYER-{i}-STATS",
    )

# ── section-c-offensive-analysis.md ──────────────────────────────────────────

update_table_in_file(
    "docs/section-c-offensive-analysis.md",
    zone_distribution_table(shots),
    "ZONE-DISTRIBUTION",
)
update_table_in_file(
    "docs/section-c-offensive-analysis.md",
    key_3p_shooters(shots, box),
    "KEY-SHOOTERS",
)

# ── section-e-transition-play.md ─────────────────────────────────────────────

update_table_in_file(
    "docs/section-e-transition-play.md",
    fastbreak_stats(shots),
    "FASTBREAK-STATS",
)

# ── appendix-box-scores.md ───────────────────────────────────────────────────

update_content_in_file(
    "docs/appendix-box-scores.md",
    last_n_game_sections(box, games, TEAM),
    "APPENDIX-LAST-5",
)
