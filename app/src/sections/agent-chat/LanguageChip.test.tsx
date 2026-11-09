import { describe, expect, it, vi } from 'vitest';

import { AgentApiError, type PlotLanguage } from 'src/lib/agent';
import { LanguageChip } from 'src/sections/agent-chat/LanguageChip';
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

const EN: PlotLanguage = { language: 'en', source: 'default' };
const chip = () => screen.getByTestId('language-chip');
const dialog = () => screen.getByRole('dialog', { name: 'Language of the replies and the plot' });

describe('LanguageChip', () => {
  it('shows the language in its own words, how it was set in its name, and is disabled while the page says so', () => {
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(<LanguageChip value={EN} disabled onSet={onSet} />);
    // `English ▾` since the v4 frame: the source leaves the screen, the name keeps it, and the
    // name starts with the words on screen (WCAG 2.5.3), so "click English" finds the chip.
    expect(chip()).toHaveTextContent(/^English ▾$/);
    expect(chip()).toBeDisabled();
    expect(chip()).toHaveAccessibleName('Reply language: English, default. Change');

    rerender(
      <LanguageChip value={{ language: 'de', source: 'offer' }} disabled={false} onSet={onSet} />
    );
    expect(chip()).toHaveTextContent(/^Deutsch ▾$/);
    expect(chip()).toHaveAccessibleName('Reply language: Deutsch, chosen from the offer. Change');
    expect(chip()).toBeEnabled();
    expect(chip()).toHaveAttribute('aria-haspopup', 'dialog');

    rerender(
      <LanguageChip value={{ language: 'de', source: 'chosen' }} disabled={false} onSet={onSet} />
    );
    expect(chip()).toHaveTextContent(/^Deutsch ▾$/);
    expect(chip()).toHaveAccessibleName('Reply language: Deutsch, chosen. Change');
    expect(chip()).toHaveAttribute(
      'title',
      "language of the replies: Deutsch · a choice here also sets the next plot's text"
    );

    // Each word of an endonym starts in capitals, as the language writes its own name.
    rerender(
      <LanguageChip value={{ language: 'vi', source: 'chosen' }} disabled={false} onSet={onSet} />
    );
    expect(chip()).toHaveTextContent(/^Tiếng Việt ▾$/);
    expect(chip()).toHaveAccessibleName('Reply language: Tiếng Việt, chosen. Change');

    // A language outside the list shows as the server stored it.
    rerender(
      <LanguageChip
        value={{ language: 'Klingon', source: 'chosen' }}
        disabled={false}
        onSet={onSet}
      />
    );
    expect(chip()).toHaveTextContent(/^Klingon ▾$/);
    expect(chip()).toHaveAccessibleName('Reply language: Klingon, chosen. Change');
    // The chip names the replies' language; a choice here sets the plot's text too (owner, 2026-11-01).
    expect(chip()).toHaveAttribute(
      'title',
      "language of the replies: Klingon · a choice here also sets the next plot's text"
    );
  });

  it('announces each change of the value once, and nothing on mount', () => {
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);
    expect(screen.getByRole('status')).toHaveTextContent('');
    rerender(
      <LanguageChip value={{ language: 'de', source: 'offer' }} disabled={false} onSet={onSet} />
    );
    expect(screen.getByRole('status')).toHaveTextContent('reply language: Deutsch');
  });

  it('opens the list with the current language pressed; Escape closes it and the focus returns', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    render(
      <LanguageChip value={{ language: 'de', source: 'offer' }} disabled={false} onSet={onSet} />
    );

    await user.click(chip());
    expect(chip()).toHaveAttribute('aria-expanded', 'true');
    const group = within(dialog()).getByRole('group', { name: 'Common languages' });
    const buttons = within(group).getAllByRole('button');
    expect(buttons.map(button => button.getAttribute('aria-label'))).toEqual([
      'en english (English)',
      'zh 中文 (Chinese)',
      'de deutsch (German)',
      'vi tiếng việt (Vietnamese)',
      'es español (Spanish)',
      'fr français (French)',
      'nl nederlands (Dutch)',
      'pt português (Portuguese)',
      'ru русский (Russian)',
      'it italiano (Italian)',
    ]);
    // label in name: every accessible name starts with the button's visible text (code, endonym)
    const words = (text: string | null) => (text ?? '').replace(/\s+/g, '');
    for (const button of buttons) {
      expect(words(button.getAttribute('aria-label'))).toMatch(
        new RegExp(`^${words(button.textContent)}`)
      );
    }
    expect(within(group).getByRole('button', { name: /German/ })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    expect(within(group).getByRole('button', { name: /English/ })).toHaveAttribute(
      'aria-pressed',
      'false'
    );

    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    await waitFor(() => expect(chip()).toHaveFocus());
    expect(onSet).not.toHaveBeenCalled();
  });

  it('sends a picked code and closes the list', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /German/ }));
    expect(onSet).toHaveBeenCalledWith('de');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('asks nothing for the language already chosen, but makes an offered one final', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(
      <LanguageChip value={{ language: 'de', source: 'chosen' }} disabled={false} onSet={onSet} />
    );
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /German/ }));
    expect(onSet).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());

    // The same language taken from an offer: a pick here makes it final, so no offer comes after it.
    rerender(
      <LanguageChip value={{ language: 'de', source: 'offer' }} disabled={false} onSet={onSet} />
    );
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /German/ }));
    expect(onSet).toHaveBeenCalledWith('de');
  });

  it('sends any other language trimmed, and refuses one outside the pattern with a hint', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);

    await user.click(chip());
    const field = within(dialog()).getByRole('textbox', { name: 'Other language' });
    expect(within(dialog()).getByRole('button', { name: 'Set language' })).toBeDisabled();
    await user.type(field, 'a/b{Enter}');
    expect(onSet).not.toHaveBeenCalled();
    expect(within(dialog()).getByRole('alert')).toHaveTextContent(
      '# letters a–z, spaces and hyphens, up to 40'
    );
    expect(field).toHaveAttribute('aria-invalid', 'true');
    expect(field).toHaveAccessibleDescription('# letters a–z, spaces and hyphens, up to 40');
    // Typing again clears the hint; outer spaces go before the check and the send.
    await user.clear(field);
    expect(within(dialog()).queryByRole('alert')).not.toBeInTheDocument();
    await user.type(field, '  klingon ');
    await user.click(within(dialog()).getByRole('button', { name: 'Set language' }));
    expect(onSet).toHaveBeenCalledWith('klingon');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('stops the field at 40 characters, the server limit', async () => {
    const user = userEvent.setup();
    render(<LanguageChip value={EN} disabled={false} onSet={vi.fn(async () => undefined)} />);
    await user.click(chip());
    const field = within(dialog()).getByRole('textbox', { name: 'Other language' });
    expect(field).toHaveAttribute('maxLength', '40');
  });

  it('shows the call in progress, keeps the focus and opens nothing meanwhile', async () => {
    const user = userEvent.setup();
    const gate = deferred();
    const onSet = vi.fn(() => gate.promise);
    // The page disables the chip while its own call runs (`languageBusy`).
    const { rerender } = render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /French/ }));
    rerender(<LanguageChip value={EN} disabled onSet={onSet} />);

    await waitFor(() => expect(chip()).toHaveFocus());
    expect(chip()).toHaveTextContent(/^English … ▾$/);
    // `aria-disabled`, not `disabled`: a disabled button would drop the keyboard focus.
    expect(chip()).toHaveAttribute('aria-disabled', 'true');
    expect(chip()).not.toBeDisabled();
    await user.click(chip());
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    gate.resolve();
    rerender(
      <LanguageChip value={{ language: 'fr', source: 'chosen' }} disabled={false} onSet={onSet} />
    );
    await waitFor(() => expect(chip()).not.toHaveAttribute('aria-disabled'));
    expect(chip()).toHaveTextContent(/^Français ▾$/);
    expect(chip()).toHaveAccessibleName('Reply language: Français, chosen. Change');
    expect(chip()).toHaveFocus();
    expect(onSet).toHaveBeenCalledTimes(1);
  });

  it('shows a failure under the chip with its ref, and clears it once something else runs', async () => {
    const user = userEvent.setup();
    const onSet = vi
      .fn<(language: string) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(422, 'invalid', 'ref-inv'))
      .mockRejectedValueOnce(new AgentApiError(409, 'run_active', 'ref-busy'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-gone'))
      .mockRejectedValueOnce(new AgentApiError(500, 'internal', 'ref-500'));
    const { rerender } = render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);

    // A refusal (4xx) names its cause and shows no ref; a fault of the server does.
    await user.click(chip());
    await user.type(
      within(dialog()).getByRole('textbox', { name: 'Other language' }),
      'Elvish{Enter}'
    );
    expect(await screen.findByRole('alert')).toHaveTextContent(
      /^the server refused this language name$/
    );

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /Russian/ }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/still in progress[^·]*$/)
    );

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /Dutch/ }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/^the session expired · reload$/)
    );
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /French/ }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'something went wrong on the server · ref ref-500'
      )
    );

    rerender(<LanguageChip value={EN} disabled onSet={onSet} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('closes an open list when something else starts', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);
    await user.click(chip());
    expect(dialog()).toBeInTheDocument();

    rerender(<LanguageChip value={EN} disabled onSet={onSet} />);
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(chip()).toHaveAttribute('aria-expanded', 'false');
    expect(onSet).not.toHaveBeenCalled();
  });
});
