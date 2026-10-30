### Changed

- **The agent chat announces timestamps it shows in UTC.** R's and Julia's
  loaders read a timestamp with a time-zone offset in UTC, so a plot shows
  `08:00+01:00` as 07:00. The instant stays exact, but the clock time moves, and
  until now nothing said so. A plot whose data holds such cells now lists them in
  "what changed", counted per column, in the same words for R and Julia
  ("R converts 4 timestamps with a time-zone offset to UTC, so the plot shows
  their UTC clock time: 3 in 'Ankunft', 1 in 'Abfahrt'"). `Z`, `+00:00` and a
  timestamp without an offset keep their clock time and are not counted. The
  status stays as the render earns it, as with the other loader notes. The
  JavaScript runtime will use the same count and wording.
