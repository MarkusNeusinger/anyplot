"""The example pairs of `/agent` without a plot must name implementations that exist.

The explainer (`app/src/sections/agent-chat/AgentIntro.tsx`) links a few catalogue pairs straight into the chat. A
pair whose implementation is renamed or removed would leave a link that opens a chat on nothing, and no frontend test
would notice, because the page's tests stub the API. So the pairs are read from the source here, the way
`test_readme_claims.py` reads `AboutPage.tsx`, and each must resolve to a file under `plots/`. Scores are not checked:
they change with every regeneration, and the pairs were picked for being above the bar, not pinned to it.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.constants import LIBRARY_LANGUAGES, library_file_extension


ROOT = Path(__file__).resolve().parents[2]
AGENT_INTRO = ROOT / "app" / "src" / "sections" / "agent-chat" / "AgentIntro.tsx"

EXAMPLES_BLOCK = re.compile(r"const AGENT_EXAMPLES = \[(?P<body>.*?)\] as const;", re.DOTALL)
PAIR = re.compile(r"\{\s*spec:\s*'(?P<spec>[a-z0-9-]+)',\s*library:\s*'(?P<library>[a-z0-9]+)'\s*\}")


def example_pairs() -> list[tuple[str, str]]:
    block = EXAMPLES_BLOCK.search(AGENT_INTRO.read_text(encoding="utf-8"))
    assert block is not None, "AgentIntro.tsx has no `const AGENT_EXAMPLES = [...] as const;`"
    pairs = [(match["spec"], match["library"]) for match in PAIR.finditer(block["body"])]
    # A pair written in another shape would otherwise be skipped without a sound.
    assert len(pairs) == block["body"].count("spec:"), "an AGENT_EXAMPLES entry is not `{ spec: '…', library: '…' }`"
    return pairs


def test_the_examples_are_read_from_the_source():
    # Guards the two tests below against passing on an empty list after a refactor of the constant.
    assert len(example_pairs()) >= 1


def test_every_example_names_a_catalogue_implementation():
    for spec, library in example_pairs():
        assert library in LIBRARY_LANGUAGES, f"{library} is not a catalogue library"
        path = ROOT / "plots" / spec / "implementations" / LIBRARY_LANGUAGES[library]
        path = path / f"{library}{library_file_extension(library)}"
        assert path.is_file(), f"{spec} in {library}: {path.relative_to(ROOT)} does not exist"


def test_the_examples_show_one_language_each():
    languages = [LIBRARY_LANGUAGES[library] for _, library in example_pairs()]
    assert len(set(languages)) == len(languages), f"two examples share a language: {languages}"
