"""Tests for `agentic.workflows.modules.regen.metadata`."""

from __future__ import annotations

import yaml

from agentic.workflows.modules.regen import QualityEval
from agentic.workflows.modules.regen.metadata import build_metadata_dict, update_impl_header, write_metadata


def _quality(score: int = 87) -> QualityEval:
    return QualityEval(
        score=score,
        vq=30,
        de=13,
        sc=15,
        dq=14,
        cq=10,
        lm=5,
        image_description="A clean scatter plot in Okabe-Ito.",
        strengths=["clean"],
        weaknesses=["minor"],
        criteria_checklist={"visual_quality": {"score": 30, "max": 30}},
        verdict="APPROVED",
    )


def test_build_metadata_includes_theme_aware_urls(tmp_path):
    md_path = tmp_path / "missing.yaml"  # does not exist; created fresh
    data = build_metadata_dict("scatter-basic", "altair", _quality(87), md_path)
    assert data["language"] == "python"
    assert data["specification_id"] == "scatter-basic"
    assert data["library"] == "altair"
    assert data["quality_score"] == 87
    assert data["preview_url_light"].endswith("/scatter-basic/python/altair/plot-light.png")
    assert data["preview_url_dark"].endswith("/scatter-basic/python/altair/plot-dark.png")
    assert data["preview_html_light"].endswith("/plot-light.html")  # altair is interactive
    assert data["preview_html_dark"].endswith("/plot-dark.html")
    assert data["review"]["verdict"] == "APPROVED"
    assert data["review"]["criteria_checklist"]["visual_quality"]["score"] == 30


def test_build_metadata_skips_html_for_static_libraries(tmp_path):
    md_path = tmp_path / "missing.yaml"
    data = build_metadata_dict("scatter-basic", "matplotlib", _quality(85), md_path)
    assert data["preview_html_light"] is None
    assert data["preview_html_dark"] is None


def test_build_metadata_preserves_existing_created_and_issue(tmp_path):
    md_path = tmp_path / "altair.yaml"
    md_path.write_text(
        yaml.safe_dump(
            {
                "library": "altair",
                "specification_id": "scatter-basic",
                "created": "2025-12-23T20:45:04Z",
                "issue": 42,
                "workflow_run": 999,
                "impl_tags": {
                    "dependencies": ["scipy"],
                    "techniques": ["layered"],
                    "patterns": [],
                    "dataprep": [],
                    "styling": [],
                },
            }
        ),
        encoding="utf-8",
    )
    data = build_metadata_dict("scatter-basic", "altair", _quality(87), md_path)
    assert data["created"] == "2025-12-23T20:45:04Z"
    assert data["issue"] == 42
    assert data["workflow_run"] == 999
    assert data["impl_tags"]["dependencies"] == ["scipy"]


def test_write_metadata_round_trips(tmp_path):
    plots = tmp_path / "plots"
    (plots / "scatter-basic" / "metadata" / "python").mkdir(parents=True)
    path = write_metadata("scatter-basic", "altair", _quality(90), plots_root=plots)
    written = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert written["quality_score"] == 90
    assert written["language"] == "python"
    assert written["review"]["criteria_checklist"]["visual_quality"]["score"] == 30


def test_update_impl_header_writes_score(tmp_path):
    plots = tmp_path / "plots"
    impl = plots / "scatter-basic" / "implementations" / "python" / "altair.py"
    impl.parent.mkdir(parents=True)
    impl.write_text(
        '"""anyplot.ai\nscatter-basic: Basic Scatter\nLibrary: altair 6.1.0 | Python 3.13.12\nQuality: /100 | Updated: 2025-12-23\n"""\n',
        encoding="utf-8",
    )
    update_impl_header("scatter-basic", "altair", 90, plots_root=plots)
    assert "Quality: 90/100 | Updated:" in impl.read_text(encoding="utf-8")
