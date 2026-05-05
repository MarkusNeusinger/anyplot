#!/usr/bin/env python3
"""Generate OG image samples in every variant for visual review.

Issue #5652 — preview the new any.plot() OG image style across the four
endpoints (`/og/home.png`, `/og/plots.png`, `/og/{spec}/{lang}/{lib}.png`,
`/og/{spec}.png`, comparison) in both light and dark themes, without needing a
running API or live data.

Usage:
    uv run python scripts/generate_og_samples.py [--out PATH]

Defaults to writing to `out/og-samples/`. Each file is a self-contained PNG you
can open directly or paste into a Slack DM / X post to confirm the cards look
on-brand. Filenames follow the pattern `<endpoint>__<theme>.png` so the
variants stack visually in any file browser sorted alphabetically.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image

from core.images import (
    OG_HEIGHT,
    OG_WIDTH,
    create_branded_og_image,
    create_comparison_image,
    create_home_og_image,
    create_og_collage,
)


# Sample data — chosen to look like a typical card without depending on the DB
# or production GCS. The spec_id and library hint pairs are fictional but
# representative.
SAMPLE_SPECS: list[tuple[str, str, str]] = [
    ("scatter-basic", "matplotlib", "pyplot.scatter()"),
    ("ridgeline-density", "seaborn", "FacetGrid()"),
    ("sankey-flow", "plotly", "graph_objects.Sankey()"),
    ("treemap-nested", "plotnine", "geom_treemap()"),
]

SAMPLE_COLLAGE_LIBS: list[str] = ["matplotlib", "seaborn", "plotly", "bokeh", "altair", "plotnine"]


def _make_dummy_plot(seed: int, width: int = 800, height: int = 600) -> bytes:
    """Render a small matplotlib chart so the OG cards have something to wrap.

    Falls back to a flat color block if matplotlib isn't available — keeps
    this script runnable in slim CI containers.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        rng = np.random.default_rng(seed)
        fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
        for i in range(4):
            x = np.linspace(0, 10, 50)
            y = np.sin(x + i * 0.6) + rng.normal(0, 0.15, 50) + i * 0.5
            ax.plot(x, y, linewidth=2, marker="o", markersize=4)
        ax.set_facecolor("#FAF8F1")
        fig.set_facecolor("#FFFDF6")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(colors="#6B6A63")
        for spine in ax.spines.values():
            spine.set_color("#E2DFD6")

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        # Fallback: a flat colored rectangle if matplotlib isn't installed.
        img = Image.new("RGB", (width, height), color=(245 - seed % 30, 240, 230))
        buf = BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()


def _save_with_log(out_dir: Path, filename: str, payload: bytes | Image.Image) -> Path:
    out_path = out_dir / filename
    if isinstance(payload, bytes):
        out_path.write_bytes(payload)
    else:
        payload.save(out_path, "PNG", optimize=True)
    print(f"  ✓ {out_path}  ({OG_WIDTH}x{OG_HEIGHT})")
    return out_path


def generate(out_dir: Path) -> list[Path]:
    """Render every OG variant into `out_dir` and return the list of file paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    plot_bytes_a = _make_dummy_plot(seed=1)
    plot_bytes_b = _make_dummy_plot(seed=2)

    print(f"\n→ writing variants to {out_dir.resolve()}\n")

    # ---- 1. Home / plots fallback -----------------------------------------
    print("• /og/home.png + /og/plots.png (hero card)")
    for theme in ("light", "dark"):
        result = create_home_og_image(theme=theme)
        assert isinstance(result, bytes)
        written.append(_save_with_log(out_dir, f"home__{theme}.png", result))

    # ---- 2. Single-impl branded card --------------------------------------
    print("• /og/{spec_id}/{language}/{library}.png (single impl)")
    for spec_id, library, method in SAMPLE_SPECS:
        for theme in ("light", "dark"):
            result = create_branded_og_image(
                plot_bytes_a, spec_id=spec_id, library=library, theme=theme, method=method
            )
            assert isinstance(result, bytes)
            written.append(_save_with_log(out_dir, f"branded__{spec_id}__{library}__{theme}.png", result))

    # ---- 3. Spec collage ---------------------------------------------------
    print("• /og/{spec_id}.png (multi-library collage)")
    collage_images = [_make_dummy_plot(seed=10 + i) for i in range(len(SAMPLE_COLLAGE_LIBS))]
    for theme in ("light", "dark"):
        result = create_og_collage(
            collage_images, labels=SAMPLE_COLLAGE_LIBS, spec_id="ridgeline-density", theme=theme
        )
        assert isinstance(result, bytes)
        written.append(_save_with_log(out_dir, f"collage__ridgeline-density__{theme}.png", result))

    # ---- 4. Compare (before/after) ----------------------------------------
    print("• comparison card (impl review)")
    before_path = out_dir / "_tmp_before.png"
    after_path = out_dir / "_tmp_after.png"
    before_path.write_bytes(plot_bytes_a)
    after_path.write_bytes(plot_bytes_b)
    for theme in ("light", "dark"):
        out_path = out_dir / f"compare__area-basic__matplotlib__{theme}.png"
        create_comparison_image(
            before_path, after_path, out_path, spec_id="area-basic", library="matplotlib", theme=theme
        )
        print(f"  ✓ {out_path}  (2400x800)")
        written.append(out_path)
    # New-impl variant (no `before`).
    out_path = out_dir / "compare__area-basic__matplotlib__new.png"
    create_comparison_image(
        None, after_path, out_path, spec_id="area-basic", library="matplotlib", theme="light"
    )
    print(f"  ✓ {out_path}  (2400x800, no before)")
    written.append(out_path)

    # Cleanup temp files used by compare.
    before_path.unlink(missing_ok=True)
    after_path.unlink(missing_ok=True)

    print(f"\n✓ wrote {len(written)} OG sample variants\n")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("out/og-samples"),
        help="Directory to write samples into (default: out/og-samples)",
    )
    args = parser.parse_args()
    generate(args.out)


if __name__ == "__main__":
    main()
