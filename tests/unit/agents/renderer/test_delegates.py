"""The delegate check of the renderer image: no program lets-plot's native ImageMagick can start is on the sandbox PATH."""

from pathlib import Path

import pytest

from agents.renderer import delegates
from agents.renderer.executor import SANDBOX_PATH


REPO_ROOT = Path(__file__).resolve().parents[4]


def test_a_clean_path_passes(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(delegates.shutil, "which", lambda name, path=None: None)

    assert delegates.main() == 0
    assert f"none of {len(delegates.DELEGATE_PROGRAMS)} delegate programs on {SANDBOX_PATH}" in capsys.readouterr().out


def test_a_delegate_on_the_sandbox_path_fails_and_is_named(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    looked_up: list[str | None] = []

    def which(name: str, path: str | None = None) -> str | None:
        looked_up.append(path)
        return "/usr/bin/gs" if name == "gs" else None

    monkeypatch.setattr(delegates.shutil, "which", which)

    assert delegates.main() == 1
    assert "gs (/usr/bin/gs)" in capsys.readouterr().out
    assert set(looked_up) == {SANDBOX_PATH}  # the sandbox's PATH, never the process's own


def test_the_list_covers_the_review_s_programs() -> None:
    reviewed = {"gs", "curl", "soffice", "ffmpeg", "inkscape", "rsvg-convert", "fc-list", "magick", "convert", "node"}

    assert reviewed <= set(delegates.DELEGATE_PROGRAMS)
    assert len(set(delegates.DELEGATE_PROGRAMS)) == len(delegates.DELEGATE_PROGRAMS)


def test_node_stays_refused_and_the_javascript_row_runs_it_by_its_path() -> None:
    """JS-1 of step 3 ships Node in the image, outside `SANDBOX_PATH`: the row names its absolute path, so a `node`
    found by name on the sandbox's PATH is still a delegate to refuse."""
    from agents.renderer.commands import NODE_BINARY, command_for

    assert "node" in delegates.DELEGATE_PROGRAMS
    assert NODE_BINARY.startswith("/") and NODE_BINARY.rsplit("/", 1)[0] not in SANDBOX_PATH.split(":")
    assert command_for("javascript", "d3").argv[0] == NODE_BINARY


def test_every_build_of_the_image_runs_the_check() -> None:
    """The Dockerfile runs it, so the Cloud Build deploy enforces it as well as the CI job, which runs it again."""
    dockerfile = (REPO_ROOT / "agents" / "renderer" / "Dockerfile").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-image.yml").read_text(encoding="utf-8")

    assert "RUN .venv/bin/python -m agents.renderer.delegates" in dockerfile
    assert dockerfile.index("COPY agents/renderer/ ./agents/renderer/") < dockerfile.index(
        "-m agents.renderer.delegates"
    )
    assert "/app/.venv/bin/python -m agents.renderer.delegates" in workflow
