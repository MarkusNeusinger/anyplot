### Changed

- **The crawler path is bounded before more crawlers use it.** The hop from
  the site's nginx to the API for a prerendered page connects within 3
  seconds and waits 10 seconds for the answer, where nginx's default of 60
  seconds let a slow API hold the request slots people share (a crawler page
  takes 40 ms at the median and took 2.3 seconds at the slowest of 3,718).
  The prerendered pages have a cache of their own (`prerender_cache_maxsize`,
  1,000 pages), so a crawler reading the catalogue no longer pushes filters,
  the sitemap and the stats out of the API's shared cache. A path that can't
  be a spec id, and a library that doesn't exist or belongs to another
  language, are a 404 without a database query.
- **The debug page's machine readers matrix counts prerendered pages and
  shell reads apart.** `pages` was the sum of both, which hid a crawler that
  was answered with the app's empty shell; `shell` is a column of its own, in
  `GET /debug/machine-readers` and in the table.
