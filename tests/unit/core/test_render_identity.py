"""Tests for core/render_identity.py with synthetic images."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from core.render_identity import DEFAULT_BOUND, compare, compare_themes, differing_pixels, main


SIZE = (200, 100)  # 20,000 pixels: 0.5 % is 100 pixels


def png(path: Path, *, changed: int = 0, size: tuple[int, int] = SIZE, mode: str = "RGB", delta: int = 50) -> Path:
    """A flat page-colored image with the first `changed` pixels (row-major) shifted by `delta` on red."""
    image = Image.new("RGB", size, (250, 248, 241))
    pixels = image.load()
    assert pixels is not None
    for index in range(changed):
        x, y = index % size[0], index // size[0]
        pixels[x, y] = (250 - delta, 248, 241)
    if mode == "P":  # an adaptive palette keeps the exact colors; the default web palette would not
        image = image.convert("P", palette=Image.Palette.ADAPTIVE)
    elif mode != "RGB":
        image = image.convert(mode)
    image.save(path)
    return path


def test_identical_renders(tmp_path: Path) -> None:
    result = compare(png(tmp_path / "a.png"), png(tmp_path / "b.png"))
    assert result.fraction == 0.0 and result.passed and result.same_size


def test_a_change_within_the_bound(tmp_path: Path) -> None:
    result = compare(png(tmp_path / "a.png"), png(tmp_path / "b.png", changed=100))
    assert result.differing == 100
    assert result.fraction == pytest.approx(DEFAULT_BOUND)
    assert result.passed


def test_a_change_over_the_bound(tmp_path: Path) -> None:
    result = compare(png(tmp_path / "a.png"), png(tmp_path / "b.png", changed=101))
    assert result.differing == 101 and not result.passed


def test_a_custom_bound(tmp_path: Path) -> None:
    assert compare(png(tmp_path / "a.png"), png(tmp_path / "b.png", changed=400), bound=0.02).passed


def test_a_size_change_is_a_failure_not_a_diff(tmp_path: Path) -> None:
    result = compare(png(tmp_path / "a.png"), png(tmp_path / "b.png", size=(200, 101)))
    assert not result.same_size and result.fraction is None and not result.passed
    assert result.to_dict()["fraction"] is None


def test_the_mode_does_not_matter(tmp_path: Path) -> None:
    rgb, palette = png(tmp_path / "a.png"), png(tmp_path / "b.png", mode="P")
    assert compare(rgb, palette).differing == 0
    assert compare(rgb, png(tmp_path / "c.png", mode="RGBA")).differing == 0


def test_tolerance(tmp_path: Path) -> None:
    a, b = png(tmp_path / "a.png"), png(tmp_path / "b.png", changed=300, delta=2)
    assert compare(a, b).differing == 300
    assert compare(a, b, tolerance=2).differing == 0


def test_differing_pixels_refuses_two_sizes() -> None:
    with pytest.raises(ValueError, match="differ in size"):
        differing_pixels(Image.new("RGB", (2, 2)), Image.new("RGB", (3, 2)))


def test_both_themes(tmp_path: Path) -> None:
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    new.mkdir()
    for theme in ("light", "dark"):
        png(old / f"plot-{theme}.png")
    png(new / "plot-light.png")
    png(new / "plot-dark.png", changed=500)
    results = compare_themes(old, new)
    assert results["light"].passed and not results["dark"].passed


def test_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a, b, c = png(tmp_path / "a.png"), png(tmp_path / "b.png", changed=10), png(tmp_path / "c.png", changed=5000)
    assert main([str(a), str(b)]) == 0
    assert json.loads(capsys.readouterr().out)["render"]["differing"] == 10
    assert main([str(a), str(c)]) == 1
    capsys.readouterr()
    assert main([str(a), str(tmp_path / "missing.png")]) == 2
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    new.mkdir()
    for theme in ("light", "dark"):
        png(old / f"plot-{theme}.png")
        png(new / f"plot-{theme}.png", changed=3)
    capsys.readouterr()
    assert main(["--themes", str(old), str(new)]) == 0
    assert set(json.loads(capsys.readouterr().out)) == {"light", "dark"}
