### Changed

- **The Dependabot command carries the check an ADK upgrade needs.** The release notes alone
  did not name what could break here: the 2.14.1 upgrade was checked by diffing the ADK files
  `VertexClaude` builds on, the rule that decides when a request carries `response_schema`, and
  the session invariant `agents/main.py` relies on, then running the real-flow service test with
  the new tree-sitter grammars. The steps now stand in the command's exact-pins rule. (#13197)
