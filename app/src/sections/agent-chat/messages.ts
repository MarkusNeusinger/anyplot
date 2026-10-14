/**
 * What the agent chat's error codes mean, in the page's voice. The code and
 * the request id stay visible next to the text, so a report can quote them.
 * Codes: docs/reference/api.md ("Agent error responses", "SSE protocol").
 */

import type { ConfirmLoss } from 'src/hooks/useAgentSession';

/** Errors of a turn (stream `error` events and failed requests). */
export const ERROR_TEXT: Record<string, string> = {
  capacity: 'the run queue is full or the wait ran out; try again in a few minutes',
  deadline: 'the run took too long and was stopped',
  guard_unavailable: 'the scope check is unavailable right now; try again',
  upstream: 'the agents service did not answer or cut the stream',
  internal: 'something went wrong on the server',
  run_active:
    'a run or a theme render is still in progress, in this tab or another one (a stopped run ends after its current step); try again in a moment',
  too_long: 'the message is longer than 2,000 characters',
  not_eligible: 'this plot cannot be adapted in that library',
  not_found: 'that plot or library is not in the catalogue',
  session_expired: 'the session expired',
  rate_limited: 'the daily limit is reached; try again tomorrow',
  unreachable:
    'no answer from the server: your sign-in may have expired, or the connection dropped',
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
  data_unconfirmed: 'confirm your data first: check the preview and the bindings, then .confirm()',
};

/** Failures of the dataset, bindings, confirmation and undo calls. */
export const DATA_FAILURE: Record<string, string> = {
  too_long: 'more than 1 MB; paste fewer rows',
  unparseable: 'could not read this as CSV, TSV, semicolon CSV or JSON',
  data_refused: 'the content check refused this data',
  // The dataset judge or the model that reads free text into a table failed closed.
  guard_unavailable:
    'the model that checks and reads your data is unavailable right now; try again in a minute',
  rate_limited: 'the daily limit is reached; try again tomorrow',
  capacity: 'the server is busy; try again in a minute',
  run_active: 'a run is in progress; wait for it to finish',
  no_dataset: 'parse the data first',
  // The service keeps the last five versions, so the history can end above version 1.
  nothing_to_undo: 'there is no earlier version to go back to',
  invalid: 'the server refused these bindings',
  session_expired: 'the session expired; reload the page',
  unreachable:
    'no answer: your sign-in may have expired (reload the page), or the connection dropped',
  network: 'the server did not answer; check your connection',
};

/**
 * What dropped a confirmation the user had given: the thread's warning notice
 * and the data card's step line next to `.confirm()` say it in these words.
 */
export const CONFIRM_LOST_TEXT: Record<ConfirmLoss, string> = {
  bindings: 'bindings changed · confirm the data again',
  data: 'the data changed · confirm it again',
  server: 'not confirmed on the server · confirm the data again',
};

/**
 * The thread's one quiet line when the session's first typed message set the
 * session language (`detected`); a choice from the chip or the chat says nothing.
 */
export const LANGUAGE_DETECTED_TEXT = (language: string) =>
  `language: ${language} · detected from your message · the lang chip in the header changes it`;

/**
 * The thread's one quiet line when a paste set the session language from the
 * language of its notes or column names (`pasted`), before any typed message.
 */
export const LANGUAGE_PASTED_TEXT = (language: string) =>
  `language: ${language} · detected from your pasted data · the lang chip in the header changes it`;

/** Failures only the language chip meets; any other code reads as the page's turn errors do. */
export const LANGUAGE_FAILURE: Record<string, string> = {
  invalid: 'the server refused this language name',
  session_expired: 'the session expired',
};

export function describeLanguageFailure(code: string, ref: string | null): string {
  const text = LANGUAGE_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}

/** Failures of a theme render or an image fetch on the result card. */
export const IMAGE_FAILURE: Record<string, string> = {
  render: 'this theme failed the render checks',
  error: 'the renderer could not run; try again',
  run_active: 'a run is in progress; try again when it is done',
  capacity: 'no render slot came free; try again',
  not_found: 'this version is no longer on the server',
  session_expired: 'the session expired; reload the page',
  unreachable: 'no answer: your sign-in may have expired (reload the page)',
};

export function describeDataFailure(code: string, ref: string | null): string {
  const text = DATA_FAILURE[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}
