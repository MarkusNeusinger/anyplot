### Fixed

- **A kept plot wish survives its own turn and the user's back-and-forth.**
  In "Use with my data", a wish kept before the data is confirmed ("top 10")
  is now judged against the bindings when the plot runs, not at every
  binding write, so unbinding and binding the same column on the way no
  longer drops it. The turn that keeps a wish holds it for the bindings and
  data it ends with, whatever order the assistant kept, bound and changed
  them in. A wish written for a column the user has since rebound is still
  dropped, as before. (#12585)
- **The assistant describes the plot by the columns it drew.** The plot
  result tells the assistant which columns each role took and whether a kept
  wish was used or dropped. It stops calling a plot of `Stock` unfit for an
  earlier "distribution of the prices" after the user rebound the values by
  hand, and stops naming the old binding. (#12585)
- **The plot is checked only for texts the user wrote.** A title or number
  format the plot must show has to stand, as a whole, in the user's own
  words: the message of that turn or the notes pasted with the data (case,
  spacing, quote marks and the kind of dash aside). On the page's
  `.create_plot()` and "plot in …" buttons the assistant can no longer
  re-send a request from an earlier turn; the kept wish and the plot memory
  carry the user's words. (#12585)
- **The plot memory holds each decision once.** A decision that differs only
  in case, spacing or a closing punctuation mark is the same one, and the
  assistant leaves a listed decision out in any wording, passing a change
  with the entry it replaces. (#12585)
