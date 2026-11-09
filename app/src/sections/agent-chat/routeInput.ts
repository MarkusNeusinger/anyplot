/**
 * What pasted text is in the chat's one message box: a table or a file's text that waits as
 * an attachment (`data`), or text the user meant to type (`message`). A paste is routed before it
 * reaches the box, and the box's own text once more on Enter, so a table typed by hand, or pasted
 * where the browser reported no paste, goes to the dataset route too (`attachTyped`).
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
import wishWords from 'src/sections/agent-chat/wishWords.json';

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

// --- Rule 12: a web table copied one cell per line (`agents/anyplot/data/layouts.py`) --------

/** The fewest rows rules 12 and 13 read (`layouts.MIN_ROWS`). */
const LAYOUT_MIN_ROWS = 2;
/** The fewest blocks of a one-cell-per-line copy without a header line (`layouts.MIN_HEADERLESS_ROWS`). */
const MIN_HEADERLESS_ROWS = 3;
/** The most cells per row of a one-cell-per-line copy (`layouts.MAX_BLOCK`). */
const MAX_BLOCK = 12;
/** Two numbers joined by a hyphen or a dash, `60–97` (`layouts.RANGE`). */
const RANGE = /^[+\-−]?\d[\d.,']*\s*[-–—]\s*[+\-−]?\d[\d.,']*$/;
/** The parser's missing-value tokens (`layouts.MISSING_TOKENS`, `parse.MISSING_VALUES`). */
const MISSING_TOKENS = new Set([
  '-',
  'NA',
  'N/A',
  'n/a',
  'NaN',
  'nan',
  '-NaN',
  '-nan',
  'null',
  'NULL',
  'None',
  '<NA>',
  '#N/A',
  '#N/A N/A',
  '#NA',
  '1.#IND',
  '-1.#IND',
  '1.#QNAN',
  '-1.#QNAN',
]);

type CellKind = 'value' | 'range' | 'missing' | 'text';

function cellKind(cell: string): CellKind {
  const text = cell.trim();
  if (MISSING_TOKENS.has(text)) return 'missing';
  if (isValue(text)) return 'value';
  return RANGE.test(text) ? 'range' : 'text';
}

/** A cell fills a place of the pattern by its kind, or as a missing token where a value goes. */
function fits(kind: CellKind, expected: CellKind): boolean {
  if (kind === expected) return true;
  return kind !== 'text' && expected !== 'text' && (kind === 'missing' || expected === 'missing');
}

/** The rows of `size` cells from `start` that repeat one pattern, and the pattern (`layouts._run`). */
function cellRun(kinds: CellKind[], start: number, size: number): [number, string] | null {
  if (start >= kinds.length || kinds.slice(0, start).some(kind => kind !== 'text')) return null;
  const pattern = kinds.slice(start, start + size);
  if (pattern.length < size || pattern[0] !== 'text') return null;
  if (!pattern.some(kind => kind === 'value' || kind === 'range')) return null;
  let count = 0;
  for (;;) {
    const block = kinds.slice(start + count * size, start + (count + 1) * size);
    if (block.length !== size || !block.every((kind, index) => fits(kind, pattern[index]))) break;
    count += 1;
  }
  const rest = kinds.slice(start + count * size);
  const least = start ? LAYOUT_MIN_ROWS : MIN_HEADERLESS_ROWS;
  if (count < least || rest.length > size || rest.some(kind => kind !== 'text')) return null;
  return [count, pattern.join(' ')];
}

/** Whether one pattern is the other repeated: the same reading (`layouts._repeats`). */
function repeats(pattern: string, other: string): boolean {
  const [short, long] = [pattern.split(' '), other.split(' ')].sort((a, b) => a.length - b.length);
  if (long.length % short.length !== 0) return false;
  return Array.from({ length: long.length / short.length }, () => short)
    .flat()
    .every((kind, index) => kind === long[index]);
}

/**
 * Rule 12: a table a browser copied one cell per line, often with blank lines between them
 * (`layouts.cell_lines_table`): blocks of 2 to 12 cells repeat one pattern of kinds (a value, a
 * range such as `60–97`, a missing token in a value's place, text), each block starts with a text
 * cell and holds a value or a range, at least two blocks under a header line and three without
 * one; header lines above them and up to one block of text lines below them (the labels repeated
 * at the table's foot). Two patterns that explain the same cells are ambiguous.
 */
function isCellLinesTable(text: string): boolean {
  const cells = text
    .split(/\r\n|\r|\n/)
    .map(line => line.trim())
    .filter(Boolean);
  if (cells.length < 2 * LAYOUT_MIN_ROWS) return false;
  const kinds = cells.map(cellKind);
  const found: [number, number, string][] = [];
  for (let size = 2; size <= MAX_BLOCK; size += 1) {
    for (const start of new Set([0, 1, size - 1, size, size + 1])) {
      const run = cellRun(kinds, start, size);
      if (run) found.push([size, run[0], run[1]]);
    }
  }
  if (found.length === 0) return false;
  const most = Math.max(...found.map(([size, count]) => size * count));
  const best = found.filter(([size, count]) => size * count === most);
  const [, , pattern] = best.reduce((a, b) => (b[0] < a[0] ? b : a));
  return best.every(([, , other]) => repeats(pattern, other));
}

// --- Plot wishes, which neither rule 13 nor rule 14 reads as data -----------------------

/** Whole words of `words`, bounded by anything that is no letter (`5bis`, `y-Achse`). */
function wordPattern(words: string[], flags: string): RegExp {
  const alternation = words.map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  return new RegExp(`(?:^|[^\\p{L}])(?:${alternation})(?=$|[^\\p{L}])`, flags);
}

/** The words of a plot wish or a change request (`wishWords.json`, `layouts.WISH_WORDS`). */
const WISH_WORDS = wordPattern(wishWords.words, 'iu');
/** `max` and `min` as written: `Max` and `Min` with a capital are first names. */
const LOWERCASE_WISH_WORDS = wordPattern(wishWords.lowercase_only, 'u');

/**
 * Whether the text holds a word of a plot wish or an instruction: what the user meant to say,
 * however many numbers it holds (`y from 0 to 100`, `x bis 2030, y bis 60`).
 */
function isWish(text: string): boolean {
  return WISH_WORDS.test(text) || LOWERCASE_WISH_WORDS.test(text);
}

// --- Rule 13: a list of label/value pairs (`layouts.pair_list_table`) ---------------------

/** The most words of a `label value` pair's label (`layouts.MAX_LABEL_WORDS`). */
const MAX_LABEL_WORDS = 3;
const MAX_LABEL_CHARS = 40;
const COLON_PAIR = /^([^:=;,\t]{1,40}?)\s*:(\s*)(\S.*)$/;
const EQUALS_PAIR = /^([^:=;,\t]{1,40}?)\s*=\s*(\S.*)$/;
const SPACE_PAIR = /^([^:=;,\t]*\S)\s+(\S+)$/;

/** The fewest pairs of a list while the session holds data (`layouts.MIN_PAIRS_WITH_DATA`). */
const MIN_PAIRS_WITH_DATA = 3;
/** A label that is an axis letter alone: `x 2030` asks about the axis, it is no row. */
const AXIS_LABEL = /^[xyz]$/i;

function isNumber(cell: string): boolean {
  return /\d/.test(cell) && NUMBER.test(cell);
}

/** The form of one piece of a pair list, or null when it is no label with a number (`layouts._pair`). */
function pairForm(piece: string): 'colon' | 'equals' | 'space' | null {
  let match = COLON_PAIR.exec(piece);
  if (match) {
    const label = match[1].trim();
    // `16:9`, `at 10:30`: a ratio or a clock time, never a label and its value (`Q1:5` is one).
    const last = label.split(/\s+/).pop() ?? '';
    if (label && isNumber(last) && !match[2]) return null;
    return label && !AXIS_LABEL.test(label) && isNumber(match[3].trim()) ? 'colon' : null;
  }
  match = EQUALS_PAIR.exec(piece);
  if (match) {
    const label = match[1].trim();
    return label && !AXIS_LABEL.test(label) && isNumber(match[2].trim()) ? 'equals' : null;
  }
  match = SPACE_PAIR.exec(piece);
  if (!match) return null;
  const label = match[1].trim();
  if (!/\p{L}/u.test(label) || label.split(/\s+/).length > MAX_LABEL_WORDS) return null;
  if (label.length > MAX_LABEL_CHARS || AXIS_LABEL.test(label)) return null;
  return isNumber(match[2].trim()) ? 'space' : null;
}

/** A list's first line that names its two columns, `Monat Umsatz` (`layouts._pair_header`). */
function pairHeader(line: string): boolean {
  return line.split(/\s+/).length === 2 && !/[\d:=]/.test(line);
}

/**
 * Rule 13: label/value pairs inline or one per line (`a:7,b:12,c:5`, `a=7; b=12`, `Apples 7,
 * Pears 12`): split at `;` and line breaks first, then at `,` too, so a decimal comma survives
 * another separator; every piece a pair of one form with a number as its value, at least two.
 * A `label value` label holds a letter and at most three words, and a `label:value` label that
 * ends in a number needs a space after the colon, so `16:9` and `at 10:30` are never pairs,
 * while `Q1:5` and `2024: 7` are. A change request is never a list (`x bis 2030, y bis 60`,
 * `Titel 2026, Schrift 14`): no word of `wishWords.json`, no axis letter alone as a label. While
 * the session holds data, which a list would replace, it takes `MIN_PAIRS_WITH_DATA` pairs.
 */
function isPairList(text: string, minPairs: number): boolean {
  const stripped = text.trim();
  if (isWish(stripped)) return false;
  for (const split of [/[;\n]/, /[,;\n]/]) {
    let pieces = stripped
      .split(split)
      .map(piece => piece.trim())
      .filter(Boolean);
    if (stripped.includes('\n') && pieces.length > LAYOUT_MIN_ROWS && pairHeader(pieces[0])) {
      pieces = pieces.slice(1);
    }
    if (pieces.length < minPairs) continue;
    // Every piece a pair of one form; the first piece that is not ends the look.
    const form = pairForm(pieces[0]);
    if (form && pieces.every(piece => pairForm(piece) === form)) return true;
  }
  return false;
}

// --- Rule 14: short text that looks like data, for the server's transcriber ---------------

/** The fewest values of rule 14, and their least share of the words. */
const MIN_LOOSE_VALUES = 3;
const LOOSE_VALUE_SHARE = 0.5;
const URL = /\bhttps?:\/\/|\bwww\./i;

/**
 * Rule 14: text the chat takes (at most `MAX_MESSAGE_CHARS`) that no rule above reads but that is
 * mostly values: at least three, at least half its words, no question, no plot wish, no URL. The
 * server's code reads it when it can, else its transcriber offers a table for `.use()` or
 * `.discard()` (owner rule of 2026-11-09). Longer text goes only by a format rule.
 */
function looksLikeData(text: string): boolean {
  if (text.length > MAX_MESSAGE_CHARS || URL.test(text) || /\?\s*$/m.test(text)) return false;
  if (isWish(text)) return false;
  const words = text.split(/[\s,;]+/).filter(Boolean);
  const values = words.filter(isValue).length;
  return values >= MIN_LOOSE_VALUES && values >= LOOSE_VALUE_SHARE * words.length;
}

/**
 * The route of pasted text: `data` for a table or a file's text, `message` for text the user
 * meant as a message, `null` for nothing to route. The numbered rules follow the plan's routing
 * spec; `routeInput.cases.json` names the rule each case meets. Text longer than the chat takes
 * (rule 2) is data only by a format rule (3, 6 to 10, 12, 13), never by rule 14, so long prose
 * stays in the box over the cap and never reaches a model as data (owner rule of 2026-11-09).
 * `hasData`: the session holds data, which data from the box would replace; a short list of
 * pairs then takes three pairs, since two are as often a change request in words.
 */
export function routeInput(text: string, { hasData = false } = {}): InputRoute | null {
  // 1. Nothing but space.
  if (!text.trim()) return null;
  const rows = logicalRows(text);
  // 3. JSON: one value with records, or one object per line.
  if (isJson(text, rows)) return 'data';
  // 5. Code stays a message, which the chat runs; also over the cap, where the box says to shorten it.
  if (looksLikeCode(text)) return 'message';
  // 13. Label/value pairs, inline or one per line; never a plot wish.
  if (isPairList(text, hasData ? MIN_PAIRS_WITH_DATA : LAYOUT_MIN_ROWS)) return 'data';
  // 4. One line is a message (a formula, a request, a question), unless it is mostly values (14).
  if (rows.length >= 2) {
    const sample = rows.slice(0, SAMPLE_ROWS);
    // 6. Signals a typed message never has: tabs on two rows, a Markdown separator row.
    if (sample.filter(row => row.includes('\t')).length >= 2) return 'data';
    if (sample.some(row => MARKDOWN_SEPARATOR.test(row))) return 'data';
    // 7. to 10. A delimited, aligned, space-separated numeric or one-column table.
    if (isDelimited(sample) || isAligned(sample) || isSpaceNumeric(sample) || isColumn(sample)) {
      return 'data';
    }
    // 12. A web table copied one cell per line.
    if (isCellLinesTable(text)) return 'data';
  }
  // 14. Short text that is mostly values: the server reads it, or its transcriber offers a table.
  if (looksLikeData(text)) return 'data';
  // 11. Anything else is what the user meant to say.
  return 'message';
}
