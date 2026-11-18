### Fixed

- **The API bounds a request body before the application takes it.** A
  route with a body model has its body read and parsed by the framework
  before the route or any of its checks runs, so a size check inside a
  route came after the bytes were already in memory. A middleware in front
  of the router now refuses a request that declares more than the cap of
  its path, and counts a body that declares no length as it arrives: once
  it passes the cap, the refusal goes out and the application is handed no
  more of it. The middleware sends that `413` itself, so it is the same on
  every route and on the mounted MCP server: in the standard error format,
  and on the agent lanes with the `too_long` code those routes answer with
  themselves. The agent lanes keep the cap their routes already declare;
  every other path takes a default of 64 KiB, far above the largest body
  those routes accept. Tests send through the real app and check what the
  application was handed, not only the status, and one test holds the
  table of caps against the app's own routes. (#13172)
