"""
Coordinate-based shot zone assignment for EuroLeague (FIBA) half-court.

Court origin = basket centre; units = cm.

Zones are defined by two criteria only — distance from basket and angular
sector — so they are strictly non-overlapping:

    A = Under basket     d <= 125  (restricted area)
    B = Left short       125 < d <= 449,  x < 0
    C = Right short      125 < d <= 449,  x >= 0
    D = Left mid-range   449 < d, inside 3PT, left of 45-deg line  (x < -y)
    E = Centre mid-range 449 < d, inside 3PT, between 45-deg lines (-y <= x <= y)
    F = Right mid-range  449 < d, inside 3PT, right of 45-deg line (x > y)
    G = Left 3PT         beyond 3PT line, left of 45-deg line
    H = Centre 3PT       beyond 3PT line, between 45-deg lines
    I = Right 3PT        beyond 3PT line, right of 45-deg line

The short/mid boundary (449 cm) equals the minimum of the maximum distances
found in the original API short-mid zones (D: 449 cm, E: 461 cm).

Angular sectors use two 45-degree lines from the basket:
    Left boundary  : x = -y  (left sector where x < -y)
    Right boundary : x =  y  (right sector where x >  y)
"""

import numpy as np
import pandas as pd

# ── court geometry (cm) ───────────────────────────────────────────────────────

THREE_PT_RADIUS: int = 675   # 3PT arc radius
CORNER_X: int = 660          # x-position of corner 3PT sideline
CORNER_Y: int = 90           # y-height of corner 3PT sideline
RESTRICTED_R: int = 125      # no-charge / restricted-area radius
SHORT_RANGE_MAX: int = 449   # max distance for zones B/C; min(max_d_orig_D, max_d_orig_E)

ZONE_LABELS: dict[str, str] = {
    "A": "Under basket",
    "B": "Left short range",
    "C": "Right short range",
    "D": "Left mid-range",
    "E": "Centre mid-range",
    "F": "Right mid-range",
    "G": "Left 3PT",
    "H": "Centre 3PT",
    "I": "Right 3PT",
}


def assign_zone(x: float, y: float) -> str:
    """Return zone label A-I for a field goal attempt at court coordinates (x, y).

    Coordinate system: basket at origin, court extends in +y direction.

    Args:
        x: Horizontal coordinate in cm (negative = left, positive = right).
        y: Depth coordinate in cm (0 = basket/baseline, positive toward mid-court).

    Returns:
        Single-character zone label from 'A' to 'I'.
    """
    x = float(x)
    y = float(y)
    d_sq = x * x + y * y

    # ── restricted area (under basket) ────────────────────────────────────────
    if d_sq <= RESTRICTED_R ** 2:
        return "A"

    # ── 3-point territory: arc or corner segments ─────────────────────────────
    is_corner = abs(x) >= CORNER_X and y <= CORNER_Y
    is_arc = d_sq >= THREE_PT_RADIUS ** 2
    if is_corner or is_arc:
        if x < -y:
            return "G"   # Left 3PT
        if x > y:
            return "I"   # Right 3PT
        return "H"       # Centre 3PT

    # ── short range: distance <= SHORT_RANGE_MAX, split by side ───────────────
    if d_sq <= SHORT_RANGE_MAX ** 2:
        return "B" if x < 0 else "C"

    # ── mid-range: SHORT_RANGE_MAX < d < 3PT arc, split by 45-deg lines ───────
    if x < -y:
        return "D"   # Left mid-range
    if x > y:
        return "F"   # Right mid-range
    return "E"       # Centre mid-range


def remap_zones(shots: pd.DataFrame) -> pd.DataFrame:
    """Replace the ZONE column in *shots* with coordinate-based zone labels.

    Shots with a blank or missing ZONE (free-throw placeholders at -1,-1) are
    kept as-is so they remain filterable downstream.

    Args:
        shots: DataFrame containing COORD_X, COORD_Y, and ZONE columns.

    Returns:
        A copy of *shots* with ZONE overwritten for field goal attempts.
    """
    df = shots.copy()
    fg_mask = df["ZONE"].str.strip() != ""
    df.loc[fg_mask, "ZONE"] = df.loc[fg_mask].apply(
        lambda r: assign_zone(r["COORD_X"], r["COORD_Y"]), axis=1
    )
    return df
