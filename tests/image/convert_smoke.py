"""The file conversion inside the built renderer image: every format through `/opt/anyplot/harness.py --convert`.

Run by the CI job "Build renderer image and render through the harness" (`.github/workflows/ci-image.yml`):

    docker run --rm -v "$PWD:/repo:ro" anyplot-renderer:ci /app/.venv/bin/python -I /repo/tests/image/convert_smoke.py

It proves that the slimmed pyarrow (`agents/renderer/Dockerfile`) still reads Parquet, Feather and Arrow, that
calamine and NumPy read their formats, and that the guard's preload covers every reader, with the image's own venv
and harness and the sandbox's environment. Stdlib, NumPy and pyarrow only (the image has no pytest); the fixtures
come from `tests/unit/agents/runtime/convert_fixtures.py`, loaded by its path. Exits non-zero on the first failure.
"""

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as pq


HARNESS = os.environ.get("CONVERT_SMOKE_HARNESS", "/opt/anyplot/harness.py")
PYTHON = os.environ.get("CONVERT_SMOKE_PYTHON", "/app/.venv/bin/python")
"""The image's harness and venv; a developer points both at a checkout to try the script outside the image."""
FIXTURES = Path(__file__).resolve().parents[1] / "unit" / "agents" / "runtime" / "convert_fixtures.py"
ENV = {
    "PATH": "/app/.venv/bin:/usr/local/bin:/usr/bin:/bin",
    "HOME": "/tmp",
    "PYTHONDONTWRITEBYTECODE": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "ARROW_DEFAULT_MEMORY_POOL": "system",
    "ANYPLOT_RLIMIT_CPU_S": "10",
    "ANYPLOT_RLIMIT_FSIZE_MB": "50",
    "ANYPLOT_RLIMIT_AS_MB": "1024",
}


def load_fixtures():
    spec = importlib.util.spec_from_file_location("convert_fixtures", FIXTURES)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(data, sheet=None):
    """Exit code, status, text and meta of one conversion in a fresh directory."""
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        (work / "input.bin").write_bytes(data)
        if sheet is not None:
            (work / "request.json").write_text(json.dumps({"sheet": sheet}), encoding="utf-8")
        done = subprocess.run(
            [PYTHON, "-I", HARNESS, "--convert", "input.bin"],
            cwd=work,
            env=ENV,
            capture_output=True,
            text=True,
            timeout=60,
        )
        status = json.loads((work / "status.json").read_text(encoding="utf-8"))
        text = (work / "out.csv").read_text(encoding="utf-8") if status["exit"] == 0 else None
        meta = json.loads((work / "meta.json").read_text(encoding="utf-8")) if status["exit"] == 0 else None
        if done.returncode != status["exit"]:
            raise AssertionError(f"exit {done.returncode} but status {status}: {done.stderr[-500:]}")
        return status, text, meta


def expect(label, data, *, text=None, reason=None, sheet=None, check=None):
    status, got, meta = run(data, sheet)
    if reason is not None:
        assert status.get("reason") == reason, (label, status)
    else:
        assert status["exit"] == 0, (label, status)
        if text is not None:
            assert got == text, (label, got)
        if check is not None:
            check(got, meta)
    print(f"OK {label}: {status.get('reason')}")


def frame_bytes(writer, table, **options):
    buffer = io.BytesIO()
    writer(table, buffer, **options)
    return buffer.getvalue()


def main():
    fx = load_fixtures()
    expect("xlsx", fx.xlsx([fx.Sheet("S", [["Titel"], [], ["a", "b"], [1, 2.5]])]), text="Titel\n\na,b\n1,2.5\n")
    expect(
        "xlsx chosen sheet, empty sheet hidden",
        fx.xlsx([fx.Sheet("Leer"), fx.Sheet("A", [["a"]]), fx.Sheet("B", [["b"], [2]])]),
        sheet="B",
        text="b\n2\n",
        check=lambda text, meta: assert_equal(meta["sheets"], ["A", "B"]),
    )
    expect("xlsx formulas only", fx.xlsx([fx.Sheet("S", formulas={"A1": ("1+1", None)})]), reason="formulas_only")
    expect("xlsx far cell", fx.xlsx([fx.Sheet("S", [["a"]], formulas={"XFD1": ("1", "1")})]), reason="too_many_columns")
    expect("ods", fx.ods({"T": [["x", "y"], [1, 2]]}), text="x,y\n1,2\n")
    expect("zip bomb", fx.zip_bomb(), reason="archive_limits")
    expect("encrypted", fx.ole("Root Entry", "EncryptedPackage"), reason="encrypted")
    table = pa.table(
        {
            "t": pa.array([1_700_000_000_123_456_789], type=pa.timestamp("ns", "UTC")),
            "n": pa.array([2**63 - 1], type=pa.int64()),
            "f": pa.array([0.1], type=pa.float32()),
        }
    )
    expect(
        "parquet",
        frame_bytes(pq.write_table, table),
        check=lambda text, meta: assert_equal(text, f"t,n,f\n2023-11-14 22:13:20.123456789Z,{2**63 - 1},0.1\n"),
    )
    expect(
        "feather with a list column",
        frame_bytes(feather.write_feather, pa.table({"s": ["A"], "x": [[1, 2]]})),
        text='[\n{"s": "A", "x": [1, 2]}\n]\n',
    )
    stream = io.BytesIO()
    with pa.ipc.new_stream(stream, pa.schema([("a", pa.int64())])) as writer:
        writer.write_table(pa.table({"a": [1]}))
    expect("arrow stream", stream.getvalue(), text="a\n1\n")
    expect(
        "npy",
        frame_bytes(lambda array, buffer: np.save(buffer, array), np.arange(4).reshape(2, 2)),
        text="column_1,column_2\n0,1\n2,3\n",
    )
    npz = io.BytesIO()
    np.savez_compressed(npz, grid=np.ones((1, 2)))
    expect("npz", npz.getvalue(), text="column_1,column_2\n1,1\n")
    expect("pickle", b"\x80\x04K\x01.", reason="pickle")
    print("all conversions passed in the image")


def assert_equal(got, wanted):
    assert got == wanted, (got, wanted)


if __name__ == "__main__":
    os.umask(0o022)
    main()
