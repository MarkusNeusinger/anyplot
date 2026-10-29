### Fixed

- **Render cancellation test waits longer and fails clearly.**
  `test_local_backend_kills_the_container_on_cancellation` waited at most 10 s
  for both fake theme containers and then cancelled anyway, so a loaded runner
  could fail with a misleading "only one container killed" assertion. It now
  waits up to 25 s and raises a clear timeout error when the containers never
  start. Written by Google Jules; the race could not be reproduced locally.
  (#12449)
