"""The harness's data mode (`harness.py --data snippet.py`): `df` to `out.csv` under the audit-hook guard.

Every case runs the real harness in a subprocess with the test interpreter, because the
guard is an audit hook, which can never be removed from the process that arms it.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from agents.anyplot.data.parse import MAX_INPUT_BYTES
from agents.anyplot.render import harness
from agents.anyplot.render.runtimes.python import HARNESS_SOURCE
from agents.anyplot.schemas import MAX_COLUMNS, MAX_ROWS


EXIT = harness.DATA_EXIT


def run(tmp_path: Path, code: str) -> tuple[int, str | None, str]:
    """Exit code, `out.csv` (None when missing) and stderr of one data-mode run in `tmp_path`."""
    (tmp_path / "snippet.py").write_text(code, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", str(HARNESS_SOURCE), harness.DATA_FLAG, "snippet.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "ANYPLOT_RLIMIT_CPU_S": "60"},
    )
    out = tmp_path / harness.DATA_OUT_FILE
    return done.returncode, out.read_text(encoding="utf-8") if out.exists() else None, done.stderr


def test_caps_are_the_parsers() -> None:
    assert harness.DATA_MAX_ROWS == MAX_ROWS
    assert harness.DATA_MAX_COLUMNS == MAX_COLUMNS
    assert harness.DATA_MAX_CSV_BYTES == MAX_INPUT_BYTES


def test_exit_codes_are_distinct() -> None:
    assert len(set(EXIT.values())) == len(EXIT)
    assert EXIT["ok"] == 0


class TestFrame:
    def test_df_becomes_csv(self, tmp_path: Path) -> None:
        code = "import numpy as np\nimport pandas as pd\nx = np.arange(3)\ndf = pd.DataFrame({'x': x, 'y': x * 2})\n"
        assert run(tmp_path, code)[:2] == (EXIT["ok"], "x,y\n0,0\n1,2\n2,4\n")

    def test_scipy_and_random_work_under_the_guard(self, tmp_path: Path) -> None:
        code = (
            "import random\nimport numpy as np\nimport pandas as pd\nfrom scipy import stats\nrandom.seed(1)\n"
            "x = np.linspace(-1, 1, 3)\ndf = pd.DataFrame({'x': x, 'p': stats.norm.pdf(x), 'r': random.random()})\n"
        )
        code_, out, stderr = run(tmp_path, code)
        assert code_ == EXIT["ok"], stderr
        assert out is not None and out.startswith("x,p,r\n")

    def test_a_named_index_becomes_a_column(self, tmp_path: Path) -> None:
        code = "import pandas as pd\ndf = pd.DataFrame({'v': [1, 2]}, index=pd.Index(['a', 'b'], name='k'))\n"
        assert run(tmp_path, code)[:2] == (EXIT["ok"], "k,v\na,1\nb,2\n")

    def test_a_default_index_is_not_written(self, tmp_path: Path) -> None:
        assert run(tmp_path, "import pandas as pd\ndf = pd.DataFrame({'v': [5]})\n")[1] == "v\n5\n"

    def test_column_names_become_text(self, tmp_path: Path) -> None:
        assert run(tmp_path, "import pandas as pd\ndf = pd.DataFrame({0: [1], 'b': [2]})\n")[1] == "0,b\n1,2\n"

    def test_multiindex_columns_are_refused(self, tmp_path: Path) -> None:
        code = (
            "import pandas as pd\n"
            "df = pd.DataFrame([[1, 2]], columns=pd.MultiIndex.from_tuples([('a', 'b'), ('a', 'c')]))\n"
        )
        assert run(tmp_path, code)[0] == EXIT["frame_shape"]

    def test_an_index_clashing_with_a_column_is_refused(self, tmp_path: Path) -> None:
        code = "import pandas as pd\ndf = pd.DataFrame({'k': [1]}, index=pd.Index(['a'], name='k'))\n"
        assert run(tmp_path, code)[0] == EXIT["frame_shape"]

    @pytest.mark.parametrize("code", ["x = 1\n", "df = [1, 2]\n", "import numpy as np\ndf = np.zeros(3)\n"])
    def test_no_frame(self, tmp_path: Path, code: str) -> None:
        assert run(tmp_path, code)[0] == EXIT["no_frame"]

    def test_too_many_rows(self, tmp_path: Path) -> None:
        code = f"import pandas as pd\ndf = pd.DataFrame({{'a': range({MAX_ROWS + 1})}})\n"
        assert run(tmp_path, code)[0] == EXIT["too_many_rows"]

    def test_too_many_columns(self, tmp_path: Path) -> None:
        code = f"import pandas as pd\ndf = pd.DataFrame({{f'c{{i}}': [i] for i in range({MAX_COLUMNS + 1})}})\n"
        assert run(tmp_path, code)[0] == EXIT["too_many_columns"]

    def test_too_large(self, tmp_path: Path) -> None:
        code = "import pandas as pd\ndf = pd.DataFrame({'a': ['x' * 50] * 10000})\n"
        assert run(tmp_path, code)[0] == EXIT["too_large"]


class TestErrors:
    def test_exception_exits_error_with_a_traceback(self, tmp_path: Path) -> None:
        exit_code, out, stderr = run(tmp_path, "import pandas as pd\nx = 1\nraise ValueError('boom')\n")
        assert exit_code == EXIT["error"]
        assert out == ""
        assert 'snippet.py", line 3' in stderr and "ValueError" in stderr

    @pytest.mark.parametrize("code", ["raise SystemExit(0)\n", "raise SystemExit(8)\n", "raise KeyboardInterrupt\n"])
    def test_the_snippet_never_chooses_the_exit_code(self, tmp_path: Path, code: str) -> None:
        assert run(tmp_path, code)[0] == EXIT["error"]


class TestGuard:
    @pytest.mark.parametrize(
        "code",
        [
            pytest.param("import ctypes\nctypes.CDLL(None)\n", id="ctypes CDLL"),
            pytest.param("import ctypes\nctypes.string_at(1, 1)\n", id="ctypes raw memory"),
            pytest.param("import numpy as np\nlib = np.zeros(1).ctypes._ctypes.CDLL(None)\n", id="numpy ctypes"),
            pytest.param("import subprocess\nsubprocess.run(['true'])\n", id="subprocess"),
            pytest.param("import os\nos.system('true')\n", id="os.system"),
            pytest.param("import os\nos.execv('/bin/true', ['true'])\n", id="os.exec"),
            pytest.param("import os\nos.posix_spawn('/bin/true', ['true'], {})\n", id="os.posix_spawn"),
            pytest.param("import socket\nsocket.socket()\n", id="socket"),
            pytest.param("import socket\nsocket.getaddrinfo('localhost', 80)\n", id="name lookup"),
            pytest.param("open('x.txt', 'w').write('x')\n", id="open for writing"),
            pytest.param("open('x.txt', 'a')\n", id="open for appending"),
            pytest.param("import os\nos.open('x.txt', os.O_CREAT | os.O_WRONLY)\n", id="os.open for writing"),
            pytest.param("import os\nos.remove('snippet.py')\n", id="remove"),
            pytest.param("import os\nos.mkdir('d')\n", id="mkdir"),
            pytest.param("import pandas as pd\npd.DataFrame({'a': [1]}).to_csv('x.csv')\n", id="pandas writer"),
        ],
    )
    def test_refused(self, tmp_path: Path, code: str) -> None:
        exit_code, _, stderr = run(tmp_path, code)
        assert exit_code == EXIT["blocked"], stderr
        assert not (tmp_path / "x.txt").exists() and not (tmp_path / "x.csv").exists()

    def test_a_caught_refusal_still_refuses_the_run(self, tmp_path: Path) -> None:
        code = (
            "import pandas as pd\ntry:\n    open('x.txt', 'w')\nexcept Exception:\n    pass\n"
            "df = pd.DataFrame({'a': [1]})\n"
        )
        assert run(tmp_path, code)[:2] == (EXIT["blocked"], "")

    def test_reading_is_allowed(self, tmp_path: Path) -> None:
        (tmp_path / "in.txt").write_text("7", encoding="utf-8")
        code = "import pandas as pd\ndf = pd.DataFrame({'a': [int(open('in.txt').read())]})\n"
        assert run(tmp_path, code)[:2] == (EXIT["ok"], "a\n7\n")


class TestGuardUnit:
    def test_refuses(self) -> None:
        guard = harness.DataGuard()
        assert guard.refuses("open", ("f", "w", 0))
        assert guard.refuses("open", ("f", "rb+", 0))
        assert not guard.refuses("open", ("f", "r", 0))
        assert not guard.refuses("open", ("f", "rb", 0))
        assert guard.refuses("open", ("f", None, harness.os.O_WRONLY))
        assert not guard.refuses("open", ("f", None, harness.os.O_RDONLY))
        assert guard.refuses("ctypes.dlopen", ("libc",))
        assert guard.refuses("socket.connect", ())
        assert not guard.refuses("import", ("numpy",))
        assert not guard.refuses("os.listdir", (".",))

    def test_unarmed_guard_lets_everything_through(self) -> None:
        guard = harness.DataGuard()
        guard("ctypes.dlopen", ("libc",))
        assert guard.blocked is None

    def test_armed_guard_raises_and_remembers(self) -> None:
        guard = harness.DataGuard()
        guard.armed = True  # never `arm()` in the test process: an audit hook cannot be removed
        with pytest.raises(RuntimeError):
            guard("socket.connect", ())
        guard("os.listdir", (".",))
        assert guard.blocked == "socket"
