/**
 * Whether the public lane of the agent chat is open (`GET /agent/lane`), for
 * the entry points: the plot page's button, the landing page's line and the
 * public chat page itself.
 *
 * The API answers `{"open": true}` while the owner has the lane open and 404
 * while it is closed, so one switch on the server opens and closes every entry
 * point at runtime. One request per page load, shared by every caller; `null`
 * until it is answered. Without the chat in the build
 * (`VITE_ENABLE_AGENT_CHAT`) nothing is asked and the answer is `false`.
 */

import { useEffect, useState } from 'react';

import { AGENT_CHAT_ENABLED } from 'src/global-config';
import { publicLaneOpen } from 'src/lib/agent';

let probe: Promise<boolean> | null = null;

function laneProbe(): Promise<boolean> {
  probe ??= publicLaneOpen();
  return probe;
}

/** Forget the shared answer, for tests. */
export function resetAgentLaneProbe(): void {
  probe = null;
}

export function useAgentLaneOpen(): boolean | null {
  const [open, setOpen] = useState<boolean | null>(AGENT_CHAT_ENABLED ? null : false);

  useEffect(() => {
    if (!AGENT_CHAT_ENABLED) return;
    let active = true;
    void laneProbe().then(answer => {
      if (active) setOpen(answer);
    });
    return () => {
      active = false;
    };
  }, []);

  return open;
}
