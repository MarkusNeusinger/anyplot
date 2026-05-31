#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "colorspacious>=1.1.2",
#   "numpy>=2.0",
#   "matplotlib>=3.10",
#   "pillow>=11.0",
# ]
# ///
"""Export the imprint pairwise colour-distance matrices as JSON for the frontend.

The /palette page (app/src/pages/PalettePage.tsx) shows per-hex *row minima*
of these matrices (Swatch.minNorm / minCvd) but never the full pairwise grid.
This script emits the complete ΔE (CAM02-UCS) matrices — normal vision, each of
the three CVD simulations (Machado 2009, severity 100), and the worst-of-three
roll-up — so the page can render the colour-distance matrix statically from this
shared data (no live colour-science in the browser). Only the ΔE values and the
threshold cutoffs are shared; the frontend applies its own cell tints and legend.

Colour set: the 8 categorical imprint hues + the amber anchor + the light-theme
neutral ink (#1A1A17). Amber and neutral live OUTSIDE the categorical pool but
are real series colours (warning / totals-baseline), so showing how close they
sit to the 8 hues is useful. The matrices are theme-independent except for the
neutral row/column, which uses the light-theme ink; this is noted in the JSON.

Reuses the existing colour math in scripts/_palette_common.py — no new
algorithms here, only serialisation.

Run::

    uv run --script scripts/palette-matrix-export.py
    uv run --script scripts/palette-matrix-export.py --out /tmp/m.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _palette_common import (  # noqa: E402
    CVD_LABELS,
    CVD_ONLY,
    hex_to_rgb1,
    pairwise_delta_e,
    worst_cvd_pairwise_delta_e,
)


# Mirror core.palette slot order (green, lavender, blue, ochre, red, cyan, rose,
# lime) + the two anchors the matrix includes. Kept inline so this script stays
# a self-contained PEP-723 runnable, matching the other scripts/palette-*.py.
COLORS: list[tuple[str, str]] = [
    ("green", "#009E73"),
    ("lavender", "#C475FD"),
    ("blue", "#4467A3"),
    ("ochre", "#BD8233"),
    ("red", "#AE3030"),
    ("cyan", "#2ABCCD"),
    ("rose", "#954477"),
    ("lime", "#99B314"),
    ("amber", "#DDCC77"),  # semantic anchor — warning / caution (outside the pool)
    ("neutral", "#1A1A17"),  # light-theme ink — totals / baseline (outside the pool)
]

# Petroff (2021) 4-step CAM02-UCS distinguishability thresholds, kept in sync
# with _palette_common.cell_class so the same ΔE cutoffs drive both surfaces.
# (The frontend applies its own tints/legend on top of these thresholds.)
THRESHOLDS = [5.0, 10.0, 15.0]


def _round(matrix: np.ndarray) -> list[list[float]]:
    """2-dp rounding for a compact, diff-friendly JSON artefact."""
    return [[round(float(v), 2) for v in row] for row in matrix]


def build() -> dict:
    labels = [name for name, _ in COLORS]
    hexes = [hx for _, hx in COLORS]
    rgb = np.array([hex_to_rgb1(hx) for hx in hexes])

    normal = pairwise_delta_e(rgb, "normal")
    worst, breakdown = worst_cvd_pairwise_delta_e(rgb)
    # breakdown[i, j, k] is ΔE under CVD_ONLY[k] (deuter / protan / tritan)
    per_cvd = {cvd: _round(breakdown[:, :, k]) for k, cvd in enumerate(CVD_ONLY)}

    return {
        "space": "CAM02-UCS",
        "cvdModel": "Machado et al. 2009 — severity 100 (full dichromacy)",
        "cvdLabels": {k: CVD_LABELS[k] for k in CVD_ONLY},
        "thresholds": THRESHOLDS,
        "anchorsOutsidePool": ["amber", "neutral"],
        "neutralTheme": "light",
        "note": (
            "Pairwise ΔE in CAM02-UCS among the 8 categorical imprint hues plus "
            "the amber and neutral anchors. <5 indistinguishable, <10 weak, "
            "<15 acceptable, >=15 comfortable (Petroff 2021). The neutral row/"
            "column uses the light-theme ink #1A1A17."
        ),
        "labels": labels,
        "hexes": hexes,
        "matrices": {
            "normal": _round(normal),
            "deuter": per_cvd["deuter"],
            "protan": per_cvd["protan"],
            "tritan": per_cvd["tritan"],
            "worstCvd": _round(worst),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "app" / "src" / "data" / "paletteMatrices.json",
        help="output JSON path (default: app/src/data/paletteMatrices.json)",
    )
    args = parser.parse_args()
    data = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n")
    n = len(data["labels"])
    print(f"wrote {n}x{n} ΔE matrices ({', '.join(data['labels'])}) -> {args.out}")


if __name__ == "__main__":
    main()
