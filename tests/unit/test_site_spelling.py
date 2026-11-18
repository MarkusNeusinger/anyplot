"""The site spells the colour-blindness words in British English, as the style guide's voice section asks.

Every text a visitor, a crawler or a search engine reads says "colourblind-safe", "colour blindness" and "colour
vision": the frontend's pages and sections, the SPA shell with its descriptions, keywords and structured data, the
public files, and the crawler copies in `api/routers/seo.py`. So does the style guide that governs them, apart from its
academic references and its addresses, which keep their own spelling. The wider British sweep of the site is still to
come, so this test holds only these words.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
STYLE_GUIDE = ROOT / "docs" / "reference" / "style-guide.md"

# The American forms. Case-sensitive after the first letter, so an identifier such as `colorBlind` is no hit.
AMERICAN = re.compile(r"\b[Cc]olor(?:blind|-blind| blind| vision)")


def _site_files() -> list[Path]:
    sources = [
        path
        for folder in (APP / "src" / "pages", APP / "src" / "sections")
        for path in sorted(folder.rglob("*"))
        if path.suffix in {".ts", ".tsx", ".json"} and ".test." not in path.name
    ]
    public = [path for path in sorted((APP / "public").rglob("*")) if path.suffix in {".txt", ".svg", ".json"}]
    return [*sources, APP / "index.html", *public, ROOT / "api" / "routers" / "seo.py"]


def test_the_site_spells_the_colour_blindness_words_in_british_english():
    files = _site_files()
    assert APP / "src" / "pages" / "PalettePage.tsx" in files, "the sweep no longer reaches the frontend's pages"
    hits = [
        f"{path.relative_to(ROOT)}:{number}: {line.strip()}"
        for path in files
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if AMERICAN.search(line)
    ]
    assert not hits, "American spelling of a colour-blindness word:\n" + "\n".join(hits)


def test_the_style_guide_states_the_rule_and_follows_it():
    guide = STYLE_GUIDE.read_text(encoding="utf-8")
    voice = re.search(r"^### 3\.4 Voice & Tone\n(.*?)^#", guide, re.MULTILINE | re.DOTALL)
    assert voice, "style-guide.md no longer has section 3.4, Voice & Tone"
    assert "Spelling: British English on the site" in voice.group(1), "style-guide.md 3.4: the spelling rule"
    # Citations and addresses keep their own spelling: Wong's "Color blindness", the Coblis simulator's domain.
    own_text = re.sub(r"https?://\S+", "", guide.split("\n## 14. Academic References\n", 1)[0])
    hits = [line.strip() for line in own_text.splitlines() if AMERICAN.search(line)]
    assert not hits, f"style-guide.md spells a colour-blindness word the American way: {hits}"
