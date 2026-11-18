### Fixed

- **The debug page ignores a status answer that comes after it is gone.**
  Its first request set the page's state whenever it settled, also after
  the admin had moved on: a request that then failed forced a reload of the
  page they were on, and in a test run the late update was an unhandled
  error that failed a run in which every test had passed. The request's
  answer is now dropped once the page is gone or a newer request replaced
  it. (#13174)
