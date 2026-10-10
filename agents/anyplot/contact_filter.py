"""Contact details in text: web addresses, e-mail addresses and phone numbers, found without a network or a model.

Text that a user or a model writes can reach other people: the root's reply, the
change request the root writes for the adapter, and the string literals the adapter
puts into the plot (and so into the watermarked PNG and `plot.py`). A scam graphic
needs a way to reach its author, so these three places refuse or strip contact
details (the guardrail audit of 2026-10-10, findings 2 and 4):

* `agents/stream.py` strips them from every root message and plot-event line;
* ToolSafety refuses a `change_request` that carries one;
* the pipeline rejects a plan whose new string literals carry one.

What counts, case-insensitively:

* **Web address**: one or more dot-separated labels ending in a top-level domain from
  `TLDS` (every two-letter country code plus a curated list of generic ones), with an
  optional port and path: `securebank.com/login`, `parcel-help.com/pay`, `t.me/x`.
  Two exceptions keep code and prose from tripping it. A chain that starts with a
  code name (`CODE_NAMES`: `df.at`, `plt.cm`, `np.ma`, `pd.NA`, `ax.spines.top`) is
  code, not a host. A country code that is also an English word or a file extension
  (`PATH_ONLY_TLDS`: `plot.py`, `README.md`, `the plot.It`) counts only with a path
  after it. URLs with a scheme or `www.` are caught by the sanitisers' own patterns
  and by this one alike.
* **E-mail address**: `local@host.tld` with any alphabetic top-level domain.
* **Phone number**: an international number (`+49 30 1234567`, `+1 (555) 010-0100`),
  a domestic one with a leading zero (`030 1234567`, `0800-123-4567`, `(030) 123456`)
  or a North American one (`555-010-0100`, `(555) 010-0100`, `1-800-555-0100`), with
  7 to 15 digits in all. Dates, decimals, years and tick values do not match.

The lists live in code on purpose: no lookup, no download, the same answer offline.
"""

import re
from dataclasses import dataclass
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
    berlin hamburg bayern nrw koeln wien swiss london nyc paris
    """.split()
)
"""Generic top-level domains: the classic ones, the ones spam and phishing use most, and a few city ones.
Generic domains that read as code (`.name`, `.int`, `.cat`, `.style`, `.show`, `.map`) are left out on purpose."""

TLDS: frozenset[str] = COUNTRY_TLDS | GENERIC_TLDS

PATH_ONLY_TLDS: frozenset[str] = frozenset(
    {"am", "as", "at", "be", "by", "cc", "do", "id", "in", "is", "it", "me", "mk", "md", "my", "no", "pl", "ps"}
    | {"py", "rs", "sh", "so", "to", "us"}
)
"""Country codes that are also English words or file extensions; they count as a host only with a path."""

CODE_NAMES: frozenset[str] = frozenset(
    """
    ax axs axes df fig plt np pd sns mpl matplotlib seaborn numpy pandas scipy stats spines self os math
    xaxis yaxis ticker dates colors cm patches lines style rc rcparams series frame figure
    """.split()
)
"""First labels that make a dotted chain code rather than a host name (`df.at`, `plt.cm`, `ax.spines.top`)."""

HOST_TLDS: frozenset[str] = frozenset({"com", "net", "org", "info", "biz", "edu", "gov"})
"""Top-level domains no attribute is named after: behind one, even a code name is a host (`matplotlib.org`)."""

MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 15  # E.164

_HOST = re.compile(
    r"(?<![\w@.-])"
    r"(?P<labels>(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+)"
    r"(?P<tld>[a-z]{2,24})(?![\w-])"
    r"(?P<port>:\d{2,5})?"
    r"(?P<path>/(?:[^\s<>\"']*[^\s<>\"'.,;:!?)\]])?)?",
    re.IGNORECASE,
)
_EMAIL = re.compile(
    r"(?<![\w.%+-])[a-z0-9._%+-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,24}\b",
    re.IGNORECASE,
)
_PHONE = re.compile(
    r"(?<![\w+(])(?:"
    r"\+\d{1,3}(?:[ .-]?\(\d{1,5}\))?(?:[ ./-]?\d{2,}){2,}"  # +49 30 1234567, +1 (555) 010-0100
    r"|\(0\d{1,4}\)[ ./-]?\d{3,}(?:[ .-]\d{2,})*"  # (030) 123456
    r"|\(\d{3}\)[ .-]?\d{3}[ .-]\d{4}"  # (555) 010-0100
    r"|0\d{2,5}[ /-]\d{3,}(?:[ .-]\d{2,})*"  # 030 1234567, 0800-123-4567, 089/123456
    r"|1[ .-]\d{3}[ .-]\d{3}[ .-]\d{4}"  # 1-800-555-0100
    r"|\d{3}[.-]\d{3}[.-]\d{4}"  # 555-010-0100
    r")(?![\w])"
)
_SPACES = re.compile(r"(?<=\S)[ \t]{2,}")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+([,.;:!?])")


@dataclass(frozen=True, slots=True)
class Contact:
    """One contact detail found in a text: its kind and its span."""

    kind: ContactKind
    start: int
    end: int


def _is_host(match: re.Match[str]) -> bool:
    labels = match.group("labels").rstrip(".").split(".")
    tld = match.group("tld").lower()
    if tld not in TLDS or (labels[0].lower() in CODE_NAMES and tld not in HOST_TLDS):
        return False
    if not any(re.search(r"[a-z]", label, re.IGNORECASE) for label in labels):
        return False  # 1.2.de, a number with a country code glued to it
    path = match.group("path") or ""
    if tld in PATH_ONLY_TLDS and labels[0].lower() != "www":
        return len(path) > 1
    return True


def _phone_digits(text: str) -> int:
    return sum(character.isdigit() for character in text)


def find_contacts(text: str) -> list[Contact]:
    """Every contact detail in `text`, in order and without overlaps (e-mail first, then web, then phone)."""
    found: list[Contact] = [Contact("email", match.start(), match.end()) for match in _EMAIL.finditer(text)]

    def free(start: int, end: int) -> bool:
        return all(end <= contact.start or start >= contact.end for contact in found)

    for match in _HOST.finditer(text):
        if _is_host(match) and free(match.start(), match.end()):
            found.append(Contact("web", match.start(), match.end()))
    for match in _PHONE.finditer(text):
        digits = _phone_digits(match.group(0))
        if MIN_PHONE_DIGITS <= digits <= MAX_PHONE_DIGITS and free(match.start(), match.end()):
            found.append(Contact("phone", match.start(), match.end()))
    return sorted(found, key=lambda contact: contact.start)


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
