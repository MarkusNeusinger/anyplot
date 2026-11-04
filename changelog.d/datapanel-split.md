### Changed

- **The agent chat's data panel is split into five files.** `DataPanel.tsx` keeps the panel's state and layout;
  the file intake moves to the `useFileIntake.ts` hook, the card's content to `DataCard.tsx` and its building
  blocks to `dataCardParts.tsx`, and the sticky summary header to `PinnedData.tsx`. Behavior and rendered output
  are unchanged: a jsdom snapshot diff of 43 panel states against the base showed 0 differing lines. (#12550)
