"""The Plausible beacon proxy in app/nginx.conf, held against the browsers whose events it must forward.

`location = /api/event`, in both server blocks, proxies the page's Plausible event to plausible.io. Before it
does, it answers 202 itself, without forwarding, when a user-agent map names the sender a crawler (`$is_bot`) or
automation (`$is_headless_client`: an empty user agent, a headless browser, an HTTP library). Such a client
still gets every page; only its event is dropped, and the 202 mirrors Plausible's own answer so it does not
retry. That makes a too-wide entry silent: real visitors vanish from the dashboard with no error anywhere.

So no map that feeds this decision may match a browser's user agent, whatever the browser's version. A crawler
farm that wears a browser's user agent shares it with real visitors, so it is answered at the Cloudflare edge
(infra/cloudflare/README.md, "Security rules"), where a person who gets caught sees a challenge and can pass it.
The browser list below carries the shapes such farms have worn, Windows 10 Chrome 103 to 138 and Windows and
macOS Chrome 148 to 150, so a browser-shaped entry cannot come back unnoticed.

The maps are read from the shipped file and evaluated the way nginx does, by the evaluator of
test_machine_reads_nginx.py. Whether nginx accepts the file is `ci-image.yml`'s job, which boots the real image.
"""

from __future__ import annotations

import re

import pytest

from tests.unit.api.test_machine_reads_nginx import CONF, evaluate


EVENT_LOCATIONS = re.findall(r"location = /api/event \{(.*?)\n    \}", CONF, re.DOTALL)
CONDITIONAL = re.compile(r"\bif \((?P<test>[^)]*)\)\s*\{(?P<body>[^}]*)\}")

WIN10_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{} Safari/{}"
MAC_CHROME = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{} Safari/537.36"
)

BROWSERS = [
    # Windows 10 and 11 Chrome across the versions a farm has worn and the ones people pin.
    *(WIN10_CHROME.format(version, "537.36") for version in ["99.0.0.0", "100.0.0.0", "103.0.0.0", "109.0.0.0"]),
    *(WIN10_CHROME.format(version, "537.36") for version in ["120.0.0.0", "138.0.0.0", "139.0.0.0", "140.0.0.0"]),
    *(WIN10_CHROME.format(version, "537.36") for version in ["148.0.0.0", "150.0.0.0", "156.0.0.0"]),
    WIN10_CHROME.format("104.0.5112.81", "537.36"),
    WIN10_CHROME.format("105.0.0.0", "537.3"),
    *(MAC_CHROME.format(version) for version in ["148.0.0.0", "149.0.0.0", "150.0.0.0"]),
    WIN10_CHROME.format("150.0.0.0", "537.36 Edg/150.0.0.0"),
    WIN10_CHROME.format("120.0.0.0", "537.36 OPR/106.0.0.0"),
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 "
    "Mobile/15E148 Safari/604.1",
]

AUTOMATION = [
    "",
    "python-requests/2.32.3",
    "curl/8.11.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/150.0.0.0 Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]


def _dropping_maps(location: str) -> list[str]:
    """The map variables whose value 1 makes this location answer 202 instead of proxying."""
    variables = []
    for conditional in CONDITIONAL.finditer(location):
        test, body = conditional.group("test").strip(), conditional.group("body").strip()
        assert re.fullmatch(r"\$\w+", test), f"/api/event tests something other than one map variable: if ({test})"
        assert body == "return 202;", f"/api/event does something other than a 202 when {test} is set: {body!r}"
        variables.append(test[1:])
    return variables


def _drops(user_agent: str) -> list[str]:
    """The maps that drop this user agent's event, read from the first /api/event location."""
    return [variable for variable in _dropping_maps(EVENT_LOCATIONS[0]) if evaluate(variable, user_agent) == "1"]


def test_both_event_locations_proxy_to_plausible_alike():
    """Both server blocks proxy /api/event; a decision in only one of them is how the copy nobody looks at rots."""
    assert len(EVENT_LOCATIONS) == 2, f"expected /api/event in both server blocks, found {len(EVENT_LOCATIONS)}"
    for location in EVENT_LOCATIONS:
        assert "proxy_pass https://plausible.io/api/event;" in location
    assert _dropping_maps(EVENT_LOCATIONS[0]) == _dropping_maps(EVENT_LOCATIONS[1])


def test_every_dropping_map_reads_only_the_user_agent():
    """An IP, network or country decision belongs at the edge, where a caught person sees a challenge."""
    for variable in _dropping_maps(EVENT_LOCATIONS[0]):
        assert re.search(r"^map \$http_user_agent \$" + variable + r" \{", CONF, re.MULTILINE), variable


@pytest.mark.parametrize("user_agent", BROWSERS)
def test_a_browser_event_reaches_plausible(user_agent):
    assert not _drops(user_agent), (
        f"{user_agent!r} is a browser's user agent and {_drops(user_agent)} answers its event with a 202, so "
        "every real visitor who sends it vanishes from Plausible with no error anywhere. A farm wearing this "
        "user agent belongs at the Cloudflare edge, not in an nginx map."
    )


@pytest.mark.parametrize("user_agent", AUTOMATION)
def test_automation_is_not_counted(user_agent):
    assert _drops(user_agent), f"{user_agent!r} is automation and its event now reaches Plausible"
