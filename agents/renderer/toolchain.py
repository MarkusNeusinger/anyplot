"""The toolchain image's tag: a hash of everything its build reads (agentic/specs/261024-agent-all-libraries.md, step 2a).

`agents/renderer/toolchain.Dockerfile` builds `anyplot-toolchain`, the base of the renderer image
(`FROM ${TOOLCHAIN_IMAGE}:${TOOLCHAIN_TAG}`).
It is built only when this tag is missing from the private Artifact Registry repository: the deploy
(`agents/renderer/cloudbuild.yaml`) and the CI job (`ci-image.yml`, `renderer-image`) ask for
`anyplot-toolchain:<tag>`, build and push it when it is not there, and build the renderer FROM it, passing
`TOOLCHAIN_IMAGE` (the repository) and `TOOLCHAIN_TAG` (the tag with its digest). A change to any input (the
Dockerfile with its pinned base digest and R version, a package list, the exec filter's source) is a new tag, so a
deploy rebuilds the toolchain exactly when it has to and never otherwise.

Standard library only: the Cloud Build step runs it with the builder image's `python3`, which has none of the
project's dependencies.

    python3 agents/renderer/toolchain.py tag          # t-<16 hex digits>
    python3 agents/renderer/toolchain.py repository   # europe-west4-docker.pkg.dev/anyplot/anyplot/anyplot-toolchain
    python3 agents/renderer/toolchain.py image        # the repository and the tag, `<repository>:<tag>`
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


REPOSITORY = "europe-west4-docker.pkg.dev/anyplot/anyplot/anyplot-toolchain"
"""The toolchain image's name in the private Artifact Registry repository, next to the renderer image."""
INPUTS = ("agents/renderer/toolchain.Dockerfile", "agents/renderer/toolchain", "agents/renderer/execdeny")
"""The files and directories the toolchain build reads from its context, relative to the repository root."""
ROOT = Path(__file__).resolve().parents[2]


def input_files(root: Path = ROOT) -> list[Path]:
    """Every file under `INPUTS`, sorted by its path relative to `root`; a missing input is an error, never skipped."""
    files: list[Path] = []
    for name in INPUTS:
        path = root / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file() and "__pycache__" not in child.parts)
        else:
            raise FileNotFoundError(f"toolchain input missing: {name}")
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def toolchain_tag(root: Path = ROOT) -> str:
    """`t-` and the first 16 hex digits of a SHA-256 over each input's relative path and bytes."""
    digest = hashlib.sha256()
    for path in input_files(root):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"t-{digest.hexdigest()[:16]}"


def main(argv: list[str]) -> int:
    answers = {
        "tag": toolchain_tag,
        "repository": lambda: REPOSITORY,
        "image": lambda: f"{REPOSITORY}:{toolchain_tag()}",
    }
    if len(argv) == 1 and argv[0] in answers:
        print(answers[argv[0]]())
        return 0
    print("usage: toolchain.py tag|repository|image", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
