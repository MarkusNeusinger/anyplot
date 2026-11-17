import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { styleAt } from 'src/test-utils';

// The helper reads the document's style sheets; these rules stand in for the ones emotion writes.
const SHEET = `
  .probe { color: red; }
  .probe:empty::before, .listed::before { content: "\\00a0"; }
  @container (min-width: 560px) { .probe::after { content: "wide"; } }
`;

describe('styleAt with a pseudo-element', () => {
  let style: HTMLStyleElement;
  let empty: HTMLElement;
  let filled: HTMLElement;

  beforeEach(() => {
    style = document.createElement('style');
    style.textContent = SHEET;
    document.head.appendChild(style);
    empty = document.createElement('div');
    empty.className = 'probe';
    filled = document.createElement('div');
    filled.className = 'probe';
    filled.textContent = 'github.open()';
    document.body.append(empty, filled);
  });

  afterEach(() => {
    style.remove();
    empty.remove();
    filled.remove();
  });

  it("reads only the pseudo-element's rules, and the element's own only without one", () => {
    expect(styleAt(empty).color).toBe('red');
    expect(styleAt(empty).content).toBe('');
    expect(styleAt(empty, 1024, undefined, '::before').content).not.toBe('');
    expect(styleAt(empty, 1024, undefined, '::before').color).toBe('');
  });

  it('checks a state in the selector against the element as it is', () => {
    expect(styleAt(filled, 1024, undefined, '::before').content).toBe('');
  });

  it('matches each selector of a list on its own', () => {
    const listed = document.createElement('span');
    listed.className = 'listed';
    document.body.append(listed);
    expect(styleAt(listed, 1024, undefined, '::before').content).not.toBe('');
    expect(styleAt(listed, 1024, undefined, '::after').content).toBe('');
    listed.remove();
  });

  it("applies a container block to the pseudo-element by the container's width", () => {
    expect(styleAt(filled, 1440, undefined, '::after').content).toBe('');
    expect(styleAt(filled, 1440, 400, '::after').content).toBe('');
    expect(styleAt(filled, 1440, 600, '::after').content).toBe('"wide"');
  });

  it('reads a pseudo-element without a selector before it as one of every element', () => {
    const universal = document.createElement('style');
    universal.textContent = '::after { content: "any"; }';
    document.head.appendChild(universal);
    expect(styleAt(filled, 1024, undefined, '::after').content).toBe('"any"');
    universal.remove();
  });
});
