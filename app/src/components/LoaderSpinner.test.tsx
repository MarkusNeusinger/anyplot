import { describe, expect, it } from 'vitest';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import { render, screen } from 'src/test-utils';
import { colors } from 'src/theme';

/** Every style emotion wrote into the document so far. */
const styles = () =>
  [...document.querySelectorAll('style')].map(style => style.textContent ?? '').join('\n');

describe('LoaderSpinner', () => {
  it('renders without crashing', () => {
    const { container } = render(<LoaderSpinner />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders with small size', () => {
    const { container } = render(<LoaderSpinner size="small" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders with large size by default', () => {
    render(<LoaderSpinner />);
    expect(screen.getByTestId('loader-spinner')).toHaveAttribute('data-size', 'large');
  });

  it('is decorative: hidden from screen readers in every size', () => {
    render(
      <>
        <LoaderSpinner size="large" />
        <LoaderSpinner size="inline" />
      </>
    );
    for (const loader of screen.getAllByTestId('loader-spinner')) {
      expect(loader).toHaveAttribute('aria-hidden', 'true');
    }
  });

  it('fits a line of text inline, in a fixed box', () => {
    render(
      <p>
        working <LoaderSpinner size="inline" />
      </p>
    );
    const loader = screen.getByTestId('loader-spinner');
    expect(loader.tagName).toBe('SPAN');
    expect(loader).toHaveStyle({ display: 'inline-block', width: '40px', height: '8px' });
  });

  it('gives each size keyframes of its own, so two sizes on one page never share one', () => {
    render(
      <>
        <LoaderSpinner size="large" />
        <LoaderSpinner size="small" />
        <LoaderSpinner size="inline" />
      </>
    );
    const css = styles();
    for (const size of ['large', 'small', 'inline']) {
      expect(css).toContain(`@keyframes trfLoader-${size}`);
      expect(css).toContain(`@keyframes ballMoveX-${size}`);
    }
    // Each loop moves by its own size's offsets: 32, 24 and 16 px.
    expect(css).toMatch(/@keyframes ballMoveX-large\{[^}]*\}[^}]*translateX\(32px\)/);
    expect(css).toMatch(/@keyframes ballMoveX-small\{[^}]*\}[^}]*translateX\(24px\)/);
    expect(css).toMatch(/@keyframes ballMoveX-inline\{[^}]*\}[^}]*translateX\(16px\)/);
    expect(css).not.toMatch(/@keyframes trfLoader\{/);
  });

  it('stands still under reduced motion, its runner green beside the gray pair', () => {
    render(<LoaderSpinner size="inline" />);
    const css = styles();
    expect(css).toMatch(
      /@media \(prefers-reduced-motion: reduce\)\{[^{]*::before,[^{]*::after\{[^}]*\banimation:none;\}/
    );
    const still = css.slice(css.indexOf('@media (prefers-reduced-motion: reduce)'));
    expect(still).toMatch(new RegExp(`::after\\{background:${colors.primary};\\}`, 'i'));
  });

  it('rests in the gray of muted text and runs in the brand green, without the ochre', () => {
    render(<LoaderSpinner size="inline" />);
    const css = styles();
    // The pair and the runner's base follow the theme through the token, never a fixed hex.
    expect(css).toMatch(/::before\{[^}]*background:var\(--ink-muted\);/);
    expect(css).toMatch(/::before\{[^}]*box-shadow:16px 0 var\(--ink-muted\);/);
    expect(css).toMatch(/::after\{[^}]*background:var\(--ink-muted\);/);
    // The runner: gray at the loop's ends, green while it travels and grows.
    const loop = css.slice(css.indexOf('@keyframes trfLoader-inline'));
    const frame = (at: string) => loop.match(new RegExp(`${at}\\{([^}]*)\\}`))?.[1] ?? '';
    expect(frame('0%,5%')).toContain('background:var(--ink-muted)');
    for (const at of ['10%', '40%', '90%,95%']) {
      expect(frame(at).toLowerCase()).toContain(`background:${colors.primary.toLowerCase()}`);
    }
    expect(frame('100%')).toContain('background:var(--ink-muted)');
    expect(css.toLowerCase()).not.toContain(colors.accent.toLowerCase());
  });
});
