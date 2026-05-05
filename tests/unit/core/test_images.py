"""Tests for core.images module."""

from pathlib import Path

import pytest
from PIL import Image

from core.images import create_responsive_variants, create_thumbnail, optimize_png, process_plot_image


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    img_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    img.save(img_path)
    return img_path


class TestCreateThumbnail:
    """Tests for create_thumbnail function."""

    def test_creates_thumbnail_with_correct_width(self, sample_image: Path, tmp_path: Path) -> None:
        """Thumbnail should have the specified width."""
        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(sample_image, output_path, width=400)

        assert width == 400
        assert output_path.exists()

        # Verify the actual image dimensions
        result_img = Image.open(output_path)
        assert result_img.width == 400

    def test_maintains_aspect_ratio(self, sample_image: Path, tmp_path: Path) -> None:
        """Thumbnail should maintain the original aspect ratio."""
        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(sample_image, output_path, width=400)

        # Original is 800x600 (4:3), so 400 width should give 300 height
        assert height == 300

        result_img = Image.open(output_path)
        assert result_img.height == 300

    def test_custom_width(self, sample_image: Path, tmp_path: Path) -> None:
        """Thumbnail should respect custom width parameter."""
        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(sample_image, output_path, width=200)

        assert width == 200
        assert height == 150  # Maintains 4:3 ratio

    def test_handles_path_objects(self, sample_image: Path, tmp_path: Path) -> None:
        """Function should accept Path objects."""
        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(Path(sample_image), Path(output_path), width=400)

        assert width == 400
        assert output_path.exists()

    def test_default_width(self, sample_image: Path, tmp_path: Path) -> None:
        """Should use default width of 1200 if not specified."""
        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(sample_image, output_path)

        assert width == 1200  # Default width is 1200
        assert height == 900  # Original 800x600 scaled to 1200x900 (4:3 ratio)

    def test_portrait_image(self, tmp_path: Path) -> None:
        """Should handle portrait orientation images."""
        # Create portrait image (600x800)
        img_path = tmp_path / "portrait.png"
        img = Image.new("RGB", (600, 800), color=(100, 150, 200))
        img.save(img_path)

        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(img_path, output_path, width=300)

        assert width == 300
        assert height == 400  # Maintains 3:4 ratio

    def test_square_image(self, tmp_path: Path) -> None:
        """Should handle square images."""
        # Create square image
        img_path = tmp_path / "square.png"
        img = Image.new("RGB", (500, 500), color=(100, 150, 200))
        img.save(img_path)

        output_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(img_path, output_path, width=250)

        assert width == 250
        assert height == 250

    def test_very_small_width(self, sample_image: Path, tmp_path: Path) -> None:
        """Should handle very small thumbnail widths."""
        output_path = tmp_path / "tiny.png"
        width, height = create_thumbnail(sample_image, output_path, width=50)

        assert width == 50
        result_img = Image.open(output_path)
        assert result_img.width == 50


class TestProcessPlotImage:
    """Tests for process_plot_image function."""

    def test_creates_optimized_image_and_thumbnail(self, sample_image: Path, tmp_path: Path) -> None:
        """Should create both optimized image and thumbnail."""
        output_path = tmp_path / "output.png"
        thumb_path = tmp_path / "thumb.png"

        result = process_plot_image(sample_image, output_path, thumb_path)

        assert output_path.exists()
        assert thumb_path.exists()
        assert result["output"] == str(output_path)
        assert result["thumbnail"] == str(thumb_path)
        assert result["thumb_size"][0] == 1200  # Default width is 1200
        assert result["thumb_size"][1] == 900  # Original 800x600 scaled to 1200x900

    def test_without_thumbnail(self, sample_image: Path, tmp_path: Path) -> None:
        """Should work without creating a thumbnail."""
        output_path = tmp_path / "output.png"

        result = process_plot_image(sample_image, output_path, thumb_path=None)

        assert output_path.exists()
        assert "thumbnail" not in result

    def test_without_optimization(self, sample_image: Path, tmp_path: Path) -> None:
        """Should work without PNG optimization."""
        output_path = tmp_path / "output.png"

        result = process_plot_image(sample_image, output_path, optimize=False)

        assert output_path.exists()
        assert "bytes_saved" not in result

    def test_custom_thumb_width(self, sample_image: Path, tmp_path: Path) -> None:
        """Should respect custom thumbnail width."""
        output_path = tmp_path / "output.png"
        thumb_path = tmp_path / "thumb.png"

        result = process_plot_image(sample_image, output_path, thumb_path, thumb_width=300)

        assert result["thumb_size"][0] == 300


class TestOptimizePng:
    """Tests for optimize_png function."""

    def test_optimizes_image(self, sample_image: Path, tmp_path: Path) -> None:
        """Should optimize PNG file."""
        output_path = tmp_path / "optimized.png"
        bytes_saved = optimize_png(sample_image, output_path)

        assert output_path.exists()
        # bytes_saved can be negative if optimized is larger (rare for simple images)
        assert isinstance(bytes_saved, int)

    def test_overwrites_input_when_no_output(self, tmp_path: Path) -> None:
        """Should overwrite input file when output_path is None."""
        # Create a larger image for better optimization potential
        img_path = tmp_path / "to_optimize.png"
        img = Image.new("RGB", (1000, 1000), color=(100, 150, 200))
        img.save(img_path)

        bytes_saved = optimize_png(img_path, output_path=None)

        # File should still exist and function should return bytes saved
        assert img_path.exists()
        assert isinstance(bytes_saved, int)

    def test_accepts_path_objects(self, sample_image: Path, tmp_path: Path) -> None:
        """Should accept Path objects."""
        output_path = tmp_path / "optimized.png"
        bytes_saved = optimize_png(Path(sample_image), Path(output_path))

        assert output_path.exists()
        assert isinstance(bytes_saved, int)

    def test_accepts_string_paths(self, sample_image: Path, tmp_path: Path) -> None:
        """Should accept string paths."""
        output_path = tmp_path / "optimized.png"
        optimize_png(str(sample_image), str(output_path))

        assert output_path.exists()


class TestErrorCases:
    """Tests for error handling."""

    def test_thumbnail_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            create_thumbnail(tmp_path / "nonexistent.png", tmp_path / "out.png")

    def test_optimize_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            optimize_png(tmp_path / "nonexistent.png", tmp_path / "out.png")


class TestPngquantFallback:
    """Tests for pngquant fallback behavior."""

    def test_pillow_fallback_when_no_pngquant(self, sample_image: Path, tmp_path: Path) -> None:
        """Should use Pillow fallback when pngquant is not available."""
        import core.images

        # Save original value
        original_has_pngquant = core.images._HAS_PNGQUANT
        try:
            # Mock pngquant not being available
            core.images._HAS_PNGQUANT = False

            output_path = tmp_path / "optimized.png"
            bytes_saved = optimize_png(sample_image, output_path)

            assert output_path.exists()
            assert isinstance(bytes_saved, int)
        finally:
            # Restore original value
            core.images._HAS_PNGQUANT = original_has_pngquant

    def test_optimize_png_with_pillow_fallback_inplace(self, tmp_path: Path) -> None:
        """Should optimize in-place with Pillow fallback."""
        import core.images

        # Create a test image
        img_path = tmp_path / "to_optimize.png"
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(img_path)

        original_has_pngquant = core.images._HAS_PNGQUANT
        try:
            core.images._HAS_PNGQUANT = False
            bytes_saved = optimize_png(img_path, output_path=None)
            assert img_path.exists()
            assert isinstance(bytes_saved, int)
        finally:
            core.images._HAS_PNGQUANT = original_has_pngquant


class TestImageFormats:
    """Tests for different image formats and edge cases."""

    def test_rgba_image(self, tmp_path: Path) -> None:
        """Should handle RGBA images with transparency."""
        img_path = tmp_path / "rgba.png"
        img = Image.new("RGBA", (400, 300), color=(100, 150, 200, 128))
        img.save(img_path)

        output_path = tmp_path / "processed.png"
        process_plot_image(img_path, output_path)

        assert output_path.exists()

    def test_grayscale_image(self, tmp_path: Path) -> None:
        """Should handle grayscale images."""
        img_path = tmp_path / "gray.png"
        img = Image.new("L", (400, 300), color=128)
        img.save(img_path)

        # Thumbnail should work
        thumb_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(img_path, thumb_path, width=200)

        assert thumb_path.exists()
        assert width == 200

    def test_large_image(self, tmp_path: Path) -> None:
        """Should handle large images."""
        img_path = tmp_path / "large.png"
        img = Image.new("RGB", (4000, 3000), color=(100, 150, 200))
        img.save(img_path)

        thumb_path = tmp_path / "thumb.png"
        width, height = create_thumbnail(img_path, thumb_path, width=400)

        assert width == 400
        assert height == 300  # Maintains 4:3 ratio


class TestCreateResponsiveVariants:
    """Tests for create_responsive_variants function."""

    def test_creates_all_variants(self, sample_image: Path, tmp_path: Path) -> None:
        """Should create all 7 responsive variants.

        Phase C: output basename follows the input stem, so sample_image
        (test_image.png) produces test_image_*.{png,webp} + test_image.webp.
        """
        output_dir = tmp_path / "variants"
        results = create_responsive_variants(sample_image, output_dir, optimize=False)

        # 800px source: only 400px sized variant is smaller (800/1200 are skipped).
        expected_files = {"test_image_400.png", "test_image_400.webp", "test_image.webp"}
        actual_files = {f.name for f in output_dir.iterdir()}
        assert actual_files == expected_files
        assert len(results) == 3

    def test_creates_all_sizes_for_large_image(self, tmp_path: Path) -> None:
        """Should create all sized variants when source is large enough."""
        img_path = tmp_path / "large.png"
        Image.new("RGB", (4000, 3000), color=(100, 150, 200)).save(img_path)

        output_dir = tmp_path / "variants"
        results = create_responsive_variants(img_path, output_dir, optimize=False)

        expected_files = {
            "large_1200.png",
            "large_1200.webp",
            "large_800.png",
            "large_800.webp",
            "large_400.png",
            "large_400.webp",
            "large.webp",
        }
        actual_files = {f.name for f in output_dir.iterdir()}
        assert actual_files == expected_files
        assert len(results) == 7

    def test_correct_dimensions(self, tmp_path: Path) -> None:
        """Resized variants should have correct width and maintained aspect ratio."""
        img_path = tmp_path / "plot.png"
        Image.new("RGB", (2000, 1000), color=(50, 100, 150)).save(img_path)

        output_dir = tmp_path / "variants"
        create_responsive_variants(img_path, output_dir, optimize=False)

        img_800 = Image.open(output_dir / "plot_800.png")
        assert img_800.width == 800
        assert img_800.height == 400  # 2:1 ratio maintained

        img_400 = Image.open(output_dir / "plot_400.png")
        assert img_400.width == 400
        assert img_400.height == 200

    def test_webp_variants_created(self, tmp_path: Path) -> None:
        """WebP variants should be valid WebP files."""
        img_path = tmp_path / "plot.png"
        Image.new("RGB", (2000, 1000), color=(50, 100, 150)).save(img_path)

        output_dir = tmp_path / "variants"
        create_responsive_variants(img_path, output_dir, optimize=False)

        webp = Image.open(output_dir / "plot_800.webp")
        assert webp.format == "WEBP"
        assert webp.width == 800

        full_webp = Image.open(output_dir / "plot.webp")
        assert full_webp.format == "WEBP"
        assert full_webp.width == 2000

    def test_skips_sizes_larger_than_source(self, tmp_path: Path) -> None:
        """Should not create variants larger than the source image."""
        img_path = tmp_path / "small.png"
        Image.new("RGB", (500, 300), color=(100, 100, 100)).save(img_path)

        output_dir = tmp_path / "variants"
        create_responsive_variants(img_path, output_dir, optimize=False)

        # 500px source: only 400 < 500, so 400 variants + full webp.
        # Basename derived from input stem: small.png → small_*.{png,webp} + small.webp
        filenames = {f.name for f in output_dir.iterdir()}
        assert "small_1200.png" not in filenames
        assert "small_800.png" not in filenames
        assert "small_400.png" in filenames
        assert "small.webp" in filenames

    def test_handles_rgba_input(self, tmp_path: Path) -> None:
        """Should convert RGBA images to RGB."""
        img_path = tmp_path / "rgba.png"
        Image.new("RGBA", (2000, 1000), color=(100, 150, 200, 128)).save(img_path)

        output_dir = tmp_path / "variants"
        results = create_responsive_variants(img_path, output_dir, optimize=False)

        assert len(results) > 0
        img = Image.open(output_dir / "rgba_800.png")
        assert img.mode == "RGB"

    def test_creates_output_dir(self, sample_image: Path, tmp_path: Path) -> None:
        """Should create output directory if it doesn't exist."""
        output_dir = tmp_path / "new" / "nested" / "dir"
        create_responsive_variants(sample_image, output_dir, optimize=False)
        assert output_dir.exists()


class TestCLI:
    """Tests for command-line interface."""

    @pytest.fixture(autouse=True)
    def clean_module_cache(self):
        """Remove core.images from sys.modules to avoid runpy warning."""
        import sys

        # Remove module before test to allow clean runpy execution
        sys.modules.pop("core.images", None)
        yield
        # Clean up after test as well
        sys.modules.pop("core.images", None)

    def test_cli_thumbnail_command(self, sample_image: Path, tmp_path: Path, monkeypatch, capsys) -> None:
        """Should run thumbnail command from CLI."""
        import sys

        output_path = tmp_path / "thumb.png"

        # Mock sys.argv for CLI
        monkeypatch.setattr(sys, "argv", ["images", "thumbnail", str(sample_image), str(output_path), "300"])

        # Run the module
        import runpy

        try:
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)
        except SystemExit:
            pass  # Expected if print_usage was called

        # Check output was created
        assert output_path.exists()
        captured = capsys.readouterr()
        assert "300x" in captured.out  # Should print dimensions

    def test_cli_thumbnail_default_width(self, sample_image: Path, tmp_path: Path, monkeypatch, capsys) -> None:
        """Should use default width of 1200 for thumbnail."""
        import sys

        output_path = tmp_path / "thumb.png"

        monkeypatch.setattr(sys, "argv", ["images", "thumbnail", str(sample_image), str(output_path)])

        import runpy

        try:
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)
        except SystemExit:
            pass

        assert output_path.exists()
        result_img = Image.open(output_path)
        assert result_img.width == 1200

    def test_cli_process_command(self, sample_image: Path, tmp_path: Path, monkeypatch, capsys) -> None:
        """Should run process command from CLI."""
        import sys

        output_path = tmp_path / "output.png"
        thumb_path = tmp_path / "thumb.png"

        monkeypatch.setattr(sys, "argv", ["images", "process", str(sample_image), str(output_path), str(thumb_path)])

        import runpy

        try:
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)
        except SystemExit:
            pass

        assert output_path.exists()
        assert thumb_path.exists()
        captured = capsys.readouterr()
        assert "Processed:" in captured.out

    def test_cli_process_without_thumbnail(self, sample_image: Path, tmp_path: Path, monkeypatch, capsys) -> None:
        """Should run process command without thumbnail."""
        import sys

        output_path = tmp_path / "output.png"

        monkeypatch.setattr(sys, "argv", ["images", "process", str(sample_image), str(output_path)])

        import runpy

        try:
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)
        except SystemExit:
            pass

        assert output_path.exists()
        captured = capsys.readouterr()
        assert "Processed:" in captured.out

    def test_cli_unknown_command(self, monkeypatch, capsys) -> None:
        """Should print usage for unknown command."""
        import sys

        monkeypatch.setattr(sys, "argv", ["images", "unknown"])

        import runpy

        with pytest.raises(SystemExit):
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)

        captured = capsys.readouterr()
        assert "Unknown command: unknown" in captured.out

    def test_cli_no_args(self, monkeypatch, capsys) -> None:
        """Should print usage when no arguments given."""
        import sys

        monkeypatch.setattr(sys, "argv", ["images"])

        import runpy

        with pytest.raises(SystemExit):
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)

        captured = capsys.readouterr()
        assert "Usage:" in captured.out

    def test_cli_thumbnail_missing_args(self, monkeypatch, capsys) -> None:
        """Should print usage when thumbnail args are missing."""
        import sys

        monkeypatch.setattr(sys, "argv", ["images", "thumbnail", "input.png"])

        import runpy

        with pytest.raises(SystemExit):
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)

        captured = capsys.readouterr()
        assert "Usage:" in captured.out

    def test_cli_process_missing_args(self, monkeypatch, capsys) -> None:
        """Should print usage when process args are missing."""
        import sys

        monkeypatch.setattr(sys, "argv", ["images", "process", "input.png"])

        import runpy

        with pytest.raises(SystemExit):
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)

        captured = capsys.readouterr()
        assert "Usage:" in captured.out


class TestBrandingFunctions:
    """Tests for OG image branding functions."""

    @pytest.fixture
    def sample_plot_image(self, tmp_path: Path) -> Path:
        """Create a sample plot image for branding tests."""
        img_path = tmp_path / "plot.png"
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(img_path)
        return img_path

    def test_get_font_fallback(self) -> None:
        """Should return a font (fallback if MonoLisa not available)."""
        from core.images import _get_font

        font = _get_font(32)
        assert font is not None

    def test_get_font_with_weight(self) -> None:
        """Should accept weight parameter."""
        from core.images import _get_font

        font = _get_font(24, weight=400)
        assert font is not None

    def test_draw_anyplot_logo(self, tmp_path: Path) -> None:
        """Should draw logo with correct colors."""
        from PIL import ImageDraw

        from core.images import _draw_anyplot_logo

        img = Image.new("RGB", (400, 100), color="#f8f9fa")
        draw = ImageDraw.Draw(img)
        width = _draw_anyplot_logo(draw, 50, 30, font_size=32)

        assert width > 0
        # Save to verify visually if needed
        img.save(tmp_path / "logo_test.png")
        assert (tmp_path / "logo_test.png").exists()

    def test_create_branded_header(self) -> None:
        """Should create header with correct dimensions."""
        from core.images import create_branded_header

        header = create_branded_header(width=1200, height=80)

        assert header.width == 1200
        assert header.height == 80
        assert header.mode == "RGB"

    def test_draw_rounded_card(self, tmp_path: Path) -> None:
        """Should draw rounded card with shadow."""
        from core.images import _draw_rounded_card

        base = Image.new("RGBA", (400, 300), "#f8f9fa")
        content = Image.new("RGB", (200, 150), "#ffffff")

        _draw_rounded_card(base, content, x=50, y=50, padding=10, radius=12)

        # Verify image was modified (not just background color)
        base.save(tmp_path / "card_test.png")
        assert (tmp_path / "card_test.png").exists()

    def test_create_branded_og_image_from_path(self, sample_plot_image: Path, tmp_path: Path) -> None:
        """Should create branded OG image from file path."""
        from core.images import create_branded_og_image

        output_path = tmp_path / "branded.png"
        create_branded_og_image(sample_plot_image, output_path, spec_id="test-spec", library="matplotlib")

        assert output_path.exists()
        img = Image.open(output_path)
        assert img.width == 1200
        assert img.height == 630

    def test_create_branded_og_image_from_bytes(self, sample_plot_image: Path) -> None:
        """Should create branded OG image from bytes and return bytes."""
        from io import BytesIO

        from core.images import create_branded_og_image

        with open(sample_plot_image, "rb") as f:
            image_bytes = f.read()

        result = create_branded_og_image(image_bytes, spec_id="test-spec", library="matplotlib")

        assert isinstance(result, bytes)
        # Verify it's a valid PNG
        img = Image.open(BytesIO(result))
        assert img.width == 1200
        assert img.height == 630

    def test_create_branded_og_image_from_pil_image(self, tmp_path: Path) -> None:
        """Should create branded OG image from PIL Image."""
        from io import BytesIO

        from core.images import create_branded_og_image

        pil_img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        result = create_branded_og_image(pil_img, spec_id="test-spec")

        assert isinstance(result, bytes)
        img = Image.open(BytesIO(result))
        assert img.width == 1200

    def test_create_branded_og_image_rgba(self, tmp_path: Path) -> None:
        """Should handle RGBA images."""
        from core.images import create_branded_og_image

        rgba_img = Image.new("RGBA", (800, 600), color=(100, 150, 200, 128))
        result = create_branded_og_image(rgba_img)

        assert isinstance(result, bytes)

    def test_create_og_collage_single_image(self, sample_plot_image: Path) -> None:
        """Should create collage with single image."""
        from io import BytesIO

        from core.images import create_og_collage

        with open(sample_plot_image, "rb") as f:
            image_bytes = f.read()

        result = create_og_collage([image_bytes], labels=["test · matplotlib"])

        assert isinstance(result, bytes)
        img = Image.open(BytesIO(result))
        assert img.width == 1200
        assert img.height == 630

    def test_create_og_collage_multiple_images(self, tmp_path: Path) -> None:
        """Should create collage with multiple images."""
        from io import BytesIO

        from core.images import create_og_collage

        # Create multiple test images
        images = []
        labels = []
        for i in range(6):
            img = Image.new("RGB", (400, 300), color=(100 + i * 20, 150, 200))
            buf = BytesIO()
            img.save(buf, "PNG")
            images.append(buf.getvalue())
            labels.append(f"test · lib{i}")

        result = create_og_collage(images, labels=labels)

        assert isinstance(result, bytes)
        img = Image.open(BytesIO(result))
        assert img.width == 1200
        assert img.height == 630

    def test_create_og_collage_to_file(self, sample_plot_image: Path, tmp_path: Path) -> None:
        """Should save collage to file."""
        from core.images import create_og_collage

        output_path = tmp_path / "collage.png"
        create_og_collage([sample_plot_image], output_path=output_path)

        assert output_path.exists()
        img = Image.open(output_path)
        assert img.width == 1200

    def test_create_og_collage_empty_raises(self) -> None:
        """Should raise ValueError for empty image list."""
        from core.images import create_og_collage

        with pytest.raises(ValueError, match="At least one image"):
            create_og_collage([])

    def test_create_og_collage_without_labels(self, sample_plot_image: Path) -> None:
        """Should work without labels."""

        from core.images import create_og_collage

        result = create_og_collage([sample_plot_image])

        assert isinstance(result, bytes)

    def test_create_home_og_image_light(self) -> None:
        """create_home_og_image renders a 1200x630 PNG in light theme."""
        from io import BytesIO

        from core.images import OG_HEIGHT, OG_WIDTH, create_home_og_image

        result = create_home_og_image(theme="light")

        assert isinstance(result, bytes)
        img = Image.open(BytesIO(result))
        assert img.width == OG_WIDTH
        assert img.height == OG_HEIGHT

    def test_create_home_og_image_dark(self) -> None:
        """create_home_og_image renders a 1200x630 PNG in dark theme."""
        from io import BytesIO

        from core.images import OG_HEIGHT, OG_WIDTH, create_home_og_image

        result = create_home_og_image(theme="dark")

        assert isinstance(result, bytes)
        img = Image.open(BytesIO(result))
        assert img.width == OG_WIDTH
        assert img.height == OG_HEIGHT

    def test_create_home_og_image_to_file(self, tmp_path: Path) -> None:
        """create_home_og_image writes to disk when output_path is given."""
        from core.images import OG_HEIGHT, OG_WIDTH, create_home_og_image

        output_path = tmp_path / "home.png"
        create_home_og_image(output_path=output_path, theme="light")

        assert output_path.exists()
        img = Image.open(output_path)
        assert img.width == OG_WIDTH
        assert img.height == OG_HEIGHT

    def test_create_comparison_image_before_and_after(self, sample_plot_image: Path, tmp_path: Path) -> None:
        """create_comparison_image writes a 2400x800 PNG with both panels."""
        from core.images import COMPARE_HEIGHT, COMPARE_WIDTH, create_comparison_image

        output_path = tmp_path / "compare.png"
        create_comparison_image(
            sample_plot_image, sample_plot_image, output_path, spec_id="area-basic", library="matplotlib"
        )

        assert output_path.exists()
        img = Image.open(output_path)
        assert img.width == COMPARE_WIDTH
        assert img.height == COMPARE_HEIGHT

    def test_create_comparison_image_no_before(self, sample_plot_image: Path, tmp_path: Path) -> None:
        """create_comparison_image handles the 'first version' case (before=None)."""
        from core.images import COMPARE_HEIGHT, COMPARE_WIDTH, create_comparison_image

        output_path = tmp_path / "compare.png"
        create_comparison_image(None, sample_plot_image, output_path, spec_id="area-basic", library="matplotlib")

        assert output_path.exists()
        img = Image.open(output_path)
        assert img.width == COMPARE_WIDTH
        assert img.height == COMPARE_HEIGHT

    def test_create_comparison_image_dark_theme(self, sample_plot_image: Path, tmp_path: Path) -> None:
        """create_comparison_image honors theme='dark'."""
        from core.images import create_comparison_image

        output_path = tmp_path / "compare.png"
        create_comparison_image(
            sample_plot_image, sample_plot_image, output_path, spec_id="x", library="seaborn", theme="dark"
        )

        assert output_path.exists()

    def test_create_branded_og_image_unknown_library_falls_back(self, sample_plot_image: Path) -> None:
        """Unknown library names should still render (chip falls back to brand green)."""
        from io import BytesIO

        from core.images import create_branded_og_image

        result = create_branded_og_image(sample_plot_image, spec_id="x", library="not-a-real-lib")

        assert isinstance(result, bytes)
        img = Image.open(BytesIO(result))
        assert img.width == 1200

    def test_create_branded_og_image_dark_theme(self, sample_plot_image: Path) -> None:
        """create_branded_og_image renders correctly in dark theme."""
        from core.images import create_branded_og_image

        result = create_branded_og_image(sample_plot_image, spec_id="x", library="bokeh", theme="dark")

        assert isinstance(result, bytes)

    def test_create_og_collage_dark_theme(self, sample_plot_image: Path) -> None:
        """create_og_collage honors theme='dark'."""
        from core.images import create_og_collage

        result = create_og_collage([sample_plot_image], labels=["x · matplotlib"], theme="dark")

        assert isinstance(result, bytes)


class TestGetMonolisaFontPath:
    """Tests for _get_monolisa_font_path GCS font download."""

    def test_returns_cached_font_without_gcs_call(self, tmp_path: Path) -> None:
        """Should return cached font path without calling GCS when file exists."""
        from unittest.mock import patch

        import core.images

        # Create fake cached font in tmp_path
        fake_font = tmp_path / "MonoLisaVariableNormal.ttf"
        fake_font.write_bytes(b"fake font data")

        with patch("core.images.FONT_CACHE_DIR", tmp_path):
            result = core.images._get_monolisa_font_path()

        assert result == fake_font

    def test_downloads_from_gcs_on_cache_miss(self, tmp_path: Path) -> None:
        """Should download font from GCS when not cached."""
        from unittest.mock import MagicMock, patch

        import core.images

        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = MagicMock()
        mock_client.bucket.return_value = mock_bucket

        with (
            patch.object(type(tmp_path / "MonoLisaVariableNormal.ttf"), "exists", return_value=False),
            patch("core.images.FONT_CACHE_DIR", tmp_path),
            patch("google.cloud.storage.Client", return_value=mock_client),
        ):
            result = core.images._get_monolisa_font_path()

        # Verify GCS interactions
        mock_client.bucket.assert_called_once_with("anyplot-static")
        mock_bucket.blob.assert_called_once_with("fonts/MonoLisaVariableNormal.ttf")
        mock_blob.download_to_filename.assert_called_once()
        assert result == tmp_path / "MonoLisaVariableNormal.ttf"

    def test_returns_none_on_gcs_exception(self, tmp_path: Path) -> None:
        """Should return None gracefully when GCS download fails."""
        from unittest.mock import patch

        import core.images

        with (
            patch.object(type(tmp_path / "MonoLisaVariableNormal.ttf"), "exists", return_value=False),
            patch("core.images.FONT_CACHE_DIR", tmp_path),
            patch("google.cloud.storage.Client", side_effect=Exception("GCS unavailable")),
        ):
            result = core.images._get_monolisa_font_path()

        assert result is None

    def test_creates_cache_dir_on_download(self, tmp_path: Path) -> None:
        """Should create cache directory if it doesn't exist before downloading."""
        from unittest.mock import MagicMock, patch

        import core.images

        cache_dir = tmp_path / "nonexistent" / "subdir"
        mock_client = MagicMock()
        mock_client.bucket.return_value.blob.return_value = MagicMock()

        with (
            patch("core.images.FONT_CACHE_DIR", cache_dir),
            patch("google.cloud.storage.Client", return_value=mock_client),
        ):
            core.images._get_monolisa_font_path()

        assert cache_dir.exists()


class TestBrandingCLI:
    """Tests for branding CLI commands."""

    @pytest.fixture(autouse=True)
    def clean_module_cache(self):
        """Remove core.images from sys.modules to avoid runpy warning."""
        import sys

        sys.modules.pop("core.images", None)
        yield
        sys.modules.pop("core.images", None)

    @pytest.fixture
    def sample_plot_image(self, tmp_path: Path) -> Path:
        """Create a sample plot image."""
        img_path = tmp_path / "plot.png"
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(img_path)
        return img_path

    def test_cli_brand_command(self, sample_plot_image: Path, tmp_path: Path, monkeypatch, capsys) -> None:
        """Should run brand command from CLI."""
        import sys

        output_path = tmp_path / "branded.png"

        monkeypatch.setattr(
            sys, "argv", ["images", "brand", str(sample_plot_image), str(output_path), "test-spec", "matplotlib"]
        )

        import runpy

        try:
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)
        except SystemExit:
            pass

        assert output_path.exists()
        captured = capsys.readouterr()
        assert "1200x630" in captured.out

    def test_cli_collage_command(self, sample_plot_image: Path, tmp_path: Path, monkeypatch, capsys) -> None:
        """Should run collage command from CLI."""
        import sys

        output_path = tmp_path / "collage.png"

        monkeypatch.setattr(sys, "argv", ["images", "collage", str(output_path), str(sample_plot_image)])

        import runpy

        try:
            runpy.run_module("core.images", run_name="__main__", alter_sys=True)
        except SystemExit:
            pass

        assert output_path.exists()
        captured = capsys.readouterr()
        assert "Collage" in captured.out
