# A dropped file goes through the same door as a paste

- Date: 2026-10-15
- Proposed: the chat read pasted text; files of other formats needed a way in.
- Decided: a text file that is dropped or opened goes through the paste's own route, with no second
  door, and a binary file (Excel, OpenDocument, Parquet, Feather, Arrow, NumPy) through one
  conversion first. A file's name is screened on its own, always.
- Where: #12192, #12194, `docs/concepts/agent-network.md`
