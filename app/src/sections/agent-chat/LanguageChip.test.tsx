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
const dialog = () => screen.getByRole('dialog', { name: 'Plot language' });

describe('LanguageChip', () => {
  it('shows the value and how it was set, and is disabled while the page says so', () => {
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(<LanguageChip value={EN} disabled onSet={onSet} />);
    expect(chip()).toHaveTextContent(/^lang: en$/);
    expect(chip()).toBeDisabled();
    expect(chip()).toHaveAccessibleName('Plot language: en, default. Change');

    rerender(
      <LanguageChip value={{ language: 'de', source: 'detected' }} disabled={false} onSet={onSet} />
    );
    expect(chip()).toHaveTextContent(/^lang: de · detected$/);
    expect(chip()).toBeEnabled();
    expect(chip()).toHaveAttribute('aria-haspopup', 'dialog');

    rerender(
      <LanguageChip value={{ language: 'de', source: 'pasted' }} disabled={false} onSet={onSet} />
    );
    expect(chip()).toHaveTextContent(/^lang: de · from data$/);
    expect(chip()).toHaveAccessibleName('Plot language: de, from data. Change');

    rerender(
      <LanguageChip
        value={{ language: 'Klingon', source: 'chosen' }}
        disabled={false}
        onSet={onSet}
      />
    );
    expect(chip()).toHaveTextContent(/^lang: Klingon · chosen$/);
    expect(chip()).toHaveAttribute('title', "language of the plot's text and the replies: Klingon");
  });

  it('announces each change of the value once, and nothing on mount', () => {
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);
    expect(screen.getByRole('status')).toHaveTextContent('');
    rerender(
      <LanguageChip value={{ language: 'de', source: 'detected' }} disabled={false} onSet={onSet} />
    );
    expect(screen.getByRole('status')).toHaveTextContent('plot language: de');
  });

  it('opens the list with the current language pressed; Escape closes it and the focus returns', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    render(
      <LanguageChip value={{ language: 'de', source: 'detected' }} disabled={false} onSet={onSet} />
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

  it('asks nothing for the language already chosen, but makes a detected one final', async () => {
    const user = userEvent.setup();
    const onSet = vi.fn(async () => undefined);
    const { rerender } = render(
      <LanguageChip value={{ language: 'de', source: 'chosen' }} disabled={false} onSet={onSet} />
    );
    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /German/ }));
    expect(onSet).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());

    rerender(
      <LanguageChip value={{ language: 'de', source: 'detected' }} disabled={false} onSet={onSet} />
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
    expect(chip()).toHaveTextContent(/^lang: en …$/);
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
    expect(chip()).toHaveTextContent(/^lang: fr · chosen$/);
    expect(chip()).toHaveFocus();
    expect(onSet).toHaveBeenCalledTimes(1);
  });

  it('shows a failure under the chip with its ref, and clears it once something else runs', async () => {
    const user = userEvent.setup();
    const onSet = vi
      .fn<(language: string) => Promise<void>>()
      .mockRejectedValueOnce(new AgentApiError(422, 'invalid', 'ref-inv'))
      .mockRejectedValueOnce(new AgentApiError(409, 'run_active', 'ref-busy'))
      .mockRejectedValueOnce(new AgentApiError(404, 'session_expired', 'ref-gone'));
    const { rerender } = render(<LanguageChip value={EN} disabled={false} onSet={onSet} />);

    await user.click(chip());
    await user.type(
      within(dialog()).getByRole('textbox', { name: 'Other language' }),
      'Elvish{Enter}'
    );
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'the server refused this language name · ref ref-inv'
    );

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /Russian/ }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/still in progress.* · ref ref-busy$/)
    );

    await user.click(chip());
    await user.click(within(dialog()).getByRole('button', { name: /Dutch/ }));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('the session expired · ref ref-gone')
    );
    expect(screen.getByRole('button', { name: 'reload' })).toBeInTheDocument();

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
