"""
Per-zone shot verification for Fenerbahce 2025-26.
One half-court per zone showing every shot (make/miss).
Free throws (zone " ", coords -1,-1) are shown in a separate axes as a bar.
All shots outside court boundary are excluded.

Zones are coordinate-based (see zone_mapping.py):
  A = Under basket     B = Left short range   C = Right short range
  D = Left mid-range   E = Centre mid-range   F = Right mid-range
  G = Left 3PT         H = Centre 3PT         I = Right 3PT
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from zone_mapping import ZONE_LABELS, remap_zones
from utils_plot import BG, PANEL_BG, RED, GREEN, GOLD, draw_half_court

# ── load data ─────────────────────────────────────────────────────────────────

shots = pd.read_csv("fenerbahce_shots_2025_26.csv")
fen = remap_zones(shots[shots["TEAM"] == "ULK"].copy())
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
    label = ZONE_LABELS.get(zone, zone)
    ax.set_title(
        f"{zone}: {label}   {pct:.1f}%  (n={len(z)})",
        color="white", fontsize=10, fontweight="bold", pad=6,
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
