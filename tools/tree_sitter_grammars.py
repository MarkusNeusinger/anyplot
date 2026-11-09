"""`uv run python -m tools.tree_sitter_grammars`: fetch the agents' tree-sitter grammars once, for a checkout.

tree-sitter-language-pack 1.x ships no grammars, and the agents service never downloads one
(agents/anyplot/code/treesitter.py). This fetches the pack release's bundle, whose sha256 and size the pack
checks against the release manifest, into a cache that is thrown away, and keeps only the grammars of
`GRAMMARS` in `treesitter.development_grammars_dir()`, the directory the tests and a local service load them
from. agents/Dockerfile does the same at build time; CI runs this before the tests.
"""

import os
import shutil
import tempfile
from pathlib import Path

import tree_sitter_language_pack as pack

from agents.anyplot.code import treesitter


def main() -> None:
    target = treesitter.development_grammars_dir()
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as cache:
        pack.configure(pack.PackConfig(cache_dir=cache))
        pack.download(list(treesitter.GRAMMARS))
        for library in Path(pack.cache_dir()).iterdir():
            shutil.copy2(library, target / library.name)
    os.environ[treesitter.GRAMMARS_DIR_ENV] = str(target)
    treesitter.check_grammars()
    print(f"tree-sitter grammars {', '.join(treesitter.GRAMMARS)} in {target}")


if __name__ == "__main__":
    main()
