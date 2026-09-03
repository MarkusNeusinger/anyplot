"""Developer tooling — not shipped with the API image or the SPA bundle.

`[tool.setuptools.packages.find]` in pyproject.toml lists `api*`, `core*` and
`automation*`, so nothing here reaches the distribution, and the API image's
root `.dockerignore` is an allowlist that does not name this directory either.
That is the point: a release helper has no business in a container that serves
requests.
"""
