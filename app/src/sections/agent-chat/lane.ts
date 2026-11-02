/**
 * Which lane the chat page runs on, for the parts that differ deep in the tree:
 * the admin lane (`/debug/agent`) or the public one (`/agent`). The page
 * provides it (`AgentChatPage`); without a provider it is the admin lane, so a
 * component rendered on its own behaves as it always has.
 *
 * What differs on the public lane: the feedback and `.save()` boxes start
 * unticked, and the feedback form says what sending stores (the owner's privacy
 * rule: explicit consent at the moment of sending).
 */

import { createContext, useContext } from 'react';

import type { AgentLane } from 'src/lib/agent';

export const AgentLaneContext = createContext<AgentLane>('admin');

export function useAgentLane(): AgentLane {
  return useContext(AgentLaneContext);
}

/**
 * The consent line under the public feedback form, next to `# include data.csv`.
 * The owner reads every user-facing text: keep it in the PR's "Texts to read".
 */
export const FEEDBACK_CONSENT =
  'sending stores this chat, its plots and a 5-row sample of your data for 180 days, for the operator to read; tick the box to add the whole data file.';
