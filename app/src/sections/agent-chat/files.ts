/**
 * Getting a result out of the browser: download a blob as a file, copy a PNG
 * to the clipboard (with a download where the Clipboard API cannot take
 * images, such as Firefox without the async clipboard item, or a denied
 * permission).
 */

/** Save `blob` under `filename` through a temporary object URL. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  // Give the browser a moment to start the download before the URL goes.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Whether this browser can put an image on the clipboard. */
export function canCopyImage(): boolean {
  return (
    typeof navigator !== 'undefined' &&
    typeof navigator.clipboard?.write === 'function' &&
    typeof ClipboardItem !== 'undefined'
  );
}

/**
 * Copy a PNG to the clipboard; downloads it instead where that is not possible.
 * Resolves with what happened, so the caller can say so.
 */
export async function copyImage(blob: Blob, filename: string): Promise<'copied' | 'downloaded'> {
  if (canCopyImage()) {
    try {
      const png = blob.type === 'image/png' ? blob : new Blob([blob], { type: 'image/png' });
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': png })]);
      return 'copied';
    } catch {
      /* permission denied or unsupported type: fall back to the download */
    }
  }
  downloadBlob(blob, filename);
  return 'downloaded';
}
