import { createRef } from 'react';

import { describe, expect, it, vi } from 'vitest';

import { Composer, type ComposerProps } from 'src/sections/agent-chat/Composer';
import { ATTACHMENT_LINE } from 'src/sections/agent-chat/messages';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';
import { render, screen } from 'src/test-utils';

const RUN_LINE = '# plotting… .stop() to cancel';

/** A composer in a running plot turn: step 1's line stands above the box unless a case says otherwise. */
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
    dataRows: null,
    step2: false,
    hasPlot: false,
    ctaPlot: true,
    canCreate: false,
    plotAll: false,
    chatLocked: false,
    libraryCount: 2,
    fanOutOpen: false,
    carryText: null,
    stepLine: '# step 1 — check the preview and the bindings above, then .create_plot()',
    runLine: RUN_LINE,
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

describe('Composer while a plot runs', () => {
  it("names .stop() in the step line's place, and in step 2's line's place before the first plot", () => {
    const { unmount } = renderComposer();
    expect(screen.getByTestId('data-step')).toHaveTextContent(RUN_LINE);
    expect(screen.queryByText(/check the preview/)).not.toBeInTheDocument();
    unmount();

    renderComposer({ stepLine: null, step2: true });
    expect(screen.getByTestId('data-step')).toHaveTextContent(RUN_LINE);
    expect(screen.queryByText(/create the plot as it is/)).not.toBeInTheDocument();
  });

  it('adds no line where none stood, so the box does not move', () => {
    renderComposer({ stepLine: null, step2: true, hasPlot: true, ctaPlot: false });
    expect(screen.queryByTestId('data-step')).not.toBeInTheDocument();
    expect(screen.queryByText(RUN_LINE)).not.toBeInTheDocument();
  });

  it('keeps the line of an attachment that waits, and the line of all that the box names', () => {
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
    const { unmount } = renderComposer({ attachment });
    expect(screen.getByTestId('data-step')).toHaveTextContent(ATTACHMENT_LINE);
    unmount();

    renderComposer({ stepLine: null, step2: true, plotAll: true, chatLocked: true });
    expect(screen.queryByText(RUN_LINE)).not.toBeInTheDocument();
    const lock = screen.getByText(/plot the table as it is in all 2 libraries at once/);
    // The box names the line as its description: it must stand.
    expect(screen.getByLabelText('Message')).toHaveAttribute('aria-describedby', lock.id);
  });
});
