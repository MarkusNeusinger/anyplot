/**
 * The plot button's one click on data that still waits in the message box (owner decision of
 * 2026-11-08): a file opened with `.open()` or dropped on the chat, a table pasted into the box,
 * or a table typed there. The click sends it as Enter would, with the box's text as its note,
 * and once the server's reading comes back clean the page goes on by itself as a click on the
 * plot button would on that data: the step-1 confirmation, then the plot. Enter still only sends.
 *
 * Clean means: the data is stored, the reading's turn ended with its `done`, every required role
 * has a column, the server refused no binding, the data card shows no warning (the parser's, a
 * wide table's `.to_long()` offer, a paste of several tables, a bound column's own warning), the
 * server's binding check names none (`bindingWarnings`, asked again once when the turn changed
 * the data or the bindings), and the reading's last reply asks no question. Anything else stops
 * at the data card, where the status line says what to look at, and the next click plots as
 * before. The page runs the chain (`AgentChatPage.tsx`); every decision of it is here.
 */

import {
  type AgentSessionState,
  familyOf,
  type ParseResult,
  sessionBusy,
} from 'src/hooks/useAgentSession';
import { isPlotAction, longSuggestion, MAX_MESSAGE_CHARS, tableChoice } from 'src/lib/agent';
import { bindingHint } from 'src/sections/agent-chat/bindings';
import { routeInput } from 'src/sections/agent-chat/routeInput';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';

/**
 * What the message box holds that the plot button sends before it plots: the attachment, once it
 * is read and the dataset route can take it (a refused one again), or a table typed into the box,
 * which Enter would send as data too (`attachTyped`). `null` for nothing to send first. The box's
 * text goes with an attachment as its note, and like any message it never goes over the cap.
 */
export function boxData(
  attachment: Attachment | null,
  draft: string
): 'attachment' | 'typed' | null {
  const text = draft.trim();
  if (text.length > MAX_MESSAGE_CHARS) return null;
  if (attachment) {
    return attachment.status === 'ready' || attachment.status === 'failed' ? 'attachment' : null;
  }
  return text && routeInput(text) === 'data' ? 'typed' : null;
}

/** Why the one click stopped at the data card: what the status line asks the user to look at. */
export type ChainStop =
  | { reason: 'question' | 'wide' | 'bindings_failed' | 'refused' | 'error' | 'stopped' }
  | { reason: 'data_warnings' | 'tables'; count: number }
  | { reason: 'binding_warning'; role: string };

/**
 * The chain's next step: `wait` for the session to settle (the reading's turn, a chat switch it
 * asked for, a binding check), `recheck` the bindings once, `plot` as a click would, or `stop`.
 * A stop without a reason ends the chain where the step's own line says what comes next: nothing
 * was stored (a table read from text to decide on, a refused attachment, text the chat took), a
 * required role has no column, or something else acted since the click.
 */
export type ChainStep =
  | { kind: 'wait' }
  | { kind: 'recheck' }
  | { kind: 'plot' }
  | { kind: 'stop'; stop: ChainStop | null };

/** How the click's send ended, and where its items start in the thread. */
export interface ChainRead {
  /** `parseData`'s answer for the click's attachment. */
  result: ParseResult;
  /** The thread's next item id at the click: the reading's items have this id or a later one. */
  since: number;
  /** The binding check ran again for this chain. */
  rechecked: boolean;
}

/** What the page adds: the admin's fan-out is on, or another attachment waits in the box. */
export interface ChainPage {
  plotAll: boolean;
  attachment: boolean;
}

const WAIT: ChainStep = { kind: 'wait' };
const END: ChainStep = { kind: 'stop', stop: null };
const stopFor = (stop: ChainStop): ChainStep => ({ kind: 'stop', stop });

/**
 * Whether a reply ends with a question, as the service's own reading of a reply has it
 * (`telemetry.ends_with_question`): its last visible character is a question mark (Latin,
 * full-width or Arabic), past closing quotes, brackets and Markdown emphasis. The assistant asks
 * at most one question, as its reply's last sentence (`root.md`, "Replies").
 */
export function endsWithQuestion(text: string): boolean {
  return /[?？؟]$/.test(
    text
      .trimEnd()
      .replace(/[)"'»”’*_`]+$/, '')
      .trimEnd()
  );
}

/**
 * The role a server binding warning names: the text before its first `: ` (`y`, `min_value and
 * max_value`), or the bindings as a whole for a line without one.
 */
export function warnedRole(line: string): string {
  const end = line.indexOf(': ');
  return end > 0 && end <= 60 ? line.slice(0, end) : 'the bindings';
}

/** The first bound column with a warning on the card (`bindingHint`): its role, or null. */
function hintedRole(state: AgentSessionState): string | null {
  const parsed = state.dataset?.parsed;
  if (!parsed) return null;
  const suggestion = longSuggestion(parsed.suggestion);
  for (const [name, column] of Object.entries(state.bindings)) {
    const role =
      familyOf(name, state.roles) ?? state.roles.find(candidate => candidate.name === name);
    if (role && bindingHint(role, column, parsed.profile.columns, suggestion)) return name;
  }
  return null;
}

/**
 * The chain's next step on the session as it is now, after the click's send ended (`read`). Pure:
 * the page calls it again after each render until it acts, and acts once.
 */
export function chainStep(state: AgentSessionState, read: ChainRead, page: ChainPage): ChainStep {
  if (state.phase !== 'ready' || read.result.outcome !== 'stored') return END;
  const since = state.items.filter(item => item.id >= read.since);
  // A plot click or a plot since the click (the summary is an action too): the chain never
  // plots a second time.
  const plotted = since.some(
    item => item.kind === 'plot' || (item.kind === 'action' && isPlotAction(item.action))
  );
  if (plotted) return END;
  if (sessionBusy(state) || state.chatSwitch) return WAIT;
  switch (read.result.turnEnd) {
    case 'stopped':
      return stopFor({ reason: 'stopped' });
    case 'refused':
      return stopFor({ reason: 'refused' });
    case 'error':
      return stopFor({ reason: 'error' });
    case null:
      return END;
    default:
      break;
  }
  // A refusal or an error after the turn's `done`: a summary run after a refused note, a chat
  // switch the server refused.
  if (since.some(item => item.kind === 'refusal')) return stopFor({ reason: 'refused' });
  if (since.some(item => item.kind === 'error' || item.kind === 'plot_failed')) {
    return stopFor({ reason: 'error' });
  }
  // The fan-out's `.plot_all()` is a click of its own; a new attachment is the user's next step.
  if (page.plotAll || page.attachment || !state.dataset || state.transcription) return END;
  if (state.bindingsError) return stopFor({ reason: 'bindings_failed' });
  if (!state.bindingsComplete || state.missingRoles.length > 0) return END;
  const parsed = state.dataset.parsed;
  if (parsed.warnings.length > 0) {
    return stopFor({ reason: 'data_warnings', count: parsed.warnings.length });
  }
  const choice = tableChoice(parsed);
  if (choice) return stopFor({ reason: 'tables', count: choice.tables.length });
  if (longSuggestion(parsed.suggestion)) return stopFor({ reason: 'wide' });
  const hinted = hintedRole(state);
  if (hinted) return stopFor({ reason: 'binding_warning', role: hinted });
  if (state.bindingWarnings === null) return read.rechecked ? END : { kind: 'recheck' };
  if (state.bindingWarnings.length > 0) {
    return stopFor({ reason: 'binding_warning', role: warnedRole(state.bindingWarnings[0]) });
  }
  const replies = since.filter(item => item.kind === 'assistant');
  const last = replies[replies.length - 1];
  if (last?.kind === 'assistant' && endsWithQuestion(last.text)) {
    return stopFor({ reason: 'question' });
  }
  return { kind: 'plot' };
}

/**
 * What the status line keeps a stop by: the data, the bindings, the thread's length and the
 * library at the stop. Once any of them changes (a new version, a binding, a message, a plot, a
 * switch), the stop's words go, and the step's own line takes over again.
 */
export interface StopMark {
  dataset: AgentSessionState['dataset'];
  bindings: AgentSessionState['bindings'];
  items: number;
  library: string;
}

export function stopMark(state: AgentSessionState): StopMark {
  return {
    dataset: state.dataset,
    bindings: state.bindings,
    items: state.items.length,
    library: state.library,
  };
}

export function sameStopMark(mark: StopMark, state: AgentSessionState): boolean {
  return (
    mark.dataset === state.dataset &&
    mark.bindings === state.bindings &&
    mark.items === state.items.length &&
    mark.library === state.library
  );
}
