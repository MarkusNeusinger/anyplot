"""The `anyplot` agent: settings and the Pydantic contracts of the plot pipeline.

ADK's loader imports this package as the top-level module `anyplot` (`adk web agents`),
and the service imports it as `agents.anyplot`; both work only because every import
inside the package is relative. The agent itself (`agent.py` with `root_agent` and
`app`) arrives in a later PR, together with the `from . import agent` that ADK needs.
"""
