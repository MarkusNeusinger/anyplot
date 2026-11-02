### Added

- **Switch the plot's library from the chat.** "Make it in seaborn" now moves the plot: the assistant's
  new `switch_plot` asks for the switch, the turn's `done` carries it, and the page switches and makes the
  plot there at once with your decisions, as the library menu's carry run does. A switch the server
  refuses shows in the thread.
- **`.plot_all()` plots your tuned plot in every library.** The fan-out's dataset copy now brings the plot
  memory and a carry of the page's latest plot along, so each library's plot starts from its catalogue
  plot with your decisions instead of from scratch.
