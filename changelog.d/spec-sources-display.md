### Added

- **A "Sources" section on the spec page.** A spec that names a work shows
  it at the end of the Specification tab, under "inspired by" and
  "references": each title links to the work, a DOI links to its
  resolver, an ISBN is plain text. Every other spec page stays as it was.
  The same entries reach machines: `GET /specs/{spec_id}` and the MCP
  tool `get_spec_detail` carry `sources`, and the prerendered hub and
  implementation pages list them and name them in their JSON-LD
  (`isBasedOn` for the works that gave the idea, `citation` for the
  references) on the page node, never on the code.
