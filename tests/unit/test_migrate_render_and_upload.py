"""scripts/migrate_render_and_upload.py promotes the `plot-*` renders only, as impl-merge does.

Its staging folder is the pipeline's, which may also hold `render.sha256` and
the private `adapt/` records; neither may reach production.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_render_and_upload.py"


def test_promotion_copies_only_the_renders(monkeypatch):
    spec = importlib.util.spec_from_file_location("migrate_render_and_upload", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)  # its dataclasses look the module up
    spec.loader.exec_module(module)
    calls: list[list[str]] = []
    monkeypatch.setattr(module, "_gsutil", lambda args, check=True: calls.append(args))
    module.promote_to_production("gs://b/staging/s/python/l", "gs://b/plots/s/python/l")
    (copy,) = [args for args in calls if "cp" in args]
    assert copy[copy.index("cp") + 1 :] == ["gs://b/staging/s/python/l/plot-*", "gs://b/plots/s/python/l/"]
    assert "-r" not in copy
