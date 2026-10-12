import { describe, expect, it, vi } from 'vitest';

import type { FeedbackInput, FeedbackRecord } from 'src/hooks/useAgentSession';
import { AgentApiError } from 'src/lib/agent';
import { ResultFeedback } from 'src/sections/agent-chat/ResultFeedback';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

type Send = (version: number, input: FeedbackInput) => Promise<void>;

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>(res => {
    resolve = res;
  });
  return { promise, resolve };
}

const SENT: FeedbackRecord = {
  reaction: 'thumbs_down',
  message: 'the legend hides the points',
  includeData: true,
  caseId: 'c1',
};

const sendButton = () => screen.getByRole('button', { name: 'Send feedback' });
const dataBox = (version: number) =>
  screen.getByRole('checkbox', { name: `Include data.csv in the feedback on version ${version}` });
const sentLine = () => screen.getByTestId('result-feedback-sent');

describe('ResultFeedback', () => {
  it('offers the four reactions and sends only once one is picked', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    render(<ResultFeedback version={3} sent={null} onSend={onSend} />);

    const group = screen.getByRole('group', { name: 'Reaction' });
    for (const name of ['Thumbs up', 'Thumbs down', 'Idea', 'Bug']) {
      expect(screen.getByRole('button', { name })).toHaveAttribute('aria-pressed', 'false');
    }
    expect(group.querySelectorAll('button')).toHaveLength(4);
    expect(sendButton()).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Bug' }));
    expect(screen.getByRole('button', { name: 'Bug' })).toHaveAttribute('aria-pressed', 'true');
    await user.click(screen.getByRole('button', { name: 'Thumbs down' }));
    expect(screen.getByRole('button', { name: 'Bug' })).toHaveAttribute('aria-pressed', 'false');
    await user.type(screen.getByRole('textbox', { name: 'Feedback message' }), 'too dark');
    await user.click(sendButton());

    expect(onSend).toHaveBeenCalledWith(3, {
      reaction: 'thumbs_down',
      message: 'too dark',
      includeData: true,
    });
  });

  it('keeps the text to 500 characters and counts them', async () => {
    const user = userEvent.setup();
    render(<ResultFeedback version={1} sent={null} onSend={vi.fn<Send>()} />);
    const box = screen.getByRole('textbox', { name: 'Feedback message' });
    expect(box).toHaveAttribute('maxLength', '500');

    await user.click(box);
    await user.paste('x'.repeat(520));
    expect(box).toHaveValue('x'.repeat(500));
    expect(screen.getByText('500/500')).toBeInTheDocument();
  });

  it('sends the data by default and without it once the box is unticked', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    render(<ResultFeedback version={2} sent={null} onSend={onSend} />);
    const box = dataBox(2);
    expect(box).toBeChecked();

    await user.click(box);
    await user.click(screen.getByRole('button', { name: 'Thumbs up' }));
    await user.click(sendButton());
    expect(onSend).toHaveBeenLastCalledWith(2, {
      reaction: 'thumbs_up',
      message: '',
      includeData: false,
    });
  });

  it('shows what was sent, and an edit replaces it with a new case', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    const { rerender } = render(<ResultFeedback version={3} sent={null} onSend={onSend} />);

    await user.click(screen.getByRole('button', { name: 'Thumbs down' }));
    await user.click(sendButton());
    // The page records the stored case on the version; the control shows it.
    rerender(<ResultFeedback version={3} sent={SENT} onSend={onSend} />);
    expect(sentLine()).toHaveTextContent('sent · v3 · thumbs down · with data.csv');
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit the feedback on version 3' }));
    expect(screen.getByRole('textbox', { name: 'Feedback message' })).toHaveValue(
      'the legend hides the points'
    );
    expect(screen.getByRole('button', { name: 'Thumbs down' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    await user.click(screen.getByRole('button', { name: 'Idea' }));
    await user.click(dataBox(3));
    await user.click(sendButton());
    expect(onSend).toHaveBeenLastCalledWith(3, {
      reaction: 'idea',
      message: 'the legend hides the points',
      includeData: false,
    });

    rerender(
      <ResultFeedback
        version={3}
        sent={{ ...SENT, reaction: 'idea', includeData: false, caseId: 'c2' }}
        onSend={onSend}
      />
    );
    expect(sentLine()).toHaveTextContent('sent · v3 · idea');
    expect(sentLine()).not.toHaveTextContent('with data.csv');
  });

  it('leaves an edit with .cancel() and shows the case sent before', async () => {
    const user = userEvent.setup();
    render(<ResultFeedback version={4} sent={SENT} onSend={vi.fn<Send>()} />);
    await user.click(screen.getByRole('button', { name: 'Edit the feedback on version 4' }));
    await user.click(
      screen.getByRole('button', { name: 'Cancel the edit of the feedback on version 4' })
    );
    expect(sentLine()).toHaveTextContent('sent · v4');
  });

  it('announces a stored case and moves the focus across the swap', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn<Send>(async () => undefined);
    const { rerender } = render(<ResultFeedback version={3} sent={null} onSend={onSend} />);
    // Mounted, and empty, before anything is sent: a live region must exist before its text.
    expect(screen.getByRole('status')).toBeEmptyDOMElement();

    await user.click(screen.getByRole('button', { name: 'Thumbs down' }));
    sendButton().focus();
    await user.keyboard('{Enter}');
    await waitFor(() =>
      expect(screen.getByRole('status')).toHaveTextContent(
        'Feedback sent on version 3: Thumbs down, with data.csv.'
      )
    );
    rerender(<ResultFeedback version={3} sent={SENT} onSend={onSend} />);

    const edit = screen.getByRole('button', { name: 'Edit the feedback on version 3' });
    await waitFor(() => expect(edit).toHaveFocus());

    await user.keyboard('{Enter}');
    expect(screen.getByRole('status')).toBeEmptyDOMElement();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Thumbs down' })).toHaveFocus());

    await user.click(
      screen.getByRole('button', { name: 'Cancel the edit of the feedback on version 3' })
    );
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Edit the feedback on version 3' })).toHaveFocus()
    );
  });

  it('leaves the focus where the user moved it while the send ran', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onSend = vi.fn<Send>(() => gate.promise);
    const { rerender } = render(
      <>
        <input aria-label="Composer" />
        <ResultFeedback version={1} sent={null} onSend={onSend} />
      </>
    );

    await user.click(screen.getByRole('button', { name: 'Bug' }));
    await user.click(sendButton());
    await user.click(screen.getByRole('textbox', { name: 'Composer' }));
    gate.resolve();
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Feedback sent'));
    rerender(
      <>
        <input aria-label="Composer" />
        <ResultFeedback version={1} sent={{ ...SENT, reaction: 'bug' }} onSend={onSend} />
      </>
    );

    expect(sentLine()).toHaveTextContent('sent · v1 · bug');
    expect(screen.getByRole('textbox', { name: 'Composer' })).toHaveFocus();
  });

  it('shows the send in progress, locks its inputs and sends once', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onSend = vi.fn<Send>(() => gate.promise);
    render(<ResultFeedback version={1} sent={null} onSend={onSend} />);

    await user.click(screen.getByRole('button', { name: 'Bug' }));
    await user.click(sendButton());
    expect(sendButton()).toHaveTextContent('.send() …');
    expect(sendButton()).toHaveAttribute('aria-disabled', 'true');
    expect(sendButton()).toHaveFocus();
    expect(screen.getByRole('textbox', { name: 'Feedback message' })).toBeDisabled();
    expect(dataBox(1)).toBeDisabled();
    await user.click(sendButton());
    expect(onSend).toHaveBeenCalledTimes(1);

    gate.resolve();
    await waitFor(() => expect(sendButton()).toHaveTextContent(/^\.send\(\)$/));
  });

  it('shows a failure with its ref and clears it on the next try', async () => {
    const user = userEvent.setup();
    const onSend = vi
      .fn<Send>()
      .mockRejectedValueOnce(new AgentApiError(502, 'storage', 'ref-st'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-se'))
      .mockResolvedValueOnce(undefined);
    render(<ResultFeedback version={1} sent={null} onSend={onSend} />);

    await user.click(screen.getByRole('button', { name: 'Thumbs up' }));
    await user.click(sendButton());
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'the case could not be stored; try again · ref ref-st'
    );

    await user.click(sendButton());
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('the session expired · ref ref-se')
    );
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

    await user.click(sendButton());
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });
});
