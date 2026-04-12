"""
Fenerbahce Beko — EuroLeague 2025-26 Advanced Analysis
  Figure 1: End-of-quarter shooters (minutes 10, 20, 30, 38-40)
  Figure 2: Second-chance and fast-break shot charts
  Figure 3: Fast-break attempts / scores per game per quarter

Notes:
  - MINUTE is cumulative: Q1=1-10, Q2=11-20, Q3=21-30, Q4=31-40
  - Free throws (COORD=-1,-1) are excluded from shot charts and FG% calculations
  - FT% for end-of-quarter is shown separately using boxscore not shot data
"""

import matplotlib.pyplot as plt

from utils_euroleague import (
load_gamecodes,
    load_or_fetch_shots,
    prepare_eoq_stats,
    prepare_eoq_by_period,
    prepare_fastbreak_per_quarter,
)
from utils_plot import (
    BG,
    plot_eoq_shooters,
    plot_eoq_heatmap,
    plot_situation_shotchart,
    plot_fastbreak_per_quarter,
    make_fig1_eoq

)

from constants import SEASON, TEAM

# ── constants ─────────────────────────────────────────────────────────────────

TEAM = "ULK"

# ── figure assembly ───────────────────────────────────────────────────────────





def make_fig2_situation_shotcharts(shots) -> plt.Figure:
    """Shot location charts for second-chance and fast-break situations.

    Args:
        shots: Output of ``load_shots`` (includes ``is_ft``, ``SECOND_CHANCE``,
            ``FASTBREAK`` columns).

    Returns:
        Matplotlib Figure.
    """
    fig, (ax_sc, ax_fb) = plt.subplots(1, 2, figsize=(14, 9))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Fenerbahce Beko — EuroLeague 2025-26  |  Shot Locations by Situation",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_situation_shotchart(ax_sc, shots, "SECOND_CHANCE", "Second-Chance Shots")
    plot_situation_shotchart(ax_fb, shots, "FASTBREAK",     "Fast-Break Shots")
    fig.tight_layout()
    return fig


def make_fig3_fastbreak_quarters(fb_q) -> plt.Figure:
    """Average fast-break made field goals per game, broken down by quarter.

    Args:
        fb_q: Output of ``prepare_fastbreak_per_quarter``.

    Returns:
        Matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Fenerbahce Beko — EuroLeague 2025-26  |  Fast-Break Volume by Quarter",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_fastbreak_per_quarter(ax, fb_q)
    fig.tight_layout()
    return fig


# ── text summary ──────────────────────────────────────────────────────────────


def print_summary(eoq_stats, shots, fb_q) -> None:
    """Print advanced insights to stdout: EOQ shooters, second-chance, fast-break.

    Args:
        eoq_stats: Output of ``prepare_eoq_stats``.
        shots: Output of ``load_shots``.
        fb_q: Output of ``prepare_fastbreak_per_quarter``.
    """
    print("\n" + "=" * 60)
    print("ADVANCED INSIGHTS — FENERBAHCE 2025-26")
    print("=" * 60)

    print("\n[END-OF-QUARTER SHOOTERS] top 8 by attempts")
    print(f"  {'Player':25s}  {'Att':>4}  {'Mk':>3}  {'FG%':>6}")
    for _, r in eoq_stats.head(8).iterrows():
        print(f"  {r['PLAYER'].split(',')[0]:25s}  {int(r['attempts']):>4}  {int(r['makes']):>3}  {r['FG%']:>5.1f}%")

    print("\n[SECOND-CHANCE SCORES]  (API only tags made shots — no FG% available)")
    sc = shots[(shots["SECOND_CHANCE"] == 1) & ~shots["is_ft"]]
    print(f"  Made FG: {len(sc)}")
    print(f"  Top scorers (by made FG):")
    sc_p = sc.groupby("PLAYER")["made"].sum().reset_index().sort_values("made", ascending=False)
    for _, r in sc_p.head(5).iterrows():
        print(f"    {r['PLAYER'].split(',')[0]:25s}  {int(r['made'])} made FG")

    print("\n[FAST-BREAK SCORES]  (API only tags made shots — no FG% available)")
    fb = shots[(shots["FASTBREAK"] == 1) & ~shots["is_ft"]]
    print(f"  Made FG: {len(fb)}")
    print(f"  Avg made FG per game per quarter:")
    for _, r in fb_q.iterrows():
        print(f"    {r['quarter']}:  {r['avg_makes']:.2f} scored FG/game")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    games = load_gamecodes(SEASON, TEAM)
    shots = load_or_fetch_shots(games=games, team=TEAM, season=SEASON, cache_path="fenerbahce_shots_2025_26.csv")


    eoq_stats     = prepare_eoq_stats(shots)
    eoq_by_period = prepare_eoq_by_period(shots)
    fb_q          = prepare_fastbreak_per_quarter(shots)

    fig1 = make_fig1_eoq(eoq_stats, eoq_by_period)
    fig1.savefig("eoq_2025_2026.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("Saved -> eoq_2025_2026.png")

    fig2 = make_fig2_situation_shotcharts(shots)
    fig2.savefig("shot_areas.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("Saved -> shot_areas.png")

    fig3 = make_fig3_fastbreak_quarters(fb_q)
    fig3.savefig("fenerbahce_fastbreak_quarters_2025_26.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_fastbreak_quarters_2025_26.png")

    print_summary(eoq_stats, shots, fb_q)
