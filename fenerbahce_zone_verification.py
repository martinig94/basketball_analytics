"""
Per-zone shot verification for Fenerbahce 2025-26.
One half-court per zone showing every shot (make/miss).
Free throws (zone " ", coords -1,-1) are shown in a separate axes as a bar.
All shots outside court boundary are excluded.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, Circle

# ── court drawing ─────────────────────────────────────────────────────────────

def draw_half_court(ax, color="#555577", lw=1.4):
    paint_w, paint_h = 490, 580

    ax.plot([-750, 750, 750, -750, -750], [0, 0, 1400, 1400, 0], color=color, lw=lw)

    basket = Circle((0, 0), radius=22, linewidth=lw, color=color, fill=False)
    ax.add_patch(basket)
    ax.plot([-90, 90], [-15, -15], color=color, lw=lw)  # backboard

    rect = patches.Rectangle(
        (-paint_w / 2, 0), paint_w, paint_h,
        linewidth=lw, edgecolor=color, facecolor="none",
    )
    ax.add_patch(rect)

    # Free-throw circle — bottom half only (stays inside key)
    ft_arc = Arc(
        (0, paint_h), width=360, height=360, angle=0,
        theta1=180, theta2=360, color=color, lw=lw,
    )
    ax.add_patch(ft_arc)

    # 3-point arc + corner lines
    three_arc = Arc(
        (0, 0), width=675 * 2, height=675 * 2, angle=0,
        theta1=12, theta2=168, color=color, lw=lw,
    )
    ax.add_patch(three_arc)
    ax.plot([-660, -660], [0, 90], color=color, lw=lw)
    ax.plot([660, 660], [0, 90], color=color, lw=lw)

    ax.set_xlim(-800, 800)
    ax.set_ylim(-150, 1450)
    ax.set_aspect("equal")
    ax.axis("off")


# ── load data ─────────────────────────────────────────────────────────────────

shots = pd.read_csv("fenerbahce_shots_2025_26.csv")
fen = shots[shots["TEAM"] == "ULK"].copy()
fen["made"] = fen["POINTS"] > 0

# Field goal attempts only — exclude zone " " (FT placeholder at -1,-1)
# and anything outside court boundary
fg = fen[fen["ZONE"].str.strip() != ""].copy()
in_bounds = (
    (fg["COORD_X"] >= -750) & (fg["COORD_X"] <= 750) &
    (fg["COORD_Y"] >= -150) & (fg["COORD_Y"] <= 1400)
)
excluded = (~in_bounds).sum()
if excluded:
    print(f"Excluded {excluded} shots outside court boundary")
fg = fg[in_bounds].copy()

# Free throw totals from boxscore (shot data only logs made FTs)
box = pd.read_csv("fenerbahce_boxscores_2025_26.csv")
fen_box = box[(box["Team"] == "ULK") & (box["Player"] != "Total")]
ft_made  = int(fen_box["FreeThrowsMade"].sum())
ft_att   = int(fen_box["FreeThrowsAttempted"].sum())
ft_pct   = ft_made / ft_att * 100 if ft_att > 0 else 0

zones = sorted(fg["ZONE"].unique())
n_zones = len(zones)
print(f"Zones to plot: {zones}")
print(f"Free throws (boxscore): {ft_made}/{ft_att}  ({ft_pct:.1f}%)")

# ── layout: one subplot per zone + 1 for free throws ─────────────────────────

n_cols = 4
n_rows = int(np.ceil((n_zones + 1) / n_cols))  # +1 for FT panel

BG       = "#1a1a2e"
PANEL_BG = "#16213e"
RED      = "#e05252"
GREEN    = "#52c77f"
GOLD     = "#FFD700"

fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 6))
fig.patch.set_facecolor(BG)
axes_flat = axes.flatten()

for idx, zone in enumerate(zones):
    ax = axes_flat[idx]
    ax.set_facecolor(PANEL_BG)
    draw_half_court(ax)

    z = fg[fg["ZONE"] == zone]
    misses = z[~z["made"]]
    makes  = z[z["made"]]

    ax.scatter(misses["COORD_X"], misses["COORD_Y"],
               c=RED, s=18, alpha=0.55, label="Miss", zorder=3)
    ax.scatter(makes["COORD_X"],  makes["COORD_Y"],
               c=GREEN, s=18, alpha=0.70, label="Make", zorder=3)

    pct = makes.shape[0] / z.shape[0] * 100 if z.shape[0] > 0 else 0
    ax.set_title(
        f"Zone {zone}   {pct:.1f}%  (n={len(z)})",
        color="white", fontsize=11, fontweight="bold", pad=6,
    )
    ax.legend(loc="upper right", fontsize=7, facecolor=PANEL_BG,
              labelcolor="white", edgecolor="none", markerscale=1.2)

# Free throw bar chart in the last zone slot (data from boxscore — shot data omits misses)
ax_ft = axes_flat[n_zones]
ax_ft.set_facecolor(PANEL_BG)
ft_missed = ft_att - ft_made

ax_ft.bar(["Made", "Missed"], [ft_made, ft_missed],
          color=[GREEN, RED], edgecolor="none", width=0.5)
for v, label in zip([ft_made, ft_missed], ["Made", "Missed"]):
    ax_ft.text(label, v + 2, str(v), ha="center", color="white", fontsize=10)
ax_ft.set_title(
    f"Free Throws   {ft_pct:.1f}%  (n={ft_att})\n(from boxscore)",
    color="white", fontsize=11, fontweight="bold", pad=6,
)
ax_ft.tick_params(colors="white")
ax_ft.spines[:].set_visible(False)
ax_ft.set_ylim(0, max(ft_made, ft_missed) * 1.18)

# Hide any unused axes
for ax in axes_flat[n_zones + 1:]:
    ax.set_visible(False)

fig.suptitle(
    "Fenerbahce Beko 2025-26 — Shot Zones Verification",
    color="white", fontsize=16, fontweight="bold", y=1.01,
)
fig.tight_layout(pad=1.5)
fig.savefig("fenerbahce_zone_verification_2025_26.png", dpi=130,
            bbox_inches="tight", facecolor=BG)
print("Saved -> fenerbahce_zone_verification_2025_26.png")

# ── text summary per zone ─────────────────────────────────────────────────────

print("\nZone breakdown:")
print(f"{'Zone':>6}  {'Attempts':>8}  {'Makes':>6}  {'FG%':>6}")
for zone in zones:
    z = fg[fg["ZONE"] == zone]
    m = z["made"].sum()
    pct = m / len(z) * 100
    print(f"  {zone:>4}  {len(z):>8}  {m:>6}  {pct:>5.1f}%")
print(f"  {'FT':>4}  {ft_att:>8}  {ft_made:>6}  {ft_pct:>5.1f}%  (boxscore)")
