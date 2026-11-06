### Fixed

- **A long reply is shortened, never refused.** A reply of the assistant over
  1,200 characters became the fixed "only this plot and your data" refusal
  unless the turn drew a plot, so an on-topic summary of a pasted bank export
  and an on-topic answer about the user's data came back refused in the persona
  tests. The output guard now asks the assistant once for a shorter reply, the
  way the reply-language check asks again, and sends that one or the reply cut
  at 1,200 characters.
- **A turn without a reply says so.** When the assistant's final answer held no
  text, the turn sent nothing but its end, and a paste with a note got no reply
  at all while the paste counted as summarized. The service now asks once more;
  a second empty answer ends the turn with the new `error` code `no_reply`,
  which the chat shows as the turn, and the paste stays unsummarized for the
  next message.
- **A note typed with a paste is read beside its table.** The scope judge saw
  such a note alone and refused a question about the pasted table as general
  advice. It now gets the plot's title and the table's column names (never a
  cell) with the note, and an off-topic or data-fetch verdict on a paste's note
  goes on to the assistant, which reads the note beside the table. An attack is
  refused as before, and a request for another library still gets its pointer
  to the catalogue.
