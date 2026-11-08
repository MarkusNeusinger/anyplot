import { createRef, type ReactNode, useRef, useState } from 'react';

import { describe, expect, it, vi } from 'vitest';

import { AgentApiError, type MemoryEntry, type PlotMemory } from 'src/lib/agent';
import {
  Remembered,
  RememberedCount,
  type RememberedProps,
} from 'src/sections/agent-chat/Remembered';
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

const LIST_ID = 'decisions';
const count = () => screen.getByTestId('decisions-toggle');
const list = () => screen.getByRole('list', { name: 'Remembered decisions' });
const forgetButton = (text: string) => screen.getByRole('button', { name: `Forget: ${text}` });

type ListProps = Omit<RememberedProps, 'id' | 'open' | 'onAnnounce'>;

function props(overrides: Partial<ListProps> = {}): ListProps {
  return {
    memory: memoryOf(LINE, LABEL, STARS),
    disabled: false,
    onForget: vi.fn(async () => undefined),
    ...overrides,
  };
}

/**
 * A chapter line with the count and the list under it, as the thread renders them, and the page's
 * status region, which announces a removal outside the thread's log.
 */
function Decisions({ open: startOpen = true, ...list }: ListProps & { open?: boolean }) {
  const [open, setOpen] = useState(startOpen);
  const [note, setNote] = useState('');
  const handoffRef = useRef(false);
  return (
    <>
      <div data-testid="line">
        <h3># plot</h3>
        <RememberedCount
          memory={list.memory}
          open={open}
          listId={LIST_ID}
          onToggle={() => setOpen(value => !value)}
          handoffRef={handoffRef}
        />
      </div>
      <Remembered {...list} id={LIST_ID} open={open} onAnnounce={setNote} />
      <div role="status">{note}</div>
    </>
  );
}

describe('Remembered', () => {
  it('shows no count and no list while the memory is empty or unknown: never "0 decisions"', () => {
    const { rerender } = render(<Decisions {...props({ memory: null })} />);
    expect(screen.queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    expect(screen.queryByTestId('plot-memory')).not.toBeInTheDocument();
    rerender(<Decisions {...props({ memory: memoryOf() })} />);
    expect(screen.queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(screen.getByTestId('line')).not.toHaveTextContent(/decision/);
  });

  it('folds the list under its count by default and unfolds it, oldest first, each with .forget()', async () => {
    const user = userEvent.setup();
    render(<Decisions {...props()} open={false} />);
    expect(count()).toHaveTextContent('3 decisions');
    expect(count()).toHaveAccessibleName('3 decisions remembered');
    expect(count()).toHaveAttribute('aria-expanded', 'false');
    expect(count()).toHaveAttribute('aria-controls', LIST_ID);
    expect(screen.getByTestId('plot-memory')).not.toBeVisible();
    expect(screen.queryByRole('button', { name: /^Forget/ })).not.toBeInTheDocument();

    await user.click(count());
    expect(count()).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByTestId('plot-memory')).toHaveAttribute('id', LIST_ID);
    expect(screen.getByTestId('plot-memory')).toBeVisible();
    expect(
      within(list())
        .getAllByTestId('memory-entry')
        .map(item => item.firstChild?.textContent)
    ).toEqual([LINE.text, LABEL.text, STARS.text]);
    expect(forgetButton(LABEL.text)).toHaveTextContent('.forget()');
    // The list is no live region of its own: the log does not read it out as it unfolds.
    expect(screen.getByTestId('plot-memory')).toHaveAttribute('aria-live', 'off');
    await user.click(count());
    expect(screen.getByTestId('plot-memory')).not.toBeVisible();
  });

  it('counts one decision in the singular, and says when the memory is full', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<Decisions {...props({ memory: memoryOf(LINE) })} />);
    expect(count()).toHaveTextContent('1 decision');
    expect(screen.getByTestId('line')).not.toHaveTextContent('full');
    rerender(
      <Decisions
        {...props({ memory: { entries: [LINE, LABEL], max_entries: 2, written: true } })}
      />
    );
    expect(screen.getByTestId('line')).toHaveTextContent('# plot2 decisions ▴·full');
    // What to do about it heads the details behind the ⓘ at the list's end.
    await user.click(screen.getByRole('button', { name: 'About the remembered decisions' }));
    const details = within(screen.getByRole('dialog', { name: 'About the remembered decisions' }));
    expect(details.getAllByRole('listitem')[0]).toHaveTextContent(
      'full: forget one before a new decision fits'
    );
  });

  it('keeps what the list does behind the ⓘ at its end', async () => {
    const user = userEvent.setup();
    render(<Decisions {...props({ onForgetAll: vi.fn(async () => undefined) })} />);
    expect(screen.queryByText(/every next plot/)).not.toBeInTheDocument();
    const info = screen.getByRole('button', { name: 'About the remembered decisions' });
    // `.forget_all()` and the ⓘ follow the decisions.
    const buttons = within(screen.getByTestId('plot-memory')).getAllByRole('button');
    expect(buttons.slice(-2)).toEqual([
      screen.getByRole('button', { name: 'Forget all remembered decisions' }),
      info,
    ]);

    await user.click(info);
    const details = within(screen.getByRole('dialog', { name: 'About the remembered decisions' }));
    expect(details.getAllByRole('listitem').map(item => item.textContent)).toEqual([
      'every next plot keeps these decisions, also in another library',
      '.start_over() keeps them too; only .forget() and .forget_all() remove them',
    ]);
    await user.keyboard('{Escape}');
    await waitFor(() => expect(info).toHaveFocus());
  });

  it('forgets every decision with .forget_all(), and waits while anything else runs', async () => {
    const onForgetAll = vi.fn(async () => undefined);
    const { rerender } = render(<Decisions {...props({ onForgetAll, disabled: true })} />);
    const all = () => screen.getByRole('button', { name: 'Forget all remembered decisions' });
    expect(all()).toBeDisabled();

    rerender(<Decisions {...props({ onForgetAll })} />);
    await userEvent.click(all());

    await waitFor(() => expect(onForgetAll).toHaveBeenCalledTimes(1));
    expect(screen.getByRole('status')).toHaveTextContent('forgot every decision');
  });

  it('offers no .forget_all() without its handler', () => {
    render(<Decisions {...props()} />);
    expect(
      screen.queryByRole('button', { name: 'Forget all remembered decisions' })
    ).not.toBeInTheDocument();
  });

  it('forgets a decision, announces it outside the list and moves the focus to the one in its place', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onForget = vi.fn(() => gate.promise);
    const { rerender } = render(<Decisions {...props({ onForget })} />);

    await user.click(forgetButton(LABEL.text));
    expect(onForget).toHaveBeenCalledWith('m2');
    // The page disables everything while the removal runs (`memoryBusy`): the own control keeps the focus.
    rerender(<Decisions {...props({ onForget, disabled: true })} />);
    const own = forgetButton(LABEL.text);
    expect(own).toHaveTextContent('.forget() …');
    expect(own).toHaveAttribute('aria-disabled', 'true');
    expect(own).not.toBeDisabled();
    expect(own).toHaveFocus();
    expect(forgetButton(LINE.text)).toBeDisabled();
    await user.click(own);
    expect(onForget).toHaveBeenCalledTimes(1);

    gate.resolve();
    rerender(<Decisions {...props({ onForget, memory: memoryOf(LINE, STARS) })} />);
    await waitFor(() => expect(forgetButton(STARS.text)).toHaveFocus());
    expect(screen.getByRole('status')).toHaveTextContent(`forgot: ${LABEL.text}`);
    expect(screen.getByTestId('plot-memory')).not.toContainElement(screen.getByRole('status'));
    expect(count()).toHaveTextContent('2 decisions');
  });

  it('gives the focus to the fallback once the last decision is gone, and still announces it', async () => {
    const user = userEvent.setup();
    const box = createRef<HTMLTextAreaElement>();
    const onForget = vi.fn(async () => undefined);
    const { rerender } = render(
      <>
        <textarea ref={box} aria-label="Message" />
        <Decisions {...props({ onForget, memory: memoryOf(STARS), fallbackFocusRef: box })} />
      </>
    );
    await user.click(forgetButton(STARS.text));
    rerender(
      <>
        <textarea ref={box} aria-label="Message" />
        <Decisions {...props({ onForget, memory: memoryOf(), fallbackFocusRef: box })} />
      </>
    );
    await waitFor(() => expect(screen.getByLabelText('Message')).toHaveFocus());
    expect(screen.queryByTestId('decisions-toggle')).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent(`forgot: ${STARS.text}`);
  });

  it('waits while anything else is in flight, its count still folding it', () => {
    render(<Decisions {...props({ disabled: true })} />);
    for (const text of [LINE.text, LABEL.text, STARS.text]) {
      expect(forgetButton(text)).toBeDisabled();
    }
    // Folding the list changes nothing on the server: it stays.
    expect(count()).toBeEnabled();
  });

  it('shows a failed removal under the list with its ref, and clears it once something else runs', async () => {
    const user = userEvent.setup();
    const onForget = vi
      .fn<(id: string) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(409, 'run_active', 'ref-busy'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-gone'))
      .mockRejectedValueOnce(new AgentApiError(500, 'internal', 'ref-500'));
    const { rerender } = render(<Decisions {...props({ onForget })} />);

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

    rerender(<Decisions {...props({ onForget, disabled: true })} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

/**
 * A browser drops the focus of an element whose node moves (it lands on the body), and React gives
 * it back after the commit to the element that had it. For one rerender, the DOM's insert drops
 * it as a browser does, so the test shows the focus comes back.
 */
function droppingFocusOnMove(run: () => void) {
  const insert = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function <T extends Node>(this: Node, node: T, child: Node | null) {
    const active = document.activeElement;
    if (active instanceof HTMLElement && node.contains(active)) active.blur();
    return insert.call(this, node, child) as T;
  };
  try {
    run();
  } finally {
    Node.prototype.insertBefore = insert;
  }
}

describe('Remembered: a newer chapter takes the decisions over', () => {
  /** Two chapter lines; the count and the list stand after the one `at` names, as one keyed row. */
  function Lines({ at, memory }: { at: 1 | 2; memory: PlotMemory }) {
    const handoffRef = useRef(false);
    const row = (index: 1 | 2): ReactNode[] => {
      const line = (
        <div key={`line-${index}`} data-testid={`line-${index}`}>
          {`# plot ${index}`}
          {at === index && (
            <RememberedCount
              memory={memory}
              open
              listId={LIST_ID}
              onToggle={() => undefined}
              handoffRef={handoffRef}
            />
          )}
        </div>
      );
      if (at !== index) return [line, <p key={`item-${index}`}>{`item ${index}`}</p>];
      return [
        line,
        <Remembered
          key="remembered"
          memory={memory}
          id={LIST_ID}
          open
          disabled={false}
          onForget={vi.fn(async () => undefined)}
          onAnnounce={() => undefined}
        />,
        <p key={`item-${index}`}>{`item ${index}`}</p>,
      ];
    };
    return <div>{[...row(1), ...row(2)]}</div>;
  }

  it('moves the list with its node and keeps a focus inside it', () => {
    const memory = memoryOf(LINE, LABEL);
    const { rerender } = render(<Lines at={1} memory={memory} />);
    const node = screen.getByTestId('plot-memory');
    forgetButton(LABEL.text).focus();
    droppingFocusOnMove(() => rerender(<Lines at={2} memory={memory} />));
    // The same element, now after the second line, with the focus where it was.
    expect(screen.getByTestId('plot-memory')).toBe(node);
    expect(screen.getByTestId('line-2').nextElementSibling).toBe(node);
    expect(forgetButton(LABEL.text)).toHaveFocus();
  });

  it('hands a focus on the count to the count on the newer line', () => {
    const memory = memoryOf(LINE);
    const { rerender } = render(<Lines at={1} memory={memory} />);
    count().focus();
    rerender(<Lines at={2} memory={memory} />);
    expect(within(screen.getByTestId('line-2')).getByTestId('decisions-toggle')).toHaveFocus();
    // No focus to hand on: a later move takes none.
    count().blur();
    rerender(<Lines at={1} memory={memory} />);
    expect(document.body).toHaveFocus();
  });
});
