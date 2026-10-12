/**
 * A unified diff as the server sends it (`difflib.unified_diff`), one line per
 * row: additions and deletions on a green or red tint, hunk headers on the
 * surface colour, file headers muted. The text stays ink-coloured, so it reads
 * at 13 px in both themes; the `+` and `-` prefixes carry the meaning in text
 * too. No grammar and no dependency.
 */

import Box from '@mui/material/Box';

import { smallText } from 'src/sections/agent-chat/styles';
import { semanticColors, typography } from 'src/theme';

type DiffLineKind = 'file' | 'hunk' | 'add' | 'del' | 'context';

/**
 * What each diff line is, by its prefix. `+++` and `---` are the file headers
 * only before the first hunk: inside one they are a changed line that starts
 * with `++` or `--`.
 */
function diffLineKinds(lines: string[]): DiffLineKind[] {
  let inHunk = false;
  return lines.map(line => {
    if (line.startsWith('@@')) {
      inHunk = true;
      return 'hunk';
    }
    if (!inHunk && (line.startsWith('+++') || line.startsWith('---'))) return 'file';
    if (line.startsWith('+')) return 'add';
    if (line.startsWith('-')) return 'del';
    return 'context';
  });
}

const LINE_SX: Record<DiffLineKind, Record<string, string>> = {
  file: { color: semanticColors.mutedText },
  hunk: { color: semanticColors.mutedText, backgroundColor: 'var(--bg-surface)' },
  add: { color: 'var(--ink)', backgroundColor: 'rgba(0, 158, 115, 0.16)' },
  del: { color: 'var(--ink)', backgroundColor: 'rgba(174, 48, 48, 0.16)' },
  context: { color: 'var(--ink)' },
};

export function UnifiedDiff({ diff, label }: { diff: string; label: string }) {
  const lines = diff.replace(/\n$/, '').split('\n');
  const kinds = diffLineKinds(lines);
  return (
    <Box
      component="pre"
      aria-label={label}
      tabIndex={0}
      sx={{
        m: 0,
        p: 1.5,
        fontFamily: typography.mono,
        fontSize: smallText,
        lineHeight: 1.6,
        bgcolor: 'var(--code-bg)',
        border: '1px solid var(--code-border)',
        borderRadius: '8px',
        overflowX: 'auto',
        maxHeight: 520,
        overflowY: 'auto',
        '&:focus-visible': { outline: '2px solid var(--ink-muted)', outlineOffset: 1 },
      }}
    >
      {/* At least as wide as the box, so a tint spans the whole row when it scrolls. */}
      <Box component="code" sx={{ display: 'inline-block', minWidth: '100%', font: 'inherit' }}>
        {lines.map((line, index) => {
          const kind = kinds[index];
          return (
            <Box
              component="span"
              key={index}
              data-line={kind}
              sx={{ display: 'block', whiteSpace: 'pre', px: 0.5, ...LINE_SX[kind] }}
            >
              {line || ' '}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
