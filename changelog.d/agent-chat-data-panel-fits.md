### Changed

- **A binding dropdown greys out the columns its role cannot take.** In the
  data panel of "Use with my data", a column whose type the role refuses
  stays listed with the reason, `Industry (text) · not numeric`, and cannot
  be picked, where picking it brought a red refusal and the dropdown snapped
  back. The page mirrors the server's type table, and a test keeps the two
  equal. (#12574)
- **An attachment that replaces the data says so before it is sent.** While
  the session holds data, the line above the message box reads
  `# the attached table replaces your data (22 rows, no .undo()) when you
  send it`, since a paste starts the data's versions anew. (#12574)

### Fixed

- **A web table with grouped columns arrives whole.** A table copied from a
  web page whose header spans two rows (`Density` over `/km2` and `/mi2`)
  is read from the clipboard's HTML with its spans expanded, so the parser
  joins the two header lines into `Density /km2` instead of refusing the
  copy. Only the cells' text is kept, and the copied page is never run.
  (#12574)
