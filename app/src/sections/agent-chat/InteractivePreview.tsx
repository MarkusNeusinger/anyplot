/**
 * A JavaScript plot's interactive page in its result card (JS-4b-2, route A).
 *
 * The card fetched the version's `plot.html` through its authenticated artifact
 * route (the download's page: the agents service's wrapper around the
 * harness's page). This component frames the API's static relay
 * (`PREVIEW_RELAY_URL`, `api/preview_relay.py`) sandboxed to scripts and posts
 * the page into it once, on the relay frame's first `load`; the relay shows it
 * in a sandboxed frame of its own, so the plot code runs three sandboxed frames
 * below the chat and never sees its origin, its token or its cookies.
 *
 * - The target origin is `*`: the relay's origin is opaque (its policy and this
 *   frame's sandbox), so it cannot be named. The page goes only into the frame
 *   this component has just mounted, and only on its first load; a later load
 *   (the frame navigated, which the plot code cannot do) gets nothing.
 * - Nothing comes back: the relay never posts to its parent, and this
 *   component listens to no message.
 * - The relay frame keeps the wrapper's own size at scale 1 (`PAGE_FRAME_SIZES`)
 *   and is scaled down to the card's width with a transform, which pointer
 *   events pass through; the parent keys the component by theme, so a theme
 *   switch mounts a fresh relay for the other page.
 */

import { useLayoutEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { PAGE_FRAME_SIZES, PREVIEW_RELAY_URL } from 'src/lib/agent';

export interface InteractivePreviewProps {
  /** The version's `plot.html`, the wrapper the download serves. */
  page: string;
  /** A square plot (1200x1200 CSS pixels) rather than a landscape one (1600x900). */
  square: boolean;
  title: string;
}

export function InteractivePreview({ page, square, title }: InteractivePreviewProps) {
  const box = useRef<HTMLDivElement>(null);
  const frame = useRef<HTMLIFrameElement>(null);
  const posted = useRef(false);
  const { width, height } = square ? PAGE_FRAME_SIZES.square : PAGE_FRAME_SIZES.landscape;
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

  const handleLoad = () => {
    if (posted.current) return;
    posted.current = true;
    frame.current?.contentWindow?.postMessage(page, '*');
  };

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
        onLoad={handleLoad}
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
