Fixes duplicate metadata elements (title, description, and OG/Twitter properties) that are present in the shell `index.html` by default and redundantly appended when React routes boot up and hydrate. We now mark the 6 shell tags with `data-shell-default` and aggressively strip them immediately before creating the React root.
Additionally, `DebugPage` now consistently sets its own explicit title.

Tests added for both the DOM utility and integration into the specific pages.

Verification steps run successfully:
```
yarn lint
yarn fm:check
yarn type-check
yarn test src/pages src/utils
yarn build
```

Refs #9629
