import { analyticsMutedThisLoad } from 'src/analytics/mute';
import { getAnalyticsAmbientProps } from 'src/hooks/useAnalytics';
import { paths } from 'src/routes/paths';
import { readAdminHint } from 'src/utils/adminAuth';

/**
 * A page load that starts on the agent chat in an admin's browser, decided when the metrics
 * register, before the chat has mounted and muted analytics itself (TTFB and FCP can report
 * by then). The signs are the ones the chat's admin check starts from (`useAgentAdmin`): the
 * chat's old admin address, which only Cloudflare Access lets through, or `/agent` with the
 * admin hint. A forged hint mutes nothing but that browser's own numbers.
 */
function startsOnAdminChat(): boolean {
  const { pathname } = window.location;
  return pathname === '/debug/agent' || (pathname === paths.agent && readAdminHint());
}

/**
 * One metric as a Plausible event with the ambient props; nothing for a page load that started
 * on the admin's chat or in which the chat muted analytics later (`src/analytics/mute.ts`),
 * since a metric measures the whole load and may report after the chat is gone.
 */
function send(adminLoad: boolean, name: string, value: string, rating: string) {
  if (adminLoad || analyticsMutedThisLoad()) return;
  window.plausible?.(name, { props: { ...getAnalyticsAmbientProps(), value, rating } });
}

/**
 * Core Web Vitals tracking via web-vitals library.
 * Reports LCP, CLS, and INP to Plausible as custom events.
 * Only runs in production (anyplot.ai), dynamically imported for zero dev cost.
 */
export function reportWebVitals() {
  if (typeof window === 'undefined' || window.location.hostname !== 'anyplot.ai') {
    return;
  }
  const admin = startsOnAdminChat();

  import('web-vitals')
    .then(({ onLCP, onCLS, onINP, onFCP, onTTFB }) => {
      onLCP(m => send(admin, 'LCP', String(Math.round(m.value / 100) * 100), m.rating));
      onCLS(m => send(admin, 'CLS', String(Math.round(m.value * 100) / 100), m.rating));
      onINP(m => send(admin, 'INP', String(Math.round(m.value / 50) * 50), m.rating));
      onFCP(m => send(admin, 'FCP', String(Math.round(m.value / 100) * 100), m.rating));
      onTTFB(m => send(admin, 'TTFB', String(Math.round(m.value / 100) * 100), m.rating));
    })
    .catch(() => {});
}
