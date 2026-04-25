import { useCallback, useRef, useMemo } from "react";
import { RESERVED_TOP_LEVEL } from "../utils/paths";

interface EventProps {
  [key: string]: string | undefined;
}

// Module-level ambient props attached to every pageview and custom event.
// Set by the layout once theme/locale-style values are known so we don't have
// to thread them through every component that fires an event. Empty-string
// values clear the key (so callers can effectively reset a prop).
let ambientProps: Record<string, string> = {};

export function setAnalyticsAmbientProps(props: Record<string, string>): void {
  const merged: Record<string, string> = { ...ambientProps, ...props };
  for (const key of Object.keys(merged)) {
    if (!merged[key]) delete merged[key];
  }
  ambientProps = merged;
}

// Snapshot of current ambient props for callers that fire `window.plausible`
// directly (e.g. reportWebVitals.ts, which runs outside React).
export function getAnalyticsAmbientProps(): Record<string, string> {
  return { ...ambientProps };
}

function debounce<T extends (...args: never[]) => void>(
  fn: T,
  delay: number,
): T {
  let timeoutId: ReturnType<typeof setTimeout>;
  return ((...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  }) as T;
}

// Konvertiert Query-Params zu Pfad-Segmenten für Plausible
// Unterstützt mehrfache Params (AND) und Komma-Werte (OR)
// /?lib=matplotlib&lib=seaborn → /lib/matplotlib/lib/seaborn
// /?lib=matplotlib,seaborn → /lib/matplotlib,seaborn
function buildPlausibleUrl(): string {
  const params = new URLSearchParams(window.location.search);
  const segments: string[] = [];

  // Preserve the current spec/language/library path prefix if present.
  // For routes like /:specId/:language[/:library] we keep the full pathname so
  // filter segments are appended after it. Reserved top-level routes use no prefix.
  const pathname = window.location.pathname;
  const parts = pathname.split("/").filter(Boolean);
  const pathPrefix =
    parts.length > 0 && !RESERVED_TOP_LEVEL.has(parts[0]) ? `/${parts.join("/")}` : "";

  // Definierte Reihenfolge der Filter-Kategorien (inkl. impl-level tags).
  // `language` is included so the hub's ?language= filter is tracked as a
  // distinct pageview path (/{spec}/language/python), matching the path-segment
  // convention used for all other filter params.
  const orderedKeys = [
    "lib",
    "spec",
    "plot",
    "data",
    "dom",
    "feat",
    "dep",
    "tech",
    "pat",
    "prep",
    "style",
    "language",
  ];

  for (const key of orderedKeys) {
    // getAll() für mehrfache Params mit gleichem Key (AND-Logik)
    const values = params.getAll(key);
    for (const value of values) {
      if (value) {
        // Komma-Werte bleiben erhalten (OR-Logik)
        segments.push(key, value);
      }
    }
  }

  return segments.length > 0
    ? `https://anyplot.ai${pathPrefix}/${segments.join("/")}`
    : `https://anyplot.ai${pathPrefix || "/"}`;
}

export function useAnalytics() {
  const lastPageviewRef = useRef<string>("");
  const isProduction =
    typeof window !== "undefined" && window.location.hostname === "anyplot.ai";

  const sendPageview = useCallback(
    (urlOverride?: string) => {
      if (!isProduction) return;

      let url: string;
      if (urlOverride) {
        // Validate urlOverride: must start with "/" and contain only safe characters
        if (!/^\/[\w\-/]*$/.test(urlOverride)) {
          return; // Invalid URL, skip tracking
        }
        url = `https://anyplot.ai${urlOverride}`;
      } else {
        url = buildPlausibleUrl();
      }

      if (url === lastPageviewRef.current) return;
      lastPageviewRef.current = url;

      const props = Object.keys(ambientProps).length > 0 ? { ...ambientProps } : undefined;
      window.plausible?.("pageview", props ? { url, props } : { url });
    },
    [isProduction],
  );

  const trackPageview = useMemo(
    () => debounce(sendPageview, 150),
    [sendPageview],
  );

  const trackEvent = useCallback(
    (name: string, props?: EventProps) => {
      if (!isProduction) return;
      const cleanProps = props
        ? Object.fromEntries(
            Object.entries(props).filter(([, v]) => v !== undefined),
          )
        : {};
      const merged = { ...ambientProps, ...cleanProps } as Record<string, string>;
      window.plausible?.(
        name,
        Object.keys(merged).length > 0 ? { props: merged } : undefined,
      );
    },
    [isProduction],
  );

  return { trackPageview, trackEvent };
}
