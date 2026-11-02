### Added

- **Every row of your data in the agent chat, to search, sort and filter.**
  `.view_all()` next to the data card's preview opens the current data version
  in a read-only MUI X Data Grid (the MIT edition, loaded only when you open
  it): a search over every column, sorting (numeric columns by number, empty
  cells last), a column filter with `>` and `<` on numbers, column resizing and hiding, the
  dtype under each column name, both themes and phone width. Values appear
  exactly as the canonical `data.csv` holds them, which the new read-only
  route `GET /debug/agent/sessions/{sid}/dataset/data.csv` serves and a strict
  RFC 4180 reader parses in the browser, so nothing is rounded or reformatted
  and an empty cell stays empty. The free grid shows at most 100 rows a page;
  the search, the sort and the filter cover every row. Opening it reports the
  content-free outcome `opened_data_view`.
