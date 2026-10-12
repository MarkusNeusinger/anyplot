"""The free direction for a polar plot's radial tick labels, computed from the render's probe.

On a polar axes matplotlib draws the radial tick labels along one ray, at
`rlabel_position` degrees (22.5 by default), one label per radius tick from the
centre to the edge. When data lies along that ray the labels sit on the markers,
and a repair that has to guess another angle may pick one that is just as crowded:
in the owner's case of 2026-10-12 (seaborn `polar-scatter`, `y = sin(x)`) the repair
moved the labels to 67.5°, onto the data. So the host measures it instead.

The harness records, per polar axes, the labels' angle, the visible theta span and
a histogram of the plotted points by angle (5° bins) and by radius as a share of the
visible radius range (tenths, centre first; `harness.polar_report`). The angles are
in the axes' own theta coordinates, which `set_rlabel_position` takes as well, so the
theta offset and direction need no conversion. A point lies under the labels of a
ray when it is on the ray's side of the centre (less than 90° away), its distance
from the ray, as a share of the radius, is at most `HALF_WIDTH`, and it is not in the
innermost ring, where every ray passes and no direction is freer than another.
Evenly spread angles alone therefore do not make every direction equal: a cardioid
crowds the edge on one side and the centre on the other.

`rlabel_hint` scores the labels' ray and a candidate ray every `STEP_DEG` degrees
inside the visible span. When the best candidate holds at most half the points of
the current ray it returns one line for the repair with the measured value, the
target and the likely cause (the repair-message rule: actual, target, cause); ties
go to the candidate nearest the current angle, then the smallest one.

The line is a hint, not a defect: it never starts a repair on its own, and the
pipeline hands it to the adapter only on a repair attempt (`AdaptRequest.hints`).
The probe is written by the code under test, so every field is validated and a
malformed one yields no hint. No ADK import.
"""

import math
from typing import Any


BIN_DEG = 5
ANGLE_BINS = 360 // BIN_DEG
RINGS = 10
HALF_WIDTH = 0.08
"""A point within this share of the radius from a ray lies under its labels (about half a label's height)."""
STEP_DEG = 22.5
"""The candidate rays: every multiple of this, matplotlib's default label angle among them."""
MAX_POLAR_AXES = 4
MAX_COUNT = 2**31


def _span(thetamin: float, thetamax: float) -> tuple[float, float]:
    """The visible span as a start angle in [0, 360) and a width in (0, 360]."""
    width = thetamax - thetamin
    if width <= 0 or width >= 360:
        return 0.0, 360.0
    return thetamin % 360, width


def _inside(angle: float, start: float, width: float) -> bool:
    return width >= 360 or (angle - start) % 360 <= width


def _distance(a: float, b: float) -> float:
    """The circular distance of two angles in degrees, 0 to 180."""
    delta = abs(a - b) % 360
    return min(delta, 360 - delta)


def _under(bins: list[list[int]], ray: float) -> int:
    """The points that lie under labels drawn along `ray` (module docstring), from the bins' centres."""
    total = 0
    for index, rings in enumerate(bins):
        delta = _distance(index * BIN_DEG + BIN_DEG / 2, ray)
        if delta >= 90:
            continue
        sine = math.sin(math.radians(delta))
        for ring, count in enumerate(rings[1:], start=1):
            if count and (ring + 0.5) / RINGS * sine <= HALF_WIDTH:
                total += count
    return total


def _count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value < MAX_COUNT


def _axes(value: Any) -> tuple[float, float, float, list[list[int]]] | None:
    """One polar axes entry of the probe, validated: (rlabel, thetamin, thetamax, bins), or None."""
    if not isinstance(value, dict):
        return None
    floats: list[float] = []
    for key in ("rlabel", "thetamin", "thetamax"):
        number = value.get(key)
        if not isinstance(number, int | float) or isinstance(number, bool):
            return None
        floats.append(float(number))
    if not all(math.isfinite(number) for number in floats):
        return None
    bins = value.get("bins")
    if not isinstance(bins, list) or len(bins) != ANGLE_BINS:
        return None
    if not all(isinstance(rings, list) and len(rings) == RINGS and all(map(_count, rings)) for rings in bins):
        return None
    return floats[0], floats[1], floats[2], bins


def _angle(value: float) -> str:
    """An angle as the line shows it and the code takes it: 22.5, 270, never 270.0."""
    return f"{value:g}"


def rlabel_hint(polar: Any) -> str | None:
    """The repair line that moves crowded radial tick labels to the freest ray, or None.

    `polar` is the probe's `polar` field. The first polar axes whose labels' ray holds
    points while a ray inside its visible span holds at most half as many gets the line.
    """
    if not isinstance(polar, list):
        return None
    for entry in polar[:MAX_POLAR_AXES]:
        parsed = _axes(entry)
        if parsed is None:
            continue
        rlabel, thetamin, thetamax, bins = parsed
        current = _under(bins, rlabel)
        if not current:
            continue
        start, width = _span(thetamin, thetamax)
        rays = [step * STEP_DEG for step in range(round(360 / STEP_DEG)) if _inside(step * STEP_DEG, start, width)]
        if not rays:
            continue
        best = min(rays, key=lambda ray: (_under(bins, ray), _distance(ray, rlabel), ray))
        fewer = _under(bins, best)
        if fewer > current // 2:
            continue
        return (
            f"polar radial tick labels: at {_angle(rlabel % 360)}° they sit on {current} plotted points → "
            f"ax.set_rlabel_position({_angle(best)}), the freest direction, {fewer} points there. "
            "Likely cause: the label angle was chosen without the data's angles."
        )
    return None
