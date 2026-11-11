### Added

- **`plots_scrolled`: how far a visitor gets through the gallery.** One
  Plausible event per visit to `/plots`, sent when the visit ends, and none for
  a visit without scrolling. `share` is the deepest point as a share of the
  result list (`0-10`, `10-25`, `25-50`, `50-75`, `75-100`, the percentage the
  filter bar shows), `results` is the size of that list (`1-24`, `25-99`,
  `100-999`, `1000+`), and `filtered` says whether it was filtered. The gallery
  loads in batches, so the page has no fixed height and Plausible's own scroll
  depth says nothing about it. (#13046)

### Changed

- **The layout sends every page's pageview, at the navigation.** `RootLayout`
  records the page in a layout effect; the pages no longer send their own,
  150 ms late, from an effect. Only the gallery still records a page itself,
  when a filter changes its address without a navigation. Three visible
  consequences: the 404 page now records a pageview, under the path that was
  asked for; a visitor's visit to `/agent` counts whatever the page shows,
  also while the public lane is closed (`agent_open` still counts sessions
  only); and a spec page counts when it is opened, not once its data loaded.
  (#13046)
- **An address that only redirects is no page.** `/{spec}/{language}` and
  `/debug/agent` redirect in their route's loader now
  (`app/src/routes/redirects.ts`), so the router never renders them: no
  pageview, no history entry, and the page being left stays on screen until
  the destination is there. (#13046)

### Fixed

- **Plausible's scroll depth is measured against the page it belongs to.**
  Plausible's script closes the page being left when the next pageview
  arrives, and divides the deepest scroll offset by the document height it
  last observed. The late pageview arrived after the next page had rendered,
  so the depth of the page being left was divided by the next page's height:
  too low before a longer page, too high before a shorter one. Measured with
  the live script on the same clicks, a landing page left at 47 % was sent as
  30 %, an implementation page left at 63 % as 92 %, and the gallery after
  12,000 px as 1,176 %; all three are now sent as they are. The pageview goes
  out before the browser lays the next page out, and after the scroll reset,
  so the new page starts at the top. On Back and forward, where the browser
  restores the offset itself and Chrome does so only afterwards, the pageview
  is sent from the top and the offset put back before anything is painted.
  (#13046)
- **Back to the gallery starts from the top before the gallery restores its
  own offset.** The gallery turns the browser's scroll restoration off, so on
  Back the offset of the page being left stood until the gallery's restore, or
  for good when it had none to restore. (#13046)
