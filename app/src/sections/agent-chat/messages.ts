/**
 * What the agent chat's error codes mean, in the page's voice. The code and
 * the request id stay visible next to the text, so a report can quote them.
 * Codes: docs/reference/api.md ("Agent error responses", "SSE protocol").
 */

import type { ConfirmLoss } from 'src/hooks/useAgentSession';

/** Errors of a turn (stream `error` events and failed requests). */
export const ERROR_TEXT: Record<string, string> = {
  capacity: 'the run queue is full or the wait ran out; try again in a few minutes',
  // The server's `AGENT_USER_MAX_RUNS` (3): plots and data runs queued or running across the user's windows.
  run_limit:
    'you already have 3 plots or data runs in progress in other windows; wait until one finishes, then try again',
  deadline: 'the run took too long and was stopped',
  guard_unavailable: 'the scope check is unavailable right now; try again',
  upstream: 'the agents service did not answer or cut the stream',
  internal: 'something went wrong on the server',
  // Per window since 2026-10-21: the user's other windows never cause it.
  run_active:
    'a run, a theme render or a paste is still in progress in this window (a stopped run ends after its current step); try again in a moment',
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
  unparseable: 'could not read this as CSV, TSV, semicolon CSV, JSON or JSON Lines',
  data_refused: 'the content check refused this data',
  // The dataset judge or the model that reads free text into a table failed closed.
  guard_unavailable:
    'the model that checks and reads your data is unavailable right now; try again in a minute',
  rate_limited: 'too many pastes in a short time; wait a minute and try again',
  daily_limit: "today's limit is reached; try again tomorrow",
  locked_out: 'paused until tomorrow after several refused requests today',
  session_closed: 'this chat is closed; reload the page to start a new session',
  capacity: 'the server is busy; try again in a minute',
  run_active: 'a run or another paste is still in progress in this window; wait for it to finish',
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

/**
 * Why a dropped, chosen or pasted file did not go into the data box, by the
 * format its first bytes name (`fileText.ts`) or the refusal. Spreadsheets,
 * Parquet, Arrow and NumPy go to the server (`CONVERT_FAILURE` below); pickle
 * and HDF5 are never read.
 */
export const FILE_REFUSAL: Record<string, string> = {
  pickle:
    'is a pickle file, which is never read because loading one can run code; export it as CSV or Parquet',
  hdf5: 'is an HDF5 file, which is not read here; export it as CSV or Parquet',
  pdf: 'is a PDF, which is not read here; copy the table in it and paste the text',
  archive: 'is an archive (zip, gzip or 7z); unpack it and drop the file inside',
  binary:
    'is not a format read here; drop a CSV, TSV, JSON, Excel, ODS, Parquet, Feather, Arrow or NumPy file',
  too_large: 'is more than 1 MB as text; drop a smaller file or paste fewer rows',
  too_large_binary:
    'is more than 5 MB; save a smaller file, or copy the cells you need and paste them',
  empty: 'is empty',
  unreadable: 'could not be read by the browser; try again',
};

/** Why the server did not convert a dropped binary file (`422 file_*` and the route's other errors). */
export const CONVERT_FAILURE: Record<string, string> = {
  file_unsupported:
    'is not a format the server reads; save it as CSV, Excel (.xlsx), ODS or Parquet',
  file_encrypted:
    'is protected by a password; remove the password (in Excel: File › Info › Protect Workbook), save it and drop it again',
  file_pickle:
    'is a pickle file, which is never read because loading one can run code; export it as CSV or Parquet',
  file_hdf5: 'is an HDF5 file, which is not read here; export it as CSV or Parquet',
  file_corrupt: 'could not be read: the file looks damaged, or it is not the format it seems to be',
  file_archive_limits:
    'unpacks to more than the server reads (100 MB, at most 250 times its own size); save a smaller file',
  file_too_many_rows:
    'has more rows than a table may have; filter it, or copy a range and paste it',
  file_too_many_columns:
    'has more columns than a table may have; copy a range of fewer columns and paste it',
  file_too_large: 'gives more than 1 MB of text; filter it, or copy a range and paste it',
  file_empty: 'has no cells with values',
  file_sheet_not_found: 'no longer has that sheet; drop the file again',
  file_array_shape: 'holds no 2-D or structured array; save the data as a 2-D array or a table',
  file_formulas_only:
    'contains only formulas without saved values; open it in Excel and save it once',
  file_object_array:
    'holds a pickled object array, which is never read because loading one can run code; save numbers or text',
  file_timeout: 'took longer than the 10 seconds a file may take to read; save a smaller file',
  file_too_complex: 'needed more memory than the reader may use; save a smaller file',
  file_unreadable: 'could not be read on the server; save it again or export it as CSV',
  convert_unavailable:
    'cannot be read right now, the file reader is not available; export it as CSV for now',
  rate_limited: 'could not be read: too many files in a short time; wait a minute and try again',
  daily_limit: "could not be read: today's limit of files is reached; try again tomorrow",
  locked_out: 'could not be read: paused until tomorrow after several refused requests today',
  session_closed: 'could not be read: this chat is closed; reload the page to start a new session',
  capacity: 'could not be read: the server is busy; try again in a minute',
  run_active: 'could not be read: another file is still being read; wait for it',
  too_long: 'is more than 5 MB; save a smaller file',
};

/** The formats the page sends to the server (`fileText.ts` `ConvertibleKind`), as a sentence names them. */
const KIND_NAME: Record<string, string> = {
  spreadsheet: 'a spreadsheet (Excel or OpenDocument)',
  parquet: 'a Parquet file',
  arrow: 'an Arrow or Feather file',
  numpy: 'a NumPy file',
};

/**
 * The broken part of a damaged file (`422 file_corrupt` with `damage`, a closed set the
 * server names; owner decision of 2026-10-16), in the page's words.
 */
export const DAMAGE_TEXT: Record<string, string> = {
  zip: 'its zip container is broken or cut off (an incomplete download or copy); save or download it again',
  workbook:
    'its workbook parts are missing or broken, so no sheet can be listed; open it in Excel or LibreOffice and save it again',
  sheet:
    'the cells of this sheet are broken; open it in Excel or LibreOffice and save it again, or pick another sheet',
  parquet: 'its Parquet footer or a data page is broken or cut off; write the file again',
  arrow: 'its Arrow or Feather structure is broken or cut off; write the file again',
  npy_header: 'its NumPy header is broken; save the array again with numpy.save',
  npy_data:
    'it holds less data than its NumPy header announces (a cut-off file); save the array again with numpy.save',
};

/**
 * The line for a file the server did not convert, the name in quotes first; a broken cap names its
 * numbers, and a damaged file the format its first bytes named (`kind`) and the broken part (`damage`).
 */
export function describeConvertFailure(
  name: string,
  code: string,
  measured: number | null,
  limit: number | null,
  ref: string | null,
  kind: string | null = null,
  damage: string | null = null
): string {
  let text = CONVERT_FAILURE[code] ?? DATA_FAILURE[code] ?? `could not be read (${code})`;
  // A damaged file names the format its first bytes claimed, and the part the server found broken.
  if (code === 'file_corrupt' && damage && DAMAGE_TEXT[damage]) {
    const as = kind && KIND_NAME[kind] ? ` as ${KIND_NAME[kind]}` : '';
    text = `could not be read${as}: ${DAMAGE_TEXT[damage]}`;
  } else if (code === 'file_corrupt' && kind && KIND_NAME[kind]) {
    text = `starts like ${KIND_NAME[kind]} but could not be read as one: the file is damaged (a cut-off download or copy), or it is another format saved under this name`;
  }
  const counted = (noun: string) =>
    measured !== null && limit !== null
      ? ` (${measured.toLocaleString('en-US')} ${noun}, the cap is ${limit.toLocaleString('en-US')})`
      : '';
  if (code === 'file_too_many_rows') text += counted('rows');
  if (code === 'file_too_many_columns') text += counted('columns');
  if (code === 'file_too_large') text += counted('bytes');
  return `"${name}" ${text}${ref ? ` · ref ${ref}` : ''}`;
}

/** What the server counted while it read a file, as the parts of the line under the box. */
export function describeConvertWarnings(
  warnings: {
    formulas_without_value?: number;
    hidden_sheets?: number;
    dropped_columns?: number;
    list_columns?: number;
    utc_timestamps?: number;
    renamed_columns?: number;
  },
  dropped: string[] = []
): string[] {
  const parts: string[] = [];
  const count = (value: number, noun: string) =>
    `${value.toLocaleString('en-US')} ${noun}${value === 1 ? '' : 's'}`;
  if (warnings.utc_timestamps) {
    parts.push(`${count(warnings.utc_timestamps, 'time-zone column')} written in UTC`);
  }
  if (warnings.renamed_columns) {
    parts.push(`${count(warnings.renamed_columns, 'repeated column name')} given a _2 suffix`);
  }
  if (warnings.formulas_without_value) {
    parts.push(
      `${count(warnings.formulas_without_value, 'formula cell')} saved without a value, left empty: open and save the file in Excel to store them`
    );
  }
  if (warnings.hidden_sheets) {
    parts.push(`${count(warnings.hidden_sheets, 'hidden sheet')} skipped`);
  }
  if (warnings.dropped_columns) {
    // The names, because a step that changes the data says what it changed (owner rule, 2026-10-15).
    const more = warnings.dropped_columns - dropped.length;
    const named = dropped.length
      ? `: ${dropped.map(name => `"${name}"`).join(', ')}${more > 0 ? ` and ${more} more` : ''}`
      : '';
    parts.push(
      `${count(warnings.dropped_columns, 'column')} of durations, intervals, binary, map or nested values left out${named}`
    );
  }
  if (warnings.list_columns) {
    parts.push(
      `${count(warnings.list_columns, 'list column')}: the table comes as JSON records, and .parse() gives one row per value`
    );
  }
  return parts;
}

/** A file dropped or chosen while the session works on something: the server runs one thing at a time. */
export const FILE_BUSY_TEXT =
  'a step is still running; drop or open the file again when it is done';

/** A file dropped or chosen while the server still reads the one before. */
export const FILE_CONVERTING_TEXT =
  'a file is still being read on the server; drop or open the next one when it is done';

/** The line under the box for a refused file, the name in quotes first. */
export function describeFileRefusal(name: string, code: string): string {
  return `"${name}" ${FILE_REFUSAL[code] ?? FILE_REFUSAL.binary}`;
}

/**
 * A failed data call in one line: what the data fails on when the server named
 * it (owner rule, 2026-10-16: never only "could not read"), else the code's
 * text, then the request id. The cause stands alone: it is a whole sentence,
 * and some say the format WAS read ("the data reads as JSON Lines, but line 2
 * …"), which a "could not read this as …" lead would contradict.
 */
export function describeDataFailure(
  code: string,
  ref: string | null,
  cause: string | null = null
): string {
  const text = cause || (DATA_FAILURE[code] ?? `request failed (${code})`);
  return ref ? `${text} · ref ${ref}` : text;
}
