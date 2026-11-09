/**
 * State machine of one "Use with my data" chat session (`/agent`), on either lane.
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
 * Theme: every turn sends the theme the site shows when it starts
 * (`useTheme().effective`, so `system` resolves first), and a plot of that turn
 * renders in it unless the user asked for a theme in the chat; the light and
 * dark switch renders the other one. A switch of
 * the site theme mid-session changes no shown version, only the next one. The
 * fan-out's sessions are this hook too, so they send the same theme.
 *
 * Bindings: the dataset answer lists the spec's roles. A single role binds
 * under its own name, a variadic family `y` under its members `y1`, `y2`, ...;
 * the hook keeps the members contiguous (`compactFamilies`), so clearing `y2`
 * of three moves `y3` up. One column may serve several roles; a family takes
 * it once, and two members trade columns rather than drop one (`setBinding`).
 * Every change replaces the whole set on the server.
 *
 * Transcriptions: pasted text that is not a table comes back as a table the
 * server read with a model and did not store (`transcription`). The dataset
 * and bindings stay as they were until the user confirms it, which posts the
 * table's CSV through the normal parse (`confirmTranscription`), or discards
 * it. A new parse, a library switch and a failed session clear it as well.
 *
 * Two steps, data first: step 1 ends when the stored dataset and its bindings
 * are confirmed (`confirmData`, `POST .../dataset/confirm`), which the page's
 * `.create_plot()` does as the first link of its click, before the plot run
 * (step 2) that needs it. The server drops
 * its confirmation whenever the dataset or a binding changes, and so does the
 * hook: a stored parse and any applied binding change clear `dataConfirmed`,
 * a library switch keeps it. A transcription clears it too, although the
 * server keeps its own until `.use()` stores the table: the user decides on
 * the data again either way. A turn can change the bindings on the server
 * too (the root's `set_bindings`): its `done` event carries the session's
 * bindings and step state, which replace the hook's (`server_sync`), so the
 * dropdowns show what the server holds and the panel goes back to step 1.
 * A `plot{not_ready, data_unconfirmed}` without that sync still drops the
 * flag, so the next `.create_plot()` confirms again. It adds no thread item:
 * it is the step line's news, not a failed plot, and it arrives before the
 * turn's `done`, so it drops the flag only once the turn is over. A data change
 * the same turn made then names the loss itself, in the step line.
 *
 * A confirmation the user had given and then lost is named right above the
 * composer: the reducer watches the flag go from set to cleared, whatever
 * action did it, and keeps the reason (`confirmLoss`: a binding change, new
 * data, or the server's word) for the step lines, with no notice in the
 * thread, which would say the same once more. The parse's own default
 * bindings land while the flag is already clear, so a first setup after a
 * paste names nothing. The reason follows the data the card shows: a later
 * paste clears it, a later data change or undo makes it a change of the data.
 * The reducer numbers the thread items itself (`nextItemId`).
 *
 * Thread items beyond the talk: every data version gets an item with a
 * snapshot of what it held (`DataSnapshot`), under the server's number for it
 * (`data v3`), which the session gives every version once and the assistant's
 * session block lists too. An undo brings a number back (`data v1 · back to
 * v1`), so two items can carry the same one, each under its own item id. The
 * live card is the one `data` item; a version it no longer shows stays as a
 * `data_stub` (`placeData` says where each goes). A
 * library switch adds a `switch` item with the decisions the plot in the new
 * library takes over, and a typed turn that reached its `done` carries what it
 * changed (`TurnOutcome`). `threadModel.ts` reads chapters, folds and counts
 * from these items.
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
 * before the last change, unconfirmed as well; the data's `can_undo` says
 * whether there is one (the service keeps the last five), never its number.
 *
 * Formulas: the assistant's `generate_data` computes a table from a formula
 * the user asks for in the chat ("y = sin(x), x from -pi to pi"). Its `done`
 * carries the table like any data change: the next version when data exists,
 * or version 1 when the session had none, which then becomes the hook's first
 * dataset with the roles and default bindings `done` names (nothing to undo).
 * The dataset route answers such text sent as an attachment with `422
 * formula`, because its free-text reader is a model that would write the rows
 * itself; code that generates data (Python, JavaScript, R) with `422 code`;
 * text that asks for data instead of holding it ("Beispieldaten", "random
 * numbers with three categories") with `422 data_request`. `parseData` sends
 * each of them to the chat as the user's turn at once (the outcome
 * `forwarded`), where the assistant computes the formula (`generate_data`),
 * runs the code or writes code for example data (`run_data_code`); the turn's
 * `done` carries the table like any data change, and a version computed from
 * code carries the Python that ran (`code`). Only text the chat takes
 * (`MAX_MESSAGE_CHARS`) can move there: longer code fails with a line that
 * asks to shorten it.
 * `exampleData` (`.example_data()`, in the line above the message box,
 * highlighted while the session has no data) asks for the same in one click as the action
 * `example_data`, never as typed words: the session's first typed message sets
 * the session language, and an action leaves it to the visitor's own words.
 *
 * The spec's roles also come with the session's open (`specRoles`), before any
 * data, for the page header's list of the columns the plot expects; the data
 * panel's dropdowns keep reading `roles`, which each dataset answer replaces.
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
 * A cut stream: the connection between the browser and the edge proxy can fail
 * (an HTTP/3 error) while the origin runs the turn to its end and stores its
 * plot. When a turn's stream fails or ends without `done` after its first event,
 * the run keeps its loader with a quiet "connection lost · reconnecting…" line
 * and reads the rest of the turn again (`agentApi.resumeTurn`, after the last SSE
 * id it read) after each of `RESUME_DELAYS_MS`; only when every read failed does
 * the error show. Such a turn stays pending: the next turn reads it first, while
 * nothing in the session changed since, and when the cut turn shipped its plot,
 * before the cut or with that read, the same request again (a retry click) ends
 * there instead of making the same plot a second time. `agent_turn_resumed{outcome}` counts each
 * cut: `resumed`, `gone` (the server holds another turn) or `failed`.
 *
 * Session lifetime: the session, with the pasted data and its renders, is
 * deleted when the page unmounts and on `pagehide` (a reload or a closed tab,
 * sent with `keepalive`); the server's idle sweep is the backstop. Nothing
 * restores it, so while it holds data, a plot or work in flight
 * (`sessionHoldsWork`) the page asks before it lets the user leave.
 *
 * Library switch and plot memory (since 2026-11-02): `switchLibrary` keeps
 * the data, the bindings, their confirmation, the language and the versions,
 * as the server does, and takes the answer's `carry`. When it says `offer`,
 * `carryOffer` holds the offer of the plot in the new library with the plot
 * memory's decisions (`carryPlot`, the action `carry_plot`); from the menu the
 * run waits for the user's click. The offer ends once a plot in that library
 * ships, whatever turn shipped it, with the next switch, whose answer
 * brings its own offer or none, or with a new data version (a paste, a change,
 * an undo), for which the server drops its carry too. `createPlot` stays the fresh plot from the
 * catalogue code, without the carry but with the remembered decisions (`.create_plot()`,
 * `.start_over()`), and `plotNewData` is "plot the new data" (`plot_new_data`), which the server
 * starts from the latest plot when its guard allows it. The plot memory is the
 * server's list of the decisions a plot takes over (`memory`): the hook reads
 * it after every turn's `done` (a shipped run adds entries, the assistant's
 * `forget` removes them; nothing else empties it), after a switch, and
 * takes the list a removal answers (`forgetMemory`, `.forget()`). A read that
 * fails, or a server without the route, leaves the list as it was; a read
 * overtaken by a newer one or by a removal's answer is dropped. The admin
 * fan-out's sessions read none. A shipped version names the decisions it kept
 * and added by id (`plot.memory`); the version keeps their texts
 * (`PlotVersion.decisions`), the kept ones from the list it arrives on, the
 * added ones from the read after its turn, so its card says what it kept also
 * after a later `.forget()`.
 *
 * Saving: `saveSession` (`.save()`) downloads the session's feedback case,
 * the conversation, code, images and config the agents service assembles,
 * as one JSON file. It only reads the session and starts no run, so no state
 * tracks it: the button keeps its own saving flag and failure line.
 *
 * Session language: one per session, for the assistant's replies and every
 * text in the plot, held as `plotLanguage` (`language` is the programming
 * language on this page). It starts as `en` with the source `default`,
 * whatever the browser's locale, as the server's does, and stays English until
 * the user picks another. A turn's `done` or a paste's answer may carry an
 * offer (`language.offer`: a language the server found in the typed message or
 * in the paste's notes or column names), which appends the thread's one
 * language line (`language_offer`) with `.switch()`; ignored, nothing changes.
 * `acceptLanguage` (`PUT .../language` with `via: offer`) takes it: source
 * `offer`, the line then names the language it set. A choice from the header's
 * chip (`setLanguage`) or the assistant's `set_language` brings `chosen`, which
 * is final: it closes every open offer, and none comes after it. Only the
 * server's answers set it, and a `done` never moves it down the ladder
 * (`SOURCE_RANK`: a choice from another tab can land between the server's
 * finish and this page's `run_end`). It is no data change: it never touches
 * the confirmation.
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
 * `agent_guardrail_block{reason}`, `agent_session_saved{include_data}`,
 * `agent_result_feedback{reaction, include_data, subject}` and
 * `agent_turn_resumed{outcome}`.
 *
 * Usage telemetry: after a copy, a download, a save or a sent feedback, a
 * fire-and-forget beacon (`POST .../outcome`) tells the BFF which action it
 * was and on which version (with the reaction for feedback), and nothing else:
 * no text, no file or column name, no code, no data. `reportOutcome` is the
 * result card's way in; the save and the feedback send it themselves.
 */

import { useCallback, useEffect, useReducer, useRef } from 'react';

import { useAnalytics } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import {
  agentApi,
  AgentApiError,
  type AgentEvent,
  type ArtifactName,
  type Binding,
  type BindingsApplied,
  type ChatSwitch,
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
  type LanguageOffer,
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
  type PlotMemory,
  type PlotResult,
  type PlotTarget,
  PNG_ARTIFACT,
  languageOffer as readLanguageOffer,
  plotLanguage as readPlotLanguage,
  renderedThemes,
  type RoleSpec,
  type Round,
  sizeBucket,
  type SwitchCarry,
  type SwitchSource,
  type Theme,
  type TurnAction,
  type TurnBody,
  type TurnOutcome,
  utf8Bytes,
  type VersionMemory,
} from 'src/lib/agent';
import { readSseEvents } from 'src/lib/sse';
import { downloadBlob } from 'src/sections/agent-chat/files';
import { sameLanguage } from 'src/sections/agent-chat/languages';
import { nextUtcMidnight, type NoticeInfo } from 'src/sections/agent-chat/messages';
import type { ConvertedFile } from 'src/sections/agent-chat/useChatAttachment';

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
  /**
   * Set while the turn waits in the run queue: `position` 1 runs next. Cleared by the wait's end
   * (`status{step:"started"}`), which also drops the `queued` step, and by a pipeline step.
   */
  queue: { position: number; waiting: number } | null;
  stopping: boolean;
  /** The rounds that ended so far, from each repair step's `outcome` (absent: none yet). */
  rounds?: Round[];
  /** The turn's stream was cut, and the page waits to read the rest of the turn again (`RESUME_DELAYS_MS`). */
  reconnecting?: boolean;
  /**
   * When the run's clock started (ms since the epoch): the turn's start, or, after a wait in the
   * run queue, the wait's end. Absent for a turn the page did not start (the late read of a cut
   * turn), which shows no clock and gives its version no `readyMs`, never a wrong time.
   */
  startedAt?: number;
  /** The most rounds the run may make, from the server's steps (`max_attempts`); absent without it. */
  maxAttempts?: number;
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
  /**
   * The decisions the version kept and added (`result.memory`), with their texts as the plot
   * memory listed them; absent when the server named none (`VersionMemory`), which shows no kept
   * label and no kept line.
   */
  decisions?: VersionDecisions;
  /**
   * How long the plot took, from the run's clock (`RunState.startedAt`) to the version (ms), for
   * the card's `ready in 1:12`; absent for a version the page did not time.
   */
  readyMs?: number;
}

/**
 * A decision of a version's memory: its entry id and its text, `null` while no list read so far
 * named the id (the read failed, or the decision was forgotten before any read). A text once known
 * stays: a later `.forget()` never rewrites an older card.
 */
export interface VersionDecision {
  id: string;
  text: string | null;
}

/** A version's decisions, from before the run (`kept`) and from the run itself (`added`). */
export interface VersionDecisions {
  kept: VersionDecision[];
  added: VersionDecision[];
}

/**
 * A version's decisions with the texts `memory` names: the kept ones resolve against the list read
 * before the run, the added ones once the read after the turn's `done` lists them
 * (`resolveDecisions`).
 */
function versionDecisions(ids: VersionMemory, memory: PlotMemory | null): VersionDecisions {
  const texts = new Map((memory?.entries ?? []).map(entry => [entry.id, entry.text]));
  const named = (id: string): VersionDecision => ({ id, text: texts.get(id) ?? null });
  return { kept: ids.kept.map(named), added: ids.added.map(named) };
}

/**
 * The versions with every text still unknown filled in from `memory`, which names it: an id names
 * one decision for the session's life, so any list that holds it gives its text. A known text
 * never changes, and a version whose texts are all known is the same object.
 */
function resolveDecisions(
  versions: Record<number, PlotVersion>,
  memory: PlotMemory
): Record<number, PlotVersion> {
  const texts = new Map(memory.entries.map(entry => [entry.id, entry.text]));
  const fill = (list: VersionDecision[]) =>
    list.some(item => item.text === null && texts.has(item.id))
      ? list.map(item =>
          item.text === null ? { ...item, text: texts.get(item.id) ?? null } : item
        )
      : list;
  let changed = false;
  const next: Record<number, PlotVersion> = {};
  for (const [key, version] of Object.entries(versions)) {
    const decisions = version.decisions;
    const kept = decisions ? fill(decisions.kept) : null;
    const added = decisions ? fill(decisions.added) : null;
    if (decisions && kept && added && (kept !== decisions.kept || added !== decisions.added)) {
      changed = true;
      next[Number(key)] = { ...version, decisions: { kept, added } };
    } else {
      next[Number(key)] = version;
    }
  }
  return changed ? next : versions;
}

/**
 * What made a data version: a paste or a dropped file (`paste`, also the fan-out's replay of
 * one), `.use()` of a table read from text (`transcription`), the table or the sheet picker, the
 * assistant in a turn (`turn`: `prepare_data`, `generate_data`, `run_data_code`), `.to_long()`,
 * `.undo()`, or the admin fan-out's copy.
 */
export type DataVersionChange =
  'paste' | 'transcription' | 'table' | 'sheet' | 'turn' | 'to_long' | 'undo' | 'copy';

/**
 * One data version as the thread keeps it, taken when the version arrives: the live card's
 * item carries it, and the stub the version leaves behind once a newer one replaces it keeps it,
 * so an older version can show what it held without the server.
 */
export interface DataSnapshot {
  /**
   * The version's number in this session (`data v3`): the server's `version`, which numbers
   * every stored version once and which the assistant's session block lists too. After an
   * undo the restored version carries its own number again, so it is no item's id.
   */
  n: number;
  change: DataVersionChange;
  /** How the version came about, in a few words: `pasted`, `sales.csv`, `sheet "2026"`, `made long`. */
  summary: string;
  /** The version's name in the thread: `data v3 · made long`. */
  label: string;
  rows: number;
  columns: number;
  /** The workbook's sheet the version was read from; `null` for data no sheet holds. */
  sheet: string | null;
  /** The dropped file's name as the server screened it; `null` for pasted or computed data. */
  fileName: string | null;
  /** The assistant's change lines (`done.dataset.changes`); empty for every other version. */
  changes: string[];
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  /**
   * A paste whose answer said a column the replaced data was plotted by is not in it
   * (`columns_changed`): its chapter line holds the remembered decisions until the next plot,
   * with `.forget_all()` (`threadModel`'s `decisionsEarlier`).
   */
  columnsChanged?: true;
}

/**
 * What a typed turn changed (`TurnOutcome` in `agent.ts`), on its item once its `done` arrived:
 * the server's own word (`done.turn`), which sees a wish kept for the first plot that the stream
 * shows nothing of, checked against what the stream showed (`turnOutcome`); the memory read after
 * the turn still moves an `answer` whose turn changed the memory (`memory_sync`).
 */
export type { TurnOutcome };

export type ChatItem =
  /**
   * `outcome`: what the turn changed, set once its `done` arrived; a turn that ended otherwise, or
   * whose server named an outcome this page does not know while its stream showed no change, has
   * none. `note`: the text typed with an attachment, the first turn on new data, whose reply
   * summarizes that data: never a question, whatever it changed.
   */
  | { id: number; kind: 'user'; text: string; outcome?: TurnOutcome; note?: true }
  /** `label`: the button as it read when the user pressed it, which the thread shows for the action. */
  | { id: number; kind: 'action'; action: TurnAction; library: string; label?: string }
  | { id: number; kind: 'assistant'; text: string }
  /** `until`: when a `service_paused` refusal ends (the next 00:00 UTC as it arrived). */
  | { id: number; kind: 'refusal'; code: string; text: string; until?: string }
  | { id: number; kind: 'error'; code: string; ref: string | null }
  | { id: number; kind: 'plot'; version: number }
  | { id: number; kind: 'plot_failed'; result: PlotResult }
  /** The attachment the user sent, as its chip named it (`▤ table · 4 lines · 46 B`). */
  | { id: number; kind: 'paste'; text: string }
  /**
   * The live data card, at the latest data version (`placeData`). One at most. `snapshot`: the
   * version it shows; the reducer always sets it, and only a thread built by hand lacks it.
   */
  | { id: number; kind: 'data'; snapshot?: DataSnapshot }
  /**
   * A data version a newer one replaced: its shape (`rows`, `columns`) and its snapshot as they
   * were then. `card` is the id of the card item that showed the version; a stub that a paste or
   * `.use()` froze in place is that item, and keeps its id.
   */
  | {
      id: number;
      kind: 'data_stub';
      rows: number;
      columns: number;
      snapshot?: DataSnapshot;
      card?: number;
    }
  /**
   * A library switch, from the menu or the chat. `decisions`: what the plot in the new library
   * takes over (`carryDecisions`), following the plot memory while the switch's offer stands;
   * `null` when the switch offered no plot with them.
   */
  | { id: number; kind: 'switch'; from: string; library: string; decisions: number | null }
  /**
   * Where a table read from text waits for `.use()` or `.discard()`; `.use()` turns it into the
   * data card, `.discard()` into a notice.
   */
  | { id: number; kind: 'transcription' }
  /** A quiet line from the page itself; `info` holds the details behind its ⓘ, which keep it short. */
  | { id: number; kind: 'notice'; text: string; info?: NoticeInfo }
  /**
   * The offer of a language found in a typed message or a paste (`basis`), the thread's one
   * language line: `open` while its `.switch()` can take it, `accepted` once it did (`plot`: a
   * plot was on screen, so its next version brings the language), `closed` once a pick elsewhere
   * made it moot (the chip, a request in the chat, another offer taken).
   */
  | {
      id: number;
      kind: 'language_offer';
      language: string;
      basis: LanguageOffer['basis'];
      state: 'open' | 'accepted' | 'closed';
      plot?: boolean;
    };

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
  /**
   * The binary file (Excel, ODS, Parquet, ...) this version's text was converted from, kept in
   * the page for the sheet picker, which converts it again for another sheet. Never stored.
   */
  file?: ConvertedFile;
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
  /** The converted workbook the text came from: `.use()` keeps it for the sheet picker. */
  file?: ConvertedFile;
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

/**
 * How a parse (`parseData`) ended. `stored`: a table, then the summary turn. `transcribed`: free
 * text read into a table to decide on, nothing stored. `forwarded`: the server answered `422
 * formula`, `422 code` or `422 data_request` and the text went to the chat as the user's turn.
 * `failed`: refused, or no answer (`datasetError` says why). `skipped`: nothing started, because
 * there is no session or no text, or something else is in flight (a second Enter before the
 * state caught up).
 */
export type ParseOutcome = 'stored' | 'transcribed' | 'forwarded' | 'failed' | 'skipped';

/**
 * How a turn ended: its `done` (`done`), a refusal of the scope judge or a guardrail
 * (`refused`), an error event, a cut stream or a failed request (`error`), or the user's
 * `.stop()` (`stopped`).
 */
export type TurnEnd = 'done' | 'error' | 'refused' | 'stopped';

/**
 * The waits before each read of a turn whose stream was cut (`agentApi.resumeTurn`): four
 * reads within about 15 s, the last after 8 s, before the page shows the error.
 */
export const RESUME_DELAYS_MS: readonly number[] = [1_000, 2_000, 4_000, 8_000];

/** How a cut turn's reads ended, for `agent_turn_resumed{outcome}`. */
type ResumeOutcome = 'resumed' | 'gone' | 'failed';

/** What a turn's events showed it changed, for its outcome (`turnOutcome`). */
interface TurnChanges {
  /** A plot result arrived, shipped or not: the turn ran the plot pipeline. */
  plotted: boolean;
  /** The `done` carried a data version, or bindings other than the page's. */
  dataChanged: boolean;
  /** The `done` asked for a library switch. */
  switched: boolean;
  /** The `done` carried a language the user chose, other than the page's. */
  languageChosen: boolean;
  /**
   * The server's own word on what the turn changed (`done.turn`): it wins over what the stream
   * showed, which cannot see a plot wish kept for the first plot, except that `answer` holds only
   * while the stream showed no change either. `null` until a `done` names one (an older server);
   * `unknown` for a value the page does not know.
   */
  serverOutcome: TurnOutcome | 'unknown' | null;
}

/** What one turn's events said, gathered while the page reads them (`runTurn`). */
interface TurnRead extends TurnChanges {
  /** The turn's `done` arrived. */
  finished: boolean;
  errorCode: string | null;
  refused: boolean;
  refusalCode: string | null;
  /** A plot result with a stored version arrived in this read. */
  shipped: boolean;
  /** The SSE id of the last event read, `<run_id>.<n>`: where a read of the turn again starts. */
  lastId: string | null;
}

const freshRead = (): TurnRead => ({
  finished: false,
  errorCode: null,
  refused: false,
  refusalCode: null,
  shipped: false,
  lastId: null,
  plotted: false,
  dataChanged: false,
  switched: false,
  languageChosen: false,
  serverOutcome: null,
});

/** The change a turn's stream showed, in the server's order (`TURN_OUTCOMES`); `null` for none. */
function shownOutcome(changes: TurnChanges): TurnOutcome | null {
  if (changes.dataChanged) return 'data';
  if (changes.plotted) return 'plot';
  if (changes.switched) return 'switch';
  if (changes.languageChosen) return 'language';
  return null;
}

/**
 * What a turn that reached its `done` changed (`TurnChanges`), or `null` for no mark. The server's
 * word wins, but "nothing changed" must hold by both sources: an `answer` whose stream showed a
 * plot, a data version, a switch or a chosen language is that change. A value the page does not
 * know is a change, never a question: the stream's, or no mark when the stream showed none.
 * Without the server's word (an older server) the stream alone decides, an `answer` when it
 * showed nothing.
 */
function turnOutcome(changes: TurnChanges): TurnOutcome | null {
  const shown = shownOutcome(changes);
  const server = changes.serverOutcome;
  if (server === 'unknown') return shown;
  if (server === null || server === 'answer') return shown ?? 'answer';
  return server;
}

/**
 * What a turn's `done` shows it changed, against the page's state before it (`before`): a data
 * version, bindings other than the page's (the root's `set_bindings`), a switch the user asked
 * for, or a language the user chose (`set_language`). A language the first typed message
 * detected is no change the user asked for. And the server's own word on it (`done.turn`).
 */
function noteDone(
  read: TurnRead,
  done: Extract<AgentEvent, { type: 'done' }>,
  before: AgentSessionState
): void {
  read.serverOutcome = done.turn ?? null;
  const bindings = done.bindings && toMap(done.bindings);
  if (done.dataset || (bindings && before.dataset && !sameBindings(bindings, before.bindings))) {
    read.dataChanged = true;
  }
  if (done.switch) read.switched = true;
  const language = done.language;
  if (
    language?.source === 'chosen' &&
    (before.plotLanguage.source !== 'chosen' || before.plotLanguage.language !== language.language)
  ) {
    read.languageChosen = true;
  }
}

/** The part of a read a cut turn's later read starts from: what its events showed before the cut. */
const changesOf = (read: TurnRead): TurnChanges => ({
  plotted: read.plotted,
  dataChanged: read.dataChanged,
  switched: read.switched,
  languageChosen: read.languageChosen,
  serverOutcome: read.serverOutcome,
});

/**
 * What a turn's `done` sets in the page: while none of it changed since a cut, the cut turn's
 * late `done` is still the session's state, so the page may take it.
 */
const sessionMark = (state: AgentSessionState): readonly unknown[] => [
  state.dataset,
  state.bindings,
  state.dataConfirmed,
  state.library,
  state.plotLanguage,
  state.memory,
];

const sameMark = (a: readonly unknown[], b: readonly unknown[]) =>
  a.length === b.length && a.every((value, index) => Object.is(value, b[index]));

const sameRequest = (a: TurnBody, b: TurnBody) =>
  'text' in a ? 'text' in b && a.text === b.text : 'action' in b && a.action === b.action;

/** A turn whose stream was cut and could not be read again, which the next turn reads first. */
interface CutTurn {
  sid: string;
  body: TurnBody;
  lastId: string;
  mark: readonly unknown[];
  /** Its plot arrived before the cut: the same request again would make that plot a second time. */
  shipped: boolean;
  /** What its events showed before the cut, which its outcome counts once its `done` arrives. */
  changes: TurnChanges;
}

/** Resolves after `ms`, or at once when `signal` aborts. */
function pause(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise(resolve => {
    if (signal.aborted) {
      resolve();
      return;
    }
    const done = () => {
      clearTimeout(timer);
      signal.removeEventListener('abort', done);
      resolve();
    };
    const timer = setTimeout(done, ms);
    signal.addEventListener('abort', done, { once: true });
  });
}

/**
 * What `parseData` resolves to: its outcome, and how the turn it started ended (null without one,
 * or for a turn that never ended because the page unmounted).
 */
export interface ParseResult {
  outcome: ParseOutcome;
  turnEnd: TurnEnd | null;
  /** Why a `failed` parse was refused, as `datasetError` holds it: the attachment shows it. */
  failure?: Failure;
}

/** What the caller of `parseData` hears before the turn a parse starts, and what goes with the text. */
export interface ParseOptions {
  /**
   * The text went to the chat as the user's message (`forwarded`), trimmed as it was sent:
   * called before that turn runs, so the attachment can go at once.
   */
  onForward?: (text: string) => void;
  /** The data is stored: called before the first turn on it runs, so the attachment can go at once. */
  onStored?: () => void;
  /**
   * The text typed together with the attachment: once the data is stored it is the first turn,
   * as the user's message, in place of the summary action. The server gives that turn the
   * notes pasted with the table and the file's name, and the assistant summarizes the data and
   * acts on the note in one reply.
   */
  note?: string;
  /** The binary file the text was converted from, kept with the data for the sheet picker. */
  file?: ConvertedFile | null;
  /**
   * The attachment's line, as its chip showed it: the thread names the paste with it, and the
   * card follows. Without it (the table and sheet pickers) the parse reads the same data again,
   * and the card stays where it is.
   */
  chip?: string;
}

/** The dataset route's answers that send pasted text to the chat instead of a parser. */
const FORWARDED = new Set(['formula', 'code', 'data_request']);

/**
 * The scope judge's refusals (`scope_guard.REFUSAL_CODES`; `attack` reads as `out_of_scope`)
 * and its outage, which leave a note's turn without the summary of the data it came with. The
 * summary action skips the judge, so it still runs. The route's own refusals (a closed session,
 * a limit, the day's budget) would refuse the action as well.
 */
const NOTE_REFUSALS = new Set(['out_of_scope', 'needs_data', 'other_library']);
const NOTE_JUDGE_OUTAGE = 'guard_unavailable';

/**
 * The offer of the plot in the library the user switched to, with the plot
 * memory's decisions (the switch answer's `carry.offer`, the action `carry_plot`).
 */
export interface CarryOffer {
  /**
   * The (spec, library) pair the offer is for. Only the library switches today,
   * so the page compares the library alone; the later plot-type switch makes
   * the spec part of the comparison.
   */
  target: PlotTarget;
  /** The decisions the switch answer counted. */
  decisions: number;
  /**
   * The memory held entries at the switch, so the count is the memory's: it
   * follows the remembered list when the user removes an entry. Without entries
   * the server counted the source plot's requests, which the page cannot list.
   */
  memoryBacked: boolean;
}

/**
 * How many decisions the carry run takes over now: the remembered list's once
 * the memory ever held one (`written`, as the server counts: what the user
 * removed never comes back through the source plot's requests), else the
 * switch answer's count.
 */
export function carryDecisions(offer: CarryOffer, memory: PlotMemory | null): number {
  return memory && (memory.written || offer.memoryBacked) ? memory.entries.length : offer.decisions;
}

export interface AgentSessionState {
  phase: SessionPhase;
  failure: Failure | null;
  sessionId: string | null;
  library: string;
  eligibility: Eligibility | null;
  dataset: DatasetState | null;
  parsing: boolean;
  datasetError: Failure | null;
  /** A table read from free text that awaits `.use()` or `.discard()`. */
  transcription: TranscriptionState | null;
  /** The spec's roles, in spec order; the data panel shows a column choice for each. */
  roles: RoleSpec[];
  /**
   * The spec's roles as the session's open answered them, before any data: the page header
   * lists them as the columns the plot expects. `null` from a server without them.
   */
  specRoles: RoleSpec[] | null;
  bindings: BindingMap;
  bindingsComplete: boolean;
  /** Required roles without a column; a variadic family by its name. */
  missingRoles: string[];
  bindingsBusy: boolean;
  bindingsError: Failure | null;
  /**
   * The warnings of the server's binding check (`PUT .../bindings`, `BindingsApplied.warnings`) on
   * the data and the bindings in force: a role that needs values of 0 or more on negative values,
   * a computed role on a column of another window, a role that takes labels on a wide table's
   * numbers, a lower bound above its upper one, a key whose rows repeat. Never a refusal. `null`
   * while unknown: a new data version or a binding change of a turn came without a check, until
   * the next one (`checkBindings`). The plot button's one click stops at the card on any of them.
   */
  bindingWarnings: string[] | null;
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
  /**
   * After a switch whose answer offered it: the plot in this library with the
   * plot memory's decisions. A shipped plot in that library, the next switch or
   * a new data version (a paste, a change, an undo, which drop the server's carry
   * too) ends it.
   */
  carryOffer: CarryOffer | null;
  /** The plot memory as the server last listed it; `null` until a list arrived, or from a server without one. */
  memory: PlotMemory | null;
  /** A removal from the plot memory is in flight. */
  memoryBusy: boolean;
  /** The sheet picker's read of another sheet is in flight on the server (`readSheet`). */
  sheetBusy: boolean;
  /**
   * A library switch the user asked for in the chat (`done.switch`, the
   * assistant's `switch_plot`), which the page carries out once the turn is
   * over: the switch route, then with `plot` the carry run, without a second
   * click (`takeChatSwitch`).
   */
  chatSwitch: ChatSwitch | null;
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
  /**
   * The typed turn read as an answer whose memory read after its `done` is still to come: that
   * read moves its mark when the list changed (`memoryOutcome`). Any memory list ends the wait, so
   * does the latest read's failure (`memory_unread`), and so does the end of every later turn but the
   * summary and example data, which cannot change the memory: a read that failed or was overtaken
   * never lands on an older question. While it waits, the thread shows the turn as no question yet
   * (`threadModel`): a turn the read moves never shows "nothing changed".
   */
  memoryTurn: number | null;
  versions: Record<number, PlotVersion>;
  /** The last feedback case stored on the chat itself (version 0), for a session without a plot. */
  chatFeedback: FeedbackRecord | null;
  run: RunState | null;
}

type Action =
  | { type: 'opened'; sessionId: string; eligibility: Eligibility; roles: RoleSpec[] | null }
  | { type: 'open_failed'; phase: SessionPhase; failure: Failure | null }
  | { type: 'unauthorized' }
  | { type: 'parse_start' }
  | {
      type: 'parse_done';
      parsed: DatasetParsed;
      bytes: number;
      paste?: { text: string; source?: string };
      upload?: DatasetUpload;
      file?: ConvertedFile;
      /** The attachment's line: a new paste, which gets its item and a card of its own. */
      chip?: string;
      /** `.use()` of a table read from text: its item becomes the card. */
      fromTranscription?: boolean;
    }
  | { type: 'parse_failed'; failure: Failure }
  /**
   * The server answered a formula, code or a request for data (`422 formula`, `code`,
   * `data_request`): no error, the text goes to the chat as the user's turn.
   */
  | { type: 'parse_forwarded' }
  | { type: 'transcribed'; transcription: TranscriptionState; chip?: string }
  | { type: 'transcription_clear' }
  | { type: 'bindings_start'; bindings: BindingMap }
  | {
      type: 'bindings_done';
      bindings: BindingMap;
      complete: boolean;
      missingRoles: string[];
      /** The check's warnings (`checkWarnings`); none when absent. */
      warnings?: string[];
    }
  | { type: 'bindings_failed'; bindings: BindingMap; failure: Failure }
  | { type: 'confirm_start' }
  | { type: 'confirm_done' }
  | { type: 'confirm_failed'; failure: Failure }
  /** The server answered `not_ready` with `data_unconfirmed`: its confirmation is gone. */
  | { type: 'confirm_lost' }
  /** A turn's `done` named the session's bindings and step state; `null` fields were absent. */
  | { type: 'server_sync'; bindings: BindingMap | null; dataConfirmed: boolean | null }
  /**
   * A turn's `done` carried the data version the assistant's `prepare_data` made, or `.to_long()`
   * (`toLong`) made one from the card.
   */
  | { type: 'data_prepared'; dataset: DatasetChanged; toLong?: boolean }
  /** The admin fan-out's copy stored another session's confirmed data here, bound and confirmed. */
  | { type: 'data_copied'; dataset: DatasetCopied }
  | { type: 'to_long_start' }
  | { type: 'to_long_failed'; failure: Failure }
  | { type: 'undo_start' }
  | { type: 'undo_done'; parsed: DatasetParsed }
  | { type: 'undo_failed'; failure: Failure }
  | { type: 'library_start' }
  | {
      type: 'library_done';
      library: string;
      eligibility: Eligibility;
      target: PlotTarget;
      /** `null` from a server without the plot memory: no offer. */
      carry: SwitchCarry | null;
    }
  | { type: 'library_failed'; failure: Failure }
  /**
   * The plot memory as the server listed it, or as a removal left it. `afterTurn`: the read that
   * follows a turn's `done`, so a change of the list is that turn's.
   */
  | { type: 'memory_sync'; memory: PlotMemory; afterTurn?: boolean }
  /**
   * The latest memory read brought no list (it failed, or the server has no memory route), the one
   * after a turn's `done` or one that overtook it: the turn waits no longer, and keeps the mark its
   * `done` gave it.
   */
  | { type: 'memory_unread' }
  | { type: 'memory_busy'; busy: boolean }
  | { type: 'sheet_busy'; busy: boolean }
  /** A turn's `done` asked for a switch (`chatSwitch`), or the page took it (`null`). */
  | { type: 'chat_switch'; request: ChatSwitch | null }
  | { type: 'theme_busy'; busy: boolean }
  | { type: 'page_busy'; busy: boolean }
  | { type: 'language_start' }
  /**
   * The language route's answer: the stored form, source `chosen` from the chip, `offer` from
   * the `.switch()` of the offer line `offerId`.
   */
  | { type: 'language_done'; plotLanguage: PlotLanguage; offerId?: number }
  | { type: 'language_failed' }
  /**
   * A turn's `done` or a paste's answer named the session language, and with data the
   * `.to_long()` offer the server computed in it: the offer applies only with that language.
   * `offer`: a language the server found in the message or the data, which the thread offers.
   */
  | {
      type: 'language_sync';
      plotLanguage: PlotLanguage;
      suggestion?: LongSuggestion | null;
      offer?: LanguageOffer | null;
    }
  /**
   * The `.to_long()` offer as the server recomputed it in the session language
   * (a turn's `done`, the language route's answer): the card names what the
   * route applies, also after the language changed (live round 9).
   */
  | { type: 'suggestion_sync'; suggestion: LongSuggestion | null }
  /** Append a thread item; the reducer gives it the next id. */
  | { type: 'item'; item: NewChatItem }
  /**
   * A turn starts. `at` (ms since the epoch) starts its clock (`RunState.startedAt`): only a turn
   * the page starts carries it, never the late read of a cut turn, whose start the page never saw.
   */
  | { type: 'run_start'; kind: RunState['kind']; at?: number }
  | { type: 'run_queued'; position: number; waiting: number }
  /** The wait in the run queue is over; `at` starts the clock again, from the wait's end. */
  | { type: 'run_started'; at?: number }
  | {
      type: 'run_step';
      step: PipelineStep;
      attempt: number | null;
      previous?: Round | null;
      /** The run's round cap, when the server sent it with the step. */
      maxAttempts?: number | null;
    }
  | { type: 'run_stopping' }
  | { type: 'run_reconnecting'; on: boolean }
  /**
   * A turn ended: what it changed goes on its item when the user typed it; `null` for a turn that
   * did not reach its `done` (refused, failed, stopped), and for one whose server named an outcome
   * the page does not know while its stream showed no change: no mark, and no memory read waited for.
   */
  | { type: 'turn_outcome'; outcome: TurnOutcome | null }
  | { type: 'run_end' }
  /** A version shipped; `at` (ms since the epoch) freezes the run's clock into `readyMs`. */
  | { type: 'version_add'; version: PlotVersion; at?: number }
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
    transcription: null,
    roles: [],
    specRoles: null,
    bindings: {},
    bindingsComplete: false,
    missingRoles: [],
    bindingsBusy: false,
    bindingsError: null,
    bindingWarnings: null,
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
    carryOffer: null,
    memory: null,
    memoryBusy: false,
    sheetBusy: false,
    chatSwitch: null,
    themeBusy: false,
    pageBusy: false,
    // The server's default too, whatever the browser's locale: no answer needed to start.
    plotLanguage: { language: 'en', source: 'default' },
    languageBusy: false,
    items: [],
    nextItemId: 1,
    memoryTurn: null,
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

/** The binding check's warnings: an older server names none, and the answer is not typed. */
function checkWarnings(applied: BindingsApplied): string[] {
  const { warnings } = applied as { warnings?: unknown };
  return Array.isArray(warnings)
    ? warnings.filter((line): line is string => typeof line === 'string')
    : [];
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
 * the composer's step line names the change the card shows. Data that was never
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
      // The paste stays with every version made from it, so the table picker can still read another of
      // its tables; the picker itself shows only beside an answer that names `tables`, which only the
      // paste route gives.
      ...(state.dataset?.paste ? { paste: state.dataset.paste } : {}),
      // So does the workbook a version was read from, for the sheet picker: the server carries the file's
      // name on every version of that file's data, and on generated data, which no sheet made, it has none.
      ...(state.dataset?.file && parsed.file_name ? { file: state.dataset.file } : {}),
    },
    roles,
    bindings,
    bindingsComplete: missing.length === 0,
    missingRoles: missing,
    bindingsError: null,
    // No binding check answered for this version: its warnings are unknown until the next one.
    bindingWarnings: null,
    dataConfirmed: false,
    confirmError: null,
    confirmLoss: state.confirmLoss === null ? null : 'data',
    dataChange,
    undoBusy: false,
    undoError: null,
    toLongBusy: false,
    toLongError: null,
    // The server dropped the switch's carry with the new version: it was taken from a plot of the
    // data before (owner decision of 2026-11-08).
    carryOffer: null,
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

/**
 * The stub a data card leaves behind, under the id `id`: the shape of the data it showed
 * (`before`) and its snapshot. A paste or `.use()` freezes the card itself (`id` is the card's);
 * any other version splits a stub of a new id off the card, which goes on.
 */
function stubOf(
  card: Extract<ChatItem, { kind: 'data' }>,
  id: number,
  before: DatasetState | null
): ChatItem {
  return {
    id,
    kind: 'data_stub',
    rows: before?.parsed.profile.rows ?? 0,
    columns: before?.parsed.profile.columns.length ?? 0,
    ...(card.snapshot ? { snapshot: card.snapshot } : {}),
    card: card.id,
  };
}

/** The index of the latest item of `kind`, or -1. */
function lastIndexOf(items: ChatItem[], kind: ChatItem['kind']): number {
  for (let index = items.length - 1; index >= 0; index -= 1) {
    if (items[index].kind === kind) return index;
  }
  return -1;
}

/** A copy of `items` with `item` at `index`. */
function replaceAt(items: ChatItem[], index: number, item: ChatItem): ChatItem[] {
  const copy = [...items];
  copy[index] = item;
  return copy;
}

/**
 * The few words a data version's label carries: the file or `pasted` for a paste, the table or
 * the sheet a picker read, what the assistant or a card's control did.
 */
function versionSummary(
  change: DataVersionChange,
  dataset: DatasetState,
  state: AgentSessionState
): string {
  const { parsed } = dataset;
  switch (change) {
    case 'paste':
      return parsed.file_name ?? 'pasted';
    case 'transcription':
      return 'read from text';
    case 'table':
      return typeof parsed.table === 'number' ? `table ${parsed.table}` : 'another table';
    case 'sheet':
      return dataset.file?.sheet ? `sheet "${dataset.file.sheet}"` : 'another sheet';
    case 'turn':
      // The turn still runs when its `done` brings the version: `.example_data()` named its own.
      if (state.run?.kind === 'example_data') return 'example data';
      return state.dataset ? 'changed' : 'generated';
    case 'to_long':
      return 'made long';
    case 'undo':
      // The version it went back to, under its own number: `data v1 · back to v1`.
      return `back to v${dataVersionNumber(dataset)}`;
    case 'copy':
      return 'copied';
  }
}

/**
 * The number a data version carries on the page (`DataSnapshot.n`, the `3` of `data v3`): the
 * one place it comes from. Every label, the status line and the full view read it through the
 * snapshot. It is the server's own (owner decision of 2026-11-07): the session numbers every
 * version it stores once, never twice, and an undo brings the restored version's number back, so
 * "v2" on the card is the v2 the assistant's session block lists.
 */
function dataVersionNumber(dataset: DatasetState): number {
  return versionOf(dataset.parsed.version);
}

/**
 * How far an undo went back, for the `agent_data_undo` bucket: the restored version's place in
 * its data, the data's first version (its paste) being 1, counted from the server's
 * `original_version`. An older server names none, and its `version` is that place already.
 */
function undoDepth(parsed: DatasetParsed): number {
  const version = versionOf(parsed.version);
  const first = parsed.original_version;
  const valid =
    typeof first === 'number' && Number.isInteger(first) && first >= 1 && first <= version;
  return valid ? version - first + 1 : version;
}

/** The snapshot of the data version `next` holds, numbered `n` in the session. */
function snapshotOf(
  next: AgentSessionState,
  dataset: DatasetState,
  change: DataVersionChange,
  state: AgentSessionState
): DataSnapshot {
  const { parsed } = dataset;
  const n = dataVersionNumber(dataset);
  const summary = versionSummary(change, dataset, state);
  return {
    n,
    change,
    summary,
    label: `data v${n} · ${summary}`,
    rows: parsed.profile.rows,
    columns: parsed.profile.columns.length,
    sheet: dataset.file?.sheet ?? null,
    fileName: parsed.file_name ?? null,
    changes: next.dataChange?.kind === 'changed' ? next.dataChange.changes : [],
    preview: parsed.preview,
    profile: parsed.profile,
    // Only a paste's answer names it; a change, an undo or a copy never carries it.
    ...(parsed.columns_changed === true ? { columnsChanged: true as const } : {}),
  };
}

/**
 * Where a new data version stands in the thread (`next` is the state with it, `state` the one
 * before). Every version gets its item, numbered by `dataVersionNumber` (`data vN`), and the
 * thread reads in time order (owner, 2026-11-07):
 *
 * - A paste (`chip`, the attachment's line): the card it replaces freezes in place into a stub
 *   of the data it showed, and the paste's item and its own card follow at the end.
 * - `.use()` of a table read from text: the card before it freezes the same way, and the table's
 *   item turns into the card, at its place.
 * - A version a turn made: a stub of the version before takes the card's place, and the card goes
 *   on directly after that turn's message or action, before the reply to it, as a plot card
 *   stands before its reply. The version arrives with the turn's `done`, after the reply streamed
 *   in, so the card lands above text the user may be reading; the thread holds that text still
 *   (`HoldReadingPosition.tsx`). A second version of the same turn stays after its
 *   stub.
 * - A version the card's own controls made (`.undo()`, `.to_long()`, the table and sheet
 *   pickers), before or after a plot, and the fan-out's copy: the stub stays where the card
 *   stood, under the summary of its own version, and the card goes on at the thread's end, where
 *   a picker's summary follows it. The focus follows the card (`useFollowFocus.ts`).
 * - Data without a card yet: after the turn that made it (example data, a formula, code), else at
 *   the end (a copy).
 *
 * The card moves under its id, so it keeps its own state (notes, code) as it moves. Every item
 * has an id of its own (`nextItemId`), also where an undo gives a stub and the card one number.
 */
function placeData(
  state: AgentSessionState,
  next: AgentSessionState,
  change: DataVersionChange,
  chip?: string
): AgentSessionState {
  if (!next.dataset) return next;
  const snapshot = snapshotOf(next, next.dataset, change, state);
  const items = next.items;
  const live = lastIndexOf(items, 'data');
  const card = live >= 0 ? (items[live] as Extract<ChatItem, { kind: 'data' }>) : null;
  const waiting = change === 'transcription' ? lastIndexOf(items, 'transcription') : -1;
  if (chip !== undefined || waiting >= 0) {
    const frozen = card ? replaceAt(items, live, stubOf(card, card.id, state.dataset)) : items;
    if (chip === undefined) {
      const used: ChatItem = { id: frozen[waiting].id, kind: 'data', snapshot };
      return { ...next, items: replaceAt(frozen, waiting, used) };
    }
    const pasted = appendItem({ ...next, items: frozen }, { kind: 'paste', text: chip });
    return appendItem(pasted, { kind: 'data', snapshot });
  }
  // A turn's version goes directly after the turn's own item; any other at the end.
  const turn = change === 'turn' ? latestTurn(items) : null;
  if (!card) {
    if (!turn) return appendItem(next, { kind: 'data', snapshot });
    const added: ChatItem = { id: next.nextItemId, kind: 'data', snapshot };
    return {
      ...next,
      items: [...items.slice(0, turn.index + 1), added, ...items.slice(turn.index + 1)],
      nextItemId: next.nextItemId + 1,
    };
  }
  const stub = stubOf(card, next.nextItemId, state.dataset);
  const moved = { ...card, snapshot };
  // The stub where the card stood; the card after the turn's item when the turn came after the
  // card, after its own stub when the card already stands in that turn, else at the end.
  const rest = replaceAt(items, live, stub);
  const at = !turn ? rest.length : turn.index > live ? turn.index + 1 : live + 1;
  return {
    ...next,
    items: [...rest.slice(0, at), moved, ...rest.slice(at)],
    nextItemId: next.nextItemId + 1,
  };
}

/** Which data version a parse stored: a paste, `.use()`, or a picker's read of the same data again. */
function parseChange(
  state: AgentSessionState,
  action: Extract<Action, { type: 'parse_done' }>
): DataVersionChange {
  if (action.chip !== undefined) return 'paste';
  if (action.fromTranscription) return 'transcription';
  // The fan-out's replay posts an upload into a session without data: the paste it came from.
  if (!state.dataset) return 'paste';
  const sheet = action.file?.sheet;
  return sheet && sheet !== state.dataset.file?.sheet ? 'sheet' : 'table';
}

/** The latest turn's item, a typed message or an action, with its index; null without one. */
function latestTurn(items: ChatItem[]): { index: number; item: ChatItem } | null {
  for (let index = items.length - 1; index >= 0; index -= 1) {
    const item = items[index];
    if (item.kind === 'user' || item.kind === 'action') return { index, item };
  }
  return null;
}

/**
 * The memory read after a turn's `done` found another list than before: a turn read as an
 * answer (nothing in its stream changed) did change the memory, a decision kept for the first
 * plot (`keep_plot_request`) or one it forgot. The mark of that turn's item (`turn`, the
 * reducer's `memoryTurn`) moves from `answer` to what it changed. The item is named by its id,
 * since the read can land while the next turn runs, such as the summary after a paste's note.
 */
function memoryOutcome(
  items: ChatItem[],
  turn: number | null,
  before: PlotMemory | null,
  after: PlotMemory
): ChatItem[] {
  const index = turn === null ? -1 : items.findIndex(item => item.id === turn);
  const item = index >= 0 ? items[index] : null;
  if (item?.kind !== 'user' || item.outcome !== 'answer') return items;
  const old = new Set((before?.entries ?? []).map(entry => entry.id));
  const ids = after.entries.map(entry => entry.id);
  if (ids.length === old.size && ids.every(id => old.has(id))) return items;
  const outcome: TurnOutcome = ids.some(id => !old.has(id)) ? 'kept' : 'memory';
  return replaceAt(items, index, { ...item, outcome });
}

/**
 * The latest switch item, its count following the memory while its offer stands
 * (`carryDecisions`): a removal from the list counts the switch's decisions down, as it does the
 * plot button's.
 */
function switchDecisions(items: ChatItem[], next: AgentSessionState): ChatItem[] {
  const offer = next.carryOffer;
  const index = lastIndexOf(items, 'switch');
  const item = index >= 0 ? items[index] : null;
  if (!offer || item?.kind !== 'switch' || item.library !== offer.target.library) return items;
  const decisions = carryDecisions(offer, next.memory);
  return decisions === item.decisions ? items : replaceAt(items, index, { ...item, decisions });
}

/** The ladder of the language sources: the server only ever climbs it within a session. */
const SOURCE_RANK: Record<LanguageSource, number> = {
  default: 0,
  offer: 1,
  chosen: 2,
};

/**
 * The thread with its language lines settled after a pick: the offer line `accepted` (the
 * `.switch()` the user pressed) names the language it set, and every other open one closes,
 * since the user picked. With no line accepted (the chip, a request in the chat), all close.
 */
function settleOffers(
  items: ChatItem[],
  picked: PlotLanguage,
  plot: boolean,
  accepted?: number
): ChatItem[] {
  let changed = false;
  const next = items.map(item => {
    if (item.kind !== 'language_offer' || item.state !== 'open') return item;
    changed = true;
    if (item.id === accepted && sameLanguage(item.language, picked.language)) {
      return { ...item, state: 'accepted' as const, plot };
    }
    return { ...item, state: 'closed' as const };
  });
  return changed ? next : items;
}

/** Whether the thread already offered `language`: the server offers each once, the page shows it once. */
const offeredBefore = (items: ChatItem[], language: string) =>
  items.some(item => item.kind === 'language_offer' && sameLanguage(item.language, language));

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
 * drops, whatever action dropped it, the reducer keeps the reason for the step
 * lines (`stepOneLine`, the card's own line), which say what dropped it and
 * end with the plot button's name. It appends no notice to the thread: every
 * state a loss leaves is step 1 with data, where the step line, the plot
 * button's description, says the same. A confirmation clears the reason. A
 * first binding setup after a paste lands while the flag is already clear, so
 * it names nothing. While the flag stays clear the reason follows the data
 * (`reduce`): a new paste clears it, a data change or an undo makes it `data`.
 */
export function agentReducer(state: AgentSessionState, action: Action): AgentSessionState {
  const next = reduce(state, action);
  if (state.dataConfirmed && !next.dataConfirmed) {
    return { ...next, confirmLoss: lossOf(state, action) };
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
        specRoles: action.roles,
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
        transcription: null,
        toLongError: null,
      };
    case 'parse_done':
      return placeData(
        state,
        {
          ...state,
          parsing: false,
          // A paste starts over at version 1: the server dropped the undo history with it.
          dataset: {
            parsed: { ...action.parsed, version: versionOf(action.parsed.version) },
            bytes: action.bytes,
            ...(action.paste ? { paste: action.paste } : {}),
            ...(action.upload ? { upload: action.upload } : {}),
            ...(action.file ? { file: action.file } : {}),
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
          // The parse's own binding call names them next.
          bindingWarnings: null,
          // A new dataset is unchecked: the server dropped its confirmation when it stored it.
          dataConfirmed: false,
          confirmError: null,
          // And it starts over: a loss named for the data before it is not its own. A paste
          // that drops a confirmation the user had given is named by `agentReducer`.
          confirmLoss: null,
          // The server dropped the switch's carry with the paste, as with every new data version.
          carryOffer: null,
        },
        parseChange(state, action),
        action.chip
      );
    case 'parse_failed':
      return { ...state, parsing: false, datasetError: action.failure, transcription: null };
    case 'parse_forwarded':
      // No failure of the data: the chat takes the text instead.
      return { ...state, parsing: false, datasetError: null, transcription: null };
    case 'transcribed': {
      // Nothing is stored yet: the dataset, its bindings and their confirmation stay until
      // the user decides (the server kept them too); the page holds step 1 while the
      // transcription waits (`inStep2`), and `.discard()` returns to where the user was.
      // The paste and the table read from it follow in the thread; the card above stays live.
      const next = { ...state, parsing: false, transcription: action.transcription };
      const pasted = action.chip ? appendItem(next, { kind: 'paste', text: action.chip }) : next;
      return appendItem(pasted, { kind: 'transcription' });
    }
    case 'transcription_clear': {
      // `.discard()`: the table read from text leaves a line where it waited.
      const items = [...state.items];
      const waiting = lastIndexOf(items, 'transcription');
      if (waiting >= 0)
        items[waiting] = { id: items[waiting].id, kind: 'notice', text: 'table discarded' };
      return { ...state, transcription: null, items };
    }
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
        bindingWarnings: action.warnings ?? [],
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
          // The root's `set_bindings` came without the check's warnings: unknown until the next one.
          ...(sameBindings(action.bindings, state.bindings) ? {} : { bindingWarnings: null }),
        };
      }
      if (action.dataConfirmed !== null) next = { ...next, dataConfirmed: action.dataConfirmed };
      return next;
    }
    case 'data_prepared': {
      const { changes, version, ...parsed } = action.dataset;
      return placeData(
        state,
        withDataVersion(
          state,
          { ...parsed, version },
          { kind: 'changed', changes, version: versionOf(version) }
        ),
        action.toLong ? 'to_long' : 'turn'
      );
    }
    case 'data_copied': {
      const { dataset } = action;
      return placeData(
        state,
        {
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
          bindingWarnings: null,
          // The server confirmed the copy with the bindings the page session confirmed.
          dataConfirmed: true,
          confirmError: null,
        },
        'copy'
      );
    }
    case 'to_long_start':
      return { ...state, toLongBusy: true, toLongError: null };
    case 'to_long_failed':
      return { ...state, toLongBusy: false, toLongError: action.failure };
    case 'undo_start':
      return { ...state, undoBusy: true, undoError: null };
    case 'undo_done':
      return placeData(
        state,
        withDataVersion(state, action.parsed, {
          kind: 'undone',
          version: versionOf(action.parsed.version),
        }),
        'undo'
      );
    case 'undo_failed':
      return { ...state, undoBusy: false, undoError: action.failure };
    case 'library_start':
      return { ...state, libraryBusy: true };
    case 'library_done': {
      // The dataset, its bindings and their confirmation stay, as on the server. The answer's
      // offer replaces any earlier one: a switch without an offer ends it.
      const carryOffer: CarryOffer | null = action.carry?.offer
        ? {
            target: action.target,
            decisions: action.carry.decisions,
            memoryBacked: (state.memory?.entries.length ?? 0) > 0,
          }
        : null;
      // The switch is an item of its own, with what the plot in the new library takes over.
      return appendItem(
        {
          ...state,
          libraryBusy: false,
          library: action.library,
          eligibility: action.eligibility,
          transcription: null,
          carryOffer,
        },
        {
          kind: 'switch',
          from: state.library,
          library: action.library,
          decisions: carryOffer ? carryDecisions(carryOffer, state.memory) : null,
        }
      );
    }
    case 'library_failed':
      return { ...state, libraryBusy: false };
    case 'memory_sync': {
      const next = {
        ...state,
        memory: action.memory,
        // A list that arrives after the switch (its read was still in flight) backs the offer's count
        // too, so a removal counts the composer's decisions down.
        carryOffer:
          state.carryOffer && action.memory.entries.length > 0
            ? { ...state.carryOffer, memoryBacked: true }
            : state.carryOffer,
      };
      // Only the read after a turn's `done` speaks for that turn: a removal the user clicked
      // changes the list too, and no turn of theirs. Any list ends the wait, so a later read,
      // which compares with this one, never speaks for the turn.
      const items = action.afterTurn
        ? memoryOutcome(state.items, state.memoryTurn, state.memory, action.memory)
        : state.items;
      // A version's added decisions get their texts from the read after its turn, and any text a
      // read before missed from the first list that names it.
      return {
        ...next,
        items: switchDecisions(items, next),
        memoryTurn: null,
        versions: resolveDecisions(state.versions, action.memory),
      };
    }
    case 'memory_unread':
      return state.memoryTurn === null ? state : { ...state, memoryTurn: null };
    case 'memory_busy':
      return { ...state, memoryBusy: action.busy };
    case 'sheet_busy':
      return { ...state, sheetBusy: action.busy };
    case 'chat_switch':
      return { ...state, chatSwitch: action.request };
    case 'theme_busy':
      return { ...state, themeBusy: action.busy };
    case 'page_busy':
      return { ...state, pageBusy: action.busy };
    case 'language_start':
      return { ...state, languageBusy: true };
    case 'language_done': {
      // A pick: the chip's closes every open offer line, a `.switch()` turns its own line into
      // the language it set. A plot on screen keeps its text until its next version.
      const picked = action.plotLanguage;
      const plot = Object.keys(state.versions).length > 0;
      const items = settleOffers(state.items, picked, plot, action.offerId);
      return { ...state, languageBusy: false, plotLanguage: picked, items };
    }
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
      const after = action.plotLanguage;
      // The assistant's `set_language` is a pick like the chip's: the open offer lines close.
      const items =
        after.source === 'chosen'
          ? settleOffers(synced.items, after, Object.keys(state.versions).length > 0)
          : synced.items;
      const next = { ...synced, plotLanguage: after, items };
      const offer = action.offer;
      // A language found in the message or the data: one line that offers it, once per
      // language, never after a pick and never for the language the session has.
      if (
        offer &&
        after.source !== 'chosen' &&
        !sameLanguage(offer.language, after.language) &&
        !offeredBefore(next.items, offer.language)
      ) {
        return appendItem(next, {
          kind: 'language_offer',
          language: offer.language,
          basis: offer.basis,
          state: 'open',
        });
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
      return {
        ...state,
        run: {
          kind: action.kind,
          steps: [],
          queue: null,
          stopping: false,
          ...(action.at !== undefined ? { startedAt: action.at } : {}),
        },
      };
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
    case 'run_started': {
      // The wait is over: a turn without pipeline steps (a summary that runs data code) had its
      // queue position on screen until the reply. A plot run that has not reached its first step
      // is starting again (`starting…`). A replayed start after a resume changes nothing more.
      // The clock starts again at the wait's end, for a timed run that waited: a run the page did
      // not time stays without a clock, and a replayed start finds no wait to end.
      if (!state.run) return state;
      const waited = state.run.steps.some(entry => entry.step === 'queued');
      const restart =
        waited && state.run.startedAt !== undefined && action.at !== undefined
          ? { startedAt: action.at }
          : {};
      return {
        ...state,
        run: {
          ...state.run,
          ...restart,
          queue: null,
          steps: state.run.steps.filter(entry => entry.step !== 'queued'),
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
          ...(action.maxAttempts ? { maxAttempts: action.maxAttempts } : {}),
        },
      };
    case 'run_stopping':
      return state.run ? { ...state, run: { ...state.run, stopping: true } } : state;
    case 'run_reconnecting':
      return state.run ? { ...state, run: { ...state.run, reconnecting: action.on } } : state;
    case 'turn_outcome': {
      // The turn's own item is the latest: no other turn starts before its end, and the late read
      // of a cut turn adds none, so its outcome lands on the cut turn's item.
      const turn = latestTurn(state.items);
      const unwaited = state.memoryTurn === null ? state : { ...state, memoryTurn: null };
      if (turn?.item.kind === 'action') {
        // The summary and example data cannot change the memory: a question's read still in flight
        // speaks for the question. Any other action ends the wait, since its own read compares
        // with the list it changed.
        const keeps = turn.item.action === 'summarize_data' || turn.item.action === 'example_data';
        return keeps ? state : unwaited;
      }
      if (turn?.item.kind !== 'user' || action.outcome === null) return unwaited;
      const marked: ChatItem = { ...turn.item, outcome: action.outcome };
      return {
        ...state,
        items: replaceAt(state.items, turn.index, marked),
        // Only a question waits for its memory read: anything else it changed is named already.
        memoryTurn: action.outcome === 'answer' ? turn.item.id : null,
      };
    }
    case 'run_end':
      return { ...state, run: null };
    case 'version_add': {
      // The version's decisions, by the server's ids: the kept ones from before the run are in the
      // list the page holds; the added ones come with the read after the turn (`memory_sync`).
      const memory = action.version.result.memory;
      // The run's clock, frozen as the version arrives; a run the page did not time gives none.
      const startedAt = state.run?.startedAt;
      const timed =
        startedAt !== undefined && action.at !== undefined
          ? { readyMs: Math.max(0, action.at - startedAt) }
          : {};
      const version = {
        ...action.version,
        ...timed,
        ...(memory ? { decisions: versionDecisions(memory, state.memory) } : {}),
      };
      // A shipped plot in the offer's library ends the offer, whichever turn shipped it (the carry
      // run, a fresh `.create_plot()`, a typed change): the server's carry is spent then too.
      // Versions carry their library, not their spec; the spec cannot change yet.
      return {
        ...state,
        versions: { ...state.versions, [version.number]: version },
        carryOffer:
          state.carryOffer?.target.library === action.version.library ? null : state.carryOffer,
      };
    }
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
  /** The waits before each read of a cut turn; `RESUME_DELAYS_MS` unless a test needs them short. */
  resumeDelaysMs?: readonly number[];
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
  // The whole service paused for the day: its day budget is spent, not the user's own.
  'service_paused',
]);

/** The paste route's guard refusals (HTTP errors, not stream refusals) that count as guardrail blocks. */
const PASTE_GUARDRAIL_REASONS = new Set([
  'data_refused',
  'rate_limited',
  'daily_limit',
  'service_paused',
  'locked_out',
  'session_closed',
]);

function failureOf(err: unknown): Failure {
  if (err instanceof AgentApiError) {
    return {
      code: err.code,
      ref: err.shownRef,
      ...(err.errors.length ? { errors: err.errors } : {}),
      ...(err.cause ? { cause: err.cause } : {}),
    };
  }
  return { code: 'network', ref: null };
}

const isAbort = (err: unknown) => err instanceof DOMException && err.name === 'AbortError';

/** The server refused the run because it holds no confirmation: no round ran, no plot was made. */
const unconfirmedPlot = (result: PlotResult) =>
  result.status === 'not_ready' && result.reason === 'data_unconfirmed';

export function useAgentSession({
  specId,
  library,
  locale,
  token,
  fanout = false,
  resumeDelaysMs = RESUME_DELAYS_MS,
}: UseAgentSessionOptions) {
  const [state, dispatch] = useReducer(agentReducer, library, initialAgentState);
  const { trackEvent } = useAnalytics();
  const { effective: siteTheme } = useTheme();

  // Values async callbacks read after an await; refs, so a stale closure never
  // acts on a previous session.
  const stateRef = useRef(state);
  stateRef.current = state;
  const siteThemeRef = useRef<Theme>(siteTheme);
  siteThemeRef.current = siteTheme;
  const abortRef = useRef<AbortController | null>(null);
  const stoppedRef = useRef(false);
  const turnErrorRef = useRef<string | null>(null);
  // How the last turn ended (`runTurn`), null when it never started: a parse reports it for
  // the turn it started (`ParseResult.turnEnd`).
  const turnEndRef = useRef<TurnEnd | null>(null);
  // The code of the refusal that ended the last turn, if one did (`out_of_scope`, `needs_data`, ...).
  const turnRefusalRef = useRef<string | null>(null);
  // The turn's plot answered `data_unconfirmed`: the confirmation drops once the turn is over (`runTurn`).
  const unconfirmedRef = useRef(false);
  // The last turn, when its stream was cut and every read of it again failed: the next turn reads it first.
  const cutTurnRef = useRef<CutTurn | null>(null);
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Set synchronously, before the state catches up, so a double click starts nothing twice.
  const themeRef = useRef(false);
  const pageRef = useRef(false);
  const parseRef = useRef(false);
  // The fan-out's copy took the page session's tuning over: its plot is the carry run (`plotTurn`).
  const copyCarryRef = useRef(false);
  const confirmRef = useRef(false);
  const undoRef = useRef(false);
  // The parse's own binding call ends right before its summary turn starts,
  // sooner than the state can say so.
  const bindingsRef = useRef(false);
  const saveRef = useRef(false);
  const languageRef = useRef(false);
  const memoryRef = useRef(false);
  const sheetRef = useRef(false);
  // Counts the memory lists asked for and answered: a read overtaken by a newer one is dropped.
  const memorySeq = useRef(0);
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
   * confirmation, an undo, a library switch, a language choice or a removal
   * from the plot memory is in flight.
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
      memoryRef.current ||
      sheetRef.current ||
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
          roles: result.roles,
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const failure = failureOf(err);
        if (err instanceof AgentApiError && err.unauthorized) {
          safeDispatch({ type: 'unauthorized' });
        } else if (failure.code === 'not_eligible') {
          safeDispatch({ type: 'open_failed', phase: 'ineligible', failure });
        } else {
          // No reload for an expired Access session: the chat at `/agent` is not behind Access,
          // whose sign-in only a page under `/debug` gets; the page checked the admin before
          // it opened this session (`useAgentAdmin`), and the error offers a reload.
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
          warnings: checkWarnings(applied),
        });
      } catch (err) {
        safeDispatch({ type: 'bindings_failed', bindings: previous, failure: handleFailure(err) });
      } finally {
        bindingsRef.current = false;
      }
    },
    [token, safeDispatch, handleFailure]
  );

  /**
   * The server's binding check again on the bindings in force, which it holds already: the same
   * set, so nothing changes there and it counts as no change by hand (`main.put_bindings`). The
   * answer names `complete`, the open roles and the warnings a turn's new data version or
   * `set_bindings` brought without a check (`bindingWarnings` `null`). Resolves to whether the
   * check ran: nothing starts without data, while a table read from text waits, or while
   * anything else is in flight.
   */
  const checkBindings = useCallback(async (): Promise<boolean> => {
    const current = stateRef.current;
    if (!current.dataset || current.transcription || current.run || busy()) return false;
    await applyBindings(current.bindings, current.bindings);
    return true;
  }, [applyBindings, busy]);

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

  /**
   * Bind `name` (a single role or a family member such as `y2`) to `column`, or clear it with `null`.
   * A column may serve several roles (owner decision of 2026-11-04: the y and the size of a
   * bubble), so another role that holds it keeps it. Inside one variadic family it stays once,
   * as the server's binding check has it: the same series twice is never meant. The member that
   * held it takes this member's column instead, so the two swap and both series stay (owner
   * decision of 2026-11-05: `y1` Sales and `y2` Cost, `y2` set to Sales, gives `y1` Cost); a
   * member without a column (the next member, which `+ y` binds) has nothing to give, so the
   * column moves and the family closes up.
   */
  const setBinding = useCallback(
    (name: string, column: string | null) => {
      if (busy()) return;
      const { bindings: current, roles } = stateRef.current;
      const next: Record<string, string | null> = { ...current };
      const family = familyOf(name, roles);
      if (column && family) {
        for (const [other, held] of Object.entries(next)) {
          if (other !== name && held === column && familyOf(other, roles)?.name === family.name) {
            next[other] = current[name] ?? null;
          }
        }
      }
      next[name] = column;
      void applyBindings(compactFamilies(next, roles), current);
    },
    [applyBindings, busy]
  );

  /**
   * The end of step 1, the first link of the page's `.create_plot()` (and of the carry and
   * `.plot_all()`) on unconfirmed data, also where the plot button's one click goes on by itself
   * after reading the box's data clean (`plotChain.ts`): the server marks the stored dataset and its current
   * bindings as checked, which a plot run needs. Resolves to whether the data is confirmed now,
   * so the caller starts the plot only then; a refusal lands in `confirmError`. Nothing starts
   * without a stored dataset, while a table read from text waits for its decision, or while
   * anything else is in flight (a second click before the state caught up).
   */
  const confirmData = useCallback(async (): Promise<boolean> => {
    const current = stateRef.current;
    const sid = current.sessionId;
    const dataset = current.dataset;
    if (!sid || !dataset || current.transcription || current.run || busy()) return false;
    confirmRef.current = true;
    safeDispatch({ type: 'confirm_start' });
    try {
      await agentApi.confirmDataset(token, sid);
      safeDispatch({ type: 'confirm_done' });
      trackEvent('agent_data_confirmed', { size_bucket: sizeBucket(dataset.bytes) });
      return true;
    } catch (err) {
      safeDispatch({ type: 'confirm_failed', failure: handleFailure(err) });
      return false;
    } finally {
      confirmRef.current = false;
    }
  }, [token, safeDispatch, handleFailure, trackEvent, busy]);

  /**
   * `.undo()`: the version before the assistant's last change to the data is
   * the current dataset again, unconfirmed (`POST .../dataset/undo`). Nothing
   * starts while the server's answer says there is nothing to undo (`can_undo`,
   * false at a paste), after it refused an undo for that, or while anything
   * else is in flight.
   */
  const undoData = useCallback(async () => {
    const current = stateRef.current;
    const sid = current.sessionId;
    const undoable = current.dataset?.parsed.can_undo === true;
    if (!sid || !undoable || current.undoError?.code === 'nothing_to_undo') return;
    if (current.run || busy()) return;
    undoRef.current = true;
    safeDispatch({ type: 'undo_start' });
    try {
      const parsed = await agentApi.undoDataset(token, sid);
      safeDispatch({ type: 'undo_done', parsed });
      trackEvent('agent_data_undo', { version: countBucket(undoDepth(parsed)) });
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
      safeDispatch({ type: 'data_prepared', dataset, toLong: true });
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
        // The page session's tuning came along (its plot memory, a carry for this library): the
        // fan-out's plot takes it over (`plotTurn`), as the carry run after a switch does.
        copyCarryRef.current = dataset.carry?.offer === true;
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
          warnings: checkWarnings(applied),
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

  // `.view_all()`: the current data version's canonical CSV, read-only; the view keeps it, the session state does not.
  const fetchDataCsv = useCallback(
    async (signal?: AbortSignal): Promise<string> => {
      const sid = stateRef.current.sessionId;
      if (!sid) throw new AgentApiError(0, 'no_session');
      return agentApi.datasetCsv(token, sid, signal);
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

  /**
   * The sheet picker's read: the workbook converted again on the server for another sheet. It is
   * work in flight like a parse (`busy()`, `sheetBusy`), so nothing confirms, plots or sends while
   * it runs, and it ends before the page parses its answer, which a busy session would skip. While
   * something else runs it starts nothing (`run_active`).
   */
  const readSheet = useCallback(
    async (dataBase64: string, sheet?: string): Promise<ConvertAnswer> => {
      if (busy()) throw new AgentApiError(409, 'run_active');
      sheetRef.current = true;
      safeDispatch({ type: 'sheet_busy', busy: true });
      try {
        return await convertFile(dataBase64, sheet);
      } finally {
        sheetRef.current = false;
        safeDispatch({ type: 'sheet_busy', busy: false });
      }
    },
    [busy, convertFile, safeDispatch]
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

  // ---------------------------------------------------------------- plot memory

  /**
   * Read the plot memory again (`GET .../memory`). Best effort: a failure, or a
   * server without the route, leaves the list as it was, and an answer that a
   * newer read or a removal overtook is dropped. The fan-out's sessions show no
   * list, so they read none. `afterTurn`: the read after a turn's `done`, whose
   * change of the list is that turn's (`memory_sync`). When the latest read brings
   * no list, also one that overtook the turn's own (a switch's), the turn waits
   * no longer (`memory_unread`) and keeps the mark its `done` gave it, a question
   * then on the server's word and the stream's alone.
   */
  const refreshMemory = useCallback(
    async (afterTurn = false) => {
      const sid = stateRef.current.sessionId;
      if (!sid || openedForFanOut.current) {
        if (afterTurn) safeDispatch({ type: 'memory_unread' });
        return;
      }
      memorySeq.current += 1;
      const seq = memorySeq.current;
      try {
        const memory = await agentApi.memory(token, sid);
        if (seq === memorySeq.current) {
          safeDispatch({ type: 'memory_sync', memory, ...(afterTurn ? { afterTurn } : {}) });
        }
      } catch {
        // Best effort: the list stays as it was. The latest read failing ends a turn's wait,
        // whichever read it is: a newer one (a switch's) drops the turn's own answer, so its failure
        // is the last word. A read a newer one or a removal overtook leaves the wait to that one.
        if (seq === memorySeq.current) safeDispatch({ type: 'memory_unread' });
      }
    },
    [token, safeDispatch]
  );

  /**
   * `.forget()` on a remembered decision (`DELETE .../memory/{id}`): the list
   * becomes the server's answer. The plot does not change; the next plot no
   * longer takes the decision over. Nothing starts without a session or while
   * anything else is in flight, which the server would refuse with `409
   * run_active`. A failure rejects with an `AgentApiError` for the list's
   * failure line; `not_found` (the entry is gone already, by the assistant's
   * `forget` or another window) reads the list again first.
   */
  const forgetMemory = useCallback(
    async (entryId: string): Promise<void> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy()) return;
      memoryRef.current = true;
      safeDispatch({ type: 'memory_busy', busy: true });
      try {
        const memory = await agentApi.forgetMemory(token, sid, entryId);
        memorySeq.current += 1;
        safeDispatch({ type: 'memory_sync', memory });
      } catch (err) {
        const failure = handleFailure(err);
        if (failure.code === 'not_found') void refreshMemory();
        throw err instanceof AgentApiError ? err : new AgentApiError(0, failure.code);
      } finally {
        memoryRef.current = false;
        safeDispatch({ type: 'memory_busy', busy: false });
      }
    },
    [token, safeDispatch, handleFailure, busy, refreshMemory]
  );

  /**
   * `.forget_all()` on the remembered list (`DELETE .../memory`): every
   * decision goes, for a blank start. Nothing else clears the memory,
   * `.start_over()` included. A failure rejects with an `AgentApiError` for
   * the list's failure line.
   */
  const forgetAllMemory = useCallback(async (): Promise<void> => {
    const current = stateRef.current;
    const sid = current.sessionId;
    if (!sid || current.run || busy()) return;
    memoryRef.current = true;
    safeDispatch({ type: 'memory_busy', busy: true });
    try {
      const memory = await agentApi.forgetAllMemory(token, sid);
      memorySeq.current += 1;
      safeDispatch({ type: 'memory_sync', memory });
    } catch (err) {
      const failure = handleFailure(err);
      throw err instanceof AgentApiError ? err : new AgentApiError(0, failure.code);
    } finally {
      memoryRef.current = false;
      safeDispatch({ type: 'memory_busy', busy: false });
    }
  }, [token, safeDispatch, handleFailure, busy]);

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
      if (unconfirmedPlot(result)) {
        // The server holds no confirmation: the next `.create_plot()` confirms again instead of
        // starting a run the server refuses. The turn's `done` sync normally says so as well, and
        // a data change of this turn comes only with it, so the flag drops at the turn's end, where
        // that change names the loss. No thread item: the step line says what to do.
        unconfirmedRef.current = true;
        return;
      }
      if (result.status !== 'ok' && result.status !== 'needs_attention') {
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
        at: Date.now(),
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
        case 'started':
          safeDispatch({ type: 'run_started', at: Date.now() });
          break;
        case 'step':
          safeDispatch({
            type: 'run_step',
            step: event.step,
            attempt: event.attempt,
            previous: event.previous,
            maxAttempts: event.maxAttempts,
          });
          break;
        case 'message':
          addItem({ kind: 'assistant', text: event.text });
          break;
        case 'plot':
          onPlot(event.result);
          break;
        case 'refusal':
          addItem({
            kind: 'refusal',
            code: event.code,
            text: event.text,
            ...(event.code === 'service_paused' ? { until: nextUtcMidnight() } : {}),
          });
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
          // The assistant's `set_language` (`chosen`) may have set the session language: the
          // chip follows the server, and a language found in the message comes as its offer.
          // The `.to_long()` offer travels with the language the server computed it in, and applies
          // only when that language does: a `done` the chip ignores never renames the card.
          if (event.language) {
            safeDispatch({
              type: 'language_sync',
              plotLanguage: event.language,
              suggestion: event.suggestion,
              offer: event.languageOffer,
            });
          }
          // The user asked for the plot in another library: the page switches once the turn is over.
          if (event.switch) safeDispatch({ type: 'chat_switch', request: event.switch });
          break;
        default:
          break;
      }
    },
    [safeDispatch, addItem, onPlot, trackEvent]
  );

  /**
   * Read a turn's events from `response` into the thread and into `read`: `done` once the turn's
   * `done` arrived, `ended` for a stream that ended without it, `cut` for one whose read failed (a
   * browser reports a lost connection as a `TypeError` from the body). A failure of the page's own
   * handling of an event is no cut: it throws, as any other failure does.
   */
  const consume = useCallback(
    async (
      response: Response,
      read: TurnRead,
      signal: AbortSignal
    ): Promise<'done' | 'ended' | 'cut'> => {
      if (!response.body) throw new AgentApiError(502, 'upstream');
      let handling = false;
      try {
        for await (const raw of readSseEvents(response.body, signal)) {
          handling = true;
          if (raw.id) read.lastId = raw.id;
          const event = parseAgentEvent(raw);
          if (event) {
            // What the turn changed is read against the state before the event: the reducer has
            // not rendered the event's own changes into `stateRef` yet.
            const before = stateRef.current;
            onEvent(event);
            if (event.type === 'error') read.errorCode = event.code;
            // A refusal arrives as an event of its own; the stream then ends with `done` as usual.
            if (event.type === 'refusal') {
              read.refused = true;
              read.refusalCode = event.code;
            }
            // A plot the server refused for unconfirmed data ran no round: the turn made no plot.
            if (event.type === 'plot' && !unconfirmedPlot(event.result)) {
              read.plotted = true;
              if (event.result.status === 'ok' || event.result.status === 'needs_attention') {
                read.shipped = true;
              }
            }
            if (event.type === 'done') {
              read.finished = true;
              noteDone(read, event, before);
              return 'done';
            }
          }
          handling = false;
        }
      } catch (err) {
        if (handling || !(err instanceof TypeError)) throw err;
        return 'cut';
      }
      return 'ended';
    },
    [onEvent]
  );

  /**
   * Read the rest of a turn whose stream was cut, after each of `delays`, from the last id `read`
   * holds, until a read reaches `done`. A read that is cut again goes on from where it stopped.
   * Null when the turn's controller aborted meanwhile (the page unmounted, or a stop the server
   * did not hear); else how it ended, with what the server answered when it refused the read. A
   * read that reaches `done` after the BFF's `upstream` error (the agents service saw the turn's
   * stream end early and cancelled it, so the turn has no result) counts as `failed`: there was
   * nothing left to read, and reading again would not bring it.
   */
  const reattach = useCallback(
    async (
      sid: string,
      read: TurnRead,
      controller: AbortController,
      delays: readonly number[]
    ): Promise<{ outcome: ResumeOutcome; failure: Failure | null } | null> => {
      safeDispatch({ type: 'run_reconnecting', on: true });
      try {
        for (const delay of delays) {
          await pause(delay, controller.signal);
          if (controller.signal.aborted || !read.lastId) return null;
          try {
            const response = await agentApi.resumeTurn(token, sid, read.lastId, controller.signal);
            safeDispatch({ type: 'run_reconnecting', on: false });
            const before = read.errorCode;
            await consume(response, read, controller.signal);
            if (read.finished) {
              const lost = read.errorCode === 'upstream' && before !== 'upstream';
              return { outcome: lost ? 'failed' : 'resumed', failure: null };
            }
          } catch (err) {
            if (isAbort(err)) return null;
            // Another turn is the latest (or the session is gone): there is nothing left to read.
            if (err instanceof AgentApiError && err.status === 404) {
              return { outcome: 'gone', failure: failureOf(err) };
            }
            // A refusal that a later read would get again (a sign-in the page lost, say).
            if (
              err instanceof AgentApiError &&
              err.status >= 400 &&
              err.status < 500 &&
              err.status !== 429
            ) {
              return { outcome: 'failed', failure: handleFailure(err) };
            }
            // No answer, a busy service or a stream cut again: the next read.
          }
          safeDispatch({ type: 'run_reconnecting', on: true });
        }
        return { outcome: 'failed', failure: null };
      } finally {
        safeDispatch({ type: 'run_reconnecting', on: false });
      }
    },
    [token, consume, safeDispatch, handleFailure]
  );

  /**
   * The frame of a turn on the page: the run from the start, Stop, and at the end how the turn
   * ended (`turnErrorRef`, `turnRefusalRef`, `turnEndRef`) and, after a `done`, the plot memory as
   * the server has it. `work` reads the turn into `read`; a failure it throws becomes the turn's
   * error line, unless the user stopped the turn. `timed`: the page starts the turn now, so its
   * clock starts too; the late read of a cut turn is not, whose start the page never saw.
   */
  const driveTurn = useCallback(
    async (
      kind: RunState['kind'],
      work: (controller: AbortController, read: TurnRead) => Promise<void>,
      timed = true
    ): Promise<TurnRead> => {
      const read = freshRead();
      const controller = new AbortController();
      abortRef.current = controller;
      stoppedRef.current = false;
      unconfirmedRef.current = false;
      safeDispatch(
        timed ? { type: 'run_start', kind, at: Date.now() } : { type: 'run_start', kind }
      );
      try {
        await work(controller, read);
      } catch (err) {
        if (!stoppedRef.current && !isAbort(err)) {
          const failure = handleFailure(err);
          addItem({ kind: 'error', code: failure.code, ref: failure.ref });
          read.errorCode = failure.code;
        }
      } finally {
        if (stopTimer.current) clearTimeout(stopTimer.current);
        stopTimer.current = null;
        if (stoppedRef.current) addItem({ kind: 'notice', text: 'stopped' });
        if (abortRef.current === controller) abortRef.current = null;
        turnErrorRef.current = read.errorCode;
        turnRefusalRef.current = read.refusalCode;
        // A stream aborted for another reason (the page unmounted) did not end: no `done`.
        turnEndRef.current = stoppedRef.current
          ? 'stopped'
          : read.errorCode
            ? 'error'
            : read.refused
              ? 'refused'
              : read.finished
                ? 'done'
                : null;
        // After `done`: a data change of the turn has named the loss already, and this changes nothing then.
        if (unconfirmedRef.current) safeDispatch({ type: 'confirm_lost' });
        unconfirmedRef.current = false;
        // Every turn's end says what it changed (`turnOutcome`), `null` for one that did not reach
        // its `done` (refused, failed, stopped, which the thread names already); that also ends
        // the wait of an earlier question's memory read (`memoryTurn`).
        safeDispatch({
          type: 'turn_outcome',
          outcome: turnEndRef.current === 'done' ? turnOutcome(read) : null,
        });
        safeDispatch({ type: 'run_end' });
      }
      // A shipped run adds decisions and the assistant's `forget` removes some; nothing else
      // changes the list, `.start_over()` included: after every `done` the list follows the
      // server, and it names the decisions a version added. Only the read after a turn that ended
      // with its `done` speaks for that turn.
      if (read.finished) void refreshMemory(turnEndRef.current === 'done');
      return read;
    },
    [safeDispatch, addItem, handleFailure, refreshMemory]
  );

  /** One turn; the code of the error that ended it (`run_limit`, `capacity`, a failed request) lands in
   * `turnErrorRef`, null when it ended without one or never started (`plotTurn`), and how it ended in
   * `turnEndRef` (`TurnEnd`), null when it never started. A turn whose stream was cut is read again
   * (`reattach`) before any error shows; one that could not be read stays pending, and the next turn
   * reads it first. `label` is the button an action came from, as it read, for the thread; `note`
   * marks a typed text as the note sent with an attachment (`ChatItem`), never a question. */
  const runTurn = useCallback(
    async (body: TurnBody, label?: string, note = false) => {
      const current = stateRef.current;
      const sid = current.sessionId;
      turnErrorRef.current = null;
      turnEndRef.current = null;
      turnRefusalRef.current = null;
      // `busy()` reads `abortRef`, which a turn sets and clears in step with `state.run`, but at once: `state.run`
      // is a render behind, so a turn that follows another (a refused note's summary) read the ended one as
      // running and never started.
      if (!sid || busy()) return;
      const cut = cutTurnRef.current;
      cutTurnRef.current = null;
      if (cut && cut.sid === sid && sameMark(cut.mark, sessionMark(current))) {
        // One read, at once: the user asked again, so the network may be back. Its `done` still
        // fits, since nothing it syncs changed since. The cut was counted when it happened
        // (`agent_turn_resumed`), so this read is not.
        const kind = 'text' in cut.body ? 'message' : cut.body.action;
        // The cut turn's plot, shown before the cut or brought by this read, is what the same
        // request asks for: asking again would make that plot a second time.
        const repeats = (shipped: boolean) =>
          sameRequest(cut.body, body) && (cut.shipped || shipped);
        // Untimed: the cut turn started long before this read, so it shows no clock and its plot
        // no `ready in`, never a wrong time.
        const late = await driveTurn(
          kind,
          async (controller, read) => {
            read.lastId = cut.lastId;
            // Its outcome counts what came before the cut too.
            Object.assign(read, cut.changes);
            const resumed = await reattach(sid, read, controller, [0]);
            // Nothing new starts then, so a read that failed says why the click did nothing.
            if (resumed?.outcome === 'failed' && !read.finished && repeats(read.shipped)) {
              addItem({ kind: 'error', code: 'network', ref: null });
              read.errorCode = 'network';
            }
          },
          false
        );
        if (repeats(late.shipped)) return;
        if (turnEndRef.current === 'stopped') return;
        if (!mounted.current || stateRef.current.sessionId !== sid) return;
      }
      await driveTurn('text' in body ? 'message' : body.action, async (controller, read) => {
        addItem(
          'text' in body
            ? { kind: 'user', text: body.text, ...(note ? { note: true as const } : {}) }
            : {
                kind: 'action',
                action: body.action,
                library: current.library,
                ...(label && { label }),
              }
        );
        const response = await agentApi.postMessage(
          token,
          sid,
          body,
          controller.signal,
          siteThemeRef.current
        );
        // The BFF always ends a turn with `done`: a stream without it, or one that failed (an HTTP/3
        // error between the browser and the edge, say), was cut, while the server may run the turn on.
        const end = await consume(response, read, controller.signal);
        if (end === 'done') return;
        const failure: Failure = { code: end === 'cut' ? 'network' : 'upstream', ref: null };
        const resumed = read.lastId ? await reattach(sid, read, controller, resumeDelaysMs) : null;
        if (resumed) trackEvent('agent_turn_resumed', { outcome: resumed.outcome });
        if (read.finished || stoppedRef.current || controller.signal.aborted) return;
        // The server's own answer says more than the cut: a session that is gone, a sign-in.
        const shown =
          resumed?.failure && resumed.failure.code !== 'not_found' ? resumed.failure : failure;
        addItem({ kind: 'error', code: shown.code, ref: shown.ref });
        read.errorCode = shown.code;
        if (resumed?.outcome === 'failed' && read.lastId) {
          cutTurnRef.current = {
            sid,
            body,
            lastId: read.lastId,
            mark: sessionMark(stateRef.current),
            shipped: read.shipped,
            changes: changesOf(read),
          };
        }
      });
    },
    [token, addItem, consume, reattach, driveTurn, busy, trackEvent, resumeDelaysMs]
  );

  /**
   * `.create_plot()`, `.start_over()`: the fresh plot from the catalogue code, without a switch's
   * carry; the server still applies the plot memory's decisions, which only the user clears.
   * `label` is the button pressed, which the thread shows.
   */
  const createPlot = useCallback(
    (label?: string) => runTurn({ action: 'create_plot' }, label),
    [runTurn]
  );

  /**
   * `plot the new data` with an empty box: the server starts from the library's latest plot when
   * the data comes from its paste with its bindings, with a request of its own for the new data,
   * else from the catalogue code as `createPlot` does; the plot's `new_data` says which (owner
   * decision of 2026-11-08). `label` is the button as it read, for the thread.
   */
  const plotNewData = useCallback(
    (label?: string) => runTurn({ action: 'plot_new_data' }, label),
    [runTurn]
  );

  /**
   * `.example_data()`: the assistant makes example data to try the plot, as for a typed request,
   * and the turn's `done` carries it as version 1. An action, never the words: the session's
   * first typed message sets the session language, so typed English would keep a German visitor
   * in English, while an action leaves the language to the visitor's own first message.
   */
  const exampleData = useCallback(() => runTurn({ action: 'example_data' }), [runTurn]);

  /**
   * The offer after a switch, which the plot button runs with an empty box: the plot
   * in the new library from its catalogue code, with the plot memory's
   * decisions and the theme the user asked for (`carry_plot`). `label` is the button as it read,
   * for the thread; a carry the chat started has none.
   */
  const carryPlot = useCallback(
    (label?: string) => runTurn({ action: 'carry_plot' }, label),
    [runTurn]
  );

  // The request `followChatSwitch` took last: an effect run twice before the state drops it switches once.
  const chatSwitchTaken = useRef<ChatSwitch | null>(null);

  /** `createPlot`, or `carryPlot` when the copy took the page session's tuning over (`copyData`), resolving to the
   * code of the error that ended the turn, or null. The fan-out tells a turn the user's cap refused (`run_limit`)
   * from a turn that ran (`FanOut`). */
  const plotTurn = useCallback(async (): Promise<string | null> => {
    await runTurn({ action: copyCarryRef.current ? 'carry_plot' : 'create_plot' });
    return turnErrorRef.current;
  }, [runTurn]);

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
   * Enter with an attachment: send its text. A table is stored (version 1, unconfirmed),
   * its default bindings are applied, and the assistant's summary of it follows
   * as the turn `summarize_data`. Text that is no table comes back as a
   * transcription to decide on, which stores nothing and asks for no summary. A
   * formula, code or text that asks for data instead ("Beispieldaten"; `422
   * formula`, `code`, `data_request`) goes to the chat as the user's turn, where
   * the assistant computes, runs or generates the data; `onForward` hears of it
   * before that turn. The promise resolves to the outcome once the turn the parse
   * started (the summary, or the forwarded text) is over, with how it ended.
   * `table` reads another of the tables the previous answer named (the data
   * panel's table picker).
   */
  const parseData = useCallback(
    async (
      text: string,
      confirmed = false,
      source?: string,
      table?: number,
      options: ParseOptions = {}
    ): Promise<ParseResult> => {
      const sid = stateRef.current.sessionId;
      if (!sid || !text.trim() || busy()) return { outcome: 'skipped', turnEnd: null };
      const bytes = utf8Bytes(text);
      const bucket = sizeBucket(bytes);
      if (bytes > MAX_DATASET_BYTES) {
        const failure: Failure = { code: 'too_long', ref: null };
        safeDispatch({ type: 'parse_failed', failure });
        trackEvent('agent_data_parsed', { status: 'too_long', size_bucket: bucket });
        return { outcome: 'failed', turnEnd: null, failure };
      }
      let outcome: ParseOutcome = 'failed';
      let refusal: Failure | undefined;
      let forward: string | null = null;
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
              ...(options.file ? { file: options.file } : {}),
            },
            ...(options.chip ? { chip: options.chip } : {}),
          });
          trackEvent('agent_data_parsed', { status: 'transcribed', size_bucket: bucket });
          return { outcome: 'transcribed', turnEnd: null };
        }
        safeDispatch({
          type: 'parse_done',
          parsed,
          bytes,
          // The text of a paste the table picker may read again (a confirmed transcription is never split).
          ...(confirmed ? {} : { paste: { text, ...(source ? { source } : {}) } }),
          upload: { text, confirmed, ...(source ? { source } : {}), ...(table ? { table } : {}) },
          ...(options.file ? { file: options.file } : {}),
          // A confirmed parse is a transcription's `.use()`: its item becomes the card.
          ...(options.chip ? { chip: options.chip } : confirmed ? { fromTranscription: true } : {}),
        });
        // Notes or column names in another language come as its offer; the language stays.
        const pastedLanguage = readPlotLanguage(parsed.language);
        if (pastedLanguage) {
          safeDispatch({
            type: 'language_sync',
            plotLanguage: pastedLanguage,
            offer: readLanguageOffer(parsed.language),
          });
        }
        trackEvent('agent_data_parsed', { status: 'ok', size_bucket: bucket });
        outcome = 'stored';
        const defaults = toMap(parsed.bindings);
        // Learn whether the defaults are complete and which required roles
        // they leave open (the parse stored them already: the PUT is idempotent).
        await applyBindings(defaults, defaults);
      } catch (err) {
        const failure = handleFailure(err);
        const trimmed = text.trim();
        // A formula, code or a request for data holds no table: the chat computes, runs or
        // generates it, with no offer to click first. Only text the chat takes can move there.
        if (FORWARDED.has(failure.code) && trimmed.length <= MAX_MESSAGE_CHARS) {
          forward = trimmed;
          outcome = 'forwarded';
          safeDispatch({ type: 'parse_forwarded' });
          trackEvent('agent_data_parsed', { status: failure.code, size_bucket: bucket });
        } else {
          // Longer code reads as a failure whose line asks to shorten it (`DATA_FAILURE.code`).
          refusal = failure;
          safeDispatch({ type: 'parse_failed', failure });
          const known = ['too_long', 'unparseable', 'data_refused', ...FORWARDED];
          const status = known.includes(failure.code) ? failure.code : 'error';
          trackEvent('agent_data_parsed', { status, size_bucket: bucket });
          if (PASTE_GUARDRAIL_REASONS.has(failure.code)) {
            trackEvent('agent_guardrail_block', { reason: failure.code });
          }
        }
      } finally {
        parseRef.current = false;
      }
      if (!mounted.current) return { outcome, turnEnd: null };
      // The forwarded text becomes the user's message, as if typed into the chat.
      if (forward !== null) {
        options.onForward?.(forward);
        await runTurn({ text: forward });
        return { outcome, turnEnd: turnEndRef.current };
      }
      // The assistant describes the stored data first thing, so the user can correct it in words
      // before confirming it. A note typed with the attachment is that first turn: the assistant
      // summarizes the data and acts on the note in one reply.
      if (outcome === 'stored') {
        options.onStored?.();
        const note = options.note?.trim() ?? '';
        if (!note || note.length > MAX_MESSAGE_CHARS) {
          await runTurn({ action: 'summarize_data' });
          return { outcome, turnEnd: turnEndRef.current };
        }
        // Its reply summarizes the data that just arrived, so "nothing changed" would be false: the
        // note's item is never a question. A forwarded text above is the user's message as typed.
        await runTurn({ text: note }, undefined, true);
        const end = turnEndRef.current;
        // The note's turn was refused before the assistant read the data, or the scope judge
        // was out: the data still gets its summary. The note stays in the thread above it.
        const unsummarized =
          (end === 'refused' && NOTE_REFUSALS.has(turnRefusalRef.current ?? '')) ||
          (end === 'error' && turnErrorRef.current === NOTE_JUDGE_OUTAGE);
        if (unsummarized && mounted.current) await runTurn({ action: 'summarize_data' });
        return { outcome, turnEnd: end };
      }
      return { outcome, turnEnd: null, ...(refusal ? { failure: refusal } : {}) };
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
  const confirmTranscription = useCallback((): Promise<ParseResult> => {
    const transcription = stateRef.current.transcription;
    if (!transcription) return Promise.resolve({ outcome: 'skipped', turnEnd: null });
    // The file's name travels with the table it was read from, whatever the box holds now, and a
    // workbook stays with it for the sheet picker.
    return parseData(
      transcription.text,
      true,
      transcription.source,
      undefined,
      transcription.file ? { file: transcription.file } : undefined
    );
  }, [parseData]);

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

  /**
   * The header's library menu: switch the session to `next`. Resolves to true
   * once the server switched, false when nothing started (no session, the
   * library already, something in flight, which the server would refuse with
   * `409 run_active`). The answer's offer, if any, becomes `carryOffer`; the
   * run waits for the user's click. A failure keeps the library and rejects
   * with an `AgentApiError` for the menu's failure line; a 401 or 403 also
   * shows the sign-in notice.
   */
  const switchLibrary = useCallback(
    async (next: string, source: SwitchSource = 'menu'): Promise<boolean> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy() || next === current.library) return false;
      safeDispatch({ type: 'library_start' });
      try {
        const result = await agentApi.switchLibrary(token, sid, specId, next, source);
        safeDispatch({
          type: 'library_done',
          library: next,
          eligibility: result.eligibility,
          // An older server names no target: the pair the page asked for.
          target: result.target ?? { spec_id: specId, library: next },
          carry: result.carry,
        });
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'library_failed', failure });
        throw err instanceof AgentApiError ? err : new AgentApiError(0, failure.code);
      }
      void refreshMemory();
      return true;
    },
    [token, specId, safeDispatch, handleFailure, busy, refreshMemory]
  );

  /**
   * Carry out the switch a turn asked for (`chatSwitch`, the assistant's
   * `switch_plot`), once: the switch route with the source `chat`. Resolves to
   * the request when the server switched, so the page follows the URL and, with
   * `plot`, starts the carry run; to `null` when there was none or the server
   * refused it, whose reason (`not_eligible`, `run_active`) the thread shows,
   * since no menu was clicked to show it under.
   */
  const followChatSwitch = useCallback(async (): Promise<ChatSwitch | null> => {
    const request = stateRef.current.chatSwitch;
    if (!request || chatSwitchTaken.current === request) return null;
    chatSwitchTaken.current = request;
    safeDispatch({ type: 'chat_switch', request: null });
    try {
      return (await switchLibrary(request.library, 'chat')) ? request : null;
    } catch (err) {
      const failure =
        err instanceof AgentApiError
          ? { code: err.code, ref: err.shownRef }
          : { code: 'network', ref: null };
      addItem({ kind: 'error', code: failure.code, ref: failure.ref });
      return null;
    }
  }, [safeDispatch, switchLibrary, addItem]);

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
   * A pick of the session language: the chip's (`PUT .../language` with the value as
   * given, which the chip trims; source `chosen`, which closes every open offer line), or
   * with `offerId` the `.switch()` of that offer line (`via: offer`, source `offer`, the line
   * then names the language it set). The answer is the new state in the server's stored
   * form (`English` comes back as `en`). Nothing starts without a session or while
   * anything else is in flight, which the server would refuse with `409 run_active`. A
   * failure keeps the old value and rejects with an `AgentApiError` for the caller's
   * failure line; a 401 or 403 also shows the sign-in notice. The server's usage
   * telemetry counts the offers and the picks (`language_offer`); the page sends nothing.
   */
  const pickLanguage = useCallback(
    async (language: string, offerId?: number): Promise<void> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy()) return;
      languageRef.current = true;
      safeDispatch({ type: 'language_start' });
      try {
        const via = offerId !== undefined ? 'offer' : undefined;
        const { suggestion, ...applied } = await agentApi.setLanguage(token, sid, language, via);
        safeDispatch({ type: 'language_done', plotLanguage: applied, offerId });
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

  /** The chip's choice (`pickLanguage` without an offer line). */
  const setLanguage = useCallback((language: string) => pickLanguage(language), [pickLanguage]);

  /** The `.switch()` of the offer line `offerId`: the language it offered, as the line holds it. */
  const acceptLanguage = useCallback(
    async (offerId: number): Promise<void> => {
      const item = stateRef.current.items.find(entry => entry.id === offerId);
      if (item?.kind !== 'language_offer' || item.state !== 'open') return;
      await pickLanguage(item.language, offerId);
    },
    [pickLanguage]
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
    setBinding,
    checkBindings,
    confirmData,
    undoData,
    createPlot,
    plotNewData,
    exampleData,
    carryPlot,
    followChatSwitch,
    plotTurn,
    sendMessage,
    stop,
    switchLibrary,
    forgetMemory,
    forgetAllMemory,
    requestTheme,
    fetchArtifact,
    reportOutcome,
    convertFile,
    readSheet,
    fetchDataCsv,
    saveSession,
    setLanguage,
    acceptLanguage,
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
    state.languageBusy ||
    state.memoryBusy ||
    state.sheetBusy
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
