"""The relay page of the agent chat's interactive preview (`api/preview_relay.py`, `api/routers/preview.py`, JS-4b-2).

The relay's behaviour in a browser (the plot drawn two sandboxes below it, the refused ways
out, the ignored senders, `frame-ancestors`) is the probe's
(`agents/renderer/page_probe.mjs relay`, the renderer image's CI step and
`tests/unit/agents/code/test_profile_javascript_page_image.py`); these tests hold the page
and the headers the API serves to what that probe measured.
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.preview_relay import (
    LOCAL_ORIGINS,
    MAX_PAGE_CHARS,
    PAGE_POLICY,
    READY_MESSAGE,
    RELAY_PATH,
    relay_headers,
    relay_html,
    relay_origins,
    relay_policy,
)
from api.routers.agent import LOCAL_ORIGIN_REGEX
from core.config import settings


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestRoute:
    def test_the_relay_is_served_with_its_headers_to_anyone(self, client: TestClient) -> None:
        """No token, no cookie, no `/debug`: Cloudflare Access guards `/debug/*` alone, and the relay holds no data."""
        response = client.get(RELAY_PATH)

        assert response.status_code == 200
        assert not RELAY_PATH.startswith("/debug")
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        for key, value in relay_headers(settings.cors_origins).items():
            assert response.headers[key] == value, key
        assert response.text == relay_html(settings.cors_origins)
        assert "set-cookie" not in response.headers

    def test_the_policy_is_an_opaque_origin_the_harness_policy_and_the_sites_ancestors(
        self, client: TestClient
    ) -> None:
        policy = client.get(RELAY_PATH).headers["content-security-policy"]
        directives = [part.strip() for part in policy.split(";")]

        assert directives[0] == "sandbox allow-scripts"
        assert "; ".join(directives[1:-1]) == PAGE_POLICY
        ancestors = directives[-1].split()
        assert ancestors[0] == "frame-ancestors"
        assert set(ancestors[1:]) == {*settings.cors_origins, LOCAL_ORIGINS}
        assert "*" not in ancestors and "'self'" not in ancestors
        assert client.get(RELAY_PATH).headers["referrer-policy"] == "no-referrer"
        assert client.get(RELAY_PATH).headers["x-content-type-options"] == "nosniff"

    def test_the_local_origins_are_the_bffs(self) -> None:
        """The relay admits the same local dev servers as the BFF's Origin check (`http://localhost:\\d+`)."""
        assert LOCAL_ORIGIN_REGEX == r"http://localhost:\d+"
        assert LOCAL_ORIGINS == "http://localhost:*"
        assert f"/^{LOCAL_ORIGIN_REGEX.replace('/', chr(92) + '/')}$/" in relay_html([])

    def test_the_sites_policy_already_frames_the_api(self) -> None:
        """The preview needs no wider site policy: the site's `frame-src` names the API's origin since `/proxy/html`."""
        conf = (ROOT / "app" / "security-headers.conf").read_text(encoding="utf-8")
        frame_src = re.search(r"frame-src ([^;]+);", conf)
        assert frame_src is not None and frame_src.group(1).split() == ["'self'", "https://api.anyplot.ai"]


class TestPage:
    def test_the_relay_takes_one_string_from_its_parent_at_an_allowed_origin(self) -> None:
        html = relay_html(["https://anyplot.ai"])
        script = html[html.index("<script>") : html.index("</script>")]

        assert "if (shown || event.source !== window.parent) return;" in script
        assert "ORIGINS.indexOf(event.origin) === -1 && !LOCAL.test(event.origin)" in script
        assert 'typeof page !== "string" || page.length === 0 || page.length > MAX_PAGE_CHARS' in script
        assert f"var MAX_PAGE_CHARS = {MAX_PAGE_CHARS};" in script
        assert 'var ORIGINS = ["https://anyplot.ai"];' in script

    def test_the_page_goes_into_a_frame_sandboxed_to_scripts_through_the_srcdoc_property(self) -> None:
        script = relay_html([])
        assert 'frame.setAttribute("sandbox", "allow-scripts");' in script
        assert "frame.srcdoc = page;" in script
        # Never as built markup.
        for forbidden in ("innerHTML", "outerHTML", "document.write", "insertAdjacentHTML", "allow-same"):
            assert forbidden not in script, forbidden

    def test_the_relays_only_message_is_the_ready_signal_to_its_parent_after_its_listener(self) -> None:
        """A constant without content, sent once the listener is in place; the chat posts the page only on it."""
        html = relay_html(["https://anyplot.ai"])
        script = html[html.index("<script>") : html.index("</script>")]
        signal = f'window.parent.postMessage("{READY_MESSAGE}", "*");'

        assert script.count("postMessage") == 1
        assert signal in script
        assert script.index('window.addEventListener("message"') < script.index(signal)

    def test_the_chat_and_the_probe_wait_for_the_same_signal(self) -> None:
        agent_ts = (ROOT / "app" / "src" / "lib" / "agent.ts").read_text(encoding="utf-8")
        probe = (ROOT / "agents" / "renderer" / "page_probe.mjs").read_text(encoding="utf-8")

        assert f"export const PREVIEW_RELAY_READY = '{READY_MESSAGE}';" in agent_ts
        assert f'const RELAY_READY = "{READY_MESSAGE}";' in probe

    def test_the_relay_loads_nothing(self) -> None:
        html = relay_html(["https://anyplot.ai"])
        assert not re.search(r"\b(src|href)=", html)
        assert html.count("<script>") == 1

    def test_an_origin_that_could_end_a_directive_is_left_out(self) -> None:
        origins = ["https://anyplot.ai", "https://evil.example; script-src *", "https://x.example/path", "*", ""]
        assert relay_origins(origins) == ["https://anyplot.ai"]
        assert relay_policy(origins).endswith(f"frame-ancestors https://anyplot.ai {LOCAL_ORIGINS}")
        assert "</script>" not in json.dumps(relay_origins(["https://a.example"]))

    def test_the_policy_is_the_harness_policy(self) -> None:
        """One owner: the harness's `CONTENT_SECURITY_POLICY`, which the agents' wrapper pins against `render.mjs`; the
        wrapper is loaded by its path (standard library only), since the agents package's `__init__` imports ADK."""
        spec = importlib.util.spec_from_file_location("wrapper", ROOT / "agents" / "anyplot" / "render" / "page.py")
        assert spec is not None and spec.loader is not None
        wrapper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wrapper)

        assert PAGE_POLICY == wrapper.PAGE_POLICY

    def test_the_command_line_writes_the_page_the_headers_and_the_signal(self) -> None:
        """The probe's input (`python3 api/preview_relay.py <origin> ...`), from the standard library alone."""
        done = subprocess.run(
            [sys.executable, "-I", str(ROOT / "api" / "preview_relay.py"), "https://anyplot.ai"],
            capture_output=True,
            text=True,
            check=True,
        )
        written = json.loads(done.stdout)
        assert written == {
            "html": relay_html(["https://anyplot.ai"]),
            "headers": relay_headers(["https://anyplot.ai"]),
            "ready": READY_MESSAGE,
        }
