### Fixed

- **Scroll-to-top button no longer hides under the feedback button.** On
  `/plots` and `/specs` it sat in the feedback button's bottom-right corner —
  fully covered on desktop, a 28 px overlap on phones. It now sits 8 px to the
  left of the feedback button on the same row, rises with it above the footer
  on phones, and the quick-feedback "Thanks!" appears above the button instead
  of in that slot. One `ScrollToTopFab` replaces the copy each page carried,
  and every floating button reads its position from one shared corner geometry
  (`theme/floating-actions.ts`), so they cannot drift into each other again.
