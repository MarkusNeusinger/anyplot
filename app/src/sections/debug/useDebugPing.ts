import { useEffect, useState } from 'react';

import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';

export const PING_INTERVAL_MS = 2000;
export const PING_HISTORY = 30;

export interface PingData {
  ms: number;
  ok: boolean;
}

export function useDebugPing(adminToken: string, authRequired: boolean) {
  const [pings, setPings] = useState<PingData[]>([]);

  useEffect(() => {
    if (authRequired) return;
    let cancelled = false;
    const tick = async () => {
      const started = performance.now();
      try {
        const r = await fetchWithAuth(`${DEBUG_API_URL}/debug/ping`, adminToken);
        const totalMs = performance.now() - started;
        if (!r.ok) throw new Error(`${r.status}`);
        const json: { database_connected: boolean } = await r.json();
        if (cancelled) return;
        setPings(prev => [
          ...prev.slice(-(PING_HISTORY - 1)),
          { ms: totalMs, ok: json.database_connected },
        ]);
      } catch {
        if (cancelled) return;
        const totalMs = performance.now() - started;
        setPings(prev => [...prev.slice(-(PING_HISTORY - 1)), { ms: totalMs, ok: false }]);
      }
    };
    tick();
    const id = setInterval(tick, PING_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [adminToken, authRequired]);

  return { pings };
}
