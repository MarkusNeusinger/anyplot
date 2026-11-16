import type { ReactElement, ReactNode } from 'react';

import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { ThemeProvider } from '@mui/material/styles';

import { theme } from 'src/theme';

function AllProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <MemoryRouter>{children}</MemoryRouter>
    </ThemeProvider>
  );
}

function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: AllProviders, ...options });
}

/**
 * The declarations the page's style sheets give an element at a viewport width, in cascade order,
 * as written: `var(--ink-soft)` stays the token and `line-height: 1.6` the number, where
 * `getComputedStyle` substitutes the token (which the test document does not define) and resolves
 * the number to pixels. jsdom evaluates `@media` against its fixed 1024 px window, and the sx
 * breakpoints (`xs` too) all compile into one, so the helper applies their width conditions itself.
 * The screen has a fine pointer: a block on any other feature (`pointer: coarse`) never applies.
 * Rules for a state the element is not in (`:hover`, `::placeholder`) do not match it. A sheet
 * stores a shorthand as its longhands, so they are copied into a fresh declaration, which reads
 * the shorthand (`flex`) back from them. jsdom has no layout, so an `@container` block applies
 * only when the call names the width of the element's query container (`containerWidth`), by the
 * same width conditions; without it, none does. With `pseudoElement`, as with `getComputedStyle`,
 * it reads that pseudo-element's declarations instead: a rule applies when one of its selectors
 * ends with the pseudo-element and the element matches the rest, so a state on the element itself
 * (`:empty::before`) is checked against the element as it is.
 */
function styleAt(
  element: Element,
  width: number = window.innerWidth,
  containerWidth?: number,
  pseudoElement?: '::before' | '::after'
): CSSStyleDeclaration {
  const fits = (media: string, size: number = width) =>
    (media.match(/\([^)]*\)/g) ?? []).every(condition => {
      const bound = /^\((min|max)-width:\s*([\d.]+)px\)$/.exec(condition);
      if (!bound) return false;
      return bound[1] === 'min' ? size >= Number(bound[2]) : size <= Number(bound[2]);
    });
  const elementMatches = (selector: string) => {
    try {
      return element.matches(selector);
    } catch {
      return false;
    }
  };
  const matches = (selectorText: string) => {
    if (!pseudoElement) return elementMatches(selectorText);
    return selectorText
      .split(',')
      .map(selector => selector.trim())
      .filter(selector => selector.endsWith(pseudoElement))
      .some(selector => elementMatches(selector.slice(0, -pseudoElement.length) || '*'));
  };
  const declared = document.createElement('div').style;
  const apply = (rules: CSSRuleList) => {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSMediaRule) {
        if (fits(rule.media.mediaText)) apply(rule.cssRules);
      } else if (rule instanceof CSSContainerRule) {
        if (containerWidth !== undefined && fits(rule.conditionText, containerWidth))
          apply(rule.cssRules);
      } else if (rule instanceof CSSStyleRule && matches(rule.selectorText)) {
        for (const name of Array.from(rule.style)) {
          declared.setProperty(name, rule.style.getPropertyValue(name));
        }
      }
    }
  };
  for (const sheet of Array.from(document.styleSheets)) apply(sheet.cssRules);
  return declared;
}

export { customRender as render, styleAt };
export { screen, within, waitFor, act, fireEvent } from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
