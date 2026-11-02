/**
 * Whether the plot page may show the "use with my data" entry for one
 * implementation, and which chat it leads to.
 *
 * The conditions, checked in this order so a public visitor never sends a
 * request to the debug API:
 *
 * 1. the build has the agent chat (`VITE_ENABLE_AGENT_CHAT`, a literal at
 *    build time: off, everything below is dead code);
 * 2. local development, or the admin hint `DebugPage` sets after a successful
 *    `/debug/status`: the admin lane (`/debug/agent`), as before;
 * 3. otherwise the public lane, while it is open (`GET /agent/lane`,
 *    `useAgentLaneOpen`);
 * 4. that lane's eligibility answer for the pair (`GET .../eligibility`).
 *
 * A 401 or 403 on the admin lane clears the hint, so a lapsed admin session
 * stops the probes. Returns the lane to open, or `null` for no entry.
 */

import { useEffect, useState } from 'react';

import { AGENT_CHAT_ENABLED, CONFIG } from 'src/global-config';
import { useAgentLaneOpen } from 'src/hooks/useAgentLaneOpen';
import { agentApi, AgentApiError, type AgentLane, PUBLIC_LANE } from 'src/lib/agent';
import { readAdminHint, readAdminToken, setAdminHint } from 'src/utils/adminAuth';

/** Gates 1 and 2: may this browser use the admin chat? */
export function agentChatAvailable(): boolean {
  return AGENT_CHAT_ENABLED && CONFIG.features.agentChat && (CONFIG.isDev || readAdminHint());
}

export function useAgentEligibility(
  specId: string | null | undefined,
  library: string | null | undefined
): AgentLane | null {
  const [answer, setAnswer] = useState<{ key: string; lane: AgentLane | null } | null>(null);
  const laneOpen = useAgentLaneOpen();
  const admin = agentChatAvailable();
  const lane: AgentLane | null = admin
    ? 'admin'
    : AGENT_CHAT_ENABLED && CONFIG.features.agentChat && laneOpen === true
      ? 'public'
      : null;
  // The lane is part of the key: an answer of one lane never stands for the other.
  const key = lane && specId && library ? `${lane}:${specId}/${library}` : null;

  useEffect(() => {
    if (!AGENT_CHAT_ENABLED) return;
    if (!key || !specId || !library || lane === null) return;
    const controller = new AbortController();
    const token = lane === 'admin' ? readAdminToken() : PUBLIC_LANE;
    agentApi
      .eligibility(token, specId, library, controller.signal)
      .then(result => {
        if (!controller.signal.aborted)
          setAnswer({ key, lane: result.eligible === true ? lane : null });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (lane === 'admin' && err instanceof AgentApiError && err.unauthorized)
          setAdminHint(false);
        setAnswer({ key, lane: null });
      });
    return () => controller.abort();
  }, [key, specId, library, lane]);

  return answer !== null && answer.key === key ? answer.lane : null;
}
