### Changed

- **The agent chat's plot follows the site theme.** On the dark site the
  first render of each plot version is now dark, and on the light site it is
  light. The other theme is still one click away on the light and dark switch,
  and each version still takes one render. The page sends the theme the site
  shows with every turn (`POST .../messages?theme=`). The query parameter lets
  the page, the API and the agents service deploy in any order. A change made
  after a site-theme switch follows the switch. A theme the user asked for in
  the chat holds for later changes of that plot. The admin fan-out
  (`.plot_all()`) plots every library in the same theme. This fixes user test
  E2 of 2026-11-01, where the dark site showed a bright plot card.
