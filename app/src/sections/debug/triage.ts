/**
 * Pure helpers of the agent cases section: the filters as a list query, the
 * optimistic form of a triage change, and the error lines.
 */

import {
  AgentApiError,
  type AgentCase,
  type CaseListQuery,
  type CasePatch,
  type CaseStatus,
  type FeedbackReaction,
} from 'src/lib/agent';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { expectedFromReaction } from 'src/sections/debug/acceptMatch';

/** The list's filters as the controls hold them; an empty string is "any". */
export interface CaseFilterValues {
  reaction: FeedbackReaction | '';
  /** A status, `open` (new and in progress), or `''` for all statuses. */
  status: CaseStatus | 'open' | '';
  spec: string;
  library: string;
  model_version: string;
  tag: string;
  include_superseded: boolean;
}

/** The open queue, superseded cases hidden: the view a triage starts from. */
export const DEFAULT_FILTERS: CaseFilterValues = {
  reaction: '',
  status: 'open',
  spec: '',
  library: '',
  model_version: '',
  tag: '',
  include_superseded: false,
};

/** The filters as a list query; "any" leaves the key out. */
export function filtersToQuery(filters: CaseFilterValues): CaseListQuery {
  return {
    reaction: filters.reaction || undefined,
    status: filters.status || undefined,
    spec: filters.spec || undefined,
    library: filters.library || undefined,
    model_version: filters.model_version || undefined,
    tag: filters.tag || undefined,
    include_superseded: filters.include_superseded || undefined,
  };
}

/** The active filters in words (`status "open", tag "legend"`), for the empty list; `''` without any. */
export function describeFilters(filters: CaseFilterValues): string {
  const parts: string[] = [];
  if (filters.status) parts.push(`status "${filters.status}"`);
  if (filters.reaction) parts.push(`reaction "${filters.reaction}"`);
  if (filters.spec) parts.push(`spec "${filters.spec}"`);
  if (filters.library) parts.push(`library "${filters.library}"`);
  if (filters.model_version) parts.push(`model version "${filters.model_version}"`);
  if (filters.tag) parts.push(`tag "${filters.tag}"`);
  return parts.join(', ');
}

/** The fields a triage change touches. */
export type Triage = Pick<AgentCase, 'status' | 'tags' | 'promoted_at' | 'expected'>;

export function triageOf(item: AgentCase): Triage {
  return {
    status: item.status,
    tags: item.tags,
    promoted_at: item.promoted_at,
    expected: item.expected,
  };
}

/**
 * What the server will answer for a change, ahead of its answer: tags sorted,
 * a promotion stamped once and given the reaction rule's outcome when it has
 * none, a withdrawn promotion cleared with its outcome kept.
 */
export function applyPatch(before: Triage, reaction: FeedbackReaction, patch: CasePatch): Triage {
  const next: Triage = { ...before };
  if (patch.status) next.status = patch.status;
  if (patch.tags) next.tags = [...new Set(patch.tags)].sort();
  if (patch.expected) next.expected = patch.expected;
  if (patch.promoted === true) {
    next.promoted_at = before.promoted_at ?? new Date().toISOString();
    next.expected = next.expected ?? expectedFromReaction(reaction);
  } else if (patch.promoted === false) {
    next.promoted_at = null;
  }
  return next;
}

/** What a failed triage call means; codes the section does not know read as `request failed (<code>)`. */
const CASE_FAILURE: Record<string, string> = {
  not_found: 'this case is gone',
  expected_required: 'choose an expected outcome before promoting a bug or idea',
  no_data: 'this case has no data file; the harness cannot run it',
  storage: 'the case files could not be read',
  not_enabled: 'agent chat is not enabled on this server',
  unreachable: ERROR_TEXT.unreachable,
  unavailable: 'the server is not ready (no database, or the admin gate is not configured)',
  invalid: 'the server refused this request',
};

/**
 * The line for a failed call: the code's meaning and the request id to quote.
 * Anything that is not an `AgentApiError` (a body the page cannot read) is
 * `fallback`.
 */
export function describeCaseError(err: unknown, fallback: string): string {
  if (!(err instanceof AgentApiError)) return fallback;
  const text = CASE_FAILURE[err.code] ?? `request failed (${err.code})`;
  return err.ref ? `${text} · ref ${err.ref}` : text;
}
