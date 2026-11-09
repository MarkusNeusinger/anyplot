/**
 * The service's mood on the chat frame's tab, after the path (kit 5 option C, the owner's pick):
 * `~/anyplot.ai/agent · ● quiet`, `● busy`, `● resting until 01:00`, the time on the visitor's
 * own clock. One word and a dot, the same for every visitor and for an admin: no numbers, which
 * the admin meters in the admin menu hold. Busy while turns wait in the run queue or the own turn
 * waits there; where the own turn stands, the working line says (`waiting · you are 3rd`).
 *
 * The word carries the state, in the tab's `--ink-soft`; the dot beside it is a status glyph in
 * the brand green, the warning amber or the error red (`colors.primary`, `.warning`, `.error`),
 * hidden from screen readers. The element is a status region of its own, outside the path's
 * hidden box: a screen reader hears "the assistant is busy" when the mood changes. The page
 * mounts it with the first answer and keeps it, so the mood a visitor meets is not read out on
 * arrival; a failed first read shows none.
 */

import Box from '@mui/material/Box';

import { type Mood, moodText } from 'src/hooks/useAgentStatus';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

const DOT: Record<Mood['kind'], string> = {
  quiet: colors.primary,
  busy: colors.warning,
  resting: colors.error,
};

export function LoadMood({ mood }: { mood: Mood }) {
  return (
    <Box component="span" role="status" data-testid="load-mood" data-mood={mood.kind}>
      <span aria-hidden>
        {' · '}
        <Box component="span" sx={{ color: DOT[mood.kind] }}>
          ●
        </Box>{' '}
      </span>
      <Box component="span" sx={visuallyHiddenSx}>
        the assistant is{' '}
      </Box>
      {moodText(mood)}
    </Box>
  );
}
