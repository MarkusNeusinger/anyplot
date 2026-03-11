/**
 * Core Web Vitals tracking via web-vitals library.
 * Reports LCP, CLS, and INP to Plausible as custom events.
 * Only runs in production (pyplots.ai), dynamically imported for zero dev cost.
 */
export function reportWebVitals() {
  if (
    typeof window === 'undefined' ||
    window.location.hostname !== 'pyplots.ai'
  ) {
    return;
  }

  import('web-vitals').then(({ onLCP, onCLS, onINP }) => {
    onLCP((metric) => {
      window.plausible?.('LCP', {
        props: {
          value: String(Math.round(metric.value / 100) * 100),
          rating: metric.rating,
        },
      });
    });

    onCLS((metric) => {
      window.plausible?.('CLS', {
        props: {
          value: String(Math.round(metric.value * 100) / 100),
          rating: metric.rating,
        },
      });
    });

    onINP((metric) => {
      window.plausible?.('INP', {
        props: {
          value: String(Math.round(metric.value / 50) * 50),
          rating: metric.rating,
        },
      });
    });
  })
  .catch(() => {});
}
