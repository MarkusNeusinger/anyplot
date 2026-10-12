/**
 * Promote one case to the regression harness, or take the promotion back.
 *
 * Promotion is a timestamp on the row plus the outcome the harness checks
 * (`expected`); `sync_cases` on the dev machine pulls promoted cases into
 * `agents/evals/.cases/`. The outcome is preselected from the reaction rule for
 * the thumbs and must be chosen for a bug or an idea. A case without its
 * `data.csv` cannot be promoted: the harness cannot run it (`422 no_data`).
 * The promotion rule under the control is guidance; nothing enforces it.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import type { CaseExpected, CasePatch, FeedbackReaction } from 'src/lib/agent';
import { ghostButtonSx } from 'src/sections/agent-chat/styles';
import { expectedFromReaction } from 'src/sections/debug/acceptMatch';
import { formatUtc } from 'src/sections/debug/format';
import { detailControlSx, detailMutedSx, detailTextSx } from 'src/sections/debug/styles';

export const PROMOTION_HINT =
  "promote only when your reaction contradicts the pipeline outcome, when the case shows a class no fixture covers, or when it is a bug or idea with a reproducer; retire the case (done or won't solve) once a fixture or a test covers it.";

export interface PromoteControlProps {
  reaction: FeedbackReaction;
  /** The outcome stored on the row, if any. */
  expected: CaseExpected | null;
  promotedAt: string | null;
  includeData: boolean;
  /** A case on the chat itself (version 0): no plot the harness could replay. */
  noPlot?: boolean;
  /** A change of this case is in flight. */
  busy: boolean;
  onPatch: (patch: CasePatch) => void;
}

export function PromoteControl({
  reaction,
  expected,
  promotedAt,
  includeData,
  noPlot = false,
  busy,
  onPatch,
}: PromoteControlProps) {
  // The outcome shown while the row has none: the reaction rule, or empty for a bug or an idea.
  const [choice, setChoice] = useState<CaseExpected | ''>(
    () => expectedFromReaction(reaction) ?? ''
  );
  const value: CaseExpected | '' = expected ?? choice;
  const promoted = promotedAt !== null;

  const changeExpected = (next: CaseExpected | '') => {
    setChoice(next);
    if (next && next !== expected) onPatch({ expected: next });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, minWidth: 0 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
        <Box
          component="label"
          sx={{ ...detailMutedSx, display: 'inline-flex', alignItems: 'center', gap: 0.75 }}
        >
          expected
          <Box
            component="select"
            aria-label="Expected outcome"
            value={value}
            disabled={busy}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              changeExpected(event.target.value as CaseExpected | '')
            }
            sx={{ ...detailControlSx, cursor: 'pointer' }}
          >
            {!promoted && <option value="">—</option>}
            <option value="accepted">accepted</option>
            <option value="rejected">rejected</option>
          </Box>
        </Box>
        {promoted ? (
          <>
            <Box component="span" sx={detailTextSx}>
              promoted {formatUtc(promotedAt)}
            </Box>
            <Box
              component="button"
              type="button"
              aria-label="Take back the promotion"
              disabled={busy}
              onClick={() => onPatch({ promoted: false })}
              sx={ghostButtonSx}
            >
              .unpromote()
            </Box>
          </>
        ) : (
          <Box
            component="button"
            type="button"
            aria-label="Promote to an eval case"
            disabled={busy || noPlot || !includeData || value === ''}
            title={value === '' ? 'choose an expected outcome first' : undefined}
            onClick={() => {
              if (value) onPatch({ promoted: true, expected: value });
            }}
            sx={ghostButtonSx}
          >
            .promote()
          </Box>
        )}
      </Box>
      {noPlot && !promoted ? (
        <Box sx={detailMutedSx}>
          no plot: a chat case belongs in the prep or scope eval fixtures, not the plot harness
        </Box>
      ) : (
        !includeData &&
        !promoted && <Box sx={detailMutedSx}>no data file: the harness cannot run this case</Box>
      )}
      <Box sx={{ ...detailMutedSx, maxWidth: '72ch' }}>{PROMOTION_HINT}</Box>
    </Box>
  );
}
