"""The `anyplot` agent: the root agent, its tools, the pipeline, the plugins and the `App`.

ADK's loader imports this package as the top-level module `anyplot` (`adk web agents`),
and the service imports it as `agents.anyplot`; both work only because every import
inside the package is relative. `adk web` looks for `app` (else `root_agent`) in this
package or in `anyplot.agent`; importing `agent` here makes the package itself carry
both, so either lookup finds the same objects.
"""

from . import agent
from .agent import app, root_agent


__all__ = ["agent", "app", "root_agent"]
