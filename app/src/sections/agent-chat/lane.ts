/**
 * Which lane the chat page runs on, for the parts that differ deep in the tree:
 * the admin lane (`/debug/agent`) or the public one (`/agent`). The page
 * provides it (`AgentChatPage`); without a provider it is the admin lane, so a
 * component rendered on its own behaves as it always has.
 *
 * What differs on the public lane: the feedback form's data box starts
 * unticked, the form says what sending stores (the owner's privacy rule:
 * explicit consent at the moment of sending), the experimental notice says that
 * an AI does the work, and there is no `.save()` (since 2026-11-02; the page
 * leaves the "⋯" menu out).
 */

import { createContext, useContext } from 'react';

import type { AgentLane } from 'src/lib/agent';

export const AgentLaneContext = createContext<AgentLane>('admin');

export function useAgentLane(): AgentLane {
  return useContext(AgentLaneContext);
}

/**
 * The public lane's notice above the first input (`ExperimentalNotice`): one line, always in
 * view, and the lines its ⓘ button opens, above the link to the legal page. The owner reads
 * every user-facing text: keep them in the PR's "Texts to read".
 */
export const EXPERIMENTAL_LINE =
  'experimental AI · results can be wrong · stored only if you send feedback';
export const EXPERIMENTAL_DETAILS = [
  'Claude by Anthropic, through Google Cloud Vertex AI in the EU',
  "don't paste data you may not share",
  'daily limits apply',
] as const;

/**
 * The consent line under the public feedback form, next to `# include data.csv`.
 * The owner reads every user-facing text: keep it in the PR's "Texts to read".
 */
export const FEEDBACK_CONSENT =
  'sending stores this chat, its plots and a 5-row sample of your data for 180 days, for the operator to read; tick the box to add the whole data file.';
