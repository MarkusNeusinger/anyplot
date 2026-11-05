/**
 * A web table copied from the browser, read from the clipboard's HTML when its plain text
 * would lose the table's shape.
 *
 * A table with grouped columns (`Density` over `/km2` and `/mi2`, `Location` spanning both
 * header rows) copies as plain text with each spanning cell written once, so its second header
 * line is shorter than the rows and the parser cannot tell which name covers which columns. The
 * HTML beside that text keeps the spans: expanded, every cell stands in each row and column it
 * covers, both header lines get the table's width, and the parser joins them into one name per
 * column (`Density /km2`). Only the cells' text is kept. The HTML is parsed into a
 * `<template>`'s content, whose document has no browsing context: its scripts never run and
 * its images, frames and styles are never fetched, so a paste tells the copied page nothing.
 */

/** Clipboard HTML larger than this is left alone: the plain text goes as it is. */
const MAX_HTML_CHARS = 2_000_000;
/** The spans a cell may claim; larger values (and `0`, "to the end") count as one. */
const MAX_ROWSPAN = 200;
const MAX_COLSPAN = 50;
/** What the browser's own copy leaves out: hidden sort keys, scripts and styles. */
const HIDDEN =
  'script, style, template, [hidden], [style*="display:none" i], [style*="display: none" i], .sortkey';

/**
 * The single table of `html` as tab-separated text with its row and column spans expanded, or
 * null: no table, more than one, or none of its cells spans, so the plain text already says it.
 */
export function spannedTable(html: string): string | null {
  if (!html || html.length > MAX_HTML_CHARS || !/\b(?:rowspan|colspan)\s*=/i.test(html))
    return null;
  const inert = document.createElement('template');
  inert.innerHTML = html;
  const tables = inert.content.querySelectorAll('table');
  if (tables.length !== 1) return null;
  const table = tables[0];
  if (![...table.querySelectorAll('th, td')].some(cell => spans(cell as HTMLTableCellElement))) {
    return null;
  }
  const rows = [...table.rows];
  const grid: string[][] = rows.map(() => []);
  rows.forEach((row, r) => {
    let c = 0;
    for (const cell of [...row.cells]) {
      while (grid[r][c] !== undefined) c += 1;
      const text = cellText(cell);
      const down = span(cell.rowSpan, MAX_ROWSPAN);
      const across = span(cell.colSpan, MAX_COLSPAN);
      for (let dr = 0; dr < down && r + dr < rows.length; dr += 1) {
        for (let dc = 0; dc < across; dc += 1) grid[r + dr][c + dc] = text;
      }
      c += across;
    }
  });
  // A reduce, not a spread into `Math.max`: a copied table can hold more rows than a call takes arguments.
  const width = grid.reduce((widest, line) => Math.max(widest, line.length), 0);
  const lines = grid
    .map(line => Array.from({ length: width }, (_, index) => line[index] ?? ''))
    .filter(line => line.some(cell => cell !== ''));
  return lines.length ? `${lines.map(line => line.join('\t')).join('\n')}\n` : null;
}

function spans(cell: HTMLTableCellElement): boolean {
  return span(cell.rowSpan, MAX_ROWSPAN) > 1 || span(cell.colSpan, MAX_COLSPAN) > 1;
}

function span(value: number, limit: number): number {
  return Number.isInteger(value) && value > 1 ? Math.min(value, limit) : 1;
}

/** A cell's text as the browser's copy writes it: hidden parts left out, whitespace as single spaces. */
function cellText(cell: HTMLTableCellElement): string {
  const copy = cell.cloneNode(true) as HTMLElement;
  copy.querySelectorAll(HIDDEN).forEach(element => element.remove());
  return (copy.textContent ?? '').replace(/\s+/g, ' ').trim();
}
