/**
 * Whether the spec pages may show the "use with my data" entry for one
 * implementation, and which chat it leads to.
 *
 * The conditions, checked in this order so a public visitor never sends a
 * request to the debug API:
 *
 * 1. the build has the agent chat (`VITE_ENABLE_AGENT_CHAT`, a literal at
 *    build time: off, everything below is dead code);
 * 2. the public lane's door (`GET /agent/lane`, `useAgentLaneOpen`): while it is
 *    open, everyone opens the public chat (`/agent`), an admin too, so the owner
 *    tests the chat exactly as a visitor sees and uses it (owner decision of
 *    2026-11-04); nothing is asked before the door answers, so no view probes
 *    one lane and then the other;
 * 3. only while the door is closed (the kill switch): local development, or the
 *    admin hint `DebugPage` sets after a successful `/debug/status`, opens the
 *    admin lane (`/debug/agent`), which stays reachable directly for the admin's
 *    tools either way (`all`, `.save()`);
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

/**
 * May this browser use the admin chat (the build has the chat, and local development or the
 * admin hint)? The entry points lead there only while the public lane is closed (gate 3).
 */
export function agentChatAvailable(): boolean {
  return AGENT_CHAT_ENABLED && CONFIG.features.agentChat && (CONFIG.isDev || readAdminHint());
}

export function useAgentEligibility(
  specId: string | null | undefined,
  library: string | null | undefined
): AgentLane | null {
  const [answer, setAnswer] = useState<{ key: string; lane: AgentLane | null } | null>(null);
  const laneOpen = useAgentLaneOpen();
  const built = AGENT_CHAT_ENABLED && CONFIG.features.agentChat;
  const lane: AgentLane | null = !built
    ? null
    : laneOpen === true
      ? 'public'
      : laneOpen === false && agentChatAvailable()
        ? 'admin'
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
