"""The vendor table of the machine reads: which crawler or AI assistant a user agent is.

`AI_AGENTS` is the table both machine-read writers use (`api/machine_reads.py`,
and the `$machine_agent` map of `app/nginx.conf`). The share counter reads it
too: a crawler's or an assistant's fetch of a preview image is a machine read,
never a shared link (`api/shared_links.py`).

Until 2026-11-11 this module also sent an `og_image_view` event to Plausible
for every preview image, with the fetcher's address and user agent. Shares are
counted in the database since, without either.
"""

# Which assistant, and on whose behalf. The distinction is the point: a
# user-directed fetch means a person asked their assistant to open this page,
# which is a reader; an index crawler is building a corpus with no one waiting.
# Ordered most-specific first — matching is substring-based, and e.g.
# "claude-user" must never be shadowed by a broader "claude" pattern.
# Vendor taxonomy per each vendor's own crawler documentation. The nginx
# `$machine_agent` map repeats every token in this order
# (tests/unit/api/test_machine_reads_nginx.py), so a vendor added here needs
# its line there too.
AI_AGENTS: tuple[tuple[str, str, str], ...] = (
    # (user-agent substring, assistant, kind)
    ("claude-user", "claude", "user_directed"),
    ("claude-searchbot", "claude", "index"),
    ("claudebot", "claude", "training"),
    ("chatgpt-user", "chatgpt", "user_directed"),
    ("oai-searchbot", "chatgpt", "index"),
    ("gptbot", "chatgpt", "training"),
    ("perplexity-user", "perplexity", "user_directed"),
    ("perplexitybot", "perplexity", "index"),
    ("gemini-deep-research", "gemini", "user_directed"),
    ("gemininotebook", "gemini", "user_directed"),
    ("notebooklm", "gemini", "user_directed"),
    ("google-agent", "gemini", "user_directed"),
    ("googleagent", "gemini", "user_directed"),
    # Builds Vertex AI agents' grounding on the site owner's request. Before
    # the google entries; it contains neither "googlebot" nor "googleother".
    ("google-cloudvertexbot", "gemini", "index"),
    ("mistralai-user", "mistral", "user_directed"),
    ("mistralai-index", "mistral", "index"),
    ("meta-externalfetcher", "meta", "user_directed"),
    ("meta-webindexer", "meta", "index"),
    ("meta-externalagent", "meta", "training"),
    ("duckassistbot", "duckduckgo", "user_directed"),
    ("amzn-user", "amazon", "user_directed"),
    ("amzn-searchbot", "amazon", "index"),
    ("amazonbot", "amazon", "index"),
    ("grok-deepsearch", "grok", "user_directed"),
    ("grokbot", "grok", "user_directed"),
    ("xai-grok", "grok", "user_directed"),
    # xAI's search index. Before the bare "xai" below, which would otherwise
    # record it as a user-directed fetch (a live sample did exactly that).
    ("xai-searchbot", "grok", "index"),
    # The bare tokens the nginx map already serves (`~*grok`, `~*xai`): xAI's
    # fetcher was seen sending plain "Grok" and "xAI-Bot" without the grok
    # substring. Both were prerendered but never counted, because nothing above
    # matched them.
    # Last among the xAI patterns so the specific ones keep winning.
    ("grok", "grok", "user_directed"),
    ("xai", "grok", "user_directed"),
    ("youbot", "you", "index"),
    ("cohere-ai", "cohere", "user_directed"),
    # AI search indexes and training corpora that nginx does not prerender
    # (its `$is_bot` map leaves them on the SPA shell), so most of their reads
    # are nginx's lines. Bytespider is a welcome training crawler since the
    # robots.txt policy opened to every crawler. Keenable documents
    # Keenable-User (a person's agent asked) and Keenable-SearchBot; the bare
    # token also catches the "KeenableBot" UA seen in the request log.
    ("exasearchbot", "exa", "index"),
    ("keenable-user", "keenable", "user_directed"),
    ("keenable", "keenable", "index"),
    # Parallel documents Shap-User (a person's agent asked for one page) and
    # ShapBot, which indexes pages for its web APIs. ShapBot runs a browser
    # (Lightpanda), so the shell serves it the page: each of its page reads is
    # followed by the app's own API reads under the same user agent.
    ("shap-user", "parallel", "user_directed"),
    ("shapbot", "parallel", "index"),
    ("bytespider", "bytedance", "training"),
    ("ccbot", "commoncrawl", "training"),
    # SEO tools: crawlers that index the web for search-marketing products.
    # HaloBot is Haloscan's.
    ("semrushbot", "semrush", "seo"),
    ("ahrefsbot", "ahrefs", "seo"),
    ("dataforseobot", "dataforseo", "seo"),
    ("mj12bot", "majestic", "seo"),
    ("dotbot", "moz", "seo"),
    ("halobot", "haloscan", "seo"),
    # Classic search crawlers. Worth recording for the same reason the AI ones
    # are: crawl frequency per engine is otherwise only visible by sampling
    # Search Console's URL inspection one URL at a time, which is how the
    # months-long recrawl gap after the June 2026 outage stayed invisible.
    # Sogou by its spider's full token: its mobile browser, which people use,
    # also carries "sogou".
    ("qwantbot", "qwant", "search"),
    ("petalbot", "huawei", "search"),
    ("sogou web spider", "sogou", "search"),
    ("google-inspectiontool", "google", "inspection"),
    ("googleother", "google", "search"),
    ("googlebot", "google", "search"),
    ("bingbot", "bing", "search"),
    ("duckduckbot", "duckduckgo", "search"),
    ("yandexbot", "yandex", "search"),
    ("baiduspider", "baidu", "search"),
    # Last among the Apple patterns: "applebot" is a substring of
    # "applebot-extended", which is a robots.txt token rather than a real UA —
    # but ordering it here keeps the match correct if that ever changes.
    ("applebot", "apple", "search"),
)


def detect_ai_agent(user_agent: str) -> tuple[str, str] | None:
    """Return (assistant, kind) for a known AI or search agent, else None.

    Matching is substring-based on the lowercased UA, first match wins, so
    AI_AGENTS is ordered most-specific first.
    """
    ua = user_agent.lower()
    for pattern, assistant, kind in AI_AGENTS:
        if pattern in ua:
            return assistant, kind
    return None
