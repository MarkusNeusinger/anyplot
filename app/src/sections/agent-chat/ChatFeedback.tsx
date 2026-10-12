/**
 * Quick feedback on the chat itself (version 0), below the composer: for a
 * session that never made a plot, where no result card offers the control.
 * The owner's case of 2026-10-12 (a sine table on `bar-feature-importance`
 * that the assistant could not turn into a feature column) could not be
 * reported and had to be pasted by hand.
 *
 * Collapsed to one line until opened (`.feedback()`), so it never crowds the
 * composer; once a case is stored it shows `ResultFeedback`'s `sent` line with
 * `.edit()`, and a later send replaces the case, as on a result card. The page
 * mounts it while the thread has a turn and the session has no plot, and keeps
 * it while a sent record exists.
 */

import { useState } from 'react';

import Box from '@mui/material/Box';

import type { FeedbackInput, FeedbackRecord } from 'src/hooks/useAgentSession';
import { ResultFeedback } from 'src/sections/agent-chat/ResultFeedback';
import { actionButtonSx, labelSx } from 'src/sections/agent-chat/styles';

export interface ChatFeedbackProps {
  sent: FeedbackRecord | null;
  /** Whether the session holds data that `# include data.csv` could add. */
  dataAvailable: boolean;
  onSend: (version: number, input: FeedbackInput) => Promise<void>;
}

export function ChatFeedback({ sent, dataAvailable, onSend }: ChatFeedbackProps) {
  const [open, setOpen] = useState(false);

  if (!open && !sent) {
    return (
      <Box
        data-testid="chat-feedback"
        sx={{ ...labelSx, display: 'flex', alignItems: 'center', gap: 1 }}
      >
        # no plot yet? tell us what went wrong
        <Box
          component="button"
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Give feedback on this chat"
          sx={actionButtonSx}
        >
          .feedback()
        </Box>
      </Box>
    );
  }
  return (
    <Box data-testid="chat-feedback">
      <ResultFeedback version={0} sent={sent} onSend={onSend} dataAvailable={dataAvailable} />
    </Box>
  );
}
