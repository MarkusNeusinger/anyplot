/**
 * Quick feedback on the chat itself (version 0): for a session that never made a plot, where no
 * result card offers the control. The owner's case of 2026-10-12 (a sine table on
 * `bar-feature-importance` that the assistant could not turn into a feature column) could not be
 * reported and had to be pasted by hand.
 *
 * The control that opens it, `.feedback()`, stands at the end of the line at the chat frame's foot
 * (`StatusLine`, `ChatFrame.tsx`), so it never crowds the composer; this is the form it opens,
 * right above that line, or once a case is stored `ResultFeedback`'s `sent` line with `.edit()`,
 * and a later send replaces the case, as on a result card. The page shows `.feedback()` while the
 * thread has a turn, no turn is running (a running one may still bring the plot) and the session
 * has no plot, and keeps the form while a sent record exists.
 */

import { useEffect, useRef } from 'react';

import Box from '@mui/material/Box';

import type { FeedbackInput, FeedbackRecord } from 'src/hooks/useAgentSession';
import { ResultFeedback } from 'src/sections/agent-chat/ResultFeedback';

export interface ChatFeedbackProps {
  sent: FeedbackRecord | null;
  /** Whether the session holds data that `# include data.csv` could add. */
  dataAvailable: boolean;
  onSend: (version: number, input: FeedbackInput) => Promise<void>;
  /**
   * Asked once as the form mounts: true when `.feedback()` opened it this moment. The button went
   * with the click, so the focus moves on to the form's first reaction instead of falling back
   * to the page's top; a form that mounts again later (after a turn) leaves the focus alone.
   */
  takeFocus?: () => boolean;
}

export function ChatFeedback({ sent, dataAvailable, onSend, takeFocus }: ChatFeedbackProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (takeFocus?.()) rootRef.current?.querySelector<HTMLButtonElement>('button')?.focus();
  }, [takeFocus]);
  return (
    <Box data-testid="chat-feedback" ref={rootRef}>
      <ResultFeedback version={0} sent={sent} onSend={onSend} dataAvailable={dataAvailable} />
    </Box>
  );
}
