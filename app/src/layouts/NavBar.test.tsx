import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, styleAt, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();
const navigate = vi.fn();
let currentPath = '/';

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigate,
    useLocation: () => ({ pathname: currentPath, search: '', hash: '', state: null, key: 'k' }),
  };
});

import { NavBar } from 'src/layouts/NavBar';

/**
 * The `::before` declarations of an element at a viewport width, read from the page's style
 * sheets the way `styleAt` reads the element's own (which never match a pseudo-element rule).
 */
function beforeStyleAt(element: Element, width: number): CSSStyleDeclaration {
  const fits = (media: string) =>
    (media.match(/\([^)]*\)/g) ?? []).every(condition => {
      const bound = /^\((min|max)-width:\s*([\d.]+)px\)$/.exec(condition);
      if (!bound) return false;
      return bound[1] === 'min' ? width >= Number(bound[2]) : width <= Number(bound[2]);
    });
  const declared = document.createElement('div').style;
  const apply = (rules: CSSRuleList) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSMediaRule) {
        if (fits(rule.media.mediaText)) apply(rule.cssRules);
      } else if (rule instanceof CSSStyleRule && rule.selectorText.endsWith('::before')) {
        if (!element.matches(rule.selectorText.slice(0, -'::before'.length))) continue;
        for (const name of Array.from(rule.style)) {
          declared.setProperty(name, rule.style.getPropertyValue(name));
        }
      }
    }
  };
  for (const sheet of Array.from(document.styleSheets)) apply(sheet.cssRules);
  return declared;
}

describe('NavBar', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    navigate.mockClear();
    currentPath = '/';
  });

  // /mcp is reached from the footer, the about page and the landing page instead.
  it('lists seven pages, about last', () => {
    const { container } = render(<NavBar />);

    const targets = Array.from(container.querySelectorAll('ul a')).map(a => a.getAttribute('href'));
    expect(targets).toEqual([
      '/specs',
      '/plots',
      '/map',
      '/libraries',
      '/stats',
      '/palette',
      '/about',
    ]);
  });

  // With MonoLisa the logo, the seven short labels and the search need 716px in one row. Below
  // that a single row wraps the logo onto two lines, and below about 624px it also pushes the
  // search past the screen's edge.
  it('keeps two rows below 720px and one from 720px', () => {
    const { container } = render(<NavBar />);

    const nav = container.querySelector('nav')!;
    for (const width of [320, 390, 600, 719]) {
      expect(styleAt(nav, width).gridTemplateAreas).toBe('"logo search" "nav nav"');
    }
    for (const width of [720, 900, 1440]) {
      expect(styleAt(nav, width).gridTemplateAreas).toBe('"logo nav search"');
    }
  });

  // jsdom lays nothing out, so this pins the declared geometry: below 360px the marker is a dot
  // that fits, with 2px to spare on each side, into the 8px a row at its tightest leaves between
  // two labels. With MonoLisa at 320px the gap is 9.6px and the dot keeps 3.6px from the label
  // before it; from 360px the gap is 16px or more, wide enough for the "•" glyph.
  it('keeps the active marker of a narrow phone clear of the label before it', () => {
    currentPath = '/about';
    const { container } = render(<NavBar />);

    const active = container.querySelector('a[href="/about"]')!;
    const row = container.querySelector('ul')!;
    const px = (value: string) => {
      expect(value).toMatch(/^-?[\d.]+px$/);
      return parseFloat(value);
    };

    const marker = beforeStyleAt(active, 320);
    expect(marker.content).toBe('""');
    expect(marker.borderRadius).toBe('50%');
    const left = px(marker.left);
    const width = px(marker.width);
    expect(px(marker.height)).toBe(width);
    expect(width).toBeGreaterThanOrEqual(4);

    // The label starts after the link's tap padding; the row's gap is the least space before it.
    const labelStart = px(styleAt(active, 320).paddingLeft);
    const leastGap = px(styleAt(row, 320).columnGap || styleAt(row, 320).gap);
    expect(labelStart - (left + width)).toBeGreaterThanOrEqual(2);
    expect(leastGap - (labelStart - left)).toBeGreaterThanOrEqual(2);
    expect(beforeStyleAt(active, 359).content).toBe('""');

    // From 360px the marker is the "•" glyph, as before.
    expect(beforeStyleAt(active, 360).content).toBe('"•"');
    expect(beforeStyleAt(active, 360).left).toBe('-4px');
    expect(beforeStyleAt(active, 1440).content).toBe('"•"');
    expect(beforeStyleAt(active, 1440).left).toBe('-12px');

    // Only the active link carries a marker.
    expect(beforeStyleAt(container.querySelector('a[href="/stats"]')!, 320).content).toBe('');
  });

  it('sends no event for the menu: the pageview that follows names the page', async () => {
    const user = userEvent.setup();
    const { container } = render(<NavBar />);

    // The labels render twice (full + short variant, CSS-hidden); we click the
    // anchor itself via href to avoid the duplicate-text ambiguity.
    await user.click(container.querySelector('a[href="/plots"]')!);
    await user.click(container.querySelector('a[href="/specs"]')!);
    await user.click(container.querySelector('a[href="/"]')!);

    expect(trackEvent).not.toHaveBeenCalled();
  });

  it('navigates on the search button, without an event', async () => {
    const user = userEvent.setup();
    render(<NavBar />);

    await user.click(screen.getByLabelText('Search plots'));
    expect(navigate).toHaveBeenCalledWith('/plots?focus=search');
    expect(trackEvent).not.toHaveBeenCalled();
  });

  it('navigates to debug on 5 clicks and stays there on 6', async () => {
    const user = userEvent.setup();
    const { container } = render(<NavBar />);

    // 5 clicks
    for (let i = 0; i < 5; i++) {
      await user.click(container.querySelector('a[href="/"]')!);
    }
    expect(navigate).toHaveBeenCalledWith('/debug');
    navigate.mockClear();

    // 1 more click (6 total) within the time window
    await user.click(container.querySelector('a[href="/"]')!);

    // should still navigate to debug, preventing default link to /
    expect(navigate).toHaveBeenCalledWith('/debug');
  });
});
