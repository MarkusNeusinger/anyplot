/**
 * State machine of one "Use with my data" chat session (`/debug/agent`).
 *
 * Owns everything the chat page shows and every call it makes to the BFF
 * (`src/lib/agent.ts`): opening the session, the pasted dataset and its
 * bindings, the turns and their `anyplot/1` stream, the plot versions with
 * their images and code, the theme toggle, the library switch and Stop.
 *
 * Phases: `opening` → `ready` (or `unauthorized`, `ineligible`, `error`). At
 * most one turn runs at a time; while it runs, `run` holds its timeline and
 * queue position.
 *
 * Versions: the `plot` event carries `version`, the number the agents service
 * stored the result under, which the artifact (`?v=`) and theme toggle routes
 * take. Against a server without that field the hook counts the shipped plot
 * events instead (the server numbers them in the same order), which drifts
 * only when a stored version's event never arrives.
 *
 * Bindings: the dataset answer lists the spec's roles. A single role binds
 * under its own name, a variadic family `y` under its members `y1`, `y2`, ...;
 * the hook keeps the members contiguous (`compactFamilies`), so clearing `y2`
 * of three moves `y3` up. Every change replaces the whole set on the server.
 *
 * Transcriptions: pasted text that is not a table comes back as a table the
 * server read with a model and did not store (`transcription`). The dataset
 * and bindings stay as they were until the user confirms it, which posts the
 * table's CSV through the normal parse (`confirmTranscription`), or discards
 * it. A new parse, a library switch and a failed session clear it as well.
 *
 * Two steps, data first: step 1 ends when the user confirms that the stored
 * dataset and its bindings fit (`confirmData`, `POST .../dataset/confirm`);
 * only then does the page offer `.create_plot()` (step 2). The server drops
 * its confirmation whenever the dataset or a binding changes, and so does the
 * hook: a stored parse and any applied binding change clear `dataConfirmed`,
 * a library switch keeps it. A transcription clears it too, although the
 * server keeps its own until `.use()` stores the table: the user decides on
 * the data again either way. A turn can change the bindings on the server
 * too (the root's `set_bindings`): its `done` event carries the session's
 * bindings and step state, which replace the hook's (`server_sync`), so the
 * dropdowns show what the server holds and the panel goes back to step 1.
 * A `plot{not_ready, data_unconfirmed}` without that sync still drops the
 * flag, so the panel offers `.confirm()` again.
 *
 * A confirmation the user had given and then lost is named where it is lost:
 * the reducer watches the flag go from set to cleared, whatever action did it,
 * keeps the reason (`confirmLoss`: a binding change, new data, or the server's
 * word) for the data card's step line, and appends a warning notice to the
 * thread. The parse's own default bindings land while the flag is already
 * clear, so a first setup after a paste says nothing. The reason follows the
 * data the card shows: a later paste clears it, a later data change or undo
 * makes it a change of the data. The reducer numbers the thread items itself
 * (`nextItemId`), so it can append that notice in the one place every loss
 * passes through.
 *
 * Step 1 talks about the data. Every parse that stores a dataset (a table, or
 * a transcription's `.use()`) is followed at once by the turn
 * `{action: "summarize_data"}`, so the assistant's summary of the data is the
 * first thing in the thread; an undo, a library switch or a transcription that
 * still waits for its decision sends none. The user can then ask in words for
 * a change to the data ("read Anteil as numbers", "sum per month"): when the
 * assistant's `prepare_data` changed it, the turn's `done` carries the new
 * version (`dataset`), which replaces the preview, the profile and the
 * bindings, drops the confirmation and fills `dataChange` with the change
 * lines. `undoData` (`.undo()`, `POST .../dataset/undo`) restores the version
 * before the last change, unconfirmed as well; the data's `version` says
 * whether there is one (a paste is 1, the service keeps the last five).
 *
 * Formulas: the assistant's `generate_data` computes a table from a formula
 * the user asks for in the chat ("y = sin(x), x from -pi to pi"). Its `done`
 * carries the table like any data change: the next version when data exists,
 * or version 1 when the session had none, which then becomes the hook's first
 * dataset with the roles and default bindings `done` names (nothing to undo).
 * The dataset route refuses such text pasted into the data box with `422
 * formula`, because its free-text reader is a model that would write the rows
 * itself; the hook keeps the refused text (`formula`), and `sendFormula`
 * (`.send()`) sends it to the chat as the user's turn. Code that generates
 * data (Python, JavaScript, R) is refused the same way with `422 code`
 * (`formulaKind`), and the assistant's `run_data_code` runs it in the chat;
 * the version it stores carries the Python that ran (`code`).
 *
 * One thing at a time: the agents service runs one turn, theme render, page
 * build (a JavaScript version's `plot.html`) or paste
 * per session (each window opens its own, and the user's other windows never
 * block it) and answers anything else with `409 run_active`, a parse, an undo or a
 * binding change rewrites the data a turn reads, and a confirmation must cover
 * exactly the data it was given. So the hook starts none of these while
 * another is in flight, and Stop keeps the stream open until the server's
 * `done` confirms the run ended (at most `STOP_GRACE_MS`), so the next action
 * does not race the stopped run.
 *
 * Session lifetime: the session, with the pasted data and its renders, is
 * deleted when the page unmounts and on `pagehide` (a reload or a closed tab,
 * sent with `keepalive`); the server's idle sweep is the backstop. Nothing
 * restores it, so while it holds data, a plot or work in flight
 * (`sessionHoldsWork`) the page asks before it lets the user leave.
 *
 * Saving: `saveSession` (`.save()`) downloads the session's feedback case,
 * the conversation, code, images and config the agents service assembles,
 * as one JSON file. It only reads the session and starts no run, so no state
 * tracks it: the button keeps its own saving flag and failure line.
 *
 * Session language: one per session, for the assistant's replies and every
 * text in the plot, held as `plotLanguage` (`language` is the programming
 * language on this page). It starts as `en` with the source `default`,
 * whatever the browser's locale, as the server's does. A paste's answer may
 * bring `pasted` (the language of the notes around the table or of its column
 * names; only over `default` or an earlier `pasted`), with one quiet notice. The
 * `done` of the session's first typed message brings `detected` (`language_sync`), which
 * appends one quiet notice to the thread; a choice from the header's chip
 * (`setLanguage`, `PUT .../language`) or the assistant's `set_language` brings
 * `chosen`, which is final. Only the server's answers set it, and a `done` never
 * moves it down from `chosen` (a choice from another tab can land between the
 * server's finish and this page's `run_end`). It is no data change: it never
 * touches the confirmation.
 *
 * Quick feedback: `sendFeedback` (`.send()` on a result card) has the BFF store
 * the case of one version in the private case bucket. It starts no run and
 * waits for nothing else in flight, so it never blocks the flow, and a turn
 * never waits for it. The stored case is recorded on the version
 * (`PlotVersion.feedback`), which the card shows as `sent · v<n>`: the record
 * outlives the card's body, which a newer version collapses and unmounts. A
 * later send for the same version stores a new case that names the recorded
 * one as `replaces`, and replaces the record; the sending flag and the failure
 * line stay in the control. Version 0 is the chat itself, for a session that
 * made no plot (or a problem with the conversation rather than a plot): its
 * case holds the transcript, the profile, the bindings and, when ticked, the
 * current data, and its record lives on the session (`chatFeedback`).
 *
 * Analytics carry enum properties only, never text or data:
 * `agent_data_parsed{status, size_bucket}`, `agent_data_confirmed{size_bucket}`,
 * `agent_data_prepared{changes}`, `agent_data_undo{version}`,
 * `agent_plot_rendered{library, status, repaired, spec}`,
 * `agent_guardrail_block{reason}`, `agent_session_saved{include_data}` and
 * `agent_result_feedback{reaction, include_data, subject}`.
 *
 * Usage telemetry: after a copy, a download, a save or a sent feedback, a
 * fire-and-forget beacon (`POST .../outcome`) tells the BFF which action it
 * was and on which version (with the reaction for feedback), and nothing else:
 * no text, no file or column name, no code, no data. `reportOutcome` is the
 * result card's way in; the save and the feedback send it themselves.
 */

import { useCallback, useEffect, useReducer, useRef } from 'react';

import { useAnalytics } from 'src/hooks/useAnalytics';
import {
  agentApi,
  AgentApiError,
  type AgentEvent,
  type ArtifactName,
  type Binding,
  codeArtifact,
  type CodeArtifact,
  type ConvertAnswer,
  countBucket,
  type DatasetChanged,
  type DatasetCopied,
  type DatasetParsed,
  type DatasetProfile,
  type Eligibility,
  type FeedbackReaction,
  isTranscribed,
  type LanguageSource,
  type LongSuggestion,
  MAX_DATASET_BYTES,
  MAX_FEEDBACK_CHARS,
  MAX_MESSAGE_CHARS,
  type OutcomeAction,
  PAGE_ARTIFACT,
  parseAgentEvent,
  type PipelineStep,
  type PlotLanguage,
  type PlotResult,
  PNG_ARTIFACT,
  plotLanguage as readPlotLanguage,
  renderedThemes,
  type RoleSpec,
  type Round,
  sizeBucket,
  type Theme,
  type TurnAction,
  type TurnBody,
  utf8Bytes,
} from 'src/lib/agent';
import { readSseEvents } from 'src/lib/sse';
import { downloadBlob } from 'src/sections/agent-chat/files';
import {
  CONFIRM_LOST_TEXT,
  LANGUAGE_DETECTED_TEXT,
  LANGUAGE_PASTED_TEXT,
} from 'src/sections/agent-chat/messages';
import { reloadOnceForAccess } from 'src/utils/adminAuth';

/** How long Stop waits for the server's `done` before it lets go of the stream. */
export const STOP_GRACE_MS = 30_000;

// ============================================================================
// State
// ============================================================================

export type SessionPhase = 'opening' | 'ready' | 'unauthorized' | 'ineligible' | 'error';

export interface Failure {
  code: string;
  ref: string | null;
  /** The binding check's lines of a refused binding set. */
  errors?: string[];
  /** What a refused paste fails on, in the server's words (`AgentApiError.cause`). */
  cause?: string;
}

export type TimelineStep = 'queued' | PipelineStep;

export interface RunState {
  kind: TurnAction | 'message';
  /** Steps in arrival order; the last one is in progress. */
  steps: { step: TimelineStep; attempt: number | null }[];
  /** Set while the turn waits in the run queue: `position` 1 runs next. */
  queue: { position: number; waiting: number } | null;
  stopping: boolean;
  /** The rounds that ended so far, from each repair step's `outcome` (absent: none yet). */
  rounds?: Round[];
}

export type ThemeImage =
  | { state: 'loading' }
  | { state: 'ready'; url: string; blob: Blob; status: 'ok' | 'needs_attention' }
  | { state: 'failed'; code: string; ref: string | null };

export type CodeText =
  { state: 'loading' } | { state: 'ready'; text: string } | { state: 'failed' };

/** What the user sends with the feedback control of a result card. */
export interface FeedbackInput {
  reaction: FeedbackReaction;
  /** Optional; stripped, and at most `MAX_FEEDBACK_CHARS` after the strip. */
  message: string;
  /** Store the version's `data.csv` with the case. */
  includeData: boolean;
}

/** A feedback case stored for a version: what was sent, and the case id the BFF gave it. */
export interface FeedbackRecord {
  reaction: FeedbackReaction;
  message: string | null;
  includeData: boolean;
  caseId: string;
}

export interface PlotVersion {
  /** The agents service's version number (1-based within the session). */
  number: number;
  library: string;
  result: PlotResult;
  /** The theme the run rendered; the other one renders on demand. */
  theme: Theme;
  images: Partial<Record<Theme, ThemeImage>>;
  code: CodeText;
  /** The last feedback case stored for this version; absent until one is sent. */
  feedback?: FeedbackRecord;
}

export type ChatItem =
  | { id: number; kind: 'user'; text: string }
  | { id: number; kind: 'action'; action: TurnAction; library: string }
  | { id: number; kind: 'assistant'; text: string }
  | { id: number; kind: 'refusal'; code: string; text: string }
  | { id: number; kind: 'error'; code: string; ref: string | null }
  | { id: number; kind: 'plot'; version: number }
  | { id: number; kind: 'plot_failed'; result: PlotResult }
  /** A line from the page itself; `warning` marks a lost confirmation. */
  | { id: number; kind: 'notice'; text: string; tone?: 'warning' };

/** Distributes `Omit` over the union, so each member keeps its own fields. */
type WithoutId<T> = T extends unknown ? Omit<T, 'id'> : never;
type NewChatItem = WithoutId<ChatItem>;

export interface DatasetState {
  /** The current version of the data, as the server stored it. */
  parsed: DatasetParsed;
  /** UTF-8 size of the pasted text, for the analytics bucket; a later version keeps it. */
  bytes: number;
  /**
   * The paste this version was parsed from, the text and the file's name, for
   * the table picker, which parses the same text again for another table; only
   * a stored paste carries it, so a failed parse never replaces it.
   */
  paste?: { text: string; source?: string };
  /**
   * The upload this version was stored from, exactly as it was posted. The admin
   * fan-out has the server copy the confirmed version into each library's
   * session (`copyData`); only against a server without that copy does it
   * post this upload again (`replayData`). Only the parse's own version carries
   * it: data the assistant changed or computed, and an undo, have none.
   */
  upload?: DatasetUpload;
}

/** A `POST .../dataset` body as the page sent it: the text, and how the server should read it. */
export interface DatasetUpload {
  text: string;
  /** A confirmed transcription: the server keeps every row and skips its free-text fallback. */
  confirmed: boolean;
  source?: string;
  table?: number;
}

/**
 * The data panel's `# changed` block: the assistant's last change to the data
 * (its change lines), or the undo that restored an earlier version. A new
 * parse clears it; the next change or undo replaces it.
 */
export type DataChange =
  { kind: 'changed'; changes: string[]; version: number } | { kind: 'undone'; version: number };

/** A table the server read from free text; nothing is stored until the user confirms it. */
export interface TranscriptionState {
  /** The canonical CSV the confirmation posts. */
  text: string;
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  warnings: string[];
  /** The model's remark on anything ambiguous; empty when it had none. */
  note: string;
  /** UTF-8 size of the pasted text it was read from, for the analytics bucket. */
  bytes: number;
  /**
   * The name of the file the text was read from, if it was: `.use()` sends it
   * with the table, also after the box was cleared or edited meanwhile.
   */
  source?: string;
}

/** Binding name (`x`, `y1`) to column; only bound names are present. */
export type BindingMap = Record<string, string>;

/**
 * What dropped a confirmation the user had given: a binding change (the
 * dropdowns, or the root's `set_bindings` reported by a turn), new data (a
 * paste, a data change of the assistant, an undo), or the server's word alone
 * (`data_unconfirmed`, or a turn's sync without a binding change).
 */
export type ConfirmLoss = 'bindings' | 'data' | 'server';

/** What the dataset route refused pasted text as, so the chat takes it instead: `422 formula` or `422 code`. */
export type FormulaKind = 'formula' | 'code';

export interface AgentSessionState {
  phase: SessionPhase;
  failure: Failure | null;
  sessionId: string | null;
  library: string;
  eligibility: Eligibility | null;
  dataset: DatasetState | null;
  parsing: boolean;
  datasetError: Failure | null;
  /**
   * Text the dataset route refused as a formula (`422 formula`) or as code
   * (`422 code`): nothing was stored, and the panel offers to send it to the
   * chat, where the assistant computes the table (`generate_data`) or runs the
   * code (`run_data_code`). The next parse, the send or a new data version clears it.
   */
  formula: string | null;
  /** What `formula` was refused as: a formula, or code that generates data. */
  formulaKind: FormulaKind;
  /** A table read from free text that awaits `.use()` or `.discard()`. */
  transcription: TranscriptionState | null;
  /** The spec's roles, in spec order; the data panel shows a column choice for each. */
  roles: RoleSpec[];
  bindings: BindingMap;
  bindingsComplete: boolean;
  /** Required roles without a column; a variadic family by its name. */
  missingRoles: string[];
  bindingsBusy: boolean;
  bindingsError: Failure | null;
  /**
   * Step 1 is done: the user confirmed that the stored dataset and its bindings
   * fit. A stored parse, a transcription and an applied binding change clear it.
   */
  dataConfirmed: boolean;
  /**
   * Why a confirmation the user had given dropped; `null` until one did, and
   * again once the data is confirmed. Set only on the step from confirmed to
   * not confirmed, never for data that was not confirmed yet.
   */
  confirmLoss: ConfirmLoss | null;
  /** The confirmation call is in flight. */
  confirmBusy: boolean;
  confirmError: Failure | null;
  /** The last change to the stored data, or the undo of one; `null` after a parse. */
  dataChange: DataChange | null;
  /** The undo call is in flight. */
  undoBusy: boolean;
  undoError: Failure | null;
  /** The `.to_long()` call is in flight. */
  toLongBusy: boolean;
  toLongError: Failure | null;
  libraryBusy: boolean;
  /** A theme toggle render is in flight. */
  themeBusy: boolean;
  /**
   * A JavaScript version's `plot.html` is being built: the server holds the
   * session's run entry for it, as for a theme render.
   */
  pageBusy: boolean;
  /** The session language and how it was set; the header's chip shows it. */
  plotLanguage: PlotLanguage;
  /** The chip's language call is in flight. */
  languageBusy: boolean;
  items: ChatItem[];
  /** The id the next thread item gets; the reducer numbers the items. */
  nextItemId: number;
  versions: Record<number, PlotVersion>;
  /** The last feedback case stored on the chat itself (version 0), for a session without a plot. */
  chatFeedback: FeedbackRecord | null;
  run: RunState | null;
}

type Action =
  | { type: 'opened'; sessionId: string; eligibility: Eligibility }
  | { type: 'open_failed'; phase: SessionPhase; failure: Failure | null }
  | { type: 'unauthorized' }
  | { type: 'parse_start' }
  | {
      type: 'parse_done';
      parsed: DatasetParsed;
      bytes: number;
      paste?: { text: string; source?: string };
      upload?: DatasetUpload;
    }
  /** `formula` is the refused text of a `422 formula` or `422 code`, which is no error to show. */
  | { type: 'parse_failed'; failure: Failure; formula?: string; formulaKind?: FormulaKind }
  /** The refused formula went to the chat as a turn. */
  | { type: 'formula_sent' }
  | { type: 'transcribed'; transcription: TranscriptionState }
  | { type: 'transcription_clear' }
  | { type: 'bindings_start'; bindings: BindingMap }
  | { type: 'bindings_done'; bindings: BindingMap; complete: boolean; missingRoles: string[] }
  | { type: 'bindings_failed'; bindings: BindingMap; failure: Failure }
  | { type: 'confirm_start' }
  | { type: 'confirm_done' }
  | { type: 'confirm_failed'; failure: Failure }
  /** The server answered `not_ready` with `data_unconfirmed`: its confirmation is gone. */
  | { type: 'confirm_lost' }
  /** A turn's `done` named the session's bindings and step state; `null` fields were absent. */
  | { type: 'server_sync'; bindings: BindingMap | null; dataConfirmed: boolean | null }
  /** A turn's `done` carried the data version the assistant's `prepare_data` made. */
  | { type: 'data_prepared'; dataset: DatasetChanged }
  /** The admin fan-out's copy stored another session's confirmed data here, bound and confirmed. */
  | { type: 'data_copied'; dataset: DatasetCopied }
  | { type: 'to_long_start' }
  | { type: 'to_long_failed'; failure: Failure }
  | { type: 'undo_start' }
  | { type: 'undo_done'; parsed: DatasetParsed }
  | { type: 'undo_failed'; failure: Failure }
  | { type: 'library_start' }
  | { type: 'library_done'; library: string; eligibility: Eligibility }
  | { type: 'library_failed'; failure: Failure }
  | { type: 'theme_busy'; busy: boolean }
  | { type: 'page_busy'; busy: boolean }
  | { type: 'language_start' }
  /** The language route's answer: the stored form, source `chosen`. */
  | { type: 'language_done'; plotLanguage: PlotLanguage }
  | { type: 'language_failed' }
  /**
   * A turn's `done` named the session language, and with data the `.to_long()`
   * offer the server computed in it: the offer applies only with that language.
   */
  | { type: 'language_sync'; plotLanguage: PlotLanguage; suggestion?: LongSuggestion | null }
  /**
   * The `.to_long()` offer as the server recomputed it in the session language
   * (a turn's `done`, the language route's answer): the card names what the
   * route applies, also after the language changed (live round 9).
   */
  | { type: 'suggestion_sync'; suggestion: LongSuggestion | null }
  /** Append a thread item; the reducer gives it the next id. */
  | { type: 'item'; item: NewChatItem }
  | { type: 'run_start'; kind: RunState['kind'] }
  | { type: 'run_queued'; position: number; waiting: number }
  | { type: 'run_step'; step: PipelineStep; attempt: number | null; previous?: Round | null }
  | { type: 'run_stopping' }
  | { type: 'run_end' }
  | { type: 'version_add'; version: PlotVersion }
  | { type: 'version_image'; number: number; theme: Theme; image: ThemeImage }
  | { type: 'version_code'; number: number; code: CodeText }
  /** A feedback case was stored for the version; a later one replaces the record. */
  | { type: 'version_feedback'; number: number; feedback: FeedbackRecord };

export function initialAgentState(library: string): AgentSessionState {
  return {
    phase: 'opening',
    failure: null,
    sessionId: null,
    library,
    eligibility: null,
    dataset: null,
    parsing: false,
    datasetError: null,
    formula: null,
    formulaKind: 'formula',
    transcription: null,
    roles: [],
    bindings: {},
    bindingsComplete: false,
    missingRoles: [],
    bindingsBusy: false,
    bindingsError: null,
    dataConfirmed: false,
    confirmLoss: null,
    confirmBusy: false,
    confirmError: null,
    dataChange: null,
    undoBusy: false,
    undoError: null,
    toLongBusy: false,
    toLongError: null,
    libraryBusy: false,
    themeBusy: false,
    pageBusy: false,
    // The server's default too, whatever the browser's locale: no answer needed to start.
    plotLanguage: { language: 'en', source: 'default' },
    languageBusy: false,
    items: [],
    nextItemId: 1,
    versions: {},
    chatFeedback: null,
    run: null,
  };
}

// ============================================================================
// Roles and bindings
// ============================================================================

/** A role the server named but did not describe (an older server, or a missing role). */
function bareRole(name: string, required: boolean): RoleSpec {
  return { name, kinds: [], required, variadic: false, description: '' };
}

/**
 * The variadic family a binding name belongs to (`y3` → `y`), as the agents
 * service resolves it: an exact single role wins, then the family with the
 * longest name whose `<name><digits>` matches.
 */
export function familyOf(name: string, roles: readonly RoleSpec[]): RoleSpec | null {
  if (roles.some(role => !role.variadic && role.name === name)) return null;
  let best: RoleSpec | null = null;
  for (const role of roles) {
    if (!role.variadic || !name.startsWith(role.name)) continue;
    if (!/^\d+$/.test(name.slice(role.name.length))) continue;
    if (!best || role.name.length > best.name.length) best = role;
  }
  return best;
}

/** A family's bound members in member order: `[[y1, col], [y2, col], ...]`. */
export function familyMembers(
  bindings: BindingMap,
  family: RoleSpec,
  roles: readonly RoleSpec[]
): [string, string][] {
  return Object.entries(bindings)
    .filter(([name]) => familyOf(name, roles)?.name === family.name)
    .sort(([a], [b]) => Number(a.slice(family.name.length)) - Number(b.slice(family.name.length)));
}

/**
 * The binding name of a family's `n`-th member (1-based). A name a single role
 * of the spec owns (a family `y` next to a role `y2`) is skipped, because the
 * server would read it as that role.
 */
export function nthMember(family: RoleSpec, n: number, roles: readonly RoleSpec[]): string {
  const singles = new Set(roles.filter(role => !role.variadic).map(role => role.name));
  let index = 0;
  let name = family.name;
  for (let found = 0; found < n;) {
    index += 1;
    name = `${family.name}${index}`;
    if (!singles.has(name)) found += 1;
  }
  return name;
}

/** Renumber every family's bound members in their order, so the members stay contiguous. */
export function compactFamilies(
  bindings: Record<string, string | null>,
  roles: readonly RoleSpec[]
): BindingMap {
  const bound: BindingMap = {};
  for (const [name, column] of Object.entries(bindings)) if (column) bound[name] = column;
  const result: BindingMap = {};
  for (const [name, column] of Object.entries(bound)) {
    if (!familyOf(name, roles)) result[name] = column;
  }
  for (const family of roles.filter(role => role.variadic)) {
    familyMembers(bound, family, roles).forEach(([, column], index) => {
      result[nthMember(family, index + 1, roles)] = column;
    });
  }
  return result;
}

/**
 * Required roles without a column, a variadic family by its name, as the
 * binding check reports them in `missing_roles`.
 */
export function missingRolesOf(bindings: BindingMap, roles: readonly RoleSpec[]): string[] {
  return roles
    .filter(role => role.required)
    .filter(role =>
      role.variadic ? familyMembers(bindings, role, roles).length === 0 : !bindings[role.name]
    )
    .map(role => role.name);
}

function toMap(bindings: readonly Binding[]): BindingMap {
  const map: BindingMap = {};
  for (const binding of bindings) if (binding.column) map[binding.role] = binding.column;
  return map;
}

/** The data's version number; an answer without one (an older server) is the paste's 1. */
function versionOf(value: unknown): number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 1 ? value : 1;
}

/**
 * Replace the stored data with another version of it: one the assistant made
 * (`done.dataset`) or the one an undo restored. The server carried the bindings
 * over and dropped its confirmation, so the dropdowns take its bindings and the
 * panel goes back to step 1. Completeness is read from the roles here, as for a
 * turn's binding sync, because no binding call answers it.
 *
 * A version the assistant generated from a formula can be the session's first
 * data: there is no stored dataset to keep the pasted size of (0 stands in),
 * and the roles come with the version; from a server that names none, the
 * bindings stand in for them, as for a paste.
 *
 * A confirmation lost earlier (a binding change, say) is now lost to the data:
 * the card's step line names the change it shows. Data that was never
 * confirmed has no loss to name.
 */
function withDataVersion(
  state: AgentSessionState,
  parsed: DatasetParsed,
  dataChange: DataChange
): AgentSessionState {
  const roles =
    parsed.roles ??
    (state.roles.length > 0
      ? state.roles
      : parsed.bindings.map(binding => bareRole(binding.role, false)));
  const bindings = toMap(parsed.bindings);
  const missing = missingRolesOf(bindings, roles);
  return {
    ...state,
    dataset: {
      parsed: { ...parsed, roles, version: versionOf(parsed.version) },
      bytes: state.dataset?.bytes ?? 0,
      // The paste stays with every version made from it (Fable review of #12200); the picker itself shows only
      // beside an answer that names `tables`, which only the paste route gives.
      ...(state.dataset?.paste ? { paste: state.dataset.paste } : {}),
    },
    roles,
    bindings,
    bindingsComplete: missing.length === 0,
    missingRoles: missing,
    bindingsError: null,
    dataConfirmed: false,
    confirmError: null,
    confirmLoss: state.confirmLoss === null ? null : 'data',
    dataChange,
    undoBusy: false,
    undoError: null,
    toLongBusy: false,
    toLongError: null,
  };
}

// ============================================================================
// Reducer
// ============================================================================

function patchVersion(
  state: AgentSessionState,
  number: number,
  patch: (version: PlotVersion) => PlotVersion
): AgentSessionState {
  const version = state.versions[number];
  if (!version) return state;
  return { ...state, versions: { ...state.versions, [number]: patch(version) } };
}

/** Append a thread item under the next id. */
function appendItem(state: AgentSessionState, item: NewChatItem): AgentSessionState {
  return {
    ...state,
    items: [...state.items, { ...item, id: state.nextItemId } as ChatItem],
    nextItemId: state.nextItemId + 1,
  };
}

/** The ladder of the language sources: the server only ever climbs it within a session. */
const SOURCE_RANK: Record<LanguageSource, number> = {
  default: 0,
  pasted: 1,
  detected: 2,
  chosen: 3,
};

function sameBindings(a: BindingMap, b: BindingMap): boolean {
  const names = Object.keys(a);
  return names.length === Object.keys(b).length && names.every(name => a[name] === b[name]);
}

/** What dropped the confirmation, from the action that dropped it. */
function lossOf(state: AgentSessionState, action: Action): ConfirmLoss {
  switch (action.type) {
    case 'bindings_done':
      return 'bindings';
    case 'parse_done':
    case 'data_prepared':
    case 'undo_done':
      return 'data';
    case 'server_sync':
      // The root's `set_bindings`, reported by the turn's `done`, is a binding change.
      return action.bindings && state.dataset && !sameBindings(action.bindings, state.bindings)
        ? 'bindings'
        : 'server';
    default:
      return 'server';
  }
}

/**
 * Every action, plus one rule on top: when a confirmation the user had given
 * drops, whatever action dropped it, the reducer keeps the reason and appends
 * a warning notice to the thread, where the loss happened. A confirmation
 * clears the reason. A first binding setup after a paste lands while the flag
 * is already clear, so it says nothing. While the flag stays clear the reason
 * follows the data (`reduce`): a new paste clears it, a data change or an undo
 * makes it `data`, with no second notice.
 */
export function agentReducer(state: AgentSessionState, action: Action): AgentSessionState {
  const next = reduce(state, action);
  if (state.dataConfirmed && !next.dataConfirmed) {
    const reason = lossOf(state, action);
    return appendItem(
      { ...next, confirmLoss: reason },
      { kind: 'notice', tone: 'warning', text: CONFIRM_LOST_TEXT[reason] }
    );
  }
  if (!state.dataConfirmed && next.dataConfirmed) return { ...next, confirmLoss: null };
  return next;
}

function reduce(state: AgentSessionState, action: Action): AgentSessionState {
  switch (action.type) {
    case 'opened':
      return {
        ...state,
        phase: 'ready',
        sessionId: action.sessionId,
        eligibility: action.eligibility,
      };
    case 'open_failed':
      return {
        ...state,
        phase: action.phase,
        failure: action.failure,
        run: null,
        transcription: null,
      };
    case 'unauthorized':
      return { ...state, phase: 'unauthorized', run: null, transcription: null };
    case 'parse_start':
      // A new parse (a confirmed transcription is one) replaces a pending transcription,
      // and a `.to_long()` that failed on the data before it is not the new data's error.
      return {
        ...state,
        parsing: true,
        datasetError: null,
        formula: null,
        transcription: null,
        toLongError: null,
      };
    case 'parse_done':
      return {
        ...state,
        parsing: false,
        // A paste starts over at version 1: the server dropped the undo history with it.
        dataset: {
          parsed: { ...action.parsed, version: versionOf(action.parsed.version) },
          bytes: action.bytes,
          ...(action.paste ? { paste: action.paste } : {}),
          ...(action.upload ? { upload: action.upload } : {}),
        },
        dataChange: null,
        undoError: null,
        // An older server names no roles: the default bindings stand in for them.
        roles:
          action.parsed.roles ??
          action.parsed.bindings.map(binding => bareRole(binding.role, false)),
        bindings: toMap(action.parsed.bindings),
        bindingsComplete: false,
        missingRoles: [],
        bindingsError: null,
        // A new dataset is unchecked: the server dropped its confirmation when it stored it.
        dataConfirmed: false,
        confirmError: null,
        // And it starts over: a loss named for the data before it is not its own. A paste
        // that drops a confirmation the user had given is named by `agentReducer`.
        confirmLoss: null,
      };
    case 'parse_failed':
      // A formula or code is no failure of the data: the panel offers the chat instead.
      return {
        ...state,
        parsing: false,
        datasetError: action.formula === undefined ? action.failure : null,
        formula: action.formula ?? null,
        formulaKind: action.formulaKind ?? 'formula',
        transcription: null,
      };
    case 'formula_sent':
      return { ...state, formula: null };
    case 'transcribed':
      // Nothing is stored yet: the dataset, its bindings and their confirmation stay until
      // the user decides (the server kept them too); the page holds step 1 while the
      // transcription waits (`inStep2`), and `.discard()` returns to where the user was.
      return {
        ...state,
        parsing: false,
        transcription: action.transcription,
      };
    case 'transcription_clear':
      return { ...state, transcription: null };
    case 'bindings_start':
      return { ...state, bindingsBusy: true, bindingsError: null, bindings: action.bindings };
    case 'bindings_done': {
      const known = new Set(state.roles.map(role => role.name));
      const missing = action.missingRoles.filter(name => !known.has(name));
      return {
        ...state,
        bindingsBusy: false,
        roles: [...state.roles, ...missing.map(name => bareRole(name, true))],
        bindings: action.bindings,
        bindingsComplete: action.complete,
        missingRoles: action.missingRoles,
        // An applied change replaces the set the user confirmed, and the server
        // drops its confirmation with it. The parse's own default PUT lands while
        // the flag is already false, so it never looks like a change.
        dataConfirmed: false,
        confirmError: null,
      };
    }
    case 'bindings_failed':
      return {
        ...state,
        bindingsBusy: false,
        bindings: action.bindings,
        bindingsError: action.failure,
      };
    case 'confirm_start':
      return { ...state, confirmBusy: true, confirmError: null };
    case 'confirm_done':
      return { ...state, confirmBusy: false, dataConfirmed: true };
    case 'confirm_failed':
      return { ...state, confirmBusy: false, confirmError: action.failure };
    case 'confirm_lost':
      return { ...state, dataConfirmed: false };
    case 'server_sync': {
      let next = state;
      // The dropdowns show what the server holds; without a stored dataset there is nothing to bind.
      if (action.bindings && state.dataset) {
        const missing = missingRolesOf(action.bindings, state.roles);
        next = {
          ...next,
          bindings: action.bindings,
          bindingsComplete: missing.length === 0,
          missingRoles: missing,
        };
      }
      if (action.dataConfirmed !== null) next = { ...next, dataConfirmed: action.dataConfirmed };
      return next;
    }
    case 'data_prepared': {
      const { changes, version, ...parsed } = action.dataset;
      // A formula refused in the data box is answered once the chat computed data.
      return withDataVersion(
        { ...state, formula: null },
        { ...parsed, version },
        { kind: 'changed', changes, version: versionOf(version) }
      );
    }
    case 'data_copied': {
      const { dataset } = action;
      return {
        ...state,
        parsing: false,
        // The copy is this session's version 1; no paste was made here, so there is no size to bucket.
        dataset: { parsed: { ...dataset, version: versionOf(dataset.version) }, bytes: 0 },
        dataChange: null,
        undoError: null,
        roles: dataset.roles ?? dataset.bindings.map(binding => bareRole(binding.role, false)),
        bindings: toMap(dataset.bindings),
        bindingsComplete: dataset.complete,
        missingRoles: dataset.missing_roles,
        bindingsError: null,
        // The server confirmed the copy with the bindings the page session confirmed.
        dataConfirmed: true,
        confirmError: null,
      };
    }
    case 'to_long_start':
      return { ...state, toLongBusy: true, toLongError: null };
    case 'to_long_failed':
      return { ...state, toLongBusy: false, toLongError: action.failure };
    case 'undo_start':
      return { ...state, undoBusy: true, undoError: null };
    case 'undo_done':
      return withDataVersion(state, action.parsed, {
        kind: 'undone',
        version: versionOf(action.parsed.version),
      });
    case 'undo_failed':
      return { ...state, undoBusy: false, undoError: action.failure };
    case 'library_start':
      return { ...state, libraryBusy: true };
    case 'library_done':
      // The dataset, its bindings and their confirmation stay, as on the server.
      return {
        ...state,
        libraryBusy: false,
        library: action.library,
        eligibility: action.eligibility,
        transcription: null,
      };
    case 'library_failed':
      return { ...state, libraryBusy: false };
    case 'theme_busy':
      return { ...state, themeBusy: action.busy };
    case 'page_busy':
      return { ...state, pageBusy: action.busy };
    case 'language_start':
      return { ...state, languageBusy: true };
    case 'language_done':
      return { ...state, languageBusy: false, plotLanguage: action.plotLanguage };
    case 'language_failed':
      return { ...state, languageBusy: false };
    case 'language_sync': {
      // A `done` never moves the chip down the ladder (the server never does either): a
      // choice that landed from another tab between the server's finish and this page's
      // `run_end` keeps `chosen`. A `chosen` over `chosen` (the assistant's `set_language`
      // during the turn) applies.
      if (SOURCE_RANK[action.plotLanguage.source] < SOURCE_RANK[state.plotLanguage.source]) {
        return state;
      }
      const synced =
        action.suggestion !== undefined
          ? reduce(state, { type: 'suggestion_sync', suggestion: action.suggestion })
          : state;
      const next = { ...synced, plotLanguage: action.plotLanguage };
      const before = state.plotLanguage;
      const after = action.plotLanguage;
      // The first typed message or a paste set it: one quiet line names the chip that changes it.
      if (after.source === 'detected' && SOURCE_RANK[before.source] < SOURCE_RANK.detected) {
        return appendItem(next, { kind: 'notice', text: LANGUAGE_DETECTED_TEXT(after.language) });
      }
      if (
        after.source === 'pasted' &&
        (before.source === 'default' || before.language !== after.language)
      ) {
        return appendItem(next, { kind: 'notice', text: LANGUAGE_PASTED_TEXT(after.language) });
      }
      return next;
    }
    case 'suggestion_sync':
      return state.dataset
        ? {
            ...state,
            dataset: {
              ...state.dataset,
              parsed: { ...state.dataset.parsed, suggestion: action.suggestion },
            },
          }
        : state;
    case 'item':
      return appendItem(state, action.item);
    case 'run_start':
      return { ...state, run: { kind: action.kind, steps: [], queue: null, stopping: false } };
    case 'run_queued': {
      if (!state.run) return state;
      const steps = state.run.steps;
      const last = steps[steps.length - 1];
      return {
        ...state,
        run: {
          ...state.run,
          steps: last?.step === 'queued' ? steps : [...steps, { step: 'queued', attempt: null }],
          queue: { position: action.position, waiting: action.waiting },
        },
      };
    }
    case 'run_step':
      if (!state.run) return state;
      return {
        ...state,
        run: {
          ...state.run,
          queue: null,
          steps: [...state.run.steps, { step: action.step, attempt: action.attempt }],
          rounds: action.previous
            ? [...(state.run.rounds ?? []), action.previous]
            : state.run.rounds,
        },
      };
    case 'run_stopping':
      return state.run ? { ...state, run: { ...state.run, stopping: true } } : state;
    case 'run_end':
      return { ...state, run: null };
    case 'version_add':
      return {
        ...state,
        versions: { ...state.versions, [action.version.number]: action.version },
      };
    case 'version_image':
      return patchVersion(state, action.number, version => ({
        ...version,
        images: { ...version.images, [action.theme]: action.image },
      }));
    case 'version_code':
      return patchVersion(state, action.number, version => ({ ...version, code: action.code }));
    case 'version_feedback':
      // Version 0 is the chat itself: its record lives on the session, not on a version.
      if (action.number === 0) return { ...state, chatFeedback: action.feedback };
      return patchVersion(state, action.number, version => ({
        ...version,
        feedback: action.feedback,
      }));
    default:
      return state;
  }
}

// ============================================================================
// Hook
// ============================================================================

export interface UseAgentSessionOptions {
  specId: string;
  library: string;
  locale: string;
  token: string;
  /** The session is one of the admin fan-out's (`FanOut`): its telemetry is filed as `fanout`, not `live`. */
  fanout?: boolean;
}

const GUARDRAIL_REASONS = new Set([
  'out_of_scope',
  'needs_data',
  'budget',
  'unsupported_content',
  // The per-user message limits and a session closed after repeated scope refusals.
  'rate_limited',
  'daily_limit',
  'session_closed',
  // This plot in another library or language (a pointer to the catalogue), and
  // a user paused for the day after repeated attack verdicts.
  'other_library',
  'locked_out',
]);

/** The paste route's guard refusals (HTTP errors, not stream refusals) that count as guardrail blocks. */
const PASTE_GUARDRAIL_REASONS = new Set([
  'data_refused',
  'rate_limited',
  'daily_limit',
  'locked_out',
  'session_closed',
]);

function failureOf(err: unknown): Failure {
  if (err instanceof AgentApiError) {
    return {
      code: err.code,
      ref: err.ref,
      ...(err.errors.length ? { errors: err.errors } : {}),
      ...(err.cause ? { cause: err.cause } : {}),
    };
  }
  return { code: 'network', ref: null };
}

const isAbort = (err: unknown) => err instanceof DOMException && err.name === 'AbortError';

export function useAgentSession({
  specId,
  library,
  locale,
  token,
  fanout = false,
}: UseAgentSessionOptions) {
  const [state, dispatch] = useReducer(agentReducer, library, initialAgentState);
  const { trackEvent } = useAnalytics();

  // Values async callbacks read after an await; refs, so a stale closure never
  // acts on a previous session.
  const stateRef = useRef(state);
  stateRef.current = state;
  const abortRef = useRef<AbortController | null>(null);
  const stoppedRef = useRef(false);
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Set synchronously, before the state catches up, so a double click starts nothing twice.
  const themeRef = useRef(false);
  const pageRef = useRef(false);
  const parseRef = useRef(false);
  const confirmRef = useRef(false);
  const undoRef = useRef(false);
  // The parse's own binding call ends right before its summary turn starts,
  // sooner than the state can say so.
  const bindingsRef = useRef(false);
  const saveRef = useRef(false);
  const languageRef = useRef(false);
  // The feedback send in flight per version: a second `.send()` for it joins the first.
  const feedbackRef = useRef<Map<number, Promise<void>>>(new Map());
  const versionCounter = useRef(0);
  const blobUrls = useRef<Set<string>>(new Set());
  const mounted = useRef(true);

  const safeDispatch = useCallback((action: Action) => {
    if (mounted.current) dispatch(action);
  }, []);

  /** Append a thread item; the reducer numbers it. */
  const addItem = useCallback(
    (item: NewChatItem) => safeDispatch({ type: 'item', item }),
    [safeDispatch]
  );

  const handleFailure = useCallback(
    (err: unknown): Failure => {
      if (err instanceof AgentApiError && err.unauthorized) safeDispatch({ type: 'unauthorized' });
      return failureOf(err);
    },
    [safeDispatch]
  );

  /**
   * Whether a turn, a theme render, a page build, a parse, a binding change, a
   * confirmation, an undo, a library switch or a language choice is in flight.
   */
  const busy = useCallback(
    () =>
      !!abortRef.current ||
      themeRef.current ||
      pageRef.current ||
      parseRef.current ||
      confirmRef.current ||
      undoRef.current ||
      bindingsRef.current ||
      languageRef.current ||
      stateRef.current.libraryBusy,
    []
  );

  // Open the session for the page's spec; the library is the URL's at mount
  // time, later switches go through `switchLibrary`. The page remounts this
  // hook (a `key`) for another spec or token, so the state starts fresh.
  const initialLibrary = useRef(library);
  const openedForFanOut = useRef(fanout);
  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    let opened: string | null = null;
    let purged = false;
    const urls = blobUrls.current;

    /** Delete the server session once: its dataset and renders go with it. */
    const purge = (keepalive: boolean) => {
      if (!opened || purged) return;
      purged = true;
      void agentApi.deleteSession(token, opened, { keepalive }).catch(() => undefined);
    };
    // A reload or a closed tab runs no effect cleanup; `pagehide` does fire.
    const onPageHide = () => purge(true);
    // Back from the back-forward cache, the page holds a session that is gone.
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted && purged) {
        safeDispatch({
          type: 'open_failed',
          phase: 'error',
          failure: { code: 'session_expired', ref: null },
        });
      }
    };
    window.addEventListener('pagehide', onPageHide);
    window.addEventListener('pageshow', onPageShow);

    agentApi
      .openSession(token, specId, initialLibrary.current, locale, openedForFanOut.current)
      .then(result => {
        if (cancelled) {
          void agentApi.deleteSession(token, result.session_id).catch(() => undefined);
          return;
        }
        opened = result.session_id;
        safeDispatch({
          type: 'opened',
          sessionId: result.session_id,
          eligibility: result.eligibility,
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const failure = failureOf(err);
        if (err instanceof AgentApiError && err.unauthorized) {
          safeDispatch({ type: 'unauthorized' });
        } else if (failure.code === 'not_eligible') {
          safeDispatch({ type: 'open_failed', phase: 'ineligible', failure });
        } else if (failure.code === 'unreachable' && reloadOnceForAccess()) {
          // An expired Access session: the reload lets Access sign the admin in.
        } else {
          safeDispatch({ type: 'open_failed', phase: 'error', failure });
        }
      });
    return () => {
      cancelled = true;
      mounted.current = false;
      window.removeEventListener('pagehide', onPageHide);
      window.removeEventListener('pageshow', onPageShow);
      if (stopTimer.current) clearTimeout(stopTimer.current);
      abortRef.current?.abort();
      purge(false);
      for (const url of urls) URL.revokeObjectURL(url);
      urls.clear();
    };
  }, [specId, locale, token, safeDispatch]);

  // ---------------------------------------------------------------- dataset

  const applyBindings = useCallback(
    async (next: BindingMap, previous: BindingMap) => {
      const sid = stateRef.current.sessionId;
      if (!sid) return;
      bindingsRef.current = true;
      safeDispatch({ type: 'bindings_start', bindings: next });
      const payload: Binding[] = Object.entries(next).map(([role, column]) => ({ role, column }));
      try {
        const applied = await agentApi.putBindings(token, sid, payload);
        safeDispatch({
          type: 'bindings_done',
          bindings: toMap(applied.bindings),
          complete: applied.complete,
          missingRoles: applied.missing_roles,
        });
      } catch (err) {
        safeDispatch({ type: 'bindings_failed', bindings: previous, failure: handleFailure(err) });
      } finally {
        bindingsRef.current = false;
      }
    },
    [token, safeDispatch, handleFailure]
  );

  /** `.discard()`: drop the transcribed table; nothing was stored, so the server is not asked. */
  const discardTranscription = useCallback(() => {
    const transcription = stateRef.current.transcription;
    if (!transcription) return;
    safeDispatch({ type: 'transcription_clear' });
    trackEvent('agent_data_parsed', {
      status: 'discarded',
      size_bucket: sizeBucket(transcription.bytes),
    });
  }, [safeDispatch, trackEvent]);

  /** Bind `name` (a single role or a family member such as `y2`) to `column`, or clear it with `null`. */
  const setBinding = useCallback(
    (name: string, column: string | null) => {
      if (busy()) return;
      const { bindings: current, roles } = stateRef.current;
      const next: Record<string, string | null> = { ...current };
      // A column belongs to one role: taking it frees the role that held it.
      if (column) {
        for (const [other, held] of Object.entries(next)) {
          if (other !== name && held === column) next[other] = null;
        }
      }
      next[name] = column;
      void applyBindings(compactFamilies(next, roles), current);
    },
    [applyBindings, busy]
  );

  /**
   * `.confirm()`: the end of step 1. The server marks the stored dataset and its
   * current bindings as checked, which `.create_plot()` needs. Nothing starts
   * without a stored dataset, while a table read from text waits for its
   * decision, or while anything else is in flight.
   */
  const confirmData = useCallback(async () => {
    const current = stateRef.current;
    const sid = current.sessionId;
    const dataset = current.dataset;
    if (!sid || !dataset || current.transcription || current.run || busy()) return;
    confirmRef.current = true;
    safeDispatch({ type: 'confirm_start' });
    try {
      await agentApi.confirmDataset(token, sid);
      safeDispatch({ type: 'confirm_done' });
      trackEvent('agent_data_confirmed', { size_bucket: sizeBucket(dataset.bytes) });
    } catch (err) {
      safeDispatch({ type: 'confirm_failed', failure: handleFailure(err) });
    } finally {
      confirmRef.current = false;
    }
  }, [token, safeDispatch, handleFailure, trackEvent, busy]);

  /**
   * `.undo()`: the version before the assistant's last change to the data is
   * the current dataset again, unconfirmed (`POST .../dataset/undo`). Nothing
   * starts at the paste (version 1), after the server said there is nothing
   * left to undo, or while anything else is in flight.
   */
  const undoData = useCallback(async () => {
    const current = stateRef.current;
    const sid = current.sessionId;
    const version = current.dataset?.parsed.version ?? 1;
    if (!sid || version <= 1 || current.undoError?.code === 'nothing_to_undo') return;
    if (current.run || busy()) return;
    undoRef.current = true;
    safeDispatch({ type: 'undo_start' });
    try {
      const parsed = await agentApi.undoDataset(token, sid);
      safeDispatch({ type: 'undo_done', parsed });
      trackEvent('agent_data_undo', { version: countBucket(versionOf(parsed.version)) });
    } catch (err) {
      safeDispatch({ type: 'undo_failed', failure: handleFailure(err) });
    } finally {
      undoRef.current = false;
    }
  }, [token, safeDispatch, handleFailure, trackEvent, busy]);

  /**
   * `.to_long()`: the service applies its wide-table suggestion as the next data
   * version, without a model call; the page shows it like the assistant's data
   * change (`# changed`, `.undo()`), unconfirmed.
   */
  const toLongData = useCallback(async () => {
    const current = stateRef.current;
    const sid = current.sessionId;
    if (!sid || !current.dataset?.parsed.suggestion || current.toLongBusy) return;
    if (current.run || busy()) return;
    undoRef.current = true;
    safeDispatch({ type: 'to_long_start' });
    try {
      const dataset = await agentApi.datasetToLong(token, sid);
      safeDispatch({ type: 'data_prepared', dataset });
      trackEvent('agent_data_prepared', { changes: countBucket(dataset.changes.length) });
    } catch (err) {
      safeDispatch({ type: 'to_long_failed', failure: handleFailure(err) });
    } finally {
      undoRef.current = false;
    }
  }, [token, safeDispatch, handleFailure, trackEvent, busy]);

  /**
   * The admin fan-out (`FanOut`): the server copies the confirmed current data
   * of `fromSession`, the page's own session, into this one, whatever its origin
   * (a paste, a file, a table the assistant changed or computed), byte for byte
   * with its bindings, their confirmation and the session language
   * (`POST .../dataset/copy`). No summary turn, so a library costs one chat
   * turn, its `create_plot`, against the user's message limits, and no paste.
   * Resolves to the failure that stopped it, or `null` once the data is
   * confirmed; `not_found` is a server without the copy, on which `FanOut`
   * posts the paste again where there is one (`replayData`).
   */
  const copyData = useCallback(
    async (fromSession: string): Promise<Failure | null> => {
      const sid = stateRef.current.sessionId;
      if (!sid || busy()) return { code: 'run_active', ref: null };
      parseRef.current = true;
      safeDispatch({ type: 'parse_start' });
      try {
        const dataset = await agentApi.copyDataset(token, sid, fromSession);
        safeDispatch({ type: 'data_copied', dataset });
        const copiedLanguage = readPlotLanguage(dataset.language);
        if (copiedLanguage) safeDispatch({ type: 'language_sync', plotLanguage: copiedLanguage });
        return dataset.complete ? null : { code: 'bindings_incomplete', ref: null };
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'parse_failed', failure });
        return failure;
      } finally {
        parseRef.current = false;
      }
    },
    [token, safeDispatch, handleFailure, busy]
  );

  /**
   * The admin fan-out against a server without the copy (`copyData` answered
   * `not_found`): store another session's upload in this one, bind the columns
   * as that session had them and confirm, all without the summary turn a paste
   * asks for (`parseData`). Resolves to the failure that stopped it, or `null`
   * once the data is confirmed.
   */
  const replayData = useCallback(
    async (upload: DatasetUpload, bindings: BindingMap): Promise<Failure | null> => {
      const sid = stateRef.current.sessionId;
      if (!sid || busy()) return { code: 'run_active', ref: null };
      parseRef.current = true;
      safeDispatch({ type: 'parse_start' });
      try {
        const parsed = await agentApi.uploadDataset(
          token,
          sid,
          upload.text,
          upload.confirmed,
          upload.source,
          upload.table
        );
        // The source session stored this text as a table; reading it as free text now is a failure.
        if (isTranscribed(parsed)) {
          const failure = { code: 'unparseable', ref: null };
          safeDispatch({ type: 'parse_failed', failure });
          return failure;
        }
        safeDispatch({ type: 'parse_done', parsed, bytes: utf8Bytes(upload.text), upload });
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'parse_failed', failure });
        return failure;
      } finally {
        parseRef.current = false;
      }
      bindingsRef.current = true;
      safeDispatch({ type: 'bindings_start', bindings });
      try {
        const payload: Binding[] = Object.entries(bindings).map(([role, column]) => ({
          role,
          column,
        }));
        const applied = await agentApi.putBindings(token, sid, payload);
        safeDispatch({
          type: 'bindings_done',
          bindings: toMap(applied.bindings),
          complete: applied.complete,
          missingRoles: applied.missing_roles,
        });
        if (!applied.complete) return { code: 'bindings_incomplete', ref: null };
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'bindings_failed', bindings: {}, failure });
        return failure;
      } finally {
        bindingsRef.current = false;
      }
      confirmRef.current = true;
      safeDispatch({ type: 'confirm_start' });
      try {
        await agentApi.confirmDataset(token, sid);
        safeDispatch({ type: 'confirm_done' });
        return null;
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'confirm_failed', failure });
        return failure;
      } finally {
        confirmRef.current = false;
      }
    },
    [token, safeDispatch, handleFailure, busy]
  );

  // ---------------------------------------------------------------- versions

  const fetchArtifact = useCallback(
    async (number: number, name: ArtifactName, theme?: Theme): Promise<Blob> => {
      const sid = stateRef.current.sessionId;
      if (!sid) throw new AgentApiError(0, 'no_session');
      if (name !== PAGE_ARTIFACT) return agentApi.artifact(token, sid, name, number);
      // The server builds `plot.html` now and holds the session's run entry while it does, as
      // for a theme render: the page holds back turns, toggles and data edits meanwhile, which
      // the server would refuse with `409 run_active`, and starts no build while one of them runs.
      if (busy()) throw new AgentApiError(409, 'run_active');
      pageRef.current = true;
      safeDispatch({ type: 'page_busy', busy: true });
      try {
        return await agentApi.artifact(token, sid, name, number, theme);
      } finally {
        pageRef.current = false;
        safeDispatch({ type: 'page_busy', busy: false });
      }
    },
    [token, safeDispatch, busy]
  );

  /**
   * The usage beacon for what the user did with a result (`copied_image`,
   * `downloaded_code`, ...): the action and the version only, sent after the
   * action succeeded. Fire and forget: without a session it sends nothing, and
   * a failure never reaches the page (`agentApi.reportOutcome`).
   */
  const reportOutcome = useCallback(
    (action: Exclude<OutcomeAction, 'feedback'>, number: number): void => {
      const sid = stateRef.current.sessionId;
      if (sid) void agentApi.reportOutcome(token, sid, { action, version: number });
    },
    [token]
  );

  // A dropped binary file read on the server; the data card keeps its own state for it (nothing is stored).
  const convertFile = useCallback(
    async (dataBase64: string, sheet?: string): Promise<ConvertAnswer> => {
      const sid = stateRef.current.sessionId;
      if (!sid) throw new AgentApiError(0, 'no_session');
      return agentApi.convertFile(token, sid, dataBase64, sheet);
    },
    [token]
  );

  const loadImage = useCallback(
    async (number: number, theme: Theme, status: 'ok' | 'needs_attention') => {
      safeDispatch({ type: 'version_image', number, theme, image: { state: 'loading' } });
      try {
        const blob = await fetchArtifact(number, PNG_ARTIFACT[theme]);
        if (!mounted.current) return;
        const url = URL.createObjectURL(blob);
        blobUrls.current.add(url);
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'ready', url, blob, status },
        });
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'failed', code: failure.code, ref: failure.ref },
        });
      }
    },
    [fetchArtifact, safeDispatch, handleFailure]
  );

  const loadCode = useCallback(
    async (number: number, name: CodeArtifact = 'plot.py') => {
      safeDispatch({ type: 'version_code', number, code: { state: 'loading' } });
      try {
        const text = await (await fetchArtifact(number, name)).text();
        safeDispatch({ type: 'version_code', number, code: { state: 'ready', text } });
      } catch (err) {
        handleFailure(err);
        safeDispatch({ type: 'version_code', number, code: { state: 'failed' } });
      }
    },
    [fetchArtifact, safeDispatch, handleFailure]
  );

  /**
   * The light and dark switch: render the other theme of a version (no model
   * call), then show it. Nothing starts while a turn or another render runs,
   * which the server would refuse with `409 run_active`.
   */
  const requestTheme = useCallback(
    async (number: number, theme: Theme) => {
      const sid = stateRef.current.sessionId;
      const version = stateRef.current.versions[number];
      if (!sid || !version || busy()) return;
      const current = version.images[theme];
      if (current && current.state !== 'failed') return;
      themeRef.current = true;
      safeDispatch({ type: 'theme_busy', busy: true });
      safeDispatch({ type: 'version_image', number, theme, image: { state: 'loading' } });
      try {
        const rendered = await agentApi.renderTheme(token, sid, number, theme);
        if (rendered.status === 'failed' || !rendered.artifacts.includes(PNG_ARTIFACT[theme])) {
          safeDispatch({
            type: 'version_image',
            number,
            theme,
            image: { state: 'failed', code: rendered.reason || 'render', ref: null },
          });
          return;
        }
        await loadImage(number, theme, rendered.status);
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'failed', code: failure.code, ref: failure.ref },
        });
      } finally {
        themeRef.current = false;
        safeDispatch({ type: 'theme_busy', busy: false });
      }
    },
    [token, safeDispatch, handleFailure, loadImage, busy]
  );

  // ---------------------------------------------------------------- turns

  const onPlot = useCallback(
    (result: PlotResult) => {
      const current = stateRef.current;
      trackEvent('agent_plot_rendered', {
        library: current.library,
        status: result.status,
        repaired: result.attempts > 1 ? 'yes' : 'no',
        spec: specId,
      });
      if (result.status !== 'ok' && result.status !== 'needs_attention') {
        // The server holds no confirmation: offer `.confirm()` again instead of a
        // dead `.create_plot()`. The turn's `done` sync normally says so as well;
        // this covers a stream that ends without it.
        if (result.status === 'not_ready' && result.reason === 'data_unconfirmed') {
          safeDispatch({ type: 'confirm_lost' });
        }
        addItem({ kind: 'plot_failed', result });
        return;
      }
      // The server's number; counting is the fallback for a server without it.
      const number = result.version ?? versionCounter.current + 1;
      versionCounter.current = Math.max(versionCounter.current, number);
      const theme = renderedThemes(result.artifacts)[0] ?? 'light';
      safeDispatch({
        type: 'version_add',
        version: {
          number,
          library: current.library,
          result,
          theme,
          images: {},
          code: { state: 'loading' },
        },
      });
      addItem({ kind: 'plot', version: number });
      void loadImage(number, theme, result.status);
      void loadCode(number, codeArtifact(result.artifacts));
    },
    [specId, trackEvent, safeDispatch, addItem, loadImage, loadCode]
  );

  const onEvent = useCallback(
    (event: AgentEvent) => {
      switch (event.type) {
        case 'queued':
          safeDispatch({ type: 'run_queued', position: event.position, waiting: event.waiting });
          break;
        case 'step':
          safeDispatch({
            type: 'run_step',
            step: event.step,
            attempt: event.attempt,
            previous: event.previous,
          });
          break;
        case 'message':
          addItem({ kind: 'assistant', text: event.text });
          break;
        case 'plot':
          onPlot(event.result);
          break;
        case 'refusal':
          addItem({ kind: 'refusal', code: event.code, text: event.text });
          trackEvent('agent_guardrail_block', {
            reason: GUARDRAIL_REASONS.has(event.code) ? event.code : 'other',
          });
          break;
        case 'error':
          addItem({ kind: 'error', code: event.code, ref: event.ref });
          if (event.code === 'guard_unavailable') {
            trackEvent('agent_guardrail_block', { reason: 'guard_unavailable' });
          }
          break;
        case 'done':
          // The assistant changed the data (`prepare_data`) or computed it from a
          // formula (`generate_data`, version 1 when there was none): the version
          // replaces the preview, and the user checks and confirms it like a paste.
          if (event.dataset) {
            safeDispatch({ type: 'data_prepared', dataset: event.dataset });
            trackEvent('agent_data_prepared', {
              changes: countBucket(event.dataset.changes.length),
            });
          }
          // The root may have changed the bindings during the turn (`set_bindings`),
          // which also drops the server's confirmation: take both as the server has them.
          // After a data change too, because a binding change may have followed it.
          if (event.bindings !== null || event.dataConfirmed !== null) {
            safeDispatch({
              type: 'server_sync',
              bindings: event.bindings && toMap(event.bindings),
              dataConfirmed: event.dataConfirmed,
            });
          }
          // The first typed message (`detected`) or the assistant's `set_language`
          // (`chosen`) may have set the session language: the chip follows the server.
          // The `.to_long()` offer travels with the language the server computed it in, and applies
          // only when that language does: a `done` the chip ignores never renames the card.
          if (event.language) {
            safeDispatch({
              type: 'language_sync',
              plotLanguage: event.language,
              suggestion: event.suggestion,
            });
          }
          break;
        default:
          break;
      }
    },
    [safeDispatch, addItem, onPlot, trackEvent]
  );

  const runTurn = useCallback(
    async (body: TurnBody) => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy()) return;
      const controller = new AbortController();
      abortRef.current = controller;
      stoppedRef.current = false;
      safeDispatch({ type: 'run_start', kind: 'text' in body ? 'message' : body.action });
      addItem(
        'text' in body
          ? { kind: 'user', text: body.text }
          : { kind: 'action', action: body.action, library: current.library }
      );
      let finished = false;
      try {
        const response = await agentApi.postMessage(token, sid, body, controller.signal);
        if (!response.body) throw new AgentApiError(502, 'upstream');
        for await (const raw of readSseEvents(response.body, controller.signal)) {
          const event = parseAgentEvent(raw);
          if (!event) continue;
          onEvent(event);
          if (event.type === 'done') {
            finished = true;
            break;
          }
        }
        if (!finished && !stoppedRef.current) {
          // The BFF always ends a turn with `done`; a stream without it was cut.
          addItem({ kind: 'error', code: 'upstream', ref: null });
        }
      } catch (err) {
        if (!stoppedRef.current && !isAbort(err)) {
          const failure = handleFailure(err);
          addItem({ kind: 'error', code: failure.code, ref: failure.ref });
        }
      } finally {
        if (stopTimer.current) clearTimeout(stopTimer.current);
        stopTimer.current = null;
        if (stoppedRef.current) addItem({ kind: 'notice', text: 'stopped' });
        if (abortRef.current === controller) abortRef.current = null;
        safeDispatch({ type: 'run_end' });
      }
    },
    [token, safeDispatch, addItem, onEvent, handleFailure, busy]
  );

  const createPlot = useCallback(() => runTurn({ action: 'create_plot' }), [runTurn]);

  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || trimmed.length > MAX_MESSAGE_CHARS) return Promise.resolve();
      return runTurn({ text: trimmed });
    },
    [runTurn]
  );

  // ---------------------------------------------------------------- parse and summary

  /**
   * `.parse()`: send the pasted text. A table is stored (version 1, unconfirmed),
   * its default bindings are applied, and the assistant's summary of it follows
   * as the turn `summarize_data`; the returned promise ends with that turn.
   * Text that is no table comes back as a transcription to decide on, which
   * stores nothing and asks for no summary. `table` reads another of the
   * tables the previous answer named (the data panel's table picker).
   */
  const parseData = useCallback(
    async (text: string, confirmed = false, source?: string, table?: number) => {
      const sid = stateRef.current.sessionId;
      if (!sid || !text.trim() || busy()) return;
      const bytes = utf8Bytes(text);
      const bucket = sizeBucket(bytes);
      if (bytes > MAX_DATASET_BYTES) {
        safeDispatch({ type: 'parse_failed', failure: { code: 'too_long', ref: null } });
        trackEvent('agent_data_parsed', { status: 'too_long', size_bucket: bucket });
        return;
      }
      let stored = false;
      parseRef.current = true;
      safeDispatch({ type: 'parse_start' });
      try {
        const parsed = await agentApi.uploadDataset(token, sid, text, confirmed, source, table);
        if (isTranscribed(parsed)) {
          // Free text read into a table: shown for the user to confirm, not stored.
          safeDispatch({
            type: 'transcribed',
            transcription: {
              text: parsed.text,
              preview: parsed.preview,
              profile: parsed.profile,
              warnings: parsed.warnings ?? [],
              note: typeof parsed.note === 'string' ? parsed.note : '',
              bytes,
              ...(source ? { source } : {}),
            },
          });
          trackEvent('agent_data_parsed', { status: 'transcribed', size_bucket: bucket });
          return;
        }
        safeDispatch({
          type: 'parse_done',
          parsed,
          bytes,
          // The text of a paste the table picker may read again (a confirmed transcription is never split).
          ...(confirmed ? {} : { paste: { text, ...(source ? { source } : {}) } }),
          upload: { text, confirmed, ...(source ? { source } : {}), ...(table ? { table } : {}) },
        });
        // A paste before any typed message may set the session language from its notes or headers.
        const pastedLanguage = readPlotLanguage(parsed.language);
        if (pastedLanguage) safeDispatch({ type: 'language_sync', plotLanguage: pastedLanguage });
        trackEvent('agent_data_parsed', { status: 'ok', size_bucket: bucket });
        stored = true;
        const defaults = toMap(parsed.bindings);
        // Learn whether the defaults are complete and which required roles
        // they leave open (the parse stored them already: the PUT is idempotent).
        await applyBindings(defaults, defaults);
      } catch (err) {
        const failure = handleFailure(err);
        // A formula or code is refused so that the chat computes or runs it (`sendFormula`).
        safeDispatch({
          type: 'parse_failed',
          failure,
          ...(failure.code === 'formula' || failure.code === 'code'
            ? { formula: text, formulaKind: failure.code }
            : {}),
        });
        const status = ['too_long', 'unparseable', 'data_refused'].includes(failure.code)
          ? failure.code
          : 'error';
        trackEvent('agent_data_parsed', { status, size_bucket: bucket });
        if (PASTE_GUARDRAIL_REASONS.has(failure.code)) {
          trackEvent('agent_guardrail_block', { reason: failure.code });
        }
      } finally {
        parseRef.current = false;
      }
      // The assistant describes the stored data first thing, so the user can
      // correct it in words before confirming it.
      if (stored && mounted.current) await runTurn({ action: 'summarize_data' });
    },
    [token, safeDispatch, handleFailure, trackEvent, applyBindings, busy, runTurn]
  );

  /**
   * `.use()`: store the transcribed table. Its CSV goes through the normal
   * parse as a confirmed table (the server skips only its free-text fallback),
   * which stores it, applies the default bindings, reports
   * `agent_data_parsed{status: ok}` and asks for the summary; the parse's start
   * clears the transcription. While something else is in flight nothing starts
   * and the table stays.
   */
  const confirmTranscription = useCallback(() => {
    const transcription = stateRef.current.transcription;
    if (!transcription) return Promise.resolve();
    // The file's name travels with the table it was read from, whatever the box holds now.
    return parseData(transcription.text, true, transcription.source);
  }, [parseData]);

  /**
   * `.send()` next to a refused formula or code: the text goes to the chat as
   * the user's turn, where the assistant's `generate_data` computes the table or
   * its `run_data_code` runs the code. The returned promise ends with that turn.
   * While anything else is in flight nothing starts and the offer stays. A
   * formula always fits a turn (the dataset route refuses only text within the
   * chat's cap as one); code longer than `MAX_MESSAGE_CHARS` is refused too, and
   * the panel asks the user to shorten it instead of offering `.send()`.
   */
  const sendFormula = useCallback(() => {
    const current = stateRef.current;
    const text = current.formula?.trim();
    if (!text || text.length > MAX_MESSAGE_CHARS || current.run || busy()) {
      return Promise.resolve();
    }
    safeDispatch({ type: 'formula_sent' });
    return runTurn({ text });
  }, [safeDispatch, busy, runTurn]);

  /**
   * Stop: the cancel route takes a waiting run out of the queue at once and
   * aborts a running one at its next step boundary. The stream stays open
   * until the server's `done` says the run is over, so the next action does
   * not meet `409 run_active`, and a result stored just before the stop still
   * arrives. After `STOP_GRACE_MS`, or when the cancel call fails, the stream
   * is closed here.
   */
  const stop = useCallback(async () => {
    const sid = stateRef.current.sessionId;
    const controller = abortRef.current;
    if (!sid || !controller || stoppedRef.current) return;
    stoppedRef.current = true;
    safeDispatch({ type: 'run_stopping' });
    stopTimer.current = setTimeout(() => controller.abort(), STOP_GRACE_MS);
    try {
      await agentApi.cancel(token, sid);
    } catch {
      controller.abort(); // the server may not have heard the cancel: end the turn in this tab
    }
  }, [token, safeDispatch]);

  // ---------------------------------------------------------------- library

  const switchLibrary = useCallback(
    async (next: string): Promise<boolean> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy() || next === current.library) return false;
      safeDispatch({ type: 'library_start' });
      try {
        const result = await agentApi.switchLibrary(token, sid, specId, next);
        safeDispatch({ type: 'library_done', library: next, eligibility: result.eligibility });
        return true;
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'library_failed', failure });
        addItem({ kind: 'error', code: failure.code, ref: failure.ref });
        return false;
      }
    },
    [token, specId, safeDispatch, addItem, handleFailure, busy]
  );

  // ---------------------------------------------------------------- save

  /**
   * `.save()`: download the session's feedback case as `anyplot-session-<id>.json`,
   * with each version's `data.csv` when `includeData` is set, and report
   * `agent_session_saved{include_data}`. Nothing starts without a session, while
   * anything else is in flight (the file would miss the turn in progress), or
   * while a save runs. A failure rejects with an `AgentApiError` for the
   * button's failure line; a 401 or 403 also shows the sign-in notice.
   */
  const saveSession = useCallback(
    async (includeData: boolean): Promise<void> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy() || saveRef.current) return;
      saveRef.current = true;
      try {
        const { blob, filename } = await agentApi.fetchBundle(token, sid, includeData);
        if (!mounted.current) return;
        downloadBlob(blob, filename);
        trackEvent('agent_session_saved', { include_data: includeData ? 'yes' : 'no' });
        void agentApi.reportOutcome(token, sid, { action: 'saved_session', version: 0 });
      } catch (err) {
        const failure = handleFailure(err);
        throw err instanceof AgentApiError ? err : new AgentApiError(0, failure.code);
      } finally {
        saveRef.current = false;
      }
    },
    [token, handleFailure, trackEvent, busy]
  );

  // ---------------------------------------------------------------- language

  /**
   * The chip's choice: `PUT .../language` with the value as given (the chip
   * trims it). The answer is the new state, source `chosen`, in the server's
   * stored form (`English` comes back as `en`). Nothing starts without a
   * session or while anything else is in flight, which the server would refuse
   * with `409 run_active`. A failure keeps the old value and rejects with an
   * `AgentApiError` for the chip's failure line; a 401 or 403 also shows the
   * sign-in notice.
   */
  const setLanguage = useCallback(
    async (language: string): Promise<void> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy()) return;
      languageRef.current = true;
      safeDispatch({ type: 'language_start' });
      try {
        const { suggestion, ...applied } = await agentApi.setLanguage(token, sid, language);
        safeDispatch({ type: 'language_done', plotLanguage: applied });
        // The offer's new column names follow the language: the card shows what `.to_long()` applies.
        if (suggestion !== undefined) safeDispatch({ type: 'suggestion_sync', suggestion });
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'language_failed' });
        throw err instanceof AgentApiError ? err : new AgentApiError(0, failure.code);
      } finally {
        languageRef.current = false;
      }
    },
    [token, safeDispatch, handleFailure, busy]
  );

  // ---------------------------------------------------------------- feedback

  /**
   * `.send()` on a result card: store the case of version `number` (`POST
   * .../feedback`), record it on the version and report
   * `agent_result_feedback{reaction, include_data, subject}`. `number` 0 is the
   * chat itself, recorded as `chatFeedback`. It runs whatever else is in
   * flight, because it starts no run and only reads the session; a second call
   * for a version whose send is still in flight joins that one. A failure
   * rejects with an `AgentApiError` for the control's failure line, and records
   * nothing, except a `502 row_missing`, whose case is stored: its `caseId` is
   * recorded so the next edit replaces it. A 401 or 403 also shows the sign-in
   * notice.
   */
  const sendFeedback = useCallback(
    (number: number, input: FeedbackInput): Promise<void> => {
      const pending = feedbackRef.current.get(number);
      if (pending) return pending;
      const sid = stateRef.current.sessionId;
      const chat = number === 0;
      if (!sid || (!chat && !stateRef.current.versions[number])) {
        return Promise.reject(new AgentApiError(0, 'no_session'));
      }
      const message = input.message.trim() || null;
      if (message && message.length > MAX_FEEDBACK_CHARS) {
        return Promise.reject(new AgentApiError(0, 'too_long'));
      }
      // An edit names the case it replaces, so the triage need not guess from the times.
      const replaces = chat
        ? stateRef.current.chatFeedback?.caseId
        : stateRef.current.versions[number].feedback?.caseId;
      const send = async () => {
        try {
          const stored = await agentApi.sendFeedback(token, sid, {
            reaction: input.reaction,
            message,
            include_data: input.includeData,
            result_version: number,
            ...(replaces ? { replaces } : {}),
          });
          safeDispatch({
            type: 'version_feedback',
            number,
            feedback: {
              reaction: input.reaction,
              message,
              includeData: input.includeData,
              caseId: stored.case_id,
            },
          });
          trackEvent('agent_result_feedback', {
            reaction: input.reaction,
            include_data: input.includeData ? 'yes' : 'no',
            subject: chat ? 'chat' : 'result',
          });
          void agentApi.reportOutcome(token, sid, {
            action: 'feedback',
            version: number,
            reaction: input.reaction,
          });
        } catch (err) {
          // `502 row_missing`: the case IS in the bucket, only its triage row is
          // missing. Record it, so the next edit names it in `replaces` and the
          // backfill can link the chain; the control still shows the failure.
          if (err instanceof AgentApiError && err.code === 'row_missing' && err.caseId) {
            safeDispatch({
              type: 'version_feedback',
              number,
              feedback: {
                reaction: input.reaction,
                message,
                includeData: input.includeData,
                caseId: err.caseId,
              },
            });
          }
          const failure = handleFailure(err);
          throw err instanceof AgentApiError ? err : new AgentApiError(0, failure.code);
        } finally {
          feedbackRef.current.delete(number);
        }
      };
      const promise = send();
      feedbackRef.current.set(number, promise);
      return promise;
    },
    [token, safeDispatch, handleFailure, trackEvent]
  );

  return {
    state,
    toLongData,
    parseData,
    copyData,
    replayData,
    confirmTranscription,
    discardTranscription,
    sendFormula,
    setBinding,
    confirmData,
    undoData,
    createPlot,
    sendMessage,
    stop,
    switchLibrary,
    requestTheme,
    fetchArtifact,
    reportOutcome,
    convertFile,
    saveSession,
    setLanguage,
    sendFeedback,
  };
}

export type AgentSession = ReturnType<typeof useAgentSession>;

/** Whether the page should hold back actions the server would refuse or race (see the module notes). */
export function sessionBusy(state: AgentSessionState): boolean {
  return (
    !!state.run ||
    state.parsing ||
    state.bindingsBusy ||
    state.confirmBusy ||
    state.undoBusy ||
    state.libraryBusy ||
    state.themeBusy ||
    state.pageBusy ||
    state.languageBusy
  );
}

/**
 * Whether leaving the page would lose something: stored data, a table read
 * from text that waits for its decision, a plot, or work in flight. The
 * session lives only in this page's memory and the server's (see the module
 * notes), so the page asks before a reload, a closed tab or a navigation ends
 * it. Only while the page shows the session (`ready`): an expired or refused
 * one shows nothing that leaving would take away.
 */
export function sessionHoldsWork(state: AgentSessionState): boolean {
  return (
    state.phase === 'ready' &&
    (!!state.dataset ||
      !!state.transcription ||
      Object.keys(state.versions).length > 0 ||
      sessionBusy(state))
  );
}
