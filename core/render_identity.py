"""Render identity: how much of a render changed between two PNGs of the same plot.

A decoupling regeneration that only moves the data into the `# Data` block should
render the same chart. `compare` measures that: the fraction of pixels whose color
differs between two PNGs of equal size, and a verdict against a bound (default
`DEFAULT_BOUND`, 0.5 % of the pixels, per theme). PNGs of different sizes are a
failure, not a diff: the canvas changed, which `core/canvas.py` reports on its own.

A pixel differs when any of its RGBA channels differs by more than `tolerance`
(default 0: any change counts). Both images are compared in RGBA, so a palette PNG
and an RGB PNG of the same picture are identical. PIL only.

Usage as CLI (exit 0 within the bound, 1 over it or on a size change, 2 when a file
cannot be read)::

    python -m core.render_identity old/plot-light.png new/plot-light.png [--bound 0.005]
    python -m core.render_identity --themes old_dir new_dir [--bound 0.005]

`--themes` compares `plot-light.png` and `plot-dark.png` of the two directories and
passes only when both themes do.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops


DEFAULT_BOUND = 0.005
THEMES = ("light", "dark")


@dataclass(frozen=True)
class RenderIdentity:
    """Two renders compared: their sizes, the share of differing pixels and the verdict against `bound`."""

    old_size: tuple[int, int]
    new_size: tuple[int, int]
    differing: int
    bound: float

    @property
    def same_size(self) -> bool:
        return self.old_size == self.new_size

    @property
    def fraction(self) -> float | None:
        """The share of differing pixels, None when the sizes differ."""
        if not self.same_size:
            return None
        total = self.new_size[0] * self.new_size[1]
        return self.differing / total if total else 0.0

    @property
    def passed(self) -> bool:
        fraction = self.fraction
        return fraction is not None and fraction <= self.bound

    def to_dict(self) -> dict[str, object]:
        return {
            "old_size": list(self.old_size),
            "new_size": list(self.new_size),
            "differing": self.differing,
            "fraction": self.fraction,
            "bound": self.bound,
            "passed": self.passed,
        }


def differing_pixels(old: Image.Image, new: Image.Image, tolerance: int = 0) -> int:
    """The number of pixels whose RGBA channels differ by more than `tolerance`; the images must have one size."""
    if old.size != new.size:
        raise ValueError(f"the images differ in size: {old.size} and {new.size}")
    difference = ImageChops.difference(old.convert("RGBA"), new.convert("RGBA"))
    red, green, blue, alpha = difference.split()
    largest = ImageChops.lighter(ImageChops.lighter(red, green), ImageChops.lighter(blue, alpha))
    histogram = largest.histogram()
    return sum(histogram[tolerance + 1 :])


def compare(old_path: Path, new_path: Path, *, bound: float = DEFAULT_BOUND, tolerance: int = 0) -> RenderIdentity:
    """Compare two PNG files; raises OSError when one cannot be read."""
    with Image.open(old_path) as old, Image.open(new_path) as new:
        if old.size != new.size:
            return RenderIdentity(old.size, new.size, 0, bound)
        return RenderIdentity(old.size, new.size, differing_pixels(old, new, tolerance), bound)


def compare_themes(
    old_dir: Path, new_dir: Path, *, bound: float = DEFAULT_BOUND, tolerance: int = 0
) -> dict[str, RenderIdentity]:
    """`compare` for `plot-light.png` and `plot-dark.png` of two render directories."""
    return {
        theme: compare(old_dir / f"plot-{theme}.png", new_dir / f"plot-{theme}.png", bound=bound, tolerance=tolerance)
        for theme in THEMES
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m core.render_identity", description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--themes", action="store_true", help="the arguments are render directories")
    parser.add_argument("--bound", type=float, default=DEFAULT_BOUND, help="largest passing share of pixels")
    parser.add_argument("--tolerance", type=int, default=0, help="largest channel difference that is no change")
    args = parser.parse_args(argv)
    try:
        if args.themes:
            results = compare_themes(args.old, args.new, bound=args.bound, tolerance=args.tolerance)
        else:
            results = {"render": compare(args.old, args.new, bound=args.bound, tolerance=args.tolerance)}
    except OSError as exc:
        print(f"::error::render_identity cannot read a render: {exc}")
        return 2
    print(json.dumps({name: result.to_dict() for name, result in results.items()}))
    return 0 if all(result.passed for result in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
