### Added

- **The agent chat offers the plot in the new library with your decisions.** After a library switch
  whose answer offers it, the composer's create action reads "plot in seaborn with your 3 decisions"
  and sends `carry_plot`; picking a library runs nothing until that click, so browsing costs nothing.
  `.create_plot()`, or `.start_over()` once the library has a plot, stays beside it as the plot from
  the catalogue code, which keeps your decisions too, and the offer ends once a plot ships in that
  library. (#12522)
- **The remembered decisions stand above the composer.** The plot memory's entries, the decisions every
  next plot takes over, are listed with `.forget()` each and `.forget_all()` for a blank start, the only
  ways the memory is cleared; the list is read again after every turn, after a switch and after a
  removal, hides while the memory is empty and waits while anything runs. (#12522)

### Changed

- **The agent chat picks its library in a menu.** A chip like the language chip,
  `lib: matplotlib · python`, opens the libraries grouped by language and, for the admin,
  `all libraries`, in place of a pill per library (up to 16 with `all`). The pills' rules stay, and a
  refused switch shows its reason under the chip instead of in the thread. (#12522)
