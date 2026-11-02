### Added

- **A public lane for the agent chat under `/agent`, shipped dark.** The new
  router calls the admin lane's route functions with an anonymous identity
  and the `public` tier, and answers `404` until the owner sets
  `_AGENT_PUBLIC_ENABLED=true` on the deploy-api trigger, on top of
  `AGENT_ENABLED`, which stays the master switch. The page's random tab id
  (`X-Anyplot-Anon`) and the client's network go to the agents service, which
  salts both with a per-process salt, so no durable key links usage to an
  address; the session id travels in `X-Anyplot-Session`, never in a URL.
  The fan-out copy, the day budget and the case triage stay admin-only, and
  `GET /agent/lane` tells the site whether the door is open without an
  upstream call. The deploy smoke checks the door answers as the trigger set
  it.
- **Per-IP limits for anonymous callers.** The users of one network (an IPv4
  address or an IPv6 /64) share 4 sandbox runs at once, 100 pipeline runs and
  20,000,000 weighted tokens a day, and twice the per-user minute and day of
  pastes, conversions, chat turns and beacons: twice the per-user caps,
  because a tab id costs nothing to mint. The public lane holds at most 10 waiting runs in the
  agents queue, one API instance relays at most 20 public chat turns at once
  so the catalogue keeps half its request slots, and a network stores at most
  20 feedback cases an hour.

### Security

- **The site feedback's IP hash is salted and short-lived.** `POST /feedback`
  stored an unsalted SHA-256 of the client address without a time limit,
  which trying every IPv4 address undoes. It now stores an HMAC under a
  random per-process salt and clears it once its 10-minute window has
  passed; rows from before keep their old hash until a reviewed migration
  clears them. A log line of an unreachable agents service no longer names
  the session id.
