/**
 * What the data box waits for, drawn over it: a file read on the server or a parse.
 * Both take seconds while the box itself does not change, so the line names the step,
 * pulses its `…` and counts the seconds from the second one on, and a thin bar runs
 * along the box's foot: a plain indicator, no spinner (docs/reference/style-guide.md
 * §10.1). Hidden from screen readers, which hear the live line under the box; without
 * motion under `prefers-reduced-motion`, where the counter still moves.
 */

import { useEffect, useState } from 'react';

import Box from '@mui/material/Box';

import { Ellipsis } from 'src/sections/agent-chat/Ellipsis';
import { labelSx } from 'src/sections/agent-chat/styles';
import { fontSize } from 'src/theme';

/**
 * `since`: when the step began (`Date.now()`), kept by the caller so a remount (a collapsed
 * and reopened card) does not restart the count. `hidden`: a drag over the box shows its own
 * hint; the count runs on underneath.
 */
export function BoxWorking({
  line,
  since,
  hidden = false,
}: {
  line: string;
  since: number;
  hidden?: boolean;
}) {
  const [mounted] = useState(() => Date.now());
  const [now, setNow] = useState(mounted);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  // A step the caller did not time (0) counts from the mount.
  const seconds = Math.max(0, Math.floor((now - (since > 0 ? since : mounted)) / 1000));

  return (
    <Box
      aria-hidden
      data-testid="box-working"
      sx={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        textAlign: 'center',
        pointerEvents: 'none',
        overflow: 'hidden',
        visibility: hidden ? 'hidden' : 'visible',
        // Dims the text underneath, so the line stands out on the box's own surface in both themes.
        bgcolor: 'color-mix(in srgb, var(--bg-elevated) 55%, transparent)',
        borderRadius: '4px',
      }}
    >
      <Box
        component="span"
        sx={{
          ...labelSx,
          fontSize: fontSize.md,
          color: 'var(--ink)',
          bgcolor: 'var(--bg-elevated)',
          border: '1px solid var(--rule)',
          borderRadius: '4px',
          px: 1.5,
          py: 0.75,
          // A long file or sheet name without spaces wraps instead of being clipped on a phone.
          minWidth: 0,
          maxWidth: '100%',
          overflowWrap: 'anywhere',
        }}
      >
        # {line} <Ellipsis />
        {seconds >= 1 ? ` · ${seconds} s` : ''}
      </Box>
      <Box
        sx={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: '2px',
          overflow: 'hidden',
          '@media (prefers-reduced-motion: reduce)': { display: 'none' },
        }}
      >
        <Box
          sx={{
            '@keyframes agentBoxWorking': {
              '0%': { transform: 'translateX(-100%)' },
              '100%': { transform: 'translateX(340%)' },
            },
            width: '30%',
            height: '100%',
            bgcolor: 'var(--ink-soft)',
            animation: 'agentBoxWorking 1.6s ease-in-out infinite',
          }}
        />
      </Box>
    </Box>
  );
}
