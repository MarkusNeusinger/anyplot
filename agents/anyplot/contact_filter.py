"""Contact details in text: web addresses, e-mail addresses and phone numbers, found without a network or a model.

Text that a user or a model writes can reach other people: the root's reply, the
change request the root writes for the adapter, the string literals and comments the
adapter puts into the plot (and so into the watermarked PNG and `plot.py`), and the
headers and cells of a pasted dataset, which reach the plot as labels. A scam graphic
needs a way to reach its author, so these places refuse or strip contact details (the
guardrail audit of 2026-10-10, findings 2 and 4):

* `output_guard.sanitize` strips them from every root message and plot-event line;
* ToolSafety refuses a `change_request` that carries one;
* the pipeline rejects a plan whose new string literals or comments carry one;
* the `/dataset` route refuses a dataset that carries one in a header or a cell.

Before matching, every character is folded: NFKC (fullwidth letters and `＠`, no-break
and narrow no-break spaces), the ideographic full stop and the dashes become `.` and
`-`, and zero-width characters drop out. Spans still index the original text.

What counts, case-insensitively:

* **Web address**: one or more dot-separated labels ending in a top-level domain from
  `TLDS` (every two-letter country code plus a curated list of generic ones), with an
  optional port and path: `securebank.com/login`, `parcel-help.com/pay`, `t.me/x`. A
  chain followed by `(` or by a further `.name` is code (`df.info()`,
  `g.ax.set_title`). Leading labels that are code names (`CODE_NAMES`) are code, not a
  host, so these rules decide the rest:
  * a chain of code names only is a host behind a `HOST_TLDS` domain
    (`matplotlib.org`), or with a path after a single code name (`math.win/prize`);
    `df.at`, `plt.cm`, `pd.NA` and `ax.spines.top/right` stay code;
  * after the code names, the rest is a host of its own when it has a path, a label
    with a hyphen or a digit, two or more labels, or a country code as its
    top-level domain: `ax.parcel-help.de`, `ax.securebank.de`,
    `np.securebank.co.uk`, `df.securebank.xyz/login`; `fig.subplotpars.top` stays
    code.
  A country code that is also an English word or a file extension (`PATH_ONLY_TLDS`:
  `plot.py`, `README.md`, `the plot.It`) counts with a path, or with a hyphen or a
  digit in a label or two or more labels (`dhl-zoll.at`, `shop.dhl.at`), unless it is
  a file extension (`FILE_TLDS`: `my-plot.py`) or written as a capitalised word
  (`long-term.It`). URLs with a scheme or `www.` are caught by the sanitisers' own
  patterns and by this one alike. A brand that is a domain (`Amazon.com`) counts too:
  plot text names the brand without its domain.
* **E-mail address**: `local@host.tld` with any alphabetic top-level domain.
* **Phone number**: an international number (`+49 30 1234567`, `0049 30 1234567`,
  `(+49) 30 1234567`, `+1 (555) 010-0100`), a domestic one with a leading zero
  (`030 1234567`, `0800-123-4567`, `030 / 123 456 78`, `(030) 123456`) or a North
  American one (`212-555-0100`, `(212) 555-0100`, `1-800-555-0100`), with 7 to 15
  digits in all; after a phone word (`call`, `Tel.`, `phone`, `anrufen`, ...) also a
  run of 9 to 12 digits with a leading zero (`0301234567`) or a North American number
  with spaces (`800 555 0100`). A digit group that continues a longer hyphenated or
  dotted number (`2024-001-0042`) does not start or end one, and North American area
  and exchange codes start with 2 to 9 (`100-200-3000` is a range). Dates, decimals,
  years and tick values do not match. The digit groups of an IBAN match too: plot
  text has no business carrying payment details either.

The lists live in code on purpose: no lookup, no download, the same answer offline.
"""

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal


ContactKind = Literal["web", "email", "phone"]
CONTACT_NAMES: dict[str, str] = {"email": "e-mail address", "phone": "phone number", "web": "web address"}
"""Each kind in words, for repair feedback."""

COUNTRY_TLDS: frozenset[str] = frozenset(
    """
    ac ad ae af ag ai al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bm bn bo bq br bs bt bw by
    bz ca cc cd cf cg ch ci ck cl cm cn co cr cu cv cw cx cy cz de dj dk dm do dz ec ee eg er es et eu fi fj
    fk fm fo fr ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs gt gu gw gy hk hm hn hr ht hu id ie il im in io
    iq ir is it je jm jo jp ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lu lv ly ma mc md me mg
    mh mk ml mm mn mo mp mq mr ms mt mu mv mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph
    pk pl pm pn pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sk sl sm sn so sr ss st su sv sx sy
    sz tc td tf tg th tj tk tl tm tn to tr tt tv tw tz ua ug uk us uy uz va vc ve vg vi vn vu wf ws ye yt za
    zm zw
    """.split()
)
"""Every two-letter country-code top-level domain."""

GENERIC_TLDS: frozenset[str] = frozenset(
    """
    com net org info biz edu gov mil mobi pro tel asia travel jobs aero coop museum
    app dev xyz online site website shop store top club live link click help support pay bank money finance
    financial loan loans credit win vip icu cyou sbs buzz rest today email network cloud tech page bond cfd
    lol work fun monster quest mom beauty uno digital agency company services solutions center world life
    news blog media studio games bet casino poker xxx sex porn adult dating lat ltd inc llc group ink wiki
    zip mov one plus space store team tips best deals sale promo gift gifts claim delivery express courier
    review party stream science download trade zone fyi host market cam racing faith bid webcam kim gdn
    berlin hamburg bayern nrw koeln wien swiss london nyc paris
    """.split()
)
"""Generic top-level domains: the classic ones, the ones spam and phishing use most, and a few city ones.
Generic domains that read as code (`.name`, `.int`, `.cat`, `.style`, `.show`, `.map`, `.date`) are left
out on purpose: `row.name` and `event.date` are attributes far more often than hosts."""

TLDS: frozenset[str] = COUNTRY_TLDS | GENERIC_TLDS

FILE_TLDS: frozenset[str] = frozenset({"am", "cc", "md", "mk", "ps", "py", "rs", "sh"})
"""Country codes that are also file extensions (`plot.py`, `README.md`): a host only with a path."""

PATH_ONLY_TLDS: frozenset[str] = FILE_TLDS | frozenset(
    {"as", "at", "ax", "be", "by", "do", "id", "in", "is", "it", "me", "my", "no", "pl", "so", "to", "us"}
)
"""Country codes that are also English words, code names or file extensions; see the module docstring."""

CODE_NAMES: frozenset[str] = frozenset(
    """
    ax axs axes df fig plt np pd sns mpl matplotlib seaborn numpy pandas scipy stats spines self os math
    xaxis yaxis ticker dates colors cm patches lines style rc rcparams series frame figure
    data row col item value values obj result args kwargs cfg config params legend title text label labels
    grid ticks index
    """.split()
)
"""First labels that make a dotted chain code rather than a host name (`df.at`, `plt.cm`, `ax.spines.top`)."""

HOST_TLDS: frozenset[str] = frozenset({"com", "net", "org", "edu", "gov"})
"""Top-level domains no attribute is named after: behind one, even a code name is a host (`matplotlib.org`).
`info` and `biz` are not among them: `df.info` is code."""

MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 15  # E.164

_HOST = re.compile(
    r"(?<![\w@.-])"
    r"(?P<labels>(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+)"
    r"(?P<tld>[a-z]{2,24})(?![\w-])(?!\.[a-z0-9])(?!\()"
    r"(?P<port>:\d{2,5})?"
    r"(?P<path>/(?:[^\s<>\"']*[^\s<>\"'.,;:!?)\]])?)?",
    re.IGNORECASE,
)
_EMAIL = re.compile(
    r"(?<![\w.%+-])[a-z0-9._%+-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,24}\b",
    re.IGNORECASE,
)
_SEP = r"(?:[ \t]*[/-][ \t]*|[ .])"
"""Between two digit groups: a space or a dot, or a slash or a hyphen with optional spaces around it."""
_NOT_INSIDE_A_NUMBER = r"(?<![\w+(])(?<!\d[-./,])"
_NOT_CONTINUED = r"(?!\w)(?![-./,]\d)"
_PHONE = re.compile(
    _NOT_INSIDE_A_NUMBER + r"(?:"
    rf"\+\d{{1,3}}(?:{_SEP}?\(\d{{1,5}}\))?(?:{_SEP}?\d{{2,}}){{2,}}"  # +49 30 1234567, +1 (555) 010-0100
    rf"|00\d{{1,3}}(?:{_SEP}?\(\d{{1,5}}\))?(?:{_SEP}\d{{2,}}){{2,}}"  # 0049 30 1234567, not the id 0012345678
    rf"|\(\+\d{{1,3}}\)(?:{_SEP}?\d{{2,}}){{2,}}"  # (+49) 30 1234567
    rf"|\(0\d{{1,4}}\){_SEP}?\d{{3,}}(?:{_SEP}\d{{2,}})*"  # (030) 123456
    r"|\([2-9]\d{2}\)[ .-]?[2-9]\d{2}[ .-]\d{4}"  # (212) 555-0100
    rf"|0\d{{2,5}}{_SEP}\d{{3,}}(?:{_SEP}\d{{2,}})*"  # 030 1234567, 0800-123-4567, 030 / 123 456 78
    r"|1[ .-][2-9]\d{2}[ .-][2-9]\d{2}[ .-]\d{4}"  # 1-800-555-0100
    r"|[2-9]\d{2}[.-][2-9]\d{2}[.-]\d{4}"  # 212-555-0100
    r")" + _NOT_CONTINUED
)
_PHONE_AFTER_WORD = re.compile(
    r"(?i)\b(?:tel|telefon|telephone|phone|call|ring|hotline|whatsapp|sms|fon|mobil|mobile|handy|anrufen)\b"
    r"[.:]*[ \t]*(?P<number>0[1-9]\d{7,10}|[2-9]\d{2}[ .][2-9]\d{2}[ .]\d{4})" + _NOT_CONTINUED
)
"""A number only a phone word marks as one: `Call 0301234567`, `Tel. 800 555 0100`."""
_SPACES = re.compile(r"(?<=\S)[ \t]{2,}")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+([,.;:!?])")
_ZERO_WIDTH = frozenset("­​‌‍⁠﻿")
_DASHES = frozenset("‐‑‒–—―−﹣－")
_FULL_STOPS = frozenset("。｡")


@dataclass(frozen=True, slots=True)
class Contact:
    """One contact detail found in a text: its kind and its span."""

    kind: ContactKind
    start: int
    end: int


@lru_cache(maxsize=4096)
def _fold_char(char: str) -> str:
    if char in _ZERO_WIDTH:
        return ""
    if char in _DASHES:
        return "-"
    folded = unicodedata.normalize("NFKC", char)
    return "." if folded in _FULL_STOPS else folded


def _fold(text: str) -> tuple[str, list[int] | None]:
    """`text` folded for matching, and the original index of every folded character (None: unchanged)."""
    if text.isascii():
        return text, None
    pieces: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        folded = _fold_char(char)
        pieces.append(folded)
        origin.extend([index] * len(folded))
    origin.append(len(text))
    return "".join(pieces), origin


def _looks_registered(labels: list[str], tld: str) -> bool:
    """Whether the labels left after the code names read as a registered name rather than an attribute."""
    return (
        len(labels) >= 2
        or any("-" in label or any(c.isdigit() for c in label) for label in labels)
        or (tld in COUNTRY_TLDS and tld not in PATH_ONLY_TLDS)
    )


def _is_host(match: re.Match[str]) -> bool:
    labels = match.group("labels").rstrip(".").split(".")
    written_tld = match.group("tld")
    tld = written_tld.lower()
    if tld not in TLDS:
        return False
    if not any(re.search(r"[a-z]", label, re.IGNORECASE) for label in labels):
        return False  # 1.2.de, a number with a country code glued to it
    has_path = len(match.group("path") or "") > 1
    code = 0
    while code < len(labels) and labels[code].lower() in CODE_NAMES:
        code += 1
    if code:
        rest = labels[code:]
        if not rest:
            return tld in HOST_TLDS or (has_path and code == 1)
        if not has_path and not _looks_registered(rest, tld):
            return False
        labels = rest
    if tld not in PATH_ONLY_TLDS or labels[0].lower() == "www" or has_path:
        return True
    if tld in FILE_TLDS or written_tld.istitle() or len(labels[-1]) < 2:
        return False
    return len(labels) >= 2 or any("-" in label or any(c.isdigit() for c in label) for label in labels)


def _phone_digits(text: str) -> int:
    return sum(character.isdigit() for character in text)


def find_contacts(text: str) -> list[Contact]:
    """Every contact detail in `text`, in order and without overlaps (e-mail first, then web, then phone)."""
    folded, origin = _fold(text)
    spans: list[tuple[ContactKind, int, int]] = [("email", m.start(), m.end()) for m in _EMAIL.finditer(folded)]

    def free(start: int, end: int) -> bool:
        return all(end <= other_start or start >= other_end for _, other_start, other_end in spans)

    for match in _HOST.finditer(folded):
        if _is_host(match) and free(match.start(), match.end()):
            spans.append(("web", match.start(), match.end()))
    phones = [(m.start(), m.end()) for m in _PHONE.finditer(folded)]
    phones += [(m.start("number"), m.end("number")) for m in _PHONE_AFTER_WORD.finditer(folded)]
    for start, end in sorted(phones):
        if MIN_PHONE_DIGITS <= _phone_digits(folded[start:end]) <= MAX_PHONE_DIGITS and free(start, end):
            spans.append(("phone", start, end))
    if origin is not None:
        spans = [(kind, origin[start], origin[end - 1] + 1) for kind, start, end in spans]
    return sorted((Contact(kind, start, end) for kind, start, end in spans), key=lambda contact: contact.start)


def has_contact(text: str) -> bool:
    """Whether `text` holds a web address, an e-mail address or a phone number."""
    return bool(find_contacts(text))


def contact_kinds(text: str) -> list[ContactKind]:
    """The kinds of contact detail in `text`, each once, in a fixed order (for content-free logs)."""
    kinds = {contact.kind for contact in find_contacts(text)}
    order: tuple[ContactKind, ...] = ("web", "email", "phone")
    return [kind for kind in order if kind in kinds]


def strip_contacts(text: str) -> str:
    """`text` without its contact details, each taken out with one space next to it."""
    contacts = find_contacts(text)
    if not contacts:
        return text
    pieces: list[str] = []
    position = 0
    for contact in contacts:
        start, end = contact.start, contact.end
        if start > position and text[start - 1] in " \t":
            start -= 1
        elif end < len(text) and text[end] in " \t":
            end += 1
        pieces.append(text[position:start])
        position = end
    pieces.append(text[position:])
    joined = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", "".join(pieces))
    return "\n".join(_SPACES.sub(" ", line).rstrip() for line in joined.split("\n"))
