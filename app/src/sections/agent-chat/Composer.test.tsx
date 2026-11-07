import { createRef } from 'react';

import { describe, expect, it, vi } from 'vitest';

import { Composer, type ComposerProps } from 'src/sections/agent-chat/Composer';
import { STATUS_LINE_ID } from 'src/sections/agent-chat/steps';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';
import { fireEvent, render, screen, userEvent } from 'src/test-utils';

/** The composer's props with data in step 1, its plot button active, unless a case says otherwise. */
function composerProps(overrides: Partial<ComposerProps> = {}): ComposerProps {
  return {
    draft: '',
    onDraftChange: vi.fn(),
    onPaste: vi.fn(),
    attachment: null,
    attachmentNotice: null,
    onRemoveAttachment: vi.fn(),
    dropHint: null,
    canOpen: true,
    fileInputRef: createRef<HTMLInputElement>(),
    onFileChosen: vi.fn(),
    onSubmit: vi.fn(),
    messageRef: createRef<HTMLTextAreaElement>(),
    plotRef: createRef<HTMLButtonElement>(),
    ready: true,
    busy: false,
    hasData: true,
    step2: false,
    hasPlot: false,
    chatLocked: false,
    plot: { kind: 'create', active: true, confirming: false, fresh: false },
    example: { filled: false, active: false },
    confirmError: null,
    pausedUntil: null,
    onExampleData: vi.fn(),
    onPlot: vi.fn(),
    ...overrides,
  };
}

const attachment: Attachment = {
  id: 1,
  via: 'paste',
  text: 'a,b\n1,2\n',
  name: null,
  lines: 2,
  bytes: 8,
  notes: [],
  converted: null,
  kind: 'csv',
  encoding: null,
  status: 'ready',
  error: null,
  readingLine: null,
};

const exampleButton = () => screen.getByRole('button', { name: 'Make example data' });
const openButton = () => screen.getByRole('button', { name: 'Attach a data file' });

describe('Composer row', () => {
  it('keeps the same four places in every state, and moves only the filled style', () => {
    // Before data: `.example_data()` is the step's action, the plot button stands quiet and inert.
    const props = composerProps({
      hasData: false,
      plot: { kind: 'create', active: false, confirming: false, fresh: false },
      example: { filled: true, active: true },
    });
    const { rerender } = render(<Composer {...props} />);
    const box = screen.getByRole('textbox', { name: 'Message' });
    const open = openButton();
    const example = exampleButton();
    const plot = screen.getByRole('button', { name: 'Create plot' });
    expect(example).not.toHaveAttribute('aria-disabled');
    expect(plot).toHaveAttribute('aria-disabled', 'true');
    expect(plot).toHaveTextContent('.create_plot() →');
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();

    // With data the plot button is the action, `.example_data()` quiet and inert, in the same
    // elements: nothing came or went.
    rerender(<Composer {...composerProps()} />);
    expect(screen.getByRole('textbox', { name: 'Message' })).toBe(box);
    expect(openButton()).toBe(open);
    expect(exampleButton()).toBe(example);
    expect(example).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByRole('button', { name: 'Create plot' })).toBe(plot);
    expect(plot).not.toHaveAttribute('aria-disabled');

    // Once the library has a plot the same button updates it.
    rerender(
      <Composer
        {...composerProps({
          step2: true,
          hasPlot: true,
          plot: { kind: 'update', active: false, confirming: false, fresh: false },
        })}
      />
    );
    expect(screen.getByRole('button', { name: 'Update plot' })).toBe(plot);
    expect(plot).toHaveTextContent('.update_plot() →');
    expect(plot).toHaveAttribute('aria-disabled', 'true');
  });

  it('names each kind of the plot button in words, and the status line as its description', () => {
    const { rerender } = render(
      <Composer
        {...composerProps({
          plot: { kind: 'new_data', active: true, confirming: false, fresh: false },
        })}
      />
    );
    const plot = screen.getByRole('button', { name: 'Plot the new data' });
    expect(plot).toHaveTextContent('plot the new data');
    expect(plot).toHaveAttribute('aria-describedby', STATUS_LINE_ID);

    rerender(
      <Composer
        {...composerProps({ plot: { kind: 'all', active: true, confirming: true, fresh: false } })}
      />
    );
    // The confirmation the click starts with is in flight: the button says it works on it.
    expect(screen.getByRole('button', { name: 'Plot in all libraries' })).toHaveTextContent(
      '.plot_all() …'
    );

    // A click that starts from the catalogue plot although the library has one says so too.
    rerender(
      <Composer
        {...composerProps({
          hasPlot: true,
          plot: { kind: 'update', active: true, confirming: false, fresh: true },
        })}
      />
    );
    const described = screen.getByRole('button', { name: 'Update plot' });
    const [line, help] = described.getAttribute('aria-describedby')!.split(' ');
    expect(line).toBe(STATUS_LINE_ID);
    expect(document.getElementById(help)).toHaveTextContent(
      'new from the catalogue plot; keeps your remembered decisions'
    );
  });

  it('never acts on an inert button, which keeps the keyboard focus', async () => {
    const user = userEvent.setup();
    const onPlot = vi.fn();
    const onExampleData = vi.fn();
    const props = composerProps({ onPlot, onExampleData });
    const { rerender } = render(<Composer {...props} />);
    const plot = screen.getByRole('button', { name: 'Create plot' });
    plot.focus();
    await user.keyboard('{Enter}');
    expect(onPlot).toHaveBeenCalledTimes(1);

    // The plot runs: the button turns inert in its place, and the focus stays on it, so a
    // second key press does nothing at all.
    rerender(
      <Composer
        {...props}
        busy
        plot={{ kind: 'create', active: false, confirming: false, fresh: false }}
      />
    );
    expect(plot).toHaveFocus();
    await user.keyboard('{Enter}');
    await user.click(exampleButton());
    expect(onPlot).toHaveBeenCalledTimes(1);
    expect(onExampleData).not.toHaveBeenCalled();
  });

  it('sends with Enter and, on a touch screen, with the ↵ inside the box, never with an empty box', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    const { rerender } = render(<Composer {...composerProps({ onSubmit })} />);
    // The `↵` shows only on a coarse pointer (a CSS media query): here it is in the DOM, hidden.
    const send = screen.getByTestId('send-return');
    expect(send).toHaveAttribute('aria-label', 'Send');
    expect(send).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(send);
    fireEvent.keyDown(screen.getByRole('textbox', { name: 'Message' }), { key: 'Enter' });
    expect(onSubmit).not.toHaveBeenCalled();

    rerender(<Composer {...composerProps({ onSubmit, draft: 'log scale on y' })} />);
    expect(send).not.toHaveAttribute('aria-disabled');
    fireEvent.click(send);
    expect(onSubmit).toHaveBeenCalledTimes(1);
    const box = screen.getByRole('textbox', { name: 'Message' });
    await user.click(box);
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    expect(onSubmit).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(onSubmit).toHaveBeenCalledTimes(2);
  });

  it('names the status line as the box’s description while all holds it, not with an attachment', () => {
    const { rerender } = render(
      <Composer
        {...composerProps({
          step2: true,
          chatLocked: true,
          plot: { kind: 'all', active: true, confirming: false, fresh: false },
        })}
      />
    );
    const box = screen.getByRole('textbox', { name: 'Message' });
    expect(box).toBeDisabled();
    expect(box).toHaveAttribute('aria-describedby', STATUS_LINE_ID);
    // The locked line moved into the status line: none stands above the box any more.
    expect(screen.queryByText(/libraries at once/)).not.toBeInTheDocument();

    // An attachment, new data, goes all the same: the box opens for Enter and a note (the `↵`
    // shows on a touch screen only, so on a desktop Enter in the box is the one way), and it names
    // nothing.
    const onSubmit = vi.fn();
    rerender(
      <Composer
        {...composerProps({
          step2: true,
          chatLocked: true,
          attachment,
          onSubmit,
          plot: { kind: 'all', active: false, confirming: false, fresh: false },
        })}
      />
    );
    expect(box).toBeEnabled();
    expect(box).toHaveAttribute('placeholder', 'add a note for this table, or press Enter');
    expect(box).not.toHaveAttribute('aria-describedby');
    fireEvent.keyDown(box, { key: 'Enter' });
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('send-return')).not.toHaveAttribute('aria-disabled');
  });
});
