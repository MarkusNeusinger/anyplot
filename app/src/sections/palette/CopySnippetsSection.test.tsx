import { useState } from 'react';

import { describe, expect, it } from 'vitest';

import { type Lang, PALETTE } from 'src/pages/PalettePage.helpers';
import { CopySnippetsSection } from 'src/sections/palette/CopySnippetsSection';
import { fireEvent, render, screen } from 'src/test-utils';

function StatefulCopySnippets() {
  const [lang, setLang] = useState<Lang>('python');
  const [oklch, setOklch] = useState(false);

  return (
    <CopySnippetsSection
      lang={lang}
      setLang={setLang}
      oklch={oklch}
      setOklch={setOklch}
      sortedPalette={PALETTE}
    />
  );
}

describe('CopySnippetsSection', () => {
  it('switches language tabs and updates the snippet text across Python, R, Julia, and JavaScript', () => {
    render(<StatefulCopySnippets />);

    expect(screen.getByRole('heading', { name: /copy & paste/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Python' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText(/from types import SimpleNamespace/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'R' }));
    expect(screen.getByRole('tab', { name: 'R' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText(/IMPRINT <- list\(/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Julia' }));
    expect(screen.getByRole('tab', { name: 'Julia' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText(/using Colors/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'JavaScript' }));
    expect(screen.getByRole('tab', { name: 'JavaScript' })).toHaveAttribute(
      'aria-selected',
      'true'
    );
    expect(screen.getByText(/const IMPRINT = \{/)).toBeInTheDocument();
  });

  it('toggles the OKLCH switch to annotate Python/R/Julia snippets and emit oklch() literals in JavaScript', () => {
    render(<StatefulCopySnippets />);

    const oklchSwitch = screen.getByRole('switch', { name: 'OKLCH' });
    expect(oklchSwitch).not.toBeChecked();
    expect(screen.queryByText(/# oklch\(0\.620 0\.130 165\.5\)/)).not.toBeInTheDocument();

    // Toggle OKLCH on in Python mode: adds trailing # oklch(...) comments
    fireEvent.click(oklchSwitch);
    expect(oklchSwitch).toBeChecked();
    expect(screen.getByText(/# oklch\(0\.620 0\.130 165\.5\)/)).toBeInTheDocument();

    // Switch to JavaScript while OKLCH is on: emits bare oklch(...) string values
    fireEvent.click(screen.getByRole('tab', { name: 'JavaScript' }));
    expect(screen.getByText(/"oklch\(0\.620 0\.130 165\.5\)"/)).toBeInTheDocument();
  });
});
