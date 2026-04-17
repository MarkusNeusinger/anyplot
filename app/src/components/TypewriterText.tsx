import Box from '@mui/material/Box';
import { useTypewriter } from '../hooks/useTypewriter';
import { colors } from '../theme';

interface TypewriterTextProps {
  lines: string[];
  charDelay?: number;
  linePause?: number;
  startDelay?: number;
  /** Color of the blinking cursor. Defaults to brand green. */
  cursorColor?: string;
  /** Rendered as `component` on each line wrapper. */
  lineComponent?: React.ElementType;
  className?: string;
  sx?: React.ComponentProps<typeof Box>['sx'];
}

/**
 * Renders `lines` with a typewriter effect. A blinking cursor sits at the end
 * of the current line while typing, and at the end of the last line when done.
 */
export function TypewriterText({
  lines,
  charDelay,
  linePause,
  startDelay,
  cursorColor = colors.primary,
  lineComponent = 'div',
  sx,
}: TypewriterTextProps) {
  const { rendered, activeLine, done } = useTypewriter(lines, {
    charDelay,
    linePause,
    startDelay,
  });
  const cursorLine = done ? lines.length - 1 : activeLine;

  return (
    <Box sx={sx}>
      {rendered.map((text, idx) => (
        <Box key={idx} component={lineComponent} sx={{ minHeight: '1.7em' }}>
          {text}
          {idx === cursorLine && (
            <Box
              component="span"
              className="anyplot-cursor"
              aria-hidden="true"
              sx={{
                display: 'inline-block',
                width: '0.55em',
                height: '1em',
                bgcolor: cursorColor,
                verticalAlign: '-0.12em',
                ml: '2px',
                animation: 'blink 1s steps(2) infinite',
              }}
            />
          )}
        </Box>
      ))}
    </Box>
  );
}
