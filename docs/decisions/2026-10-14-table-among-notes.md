# Pasted data must work with notes, metadata or total rows around the table

- Date: 2026-10-14
- Proposed: the reader took a paste as a bare table. A test with a raw Open-Meteo weather download,
  which starts with two metadata lines, turned that metadata into the header and lost the data
  columns.
- Decided: his rule: data must parse when it carries lines around the table, such as metadata
  above it, a comment on the columns, a source line below it or a total row at the end. The reader
  now finds the table among the lines and keeps the others as the user's notes on the data.
- Where: #12166, #12168, `README.md` ("How I build anyplot")
