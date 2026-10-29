import { afterEach, describe, expect, it } from 'vitest';

import { removeShellDefaults } from 'src/utils/shellMetadata';

describe('removeShellDefaults', () => {
  afterEach(() => {
    document.head.innerHTML = '';
  });

  it('removes only tags with data-shell-default attribute and returns correct count', () => {
    // Add marked shell tags
    const title = document.createElement('title');
    title.setAttribute('data-shell-default', '');
    title.textContent = 'shell title';
    document.head.appendChild(title);

    const desc = document.createElement('meta');
    desc.setAttribute('data-shell-default', '');
    desc.name = 'description';
    document.head.appendChild(desc);

    // Add unmarked tags that should stay
    const otherTitle = document.createElement('title');
    otherTitle.textContent = 'page title';
    document.head.appendChild(otherTitle);

    const otherMeta = document.createElement('meta');
    otherMeta.name = 'keywords';
    document.head.appendChild(otherMeta);

    expect(document.head.children.length).toBe(4);

    const count = removeShellDefaults();

    expect(count).toBe(2);
    expect(document.head.children.length).toBe(2);

    // Verify only the unmarked ones are left
    const titles = document.head.querySelectorAll('title');
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toBe('page title');

    const metas = document.head.querySelectorAll('meta');
    expect(metas.length).toBe(1);
    expect(metas[0].name).toBe('keywords');
  });

  it('handles empty head', () => {
    expect(document.head.children.length).toBe(0);
    const count = removeShellDefaults();
    expect(count).toBe(0);
    expect(document.head.children.length).toBe(0);
  });
});
