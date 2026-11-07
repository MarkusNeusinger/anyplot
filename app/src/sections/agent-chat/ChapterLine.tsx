/**
 * A chapter's line in the thread (`threadModel.ts`): `# data` where the talk turns to the data
 * (step 1), `# plot` where it turns to the plot (step 2), centred between two rules (the v4 mock,
 * kit 3 option C). The name is an `h3` heading, so a screen reader can walk the session by its
 * chapters; the `#` is the chat's comment mark and is not read out.
 *
 * The line is a flex row with its rules as pseudo-elements, and the heading holds the name alone:
 * what a chapter will count later (its questions, the plot's remembered decisions) stands in the
 * row beside the heading, between the name and the right-hand rule, so a control never becomes
 * part of the heading's name. The heading carries an id of its own, for a jump to it; the page's
 * `scroll-padding-top` keeps a jump's target clear of the site's sticky masthead.
 */

import Box from '@mui/material/Box';

import { labelSx } from 'src/sections/agent-chat/styles';
import type { Chapter } from 'src/sections/agent-chat/threadModel';

/** The rule on either side of the line's words. */
const rule = { content: '""', flex: '1 1 0', minWidth: 16, borderTop: '1px solid var(--rule)' };

export function ChapterLine({ chapter }: { chapter: Chapter }) {
  return (
    <Box
      data-testid="chapter-line"
      data-chapter={chapter.kind}
      sx={{
        ...labelSx,
        color: 'var(--ink-soft)',
        lineHeight: 1.6,
        display: 'flex',
        alignItems: 'center',
        gap: 1.25,
        minWidth: 0,
        '&::before': rule,
        '&::after': rule,
      }}
    >
      <Box
        component="h3"
        id={`agent-chapter-${chapter.index}`}
        sx={{ font: 'inherit', color: 'inherit', m: 0 }}
      >
        <Box component="span" aria-hidden>
          #{' '}
        </Box>
        {chapter.kind}
      </Box>
    </Box>
  );
}
