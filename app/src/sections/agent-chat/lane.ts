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
 * view, and the lines its ⓘ button opens, above the link to the legal page. Each detail states
 * what the legal page's assistant section says ("memory", "feedback", "the model", "limits"):
 * the hour is the agents service's idle sweep (`AGENT_SESSION_IDLE_S`, 3600 s). The owner reads
 * every user-facing text: keep them in the PR's "Texts to read".
 */
export const EXPERIMENTAL_LINE = 'experimental AI · answers can be wrong';
export const EXPERIMENTAL_DETAILS = [
  'your chat and data live only in server memory, deleted after an hour idle',
  'nothing is saved unless you send feedback',
  'Claude by Anthropic, via Google Cloud Vertex AI in the EU · not used for training',
  "don't paste data you may not share",
  'daily limits apply',
] as const;

/**
 * The consent line under the public feedback form, next to `# include data.csv`.
 * The owner reads every user-facing text: keep it in the PR's "Texts to read".
 */
export const FEEDBACK_CONSENT =
  'sending stores this chat, its plots and a 5-row sample of your data for 180 days, for the operator to read; tick the box to add the whole data file.';
