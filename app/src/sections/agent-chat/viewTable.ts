/**
 * The data panel's full view (`.view_all()`, `DataView.tsx`) without the grid:
 * the table read from the current version's canonical CSV with the profile's
 * dtypes, the width each column opens with, and the number order of a numeric
 * column's text. The cells stay the file's text throughout; only the sort and
 * the `>` / `<` filters read a number from it, and never write one back.
 */

import type { ColumnDtype, ColumnProfile } from 'src/lib/agent';
import { readCsvTable } from 'src/sections/agent-chat/csv';

export interface ViewColumn {
  name: string;
  /** The profile's dtype; null for a column the profile does not name (the data changed meanwhile). */
  dtype: ColumnDtype | null;
  /** Sorted and compared by number: the profile reads it as `integer` or `number`. */
  numeric: boolean;
  /** The width it opens with, in pixels; the user resizes it. */
  width: number;
}

export interface ViewTable {
  columns: ViewColumn[];
  rows: string[][];
}

/** The grid's monospace text at 13 px: one character's advance, in pixels, a little generous. */
const CHAR_PX = 8;
/** A header's name or dtype line beside the sort arrow and the menu button. */
const HEADER_EXTRA_PX = 64;
/** A cell's text and its padding. */
const CELL_EXTRA_PX = 24;
export const MIN_COLUMN_PX = 72;
export const MAX_COLUMN_PX = 320;
/** The rows a column's width is measured on: enough to see its long values, cheap on 20,000 rows. */
const MEASURED_ROWS = 1000;

/** The table of `csv`, every column with its dtype by name from `profile` and an opening width. */
export function viewTable(csv: string, profile: ColumnProfile[]): ViewTable {
  const { header, rows } = readCsvTable(csv);
  const dtypes = new Map(profile.map(column => [column.name, column.dtype]));
  const columns = header.map((name, index) => {
    const dtype = dtypes.get(name) ?? null;
    return {
      name,
      dtype,
      numeric: dtype === 'integer' || dtype === 'number',
      width: columnWidth(name, dtype, rows, index),
    };
  });
  return { columns, rows };
}

/** Wide enough for the name, the dtype and the longest of the first values, within the bounds. */
export function columnWidth(
  name: string,
  dtype: string | null,
  rows: string[][],
  index: number
): number {
  let longest = 0;
  const measured = Math.min(rows.length, MEASURED_ROWS);
  for (let row = 0; row < measured; row += 1) {
    longest = Math.max(longest, rows[row][index].length);
  }
  const header = Math.max(name.length, dtype?.length ?? 0) * CHAR_PX + HEADER_EXTRA_PX;
  const cells = longest * CHAR_PX + CELL_EXTRA_PX;
  return Math.min(MAX_COLUMN_PX, Math.max(MIN_COLUMN_PX, header, cells));
}

/** The width of the row number column: its largest number and the cell's padding. */
export function rowNumberWidth(rows: number): number {
  return Math.max(48, String(rows).length * CHAR_PX + CELL_EXTRA_PX);
}

const INFINITY = /^([+-]?)inf(inity)?$/i;

/** The number a cell's text reads as, or null for an empty cell or a text that is no number. */
export function numberOf(cell: string): number | null {
  if (cell.trim() === '') return null;
  const infinity = cell.trim().match(INFINITY);
  if (infinity) return infinity[1] === '-' ? -Infinity : Infinity;
  const value = Number(cell);
  return Number.isNaN(value) ? null : value;
}

function compareText(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** A sort's way up, as the grid names it; anything but `desc` reads ascending. */
export type SortDirection = 'asc' | 'desc' | null | undefined;

/**
 * A numeric column's order: by number, then by text for equal numbers (`1.0`
 * and `1`). The empty cells and any text that is no number stay after every
 * number either way up: negated as a whole, a descending sort would open on a
 * page of gaps.
 */
export function compareNumericText(a: string, b: string, direction?: SortDirection): number {
  const x = numberOf(a);
  const y = numberOf(b);
  if (x !== null && y !== null) {
    const order = x - y || compareText(a, b);
    return direction === 'desc' ? -order : order;
  }
  if (x !== null) return -1;
  if (y !== null) return 1;
  return compareText(a, b);
}

/** The order of a text column's values: the grid's own default. */
const collator = new Intl.Collator();

/** A text column's order; the empty cells stay after every value either way up. */
export function compareTextCells(a: string, b: string, direction?: SortDirection): number {
  if (a === '' || b === '') return Number(a === '') - Number(b === '');
  const order = collator.compare(a, b);
  return direction === 'desc' ? -order : order;
}
