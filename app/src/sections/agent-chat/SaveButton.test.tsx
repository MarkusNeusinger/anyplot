import { describe, expect, it, vi } from 'vitest';

import { AgentApiError } from 'src/lib/agent';
import { SaveButton } from 'src/sections/agent-chat/SaveButton';
import { render, screen, userEvent, waitFor } from 'src/test-utils';

function deferred() {
  let resolve!: () => void;
  let reject!: (err: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('SaveButton', () => {
  it('is disabled while the page says so, and the data box starts ticked', () => {
    const onSave = vi.fn(async () => undefined);
    const { rerender } = render(<SaveButton disabled onSave={onSave} />);
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).toBeChecked();

    rerender(<SaveButton disabled={false} onSave={onSave} />);
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
  });

  it('saves with the data by default and without it once unticked', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(async () => undefined);
    render(<SaveButton disabled={false} onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(onSave).toHaveBeenLastCalledWith(true);

    await user.click(screen.getByRole('checkbox', { name: '# include data.csv' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(onSave).toHaveBeenLastCalledWith(false);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows the save in progress and starts no second one', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onSave = vi.fn(() => gate.promise);
    render(<SaveButton disabled={false} onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: 'Save' }));
    const button = screen.getByRole('button', { name: 'Save' });
    expect(button).toHaveTextContent('.save() …');
    expect(button).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).toBeDisabled();
    await user.click(button);
    expect(onSave).toHaveBeenCalledTimes(1);

    gate.resolve();
    await waitFor(() => expect(button).toHaveTextContent('.save()'));
    expect(button).not.toHaveTextContent('…');
    expect(button).toBeEnabled();
  });

  it('shows a failure under the button with its ref, and clears it on the next try', async () => {
    const user = userEvent.setup();
    const onSave = vi
      .fn<(includeData: boolean) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(502, 'too_large', 'ref-big'))
      .mockResolvedValueOnce(undefined);
    render(<SaveButton disabled={false} onSave={onSave} />);

    await user.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'the session is over 32 MB, too large for one file · ref ref-big'
    );

    await user.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });

  it('offers a reload for an expired session and reads other codes as the page does', async () => {
    const user = userEvent.setup();
    const onSave = vi
      .fn<(includeData: boolean) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'r1'))
      .mockRejectedValueOnce(new AgentApiError(502, 'upstream', 'r2'))
      .mockRejectedValueOnce(new TypeError('Failed to fetch'));
    render(<SaveButton disabled={false} onSave={onSave} />);
    const save = screen.getByRole('button', { name: 'Save' });

    await user.click(save);
    expect(await screen.findByRole('alert')).toHaveTextContent('the session expired · ref r1');
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

    await user.click(save);
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'the agents service did not answer or cut the stream · ref r2'
      )
    );

    await user.click(save);
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'the server did not answer; check your connection'
      )
    );
  });
});
