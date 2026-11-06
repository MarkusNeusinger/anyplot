import { createRef } from 'react';

import { describe, expect, it, vi } from 'vitest';

import { Composer, type ComposerProps } from 'src/sections/agent-chat/Composer';
import { STATUS_LINE_ID } from 'src/sections/agent-chat/steps';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';
import { render, screen } from 'src/test-utils';

/** A composer in a running plot turn, in step 1 unless a case says otherwise. */
function renderComposer(overrides: Partial<ComposerProps> = {}) {
  const props: ComposerProps = {
    draft: '',
    onDraftChange: vi.fn(),
    onPaste: vi.fn(),
    attachment: null,
    attachmentNotice: null,
    onRemoveAttachment: vi.fn(),
    dropHint: null,
    canOpen: false,
    fileInputRef: createRef<HTMLInputElement>(),
    onFileChosen: vi.fn(),
    onSubmit: vi.fn(),
    messageRef: createRef<HTMLTextAreaElement>(),
    createRef: createRef<HTMLButtonElement>(),
    ready: true,
    busy: true,
    running: true,
    stopping: false,
    hasData: true,
    step2: false,
    hasPlot: false,
    ctaPlot: true,
    canCreate: false,
    plotAll: false,
    chatLocked: false,
    libraryCount: 2,
    fanOutOpen: false,
    carryText: null,
    newData: false,
    confirming: false,
    confirmError: null,
    pausedUntil: null,
    exampleOffer: false,
    exampleWorking: false,
    onExampleData: vi.fn(),
    onStop: vi.fn(),
    onPlot: vi.fn(),
    onCreate: vi.fn(),
    onCarry: vi.fn(),
    onPlotAll: vi.fn(),
    keepKeyboardFocus: vi.fn(),
    ...overrides,
  };
  return render(<Composer {...props} />);
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

describe('Composer and the status line', () => {
  it("leaves the step's line to the status line at the frame's foot, which the plot button names", () => {
    const { unmount } = renderComposer();
    // The step lines stood above the box until the v4 frame: none stands there now.
    expect(screen.queryByTestId('data-step')).not.toBeInTheDocument();
    expect(screen.queryByText(/plotting…|check the preview/)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create plot' })).toHaveAttribute(
      'aria-describedby',
      STATUS_LINE_ID
    );
    unmount();

    // Once the confirmed data has a plot here, `.start_over()` names it after its own help.
    const { unmount: unmountPlotted } = renderComposer({
      running: false,
      step2: true,
      hasPlot: true,
      ctaPlot: false,
    });
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver.getAttribute('aria-describedby')?.split(' ')).toContain(STATUS_LINE_ID);
    unmountPlotted();

    // Beside a switch's offer the status line describes the offer: `.start_over()` keeps its help.
    renderComposer({
      running: false,
      step2: true,
      carryText: 'plot in seaborn with your 2 decisions',
    });
    expect(screen.getByTestId('carry-plot').getAttribute('aria-describedby')).toBe(STATUS_LINE_ID);
    expect(
      screen.getByRole('button', { name: 'Start over' }).getAttribute('aria-describedby')
    ).not.toContain(STATUS_LINE_ID);
  });

  it('lets .send() name the status line while an attachment waits, which says it goes with Enter', () => {
    renderComposer({ running: false, busy: false, attachment });
    expect(screen.getByRole('button', { name: '.send()' })).toHaveAttribute(
      'aria-describedby',
      STATUS_LINE_ID
    );
  });

  it('keeps the line of all above the box, which the box and the plot button name', () => {
    renderComposer({ step2: true, plotAll: true, chatLocked: true });
    const lock = screen.getByText(/plot the table as it is in all 2 libraries at once/);
    // The box names the line as its description: it must stand.
    expect(screen.getByLabelText('Message')).toHaveAttribute('aria-describedby', lock.id);
    expect(
      screen.getByRole('button', { name: 'Plot in all libraries' }).getAttribute('aria-describedby')
    ).toBe(`${STATUS_LINE_ID} ${lock.id}`);
  });

  it('drops the line of all while an attachment waits: new data goes, and the box names nothing', () => {
    renderComposer({ step2: true, plotAll: true, chatLocked: true, attachment });
    expect(screen.queryByText(/libraries at once/)).not.toBeInTheDocument();
    expect(screen.getByLabelText('Message')).not.toHaveAttribute('aria-describedby');
  });
});
