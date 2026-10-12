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
  it('opens from one line and sends the chat as version 0', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    render(<ChatFeedback sent={null} dataAvailable onSend={onSend} />);

    expect(screen.queryByRole('form')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Give feedback on this chat' }));
    expect(screen.getByRole('form', { name: 'Feedback on this chat' })).toBeInTheDocument();
    expect(screen.getByText('# feedback on this chat')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Idea' }));
    await user.type(screen.getByRole('textbox', { name: 'Feedback message' }), 'no feature column');
    await user.click(screen.getByRole('button', { name: 'Send feedback' }));

    expect(onSend).toHaveBeenCalledWith(0, {
      reaction: 'idea',
      message: 'no feature column',
      includeData: true,
    });
  });

  it('sends without data.csv and says why while the session has no data', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    render(<ChatFeedback sent={null} dataAvailable={false} onSend={onSend} />);
    await user.click(screen.getByRole('button', { name: 'Give feedback on this chat' }));

    const box = screen.getByRole('checkbox', {
      name: 'Include data.csv in the feedback on this chat',
    });
    expect(box).not.toBeChecked();
    expect(box).toBeDisabled();
    expect(screen.getByText('# no data yet')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Bug' }));
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
