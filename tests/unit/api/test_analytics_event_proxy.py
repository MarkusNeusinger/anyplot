"""The Plausible beacon proxy in app/nginx.conf, held against the browsers whose events it must forward.

`location = /api/event`, in both server blocks, proxies the page's Plausible event to plausible.io. Before it
does, it answers 202 itself, without forwarding, when a user-agent map names the sender a crawler (`$is_bot`) or
automation (`$is_headless_client`: an empty user agent, a headless browser, an HTTP library). Such a client
still gets every page; only its event is dropped, and the 202 mirrors Plausible's own answer so it does not
retry. That makes a too-wide entry silent: real visitors vanish from the dashboard with no error anywhere.

So no map that feeds this decision may match a browser's user agent, whatever the browser's version. A crawler
farm that wears a browser's user agent shares it with real visitors, so it is challenged at the Cloudflare edge,
by hosting network and by outdated Chrome version (infra/cloudflare/README.md, "Security rules"), where a person
who gets caught sees the challenge and can pass it.
The browser list below carries the shapes such farms have worn, Windows 10 Chrome 103 to 138 and Windows and
macOS Chrome 148 to 150, so a browser-shaped entry cannot come back unnoticed.

The maps are read from the shipped file and evaluated the way nginx does, by the evaluator of
test_machine_reads_nginx.py. Whether nginx accepts the file is `ci-image.yml`'s job, which boots the real image.
"""

from __future__ import annotations

import re

import pytest

from tests.unit.api.test_machine_reads_nginx import CONF, evaluate


def _code(text: str) -> str:
    """Config text without its comment lines, so prose about an `if` or a brace is never read as config."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _event_locations() -> list[str]:
    """The body of every `location = /api/event { … }`, delimited by brace depth rather than by indentation."""
    code = _code(CONF)
    bodies = []
    for opening in re.finditer(r"location\s*=\s*/api/event\s*\{", code):
        depth = 1
        for index in range(opening.end(), len(code)):
            depth += {"{": 1, "}": -1}.get(code[index], 0)
            if depth == 0:
                bodies.append(code[opening.end() : index])
                break
    return bodies


EVENT_LOCATIONS = _event_locations()
CONDITIONAL = re.compile(r"\bif\s*\((?P<test>[^)]*)\)\s*\{(?P<body>[^}]*)\}")

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
    *(MAC_CHROME.format(version) for version in ["120.0.0.0", "148.0.0.0", "149.0.0.0", "150.0.0.0"]),
    WIN10_CHROME.format("150.0.0.0", "537.36 Edg/150.0.0.0"),
    WIN10_CHROME.format("120.0.0.0", "537.36 OPR/106.0.0.0"),
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/29.0 "
    "Chrome/136.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.0 "
    "Mobile/15E148 Safari/604.1",
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


# A person reading the page inside an app: the app's in-app browser is Safari or Chrome with the app's own name
# appended. An `$is_bot` entry that names the app, not its preview fetcher, answers that person with the
# prerendered page and drops their events, and nothing shows it.
IN_APP_BROWSERS = [
    # Snapchat on iOS, as reported from a live request, and the shape its Android WebView takes.
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/13.0.3 Mobile/15E148 Snapchat/10.72.0.2 (like Safari/604.1)",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/AP2A.240805.005; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36 Snapchat/12.92.0.46 (Pixel 8; Android 14; gzip)",
    # Facebook and Instagram.
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "[FBAN/FBIOS;FBAV/470.0.0.37.103;FBDV/iPhone14,5;FBMD/iPhone;FBSN/iOS;FBSV/17.5;FBLC/en_US]",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Version/4.0 Chrome/126.0.6478.134 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/470.0.0.37.103;]",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "Instagram 339.0.3.12.91 (iPhone14,5; iOS 17_5; en_US; en; scale=3.00; 1170x2532; 619461904)",
    # X, LinkedIn, Pinterest and Telegram.
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "Twitter for iPhone/10.50",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "[LinkedInApp]/9.29.8291",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
    "[Pinterest/iOS]",
    "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.134 Mobile "
    "Safari/537.36 Telegram-Android/11.0.0 (Samsung SM-S918B; Android 14; SDK 34; HIGH)",
]

# The fetchers the same apps send for a link's preview: these read no JavaScript and need the prerendered page.
PREVIEW_FETCHERS = [
    "Snap URL Preview Service; bot; snapchat; https://developers.snap.com/robots",
    "WhatsApp/2.23.18.78 i",
    # Signal signs as WhatsApp without a full version.
    "WhatsApp/2",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) SkypeUriPreview Preview/0.5 skype-url-preview@microsoft.com",
    "TelegramBot (like TwitterBot)",
    "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
    "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Twitterbot/1.0",
    "LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)",
    "Tumblr/14.0.835.186",
    "http.rb/5.1.1 (Mastodon/4.2.0; +https://mastodon.social/)",
    # Apple's Messages borrows two crawlers' names at once.
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 "
    "Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0",
]


def _dropping_maps(location: str) -> list[str]:
    """The map variables whose value 1 makes this location answer 202 instead of proxying."""
    code = _code(location)
    conditionals = list(CONDITIONAL.finditer(code))
    # A test with a parenthesis in it, `if ($http_user_agent ~ "(...)")`, escapes CONDITIONAL; counting the
    # keywords keeps such an `if`, or a bare `return`, from passing unread.
    assert len(re.findall(r"\bif\b", code)) == len(conditionals), "/api/event has an `if` this test cannot read"
    assert len(re.findall(r"\b(?:return|deny)\b", code)) == len(conditionals), (
        "/api/event answers a request itself outside a map's conditional"
    )
    variables = []
    for conditional in conditionals:
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


@pytest.mark.parametrize("user_agent", IN_APP_BROWSERS)
def test_a_person_in_an_in_app_browser_is_no_crawler(user_agent):
    """`$is_bot` decides two things at once: the prerendered page instead of the app, and a dropped event."""
    assert evaluate("is_bot", user_agent) == "0", (
        f"{user_agent!r} is an app's in-app browser, a person, and `$is_bot` matches it: they get the prerendered "
        "page and vanish from Plausible. Name the app's preview fetcher in the map, not the app."
    )
    assert not _drops(user_agent)


@pytest.mark.parametrize("user_agent", PREVIEW_FETCHERS)
def test_a_preview_fetcher_gets_the_prerendered_page(user_agent):
    assert evaluate("is_bot", user_agent) == "1", (
        f"{user_agent!r} fetches a link's preview and reads no JavaScript: without `$is_bot` it gets the empty "
        "shell, and every shared link shows the home page's title."
    )


def test_no_entry_names_an_app_whose_fetcher_signs_otherwise():
    """Snap's fetcher signs as "Snap URL Preview Service" and Signal's as WhatsApp: the apps' names match people."""
    assert evaluate("is_bot", "Snapchat/12.92.0.46") == "0"
    assert evaluate("is_bot", "Signal-Desktop/7.20.0") == "0"


@pytest.mark.parametrize("user_agent", AUTOMATION)
def test_automation_is_not_counted(user_agent):
    assert _drops(user_agent), f"{user_agent!r} is automation and its event now reaches Plausible"
