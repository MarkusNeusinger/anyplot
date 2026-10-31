/**
 * A JavaScript plot's interactive page in its result card (JS-4b-2, route A).
 *
 * The card fetched the version's `plot.html` through its authenticated artifact
 * route (the download's page: the agents service's wrapper around the
 * harness's page). This component frames the API's static relay
 * (`PREVIEW_RELAY_URL`, `api/preview_relay.py`) sandboxed to scripts and posts
 * the page into it; the relay shows it in a sandboxed frame of its own, so the
 * plot code runs three sandboxed frames below the chat and never sees its
 * origin, its token or its cookies.
 *
 * - A handshake, not a `load` event: the page goes out only on the relay's
 *   ready signal (`PREVIEW_RELAY_READY`) from this frame's own window, once per
 *   mount. A page that stands in at the relay's URL (an error or challenge page
 *   of the edge, a route that shadows the path) sends no signal and gets
 *   nothing; a signal from any other window (the plot, a sibling) is ignored.
 * - The target origin is `*`: the relay's origin is opaque (its policy and this
 *   frame's sandbox), so it cannot be named. The page goes only into the frame
 *   this component mounted, whose window the signal came from.
 * - Without a signal within `RELAY_READY_TIMEOUT_MS`, `onUnavailable` reports
 *   `relay_unavailable`, so the card says so instead of showing a blank frame.
 * - The relay frame has the wrapper's own size at scale 1, read from the page
 *   (`pageFrameSize`), and is scaled down to the card's width with a transform,
 *   which pointer events pass through; the parent keys the component by theme,
 *   so a theme switch mounts a fresh relay for the other page.
 */

import { useLayoutEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { pageFrameSize, PREVIEW_RELAY_READY, PREVIEW_RELAY_URL } from 'src/lib/agent';

/** How long the card waits for the relay's signal: the relay is a 1 KB static page of the API. */
export const RELAY_READY_TIMEOUT_MS = 10_000;

export interface InteractivePreviewProps {
  /** The version's `plot.html`, the wrapper the download serves. */
  page: string;
  title: string;
  /** The relay did not answer in time: the card shows the code instead of the frame. */
  onUnavailable: (code: 'relay_unavailable') => void;
}

export function InteractivePreview({ page, title, onUnavailable }: InteractivePreviewProps) {
  const box = useRef<HTMLDivElement>(null);
  const frame = useRef<HTMLIFrameElement>(null);
  const unavailable = useRef(onUnavailable);
  unavailable.current = onUnavailable;
  const { width, height } = pageFrameSize(page);
  const [scale, setScale] = useState(0);

  useLayoutEffect(() => {
    const element = box.current;
    if (!element) return undefined;
    const measure = () => setScale(element.getBoundingClientRect().width / width);
    measure();
    if (typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [width]);

  // A layout effect, so the listener is in place before the relay frame, mounted in the same commit, can answer.
  useLayoutEffect(() => {
    let posted = false;
    const timer = setTimeout(
      () => unavailable.current('relay_unavailable'),
      RELAY_READY_TIMEOUT_MS
    );
    const handleMessage = (event: MessageEvent) => {
      const relay = frame.current?.contentWindow;
      if (posted || !relay || event.source !== relay || event.data !== PREVIEW_RELAY_READY) return;
      posted = true;
      clearTimeout(timer);
      relay.postMessage(page, '*');
    };
    window.addEventListener('message', handleMessage);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('message', handleMessage);
    };
  }, [page]);

  return (
    <Box
      ref={box}
      data-testid="interactive-preview"
      sx={{
        position: 'relative',
        width: '100%',
        aspectRatio: `${width}/${height}`,
        overflow: 'hidden',
      }}
    >
      <iframe
        ref={frame}
        src={PREVIEW_RELAY_URL}
        sandbox="allow-scripts"
        referrerPolicy="no-referrer"
        title={title}
        style={{
          display: 'block',
          border: 0,
          width: `${width}px`,
          height: `${height}px`,
          transform: `scale(${scale})`,
          transformOrigin: '0 0',
          visibility: scale > 0 ? 'visible' : 'hidden',
        }}
      />
    </Box>
  );
}
