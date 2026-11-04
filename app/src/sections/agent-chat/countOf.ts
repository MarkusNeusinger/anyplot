/**
 * The count formatter of the agent chat's data panel and attachment (`useChatAttachment.ts`,
 * `DataCard.tsx`, `dataCardParts.tsx`, `PinnedData.tsx`): `1 row`,
 * `1,234 columns`.
 */

export function countOf(count: number, noun: string): string {
  return `${count.toLocaleString('en-US')} ${noun}${count === 1 ? '' : 's'}`;
}
