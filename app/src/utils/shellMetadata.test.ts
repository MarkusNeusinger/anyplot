import { afterEach, describe, expect, it } from 'vitest';

import { syncShellDefaults, watchShellDefaults } from 'src/utils/shellMetadata';

function shellTag(tag: 'title' | 'meta', attrs: Record<string, string>, text = ''): Element {
  const el = document.createElement(tag);
  el.setAttribute('data-shell-default', '');
  Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
  el.textContent = text;
  document.head.appendChild(el);
  return el;
}

function pageTag(tag: 'title' | 'meta', attrs: Record<string, string>, text = ''): Element {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
  el.textContent = text;
  document.head.appendChild(el);
  return el;
}

describe('syncShellDefaults', () => {
  afterEach(() => {
    document.head.innerHTML = '';
  });

  it('detaches a shell default only while a page tag of the same kind exists', () => {
    const title = shellTag('title', {}, 'shell title');
    const description = shellTag('meta', { name: 'description', content: 'shell' });
    const ogTitle = shellTag('meta', { property: 'og:title', content: 'shell' });
    const keywords = pageTag('meta', { name: 'keywords', content: 'kept' });
    const pageTitle = pageTag('title', {}, 'page title');
    pageTag('meta', { property: 'og:title', content: 'page' });

    expect(syncShellDefaults(document.head, [title, description, ogTitle])).toBe(2);

    expect(Array.from(document.head.querySelectorAll('title')).map(t => t.textContent)).toEqual([
      'page title',
    ]);
    expect(document.head.querySelectorAll('meta[property="og:title"]')).toHaveLength(1);
    // Nothing replaces the description, so the shell's stays.
    expect(description.isConnected).toBe(true);
    expect(keywords.isConnected).toBe(true);

    // The page's title goes away (an error state, a lazy chunk loading): the shell's comes back.
    pageTitle.remove();
    expect(syncShellDefaults(document.head, [title, description, ogTitle])).toBe(1);
    expect(document.title).toBe('shell title');
  });

  it('is idempotent', () => {
    const title = shellTag('title', {}, 'shell title');
    pageTag('title', {}, 'page title');
    syncShellDefaults(document.head, [title]);
    const before = document.head.innerHTML;
    expect(syncShellDefaults(document.head, [title])).toBe(1);
    expect(document.head.innerHTML).toBe(before);
  });
});

describe('watchShellDefaults', () => {
  afterEach(() => {
    document.head.innerHTML = '';
  });

  it('follows page tags as they come and go', async () => {
    const title = shellTag('title', {}, 'shell title');
    const stop = watchShellDefaults(document.head);
    expect(title.isConnected).toBe(true);

    const pageTitle = pageTag('title', {}, 'page title');
    await Promise.resolve();
    expect(title.isConnected).toBe(false);
    expect(document.title).toBe('page title');

    pageTitle.remove();
    await Promise.resolve();
    expect(title.isConnected).toBe(true);
    expect(document.title).toBe('shell title');
    stop();
  });
});
