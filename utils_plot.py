"""
Plotting and visualisation utilities for EuroLeague shot data.

Exports colour constants, a half-court drawing helper, and one plotting
function per chart type.  Figure assembly (``make_fig*``) lives in the
analysis scripts; these functions operate on a single ``Axes`` object.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Arc, Circle, Rectangle
from zone_mapping import (
    CORNER_X,
    CORNER_Y,
    RESTRICTED_R,
    SHORT_RANGE_MAX,
    THREE_PT_RADIUS,
)

from utils_euroleague import _short_name
from constants import DPI
import math
# ── colour palette ─────────────────────────────────────────────────────────────

BG: str       = "#1a1a2e"
PANEL_BG: str = "#16213e"
GOLD: str     = "#FFD700"
RED: str      = "#e05252"
GREEN: str    = "#52c77f"
BLUE: str     = "#5288c7"
ORANGE: str   = "#e08c52"
PURPLE: str   = "#9b59b6"

TITLE_KW: dict = dict(color="white", fontsize=13, fontweight="bold", pad=10)

# ── court drawing ──────────────────────────────────────────────────────────────


def draw_half_court(ax: Axes, color: str = "#555577", lw: float = 1.4) -> None:
    """Draw a FIBA/EuroLeague half-court on *ax*.

    Origin is the basket centre; units are centimetres.  All dimensions
    follow FIBA Official Basketball Rules.  Court elements are built as
    individual patches — hoop, backboard, key, free-throw arcs, restricted
    area, three-point line, boundary, centre circle — mirroring the
    structure of the classic NBA patch-based court template but rescaled to
    FIBA dimensions.  The function sets axis limits, aspect ratio, and turns
    the axis off.

    Args:
        ax: Matplotlib axes to draw on.
        color: Line colour for all court markings.
        lw: Line width for all court markings.
    """
    # Basket rim – FIBA internal diameter 450 mm → radius 22.5 cm
    hoop = Circle((0, 0), radius=22.5, linewidth=lw, color=color, fill=False)

    # Backboard – 1.83 m wide, drawn as a thin filled bar
    backboard = Rectangle((-91.5, -20), 183, -4, linewidth=lw, color=color)

    # Key / paint – 4.90 m wide.
    # Depth is measured from the basket (y=0), not from the endline:
    #   FIBA FT-line is 5.80 m from the endline, and the basket centre is
    #   1.575 m from the endline → FT line is 4.225 m = 422 cm from basket.
    ft_y = 422
    paint = Rectangle(
        (-245, 0), 490, ft_y, linewidth=lw, edgecolor=color, facecolor="none",
    )

    # Free-throw arcs (radius 1.80 m, centre at the free-throw line).
    # Solid toward the basket; dashed inside the key.
    ft_top = Arc(
        (0, ft_y), 360, 360, theta1=0, theta2=180, linewidth=lw, color=color,
    )
    ft_bottom = Arc(
        (0, ft_y), 360, 360, theta1=180, theta2=0,
        linewidth=lw, color=color, linestyle="dashed",
    )

    # No-charge restricted-area arc – 1.25 m radius from basket centre
    restricted = Arc(
        (0, 0), 250, 250, theta1=0, theta2=180, linewidth=lw, color=color,
    )

    # Corner three-point lines – 6.60 m from court centre-line, 0.90 m long
    # (FIBA: the parallel segment and the arc do not physically meet;
    #  the arc begins at y ≈ 141 cm when x = 660 cm)
    corner_left  = Rectangle((-660, 0), 0, 90, linewidth=lw, color=color)
    corner_right = Rectangle(( 660, 0), 0, 90, linewidth=lw, color=color)

    # Three-point arc – 6.75 m radius; theta values tuned to align with
    # the corner lines at x = ±660 cm (theta ≈ 12° where the arc crosses x = 660)
    three_arc = Arc(
        (0, 0), 1350, 1350, theta1=12, theta2=168, linewidth=lw, color=color,
    )

    # Half-court boundary – 15.0 m wide × 14.0 m deep
    boundary = Rectangle(
        (-750, 0), 1500, 1400, linewidth=lw, edgecolor=color, facecolor="none",
    )

    # Half-court centre circle – FIBA diameter 3.60 m; lower semicircle only
    centre_circle = Arc(
        (0, 1400), 360, 360, theta1=180, theta2=0, linewidth=lw, color=color,
    )

    for element in [
        hoop, backboard, paint,
        ft_top, ft_bottom,
        restricted,
        corner_left, corner_right, three_arc,
        boundary, centre_circle,
    ]:
        ax.add_patch(element)

    ax.set_xlim(-800, 800)
    ax.set_ylim(-150, 1450)
    ax.set_aspect("equal")
    ax.axis("off")


# ── zone and shot-chart plots ──────────────────────────────────────────────────


def plot_zone_efficiency(ax: Axes, zone_stats: pd.DataFrame) -> None:
    """Horizontal bar chart of FG% per zone.

    Bars are coloured red when FG% < 45 %, green otherwise.  Each bar is
    annotated with the exact percentage and attempt count.

    Args:
        ax: Matplotlib axes to draw on.
        zone_stats: DataFrame with ``label``, ``FG%``, and ``attempts`` columns.
    """
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


def plot_shot_chart(ax: Axes, shots: pd.DataFrame) -> None:
    """Scatter shot chart with makes (green) and misses (red) on a half-court.

    Args:
        ax: Matplotlib axes to draw on.
        shots: Shot DataFrame with ``ZONE``, ``POINTS``, ``COORD_X``, and
            ``COORD_Y`` columns.
    """
    ax.set_facecolor(PANEL_BG)
    draw_half_court(ax)
    fg = shots[shots["ZONE"].str.strip() != ""].copy()
    fg["made"] = fg["POINTS"] > 0
    fg = fg[
        (fg["COORD_X"] >= -750) & (fg["COORD_X"] <= 750) &
        (fg["COORD_Y"] >= -150) & (fg["COORD_Y"] <= 1400)
    ]
    misses = fg[~fg["made"]]
    makes  = fg[fg["made"]]
    ax.scatter(misses["COORD_X"], misses["COORD_Y"], c=RED,   s=10, alpha=0.35, label="Miss")
    ax.scatter(makes["COORD_X"],  makes["COORD_Y"],  c=GREEN, s=10, alpha=0.50, label="Make")
    ax.legend(loc="upper right", fontsize=9, facecolor=PANEL_BG,
              labelcolor="white", edgecolor="none")
    ax.set_title("Shot Chart — All FEN field goal attempts", **TITLE_KW)


# ── zone heatmap ──────────────────────────────────────────────────────────────

# Visual centre of each zone (x, y) in court coordinates (cm).
# Verified to lie inside the correct zone geometry.
_ZONE_LABEL_POS: dict[str, tuple[float, float]] = {
    "A": (0,    55),
    "B": (-215, 270),
    "C": (215,  270),
    "D": (-450, 360),
    "E": (0,    560),
    "F": (450,  360),
    "G": (-620, 480),
    "H": (0,    950),
    "I": (620,  480),
}


def _build_zone_grid(XX: np.ndarray, YY: np.ndarray) -> np.ndarray:
    """Assign zone labels A–I to every point in a 2-D coordinate grid.

    Implements the same geometry as :func:`~zone_mapping.assign_zone` but
    operates on entire NumPy arrays for performance.

    Args:
        XX: 2-D array of x-coordinates in cm.
        YY: 2-D array of y-coordinates in cm.

    Returns:
        2-D ``dtype="U1"`` array of zone labels with the same shape as *XX*.
        Points that lie outside all zones (should not occur within the
        half-court grid) receive the placeholder label ``"X"``.
    """
    d_sq = XX ** 2 + YY ** 2
    is_corner = (np.abs(XX) >= CORNER_X) & (YY <= CORNER_Y)
    is_3pt = is_corner | (d_sq >= THREE_PT_RADIUS ** 2)
    mask_a = d_sq <= RESTRICTED_R ** 2

    zones = np.full(XX.shape, "X", dtype="U1")
    zones[mask_a] = "A"

    # 3-point zones: seed with H (centre), then override the lateral wedges
    three = ~mask_a & is_3pt
    zones[three] = "H"
    zones[three & (XX < -YY)] = "G"
    zones[three & (XX > YY)] = "I"

    # Short-range two-point zones
    short = ~mask_a & ~is_3pt & (d_sq <= SHORT_RANGE_MAX ** 2)
    zones[short & (XX < 0)] = "B"
    zones[short & (XX >= 0)] = "C"

    # Mid-range zones: seed with E (centre), then override lateral wedges
    mid = ~mask_a & ~is_3pt & (d_sq > SHORT_RANGE_MAX ** 2)
    zones[mid] = "E"
    zones[mid & (XX < -YY)] = "D"
    zones[mid & (XX > YY)] = "F"

    return zones


def plot_zone_heatmap(
    ax: Axes,
    shots: pd.DataFrame,
    title: str = "",
    colorbar: bool = True,
) -> None:
    """Half-court zone heatmap coloured by FG%, labelled with makes/attempts/%.

    Each of the nine zones (A–I) is filled on a red–yellow–green scale
    proportional to field-goal percentage.  A text label inside every zone
    shows ``makes/attempts`` and the percentage.  Zones with no recorded
    attempts are drawn in a neutral dark colour.

    Pass the full team shot DataFrame for a team chart, or filter to a single
    player before calling for a per-player chart::

        # team
        plot_zone_heatmap(ax, shots)

        # single player — loop-friendly
        for player, ax in zip(players, axes.ravel()):
            plot_zone_heatmap(ax, shots[shots["PLAYER"] == player],
                              title=player, colorbar=False)

    Args:
        ax: Matplotlib axes to draw on.
        shots: Shot DataFrame with a ``ZONE`` column (already remapped via
            :func:`~zone_mapping.remap_zones`) and a ``made`` boolean column.
            Free throws (blank ``ZONE``) are ignored automatically.
        title: Axes title string.
        colorbar: When ``True`` (default) a thin FG% colour-scale bar is
            added beside the axes.  Set to ``False`` when tiling many charts.
    """
    ax.set_facecolor(PANEL_BG)

    # ── zone statistics ────────────────────────────────────────────────────────
    fg = shots[shots["ZONE"].str.strip() != ""].copy()
    agg = (
        fg.groupby("ZONE")
        .agg(attempts=("made", "count"), makes=("made", "sum"))
        .reset_index()
    )
    agg["pct"] = agg["makes"] / agg["attempts"] * 100
    stat_map: dict[str, tuple[int, int, float]] = {
        row["ZONE"]: (int(row["makes"]), int(row["attempts"]), float(row["pct"]))
        for _, row in agg.iterrows()
    }

    # ── build FG%-coloured grid ────────────────────────────────────────────────
    xs = np.linspace(-750, 750, 400)
    ys = np.linspace(0, 1350, 350)
    XX, YY = np.meshgrid(xs, ys)
    zone_grid = _build_zone_grid(XX, YY)

    pct_grid = np.full(zone_grid.shape, np.nan)
    for zone, (_, _, pct) in stat_map.items():
        pct_grid[zone_grid == zone] = pct

    cmap = plt.cm.RdYlGn.copy()
    cmap.set_bad(color="#2a2a4a")  # neutral dark for zones with no attempts
    mesh = ax.pcolormesh(
        XX, YY, pct_grid,
        cmap=cmap, vmin=0, vmax=100, alpha=0.85,
        shading="auto", zorder=1,
    )

    # ── court outline drawn on top of the heatmap ─────────────────────────────
    draw_half_court(ax, color="#ccccdd", lw=1.6)

    # ── zone labels ────────────────────────────────────────────────────────────
    for zone, (cx, cy) in _ZONE_LABEL_POS.items():
        mk, att, pct = stat_map.get(zone, (0, 0, 0.0))
        if att == 0:
            label = "0/0\n—"
            txt_color = "#888899"
        else:
            label = f"{mk}/{att}\n{pct:.0f}%"
            txt_color = "black" if 25 < pct < 75 else "white"
        ax.text(
            cx, cy, label,
            ha="center", va="center",
            color=txt_color, fontsize=8.5, fontweight="bold",
            zorder=5,
        )

    # ── optional colour scale bar ──────────────────────────────────────────────
    if colorbar:
        cbar = plt.colorbar(mesh, ax=ax, fraction=0.025, pad=0.02)
        cbar.set_ticks([0, 25, 50, 75, 100])
        cbar.set_label("FG%", color="white", fontsize=8)
        cbar.ax.yaxis.set_tick_params(color="white", labelcolor="white")

    if title:
        ax.set_title(title, **TITLE_KW)


# ── player-profile plots ───────────────────────────────────────────────────────


def plot_offensive_players(ax: Axes, per_game: pd.DataFrame) -> None:
    """Stacked horizontal bar of PPG + APG for all players, sorted by PIR.

    Args:
        ax: Matplotlib axes to draw on.
        per_game: DataFrame with ``Player`` (display name), ``PPG``, ``APG``,
            and ``PIR`` columns.
    """
    ax.set_facecolor(PANEL_BG)
    top = per_game.sort_values("PIR", ascending=False)
    y   = np.arange(len(top))
    ax.barh(y, top["PPG"], color=GOLD, label="PPG", alpha=0.9)
    ax.barh(y, top["APG"], left=top["PPG"], color=BLUE, label="APG", alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [_short_name(p) for p in top["Player"]], color="white", fontsize=9,
    )
    for i, (ppg, apg, pir) in enumerate(zip(top["PPG"], top["APG"], top["PIR"])):
        ax.text(
            ppg + apg + 0.3, i, f"PIR {pir:.1f}",
            va="center", color="#cccccc", fontsize=8,
        )
    ax.set_title("Offensive Players — sorted by PIR\n(PPG + APG stacked)", **TITLE_KW)
    ax.legend(fontsize=9, facecolor=PANEL_BG, labelcolor="white", edgecolor="none")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def plot_shooting_efficiency(ax: Axes, eff: pd.DataFrame) -> None:
    """Grouped bar chart of eFG%, FT%, and TS% per player.

    TS% (True Shooting %) accounts for field goals, three-pointers, and free
    throws and is the most comprehensive single-number scoring efficiency
    metric.

    Args:
        ax: Matplotlib axes to draw on.
        eff: DataFrame with ``Player`` (display name), ``eFG%``, ``FT%``, and
            ``TS%`` columns.
    """
    ax.set_facecolor(PANEL_BG)
    x = np.arange(len(eff))
    w = 0.25
    ax.bar(x - w, eff["eFG%"], width=w, color=GOLD,   label="eFG%", alpha=0.9)
    ax.bar(x,     eff["FT%"],  width=w, color=BLUE,   label="FT%",  alpha=0.9)
    ax.bar(x + w, eff["TS%"],  width=w, color=GREEN,  label="TS%",  alpha=0.9)
    ax.axhline(50, color="white", lw=0.8, ls="--", alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [_short_name(p) for p in eff["Player"]],
        rotation=35, ha="right", color="white", fontsize=8,
    )
    ax.set_title("Shooting Efficiency: eFG% / FT% / TS%", **TITLE_KW)
    ax.set_ylabel("Percentage", color="white", fontsize=9)
    ax.legend(fontsize=9, facecolor=PANEL_BG, labelcolor="white", edgecolor="none")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def plot_pir_vs_ts(
    ax: Axes,
    data: pd.DataFrame,
    minutes: bool = True,
) -> None:
    """Scatter plot of PIR (x) vs TS% (y), one dot per player.

    Args:
        ax: Matplotlib axes to draw on.
        data: DataFrame with ``Player`` (display name), ``PIR``, ``TS%``, and
            ``MPG`` columns.
        minutes: When ``True`` (default) the dot area is proportional to
            minutes per game, making high-usage players visually prominent.
            When ``False`` all dots have the same size.
    """
    ax.set_facecolor(PANEL_BG)

    sizes = (data["MPG"] / data["MPG"].max() * 400 + 40) if minutes else 120

    scatter = ax.scatter(
        data["PIR"], data["TS%"],
        s=sizes, c=GOLD, alpha=0.85, edgecolors="#333355", linewidths=0.6,
        zorder=3,
    )

    for _, row in data.iterrows():
        ax.annotate(
            _short_name(row["Player"]),
            xy=(row["PIR"], row["TS%"]),
            xytext=(4, 4), textcoords="offset points",
            color="white", fontsize=7.5, zorder=4,
        )

    # Reference lines at medians
    ax.axvline(data["PIR"].median(), color="white", lw=0.7, ls="--", alpha=0.35)
    ax.axhline(data["TS%"].median(), color="white", lw=0.7, ls="--", alpha=0.35)

    ax.set_xlabel("PIR (Performance Index Rating)", color="white", fontsize=9)
    ax.set_ylabel("TS% (True Shooting %)", color="white", fontsize=9)
    size_note = "  —  dot size = MPG" if minutes else ""
    ax.set_title(f"PIR vs True Shooting%{size_note}", **TITLE_KW)
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)

    if minutes:
        # Legend proxy showing small / large dot meaning
        for mpg, label in [(data["MPG"].min(), "low MPG"), (data["MPG"].max(), "high MPG")]:
            s = mpg / data["MPG"].max() * 400 + 40
            ax.scatter([], [], s=s, c=GOLD, alpha=0.85, label=label)
        ax.legend(
            fontsize=8, facecolor=PANEL_BG, labelcolor="white",
            edgecolor="none", loc="lower right",
        )


def plot_turnovers(ax: Axes, per_game: pd.DataFrame) -> None:
    """Horizontal bar of turnovers per 36 minutes, sorted descending.

    Bars are coloured red (> 3.5), orange (> 2.5), or gold otherwise.

    Args:
        ax: Matplotlib axes to draw on.
        per_game: DataFrame with ``Player`` (display name), ``TO_per36``,
            and ``GP`` columns.
    """
    ax.set_facecolor(PANEL_BG)
    to_df  = per_game.sort_values("TO_per36", ascending=False)
    colors = [RED if v > 3.5 else ORANGE if v > 2.5 else GOLD for v in to_df["TO_per36"]]
    ax.barh(
        [_short_name(p) for p in to_df["Player"]],
        to_df["TO_per36"], color=colors, edgecolor="none",
    )
    for i, (v, gp) in enumerate(zip(to_df["TO_per36"], to_df["GP"])):
        ax.text(v + 0.05, i, f"{v:.2f}  ({gp} GP)", va="center", color="white", fontsize=9)
    ax.axvline(3.5, color=RED, lw=0.8, ls="--", alpha=0.6)
    ax.set_title("Turnovers per 36 min  (red > 3.5)", **TITLE_KW)
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


# ── end-of-quarter plots ───────────────────────────────────────────────────────


def plot_eoq_shooters(
    ax: Axes,
    eoq_stats: pd.DataFrame,
    top_n: int = 12,
) -> None:
    """Horizontal bar: attempts (grey background) with makes (gold fill) and FG% label.

    Args:
        ax: Matplotlib axes to draw on.
        eoq_stats: DataFrame with ``PLAYER``, ``attempts``, ``makes``, and
            ``FG%`` columns.
        top_n: Number of players to show.
    """
    ax.set_facecolor(PANEL_BG)
    top   = eoq_stats.head(top_n)
    y     = np.arange(len(top))
    names = [p.split(",")[0] for p in top["PLAYER"]]

    ax.barh(y, top["attempts"], color="#334466", edgecolor="none", label="Attempts")
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


def plot_eoq_heatmap(
    ax: Axes,
    eoq_by_period: pd.DataFrame,
    top_n: int = 10,
) -> None:
    """Heatmap coloured by FG%; each cell shows makes/attempts and FG%.

    Args:
        ax: Matplotlib axes to draw on.
        eoq_by_period: DataFrame with ``PLAYER``, ``period``, ``attempts``,
            and ``makes`` columns.
        top_n: Number of players (by total attempts) to display.
    """
    ax.set_facecolor(PANEL_BG)
    periods = ["End Q1", "End Q2", "End Q3", "End Q4"]

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


# ── situation shot-chart plots ─────────────────────────────────────────────────


def plot_situation_shotchart(
    ax: Axes,
    shots: pd.DataFrame,
    flag_col: str,
    title: str,
) -> None:
    """Shot chart for a binary situation flag (FASTBREAK or SECOND_CHANCE).

    The API only flags *made* shots with situation tags, so this chart shows
    scored locations only — no FG% can be computed.

    Args:
        ax: Matplotlib axes to draw on.
        shots: Shot DataFrame with ``is_ft``, ``COORD_X``, ``COORD_Y``, and
            a column named *flag_col*.
        flag_col: Column name of the binary flag (e.g. ``"FASTBREAK"``).
        title: Axes title prefix.
    """
    ax.set_facecolor(PANEL_BG)
    draw_half_court(ax)
    makes = shots[
        (shots[flag_col] == 1) & ~shots["is_ft"] &
        (shots["COORD_X"] >= -750) & (shots["COORD_X"] <= 750) &
        (shots["COORD_Y"] >= -150) & (shots["COORD_Y"] <= 1400)
    ].copy()
    ax.scatter(makes["COORD_X"], makes["COORD_Y"], c=GREEN, s=22, alpha=0.80, zorder=4)
    ax.set_title(f"{title}\nScored locations only  (n={len(makes)} made FG)", **TITLE_KW)


def plot_fastbreak_per_quarter(ax: Axes, fb_q: pd.DataFrame) -> None:
    """Bar chart of average fast-break made field goals per game per quarter.

    The API only tags made fast-break shots, so these are scored FGs only.

    Args:
        ax: Matplotlib axes to draw on.
        fb_q: DataFrame with ``quarter`` and ``avg_makes`` columns.
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
        "Fast-Break Scores per Game per Quarter\n"
        "(made FG only — API does not tag missed fast breaks)",
        **TITLE_KW,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)


def make_fig1_eoq(eoq_stats, eoq_by_period, team_name, season) -> plt.Figure:
    """End-of-quarter shooting: bar chart of top shooters + FG% heatmap by period.

    Args:
        eoq_stats: Output of ``prepare_eoq_stats``.
        eoq_by_period: Output of ``prepare_eoq_by_period``.

    Returns:
        Matplotlib Figure.
    """
    fig, (ax_bar, ax_heat) = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"{team_name} — EuroLeague {season}-{season+1}  |  End-of-Quarter Shooting",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_eoq_shooters(ax_bar, eoq_stats)
    plot_eoq_heatmap(ax_heat, eoq_by_period)
    fig.tight_layout()
    return fig





def heatmap_shot_team(shots, team):
    # Team heatmap
    _fig, _ax = plt.subplots(figsize=(8, 9), facecolor=BG)
    _ax.set_facecolor(PANEL_BG)
    plot_zone_heatmap(_ax, shots, title=f"{team} — Shot Zone Heatmap")
    _fig.savefig(
        "docs/images/zone_heatmap_team.png",
        dpi=DPI, bbox_inches="tight", facecolor=_fig.get_facecolor(),
    )
    plt.close(_fig)

def heatmap_shot_players(
    shots: pd.DataFrame,
    players_data: list[dict],
    team: str = "MIX",
) -> None:
    """Save a grid heatmap and individual heatmaps for each player in *players_data*.

    Uses ``box_name`` (boxscore format) from each player dict to correctly
    filter the shots DataFrame, and ``name`` (CSV display name) for titles.

    Args:
        shots: Shot DataFrame with a ``PLAYER`` column in boxscore format.
        players_data: List of player dicts as returned by
            :func:`~utils_euroleague.top_players_profile`.  Each dict must
            have ``name``, ``box_name``, and ``dorsal`` keys.
        team: Three-letter team code used to name the individual files.
    """
    n    = len(players_data)
    cols = 3
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5.5, rows * 6.5), facecolor=BG)
    axes_flat = axes.ravel() if n > 1 else [axes]

    for i, player in enumerate(players_data):
        ax = axes_flat[i]
        ax.set_facecolor(PANEL_BG)
        player_shots = shots[shots["PLAYER"] == player["box_name"]]
        plot_zone_heatmap(
            ax,
            player_shots,
            title=f"#{player['dorsal']} {_short_name(player['name'])}",
            colorbar=False,
        )

    for ax in axes_flat[n:]:
        ax.set_visible(False)

    fig.tight_layout(pad=1.5)
    fig.savefig(
        "docs/images/zone_heatmap_players.png",
        dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor(),
    )
    plt.close(fig)

    # Individual per-player files — {TEAM}_heatmap_player_{num}.png
    for num, player in enumerate(players_data, start=1):
        fig, ax = plt.subplots(figsize=(7, 9), facecolor=BG)
        ax.set_facecolor(PANEL_BG)
        player_shots = shots[shots["PLAYER"] == player["box_name"]]
        plot_zone_heatmap(
            ax,
            player_shots,
            title=f"{_short_name(player['name'])} — #{player['dorsal']}",
            colorbar=True,
        )
        fig.savefig(
            f"docs/images/{team}_heatmap_player_{num}.png",
            dpi=DPI, bbox_inches="tight", facecolor=fig.get_facecolor(),
        )
        plt.close(fig)


def make_fig2_offense(
    per_game: pd.DataFrame,
    eff: pd.DataFrame,
    team: str,
    season: int,
) -> plt.Figure:
    """Offensive player overview: PIR bar chart and shooting efficiency chart.

    Args:
        per_game: Output of :func:`~utils_euroleague.player_per_game`.
        eff: Output of :func:`~utils_euroleague.player_shooting_eff`.
        team: Three-letter team code used in the figure title.
        season: Season start year (e.g. 2025 for the 2025-26 season).

    Returns:
        Matplotlib Figure ready for ``savefig``.
    """
    fig, (ax_off, ax_eff) = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"{team} — EuroLeague {season}-{season + 1}  |  Player Offensive Overview",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_offensive_players(ax_off, per_game)
    plot_shooting_efficiency(ax_eff, eff)
    fig.tight_layout()
    return fig


def make_fig3_pir_ts(
    per_game: pd.DataFrame,
    eff: pd.DataFrame,
    team: str,
    season: int,
    minutes: bool = True,
) -> plt.Figure:
    """PIR vs True Shooting% scatter plot, one dot per active-roster player.

    Args:
        per_game: Output of :func:`~utils_euroleague.player_per_game`.
        eff: Output of :func:`~utils_euroleague.player_shooting_eff`.
        team: Three-letter team code used in the figure title.
        season: Season start year (e.g. 2025 for the 2025-26 season).
        minutes: When ``True`` dot size scales with minutes per game.

    Returns:
        Matplotlib Figure ready for ``savefig``.
    """
    scatter_data = per_game.merge(eff[["Player", "TS%"]], on="Player", how="inner")

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"{team} — EuroLeague {season}-{season + 1}  |  PIR vs True Shooting%",
        color="white", fontsize=15, fontweight="bold", y=1.01,
    )
    plot_pir_vs_ts(ax, scatter_data, minutes=minutes)
    fig.tight_layout()
    return fig