"""
Fenerbahce Beko — EuroLeague 2025-26 Analysis
  Figure 1: Zone FG% bar chart + shot chart
  Figure 2: Key offensive players + shooting efficiency (eFG% vs FT%)
  Figure 3: Turnovers per 36 min

Zone labels verified against coordinate data (API units ~cm from basket):
  A = Under basket       B = Left paint          C = Right paint
  D = Centre-left mid    E = Right baseline mid   F = Left mid-range
  G = Centre-right mid   H = Left wing 3PT        I = Top / right 3PT
FT% comes from boxscore totals — the shot API only logs made free throws.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, Circle
from euroleague_api.shot_data import ShotData
from euroleague_api.EuroLeagueData import EuroLeagueData

# ── constants ─────────────────────────────────────────────────────────────────

TEAM   = "ULK"
SEASON = 2025

ZONE_LABELS = {
    "A": "Under basket",
    "B": "Left paint",
    "C": "Right paint",
    "D": "Centre-left mid-range",
    "E": "Right baseline mid-range",
    "F": "Left mid-range",
    "G": "Centre-right mid-range",
    "H": "Left wing 3PT",
    "I": "Top / right 3PT",
}

BG       = "#1a1a2e"
PANEL_BG = "#16213e"
GOLD     = "#FFD700"
RED      = "#e05252"
GREEN    = "#52c77f"
BLUE     = "#5288c7"
ORANGE   = "#e08c52"

TITLE_KW = dict(color="white", fontsize=13, fontweight="bold", pad=10)

# ── data loading ──────────────────────────────────────────────────────────────

def load_gamecodes() -> pd.DataFrame:
    base = EuroLeagueData()
    games = base.get_gamecodes_season(SEASON)
    return games[(games["homecode"] == TEAM) | (games["awaycode"] == TEAM)].reset_index(drop=True)


def load_shot_data(games: pd.DataFrame, cache_path: str = "fenerbahce_shots_2025_26.csv") -> pd.DataFrame:
    """Load from cache if available, otherwise fetch from API and save."""
    if os.path.exists(cache_path):
        print(f"Loading shot data from cache: {cache_path}")
        return pd.read_csv(cache_path)

    print(f"Fetching shot data for {len(games)} games from API ...")
    sd = ShotData()
    frames = []
    for _, row in games.iterrows():
        gc = int(row["gameCode"])
        try:
            frames.append(sd.get_game_shot_data(SEASON, gc))
        except Exception as e:
            print(f"  WARNING game {gc}: {e}")
    shots_all = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    shots_all.to_csv(cache_path, index=False)
    return shots_all


def load_boxscore(path: str = "fenerbahce_boxscores_2025_26.csv") -> pd.DataFrame:
    box = pd.read_csv(path)
    fen = box[(box["Team"] == TEAM) & (box["Player"] != "Total")].copy()
    fen["min_float"] = fen["Minutes"].apply(_minutes_to_float)
    return fen


def _minutes_to_float(m) -> float:
    try:
        parts = str(m).split(":")
        return int(parts[0]) + int(parts[1]) / 60
    except Exception:
        return 0.0


# ── data preparation ──────────────────────────────────────────────────────────

def prepare_zone_stats(shots: pd.DataFrame, fen_qualified: pd.DataFrame) -> pd.DataFrame:
    """Zone FG% from shot data + FT% from boxscore (shot API omits missed FTs)."""
    fg = shots[shots["ZONE"].str.strip() != ""].copy()
    fg["made"] = fg["POINTS"] > 0

    zone_stats = (
        fg.groupby("ZONE")
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    zone_stats["FG%"]   = zone_stats["makes"] / zone_stats["attempts"] * 100
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


def prepare_per_game(fen_qualified: pd.DataFrame, min_gp: int = 5) -> pd.DataFrame:
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


def prepare_shooting_efficiency(fen_qualified: pd.DataFrame, min_gp: int = 5) -> pd.DataFrame:
    eff = fen_qualified.groupby("Player").agg(
        GP=("Gamecode",            "nunique"),
        FGM2=("FieldGoalsMade2",   "sum"),
        FGA2=("FieldGoalsAttempted2", "sum"),
        FGM3=("FieldGoalsMade3",   "sum"),
        FGA3=("FieldGoalsAttempted3", "sum"),
        FTM=("FreeThrowsMade",     "sum"),
        FTA=("FreeThrowsAttempted","sum"),
    ).reset_index()
    eff = eff[eff["GP"] >= min_gp].copy()
    eff["FGA"]  = eff["FGA2"] + eff["FGA3"]
    eff = eff[eff["FGA"] > 0]
    eff["eFG%"] = (eff["FGM2"] + eff["FGM3"] + 0.5 * eff["FGM3"]) / eff["FGA"] * 100
    eff["FT%"]  = eff.apply(lambda r: r["FTM"] / r["FTA"] * 100 if r["FTA"] > 0 else 0, axis=1)
    return eff.sort_values("eFG%", ascending=False)


# ── court drawing ─────────────────────────────────────────────────────────────

def draw_half_court(ax, color="#555577", lw=1.4):
    """EuroLeague half-court. Origin = basket centre, units ~cm."""
    paint_w, paint_h = 490, 580

    ax.plot([-750, 750, 750, -750, -750], [0, 0, 1400, 1400, 0], color=color, lw=lw)

    ax.add_patch(Circle((0, 0), radius=22, linewidth=lw, color=color, fill=False))
    ax.plot([-90, 90], [-15, -15], color=color, lw=lw)

    ax.add_patch(patches.Rectangle(
        (-paint_w / 2, 0), paint_w, paint_h,
        linewidth=lw, edgecolor=color, facecolor="none",
    ))

    # Free-throw circle — bottom half only so it stays inside the key
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

def plot_zone_efficiency(ax, zone_stats: pd.DataFrame) -> None:
    ax.set_facecolor(PANEL_BG)
    colors = [RED if v < 45 else GREEN for v in zone_stats["FG%"]]
    bars = ax.barh(zone_stats["label"], zone_stats["FG%"], color=colors, edgecolor="none")
    for bar, att, fg in zip(bars, zone_stats["attempts"], zone_stats["FG%"]):
        ax.text(
            bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{fg:.1f}%  (n={int(att)})", va="center", color="white", fontsize=8,
        )
    ax.set_xlim(0, 100)
    ax.axvline(50, color="white", lw=0.8, ls="--", alpha=0.4)
    ax.set_title("FG% by Zone  (red < 45%)", **TITLE_KW)
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def plot_shot_chart(ax, shots: pd.DataFrame) -> None:
    ax.set_facecolor(PANEL_BG)
    draw_half_court(ax)
    fg = shots[shots["ZONE"].str.strip() != ""].copy()
    fg["made"] = fg["POINTS"] > 0
    fg = fg[(fg["COORD_X"] >= -750) & (fg["COORD_X"] <= 750) &
            (fg["COORD_Y"] >= -150) & (fg["COORD_Y"] <= 1400)]
    misses = fg[~fg["made"]]
    makes  = fg[fg["made"]]
    ax.scatter(misses["COORD_X"], misses["COORD_Y"], c=RED,   s=10, alpha=0.35, label="Miss")
    ax.scatter(makes["COORD_X"],  makes["COORD_Y"],  c=GREEN, s=10, alpha=0.50, label="Make")
    ax.legend(loc="upper right", fontsize=9, facecolor=PANEL_BG,
              labelcolor="white", edgecolor="none")
    ax.set_title("Shot Chart — All FEN field goal attempts", **TITLE_KW)


def plot_offensive_players(ax, per_game: pd.DataFrame) -> None:
    ax.set_facecolor(PANEL_BG)
    top = per_game.sort_values("PIR", ascending=False).head(10)
    y   = np.arange(len(top))
    ax.barh(y, top["PPG"], color=GOLD, label="PPG", alpha=0.9)
    ax.barh(y, top["APG"], left=top["PPG"], color=BLUE, label="APG", alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([p.split(",")[0] for p in top["Player"]], color="white", fontsize=9)
    for i, (ppg, apg, pir) in enumerate(zip(top["PPG"], top["APG"], top["PIR"])):
        ax.text(ppg + apg + 0.3, i, f"PIR {pir:.1f}", va="center", color="#cccccc", fontsize=8)
    ax.set_title("Key Offensive Players\n(sorted by PIR — PPG + APG)", **TITLE_KW)
    ax.legend(fontsize=9, facecolor=PANEL_BG, labelcolor="white", edgecolor="none")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def plot_shooting_efficiency(ax, eff: pd.DataFrame) -> None:
    ax.set_facecolor(PANEL_BG)
    x = np.arange(len(eff))
    ax.bar(x - 0.2, eff["eFG%"], width=0.38, color=GOLD, label="eFG%", alpha=0.9)
    ax.bar(x + 0.2, eff["FT%"],  width=0.38, color=BLUE, label="FT%",  alpha=0.9)
    ax.axhline(50, color="white", lw=0.8, ls="--", alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [p.split(",")[0] for p in eff["Player"]],
        rotation=35, ha="right", color="white", fontsize=8,
    )
    ax.set_title("Shooting Efficiency: eFG% vs FT%", **TITLE_KW)
    ax.set_ylabel("Percentage", color="white", fontsize=9)
    ax.legend(fontsize=9, facecolor=PANEL_BG, labelcolor="white", edgecolor="none")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def plot_turnovers(ax, per_game: pd.DataFrame) -> None:
    ax.set_facecolor(PANEL_BG)
    to_df   = per_game.sort_values("TO_per36", ascending=False).head(10)
    colors  = [RED if v > 3.5 else ORANGE if v > 2.5 else GOLD for v in to_df["TO_per36"]]
    ax.barh(
        to_df["Player"].apply(lambda p: p.split(",")[0]),
        to_df["TO_per36"], color=colors, edgecolor="none",
    )
    for i, (v, gp) in enumerate(zip(to_df["TO_per36"], to_df["GP"])):
        ax.text(v + 0.05, i, f"{v:.2f}  ({gp} GP)", va="center", color="white", fontsize=9)
    ax.axvline(3.5, color=RED, lw=0.8, ls="--", alpha=0.6)
    ax.set_title("Turnovers per 36 min  (red > 3.5)", **TITLE_KW)
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


# ── figure assembly ───────────────────────────────────────────────────────────

def make_fig1_zones_shotchart(zone_stats, shots, games_played):
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


def make_fig2_offense(per_game, eff):
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


def make_fig3_turnovers(per_game):
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

def print_summary(zone_stats: pd.DataFrame, per_game: pd.DataFrame) -> None:
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
    games = load_gamecodes()
    games_played = int(games["played"].sum())

    shots_all    = load_shot_data(games)
    shots_fen    = shots_all[shots_all["TEAM"] == TEAM].copy()

    fen          = load_boxscore()
    fen_qualified = fen[fen["min_float"] > 3]

    zone_stats   = prepare_zone_stats(shots_fen, fen_qualified)
    per_game     = prepare_per_game(fen_qualified)
    eff          = prepare_shooting_efficiency(fen_qualified)

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
