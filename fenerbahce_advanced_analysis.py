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

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, Circle

# ── constants ─────────────────────────────────────────────────────────────────

TEAM = "ULK"

EOQ_MINUTES   = [10, 20, 30, 38, 39, 40]   # end-of-quarter minutes to analyse
EOQ_LABELS    = {10: "End Q1", 20: "End Q2", 30: "End Q3", 38: "End Q4", 39: "End Q4", 40: "End Q4"}
QUARTER_MAP   = {**{m: "Q1" for m in range(1, 11)},
                 **{m: "Q2" for m in range(11, 21)},
                 **{m: "Q3" for m in range(21, 31)},
                 **{m: "Q4" for m in range(31, 41)}}

BG       = "#1a1a2e"
PANEL_BG = "#16213e"
GOLD     = "#FFD700"
RED      = "#e05252"
GREEN    = "#52c77f"
BLUE     = "#5288c7"
ORANGE   = "#e08c52"
PURPLE   = "#9b59b6"

TITLE_KW = dict(color="white", fontsize=13, fontweight="bold", pad=10)

# ── data loading ──────────────────────────────────────────────────────────────

def load_shots() -> pd.DataFrame:
    shots = pd.read_csv("fenerbahce_shots_2025_26.csv")
    fen = shots[shots["TEAM"] == TEAM].copy()
    fen["made"]    = fen["POINTS"] > 0
    fen["is_ft"]   = fen["COORD_X"] == -1
    fen["quarter"] = fen["MINUTE"].map(QUARTER_MAP).fillna("OT")
    return fen


def load_boxscore() -> pd.DataFrame:
    box = pd.read_csv("fenerbahce_boxscores_2025_26.csv")
    return box[(box["Team"] == TEAM) & (box["Player"] != "Total")].copy()

# ── data preparation ──────────────────────────────────────────────────────────

def prepare_eoq_stats(shots: pd.DataFrame) -> pd.DataFrame:
    """End-of-quarter field goal stats per player."""
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
    """End-of-quarter attempts breakdown per player per period."""
    eoq = shots[shots["MINUTE"].isin(EOQ_MINUTES) & ~shots["is_ft"]].copy()
    eoq["period"] = eoq["MINUTE"].map(EOQ_LABELS)
    return (
        eoq.groupby(["PLAYER", "period"])
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )


def prepare_fastbreak_per_quarter(shots: pd.DataFrame) -> pd.DataFrame:
    """Average fast-break FG attempts and makes per game per quarter."""
    fb = shots[(shots["FASTBREAK"] == 1) & ~shots["is_ft"]].copy()
    per_game_q = (
        fb.groupby(["Gamecode", "quarter"])
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    avg = (
        per_game_q.groupby("quarter")
        .agg(avg_makes=("makes", "mean"))
        .reindex(["Q1", "Q2", "Q3", "Q4"])
        .reset_index()
    )
    return avg

# ── court drawing ─────────────────────────────────────────────────────────────

def draw_half_court(ax, color="#555577", lw=1.4):
    paint_w, paint_h = 490, 580
    ax.plot([-750, 750, 750, -750, -750], [0, 0, 1400, 1400, 0], color=color, lw=lw)
    ax.add_patch(Circle((0, 0), radius=22, linewidth=lw, color=color, fill=False))
    ax.plot([-90, 90], [-15, -15], color=color, lw=lw)
    ax.add_patch(patches.Rectangle(
        (-paint_w / 2, 0), paint_w, paint_h,
        linewidth=lw, edgecolor=color, facecolor="none",
    ))
    ax.add_patch(Arc(
        (0, paint_h), width=360, height=360, angle=0,
        theta1=180, theta2=360, color=color, lw=lw,
    ))
    ax.add_patch(Arc(
        (0, 0), width=675 * 2, height=675 * 2, angle=0,
        theta1=12, theta2=168, color=color, lw=lw,
    ))
    ax.plot([-660, -660], [0, 90], color=color, lw=lw)
    ax.plot([660, 660],   [0, 90], color=color, lw=lw)
    ax.set_xlim(-800, 800)
    ax.set_ylim(-150, 1450)
    ax.set_aspect("equal")
    ax.axis("off")

# ── plot functions ────────────────────────────────────────────────────────────

def plot_eoq_shooters(ax, eoq_stats: pd.DataFrame, top_n: int = 12) -> None:
    """Horizontal bar: attempts (outline) with makes (filled) and FG% label."""
    ax.set_facecolor(PANEL_BG)
    top  = eoq_stats.head(top_n)
    y    = np.arange(len(top))
    names = [p.split(",")[0] for p in top["PLAYER"]]

    # Grey background = total attempts
    ax.barh(y, top["attempts"], color="#334466", edgecolor="none", label="Attempts")
    # Gold fill = makes
    ax.barh(y, top["makes"], color=GOLD, edgecolor="none", alpha=0.9, label="Makes")

    for i, (att, mk, fg) in enumerate(zip(top["attempts"], top["makes"], top["FG%"])):
        ax.text(att + 0.15, i, f"{fg:.0f}%  ({mk}/{att})", va="center", color="white", fontsize=8)

    ax.set_yticks(y)
    ax.set_yticklabels(names, color="white", fontsize=9)
    ax.set_xlim(0, top["attempts"].max() * 1.55)
    ax.set_title(
        "End-of-Quarter Shooters\n(minutes 10, 20, 30, 38-40  —  FG only)",
        **TITLE_KW,
    )
    ax.legend(fontsize=8, facecolor=PANEL_BG, labelcolor="white", edgecolor="none")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def plot_eoq_heatmap(ax, eoq_by_period: pd.DataFrame, top_n: int = 10) -> None:
    """Heatmap coloured by FG%; each cell shows 'makes/att' on line 1 and 'FG%' on line 2."""
    ax.set_facecolor(PANEL_BG)
    periods = ["End Q1", "End Q2", "End Q3", "End Q4"]

    # Keep only top players by total attempts
    totals = eoq_by_period.groupby("PLAYER")["attempts"].sum().nlargest(top_n)
    top_players = totals.index.tolist()

    filtered = eoq_by_period[eoq_by_period["PLAYER"].isin(top_players)]
    pivot_att = (
        filtered.pivot_table(index="PLAYER", columns="period", values="attempts", fill_value=0)
        .reindex(columns=periods, fill_value=0)
        .loc[top_players]
    )
    pivot_mk = (
        filtered.pivot_table(index="PLAYER", columns="period", values="makes", fill_value=0)
        .reindex(columns=periods, fill_value=0)
        .loc[top_players]
    )
    # FG% matrix; NaN where no attempts
    with np.errstate(invalid="ignore"):
        pivot_pct = np.where(
            pivot_att.values > 0,
            pivot_mk.values / pivot_att.values * 100,
            np.nan,
        )

    im = ax.imshow(pivot_pct, aspect="auto", cmap="RdYlGn", vmin=0, vmax=100)
    ax.set_xticks(range(len(periods)))
    ax.set_xticklabels(periods, color="white", fontsize=9)
    ax.set_yticks(range(len(top_players)))
    ax.set_yticklabels([p.split(",")[0] for p in top_players], color="white", fontsize=9)

    for i in range(len(top_players)):
        for j in range(len(periods)):
            att = int(pivot_att.values[i, j])
            mk  = int(pivot_mk.values[i, j])
            pct = pivot_pct[i, j]
            if att > 0:
                # Choose text colour for contrast against the colourmap
                txt_color = "black" if 25 < pct < 75 else "white"
                ax.text(j, i - 0.15, f"{mk}/{att}",
                        ha="center", va="center", color=txt_color, fontsize=8, fontweight="bold")
                ax.text(j, i + 0.22, f"{pct:.0f}%",
                        ha="center", va="center", color=txt_color, fontsize=7.5)

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.yaxis.set_tick_params(color="white")
    cbar.set_label("FG%", color="white", fontsize=8)
    ax.set_title("End-of-Quarter FG% by Period\n(makes / attempts)", **TITLE_KW)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_situation_shotchart(ax, shots: pd.DataFrame, flag_col: str, title: str) -> None:
    """Shot chart for a binary situation flag (FASTBREAK or SECOND_CHANCE).
    NOTE: the API only flags makes with these situations — misses are absent,
    so this chart shows scored locations only (no FG% can be computed).
    """
    ax.set_facecolor(PANEL_BG)
    draw_half_court(ax)
    makes = shots[(shots[flag_col] == 1) & ~shots["is_ft"] &
                  (shots["COORD_X"] >= -750) & (shots["COORD_X"] <= 750) &
                  (shots["COORD_Y"] >= -150) & (shots["COORD_Y"] <= 1400)].copy()
    n = len(makes)
    ax.scatter(makes["COORD_X"], makes["COORD_Y"], c=GREEN, s=22, alpha=0.80, zorder=4)
    ax.set_title(f"{title}\nScored locations only  (n={n} made FG)", **TITLE_KW)


def plot_fastbreak_per_quarter(ax, fb_q: pd.DataFrame) -> None:
    """Bar: avg fast-break made FG per game per quarter.
    NOTE: the API only flags makes — these are scored fast-break field goals only.
    """
    ax.set_facecolor(PANEL_BG)
    quarters = fb_q["quarter"].tolist()
    x = np.arange(len(quarters))

    bars = ax.bar(x, fb_q["avg_makes"], width=0.5, color=GREEN, alpha=0.9)
    for bar, v in zip(bars, fb_q["avg_makes"]):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.03, f"{v:.2f}",
                ha="center", color="white", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(quarters, color="white", fontsize=11)
    ax.set_ylabel("Avg made FG per game", color="white", fontsize=9)
    ax.set_title(
        "Fast-Break Scores per Game per Quarter\n(made FG only — API does not tag missed fast breaks)",
        **TITLE_KW,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)

# ── figure assembly ───────────────────────────────────────────────────────────

def make_fig1_eoq(eoq_stats, eoq_by_period):
    fig, (ax_bar, ax_heat) = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Fenerbahce Beko — EuroLeague 2025-26  |  End-of-Quarter Shooting",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_eoq_shooters(ax_bar, eoq_stats)
    plot_eoq_heatmap(ax_heat, eoq_by_period)
    fig.tight_layout()
    return fig


def make_fig2_situation_shotcharts(shots):
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


def make_fig3_fastbreak_quarters(fb_q):
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

def print_summary(eoq_stats, shots, fb_q):
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
    shots = load_shots()

    eoq_stats     = prepare_eoq_stats(shots)
    eoq_by_period = prepare_eoq_by_period(shots)
    fb_q          = prepare_fastbreak_per_quarter(shots)

    fig1 = make_fig1_eoq(eoq_stats, eoq_by_period)
    fig1.savefig("fenerbahce_eoq_2025_26.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_eoq_2025_26.png")

    fig2 = make_fig2_situation_shotcharts(shots)
    fig2.savefig("fenerbahce_situation_shots_2025_26.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_situation_shots_2025_26.png")

    fig3 = make_fig3_fastbreak_quarters(fb_q)
    fig3.savefig("fenerbahce_fastbreak_quarters_2025_26.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("Saved -> fenerbahce_fastbreak_quarters_2025_26.png")

    print_summary(eoq_stats, shots, fb_q)
