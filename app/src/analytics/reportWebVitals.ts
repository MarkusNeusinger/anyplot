import { analyticsMutedThisLoad } from 'src/analytics/mute';
import { getAnalyticsAmbientProps } from 'src/hooks/useAnalytics';

/**
 * One metric as a Plausible event with the ambient props; nothing for a page load in which the
 * admin's own use of the agent chat muted analytics (`src/analytics/mute.ts`), since a metric
 * measures the whole load and may report after the chat is gone.
 */
function send(name: string, value: string, rating: string) {
  if (analyticsMutedThisLoad()) return;
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

  import('web-vitals')
    .then(({ onLCP, onCLS, onINP, onFCP, onTTFB }) => {
      onLCP(metric => send('LCP', String(Math.round(metric.value / 100) * 100), metric.rating));
      onCLS(metric => send('CLS', String(Math.round(metric.value * 100) / 100), metric.rating));
      onINP(metric => send('INP', String(Math.round(metric.value / 50) * 50), metric.rating));
      onFCP(metric => send('FCP', String(Math.round(metric.value / 100) * 100), metric.rating));
      onTTFB(metric => send('TTFB', String(Math.round(metric.value / 100) * 100), metric.rating));
    })
    .catch(() => {});
}
