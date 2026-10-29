/**
 * The SPA shell (`index.html`) carries a default `<title>`, description, and Open Graph and
 * Twitter tags, marked `data-shell-default`, for clients without JavaScript. Pages render their
 * own, which React 19 hoists into `<head>`. A shell default is therefore shown only while no
 * page-rendered tag of the same kind exists: hidden while a page provides its own, back while
 * a route shows none (a lazy chunk loading, the error boundary, a spec page still loading).
 */

const SHELL_ATTR = 'data-shell-default';

/** The selector a page-rendered tag matches when it replaces this shell default. */
function replacementSelector(shellTag: Element): string {
  if (shellTag.tagName === 'TITLE') return 'title';
  const name = shellTag.getAttribute('name');
  if (name) return `meta[name="${name}"]`;
  return `meta[property="${shellTag.getAttribute('property')}"]`;
}

/**
 * Detach every shell default that a page-rendered tag replaces and re-attach every one that
 * nothing replaces any more. Idempotent: a second call changes nothing. Returns how many shell
 * defaults are detached afterwards.
 */
export function syncShellDefaults(head: HTMLHeadElement, defaults: Element[]): number {
  let detached = 0;
  for (const shellTag of defaults) {
    const replaced = Array.from(head.querySelectorAll(replacementSelector(shellTag))).some(
      tag => tag !== shellTag && !tag.hasAttribute(SHELL_ATTR)
    );
    if (replaced && shellTag.isConnected) shellTag.remove();
    if (!replaced && !shellTag.isConnected) head.appendChild(shellTag);
    if (!shellTag.isConnected) detached++;
  }
  return detached;
}

/**
 * Keep the shell defaults in sync with the page's own tags from now on. Call once before the
 * React root renders; returns a function that stops watching.
 */
export function watchShellDefaults(head: HTMLHeadElement = document.head): () => void {
  const defaults = Array.from(head.querySelectorAll(`[${SHELL_ATTR}]`));
  syncShellDefaults(head, defaults);
  // Our own detach or re-attach triggers the observer once more; the second sync is a no-op.
  const observer = new MutationObserver(() => syncShellDefaults(head, defaults));
  observer.observe(head, { childList: true });
  return () => observer.disconnect();
}
