### Fixed

- **One title and description per page.** The SPA shell in `app/index.html`
  kept its default `<title>`, description, and Open Graph and Twitter tags
  after a page rendered its own, so every route carried two of each and the
  shell's description came first. The six defaults are now marked
  `data-shell-default` and removed when the app boots (`removeShellDefaults`
  in `app/src/main.tsx`), so clients without JavaScript still get them, and
  `/debug` has its own title. Chosen from two Google Jules variants by
  measuring the built pages; the other removed the shell defaults outright
  and left clients without JavaScript with no title.
