import { createRef } from 'react';

import { describe, expect, it, vi } from 'vitest';

import { AgentApiError, type MemoryEntry, type PlotMemory } from 'src/lib/agent';
import { Remembered, type RememberedProps } from 'src/sections/agent-chat/Remembered';
import { render, screen, userEvent, waitFor, within } from 'src/test-utils';

function deferred() {
  let resolve!: () => void;
  let reject!: (err: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const entry = (id: string, text: string, turn = 2): MemoryEntry => ({
  id,
  kind: 'other',
  target: null,
  text,
  expect: null,
  turn,
});

const LINE = entry('m1', 'horizontal reference line at y = 7');
const LABEL = entry('m2', "x-axis label: 'Zeit (h)'");
const STARS = entry('m3', 'outliers as red stars');
const memoryOf = (...entries: MemoryEntry[]): PlotMemory => ({
  entries,
  max_entries: 30,
  written: true,
});

const section = () => screen.getByRole('region', { name: /remembered/ });
const forgetButton = (text: string) => screen.getByRole('button', { name: `Forget: ${text}` });

function props(overrides: Partial<RememberedProps> = {}): RememberedProps {
  return {
    memory: memoryOf(LINE, LABEL, STARS),
    disabled: false,
    onForget: vi.fn(async () => undefined),
    ...overrides,
  };
}

describe('Remembered', () => {
  it('forgets every decision with .forget_all(), and waits while anything else runs', async () => {
    const onForgetAll = vi.fn(async () => undefined);
    const { rerender } = render(<Remembered {...props({ onForgetAll, disabled: true })} />);
    const all = () => screen.getByRole('button', { name: 'Forget all remembered decisions' });
    expect(all()).toBeDisabled();

    rerender(<Remembered {...props({ onForgetAll })} />);
    await userEvent.click(all());

    await waitFor(() => expect(onForgetAll).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('forgot every decision')).toBeInTheDocument();
  });

  it('offers no .forget_all() without its handler', () => {
    render(<Remembered {...props()} />);
    expect(
      screen.queryByRole('button', { name: 'Forget all remembered decisions' })
    ).not.toBeInTheDocument();
  });

  it('shows nothing but a hidden status while the memory is empty or unknown', () => {
    const { rerender } = render(<Remembered {...props({ memory: null })} />);
    expect(screen.queryByRole('region')).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('');
    rerender(<Remembered {...props({ memory: memoryOf() })} />);
    expect(screen.queryByRole('region')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('lists the decisions oldest first, each with .forget()', () => {
    render(<Remembered {...props()} />);
    expect(section()).toHaveAccessibleName('# remembered · 3 decisions');
    expect(
      within(section())
        .getAllByTestId('memory-entry')
        .map(item => item.firstChild?.textContent)
    ).toEqual([LINE.text, LABEL.text, STARS.text]);
    const forget = forgetButton(LABEL.text);
    expect(forget).toHaveTextContent('.forget()');
    expect(forget).toBeEnabled();
  });

  it('counts one decision in the singular, and says when the memory is full', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<Remembered {...props({ memory: memoryOf(LINE) })} />);
    expect(section()).toHaveAccessibleName('# remembered · 1 decision');
    rerender(
      <Remembered
        {...props({ memory: { entries: [LINE, LABEL], max_entries: 2, written: true } })}
      />
    );
    expect(section()).toHaveAccessibleName('# remembered · 2 decisions · full');
    // What to do about it heads the details behind the ⓘ.
    await user.click(screen.getByRole('button', { name: 'About the remembered decisions' }));
    const details = within(screen.getByRole('dialog', { name: 'About the remembered decisions' }));
    expect(details.getAllByRole('listitem')[0]).toHaveTextContent(
      'full: forget one before a new decision fits'
    );
  });

  it('keeps its heading to one short line, what the list does behind the ⓘ, closed by default', async () => {
    const user = userEvent.setup();
    render(<Remembered {...props()} />);
    expect(screen.queryByText(/every next plot/)).not.toBeInTheDocument();
    const info = screen.getByRole('button', { name: 'About the remembered decisions' });
    expect(info).toHaveAttribute('aria-expanded', 'false');

    await user.click(info);
    const details = within(screen.getByRole('dialog', { name: 'About the remembered decisions' }));
    expect(details.getAllByRole('listitem').map(item => item.textContent)).toEqual([
      'every next plot keeps these decisions, also in another library',
      '.start_over() keeps them too; only .forget() and .forget_all() remove them',
    ]);
    await user.keyboard('{Escape}');
    await waitFor(() => expect(info).toHaveFocus());
  });

  it('folds the list under its heading and opens it again', async () => {
    const user = userEvent.setup();
    render(<Remembered {...props()} />);
    const toggle = screen.getByRole('button', { name: 'Hide the remembered decisions' });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await user.click(toggle);
    expect(screen.queryByRole('button', { name: /^Forget/ })).not.toBeInTheDocument();
    const show = screen.getByRole('button', { name: 'Show the remembered decisions' });
    expect(show).toHaveTextContent('.show()');
    expect(show).toHaveAttribute('aria-expanded', 'false');
    await user.click(show);
    expect(forgetButton(LINE.text)).toBeInTheDocument();
  });

  it('forgets a decision, announces it and moves the focus to the one in its place', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onForget = vi.fn(() => gate.promise);
    const { rerender } = render(<Remembered {...props({ onForget })} />);

    await user.click(forgetButton(LABEL.text));
    expect(onForget).toHaveBeenCalledWith('m2');
    // The page disables everything while the removal runs (`memoryBusy`): the own control keeps the focus.
    rerender(<Remembered {...props({ onForget, disabled: true })} />);
    const own = forgetButton(LABEL.text);
    expect(own).toHaveTextContent('.forget() …');
    expect(own).toHaveAttribute('aria-disabled', 'true');
    expect(own).not.toBeDisabled();
    expect(own).toHaveFocus();
    expect(forgetButton(LINE.text)).toBeDisabled();
    await user.click(own);
    expect(onForget).toHaveBeenCalledTimes(1);

    gate.resolve();
    rerender(<Remembered {...props({ onForget, memory: memoryOf(LINE, STARS) })} />);
    await waitFor(() => expect(forgetButton(STARS.text)).toHaveFocus());
    expect(screen.getByRole('status')).toHaveTextContent(`forgot: ${LABEL.text}`);
    expect(section()).toHaveAccessibleName(/^# remembered · 2 decisions/);
  });

  it('gives the focus to the fallback once the last decision is gone, and still announces it', async () => {
    const user = userEvent.setup();
    const box = createRef<HTMLTextAreaElement>();
    const onForget = vi.fn(async () => undefined);
    const { rerender } = render(
      <>
        <textarea ref={box} aria-label="Message" />
        <Remembered {...props({ onForget, memory: memoryOf(STARS), fallbackFocusRef: box })} />
      </>
    );
    await user.click(forgetButton(STARS.text));
    rerender(
      <>
        <textarea ref={box} aria-label="Message" />
        <Remembered {...props({ onForget, memory: memoryOf(), fallbackFocusRef: box })} />
      </>
    );
    await waitFor(() => expect(screen.getByLabelText('Message')).toHaveFocus());
    expect(screen.queryByRole('region')).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent(`forgot: ${STARS.text}`);
  });

  it('waits while anything else is in flight', () => {
    render(<Remembered {...props({ disabled: true })} />);
    for (const text of [LINE.text, LABEL.text, STARS.text]) {
      expect(forgetButton(text)).toBeDisabled();
    }
    // Folding the list changes nothing on the server: it stays.
    expect(screen.getByRole('button', { name: 'Hide the remembered decisions' })).toBeEnabled();
  });

  it('shows a failed removal under the list with its ref, and clears it once something else runs', async () => {
    const user = userEvent.setup();
    const onForget = vi
      .fn<(id: string) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(409, 'run_active', 'ref-busy'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-gone'))
      .mockRejectedValueOnce(new AgentApiError(500, 'internal', 'ref-500'));
    const { rerender } = render(<Remembered {...props({ onForget })} />);

    // A refusal (4xx) names its cause and shows no ref; a fault of the server does.
    await user.click(forgetButton(LINE.text));
    expect(await screen.findByRole('alert')).toHaveTextContent(
      /^could not forget: a run is in progress in this window; try again when it is done$/
    );
    // The decision stays, and so does the focus on its control.
    expect(forgetButton(LINE.text)).toHaveFocus();
    expect(forgetButton(LINE.text)).toBeEnabled();

    await user.click(forgetButton(STARS.text));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        /^could not forget: the session expired · reload$/
      )
    );
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

    await user.click(forgetButton(LINE.text));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'could not forget: something went wrong on the server · ref ref-500'
      )
    );

    rerender(<Remembered {...props({ onForget, disabled: true })} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
