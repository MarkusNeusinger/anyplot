/**
 * What the agent chat's error codes mean, in the page's voice. The code and
 * the request id stay visible next to the text, so a report can quote them.
 * Codes: docs/reference/api.md ("Agent error responses", "SSE protocol").
 */

/** Errors of a turn (stream `error` events and failed requests). */
export const ERROR_TEXT: Record<string, string> = {
  capacity: 'the run queue is full or the wait ran out; try again in a few minutes',
  deadline: 'the run took too long and was stopped',
  guard_unavailable: 'the scope check is unavailable right now; try again',
  upstream: 'the agents service did not answer or cut the stream',
  internal: 'something went wrong on the server',
  run_active: 'a run is already in progress, in this tab or another one',
  too_long: 'the message is longer than 2,000 characters',
  not_eligible: 'this plot cannot be adapted in that library',
  not_found: 'that plot or library is not in the catalogue',
  session_expired: 'the session expired; reload the page',
  rate_limited: 'the daily limit is reached; try again tomorrow',
  network: 'the server did not answer; check your connection',
};

/** Why a `plot` event shipped no render (`failed` or `not_ready`). */
export const PLOT_FAILED_TEXT: Record<string, string> = {
  validation: 'the adapted code did not pass the safety checks',
  render: 'the plot did not render',
  deadline: 'the run ran out of time before a render passed',
  budget: 'the usage limit is reached',
  error: 'something went wrong while adapting',
  no_dataset: 'paste and parse your data first',
  incomplete_bindings: 'pick a column for every required role first',
};

/** Failures of the dataset and bindings calls. */
export const DATA_FAILURE: Record<string, string> = {
  too_long: 'more than 200 KB; paste fewer rows',
  unparseable: 'could not read this as CSV, TSV, semicolon CSV or JSON',
  data_refused: 'the content check refused this data',
  guard_unavailable: 'the content check is unavailable right now; try again',
  rate_limited: 'the daily limit is reached; try again tomorrow',
  capacity: 'the server is busy; try again in a minute',
  run_active: 'a run is in progress; wait for it to finish',
  no_dataset: 'parse the data first',
  invalid: 'the server refused these bindings',
  session_expired: 'the session expired; reload the page',
  network: 'the server did not answer; check your connection',
};

/** Failures of a theme render or an image fetch on the result card. */
export const IMAGE_FAILURE: Record<string, string> = {
  render: 'this theme failed the render checks',
  error: 'the renderer could not run; try again',
  run_active: 'a run is in progress; try again when it is done',
  capacity: 'no render slot came free; try again',
  not_found: 'this version is no longer on the server',
  session_expired: 'the session expired; reload the page',
};

export function describeDataFailure(code: string, ref: string | null): string {
  const text = DATA_FAILURE[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}
