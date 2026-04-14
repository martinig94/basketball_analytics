"""Generate all data-driven tables in the MkDocs documentation.

Run this script before ``mkdocs build`` to populate the markdown files with
live data from the EuroLeague API and local CSV caches.
"""

from zone_mapping import remap_zones

from constants import SEASON, TEAM
from utils_euroleague import (
    add_winner_team,
    defense_stats_section,
    fastbreak_stats,
    get_ranking,
    key_3p_shooters,
    key_midrange_shooters,
    key_paint_shooters,
    last_n_game_sections,
    last_n_games,
    load_gamecodes,
    load_or_fetch_boxscores,
    load_or_fetch_shots,
    prepare_eoq_by_period,
    prepare_eoq_stats,
    save_active_roster,
    season_record_splits,
    team_defense_stats,
    team_offense_stats,
    top_players_profile,
    zone_distribution_table,
    zone_summary,
)
from utils_css import write_team_css
from utils_markdown import update_content_in_file, update_info_in_file, update_table_in_file
from utils_plot import BG, heatmap_shot_players, heatmap_shot_team, make_fig1_eoq
from utils_roster import download_player_image, fetch_or_load_rosters, get_player_image_url

# ── per-team CSS ──────────────────────────────────────────────────────────────

write_team_css(TEAM, "docs/stylesheets/extra.css")

# ── shared data ───────────────────────────────────────────────────────────────

games = load_gamecodes(SEASON, TEAM)
games_all = load_gamecodes(SEASON)
games = add_winner_team(games)
box = load_or_fetch_boxscores(
    games, season=SEASON, team=TEAM, file_name="fenerbahce_boxscores_2025_26.csv"
)
box_all = load_or_fetch_boxscores(
    games, season=SEASON, file_name="boxscore_2025.csv"
)
shots = remap_zones(
    load_or_fetch_shots(
        games=games, team=TEAM, season=SEASON, cache_path="fenerbahce_shots_2025_26.csv"
    )
)

# ── active roster CSV (seed on first run; manual edits are preserved) ─────────────

save_active_roster(box, TEAM)

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

# ── section-d-defensive-analysis.md ──────────────────────────────────────────

update_table_in_file(
    "docs/section-d-defensive-analysis.md",
    defense_stats_section(box, games, box_all, TEAM),
    "DEFENSE-STATS-5",
)

# ── section-b-roster-players.md ───────────────────────────────────────────────

players_data = top_players_profile(box, games, TEAM, top_n=5)
players_data_9 = top_players_profile(box, games, TEAM, top_n=9)
roster = fetch_or_load_rosters(season=SEASON, cache_path="data/rosters_2025.csv")

for i, player in enumerate(players_data, start=1):
    update_content_in_file(
        "docs/section-b-roster-players.md",
        f"### {player['name']} — #{player['dorsal']}",
        f"PLAYER-{i}-HEADER",
    )

    img_dest = f"docs/images/{TEAM}_player_{i}.png"
    img_url = get_player_image_url(roster, player["name"], TEAM)
    if img_url and download_player_image(img_url, img_dest):
        img_md = f"![{player['name']} headshot](images/{TEAM}_player_{i}.png)"
    else:
        img_md = ""
    update_content_in_file(
        "docs/section-b-roster-players.md",
        img_md,
        f"PLAYER-{i}-IMAGE",
    )

    update_table_in_file(
        "docs/section-b-roster-players.md",
        player["stats_df"],
        f"PLAYER-{i}-STATS",
    )

    update_content_in_file(
        "docs/section-b-roster-players.md",
        f"![{player['name']} zone heatmap](images/{TEAM}_heatmap_player_{i}.png)",
        f"PLAYER-{i}-HEATMAP",
    )

# ── section-c-offensive-analysis.md ──────────────────────────────────────────

update_table_in_file(
    "docs/section-c-offensive-analysis.md",
    zone_distribution_table(shots),
    "ZONE-DISTRIBUTION",
)
update_info_in_file(
    "docs/section-c-offensive-analysis.md",
    zone_summary(shots),
    "ZONE-SUMMARY",
)
update_table_in_file(
    "docs/section-c-offensive-analysis.md",
    key_3p_shooters(shots, box, TEAM),
    "KEY-SHOOTERS",
)
update_table_in_file(
    "docs/section-c-offensive-analysis.md",
    key_midrange_shooters(shots, box, TEAM),
    "KEY-SHOOTERS-MIDRANGE",
)
update_table_in_file(
    "docs/section-c-offensive-analysis.md",
    key_paint_shooters(shots, box, TEAM),
    "KEY-SHOOTERS-PAINT",
)

# ── section-e-transition-play.md ─────────────────────────────────────────────

update_table_in_file(
    "docs/section-e-transition-play.md",
    fastbreak_stats(shots),
    "FASTBREAK-STATS",
)

# ── section-f-special-situations.md (EOQ) ────────────────────────────────────

eoq_stats = prepare_eoq_stats(shots)
eoq_by_period = prepare_eoq_by_period(shots)
fig1 = make_fig1_eoq(eoq_stats, eoq_by_period, team_name=TEAM, season=SEASON)
fig1.savefig("docs/images/eoq_image.png", dpi=150, bbox_inches="tight", facecolor=BG)
print("Saved -> eoq_image.png")

# ── appendix-box-scores.md ───────────────────────────────────────────────────

update_content_in_file(
    "docs/appendix-box-scores.md",
    last_n_game_sections(box, games, TEAM),
    "APPENDIX-LAST-5",
)

# ── zone heatmaps ─────────────────────────────────────────────────────────────

heatmap_shot_team(shots, TEAM)
heatmap_shot_players(shots, players_data_9, TEAM)
