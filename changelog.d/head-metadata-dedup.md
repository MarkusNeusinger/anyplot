### Fixed

- **One title and description per page.** The SPA shell in `app/index.html`
  kept its default `<title>`, description, and Open Graph and Twitter tags
  after a page rendered its own, so every route carried two of each and the
  shell's description came first. The six defaults are now marked
  `data-shell-default` and step aside only while a page renders a tag of the
  same kind (`watchShellDefaults` in `app/src/main.tsx`), so they still serve
  clients without JavaScript, a route whose chunk is loading, the error
  boundary, and pages without a description of their own; `/debug` has its
  own title. Built from the better of two Google Jules variants, measured on
  the built pages; the other deleted the shell defaults outright. (#12442)
