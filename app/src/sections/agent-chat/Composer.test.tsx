import { createRef } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

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
    example: { active: false },
    confirmError: null,
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

/**
 * The declarations the page's style sheets give an element at a viewport width, in cascade order:
 * jsdom's `getComputedStyle` skips every `@media` block, and the sx breakpoints (`xs` too) all
 * compile into one, so the test applies their width conditions itself. The screen has a fine
 * pointer: a block on any other feature (`pointer: coarse`) never applies. Rules for a state the
 * element is not in (`:hover`, `::placeholder`) do not match it.
 */
function styleAt(element: Element, width: number): Record<string, string> {
  const fits = (media: string) =>
    (media.match(/\([^)]*\)/g) ?? []).every(condition => {
      const bound = /^\((min|max)-width:\s*([\d.]+)px\)$/.exec(condition);
      if (!bound) return false;
      return bound[1] === 'min' ? width >= Number(bound[2]) : width <= Number(bound[2]);
    });
  const matches = (selector: string) => {
    try {
      return element.matches(selector);
    } catch {
      return false;
    }
  };
  const declared: Record<string, string> = {};
  const apply = (rules: CSSRuleList) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSMediaRule) {
        if (fits(rule.media.mediaText)) apply(rule.cssRules);
      } else if (rule instanceof CSSStyleRule && matches(rule.selectorText)) {
        for (const name of Array.from(rule.style)) {
          declared[name] = rule.style.getPropertyValue(name);
        }
      }
    }
  };
  for (const sheet of Array.from(document.styleSheets)) apply(sheet.cssRules);
  return declared;
}

const exampleButton = () => screen.getByRole('button', { name: 'Make example data' });
// The accessible names hold the visible words ("open", "example data") without the punctuation a
// screen reader would spell out (WCAG 2.5.3, style guide §7.4.1).
const openButton = () => screen.getByRole('button', { name: 'Open a data file' });

describe('Composer row', () => {
  it('holds the box and the plot button in the row, and the two ways to data in the line above', () => {
    // Before data: the line is highlighted and its links act, the plot button stands inert.
    const props = composerProps({
      hasData: false,
      plot: { kind: 'create', active: false, confirming: false, fresh: false },
      example: { active: true },
    });
    const { rerender } = render(<Composer {...props} />);
    const row = screen.getByTestId('composer-row');
    const line = screen.getByTestId('data-line');
    const box = screen.getByRole('textbox', { name: 'Message' });
    const example = exampleButton();
    const plot = screen.getByRole('button', { name: 'Create plot' });
    expect(line).toHaveTextContent(/^# no data at hand\?\.example_data\(\)·\.open\(\)a file$/);
    expect(line).toHaveAttribute('data-highlighted', 'true');
    expect(line).toContainElement(example);
    expect(line).toContainElement(openButton());
    expect(row).toContainElement(box);
    expect(row).toContainElement(plot);
    expect(row).not.toContainElement(example);
    expect(box).toHaveAttribute('placeholder', 'paste a table or drop a file');
    expect(example).not.toHaveAttribute('aria-disabled');
    expect(plot).toHaveAttribute('aria-disabled', 'true');
    expect(plot).toHaveTextContent('.create_plot() →');
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();

    // With data the line stays, muted, `.open()` first; `.example_data()` is the same element,
    // inert, so a focus on it survives the change. The plot button is the action.
    example.focus();
    rerender(<Composer {...composerProps()} />);
    expect(screen.getByTestId('data-line')).toBe(line);
    expect(line).not.toHaveAttribute('data-highlighted');
    expect(line).toHaveTextContent(/^# other data\?\.open\(\)·\.example_data\(\)$/);
    expect(screen.getByRole('textbox', { name: 'Message' })).toBe(box);
    expect(exampleButton()).toBe(example);
    expect(example).toHaveFocus();
    expect(example).toHaveAttribute('aria-disabled', 'true');
    expect(openButton()).not.toHaveAttribute('aria-disabled');
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

  it('makes the data line’s links real buttons that Tab reaches; .open() opens the file picker', async () => {
    const user = userEvent.setup();
    const onExampleData = vi.fn();
    const fileInputRef = createRef<HTMLInputElement>();
    render(
      <Composer
        {...composerProps({
          hasData: false,
          example: { active: true },
          onExampleData,
          fileInputRef,
        })}
      />
    );
    const pick = vi.spyOn(fileInputRef.current!, 'click');
    await user.tab();
    expect(exampleButton()).toHaveFocus();
    expect(exampleButton().tagName).toBe('BUTTON');
    await user.keyboard('{Enter}');
    expect(onExampleData).toHaveBeenCalledTimes(1);
    await user.tab();
    expect(openButton()).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(pick).toHaveBeenCalledTimes(1);
    // The file input stays out of the tab order: the box comes next.
    expect(screen.getByTestId('chat-file-input')).toHaveAttribute('tabindex', '-1');
    await user.tab();
    expect(screen.getByRole('textbox', { name: 'Message' })).toHaveFocus();
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

describe('Composer placeholder on a phone', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('reads short where a browser cuts it without an ellipsis, and long on a wider screen', () => {
    const placeholders = () => {
      const states: Partial<ComposerProps>[] = [
        { hasData: false },
        {},
        { step2: true },
        { hasPlot: true },
        { step2: true, hasPlot: true },
        { attachment },
      ];
      return states.map(state => {
        const { unmount } = render(<Composer {...composerProps(state)} />);
        const text = screen.getByRole('textbox', { name: 'Message' }).getAttribute('placeholder');
        unmount();
        return text;
      });
    };
    expect(placeholders()).toEqual([
      'paste a table or drop a file',
      'ask about your data, or say what the first plot should do',
      'optional: what the first plot should do differently',
      'ask about your data, or say what the next plot should do',
      'ask for a change, e.g. log scale on y',
      'add a note for this table, or press Enter',
    ]);
    // Below 600 px (owner, 2026-11-08): before the first plot, and once there is one.
    vi.stubGlobal(
      'matchMedia',
      vi.fn((query: string) => ({
        matches: query === '(max-width: 599.95px)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        onchange: null,
        dispatchEvent: vi.fn(),
      }))
    );
    expect(placeholders()).toEqual([
      'paste a table or drop a file',
      'ask or say what to plot',
      'ask or say what to plot',
      'ask for a change',
      'ask for a change',
      'add a note for this table, or press Enter',
    ]);
  });
});

// The row's phone form starts below the theme's `sm` (600 px), the page's phone width
// (`PHONE_QUERY` in styles.ts): 390 is the phone the owner checks, 599 and 600 the two sides of it.
describe('Composer row by width', () => {
  it('stacks the box and the plot button at the full width below sm, side by side from sm up', () => {
    render(<Composer {...composerProps()} />);
    // The box's own line holds the box and its `↵`.
    const field = screen.getByRole('textbox', { name: 'Message' }).parentElement!;
    const plot = screen.getByRole('button', { name: 'Create plot' });
    const prompt = screen.getByText('❯');

    for (const width of [390, 599]) {
      expect(styleAt(field, width).flex).toBe('1 1 100%');
      expect(styleAt(plot, width).flex).toBe('1 1 100%');
      expect(styleAt(prompt, width).display).toBe('none');
    }
    for (const width of [600, 1440]) {
      expect(styleAt(field, width).flex).toBe('1 1 240px');
      expect(styleAt(plot, width).flex).toBe('0 0 auto'); // `none`, as the parser spells it
      expect(styleAt(plot, width)['margin-left']).toBe('auto');
      expect(styleAt(prompt, width).display).toBe('block');
    }
    // One size at every width: alone on its line, the plot button needs no smaller text.
    expect(styleAt(plot, 390)['font-size']).toBe(styleAt(plot, 1440)['font-size']);
    // The `↵` stays a touch screen's (`pointer: coarse`): hidden on this fine pointer at any width.
    expect(styleAt(screen.getByTestId('send-return'), 390).display).toBe('none');
  });

  it('keeps the box before the plot button, which is inert before data and keeps the focus', async () => {
    const user = userEvent.setup();
    const onPlot = vi.fn();
    const { rerender } = render(
      <Composer
        {...composerProps({
          hasData: false,
          onPlot,
          plot: { kind: 'create', active: false, confirming: false, fresh: false },
          example: { active: true },
        })}
      />
    );
    const box = screen.getByRole('textbox', { name: 'Message' });
    const plot = screen.getByRole('button', { name: 'Create plot' });
    // Stacked on a phone in its ghost form too, after the box in the DOM and for Tab.
    expect(styleAt(plot, 390).flex).toBe('1 1 100%');
    expect(box.compareDocumentPosition(plot) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    await user.click(box);
    await user.tab();
    expect(plot).toHaveFocus();
    expect(plot).toHaveAttribute('aria-disabled', 'true');
    await user.keyboard('{Enter}');
    expect(onPlot).not.toHaveBeenCalled();

    // The data arrives: the same button fills and acts, and the focus stayed on it.
    rerender(<Composer {...composerProps({ onPlot })} />);
    expect(screen.getByRole('button', { name: 'Create plot' })).toBe(plot);
    expect(plot).toHaveFocus();
    expect(plot).not.toHaveAttribute('aria-disabled');
    expect(styleAt(plot, 390).flex).toBe('1 1 100%');
    await user.keyboard('{Enter}');
    expect(onPlot).toHaveBeenCalledTimes(1);
  });
});
