### Changed

- **MCP tools return what an assistant needs and nothing it does not.**
  `get_spec_detail` and `get_implementation` entries now carry `spec_id`,
  strip `# noqa` comments like the REST code endpoint, and leave out the
  review checklist, the review image description and the legacy single-theme
  preview fields: pipeline internals of about 10 KB per implementation that
  made an unfiltered `get_spec_detail` about 0.5 MB. `list_libraries` returns
  the REST `/libraries` fields (language, framework, version, documentation
  URL), so an assistant can pick a library by language without a second call.
  `get_tag_values` returns `{value, count}` pairs, most frequent first, counting
  specs for spec-level and implementations with code for impl-level
  categories. Breaking for clients that read the old shapes; the MCP server is
  not versioned and the old shapes were never what the reference described.
  (#12100)
- **Agent network design records the licensing decision.** The open question
  of where the agent code lives is settled in the decisions table: everything
  stays MIT in this repository, paid AI credits remain a later option, and the
  Highcharts licence must be settled before the first paid credit. (#12100)

### Fixed

- **MCP tag search scopes values to their category and ANDs the categories.**
  `search_specs_by_tags` flattened every spec-level value into one list and
  matched it in any category, so `plot_type=["scatter"]` with
  `domain=["finance"]` returned the union of both and `plot_type=["finance"]`
  matched finance domains. The new `SpecRepository.search_by_tag_filters`
  keeps each value in the category it was passed in (JSONB containment on
  PostgreSQL, `json_extract` on SQLite), ORs the values within a category and
  ANDs the categories, which is what the MCP reference promised all along.
  (#12100)
- **MCP reference and page describe what the tools return.**
  `docs/reference/mcp.md` and the MCP page carried wrapper objects, limits and
  library lists the server never produced: `list_specs` defaults to 100 and
  returns a bare array with `website_url`, `search_specs_by_tags` also takes
  `patterns`, `dataprep` and `styling`, `get_spec_detail` takes a `libraries`
  filter, and `get_implementation` covers all 15 libraries. (#12100)

### Removed

- **`SpecRepository.search_by_tags` and its any-category filter builder.**
  Nothing outside the MCP search used them, and matching a value in any
  category is exactly the bug the new filter fixes. (#12100)
