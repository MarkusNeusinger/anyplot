### Changed

- **Each route of the agent chat takes only the body it needs.** The bound
  on request bodies gave every route of the two chat lanes the cap of the
  largest one, the file conversion. Now the paste takes about 2 MB (its
  1 MB of text as JSON writes it), the file conversion keeps its 6.7 MB,
  and every other chat route takes the API's default of 64 KiB, answered
  with the `too_long` code the page already reads. The two routes that
  carry data must declare a `Content-Length` (`411 length_required`
  otherwise, as the conversion already answered). Their bodies above
  64 KiB are taken a few at a time (`503 capacity` for one more, which the
  page words as busy) and have to arrive in time (`408 upload_timeout`
  for a body that stalls or takes too long). The bound itself gained
  rules for single routes, looked at before the prefixes, and the places
  for large bodies with their time limits; both are general, and the
  chat's table lives beside its routes. No limit on what a visitor may
  paste or upload changes. One test holds the table against the app's
  routes by endpoint, and two build the largest body each data route
  accepts and check that it fits its bound. (#13178)
