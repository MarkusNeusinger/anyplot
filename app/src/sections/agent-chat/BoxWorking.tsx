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

export function BoxWorking({ line }: { line: string }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const started = Date.now();
    const timer = window.setInterval(
      () => setSeconds(Math.floor((Date.now() - started) / 1000)),
      1000
    );
    return () => window.clearInterval(timer);
  }, []);

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
