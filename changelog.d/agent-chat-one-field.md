### Added

- **A decimal comma reads ambiguous dots again from the pasted cells.** A pasted number column of whole numbers
  and `1.234` shapes that nothing else in the file settles now reads as decimals with a warning ("dots read as
  decimal points; say so in the chat if they separate thousands"), and the paste keeps the column's cells as
  written. When the user says the dots separate thousands, the assistant's `set_type` with a decimal comma reads
  the column again from those cells, so `7.000` becomes 7000 rather than 7, while the rows are still the paste's.
- **`agent_input_routed`.** A Plausible event with `as` (`data`, `message`) and `via` (`paste`, `file`) counts how
  the message box takes each paste and file, for tuning the routing. `agent_data_file` gains the outcomes
  `attached` and `removed`; `filled`, `replaced` and `kept` end with the data card's box.

### Changed

- **One chat field for everything.** The agent chat's message box takes the data now: a table pasted into it, or a
  file opened with `.open()` beside it, dropped anywhere on the chat or pasted as a file, waits above the text as an
  attachment with its name, its lines and its size, and Enter sends it. One line, code, prose, a formula or a
  request for data stays typed text, by rules the page and the server share as 41 test cases. The data card loses
  its text box, its counter, `.parse()`, `.open()`, `.replace()`, `.keep()` and its drop zone, and shows once there
  is data; a workbook's sheet picker reads the stored file again. A table over 1 MB or 20,050 lines turns the
  attachment red, and so does one the server refused, with the reason under it. While an attachment waits, the plot
  buttons wait too.
- **The note typed with a paste is its first turn.** Text typed beside an attachment goes with it: once the data is
  stored, the assistant summarizes it in two sentences and acts on the note in the same reply ("nur 2024", "the
  decimal mark is a comma", a title for the first plot, a question about the data) instead of a summary first and
  the note after. A note the scope judge refused is followed by the summary, which skips the judge; when nothing
  was stored (a table read from text, a refusal), the note goes back into the box, and `.discard()` of a table read
  from text gives back what it came from: short pasted text into the box, a file or a longer text as the
  attachment. The scope judge reads the note alone; the paste's notes and file name reach the assistant beside it.
- **The message box no longer cuts a long text.** Over 2,000 characters the counter turns red and nothing sends
  until it fits. Enter sends (also with Ctrl or ⌘), Shift+Enter is a new line, and an input method's composition
  keeps Enter for itself. A draft or an attachment not sent yet makes a reload ask first.
- **The assistant sends the user to the message box.** Its prompt names the attachment and `.open()` in the
  composer, never the data card's box or `.parse()`; a small table typed as a message gets the answer that data
  comes as a paste of at least two rows or a file.
