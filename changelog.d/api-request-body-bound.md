### Fixed

- **The API bounds a request body before it reads it.** A route with a body
  model has its body read and parsed by the framework before the route or
  any of its checks runs, so a size check inside a route came after the
  bytes were already in memory. A middleware directly around the router
  now refuses a request that declares more than the cap of its path
  without reading it, and counts a body that declares no length as it
  arrives and cuts it off at the cap. Both answer `413` in the standard
  error format. The agent lanes keep the cap their routes already declare;
  every other path takes a default of 64 KiB, far above the largest body
  those routes accept. Tests send through the real app and check that the
  reading stops, not only that the status is right.
