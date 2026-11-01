import { describe, expect, it } from 'vitest';

import { dataViewTheme, SITE_TOKENS } from 'src/sections/agent-chat/dataViewTheme';
import tokensCss from 'src/styles/tokens.css?raw';

/** The value `tokens.css` gives `name` in the block that starts with `selector {`. */
function tokenIn(selector: string, name: string): string | undefined {
  const start = tokensCss.indexOf(`${selector} {`);
  const block = tokensCss.slice(start, tokensCss.indexOf('\n}', start));
  return block.match(new RegExp(`${name}:\\s*([^;]+);`))?.[1].trim();
}

describe('dataViewTheme', () => {
  it.each([
    ['light', ':root'],
    ['dark', "[data-theme='dark']"],
  ] as const)('carries the site’s %s tokens as tokens.css defines them', (mode, selector) => {
    for (const [name, value] of Object.entries(SITE_TOKENS[mode])) {
      expect(tokenIn(selector, name), name).toBe(value);
    }
  });

  it('builds one theme per site theme, in its mode and on its surfaces', () => {
    const dark = dataViewTheme('dark');
    expect(dark).toBe(dataViewTheme('dark'));
    expect(dark.palette.mode).toBe('dark');
    expect(dark.palette.background.paper).toBe(SITE_TOKENS.dark['--bg-elevated']);
    expect(dark.palette.text.primary).toBe(SITE_TOKENS.dark['--ink']);
    expect(dataViewTheme('light').palette.background.paper).toBe(
      SITE_TOKENS.light['--bg-elevated']
    );
  });
});
