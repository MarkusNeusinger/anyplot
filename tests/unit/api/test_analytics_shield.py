"""The analytics shield in app/nginx.conf, held against the user agents it must tell apart.

`location = /api/event` answers 202 itself, without forwarding to Plausible, when
`$is_headless_client` says the sender is automation. The map blocks nobody: a
matched client still gets every page, it just stops being counted. That makes
a wrong entry silent in both directions. Too narrow, and a crawler farm shows up
as hundreds of dashboard visitors (one in November 2026 made up about half of a
week's visitors). Too wide, and real visitors vanish from the numbers with no
error anywhere.

The farm entry is the delicate one, because the farm wears plain Windows 10
Chrome UAs: one regex has to match its whole pool and no current browser. These
tests read the map out of the shipped file and evaluate it the way nginx does
(first matching entry wins, `~*` case-insensitive, a quoted key unescaped), with
Python's `re` standing in for PCRE: the entries use nothing whose meaning differs
between the two. Whether nginx accepts the file is `ci-image.yml`'s job, which
boots the real image.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


NGINX_CONF = Path(__file__).resolve().parents[3] / "app" / "nginx.conf"

WIN10_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{} Safari/{}"


def _map_entries(variable: str) -> list[tuple[str, str]]:
    """The `key value;` lines of `map $http_user_agent $<variable> { … }`, comments dropped."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    block = re.search(r"^map \$http_user_agent \$" + variable + r" \{\n(.*?)^\}", conf, re.MULTILINE | re.DOTALL)
    assert block, f"app/nginx.conf has no map for ${variable}"
    entries = []
    for line in block.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert line.endswith(";"), f"map line without a closing semicolon: {line!r}"
        key, value = line[:-1].rsplit(None, 1)
        if key.startswith('"'):
            assert key.endswith('"'), f"unbalanced quotes in map key: {key!r}"
            # nginx's tokenizer unescapes only \", \' and \\ inside a quoted string.
            key = re.sub(r"\\([\"'\\])", r"\1", key[1:-1])
        entries.append((key, value))
    return entries


def is_headless_client(user_agent: str) -> bool:
    """Evaluate `$is_headless_client` for one user agent the way nginx does."""
    default = "0"
    for key, value in _map_entries("is_headless_client"):
        if key == "default":
            default = value
        elif key.startswith("~*"):
            if re.search(key[2:], user_agent, re.IGNORECASE):
                return value == "1"
        elif key.startswith("~"):
            if re.search(key[1:], user_agent):
                return value == "1"
        elif key == user_agent:
            return value == "1"
    return default == "1"


@pytest.mark.parametrize(
    "user_agent",
    [
        WIN10_CHROME.format("109.0.0.0", "537.36"),
        WIN10_CHROME.format("103.0.0.0", "537.36"),
        WIN10_CHROME.format("138.0.0.0", "537.36"),
        # A full build number instead of the reduced 0.0.0 tail.
        WIN10_CHROME.format("104.0.5112.81", "537.36"),
        # The truncated variant some of the pool sends.
        WIN10_CHROME.format("105.0.0.0", "537.3"),
    ],
)
def test_the_crawler_farm_is_shielded(user_agent):
    assert is_headless_client(user_agent), (
        f"{user_agent!r} reaches Plausible. This is the crawler farm's shape (Windows 10, "
        "Chrome 103 to 138); every page load of it becomes up to three dashboard visitors."
    )


@pytest.mark.parametrize(
    "user_agent",
    [
        WIN10_CHROME.format("156.0.0.0", "537.36"),
        WIN10_CHROME.format("140.0.0.0", "537.36"),
        WIN10_CHROME.format("156.0.0.0", "537.36 Edg/156.0.0.0"),
        WIN10_CHROME.format("120.0.0.0", "537.36 Edg/120.0.0.0"),
        WIN10_CHROME.format("120.0.0.0", "537.36 OPR/106.0.0.0"),
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/156.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.1 Mobile/15E148 Safari/604.1",
    ],
)
def test_current_browsers_are_counted(user_agent):
    assert not is_headless_client(user_agent), (
        f"{user_agent!r} is a current browser and the shield now drops its events. Its "
        "visitors vanish from Plausible with no error anywhere."
    )


@pytest.mark.parametrize("user_agent", ["", "python-requests/2.32.3", "curl/8.11.0", "Mozilla/5.0 HeadlessChrome/138"])
def test_automation_stays_shielded(user_agent):
    assert is_headless_client(user_agent)


def test_every_event_location_consults_the_shield():
    """Both server blocks proxy /api/event; a shield in one of them is half a shield."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    locations = re.findall(r"location = /api/event \{(.*?)\n    \}", conf, re.DOTALL)
    assert len(locations) == 2, f"expected the /api/event location in both server blocks, found {len(locations)}"
    for body in locations:
        assert "if ($is_headless_client) { return 202; }" in body
