/**
 * A reader of the canonical `data.csv` the agents service stores, for the data
 * panel's full view (`.view_all()`).
 *
 * The service writes it with Python's `csv.writer` in the default dialect
 * (`agents/anyplot/data/parse.py` `_write_csv`): commas between cells, a cell
 * that holds a comma, a quote, a line break or a carriage return in double
 * quotes with every quote inside doubled, and `\n` after every row. That is
 * RFC 4180, and this reader reads exactly that and nothing more: no delimiter
 * sniffing, no trimming, no reading of numbers or dates. Every cell comes back
 * as the exact text the file holds, an empty cell as an empty string, so the
 * view never shows a value the data does not hold (the data-fidelity rule).
 * `\r\n` ends a row too. A file that breaks the format (an unclosed quote, a
 * stray quote, a row of another width) is refused with a `CsvError` rather
 * than read some other way.
 */

const QUOTE = 0x22;
const COMMA = 0x2c;
const LF = 0x0a;
const CR = 0x0d;

export class CsvError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CsvError';
  }
}

/** Every row of `text`, each a list of its cells; a final line end adds no row. */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  const end = text.length;
  if (end === 0) return rows;
  let row: string[] = [];
  let at = 0;
  for (;;) {
    let cell: string;
    if (text.charCodeAt(at) === QUOTE) {
      // A quoted cell runs to the quote that is not doubled; `""` inside is one quote.
      cell = '';
      let from = at + 1;
      for (;;) {
        const close = text.indexOf('"', from);
        if (close < 0) throw new CsvError(`row ${rows.length + 1}: a quoted cell is never closed`);
        cell += text.slice(from, close);
        if (text.charCodeAt(close + 1) === QUOTE) {
          cell += '"';
          from = close + 2;
        } else {
          at = close + 1;
          break;
        }
      }
    } else {
      let stop = at;
      while (stop < end) {
        const code = text.charCodeAt(stop);
        if (code === COMMA || code === LF || code === CR) break;
        if (code === QUOTE)
          throw new CsvError(`row ${rows.length + 1}: a quote inside an unquoted cell`);
        stop += 1;
      }
      cell = text.slice(at, stop);
      at = stop;
    }
    row.push(cell);
    if (at >= end) {
      rows.push(row);
      break;
    }
    const code = text.charCodeAt(at);
    if (code === COMMA) {
      // The next cell, also an empty one at the very end of the text.
      at += 1;
      continue;
    }
    if (code === LF) at += 1;
    else if (code === CR && text.charCodeAt(at + 1) === LF) at += 2;
    else throw new CsvError(`row ${rows.length + 1}: text after a quoted cell`);
    rows.push(row);
    row = [];
    if (at >= end) break;
  }
  return rows;
}

/** The header and the rows of a canonical CSV, every row as wide as the header. */
export function readCsvTable(text: string): { header: string[]; rows: string[][] } {
  const [header, ...rows] = parseCsv(text);
  if (!header) throw new CsvError('the file is empty');
  rows.forEach((row, index) => {
    if (row.length !== header.length) {
      throw new CsvError(
        // Counted as `parseCsv` counts: the header is row 1 of the file.
        `row ${index + 2} has ${row.length} cells, the header ${header.length} columns`
      );
    }
  });
  return { header, rows };
}
