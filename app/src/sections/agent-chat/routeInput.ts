/**
 * What pasted text is in the chat's one message box: a table or a file's text that waits as
 * an attachment (`data`), or text the user meant to type (`message`). Typed text is always a
 * message; only a paste is routed, before it reaches the box.
 *
 * The rules read the text the way the dataset route's parser and classifier will: a table
 * the parser reads must become an attachment, and code, a formula or a request for data must
 * stay a message, which the chat runs, computes or answers. Every case in
 * `routeInput.cases.json` names both the route and the server's class for the same text
 * (`classify_paste` in `agents/anyplot/data/classify.py`), and a test on each side holds them
 * together (`routeInput.test.ts`, `tests/unit/agents/test_route_cases.py`).
 *
 * A table the rules miss (two rows of words, `name,city` over `Anna,Wien`, or a comma table of
 * words alone with a sentence in an unquoted cell) goes as a message, and the assistant asks
 * for it again with more rows or as a file: a miss costs one turn, never data. Prose stored as
 * a table would cost the user's message and a summary of nonsense.
 */

import { MAX_MESSAGE_CHARS } from 'src/lib/agent';

export type InputRoute = 'data' | 'message';

/** Logical rows read for the table signals: a table is decided long before. */
const SAMPLE_ROWS = 50;
/** The code veto's lines, as the server's `SCAN_LINES` and `MAX_LINE_SCAN`. */
const CODE_LINES = 200;
const CODE_LINE_CHARS = 400;
/** The share of code-shaped lines that makes text code (`MIN_CODE_SHARE`). */
const MIN_CODE_SHARE = 0.5;
/** The longest field of a table read from words alone (rule 7b). */
const MAX_WORD_FIELD = 40;
/** The words of a comma-split field that make it a clause of a sentence, not a cell (rule 7b at `,`). */
const CLAUSE_WORDS = 4;
/** A list item's marker: `- `, `* `, `• `, `1. `, `2) `. */
const LIST_MARKER = /^(?:[-*•]|\d+[.)])\s/;

// The code veto, copied from `classify.py` (`_STRONG`, `_ARROW`, `_SHAPED`): a line no table has.
// The shared `lines` cases keep the two copies in step.
const DATA_MODULES = String.raw`(?:np|numpy|pd|pandas|math|Math|random|scipy|stats|st|rng|torch|tf|sp|R)`;
const STRONG = new RegExp(
  [
    String.raw`^(?:`,
    String.raw`import\s+[A-Za-z_][\w.]*(?:\s+as\s+\w+)?(?:\s*,\s*[A-Za-z_][\w.]*)*;?$`,
    String.raw`|from\s+[A-Za-z_][\w.]*\s+import\s+\S`,
    String.raw`|(?:library|require|suppressPackageStartupMessages)\s*\(\s*['"]?\w+['"]?\s*\)`,
    String.raw`|def\s+[A-Za-z_]\w*\s*\(`,
    String.raw`|(?:async\s+)?function\s*\*?\s*[A-Za-z_$]?[\w$]*\s*\(`,
    String.raw`|(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=`,
    String.raw`|[A-Za-z_.][\w.]*(?:\[[^\]]*\])?\s*<-\s*\S`,
    String.raw`|for\s*\(|while\s*\(|for\s+[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s+in[ \t]+\S.*:$`,
    String.raw`|(?:print|console\.log|set\.seed|cat|plot|hist|lines)\s*\(`,
    String.raw`|${DATA_MODULES}\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*\(`,
    String.raw`|[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*=\s*(?:${DATA_MODULES}\.[A-Za-z_][\w.]*\s*\(|\[.+\bfor\b.+\bin\b.+\])`,
    String.raw`|[A-Za-z_]\w*\s*=\s*(?:rnorm|runif|rbinom|rpois|seq|rep|c|data\.frame|tibble|cumsum|sapply|lapply)\s*\(`,
    String.raw`)`,
  ].join('')
);
const ARROW = /\)[ \t]*=>|\b[A-Za-z_$][\w$]*[ \t]*=>/;
const SHAPED =
  /^(?:#|\/\/|\/\*|\*|[{}\])]+;?$|return\b|else\b|elif\b|if\s*\(|if[ \t]+\S.*:$|end$)|[;{:]$/;

/** A Markdown table's separator row: `|---|:---:|`. */
const MARKDOWN_SEPARATOR = /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/;
/** A number as a table cell writes it: a sign, thousands groups, a decimal mark, an exponent, `%`, a currency. */
const NUMBER =
  /^[+\-−]?[$€£]?\s?(?:\d{1,3}(?:[.,' ]\d{3})+|\d+)?(?:[.,]\d+)?(?:[eE][+-]?\d+)?\s?(?:%|[$€£])?$/;
/** A date or a time: ISO, day-month-year with `.`, `/` or `-`, a clock time. */
const DATE =
  /^(?:\d{4}-\d{1,2}(?:-\d{1,2})?(?:[T ]\d{1,2}:\d{2}(?::\d{2})?)?|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}:\d{2}(?::\d{2})?)$/;

/** Whether a line has the shape of a statement no table cell has (`classify.py` `_STRONG`, `_ARROW`). */
export function isStrongCodeLine(line: string): boolean {
  const text = line.trim().slice(0, CODE_LINE_CHARS);
  return STRONG.test(text) || ARROW.test(text);
}

/** Whether a line is shaped like code at all: strong, or a comment, a brace, `return`, a line ending in `;` `{` `:`. */
export function isCodeShapedLine(line: string): boolean {
  const text = line.trim().slice(0, CODE_LINE_CHARS);
  return isStrongCodeLine(text) || SHAPED.test(text);
}

/** `looks_like_code`: one strong line, and code-shaped lines at least half of the first lines. */
function looksLikeCode(text: string): boolean {
  const lines = text
    .split(/\r\n|\r|\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .slice(0, CODE_LINES);
  if (!lines.some(isStrongCodeLine)) return false;
  return lines.filter(isCodeShapedLine).length / lines.length >= MIN_CODE_SHARE;
}

/**
 * The text's rows: a newline inside an open double quote does not end one (Excel's multi-line
 * cells). A quote still open at the end was no cell's (`5" pipe` in a title): the lines are the rows.
 */
function logicalRows(text: string): string[] {
  const rows: string[] = [];
  let row = '';
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"') {
      // `""` inside a quoted cell is an escaped quote and keeps it open.
      if (quoted && text[index + 1] === '"') {
        row += '""';
        index += 1;
        continue;
      }
      quoted = !quoted;
    }
    if (!quoted && (char === '\n' || char === '\r')) {
      if (char === '\r' && text[index + 1] === '\n') index += 1;
      rows.push(row);
      row = '';
      continue;
    }
    row += char;
  }
  rows.push(row);
  const lines = quoted ? text.split(/\r\n|\r|\n/) : rows;
  return lines.filter(item => item.trim() !== '');
}

/** A row's fields at `delimiter`, outside double quotes, each trimmed and unquoted. */
function fieldsOf(row: string, delimiter: string): string[] {
  const fields: string[] = [];
  let field = '';
  let quoted = false;
  for (const char of row) {
    if (char === '"') quoted = !quoted;
    if (char === delimiter && !quoted) {
      fields.push(field);
      field = '';
      continue;
    }
    field += char;
  }
  fields.push(field);
  return fields.map(item => item.trim().replace(/^"(.*)"$/s, '$1'));
}

/** Whether a cell reads as a number or a date, as the parser would read it. */
function isValue(cell: string): boolean {
  const text = cell.trim();
  return text !== '' && /\d/.test(text) && (NUMBER.test(text) || DATE.test(text));
}

/** Rule 7a's and 8a's evidence: at least half the fields after the first row read as values. */
function valueEvidence(rows: string[][]): boolean {
  const body = rows
    .slice(1)
    .flat()
    .filter(cell => cell !== '');
  return body.length > 0 && body.filter(isValue).length / body.length >= 0.5;
}

/** Rule 7b's and 8b's evidence: three rows or more and no field long enough for prose. */
function wordEvidence(rows: string[][]): boolean {
  return rows.length >= 3 && rows.every(row => row.every(cell => cell.length <= MAX_WORD_FIELD));
}

/**
 * Commas that split sentences, not cells: a first row that ends on its comma (`Hello,`), a
 * clause of four words or more, or every row a list item (`- one, two`). A quoted field is a
 * CSV cell's mark, so a run with one is no prose for its long cells. Only the word evidence
 * yields to it; a run whose fields read as values stays a table.
 */
function readsAsProse(rows: string[][], raw: string[]): boolean {
  if (rows[0].some(cell => cell === '')) return true;
  if (raw.some(row => row.includes('"'))) return false;
  if (rows.some(row => row.some(cell => cell.split(/\s+/).length >= CLAUSE_WORDS))) return true;
  return rows.every(row => LIST_MARKER.test(row[0]));
}

/** The longest run of consecutive rows whose `count` is the same and at least `min`. */
function longestRun(counts: number[], min: number): { start: number; length: number } {
  let best = { start: 0, length: 0 };
  let start = 0;
  for (let index = 1; index <= counts.length; index += 1) {
    if (index < counts.length && counts[index] === counts[start]) continue;
    const length = index - start;
    if (counts[start] >= min && length > best.length) best = { start, length };
    start = index;
  }
  return best;
}

function isJson(text: string, rows: string[]): boolean {
  const trimmed = text.trim();
  if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
    try {
      const value: unknown = JSON.parse(trimmed);
      if (Array.isArray(value) ? value.length >= 2 : value !== null && typeof value === 'object') {
        return true;
      }
    } catch {
      // Not one JSON value: perhaps one object per line (JSON Lines).
    }
  }
  if (rows.length < 2) return false;
  return rows.every(row => {
    try {
      const value: unknown = JSON.parse(row);
      return value !== null && typeof value === 'object' && !Array.isArray(value);
    } catch {
      return false;
    }
  });
}

/** Rule 7: a delimiter whose longest equal-count run covers half the sample, with table evidence. */
function isDelimited(sample: string[]): boolean {
  return [';', '|', ','].some(delimiter => {
    const counts = sample.map(row => fieldsOf(row, delimiter).length - 1);
    const run = longestRun(counts, 1);
    if (run.length < 2 || run.length < sample.length * 0.5) return false;
    const raw = sample.slice(run.start, run.start + run.length);
    const rows = raw.map(row => fieldsOf(row, delimiter));
    if (valueEvidence(rows)) return true;
    return wordEvidence(rows) && !(delimiter === ',' && readsAsProse(rows, raw));
  });
}

/** Rule 8: columns aligned with two or more spaces, the same count on 80 % of the sample. */
function isAligned(sample: string[]): boolean {
  const split = sample.map(row => row.trim().split(/ {2,}/));
  const tally = new Map<number, number>();
  for (const fields of split) {
    if (fields.length >= 2) tally.set(fields.length, (tally.get(fields.length) ?? 0) + 1);
  }
  return [...tally.entries()].some(
    ([count, rows]) =>
      rows >= sample.length * 0.8 &&
      [valueEvidence, wordEvidence].some(evidence =>
        evidence(split.filter(fields => fields.length === count))
      )
  );
}

/** Rule 9: three rows or more split at single spaces into the same count, values after the first. */
function isSpaceNumeric(sample: string[]): boolean {
  const split = sample.map(row => row.trim().split(/\s+/));
  const run = longestRun(
    split.map(fields => fields.length),
    2
  );
  if (run.length < 3) return false;
  return split.slice(run.start + 1, run.start + run.length).every(fields => fields.every(isValue));
}

/** Rule 10: a header over three values or more, one per row. */
function isColumn(sample: string[]): boolean {
  const values = sample.slice(1);
  return values.length >= 3 && values.every(row => isValue(row));
}

/**
 * The route of pasted text: `data` for a table or a file's text, `message` for text the user
 * meant as a message, `null` for nothing to route. The numbered rules follow the plan's routing
 * spec; `routeInput.cases.json` names the rule each case meets.
 */
export function routeInput(text: string): InputRoute | null {
  // 1. Nothing but space.
  if (!text.trim()) return null;
  // 2. Longer than the chat takes: no message, whatever it holds. Code over it gets its own
  //    refusal from the dataset route, which asks to shorten it.
  if (text.length > MAX_MESSAGE_CHARS) return 'data';
  const rows = logicalRows(text);
  // 3. JSON: one value with records, or one object per line.
  if (isJson(text, rows)) return 'data';
  // 4. One line is a message: a formula, a request, a question.
  if (rows.length < 2) return 'message';
  // 5. Code stays a message, which the chat runs.
  if (looksLikeCode(text)) return 'message';
  const sample = rows.slice(0, SAMPLE_ROWS);
  // 6. Signals a typed message never has: tabs on two rows, a Markdown separator row.
  if (sample.filter(row => row.includes('\t')).length >= 2) return 'data';
  if (sample.some(row => MARKDOWN_SEPARATOR.test(row))) return 'data';
  // 7. to 10. A delimited, aligned, space-separated numeric or one-column table.
  if (isDelimited(sample) || isAligned(sample) || isSpaceNumeric(sample) || isColumn(sample)) {
    return 'data';
  }
  // 11. Anything else is what the user meant to say.
  return 'message';
}
