/**
 * What the agent chat's error codes mean, in the page's voice. The request id
 * stands next to the text only for a fault of the server or the connection (a
 * 5xx, no answer, a stream's error event), where a report needs it to find the
 * request. A refusal (a 4xx) names its cause in the text, which the visitor acts
 * on, so it shows no id (`AgentApiError.shownRef`).
 * Codes: docs/reference/api.md ("Agent error responses", "SSE protocol").
 */

import type { ConfirmLoss } from 'src/hooks/useAgentSession';
import { countOf } from 'src/sections/agent-chat/countOf';
import type { ChainStop } from 'src/sections/agent-chat/plotChain';

/** Errors of a turn (stream `error` events and failed requests). */
export const ERROR_TEXT: Record<string, string> = {
  // The agents service's `capacity`: a full run queue, a wait that ran out, or a model call the model service still
  // refused for its quota or an overload after the retries (`model_busy`, the root's call before any plot run).
  capacity:
    'the server is busy: the run queue is full, the wait ran out, or the model service is overloaded; try again in a few minutes',
  // The user's own cap (`user_max_runs` of `/status`: 2, or 5 for an admin): plots and data runs queued or
  // running across the user's windows; on the public lane also the network's cap (`AGENT_IP_MAX_RUNS`, 4).
  run_limit:
    'your plots and data runs in other windows, or others on your network, already fill the share; wait until one finishes, then try again',
  deadline: 'the run took too long and was stopped',
  guard_unavailable: 'the scope check is unavailable right now; try again',
  // The assistant wrote no reply, also when asked once more; a paste stays unsummarized for the next message.
  no_reply: 'the assistant sent no reply; send your message again',
  upstream: 'the agents service did not answer or cut the stream',
  internal: 'something went wrong on the server',
  // Per window since 2026-10-21: the user's other windows never cause it.
  run_active:
    'a run, a theme render or a paste is still in progress in this window (a stopped run ends after its current step); try again in a moment',
  too_long: 'the message is longer than 2,000 characters',
  not_eligible: 'this plot cannot be adapted in that library',
  not_found: 'that plot or library is not in the catalogue',
  session_expired: 'the session expired',
  // The admin fan-out's copy of the page session's data (`.plot_all()`).
  unconfirmed: 'the data is not confirmed any more; check it, then .plot_all() again',
  has_dataset: 'this library already holds data; close the panel and .plot_all() again',
  // A server without the copy, and data the assistant changed or computed, which has no paste to post again.
  copy_unavailable:
    'this server cannot copy changed or computed data yet; paste or open the table, or try again after the deploy',
  rate_limited: 'the daily limit is reached; try again tomorrow',
  // The public lane's cap on live sessions per network (`AGENT_IP_MAX_SESSIONS`).
  session_limit:
    'too many chats are open from your network; close another window, or try again within the hour',
  unreachable: 'no answer from the server: the connection dropped, or an admin sign-in expired',
  network: 'the server did not answer; check your connection',
  // The public lane's Turnstile check on opening a session (`src/lib/turnstile.ts`), in the browser or on the
  // server; `ReloadHint` adds the "try again" after it.
  bot_check_failed: 'the browser check did not go through',
  bot_check_unavailable: 'the browser check is not available right now',
};

/**
 * The plain label over a refusal in the thread, by the stream's refusal code (`refusals.yaml`).
 * The code itself is the service's word for the log: the visitor reads this label and the fixed
 * text under it, and finds the code behind the label's ⓘ.
 */
export const REFUSAL_LABEL: Record<string, string> = {
  out_of_scope: 'outside this chat',
  needs_data: "can't fetch data",
  other_library: 'another library',
  unsupported_content: 'text only',
  budget: 'usage limit reached',
  service_paused: 'chat paused',
  rate_limited: 'too many messages',
  daily_limit: "today's limit reached",
  session_closed: 'chat closed',
  locked_out: 'paused until tomorrow',
};

/** A refusal's label; a code the page does not know yet still reads as a refusal, never as a code. */
export function refusalLabel(code: string): string {
  return REFUSAL_LABEL[code] ?? 'not answered';
}

/**
 * The run's quiet line while the page reads the rest of a turn whose stream was cut: the
 * server runs the turn on, so its result is still to come and nothing reads as an error yet.
 */
export const RECONNECTING_TEXT = 'connection lost · reconnecting…';

/** The working line's words while a plot is drawn (`workingLine`), and the status line's. */
export const DRAWING_TEXT = 'drawing your plot';
/** The same words on a phone (the v4 phone mock): `drawing · 0:42`. */
export const DRAWING_SHORT = 'drawing';
/** How long a plot usually takes, at the status line's end while one is drawn. */
export const USUAL_PLOT_TIME = 'usually 1–3 min';

/**
 * An elapsed time as the working line's clock reads it: `0:42`, `12:05`, past an hour `1:02:03`;
 * never below zero, so a clock that starts a moment late reads `0:00`.
 */
export function elapsedClock(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = String(total % 60).padStart(2, '0');
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, '0')}:${seconds}`
    : `${minutes}:${seconds}`;
}

/**
 * Where the own turn waits in the run queue, after `you are`: position 1 runs next, so `next`;
 * then `2nd`, `3rd`, `4th`, `11th`, `21st`.
 */
export function queuePlace(position: number): string {
  if (position <= 1) return 'next';
  const tens = position % 100;
  const suffix =
    tens >= 11 && tens <= 13
      ? 'th'
      : position % 10 === 1
        ? 'st'
        : position % 10 === 2
          ? 'nd'
          : position % 10 === 3
            ? 'rd'
            : 'th';
  return `${position}${suffix}`;
}

/**
 * Why a `plot` event shipped no render (`failed` or `not_ready`). `data_unconfirmed` has no line:
 * the thread shows no failed plot for it, only the status line at the chat frame's foot
 * (`useAgentSession`).
 */
export const PLOT_FAILED_TEXT: Record<string, string> = {
  validation: 'the adapted code did not pass the safety checks',
  render: 'the plot did not render',
  deadline: 'the run ran out of time before a render passed',
  budget: 'the usage limit is reached',
  // The model service refused a call for its quota or an overload, also after the retries.
  busy: 'the model service is busy; try again in a minute',
  error: 'something went wrong while adapting',
  no_dataset: 'paste and parse your data first',
  incomplete_bindings: 'pick a column for every required role first',
};

/**
 * An instant on the browser's own clock (`01:00`), or null for one that does not
 * parse: the agents service counts its days in UTC, the user reads their own time.
 */
export function localClock(iso: string): string | null {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

/** The next 00:00 UTC, when the agents service's day budget starts again from zero. */
export function nextUtcMidnight(now: number = Date.now()): string {
  const date = new Date(now);
  return new Date(
    Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 1)
  ).toISOString();
}

/**
 * The whole chat paused for the day: the service's day budget is spent. `until` is
 * the reset in the user's time; the server's own refusal says 00:00 UTC, since it
 * does not know the user's time zone. The line of a data call the pause refused (a
 * paste, a conversion: `429 service_paused`); before the user types, the frame's
 * tab says it as its mood (`resting until 01:00`, `LoadMood.tsx`).
 */
export function servicePausedText(until: string = nextUtcMidnight()): string {
  return `the chat has reached today's overall limit and is paused until ${localClock(until) ?? '00:00 UTC'}`;
}

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
  // Text the chat takes goes there by itself (`parseData`); only longer text meets these lines.
  code: 'looks like code that makes data: shorten it to 2,000 characters, keeping only the part that computes the data, and the chat runs it',
  formula:
    'looks like a formula: shorten it to 2,000 characters, and the chat computes the table from it',
  data_request: 'asks for data: shorten it to 2,000 characters, and the chat makes the data',
};

/**
 * A data call's failure text: `DATA_FAILURE`, except the service's pause
 * (`429 service_paused`), which names its end in the user's own time.
 */
function dataFailureText(code: string): string | undefined {
  return code === 'service_paused' ? servicePausedText() : DATA_FAILURE[code];
}

/**
 * The full data view's line when it could not read the data (`DataView.tsx`): a code of the
 * data route, or `csv` with the reader's sentence for a file that breaks the canonical format.
 */
export function describeViewFailure(code: string, ref: string | null, detail?: string): string {
  const text =
    code === 'csv'
      ? `the file is not the CSV it should be (${detail ?? 'unreadable'})`
      : code === 'not_found'
        ? 'this server cannot show every row yet'
        : code === 'too_large'
          ? 'the data is larger than the view reads (4 MB)'
          : (dataFailureText(code) ?? `request failed (${code})`);
  return `could not show every row: ${text}${ref ? ` · ref ${ref}` : ''}`;
}

/**
 * The composer's filled plot button after a change to data the user had confirmed: it still
 * confirms and plots in one click, and its name says that the plot will show the new data.
 */
export const NEW_DATA_PLOT = 'plot the new data';

/**
 * What dropped a confirmation the user had given, as the status line at the chat frame's foot says
 * it, the description of the composer's action (`.create_plot()`, after a data change `plot the
 * new data`, or `.plot_all()` with `all` pressed), which points up at the card above it. The
 * thread carries no notice of its own for it: the status line says it.
 */
export const CONFIRM_LOST_STEP_TEXT: Record<ConfirmLoss, (action: string) => string> = {
  bindings: action => `bindings changed · check them above, then ${action}`,
  data: action => `data changed · check it above, then ${action}`,
  server: action => `check the data above, then ${action}`,
};

/** The details behind a thread notice's ⓘ: the button's name, the popover's heading and its lines. */
export interface NoticeInfo {
  label: string;
  heading: string;
  lines: readonly string[];
}

/**
 * The thread's one quiet line when the session's first typed message (`detected`) or a paste
 * before any typed message (`pasted`, the language of its notes or column names) set the
 * session language; a choice from the chip or the chat says nothing. The line names only the
 * language: where it came from, that a plot keeps its own and the chip that changes both are
 * behind its ⓘ, as the experimental notice does it.
 */
export function languageNotice(
  language: string,
  source: 'detected' | 'pasted'
): { text: string; info: NoticeInfo } {
  return {
    text: `reply language: ${language}`,
    info: {
      label: 'About the reply language',
      heading: '# reply language',
      lines: [
        source === 'pasted' ? 'detected from your pasted data' : 'detected from your message',
        'a plot you have keeps its language',
        'the language chip in the header changes both',
      ],
    },
  };
}

/**
 * The browser's confirm before a link inside the site leaves the chat with data
 * or plots in it; a reload or a closed tab gets the browser's own wording.
 */
export const LEAVE_TEXT =
  'leave the chat? the session ends here, and its data and plots cannot be restored';

/**
 * The admin menu's "view as visitor" switched while the session holds work: the other lane
 * opens a session of its own (`AgentChatPage`).
 */
export const VIEW_SWITCH_TEXT =
  'switch the view? the session ends here, and its data and plots cannot be restored';

/**
 * The how-to behind the chat's `# chat ⓘ` (the data card's `# your data ⓘ` until the message box
 * took the data; a label and a paragraph under the card before 2026-11-02, owner: far too long,
 * and interesting only once): the formats, how a table or a file comes in with a note, code or a
 * formula instead of a table, the steps, a fix in plain words and changes afterwards. Code and a
 * formula go as a message, which takes 2,000 characters (`MAX_MESSAGE_CHARS`); the assistant
 * translates code in any language into Python, so no line lists the languages as if they were
 * all. Example data is `.example_data()` in the composer's row. The owner reads every user-facing
 * text: keep them in the PR's "Texts to read".
 */
export const DATA_HOWTO = [
  'formats: CSV, TSV, JSON, plain text, Excel, ODS, Parquet, Feather or NumPy',
  'paste or drop a table or a file: it waits in the message box until Enter',
  'type a note with it: "only 2024", "the decimal mark is a comma"',
  'code or a formula that makes data goes as a message, up to 2,000 characters',
  'check the preview and the bindings → .create_plot()',
  'the assistant fixes your data in plain words: "sum per month"',
  'afterwards, ask for changes: "log scale on y", "label the outliers"',
] as const;

/**
 * The message box's placeholder before any data: the box's own ways in, a table or a file; the
 * data line right above it offers example data and `.open()`.
 */
export const NO_DATA_PLACEHOLDER = 'paste a table or drop a file';

/**
 * The message box's placeholders with data on a phone (`PHONE_QUERY`), where a browser cuts a
 * placeholder without an ellipsis (owner, 2026-11-08): before the library's first plot, and once
 * it has one. The wider screen keeps its longer words.
 */
export const PHONE_PLACEHOLDER = {
  first: 'ask or say what to plot',
  change: 'ask for a change',
} as const;

/** Failures only the language chip meets; any other code reads as the page's turn errors do. */
export const LANGUAGE_FAILURE: Record<string, string> = {
  invalid: 'the server refused this language name',
  session_expired: 'the session expired',
};

export function describeLanguageFailure(code: string, ref: string | null): string {
  const text = LANGUAGE_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return ref ? `${text} · ref ${ref}` : text;
}

/** Failures only the library menu meets; any other code reads as the page's turn errors do. */
export const LIBRARY_FAILURE: Record<string, string> = {
  // Another spec than the session's, until the plot-type switch.
  invalid: 'the server refused this switch',
  not_found: 'this plot is not in the catalogue for that library',
};

/** The library menu's failure line: the library stays the one it was. */
export function describeLibraryFailure(code: string, ref: string | null): string {
  const text = LIBRARY_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return `could not switch: ${text}${ref ? ` · ref ${ref}` : ''}`;
}

/**
 * What `.start_over()` at the end of the line at the chat frame's foot does, and the plot button
 * when its click starts from the catalogue plot although the library has one (data or bindings
 * changed since): the catalogue code again, with the remembered decisions, which only the user
 * clears. Its `title`, and the hidden text both name as their description.
 */
export const START_OVER_HELP = 'new from the catalogue plot; keeps your remembered decisions';

/** What the remembered decisions do, behind the ⓘ at the end of their list (`Remembered`). */
export const REMEMBERED_DETAILS = [
  'every next plot keeps these decisions, also in another library',
  '.start_over() keeps them too; only .forget() and .forget_all() remove them',
] as const;

/** The first line behind that ⓘ once the memory has no room; the chapter line itself says `full`. */
export const REMEMBERED_FULL = 'full: forget one before a new decision fits';

/**
 * The label a question's reply starts with (the v4 mock): the turn changed nothing, by the
 * server's word and by what the page saw. On screen with its `?` before it; a screen reader reads
 * `ANSWER_LABEL_SPOKEN` instead, and the question's bubble starts with `QUESTION_WORD`.
 */
export const ANSWER_LABEL = 'answer · nothing changed';

/** The same in words, which a screen reader reads in its place: it reads `·` badly. */
export const ANSWER_LABEL_SPOKEN = 'answer, nothing changed';

/** What a question's bubble starts with for a screen reader, in place of its `?` mark. */
export const QUESTION_WORD = 'Question:';

/** The name of a chapter's count of its questions, which jumps to them in turn (PLAN §4). */
export function questionJumpName(count: number): string {
  return count === 1
    ? '1 question in this chapter, go to it'
    : `${count} questions in this chapter, go to the next`;
}

/** Failures of a removal from the remembered list; any other code reads as the page's turn errors do. */
export const MEMORY_FAILURE: Record<string, string> = {
  // The assistant's `forget` or another window removed it first; the list is read again.
  not_found: 'that decision was already forgotten',
  run_active: 'a run is in progress in this window; try again when it is done',
};

/** The remembered list's failure line: the decision stays in the list. */
export function describeMemoryFailure(code: string, ref: string | null): string {
  const text = MEMORY_FAILURE[code] ?? ERROR_TEXT[code] ?? `request failed (${code})`;
  return `could not forget: ${text}${ref ? ` · ref ${ref}` : ''}`;
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
 * Why a dropped, chosen or pasted file did not become the message box's attachment, by the
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
  file_array_shape:
    'holds no array a table can be read from (1-D, 2-D or a 1-D structured array); save the data as one of those or as a table',
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
 * server names), in the page's words.
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
  let text = CONVERT_FAILURE[code] ?? dataFailureText(code) ?? `could not be read (${code})`;
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
    // The names, because a step that changes the data says what it changed.
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
      `${count(warnings.list_columns, 'list column')}: the table comes as JSON records, and the parse gives one row per value`
    );
  }
  return parts;
}

/**
 * The status line's part while an attachment waits that only Enter sends, in place of the step's
 * part: one still read on the server or over the cap, or with the admin's fan-out on, whose
 * `.plot_all()` takes data already stored. The `↵` names the key, and the button that a phone
 * shows inside the message box.
 */
export const ATTACHMENT_LINE =
  'the attached table is read when you press Enter ↵, with a note if you like';

/**
 * The status line's part while an attachment waits, in place of the step's part. With `action`,
 * the plot button the attachment goes with (`plotChain.ts`): its click reads the attachment and
 * plots it, while Enter only reads it. Without, `ATTACHMENT_LINE`. While the session holds data
 * of `rows` rows, the line says the attachment replaces it: a paste starts the data's versions
 * anew, so `.undo()` cannot bring the old data back, which the line says before the user sends.
 */
export function attachmentWaitLine(rows: number | null, action: string | null = null): string {
  const replaces =
    rows === null ? null : `replaces your data (${countOf(rows, 'row')}, no .undo())`;
  if (action === null) {
    return replaces === null
      ? ATTACHMENT_LINE
      : `the attached table ${replaces} when you press Enter ↵, with a note if you like`;
  }
  return replaces === null
    ? `${action} reads the attached table and plots it · Enter ↵ only reads it`
    : `the attached table ${replaces} · ${action} reads and plots it, Enter ↵ only reads it`;
}

/** The status line's part while the plot button's one click reads the box's data (`plotChain.ts`). */
export const CHAIN_READING_TEXT =
  'reading your data · the plot follows by itself unless something needs a look';

/**
 * The status line's part after the plot button's one click stopped at the data card
 * (`plotChain.ts`, `ChainStop`): what to look at, then the button (`action`) as it reads now.
 */
export function chainStopText(stop: ChainStop, action: string): string {
  switch (stop.reason) {
    case 'question':
      return `the assistant asked a question · answer it in the box, or ${action}`;
    case 'data_warnings':
      return `${countOf(stop.count, 'warning')} on the data · check above, then ${action}`;
    case 'tables':
      return `the paste held ${stop.count} tables · check the one read above, then ${action}`;
    case 'wide':
      return `the table is wide for this plot · check .to_long() above, then ${action}`;
    case 'binding_warning':
      return `a warning on ${stop.role} · check it above, then ${action}`;
    case 'bindings_failed':
      return `the binding check failed · check the bindings above, then ${action}`;
    case 'refused':
      return `the reading ended in a refusal · see above, then ${action}`;
    case 'error':
      return `the reading ended in an error · see above, then ${action}`;
    case 'stopped':
      return `the reading was stopped · check the data above, then ${action}`;
  }
}

/** The message box's placeholder while an attachment waits: the typed text goes with it as its note. */
export const ATTACHMENT_PLACEHOLDER = 'add a note for this table, or press Enter';

/** Under a pasted table or a file too large for the dataset route (`overCap`). */
export const ATTACHMENT_OVER_CAP_TEXT =
  'at most 20,000 rows and 1 MB: filter first, or .open() an Excel or Parquet file (5 MB)';

/** The drop hint over the composer while a file is dragged over the chat, and why a drop would wait. */
export const DROP_HINT_TEXT = {
  ready: 'drop the file to attach it',
  reading: 'a file is still being read: drop the next one when it is done',
  locked: 'all libraries are plotting this data: close the panel first',
  working: 'a step is still running: drop the file when it is done',
} as const;

/** A file dropped or chosen while the session works on something: the server runs one thing at a time. */
export const FILE_BUSY_TEXT =
  'a step is still running; drop or open the file again when it is done';

/** A file dropped while the admin fan-out's panel copies the data: the data waits until it closes. */
export const FILE_LOCKED_TEXT =
  'all libraries are plotting this data; close the panel, then drop or open the file again';

/** A file dropped or chosen while the server still reads the one before. */
export const FILE_CONVERTING_TEXT =
  'a file is still being read on the server; drop or open the next one when it is done';

/** The line under the box for a refused file, the name in quotes first. */
export function describeFileRefusal(name: string, code: string): string {
  return `"${name}" ${FILE_REFUSAL[code] ?? FILE_REFUSAL.binary}`;
}

/**
 * A failed data call in one line: what the data fails on when the server named
 * it (never only "could not read", which leaves the user nothing to fix), else the code's
 * text, then the request id. The cause stands alone: it is a whole sentence,
 * and some say the format WAS read ("the data reads as JSON Lines, but line 2
 * …"), which a "could not read this as …" lead would contradict.
 */
export function describeDataFailure(
  code: string,
  ref: string | null,
  cause: string | null = null
): string {
  const text = cause || (dataFailureText(code) ?? `request failed (${code})`);
  return ref ? `${text} · ref ${ref}` : text;
}
