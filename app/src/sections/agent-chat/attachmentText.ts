/** What the attachment chip (`AttachmentChip.tsx`) and the composer's live region say. */

import { countOf } from 'src/sections/agent-chat/countOf';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';

/** A size as the chip says it: bytes under 1 KB (`46 B`, never `0.0 KB`), then KB with one decimal below 10. */
export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(bytes < 10 * 1024 ? 1 : 0)} KB`;
}

/** What the chip names: the file with its sheet, or a pasted table. */
function title(attachment: Attachment): string {
  return attachment.source ?? attachment.name ?? 'table';
}

/** The chip's accessible name: "Attached table, 1,204 lines, 48 KB", or the file's name. */
export function attachmentLabel(attachment: Attachment): string {
  const what = attachment.name ? `file ${title(attachment)}` : 'table';
  if (attachment.status === 'reading') return `Attached ${what}, being read on the server`;
  return `Attached ${what}, ${countOf(attachment.lines, 'line')}, ${formatSize(attachment.bytes)}`;
}

/** What was attached, in one line: `▤ table · 1,204 lines · 48 KB`; the thread names a sent paste so. */
export function attachmentSummary(attachment: Attachment): string {
  return `▤ ${title(attachment)} · ${countOf(attachment.lines, 'line')} · ${formatSize(attachment.bytes)}`;
}

/** The chip's line as the screen shows it. */
export function attachmentLine(attachment: Attachment): string {
  if (attachment.status === 'reading') return attachment.readingLine ?? 'reading the file';
  if (attachment.status === 'sending') return 'parsing your data';
  return attachmentSummary(attachment);
}
