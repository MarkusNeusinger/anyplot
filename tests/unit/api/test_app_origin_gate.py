"""The APP container's origin gate, held against the six files it is spread over.

`api/origin_gate.py` closes the API service's door and says, in as many words,
that the app service has a second one: its nginx relays a crawler user agent to
`https://api.anyplot.ai`, where the edge stamps the API's secret legitimately,
so a caller on the raw `*.run.app` URL reaches the prerendered render — and its
repository queries and its Plausible event — without having passed the edge
himself. This is that door, and `tests/unit/api/test_origin_gate.py` next door is
the other half of the same mechanism.

The reason it needs a test at all is that no single file contains it:

1. **`app/origin-gate.conf.template`** decides, and is the only place the secret
   is written. It is a TEMPLATE because nginx cannot read the environment; the
   base image's entrypoint renders it before nginx starts.
2. **`app/nginx.conf`** enforces, in every server block, and must never so much
   as name the header — a `log_format`, an `add_header` or a `return` that did
   would publish the secret the gate exists to keep.
3. **`app/Dockerfile`** is what makes the rendering happen, and carries the two
   defaults without which the container does not boot at all.
4. **`app/cloudbuild.yaml`** and **`.github/workflows/bot-serving-check.yml`**
   are the two legitimate callers that reach this origin WITHOUT the edge, by
   design, and would each be 403'd into silence.
5. **`infra/cloudflare/anyplot-api-proxy.js`** forwards exactly one path to this
   container, and a Worker subrequest skips its own zone's Transform Rules — so
   it has to stamp that path itself or arming the gate takes site analytics down.

None of the five can see the other four, and every one of them fails silently:
the site keeps serving, the deploy keeps going green, and what breaks is a
crawler path or an analytics call that nobody watches by eye.

What this file cannot see is whether the rendered config actually boots —
`ci-image.yml` runs the real image with the gate off, armed, and armed with no
secret, which is the half a text test can never do.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
NGINX_CONF = ROOT / "app" / "nginx.conf"
GATE_TEMPLATE = ROOT / "app" / "origin-gate.conf.template"
APP_DOCKERFILE = ROOT / "app" / "Dockerfile"
APP_CLOUDBUILD = ROOT / "app" / "cloudbuild.yaml"
BOT_CHECK = ROOT / ".github" / "workflows" / "bot-serving-check.yml"
WORKER = ROOT / "infra" / "cloudflare" / "anyplot-api-proxy.js"


def _without_comments(text: str) -> str:
    """Comment lines dropped — prose that MENTIONS a directive is not one."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def server_blocks() -> list[str]:
    """Every `server { … }` block of app/nginx.conf, as raw text."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    blocks = []
    for match in re.finditer(r"^server\s*\{", conf, re.MULTILINE):
        depth = 0
        for i in range(match.end() - 1, len(conf)):
            if conf[i] == "{":
                depth += 1
            elif conf[i] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(conf[match.start() : i + 1])
                    break
    return blocks


def test_every_server_block_is_gated():
    """A gate on one of two server blocks is a door with a window beside it."""
    ungated = [
        b.strip().splitlines()[1].strip() for b in server_blocks() if "$origin_gate_deny" not in _without_comments(b)
    ]
    assert not ungated, (
        f"these app/nginx.conf server blocks refuse nothing: {ungated}. Every block "
        "the container serves has to carry `if ($origin_gate_deny) { return 421; }`, "
        "including one whose hostname is not live yet — a gate that covers 'every "
        "server block' is a rule someone can keep."
    )


def test_the_refusal_has_somewhere_to_land_in_every_block():
    """`error_page` and the named location are per server block, not global."""
    for block in server_blocks():
        head = block.strip().splitlines()[1].strip()
        text = _without_comments(block)
        assert "error_page 421 = @origin_denied;" in text, (
            f"the server block at `{head}` refuses with 421 but never maps it — "
            "the caller would get nginx's stock 421 page instead of the refusal."
        )
        assert "location @origin_denied" in text, (
            f"the server block at `{head}` points `error_page 421` at a named "
            "location it does not define. Named locations do not cross server blocks."
        )


def test_the_gate_refuses_before_the_trailing_slash_rewrite():
    """Rewrite-module directives run in source order.

    Behind the gate there is a `rewrite ^/(.*)/$ … permanent;` at server level.
    Below the gate it never runs, which is the point: a refused request must not
    first be handed a redirect to a URL it is equally not allowed to fetch.
    """
    for block in server_blocks():
        text = _without_comments(block)
        if "rewrite ^/(.*)/$" not in text:
            continue
        assert text.index("$origin_gate_deny") < text.index("rewrite ^/(.*)/$"), (
            "app/nginx.conf runs its trailing-slash rewrite before the origin gate, "
            "so a refused request is answered with a redirect first."
        )


def test_nginx_conf_never_names_the_secret_header():
    """The one rule that keeps the secret out of a log line and an error page.

    `$http_x_origin_secret` belongs to the map file and nowhere else. The moment
    it appears in a `log_format`, an `add_header` or a `return` body, the value
    the whole gate protects is written into a place someone reads.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    assert "$http_x_origin_secret" not in conf, (
        "app/nginx.conf names $http_x_origin_secret. Only "
        "app/origin-gate.conf.template may read the header; nginx.conf reads the "
        "verdict ($origin_gate_status) and the decision ($origin_gate_deny)."
    )


def test_every_gate_variable_nginx_conf_uses_is_defined_by_the_template():
    """Two files, one mechanism: an undefined variable is a container that will
    not start, and the container that will not start is the production one."""
    used = set(re.findall(r"\$origin_gate_\w+", NGINX_CONF.read_text(encoding="utf-8")))
    template = GATE_TEMPLATE.read_text(encoding="utf-8")
    defined = set(re.findall(r"^map\s+\S+\s+(\$origin_gate_\w+)\s*\{", template, re.MULTILINE))
    assert used <= defined, (
        f"app/nginx.conf reads {sorted(used - defined)}, which "
        "app/origin-gate.conf.template does not define — nginx refuses to start on "
        "an unknown variable, so this is a boot failure, not a wrong answer."
    )


def test_the_map_bucket_holds_a_real_secret():
    """The tag that makes the gate fail closed is also what overflows the hash.

    nginx cannot hash a `map` key longer than one bucket, and the default bucket
    is the processor's cache line — 64 bytes. The key is `presented:` plus the
    whole secret, so 32 random bytes written as hex is 74 characters and nginx
    refuses to start with "could not build map_hash". It starts perfectly with
    the gate off, because the key is short then; the failure appears at the
    moment of arming and nowhere earlier. Found by the container smoke, which is
    the only thing here that runs the rendered config.
    """
    template = _without_comments(GATE_TEMPLATE.read_text(encoding="utf-8"))
    match = re.search(r"map_hash_bucket_size\s+(\d+);", template)
    assert match, (
        "app/origin-gate.conf.template does not raise map_hash_bucket_size. The "
        "tagged secret key is longer than nginx's default 64-byte bucket, so the "
        "container starts with the gate off and refuses to start the moment it is "
        "armed."
    )
    # `presented:` + a 64-character hex secret is 74; the headroom is for a
    # longer or base64 value, and the directive wants a multiple of the cache
    # line either way.
    assert int(match.group(1)) >= 128, (
        f"map_hash_bucket_size is {match.group(1)}, which leaves no room for a "
        "secret longer than a few dozen characters."
    )


def test_the_secret_is_written_exactly_once_and_is_tagged():
    """An untagged key would open the gate the day the variable is forgotten.

    `map` compares literally. With a bare `"${ORIGIN_SECRET}"` key, an unset
    variable renders as `""` — which is exactly what an absent header looks
    like, so every request in the world would match and the gate would read as
    armed while admitting everyone. The tag makes the empty-secret key
    unreachable, because a present-but-empty header is reported as `absent`.
    """
    # Comments dropped first: this file explains the trap at length, and prose
    # about `${ORIGIN_SECRET}` must not count as another copy of it.
    template = _without_comments(GATE_TEMPLATE.read_text(encoding="utf-8"))
    occurrences = re.findall(r'"([^"]*)\$\{ORIGIN_SECRET\}([^"]*)"', template)
    assert len(occurrences) == 1, (
        f"${{ORIGIN_SECRET}} appears in {len(occurrences)} map keys of "
        "app/origin-gate.conf.template; it belongs in exactly one, and every extra "
        "one is another copy of the secret in the rendered config."
    )
    prefix, suffix = occurrences[0]
    assert prefix and not suffix, (
        f'the secret\'s map key is "{prefix}${{ORIGIN_SECRET}}{suffix}" — it needs a '
        "non-empty PREFIX and nothing after it, or an unset secret becomes a key "
        "that every request matches."
    )
    assert template.count("${ORIGIN_SECRET}") == 1, (
        "the secret is substituted more than once in app/origin-gate.conf.template."
    )


def test_the_exemption_is_one_exact_path():
    """Exact paths only, no prefixes — a prefix exemption is how a gate grows a
    hole, which is the rule `api/origin_gate.py` states for its own list."""
    template = _without_comments(GATE_TEMPLATE.read_text(encoding="utf-8"))
    block = re.search(r"map \$uri \$origin_gate_exempt \{(.*?)\}", template, re.DOTALL)
    assert block, "app/origin-gate.conf.template defines no exemption map"
    exempt = re.findall(r'"([^"]+)"\s+1;', block.group(1))
    assert exempt == ["/_health"], (
        f"the origin gate exempts {exempt}. `/_health` is the measuring instrument "
        "and the one path a probe must reach on the raw URL whatever the gate is "
        "doing; anything else added here is a hole with a reason attached."
    )


def test_the_health_endpoint_reports_the_verdict_in_every_block():
    """`off-seen` is what makes arming a measurement rather than a leap, and a
    verdict is only useful on the host it is asked about."""
    for block in server_blocks():
        head = block.strip().splitlines()[1].strip()
        health = re.search(r"location /_health \{(.*?)\n    \}", block, re.DOTALL)
        assert health, f"the server block at `{head}` has no /_health location"
        body = _without_comments(health.group(1))
        assert "add_header X-Origin-Gate $origin_gate_status always;" in body, (
            f"the /_health of `{head}` does not report the gate verdict, so that "
            "route cannot be measured before the gate is armed."
        )
        assert "include /etc/nginx/security-headers.conf;" in body, (
            f"the /_health of `{head}` sets a header of its own and so drops every "
            "inherited one; it has to re-include the snippet."
        )


def test_the_worker_stamps_the_one_path_it_sends_to_this_container():
    """`/api/event` is the ONLY path under anyplot.ai/api/* that reaches the app.

    A Worker subrequest to a host in the same zone skips that zone's Transform
    Rules — the finding `infra/cloudflare/README.md` exists for — so on this
    path the header can only come from the Worker's own binding. Without it,
    arming the app gate takes every Plausible pageview on the site down, and
    analytics failing is not something a page tells its visitor about.
    """
    worker = WORKER.read_text(encoding="utf-8")
    branch = re.search(r"if \(url\.pathname === '/api/event'\) \{(.*?)\n    \}", worker, re.DOTALL)
    assert branch, "the Worker no longer has a distinct /api/event branch"
    body = branch.group(1)
    assert "env.ORIGIN_SECRET" in body and "set('X-Origin-Secret'" in body, (
        "the Worker's /api/event branch forwards without stamping X-Origin-Secret. "
        "That path goes to the APP origin, and its gate will refuse it."
    )
    assert "delete('X-Origin-Secret')" in body, (
        "the Worker's /api/event branch forwards the caller's own X-Origin-Secret. "
        "It must be deleted before the binding is applied, or a caller can make an "
        "unarmed probe report a false `off-seen` and corrupt the rollout's one "
        "measurement."
    )


def test_the_deploy_smoke_carries_the_header():
    """The pre-traffic smoke probes the candidate on its `run.app` tag URL, which
    by definition never passes the edge — so every probe but the exempt one has
    to stamp the header itself, or arming the gate reds every deploy."""
    build = APP_CLOUDBUILD.read_text(encoding="utf-8")
    assert "--secret=ORIGIN_SECRET" in build, (
        "app/cloudbuild.yaml never reads ORIGIN_SECRET, so its smoke probes the "
        "candidate bare and would be 403'd the moment the gate is armed."
    )
    bare = [line for line in build.splitlines() if re.search(r'curl -fsS \$\$RETRY (?!"\$\$\{HDR\[@\]\}")', line)]
    assert not bare, f"these smoke probes do not send the origin header: {bare}"


def test_the_bot_monitor_carries_the_header_and_fails_loudly_without_it():
    """The daily monitor probes this origin BECAUSE Cloudflare 403s runner IPs.

    That is also why the gate could not be a Host rule. A missing repository
    secret has to be an error that names itself — otherwise an armed gate turns
    all ~36 checks into 403s and opens an incident saying every crawler page is
    broken, which is the wrong thing to go looking for at 06:23 UTC.
    """
    workflow = BOT_CHECK.read_text(encoding="utf-8")
    assert "ORIGIN_SECRET: ${{ secrets.ORIGIN_SECRET }}" in workflow, (
        ".github/workflows/bot-serving-check.yml does not take the ORIGIN_SECRET "
        "repository secret, so every probe it makes is refused once the gate is armed."
    )
    assert 'HDR=(-H "X-Origin-Secret: ${ORIGIN_SECRET}")' in workflow, (
        "the monitor reads the secret but never sends it."
    )
    for verdict in ("missing", "mismatch"):
        assert re.search(rf"\n\s+{verdict}\)\n.*?::error::.*?\n\s+exit 1", workflow, re.DOTALL), (
            f"the monitor does not fail on an origin-gate verdict of `{verdict}` — "
            "a missing or half-rotated secret would be reported as a broken site."
        )
    bare = [
        line
        for line in workflow.splitlines()
        if re.search(r'curl -sS[^|]*"\$ORIGIN', line) and '"${HDR[@]}"' not in line
    ]
    assert not bare, f"these monitor probes do not send the origin header: {bare}"


def test_the_image_renders_the_template_and_defaults_both_variables():
    """Three Dockerfile lines the gate cannot work without, each failing
    differently and none of them visibly.

    Without the COPY the maps never exist and nginx will not start. Without the
    two ENV defaults envsubst leaves `${ORIGIN_SECRET}` standing as a literal —
    nginx reads it as a reference to a variable it does not know, and again does
    not start. Without the filter, envsubst rewrites every `$name` in the
    template that happens to exist in the environment, and `$host` and `$uri`
    there are nginx's variables, not the shell's.
    """
    dockerfile = APP_DOCKERFILE.read_text(encoding="utf-8")
    assert "/etc/nginx/templates/" in dockerfile and "origin-gate.conf.template" in dockerfile, (
        "app/Dockerfile does not put origin-gate.conf.template where the base "
        "image's entrypoint looks for it (/etc/nginx/templates)."
    )
    for setting in ("ORIGIN_GATE=off", 'ORIGIN_SECRET=""', "NGINX_ENVSUBST_FILTER="):
        assert setting in dockerfile, (
            f"app/Dockerfile does not declare `{setting}`. All three are what make "
            "an unset variable on the Cloud Run service mean 'gate off' instead of "
            "'container will not boot'."
        )
