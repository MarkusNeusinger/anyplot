import { describe, expect, it, vi } from 'vitest';

import type { FeedbackInput, FeedbackRecord } from 'src/hooks/useAgentSession';
import { ChatFeedback } from 'src/sections/agent-chat/ChatFeedback';
import { render, screen, userEvent } from 'src/test-utils';

type Send = (version: number, input: FeedbackInput) => Promise<void>;

const SENT: FeedbackRecord = {
  reaction: 'idea',
  message: 'sin x as a feature column',
  includeData: true,
  caseId: 'c0',
};

describe('ChatFeedback', () => {
  it('is the form .feedback() opens, takes the focus once, and sends the chat as version 0', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    // `.feedback()` at the status line's end went with its click: the form's first reaction
    // takes the focus, and only once.
    const takeFocus = vi.fn().mockReturnValueOnce(true).mockReturnValue(false);
    render(<ChatFeedback sent={null} dataAvailable onSend={onSend} takeFocus={takeFocus} />);

    expect(screen.getByRole('form', { name: 'Feedback on this chat' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Thumbs up' })).toHaveFocus();
    expect(takeFocus).toHaveBeenCalledTimes(1);
    expect(screen.getByText('# feedback on this chat')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Idea' }));
    await user.type(screen.getByRole('textbox', { name: 'Feedback message' }), 'no feature column');
    await user.click(screen.getByRole('button', { name: 'Send feedback' }));

    // The data box starts unticked, for an admin as for a visitor.
    expect(onSend).toHaveBeenCalledWith(0, {
      reaction: 'idea',
      message: 'no feature column',
      includeData: false,
    });
  });

  it('sends without data.csv and says why while the session has no data', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    render(<ChatFeedback sent={null} dataAvailable={false} onSend={onSend} />);
    // A form that mounts again later, after a turn, leaves the focus where it is.
    expect(document.body).toHaveFocus();
    await user.click(screen.getByRole('button', { name: 'Bug' }));

    const box = screen.getByRole('checkbox', {
      name: 'Include data.csv in the feedback on this chat',
    });
    expect(box).not.toBeChecked();
    expect(box).toBeDisabled();
    expect(screen.getByText('# no data yet')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Send feedback' }));

    expect(onSend).toHaveBeenCalledWith(0, { reaction: 'bug', message: '', includeData: false });
  });

  it('shows a stored case as sent on this chat, with .edit()', () => {
    render(<ChatFeedback sent={SENT} dataAvailable onSend={vi.fn<Send>()} />);

    expect(screen.getByTestId('result-feedback-sent')).toHaveTextContent('sent · this chat');
    expect(
      screen.getByRole('button', { name: 'Edit the feedback on this chat' })
    ).toBeInTheDocument();
  });
});
