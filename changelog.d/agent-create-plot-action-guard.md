### Fixed

- **A click on the plot button plots.** In two persona tests the user pressed
  the plot button right after a data change and got "not confirmed yet": the
  assistant had bound the new derived column inside the plot turn, which voided
  the click's confirmation. A turn of `.create_plot()` (also "plot the new data"
  and `.start_over()`), the switch offer's carry and `.plot_all()` now plots the
  data and bindings the click confirmed: the agents service refuses every tool
  that would change something in it, and the assistant plots all the same. A
  column you ask to have plotted is bound in the data turn that makes it, so the
  data panel shows it before the click, and the assistant no longer asks you to
  bind a column it can bind itself. (#12593)
- **A note sent with a re-paste is read as the table's note.** The assistant
  answered it with the rule for a table typed into the message ("I can't read
  data from the message itself"), although the table had arrived as the
  message's attachment. The session facts now say that the table came in as an
  attachment and is stored. (#12593)
