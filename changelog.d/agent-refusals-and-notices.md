### Fixed

- **A note sent with a file is never refused as a request for data.** The scope judge sees the note alone, so
  "unemployment rate per country" with a Eurostat file read as a request to fetch figures and got the data
  refusal in red. A `needs_data` verdict on the note sent with a paste now goes on as in scope, and the root's
  instructions say that such a note never gets the data refusal. A refused note's summary now runs too: the page
  read the note's ended turn as still running and never sent it. (#12578)
- **A table typed into the message box is read as data.** Only a paste was routed, so a CSV table typed by hand
  went out as a message the assistant cannot read data from. Enter now routes the box's own text like a paste:
  a table goes to the dataset route at once, and × on a refused one puts it back into the box. (#12578)
- **One quiet line after a data change, and the button says what it does.** A data change followed by a plot the
  server refused showed the same instruction four times, once in red with the raw code `data_unconfirmed`. The
  refused plot adds no row now, the data change names itself in one notice ("data changed · check it, then plot
  the new data"), the plot button reads "plot the new data", and the root no longer calls the plot in the turn of
  its own data change or repeats the instruction in its reply. (#12578)
- **The data refusals name the message box and `.open()`.** The `needs_data` and `unsupported_content` refusals
  pointed to the data panel's field, which the one message box replaced; all 11 languages now name the message
  box and `.open()`. (#12578)
