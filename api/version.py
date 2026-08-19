"""Single source of the running app version.

The value is the installed distribution's version, i.e. pyproject.toml's
`version` field — the one the release flow bumps. Before this module existed,
/openapi.json said 1.0.0, /health said 0.2.0 and pyproject said 3.1.0, so no
client could tell which build it was talking to.
"""

from importlib.metadata import PackageNotFoundError, version


try:
    APP_VERSION = version("anyplot")
except PackageNotFoundError:  # running from a checkout without the dist installed
    APP_VERSION = "0.0.0+unknown"
