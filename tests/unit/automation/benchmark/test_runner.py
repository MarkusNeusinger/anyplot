"""Tests for automation.benchmark.runner."""

import os
import textwrap

from PIL import Image

from automation.benchmark.runner import check_canvas, render_env, run_python_implementation


def _write_png(path, width, height):
    Image.new("RGB", (width, height), color=(0, 158, 115)).save(path)


class TestCheckCanvas:
    def test_exact_landscape_target(self, tmp_path):
        png = tmp_path / "plot.png"
        _write_png(png, 3200, 1800)
        assert check_canvas(png) is True

    def test_exact_square_target(self, tmp_path):
        png = tmp_path / "plot.png"
        _write_png(png, 2400, 2400)
        assert check_canvas(png) is True

    def test_within_tolerance(self, tmp_path):
        png = tmp_path / "plot.png"
        _write_png(png, 3200 - 16, 1800 + 16)
        assert check_canvas(png) is True

    def test_drifted_canvas_fails(self, tmp_path):
        png = tmp_path / "plot.png"
        _write_png(png, 3000, 1800)
        assert check_canvas(png) is False


class TestRenderEnv:
    def test_secrets_are_not_inherited(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAKE_GCP_CREDENTIAL", "super-secret")
        env = render_env("light", home=tmp_path)
        assert "FAKE_GCP_CREDENTIAL" not in env

    def test_theme_and_backend_are_set(self, tmp_path):
        env = render_env("dark", home=tmp_path)
        assert env["ANYPLOT_THEME"] == "dark"
        assert env["MPLBACKEND"] == "Agg"

    def test_path_passes_through(self, tmp_path):
        assert "PATH" in render_env("light", home=tmp_path)

    def test_home_is_remapped_to_scratch_dir(self, tmp_path):
        # The caller's real HOME (~/.config with gcloud credentials, …) must
        # not be visible to LLM-generated code.
        env = render_env("light", home=tmp_path)
        assert env["HOME"] == str(tmp_path)
        assert env["HOME"] != os.environ.get("HOME")


class TestRunPythonImplementation:
    def _write_script(self, tmp_path, body):
        script = tmp_path / "impl.py"
        script.write_text(textwrap.dedent(body), encoding="utf-8")
        return script

    def test_successful_render(self, tmp_path):
        script = self._write_script(
            tmp_path,
            """
            import os
            from PIL import Image
            theme = os.getenv("ANYPLOT_THEME", "light")
            Image.new("RGB", (100, 100)).save(f"plot-{theme}.png")
            """,
        )
        result = run_python_implementation(script, workdir=tmp_path, timeout=60)
        assert result.success is True
        assert result.canvas_ok is False  # 100x100 is far off both canonical targets
        assert set(result.images) == {"light", "dark"}

    def test_failing_script_reports_stderr(self, tmp_path):
        script = self._write_script(tmp_path, "raise SystemExit('boom')")
        result = run_python_implementation(script, workdir=tmp_path, timeout=60)
        assert result.success is False
        assert "exited 1" in result.error
        assert "boom" in result.error

    def test_missing_png_is_an_error(self, tmp_path):
        script = self._write_script(tmp_path, "print('renders nothing')")
        result = run_python_implementation(script, workdir=tmp_path, timeout=60)
        assert result.success is False
        assert "wrote no plot-light.png" in result.error

    def test_generated_code_does_not_see_caller_secrets(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FAKE_GCP_CREDENTIAL", "super-secret")
        script = self._write_script(
            tmp_path,
            """
            import os
            from PIL import Image
            assert "FAKE_GCP_CREDENTIAL" not in os.environ, "secret leaked into render env"
            theme = os.getenv("ANYPLOT_THEME", "light")
            Image.new("RGB", (10, 10)).save(f"plot-{theme}.png")
            """,
        )
        result = run_python_implementation(script, workdir=tmp_path, timeout=60)
        assert result.success is True
