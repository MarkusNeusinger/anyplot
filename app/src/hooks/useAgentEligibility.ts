/**
 * Whether the plot page may show the `.adapt()` button ("Use with my data")
 * for one implementation.
 *
 * Three conditions, checked in this order so a public visitor never sends a
 * request to the debug API:
 *
 * 1. the build has the agent chat (`VITE_ENABLE_AGENT_CHAT`, a literal at
 *    build time: off, everything below is dead code);
 * 2. local development, or the admin hint `DebugPage` sets after a successful
 *    `/debug/status`;
 * 3. the BFF's eligibility answer for the pair (`GET /debug/agent/eligibility`).
 *
 * A 401 or 403 clears the hint, so a lapsed admin session stops the probes.
 */

import { useEffect, useState } from 'react';

import { AGENT_CHAT_ENABLED, CONFIG } from 'src/global-config';
import { agentApi, AgentApiError } from 'src/lib/agent';
import { readAdminHint, readAdminToken, setAdminHint } from 'src/utils/adminAuth';

/** Gates 1 and 2: may this browser use the agent chat at all? */
export function agentChatAvailable(): boolean {
  return AGENT_CHAT_ENABLED && CONFIG.features.agentChat && (CONFIG.isDev || readAdminHint());
}

export function useAgentEligibility(
  specId: string | null | undefined,
  library: string | null | undefined
): boolean {
  const key = specId && library ? `${specId}/${library}` : null;
  const [answer, setAnswer] = useState<{ key: string; eligible: boolean } | null>(null);

  useEffect(() => {
    if (!AGENT_CHAT_ENABLED) return;
    if (!key || !specId || !library || !agentChatAvailable()) return;
    const controller = new AbortController();
    agentApi
      .eligibility(readAdminToken(), specId, library, controller.signal)
      .then(result => {
        if (!controller.signal.aborted) setAnswer({ key, eligible: result.eligible === true });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof AgentApiError && err.unauthorized) setAdminHint(false);
        setAnswer({ key, eligible: false });
      });
    return () => controller.abort();
  }, [key, specId, library]);

  return answer !== null && answer.key === key && answer.eligible;
}
