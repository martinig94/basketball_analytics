"""
Fenerbahce Beko — EuroLeague 2025-26 Analysis
  Figure 1: Zone FG% bar chart + shot chart
  Figure 2: Key offensive players + shooting efficiency (eFG% vs FT%)
  Figure 3: Turnovers per 36 min

Zones are assigned from shot coordinates (see zone_mapping.py):
  A = Under basket     B = Left short range   C = Right short range
  D = Left mid-range   E = Centre mid-range   F = Right mid-range
  G = Left 3PT         H = Centre 3PT         I = Right 3PT
FT% comes from boxscore totals — the shot API only logs made free throws.
"""

import matplotlib.pyplot as plt

from zone_mapping import remap_zones
from utils_euroleague import (
    load_gamecodes,
    load_shot_data,
    load_boxscore,
    prepare_zone_stats,
    prepare_per_game,
    prepare_shooting_efficiency,
)
from utils_plot import (
    BG,
    plot_zone_efficiency,
    plot_shot_chart,
    plot_offensive_players,
    plot_shooting_efficiency,
    plot_turnovers,
)

# ── constants ─────────────────────────────────────────────────────────────────

TEAM   = "ULK"
SEASON = 2025

# ── figure assembly ───────────────────────────────────────────────────────────


def make_fig1_zones_shotchart(
    zone_stats,
    shots,
    games_played: int,
) -> plt.Figure:
    """Zone FG% bar chart alongside a full shot chart.

    Args:
        zone_stats: Output of ``prepare_zone_stats``.
        shots: Remapped team shot DataFrame.
        games_played: Total games played, shown in the figure title.

    Returns:
        Matplotlib Figure.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"Fenerbahce Beko — EuroLeague 2025-26  |  {games_played} games played",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_zone_efficiency(ax1, zone_stats)
    plot_shot_chart(ax2, shots)
    fig.tight_layout()
    return fig


def make_fig2_offense(per_game, eff) -> plt.Figure:
    """Offensive player profiles: PPG/APG stacked bars + eFG% vs FT% chart.

    Args:
        per_game: Output of ``prepare_per_game``.
        eff: Output of ``prepare_shooting_efficiency``.

    Returns:
        Matplotlib Figure.
    """
    fig, (ax3, ax5) = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Fenerbahce Beko — EuroLeague 2025-26  |  Offensive Profile",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_offensive_players(ax3, per_game)
    plot_shooting_efficiency(ax5, eff)
    fig.tight_layout()
    return fig


def make_fig3_turnovers(per_game) -> plt.Figure:
    """Turnovers per 36 minutes for the top 10 players.

    Args:
        per_game: Output of ``prepare_per_game``.

    Returns:
        Matplotlib Figure.
    """
    fig, ax4 = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Fenerbahce Beko — EuroLeague 2025-26  |  Ball Security",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_turnovers(ax4, per_game)
    fig.tight_layout()
    return fig


# ── text summary ──────────────────────────────────────────────────────────────


def print_summary(zone_stats, per_game) -> None:
    """Print key insights to stdout: weakest zones, top scorers, most turnovers.

    Args:
        zone_stats: Output of ``prepare_zone_stats``.
        per_game: Output of ``prepare_per_game``.
    """
    print("\n" + "=" * 60)
    print("FENERBAHCE 2025-26 -- KEY INSIGHTS")
    print("=" * 60)

    worst = zone_stats[zone_stats["attempts"] >= 15].sort_values("FG%").head(3)
    print("\n[WEAKEST SHOT ZONES] (min 15 attempts)")
    for _, r in worst.iterrows():
        print(f"  {r['label']:32s}  {r['FG%']:.1f}%  ({int(r['attempts'])} att)")

    best_off = per_game.sort_values("PIR", ascending=False).head(5)
    print("\n[TOP OFFENSIVE PLAYERS] (by PIR)")
    for _, r in best_off.iterrows():
        print(f"  {r['Player']:30s}  {r['PPG']:.1f} PPG  {r['APG']:.1f} APG  PIR {r['PIR']:.1f}")

    worst_to = per_game.sort_values("TO_per36", ascending=False).head(5)
    print("\n[MOST TURNOVERS per 36 min]")
    for _, r in worst_to.iterrows():
        print(f"  {r['Player']:30s}  {r['TO_per36']:.2f} TO/36  ({int(r['total_to'])} total)")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading gamecodes ...")
    games = load_gamecodes(TEAM, SEASON)
    games_played = int(games["played"].sum())

    shots_all = load_shot_data(games, SEASON)
    shots_fen = remap_zones(shots_all[shots_all["TEAM"] == TEAM].copy())

    fen           = load_boxscore(TEAM)
    fen_qualified = fen[fen["min_float"] > 3]

    zone_stats = prepare_zone_stats(shots_fen, fen_qualified)
    per_game   = prepare_per_game(fen_qualified)
    eff        = prepare_shooting_efficiency(fen_qualified)

    fig1 = make_fig1_zones_shotchart(zone_stats, shots_fen, games_played)
    fig1.savefig("fenerbahce_zones_shotchart_2025_26.png", dpi=150,
                 bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_zones_shotchart_2025_26.png")

    fig2 = make_fig2_offense(per_game, eff)
    fig2.savefig("fenerbahce_offense_2025_26.png", dpi=150,
                 bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_offense_2025_26.png")

    fig3 = make_fig3_turnovers(per_game)
    fig3.savefig("fenerbahce_turnovers_2025_26.png", dpi=150,
                 bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_turnovers_2025_26.png")

    print_summary(zone_stats, per_game)
