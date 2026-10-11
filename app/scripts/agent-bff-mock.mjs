#!/usr/bin/env node
/**
 * A local mock of the agent chat BFF (`/debug/agent/*`) plus the few catalogue
 * routes the plot page needs, for driving the "Use with my data" UI in a
 * browser without the real API, the agents service, a model or a database.
 *
 *   node app/scripts/agent-bff-mock.mjs            # http://localhost:8010, loopback only
 *   cd app && VITE_ENABLE_AGENT_CHAT=true \
 *     VITE_API_URL=http://localhost:8010 VITE_DEBUG_API_URL=http://localhost:8010 yarn dev
 *   open http://localhost:3000/scatter-basic/python/matplotlib   (the .adapt() button)
 *   open http://localhost:3000/debug/agent?spec=scatter-basic&library=matplotlib&language=python
 *   open http://localhost:3000/debug/agent?spec=line-multi&library=matplotlib&language=python
 *
 * It follows the documented contract (docs/reference/api.md, "Agent chat"):
 * the CSRF header on every POST, PUT and DELETE, `{detail, ref}` errors with
 * an `X-Request-Id`, the spec's `roles` in the dataset answer, the binding
 * check's `errors` lines on a refused binding set, and a scripted `anyplot/1`
 * stream with `ready`, two `queued` statuses, the pipeline steps, `plot` (with
 * the stored `version`), `message` and `done`, with `: ping` comments in
 * between. Two specs exist: scatter-basic (`x`, `y`) and line-multi (`x`, the
 * series family `y1, y2, ...`, an optional `series`). Plots are drawn here as
 * PNGs from the pasted data (a scatter of the bound x and y columns, in the
 * theme's colours), in the spirit of the fake render backend's fixture PNG
 * (agents/anyplot/render/backends/fake.py); no code runs. Like the agents
 * service, the mock appends the footer strip below every plot it serves
 * (1600x900 becomes 1600x932); catalogue previews stay without it. Pasted text
 * that is no table ("Hund 7 Katze 3 und Vogel 4") comes back as the service's
 * transcribed answer (`transcribed: true`, the table's CSV in `text`, nothing
 * stored), so the confirmation card can be driven without a model. Step 1 ends
 * with `POST .../dataset/confirm`, which marks the stored dataset and its
 * bindings as checked (`422 no_dataset` without one); a stored parse or an
 * applied binding change clears the mark, and until it holds every pipeline
 * run answers `plot{status: not_ready, reason: data_unconfirmed}`. Every
 * `done` carries the session's `bindings` and `data_confirmed`, as the service
 * syncs them after a run, and `dataset` after a turn that changed the data.
 * `GET .../bundle?include_data=&version=` (the page's `.save()`) answers the
 * session's feedback case from the mock's state, with the agents service's
 * top-level keys (the transcript of the turns, every version's code, result and
 * PNGs as base64, the profile, the bindings, a config stamp; each version's
 * `data.csv` only with `include_data`) and the BFF's attachment headers.
 * `POST .../feedback` (the result card's quick feedback) validates the body
 * like the BFF (`reaction` from the site's set, `message` at most 500
 * characters after the strip, `include_data` a boolean, `result_version` 1 to
 * 999, no other field), answers `404 not_found` for a version the session does
 * not have, records the submission on the session per version (a later one
 * replaces it; `GET /mock/feedback` lists them) and answers `201 {case_id,
 * stored}` with the file names the BFF would store. A message containing "502"
 * answers `502 storage` instead, so the failure line can be driven.
 *
 * The step-1 data changes (the service's `prepare_data` tool) in miniature:
 * the action `{action: "summarize_data"}` answers a scripted summary of the
 * profile; a message containing "prozent" or "percent" plays a `set_type`
 * (number) on the second column (a unit such as `%` removed, a decimal comma
 * read), "gruppier" or "group" an `aggregate` (a numeric column summed by the
 * column the message names, "gruppier nach x", else by the first text column),
 * "umbenenn" or "rename" a `rename` of the second column. Each stores the result as the next dataset version (the previous one
 * kept, at most five, the bindings carried over, the confirmation dropped) and
 * the turn's `done.dataset` carries `{preview, profile, bindings, warnings,
 * roles, changes, version}` like the service; `POST .../dataset/undo` restores
 * the previous version (`422 nothing_to_undo` at the paste).
 *
 * The service's `generate_data` tool (a table computed from a formula) in
 * miniature: a message that contains "sin(" or "cos(" or "x**2", or "= " together
 * with "pi", "from" or "von", is a formula. A tiny fixed evaluator computes
 * `sin(x)`, `cos(x)` or `x**2` over 200 evenly spaced points (or the "N points"
 * the message names) of the range it names ("from -pi to pi", "von -3 bis 3"; by
 * default -pi to pi, -3 to 3 for the parabola), and the turn's `done.dataset`
 * carries the result: version 1 in a session without data (the roles included,
 * since the page has none yet), the next version otherwise, unconfirmed either
 * way. Pasted text that looks like a formula ("zeichne sin(x) von -pi bis pi",
 * "y = x**2") answers `422 formula` instead of the transcription, as the
 * service does, because a model must never compute rows.
 *
 * Scripted behaviour of a chat message:
 * - contains "weather" or "joke": the fixed out-of-scope refusal;
 * - contains "busy": `error {code: capacity}`;
 * - contains "swap": the root's `set_bindings` in miniature, swapping the
 *   columns of `x` and the first `y` (which drops the confirmation), and a reply;
 * - a formula (see above): `generate_data`, and a reply naming the rows;
 * - contains "prozent"/"percent", "gruppier"/"group" or "umbenenn"/"rename":
 *   a data change, see above, and a reply naming it;
 * - ends with "?": a reply only, no pipeline run;
 * - anything else: a refinement with a repair round, shipped as
 *   `needs_attention`; "dark" in the text renders the dark theme.
 * Pasted data containing "ignore previous" answers `403 data_refused`; pasted
 * text that looks like a formula answers `422 formula`.
 *
 * Environment: PORT (8010), MOCK_STEP_MS (700, per pipeline step),
 * MOCK_QUEUE_MS (2500, per queue position), MOCK_QUEUE (2, the starting
 * position of a turn; 0 skips the queue), MOCK_STOP_MS (2000, how long a run
 * stopped during a pipeline step takes to finish that step before `done`,
 * like the real run, which notices the abort only between steps; a turn that
 * still waits in the queue leaves it at once).
 */

import http from 'node:http';
import { randomBytes, randomUUID } from 'node:crypto';
import zlib from 'node:zlib';

const PORT = Number(process.env.PORT || 8010);
const STEP_MS = Number(process.env.MOCK_STEP_MS || 700);
const QUEUE_MS = Number(process.env.MOCK_QUEUE_MS || 2500);
const QUEUE_START = Number(process.env.MOCK_QUEUE ?? 2);
const STOP_MS = Number(process.env.MOCK_STOP_MS ?? 2000);
const BASE = `http://localhost:${PORT}`;

const role = (name, kinds, description, { required = true, variadic = false } = {}) => ({
  name,
  kinds,
  required,
  variadic,
  description,
});

// Two catalogue specs with the roles the agents service parses from their
// `## Data` bullets: scatter-basic (two single roles) and line-multi (a
// variadic series family `y1, y2, ...` and an optional role).
const SPECS = {
  'scatter-basic': {
    id: 'scatter-basic',
    title: 'Basic Scatter Plot',
    description:
      'A fundamental 2D scatter plot that displays the relationship between two numeric variables.',
    data: [
      '`x` (numeric) - Independent variable values plotted on the horizontal axis',
      '`y` (numeric) - Dependent variable values plotted on the vertical axis',
    ],
    notes: ['Points should have moderate transparency (alpha ~0.7) to reveal overlapping data'],
    roles: [
      role('x', ['numeric'], 'Independent variable values plotted on the horizontal axis'),
      role('y', ['numeric'], 'Dependent variable values plotted on the vertical axis'),
    ],
  },
  'line-multi': {
    id: 'line-multi',
    title: 'Multi-Line Comparison Plot',
    description:
      'A multi-line plot displays multiple data series on the same axes for direct comparison.',
    data: [
      '`x` (numeric/datetime) - Shared sequential or time values for alignment',
      '`y1, y2, ...` (numeric) - Multiple continuous series to compare',
      '`series` (categorical) - Optional grouping variable if data is in long format',
    ],
    notes: ['Use distinct colors for each series'],
    roles: [
      role('x', ['numeric', 'datetime'], 'Shared sequential or time values for alignment'),
      role('y', ['numeric'], 'Multiple continuous series to compare', { variadic: true }),
      role('series', ['categorical'], 'Optional grouping variable if data is in long format', {
        required: false,
      }),
    ],
  },
};
const AGENT_LIBRARIES = ['matplotlib', 'seaborn'];
const MAX_DATASET_BYTES = 200 * 1024;
/** What the agents service stores as the user's message of an action turn (`ACTION_MESSAGES`). */
const ACTION_MESSAGES = {
  create_plot: '[action] Create the plot from my dataset and bindings.',
  summarize_data: '[action] Summarize the dataset for the user.',
};

// ---------------------------------------------------------------- PNG drawing

const THEMES = {
  light: { bg: [0xfa, 0xf8, 0xf1], ink: [0x1a, 0x1a, 0x17], grid: [0xe4, 0xe1, 0xd8] },
  dark: { bg: [0x1a, 0x1a, 0x17], ink: [0xf0, 0xef, 0xe8], grid: [0x33, 0x33, 0x2e] },
};
const IMPRINT = ['#009E73', '#C475FD', '#4467A3', '#BD8233', '#AE3030', '#2ABCCD'].map(hex => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16),
]);

const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([length, body, crc]);
}

class Canvas {
  constructor(width, height, bg) {
    this.width = width;
    this.height = height;
    this.rgb = Buffer.alloc(width * height * 3);
    for (let i = 0; i < width * height; i += 1) this.rgb.set(bg, i * 3);
  }
  rect(x0, y0, x1, y1, color, alpha = 1) {
    for (let y = Math.max(0, Math.round(y0)); y < Math.min(this.height, Math.round(y1)); y += 1) {
      for (let x = Math.max(0, Math.round(x0)); x < Math.min(this.width, Math.round(x1)); x += 1) {
        this.blend(x, y, color, alpha);
      }
    }
  }
  disc(cx, cy, r, color, alpha) {
    for (let y = Math.floor(cy - r); y <= Math.ceil(cy + r); y += 1) {
      for (let x = Math.floor(cx - r); x <= Math.ceil(cx + r); x += 1) {
        if (x < 0 || y < 0 || x >= this.width || y >= this.height) continue;
        if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r) this.blend(x, y, color, alpha);
      }
    }
  }
  blend(x, y, color, alpha) {
    const i = (y * this.width + x) * 3;
    for (let c = 0; c < 3; c += 1) {
      this.rgb[i + c] = Math.round(this.rgb[i + c] * (1 - alpha) + color[c] * alpha);
    }
  }
  png() {
    const stride = this.width * 3;
    const raw = Buffer.alloc((stride + 1) * this.height);
    for (let y = 0; y < this.height; y += 1) {
      this.rgb.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
    }
    const header = Buffer.alloc(13);
    header.writeUInt32BE(this.width, 0);
    header.writeUInt32BE(this.height, 4);
    header.set([8, 2, 0, 0, 0], 8);
    return Buffer.concat([
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      chunk('IHDR', header),
      chunk('IDAT', zlib.deflateSync(raw)),
      chunk('IEND', Buffer.alloc(0)),
    ]);
  }
}

// ---------------------------------------------------------------- the footer strip

// The agents service appends a footer strip below every PNG it serves
// (agents/anyplot/render/watermark.py): defined on the 3200 px canvas and scaled
// with the width, so the mock's 1600x900 plots arrive as 1600x932. The mock draws
// the same layout with a 5x9 pixel font instead of JetBrains Mono, which is close
// enough to judge the result card at the served aspect.
const FOOTER = { strip: 64, text: 22, inset: 40, capEm: 0.73, dotEm: 1.45 };
const BRAND = [0x00, 0x9e, 0x73];
// Rows top to bottom; rows 0-6 sit above the baseline, rows 7-8 are descenders. Bit 4 is the left column.
const GLYPHS = {
  a: [0, 0, 14, 1, 15, 17, 15, 0, 0],
  b: [16, 16, 22, 25, 17, 17, 30, 0, 0],
  c: [0, 0, 14, 16, 16, 17, 14, 0, 0],
  d: [1, 1, 13, 19, 17, 17, 15, 0, 0],
  e: [0, 0, 14, 17, 31, 16, 14, 0, 0],
  f: [6, 9, 8, 28, 8, 8, 8, 0, 0],
  g: [0, 0, 15, 17, 17, 17, 15, 1, 14],
  h: [16, 16, 22, 25, 17, 17, 17, 0, 0],
  i: [4, 0, 12, 4, 4, 4, 14, 0, 0],
  j: [2, 0, 6, 2, 2, 2, 2, 18, 12],
  k: [16, 16, 18, 20, 24, 20, 18, 0, 0],
  l: [12, 4, 4, 4, 4, 4, 14, 0, 0],
  m: [0, 0, 26, 21, 21, 21, 21, 0, 0],
  n: [0, 0, 22, 25, 17, 17, 17, 0, 0],
  o: [0, 0, 14, 17, 17, 17, 14, 0, 0],
  p: [0, 0, 30, 17, 17, 17, 30, 16, 16],
  q: [0, 0, 15, 17, 17, 17, 15, 1, 1],
  r: [0, 0, 22, 25, 16, 16, 16, 0, 0],
  s: [0, 0, 15, 16, 14, 1, 30, 0, 0],
  t: [8, 8, 28, 8, 8, 9, 6, 0, 0],
  u: [0, 0, 17, 17, 17, 19, 13, 0, 0],
  v: [0, 0, 17, 17, 17, 10, 4, 0, 0],
  w: [0, 0, 17, 17, 21, 21, 10, 0, 0],
  x: [0, 0, 17, 10, 4, 10, 17, 0, 0],
  y: [0, 0, 17, 17, 17, 17, 15, 1, 14],
  z: [0, 0, 31, 2, 4, 8, 31, 0, 0],
  '-': [0, 0, 0, 0, 14, 0, 0, 0, 0],
  '/': [1, 2, 2, 4, 8, 8, 16, 0, 0],
  '(': [2, 4, 8, 8, 8, 4, 2, 0, 0],
  ')': [8, 4, 2, 2, 2, 4, 8, 0, 0],
};
const DOT = null;

function footerHeight(width) {
  return Math.round((FOOTER.strip * width) / 3200);
}

/** "made with any.plot()" and "anyplot.ai/<spec>" in the strip below the plot's `top` rows. */
function drawFooter(canvas, theme, specId, top) {
  const { ink } = THEMES[theme];
  const scale = canvas.width / 3200;
  const size = FOOTER.text * scale;
  const inset = FOOTER.inset * scale;
  const cell = Math.round(0.6 * size); // a monospaced advance
  const dot = FOOTER.dotEm * size;
  const side = Math.max(1, Math.round(0.185 * dot));
  const baseline = top + Math.round((footerHeight(canvas.width) + FOOTER.capEm * size) / 2);
  const widthOf = parts =>
    parts.reduce((sum, part) => sum + (part === DOT ? 0.64 * dot : part[0].length * cell), 0);
  const draw = (parts, start) => {
    let x = start;
    for (const part of parts) {
      if (part === DOT) {
        const x0 = Math.round(x + 0.251 * dot);
        canvas.rect(x0, baseline - side, x0 + side, baseline, BRAND, 0.9);
        x += 0.64 * dot;
        continue;
      }
      const [text, bold, alpha] = part;
      for (const ch of text) {
        (GLYPHS[ch] ?? []).forEach((bits, row) => {
          const mask = bold ? (bits << 1) | bits : bits << 1; // bold doubles each column
          for (let column = 0; column < 6; column += 1) {
            if (mask & (32 >> column)) {
              const px = Math.round(x) + column;
              const py = baseline - 7 + row;
              canvas.rect(px, py, px + 1, py + 1, ink, alpha);
            }
          }
        });
        x += cell;
      }
    }
  };
  canvas.rect(0, top, canvas.width, top + 1, ink, 0.15);
  const madeWith = [
    ['made with ', false, 0.56],
    ['any', true, 0.7],
    DOT,
    ['plot', true, 0.7],
    ['()', false, 0.315],
  ];
  draw(madeWith, inset);
  const address = [['anyplot', true, 0.7], DOT, ['ai', true, 0.7], [`/${specId}`, false, 0.56]];
  draw(address, canvas.width - inset - widthOf(address));
}

/**
 * A plot-like PNG: axes, a light grid, and either a scatter of each series in
 * `series` or bars; with `footer` (a spec id), the served footer strip below it.
 */
function drawPlot(
  theme,
  series,
  { width = 1600, height = 900, firstColor = 0, footer = null } = {}
) {
  const { bg, ink, grid } = THEMES[theme];
  const canvas = new Canvas(width, footer ? height + footerHeight(width) : height, bg);
  const left = width * 0.09;
  const right = width * 0.96;
  const top = height * 0.08;
  const bottom = height * 0.88;
  for (let i = 1; i <= 4; i += 1) {
    const y = bottom - ((bottom - top) * i) / 4;
    canvas.rect(left, y, right, y + 2, grid);
    const x = left + ((right - left) * i) / 4;
    canvas.rect(x, top, x + 2, bottom, grid);
  }
  canvas.rect(left, top, left + 3, bottom + 3, ink);
  canvas.rect(left, bottom, right, bottom + 3, ink);
  const all = (series ?? []).flat();
  if (all.length > 1) {
    const xs = all.map(p => p[0]);
    const ys = all.map(p => p[1]);
    const [xmin, xmax] = [Math.min(...xs), Math.max(...xs)];
    const [ymin, ymax] = [Math.min(...ys), Math.max(...ys)];
    const sx = v => left + 30 + ((v - xmin) / (xmax - xmin || 1)) * (right - left - 60);
    const sy = v => bottom - 30 - ((v - ymin) / (ymax - ymin || 1)) * (bottom - top - 60);
    series.forEach((points, index) => {
      const color = IMPRINT[(firstColor + index) % IMPRINT.length];
      for (const [x, y] of points) canvas.disc(sx(x), sy(y), height * 0.016, color, 0.72);
    });
  } else {
    const bar = (right - left) / 12;
    IMPRINT.forEach((c, i) => {
      const x0 = left + bar * 0.6 + i * bar * 1.6;
      canvas.rect(x0, bottom - (i + 2) * ((bottom - top) / 9), x0 + bar, bottom - 2, c);
    });
  }
  if (footer) drawFooter(canvas, theme, footer, height);
  return canvas.png();
}

const catalogueImages = new Map();
function cataloguePng(theme) {
  if (!catalogueImages.has(theme)) catalogueImages.set(theme, drawPlot(theme, null));
  return catalogueImages.get(theme);
}

// ---------------------------------------------------------------- data parsing

function splitLine(line, delimiter) {
  const cells = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') quoted = false;
      else cell += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delimiter) {
      cells.push(cell.trim());
      cell = '';
    } else cell += ch;
  }
  cells.push(cell.trim());
  return cells;
}

/**
 * The transcribed answer of `POST .../dataset` for text that is no table: every
 * `<label> <number>` pair becomes a row of `category,value`, and the CSV goes
 * through `parseDataset` so the preview and profile match a later `.use()`.
 * Returns null when the text holds no such pair (the real service answers 422).
 */
function transcribeFreeText(text) {
  const pairs = [...text.matchAll(/([\p{L}][\p{L}\p{N}_-]*)\s+(-?\d+(?:[.,]\d+)?)\b/gu)];
  if (!pairs.length) return null;
  const rows = pairs.map(([, label, number]) => [label, number.replace(',', '.')]);
  const csv = ['category,value', ...rows.map(row => row.join(','))].join('\n') + '\n';
  const parsed = parseDataset(csv);
  return {
    transcribed: true,
    text: csv,
    preview: parsed.preview,
    profile: parsed.profile,
    warnings: parsed.warnings,
    note: rows.length < 3 ? 'only two values found; check the text' : '',
  };
}

function parseDataset(text) {
  const trimmed = text.replace(/^﻿/, '').trim();
  let header;
  let rows;
  let format;
  if (trimmed.startsWith('[')) {
    const records = JSON.parse(trimmed);
    if (!Array.isArray(records) || !records.length || typeof records[0] !== 'object') {
      throw new Error('unparseable');
    }
    header = Object.keys(records[0]);
    rows = records.map(record => header.map(name => String(record[name] ?? '')));
    format = 'json_records';
  } else {
    const lines = trimmed.split(/\r\n|\r|\n/).filter(line => line.trim());
    if (lines.length < 2) throw new Error('unparseable');
    const candidates = [
      [',', 'csv'],
      [';', 'semicolon'],
      ['\t', 'tsv'],
      ['|', 'pipe'],
    ];
    const [delimiter, name] = candidates
      .map(([d, n]) => [d, n, splitLine(lines[0], d).length])
      .sort((a, b) => b[2] - a[2])[0];
    header = splitLine(lines[0], delimiter);
    if (header.length < 2) throw new Error('unparseable');
    rows = lines.slice(1).map(line => splitLine(line, delimiter));
    format = name;
  }
  const warnings = [];
  header = header.map((name, index) => {
    if (name) return name.slice(0, 64);
    warnings.push(`column ${index + 1} has no name; it is called 'column_${index + 1}'`);
    return `column_${index + 1}`;
  });
  rows = rows.map(row => header.map((_, index) => row[index] ?? ''));
  const columns = header.map((name, index) => {
    const cells = rows.map(row => row[index]);
    const present = cells.filter(cell => cell !== '');
    const numeric =
      present.length > 0 && present.every(cell => /^-?\d+(\.\d+)?(e[+-]?\d+)?$/i.test(cell));
    const integer = numeric && present.every(cell => /^-?\d+$/.test(cell));
    const date =
      !numeric && present.length > 0 && present.every(c => /^\d{4}-\d{2}(-\d{2})?$/.test(c));
    const dtype = integer ? 'integer' : numeric ? 'number' : date ? 'datetime' : 'text';
    const values = numeric ? present.map(Number) : [];
    const counts = new Map();
    for (const cell of present) counts.set(cell, (counts.get(cell) ?? 0) + 1);
    const missing = cells.length - present.length;
    if (missing)
      warnings.push(`column '${name}': ${missing} missing value${missing > 1 ? 's' : ''}`);
    const sorted = [...values].sort((a, b) => a - b);
    const median = sorted.length
      ? sorted.length % 2
        ? sorted[(sorted.length - 1) / 2]
        : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : null;
    return {
      name,
      dtype,
      missing,
      unique: counts.size,
      min: numeric ? Math.min(...values) : (present[0] ?? null),
      max: numeric ? Math.max(...values) : (present[present.length - 1] ?? null),
      // The service's statistics of a numeric column (six significant digits), for the step-1 summary.
      mean: numeric
        ? Number((values.reduce((a, b) => a + b, 0) / values.length).toPrecision(6))
        : null,
      median: numeric ? Number(median.toPrecision(6)) : null,
      top: [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([cell]) => cell.slice(0, 40)),
    };
  });
  return {
    header,
    rows,
    profile: {
      rows: rows.length,
      columns,
      sample: rows.slice(0, 5),
      source_format: format,
      decimal: '.',
      warnings,
    },
    preview: rows.slice(0, 20).map(row => row.map(cell => cell.slice(0, 40))),
    warnings,
  };
}

// The agents service's ACCEPTS table (agents/anyplot/data/bindings.py), without the tiers.
const ACCEPTS = {
  numeric: ['number', 'integer'],
  categorical: ['text', 'boolean', 'integer'],
  text: ['text', 'boolean', 'integer'],
  boolean: ['boolean', 'integer'],
  datetime: ['datetime'],
};
const accepts = (spec, dtype) =>
  !spec.kinds.length || spec.kinds.some(kind => ACCEPTS[kind]?.includes(dtype));

/** The role a binding name refers to: an exact single role, else the family `<name><digits>`. */
function resolveRole(roles, name) {
  return (
    roles.find(r => !r.variadic && r.name === name) ??
    roles.find(r => r.variadic && new RegExp(`^${r.name}\\d+$`).test(name)) ??
    null
  );
}

/** Like `check_bindings`: the error lines, or the stored set with its completeness. */
function checkBindings(session, bindings) {
  const roles = SPECS[session.specId].roles;
  const columns = new Map(session.dataset.profile.columns.map(c => [c.name, c]));
  const errors = [];
  const seen = new Set();
  const bound = new Set();
  for (const { role: name, column } of bindings) {
    const spec = resolveRole(roles, name);
    const family = roles.find(r => r.variadic && r.name === name);
    if (!spec) {
      errors.push(
        family
          ? `role '${name}' takes numbered members such as '${name}1'`
          : `unknown role '${name}'`
      );
      continue;
    }
    if (!columns.has(column)) errors.push(`column '${column}' is not in the dataset`);
    else if (seen.has(column)) errors.push(`column '${column}' is bound more than once`);
    else if (!accepts(spec, columns.get(column).dtype)) {
      errors.push(
        `role '${name}' needs ${spec.kinds.join(' or ')} data, but column '${column}' is ${columns.get(column).dtype}`
      );
    } else bound.add(spec.name);
    seen.add(column);
  }
  const missing = roles.filter(r => r.required && !bound.has(r.name)).map(r => r.name);
  return { errors, bindings, complete: !errors.length && !missing.length, missing_roles: missing };
}

/** Required roles first; a family takes every unused numeric column, a single role the first fit. */
function defaultBindings(session, profile) {
  const roles = SPECS[session.specId].roles;
  const used = new Set();
  const bindings = [];
  const order = [...roles.filter(r => r.required), ...roles.filter(r => !r.required)];
  for (const spec of order) {
    const free = profile.columns.filter(c => !used.has(c.name) && accepts(spec, c.dtype));
    if (spec.variadic) {
      const numeric = free.filter(c => c.dtype !== 'datetime');
      numeric.slice(0, 12).forEach((c, i) => {
        bindings.push({ role: `${spec.name}${i + 1}`, column: c.name });
        used.add(c.name);
      });
    } else if (free.length) {
      bindings.push({ role: spec.name, column: free[0].name });
      used.add(free[0].name);
    }
  }
  return bindings;
}

// The helpers below read `dataset` and `bindings` from whatever holds them: the
// session while a run is in progress, or a version afterwards. A version keeps the
// dataset and bindings it was made from (the session replaces, never mutates,
// both on a reparse or a binding change), so its code, its CSV and a later theme
// render stay its own after the admin pastes new data, like the real service's
// stored run form.

function csvText(holder) {
  const quote = cell => (/[",\n]/.test(cell) ? `"${cell.replace(/"/g, '""')}"` : cell);
  return [holder.dataset.header, ...holder.dataset.rows]
    .map(row => row.map(quote).join(','))
    .join('\n')
    .concat('\n');
}

const columnOf = (holder, name) => holder.bindings.find(b => b.role === name)?.column;
/** The bound y columns: `y` of scatter-basic, or every member `y1, y2, ...` of line-multi. */
const yColumns = holder => holder.bindings.filter(b => /^y\d*$/.test(b.role)).map(b => b.column);

/** One point list per y column; a non-numeric x (a date) plots by row order. */
function points(holder) {
  const names = holder.dataset.header;
  const x = names.indexOf(columnOf(holder, 'x'));
  if (x < 0) return null;
  return yColumns(holder).map(column => {
    const y = names.indexOf(column);
    return holder.dataset.rows
      .map((row, index) => [
        Number.isFinite(Number(row[x])) ? Number(row[x]) : index,
        Number(row[y]),
      ])
      .filter(([a, b]) => Number.isFinite(a) && Number.isFinite(b));
  });
}

function plotPy(session, version) {
  const x = columnOf(version, 'x') ?? 'x';
  const y = yColumns(version)[0] ?? 'y';
  const markerSize = version.number > 1 ? 160 : 110;
  return `# Adapted by anyplot.ai from ${session.specId} (${version.library}) for your data.csv; run: \`ANYPLOT_THEME=${version.theme} python plot.py\`
import os

import matplotlib.pyplot as plt
import pandas as pd

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
GRID = "#E4E1D8" if THEME == "light" else "#33332E"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

df = pd.read_csv("data.csv")

fig, ax = plt.subplots(figsize=(16, 9), dpi=200, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.scatter(df[${JSON.stringify(x)}], df[${JSON.stringify(y)}], s=${markerSize}, alpha=0.7, color=IMPRINT[0], edgecolor=PAGE_BG, linewidth=0.8)
ax.set_xlabel(${JSON.stringify(x)}, fontsize=20, color=INK)
ax.set_ylabel(${JSON.stringify(y)}, fontsize=20, color=INK)
ax.set_title("", fontsize=24, color=INK)
ax.tick_params(colors=INK, labelsize=16)
ax.grid(True, color=GRID, linewidth=1)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK)

fig.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
`;
}

// ---------------------------------------------------------------- sessions

const sessions = new Map();
let waitingTurns = 0;
let runsInFlight = 0;

function renderVersion(session, version, theme) {
  version.pngs[theme] = drawPlot(theme, points(version), {
    firstColor: version.number > 1 ? 2 : 0,
    footer: session.specId,
  });
}

// ---------------------------------------------------------------- HTTP helpers

function cors(req, res) {
  const origin = req.headers.origin;
  if (origin && /^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Vary', 'Origin');
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'Content-Type, Accept, X-Anyplot-Client, X-Admin-Token'
  );
  res.setHeader('Access-Control-Expose-Headers', 'X-Request-Id');
}

function json(res, status, body, ref) {
  const headers = { 'Content-Type': 'application/json', 'Cache-Control': 'private, no-store' };
  if (ref) headers['X-Request-Id'] = ref;
  res.writeHead(status, headers);
  res.end(JSON.stringify(body));
}

function fail(res, status, detail, ref) {
  json(res, status, ref ? { detail, ref } : { detail }, ref);
}

async function readBody(req) {
  const chunks = [];
  for await (const part of req) chunks.push(part);
  const text = Buffer.concat(chunks).toString('utf8');
  return text ? JSON.parse(text) : null;
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// ---------------------------------------------------------------- the chat turn

async function streamTurn(req, res, session, body, ref) {
  const text = typeof body.text === 'string' ? body.text : '';
  const lower = text.toLowerCase();
  let closed = false;
  req.on('close', () => {
    closed = true;
  });
  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'private, no-store',
    'X-Request-Id': ref,
    'X-Accel-Buffering': 'no',
  });
  const send = (event, data) => {
    // The bundle's transcript: the user's words or action and the assistant's replies.
    if (event === 'message') session.transcript.push({ role: 'assistant', text: data.text });
    if (!closed) res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };
  session.transcript.push({
    role: 'user',
    text: body.action ? (ACTION_MESSAGES[body.action] ?? `[action] ${body.action}`) : text,
  });
  const ping = () => {
    if (!closed) res.write(': ping\n\n');
  };
  const stopped = () => closed || session.cancelled;
  // Like the real queue, a cancel or a disconnect ends the wait at once.
  const wait = async ms => {
    for (let left = ms; left > 0 && !stopped(); left -= 100) await sleep(Math.min(100, left));
  };
  session.active = true;
  session.cancelled = false;
  session.changed = null; // set by a data change of this turn, carried in `done.dataset`
  try {
    send('ready', { v: 'anyplot/1', run_id: randomBytes(8).toString('hex') });
    // Pretend `QUEUE_START - 1` other turns wait ahead of this one.
    let queued = Math.max(0, QUEUE_START);
    waitingTurns += queued;
    try {
      for (let position = queued; position >= 1; position -= 1) {
        send('status', { step: 'queued', position, waiting: waitingTurns });
        await wait(QUEUE_MS / 2);
        ping();
        await wait(QUEUE_MS / 2);
        waitingTurns -= 1;
        queued -= 1;
        if (stopped()) return;
      }
    } finally {
      waitingTurns -= queued;
    }
    runsInFlight += 1;
    try {
      if (body.action === 'summarize_data') {
        await sleep(STEP_MS * 2);
        send('message', { text: summarizeData(session) });
        return;
      }
      if (asksForFormula(lower)) {
        await sleep(STEP_MS * 2);
        send('message', { text: generateData(session, lower) });
        return;
      }
      const change = /prozent|percent/.test(lower)
        ? setTypeNumber
        : /gruppier|group/.test(lower)
          ? s => aggregateSum(s, lower)
          : /umbenenn|rename/.test(lower)
            ? s => renameSecond(s, /umbenenn/.test(lower))
            : null;
      if (change) {
        await sleep(STEP_MS * 2);
        send('message', { text: session.dataset ? change(session) : 'Paste your data first.' });
        return;
      }
      if (/weather|joke/.test(lower)) {
        await sleep(STEP_MS);
        send('refusal', {
          code: 'out_of_scope',
          text: 'I can only help with this plot and your data for it: choosing columns, adapting, styling and exporting the plot, and questions about its code.',
        });
        return;
      }
      if (lower.includes('busy')) {
        await sleep(STEP_MS);
        send('error', { code: 'capacity', ref });
        return;
      }
      if (lower.includes('swap')) {
        await sleep(STEP_MS);
        send('message', { text: swapBindings(session) });
        return;
      }
      if (text.trim().endsWith('?')) {
        await sleep(STEP_MS * 2);
        send('message', {
          text: 'The x axis uses the column you bound to x; the marker size is the s= argument of ax.scatter, line 18 of plot.py.',
        });
        return;
      }
      if (!session.dataset || !session.complete || !session.confirmed) {
        await sleep(STEP_MS);
        const reason = !session.dataset
          ? 'no_dataset'
          : !session.complete
            ? 'incomplete_bindings'
            : 'data_unconfirmed';
        send('plot', {
          status: 'not_ready',
          reason,
          attempts: 0,
          artifacts: [],
          changes: [],
          residual_defects: [],
        });
        send('message', {
          text:
            reason === 'data_unconfirmed'
              ? 'Check the preview and the bindings, then confirm your data first.'
              : 'Paste your data and bind the required roles first.',
        });
        return;
      }
      const refine = body.action !== 'create_plot';
      const steps = refine
        ? [
            ['adapting', 1],
            ['checking', 1],
            ['rendering', 1],
            ['reviewing', 1],
            ['repairing', 2],
            ['checking', 2],
            ['rendering', 2],
          ]
        : [
            ['adapting', 1],
            ['checking', 1],
            ['rendering', 1],
            ['reviewing', 1],
          ];
      for (const [step, attempt] of steps) {
        if (stopped()) return;
        send('status', { step, attempt });
        await wait(STEP_MS);
        // A stopped run finishes the step in progress before it ends.
        if (session.cancelled && !closed) await sleep(STOP_MS);
      }
      if (stopped()) return;
      const previous = session.versions[session.versions.length - 1];
      const theme = lower.includes('dark') ? 'dark' : refine && previous ? previous.theme : 'light';
      const version = {
        number: session.versions.length + 1,
        library: session.library,
        theme,
        dataset: session.dataset,
        bindings: session.bindings,
        pngs: {},
      };
      renderVersion(session, version, theme);
      session.versions.push(version);
      const x = columnOf(version, 'x');
      const y = yColumns(version).join(', ');
      // Kept on the version for the bundle, like the service's stored `PlotResult`.
      version.result = {
        status: refine ? 'needs_attention' : 'ok',
        reason: null,
        attempts: refine ? 2 : 1,
        artifacts: [`plot-${theme}.png`, 'plot.py', 'data.csv'],
        changes: refine
          ? ['Applied your change request', 'Marker size raised from 110 to 160']
          : [`x now reads ${x}, y reads ${y}`, 'Axis labels name your columns'],
        residual_defects: refine
          ? ['VQ-03 light: two markers overlap the y axis label; likely cause: axis limits']
          : [],
        // The stored version's number, which the artifact and theme routes take.
        version: version.number,
      };
      send('plot', version.result);
      await sleep(STEP_MS / 2);
      send('message', {
        text: refine
          ? 'Done. One note remains: two markers sit close to the y axis label.'
          : `Here is ${SPECS[session.specId].title.toLowerCase()} with your data: ${x} on x and ${y} on y.`,
      });
    } finally {
      runsInFlight -= 1;
    }
  } finally {
    session.active = false;
    // The sync fields: the session's bindings and step state after the run, and the
    // new dataset version after a turn that changed the data.
    send('done', {
      llm_calls: 4,
      tokens: 18734,
      bindings: session.bindings,
      data_confirmed: session.confirmed,
      ...(session.changed ? { dataset: session.changed } : {}),
    });
    res.end();
  }
}

/**
 * The root's `set_bindings` in miniature: swap the columns of `x` and the first
 * `y`, as the binding check allows it. An applied change drops the confirmation.
 */
function swapBindings(session) {
  const x = session.bindings.find(b => b.role === 'x');
  const y = session.bindings.find(b => /^y1?$/.test(b.role));
  if (!session.dataset || !x || !y) return 'There is nothing to swap yet: paste your data first.';
  const swapped = session.bindings.map(b =>
    b === x ? { ...b, column: y.column } : b === y ? { ...b, column: x.column } : b
  );
  const { errors, complete } = checkBindings(session, swapped);
  if (errors.length) return `I cannot swap them: ${errors[0]}.`;
  session.bindings = swapped;
  session.complete = complete;
  session.confirmed = false;
  return `Swapped: x now reads ${y.column} and ${y.role} reads ${x.column}. Check the bindings and confirm your data again.`;
}

// ---------------------------------------------------------------- data versions (prepare_data in miniature)

const MAX_DATASET_HISTORY = 5;

/** The CSV of a header and rows, for a re-parse through `parseDataset` after an operation. */
function toCsv(header, rows) {
  const quote = cell => (/[",\n]/.test(cell) ? `"${cell.replace(/"/g, '""')}"` : cell);
  return [header, ...rows].map(row => row.map(quote).join(',')).join('\n') + '\n';
}

/**
 * `carry_bindings`: the bindings still valid for the new profile stay, the roles left
 * (a family counts as bound while one member stays) get the defaults, computed on the
 * columns no kept binding uses, so a role whose first choice is taken gets its next one.
 */
function carryBindings(session, bindings, profile) {
  const holder = { specId: session.specId, dataset: { profile } };
  const kept = bindings.filter(b => !checkBindings(holder, [b]).errors.length);
  if (kept.length === bindings.length) return bindings;
  const used = new Set(kept.map(b => b.column));
  const bound = new Set(kept.map(b => b.role.replace(/\d+$/, '')));
  const free = { ...profile, columns: profile.columns.filter(c => !used.has(c.name)) };
  for (const b of defaultBindings(session, free)) {
    if (!bound.has(b.role.replace(/\d+$/, ''))) kept.push(b);
  }
  return kept;
}

/** Store `parsed` as the session's next dataset version; the previous one joins the history (at most five). */
function storeVersion(session, parsed, changes) {
  session.history.push({ dataset: session.dataset, bindings: session.bindings });
  session.history = session.history.slice(-MAX_DATASET_HISTORY);
  session.dataset = parsed;
  session.bindings = carryBindings(session, session.bindings, parsed.profile);
  session.complete = checkBindings(session, session.bindings).complete;
  session.confirmed = false; // the user confirms every version they see
  session.version += 1;
  session.changed = { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes };
}

/** `{preview, profile, bindings, warnings, version}`: a dataset as the routes and `done.dataset` answer it. */
function datasetPayload(session) {
  return {
    preview: session.dataset.preview,
    profile: session.dataset.profile,
    bindings: session.bindings,
    warnings: session.dataset.warnings,
    version: session.version,
  };
}

/** The unit token at either end of a cell (`12,5 %`, `€ 12`), or null; a plain number has none. */
function unitOf(cell) {
  const match = cell.match(/^(?:([^\d\s+-][^\d]*?)\s*)?[+-]?[\d.,' ]*\d(?:\s*([^\d\s][^\d]*))?$/);
  return match ? (match[1] ?? match[2] ?? null) : null;
}

/** `set_type number` on the second column: the unit removed, thousands separators dropped, a decimal comma read. */
function setTypeNumber(session) {
  const { header, rows } = session.dataset;
  if (header.length < 2) return 'There is no second column to read as numbers.';
  const index = 1;
  const column = header[index];
  if (session.dataset.profile.columns[index].dtype !== 'text')
    return `${column} already holds numbers; nothing changed.`;
  const decimalComma = rows.some(row => /\d,\d/.test(row[index]));
  const units = new Set();
  let failed = 0;
  const converted = rows.map(row => {
    const cell = row[index];
    if (!cell) return '';
    const unit = unitOf(cell);
    if (unit) units.add(unit);
    let body = unit ? cell.replace(unit, '').trim() : cell;
    body = body.replace(/[\s']/g, '').replace(decimalComma ? /\./g : /,/g, '');
    if (decimalComma) body = body.replace(',', '.');
    if (!/^[+-]?\d+(\.\d+)?$/.test(body)) {
      failed += 1;
      return '';
    }
    return body;
  });
  if (units.size > 1)
    return `I cannot read ${column} as numbers: it mixes ${units.size} different units.`;
  const present = rows.filter(row => row[index]).length;
  if (present && failed / present > 0.1)
    return `I cannot read ${column} as numbers: ${failed} of ${present} cells are no number.`;
  const parsed = parseDataset(
    toCsv(
      header,
      rows.map((row, i) => row.map((c, j) => (j === index ? converted[i] : c)))
    )
  );
  let change = `${column}: ${present - failed} cells read as numbers`;
  if (units.size) change += `, unit '${[...units][0]}' removed`;
  if (failed)
    change += `, ${failed} cell${failed > 1 ? 's' : ''} could not be read and ${failed > 1 ? 'are' : 'is'} now missing`;
  storeVersion(session, parsed, [change]);
  return `I read ${column} as numbers${units.size ? ` and removed the unit '${[...units][0]}'` : ''}. Check the preview and confirm the data.`;
}

/**
 * `aggregate`: the first other numeric column summed by the column the message
 * names after "nach", "by", "per" or "pro" ("gruppier nach Monat"), else by the
 * first text column; the other columns go.
 */
function aggregateSum(session, lower) {
  const { header, rows, profile } = session.dataset;
  const escape = name => name.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const named = header.findIndex(name =>
    new RegExp(`(?:nach|by|per|pro)\\s+${escape(name)}(?![\\p{L}\\p{N}_])`, 'u').test(lower)
  );
  const key = named >= 0 ? named : profile.columns.findIndex(c => c.dtype === 'text');
  const value = profile.columns.findIndex(
    (c, i) => i !== key && (c.dtype === 'number' || c.dtype === 'integer')
  );
  if (key < 0 || value < 0) return 'I need a column to group by and a number column to sum.';
  const sums = new Map();
  for (const row of rows) {
    const number = Number(row[value]);
    if (!row[value] || !Number.isFinite(number)) continue;
    sums.set(row[key], (sums.get(row[key]) ?? 0) + number);
  }
  const grouped = [...sums.entries()]
    .sort(([a], [b]) => a.localeCompare(b, 'en', { numeric: true }))
    .map(([k, v]) => [k, String(v)]);
  if (!grouped.length) return 'There is nothing to sum.';
  const parsed = parseDataset(toCsv([header[key], header[value]], grouped));
  const other = header.length - 2;
  let change = `summed ${header[value]} by ${header[key]}: ${grouped.length} row${grouped.length > 1 ? 's' : ''}`;
  if (other) change += `, ${other} other column${other > 1 ? 's' : ''} dropped`;
  storeVersion(session, parsed, [change]);
  return `I summed ${header[value]} per ${header[key]}: ${grouped.length} rows. Check the preview and confirm the data.`;
}

/** `rename`: the second column gets a new name. */
function renameSecond(session, german) {
  const { header, rows } = session.dataset;
  if (header.length < 2) return 'There is no second column to rename.';
  const name = german ? 'Wert' : 'Value';
  if (header.includes(name)) return `A column named '${name}' already exists.`;
  const renamed = header.map((h, i) => (i === 1 ? name : h));
  const parsed = parseDataset(toCsv(renamed, rows));
  storeVersion(session, parsed, [`renamed '${header[1]}' to '${name}'`]);
  return `I renamed ${header[1]} to ${name}. Check the preview and confirm the data.`;
}

// ---------------------------------------------------------------- formulas (generate_data in miniature)

/** Whether a chat message asks for a formula: `sin(`, `cos(` or `x**2`, or `= ` with "pi", "from" or "von". */
function asksForFormula(lower) {
  return (
    /\b(?:sin|cos)\(|x\*\*2/.test(lower) ||
    (lower.includes('= ') && /\bpi\b|\bfrom\b|\bvon\b/.test(lower))
  );
}

/**
 * The dataset route's guard, a short form of the service's `looks_like_formula`. Text
 * that holds its own values (three numbers or more besides its ranges, expressions and
 * point counts) is data. Otherwise a line or sentence of at most 300 characters asks
 * for a formula with a call whose argument holds a variable (`sin(x)`, never `Max(3)`),
 * an assignment of an expression to a short name (`y = x**2`, never `Äpfel = 3x`), or
 * a range phrase with numbers or pi next to pi, a one-letter variable before it, a
 * power (never a unit such as `m²`) or a curve's name such as "Parabel" (never a word
 * that data has as well, such as "curve" or "Quadratmeter").
 */
function looksLikeFormula(text) {
  const trimmed = text.trim();
  if (!trimmed || trimmed.length > 4000) return false;
  const lines = trimmed.split(/\r\n|\r|\n/).filter(line => line.trim());
  const delimiter = [',', ';', '\t', '|'].find(mark => lines[0].includes(mark));
  if (lines.length > 1 && delimiter && lines.filter(line => line.includes(delimiter)).length >= 2) {
    return false; // a table, perhaps a broken one
  }
  const end = String.raw`[-+]?\s*(?:\d+(?:[.,]\d+)?\s*\*?\s*(?:pi)?|pi)`;
  const phrase = String.raw`\b(?:from|von|between|zwischen)\s+(${end})\s+(?:to|bis|and|und)\s+(${end})(?!\w)`;
  const range = new RegExp(phrase, 'gi');
  const call = /(?<![\w.])(?:sin|cos|tan|exp|log|sqrt|abs|min|max)\s*\(([^()]*)\)/gi;
  const stop = String.raw`(?=\s+(?:from|von|for|für|mit|with)\b|[,;\n]|$)`;
  const name = String.raw`(?<![\w.])(?:[a-z]\w?|[a-z]\w*\([a-z]\))`;
  const assignment = new RegExp(String.raw`${name}\s*=\s*([^=\n,;]*?)${stop}`, 'gi');
  const power = /\*\*|(?<=[\w)])\s?\^|(?<![a-z])[a-ln-z]\s?[²³]/i;
  const shape = /\b(?:sinus\w*|[ck]osinus\w*|parab\w*|squared|normalverteilung|gau\w*kurve)/i;
  const subject = /(?<![\w.,-])(?<!\bin )[b-df-z](?:\s+(?:and|und)\s+[b-df-z])?\s+$/;
  let formula = false;
  for (const segment of trimmed.split(/\n|(?<=[.!?;])\s+/).filter(part => part.length <= 300)) {
    for (const match of segment.matchAll(call)) {
      const argument = match[1].trim();
      const lowercase = /^[a-z]/.test(match[0]);
      if (/[a-z]/i.test(argument) && (lowercase || /^[a-z]$|[-+*/^]/i.test(argument))) {
        formula = true;
      }
    }
    for (const match of segment.matchAll(assignment)) {
      const right = match[1].trim();
      if (/[a-z]/i.test(right) && /\*\*|[*^/+-]|\(|^[a-z]\w?$/i.test(right)) {
        formula = true;
      }
    }
    for (const match of segment.matchAll(range)) {
      const constant = /pi/i.test(match[1] + match[2]);
      const variable = subject.test(segment.slice(0, match.index));
      if (constant || variable || power.test(segment) || shape.test(segment)) {
        formula = true;
      }
    }
  }
  const rest = trimmed
    .replace(range, ' ')
    .replace(call, match => (/[a-z]/i.test(match.slice(match.indexOf('('))) ? ' ' : match))
    .replace(assignment, ' ')
    .replace(/\d+\s*(?:points?|punkte?n?)\b/gi, ' ');
  const value = /(?<![\w.^*/+-])[-+]?\d+(?:[.,]\d+)?(?![*^/]|[a-z]?\s*[*^/]|[a-z]\s*[+-])/gi;
  return formula && (rest.match(value) ?? []).length < 3;
}

/** A range end the message names: a number, `pi`, `-pi`, `2 pi` or `2*pi`; null for anything else. */
function rangeEnd(text) {
  const match = text.trim().match(/^([+-])?\s*(\d+(?:[.,]\d+)?)?\s*\*?\s*(pi|π)?$/);
  if (!match || (!match[2] && !match[3])) return null;
  const number = match[2] ? Number(match[2].replace(',', '.')) : 1;
  return (match[1] === '-' ? -1 : 1) * number * (match[3] ? Math.PI : 1);
}

/** A value close to the parser's number text: eight significant digits, `1.0` for a whole one, no `-0.0`. */
function pyFloat(value) {
  if (!Number.isFinite(value)) return '';
  const rounded = Number(value.toPrecision(8));
  if (rounded === 0) return '0.0';
  if (Number.isInteger(rounded) && Math.abs(rounded) < 1e16) return rounded.toFixed(1);
  return String(rounded).replace(/e([+-])(\d)$/, 'e$10$2'); // Python writes 1e-07 where JS writes 1e-7
}

/**
 * `generate_data` in miniature: `sin(x)`, `cos(x)` or `x**2` over the range the message
 * names, stored as version 1 in a session without data (default bindings, no history) or
 * as the next version (`storeVersion`), unconfirmed either way, like the service.
 */
function generateData(session, lower) {
  const [formula, f, defaultStart, defaultStop] = lower.includes('cos(')
    ? ['cos(x)', Math.cos, -Math.PI, Math.PI]
    : lower.includes('sin(')
      ? ['sin(x)', Math.sin, -Math.PI, Math.PI]
      : ['x**2', x => x * x, -3, 3];
  let [start, stop] = [defaultStart, defaultStop];
  const range = lower.match(
    /\b(?:from|von)\s+(.+?)\s+(?:to|bis)\s+([-+]?\s*[\d.,]*\s*\*?\s*(?:pi|π)?)(?![\w.])/
  );
  if (range) {
    const [a, b] = [rangeEnd(range[1]), rangeEnd(range[2])];
    if (a !== null && b !== null && a !== b) [start, stop] = [a, b];
  }
  const named = lower.match(/(\d+)\s*(?:points|punkte)/);
  const points = named ? Math.min(Math.max(Number(named[1]), 2), 5000) : 200;
  const rows = Array.from({ length: points }, (_, i) => {
    const x = i === points - 1 ? stop : start + ((stop - start) * i) / (points - 1);
    return [pyFloat(x), pyFloat(f(x))];
  });
  const parsed = parseDataset(toCsv(['x', 'y'], rows));
  const short = value => String(Number(value.toPrecision(5)));
  const span = `x from ${short(start)} to ${short(stop)}`;
  const changes = [`generated ${points} rows: ${span}, y = ${formula}`];
  const first = !session.dataset;
  if (first) {
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false;
    session.history = [];
    session.version = 1;
    session.changed = { ...datasetPayload(session), roles: SPECS[session.specId].roles, changes };
  } else {
    storeVersion(session, parsed, changes);
  }
  const undo = first
    ? ''
    : ' as a new version of your data; .undo() in the data panel takes it back';
  return `I generated ${points} rows from y = ${formula} for ${span}${undo}. Check the preview and confirm the data.`;
}

/** The step-1 summary the root writes after `summarize_data`, from the profile alone. */
function summarizeData(session) {
  if (!session.dataset) return 'Paste your data first; then I can summarize it.';
  const { profile } = session.dataset;
  const columns = profile.columns
    .map(
      c =>
        `${c.name} (${c.dtype}${c.dtype === 'number' || c.dtype === 'integer' ? `, mean ${c.mean}` : ''})`
    )
    .join(', ');
  const missing = profile.columns.filter(c => c.missing).map(c => `${c.missing} in ${c.name}`);
  const percent = profile.columns.find(c => c.top.some(v => /%$/.test(v)));
  const bound = session.bindings.map(b => `${b.role} → ${b.column}`).join(', ');
  return [
    `${profile.rows} rows and ${profile.columns.length} columns: ${columns}.`,
    missing.length ? `Missing values: ${missing.join(', ')}.` : 'No values are missing.',
    `Proposed bindings: ${bound || 'none yet'}.`,
    percent
      ? `${percent.name} looks like percentages written as text; should I read it as numbers?`
      : 'Is the first column the one to plot on x?',
  ].join(' ');
}

// ---------------------------------------------------------------- routes

const LIBRARY_META = {
  matplotlib: { id: 'matplotlib', name: 'matplotlib', language: 'python' },
  seaborn: { id: 'seaborn', name: 'seaborn', language: 'python' },
};

function implementation(specId, library) {
  const base = `${BASE}/mock/plots/${specId}/${library}`;
  return {
    library_id: library,
    library_name: library,
    language: 'python',
    preview_url: `${base}/plot-light.png`,
    preview_url_light: `${base}/plot-light.png`,
    preview_url_dark: `${base}/plot-dark.png`,
    quality_score: 92,
    code: `# ${specId} (${library}) — catalogue code served by the mock\nimport matplotlib.pyplot as plt\n`,
    library_version: '3.10.0',
  };
}

async function route(req, res) {
  const url = new URL(req.url, BASE);
  const path = url.pathname;
  const method = req.method;
  cors(req, res);
  if (method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Catalogue routes the layout and the plot page call.
  if (method === 'GET' && path === '/health') return json(res, 200, { status: 'ok' });
  if (method === 'GET' && path === '/specs')
    return json(
      res,
      200,
      Object.values(SPECS).map(({ id, title, description }) => ({ id, title, description }))
    );
  if (method === 'GET' && path === '/libraries')
    return json(res, 200, { libraries: Object.values(LIBRARY_META) });
  if (method === 'GET' && path === '/languages')
    return json(res, 200, { languages: [{ id: 'python', name: 'Python' }] });
  if (method === 'GET' && path === '/stats')
    return json(res, 200, { specs: 2, plots: 4, libraries: 2 });
  const specMatch = path.match(/^\/specs\/([a-z0-9-]+)$/);
  if (method === 'GET' && specMatch && SPECS[specMatch[1]]) {
    const spec = SPECS[specMatch[1]];
    return json(res, 200, {
      id: spec.id,
      title: spec.title,
      description: spec.description,
      data: spec.data,
      notes: spec.notes,
      tags: { plot_type: [spec.id.split('-')[0]] },
      implementations: AGENT_LIBRARIES.map(library => implementation(spec.id, library)),
    });
  }
  const codeMatch = path.match(/^\/specs\/([a-z0-9-]+)\/([a-z0-9]+)\/code$/);
  if (method === 'GET' && codeMatch)
    return json(res, 200, { code: implementation(codeMatch[1], codeMatch[2]).code });
  if (method === 'GET' && path.startsWith('/insights/related/'))
    return json(res, 200, { related: [] });
  if (method === 'GET' && path === '/plots/filter')
    return json(res, 200, { images: [], total: 0, counts: {}, globalCounts: {} });
  const imageMatch = path.match(/^\/mock\/plots\/.+\/plot-(light|dark)/);
  if (method === 'GET' && imageMatch) {
    res.writeHead(200, { 'Content-Type': 'image/png', 'Cache-Control': 'no-store' });
    res.end(cataloguePng(imageMatch[1]));
    return;
  }

  // The recorded quick feedback of every open session, per result version (a mock-only route).
  if (method === 'GET' && path === '/mock/feedback')
    return json(
      res,
      200,
      Object.fromEntries([...sessions].map(([sid, session]) => [sid, session.feedback]))
    );

  if (!path.startsWith('/debug/agent')) return fail(res, 404, 'not_found');

  // The BFF's CSRF guard.
  if (method !== 'GET' && req.headers['x-anyplot-client'] !== 'agent-chat/1')
    return fail(res, 403, 'client_header_required');
  const hasBody = req.headers['content-length'] && req.headers['content-length'] !== '0';
  if (hasBody && !String(req.headers['content-type'] || '').startsWith('application/json'))
    return fail(res, 403, 'json_required');

  const ref = randomUUID();
  const sub = path.slice('/debug/agent'.length);
  let body = null;
  try {
    body = method === 'GET' ? null : await readBody(req);
  } catch {
    return fail(res, 422, 'invalid', ref);
  }

  if (method === 'GET' && sub === '/status')
    return json(
      res,
      200,
      {
        libraries: AGENT_LIBRARIES,
        model: 'claude-haiku-5-5',
        location: 'eu',
        provider: 'anthropic-vertex',
        version: 'mock',
        waiting: waitingTurns,
        in_flight: runsInFlight,
        enabled: true,
      },
      ref
    );
  if (method === 'GET' && sub === '/eligibility') {
    const library = url.searchParams.get('library');
    const eligible = !!SPECS[url.searchParams.get('spec')] && AGENT_LIBRARIES.includes(library);
    return json(
      res,
      200,
      {
        eligible,
        status: eligible ? 'coupled' : 'blocked',
        reasons: eligible ? [] : ['library-disabled'],
      },
      ref
    );
  }
  if (method === 'POST' && sub === '/sessions') {
    if (!SPECS[body?.spec_id]) return fail(res, 404, 'not_found', ref);
    if (!AGENT_LIBRARIES.includes(body.library)) return fail(res, 422, 'not_eligible', ref);
    const sid = randomBytes(18).toString('base64url');
    sessions.set(sid, {
      specId: body.spec_id,
      library: body.library,
      dataset: null,
      bindings: [],
      complete: false,
      // Step 1's confirmation of the dataset and its bindings.
      confirmed: false,
      // The dataset versions: the paste is 1, each data change one more, undo one less.
      history: [],
      version: 1,
      changed: null,
      versions: [],
      // `{role, text}` per user message or action and per assistant reply, for the bundle.
      transcript: [],
      // The quick feedback per result version: the latest submission, with its case id.
      feedback: {},
      active: false,
      cancelled: false,
    });
    return json(
      res,
      200,
      { session_id: sid, eligibility: { eligible: true, status: 'coupled', reasons: [] } },
      ref
    );
  }

  const sessionMatch = sub.match(/^\/sessions\/([A-Za-z0-9_-]+)(\/.*)?$/);
  if (!sessionMatch) return fail(res, 404, 'not_found', ref);
  const [, sid, rest = ''] = sessionMatch;
  const session = sessions.get(sid);
  if (!session) return fail(res, 404, 'session_expired', ref);

  if (method === 'DELETE' && rest === '') {
    sessions.delete(sid);
    res.writeHead(204, { 'X-Request-Id': ref });
    res.end();
    return;
  }
  if (method === 'POST' && rest === '/library') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (!AGENT_LIBRARIES.includes(body?.library)) return fail(res, 422, 'not_eligible', ref);
    session.library = body.library;
    return json(
      res,
      200,
      { session_id: sid, eligibility: { eligible: true, status: 'coupled', reasons: [] } },
      ref
    );
  }
  if (method === 'POST' && rest === '/dataset') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    const text = typeof body?.text === 'string' ? body.text : '';
    if (Buffer.byteLength(text, 'utf8') > MAX_DATASET_BYTES) return fail(res, 413, 'too_long', ref);
    if (/ignore previous/i.test(text)) return fail(res, 403, 'data_refused', ref);
    await sleep(400);
    let parsed;
    try {
      parsed = parseDataset(text);
    } catch {
      // A formula ("zeichne sin(x) von -pi bis pi") is never transcribed: a model would compute
      // its rows. The service answers 422 formula; the page points to the chat's generate_data.
      if (looksLikeFormula(text)) return fail(res, 422, 'formula', ref);
      // Free text (no delimiter, "Hund 7 Katze 3 und Vogel 4"): the real service has a model read
      // it into a table and answers it unstored, for the user to confirm. The mock pairs each
      // word with the number after it.
      const transcribed = body?.confirmed ? null : transcribeFreeText(text);
      if (!transcribed) return fail(res, 422, 'unparseable', ref);
      await sleep(900);
      return json(res, 200, transcribed, ref);
    }
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false; // a new dataset is unchecked
    session.history = []; // a paste starts over at version 1
    session.version = 1;
    return json(res, 200, { ...datasetPayload(session), roles: SPECS[session.specId].roles }, ref);
  }
  if (method === 'POST' && rest === '/dataset/undo') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    const previous = session.history.pop();
    if (!previous) return fail(res, 422, 'nothing_to_undo', ref);
    session.dataset = previous.dataset;
    session.bindings = carryBindings(session, session.bindings, previous.dataset.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    session.confirmed = false; // restored, but confirmed again by the user
    session.version -= 1;
    return json(res, 200, { ...datasetPayload(session), roles: SPECS[session.specId].roles }, ref);
  }
  if (method === 'PUT' && rest === '/bindings') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (!session.dataset) return fail(res, 422, 'no_dataset', ref);
    const wanted = (Array.isArray(body) ? body : []).filter(b => b && b.column);
    const { errors, ...checked } = checkBindings(session, wanted);
    // The BFF passes the check's lines of a refused set on (at most 20).
    if (errors.length)
      return json(res, 422, { detail: 'invalid', ref, errors: errors.slice(0, 20) }, ref);
    session.bindings = checked.bindings;
    session.complete = checked.complete;
    session.confirmed = false; // the confirmation covered the previous set
    return json(res, 200, checked, ref);
  }
  if (method === 'POST' && rest === '/dataset/confirm') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (!session.dataset) return fail(res, 422, 'no_dataset', ref);
    session.confirmed = true;
    return json(
      res,
      200,
      {
        confirmed: true,
        rows: session.dataset.profile.rows,
        columns: session.dataset.profile.columns.length,
      },
      ref
    );
  }
  if (method === 'POST' && rest === '/messages') {
    if (session.active) return fail(res, 409, 'run_active', ref);
    if (typeof body?.text === 'string' && body.text.length > 2000)
      return fail(res, 413, 'too_long', ref);
    return streamTurn(req, res, session, body ?? {}, ref);
  }
  if (method === 'POST' && rest === '/cancel') {
    session.cancelled = true;
    res.writeHead(204, { 'X-Request-Id': ref });
    res.end();
    return;
  }
  const renderMatch = rest.match(/^\/versions\/(\d+)\/render$/);
  if (method === 'POST' && renderMatch) {
    if (session.active) return fail(res, 409, 'run_active', ref);
    const number = Number(renderMatch[1]);
    const version = number
      ? session.versions.find(v => v.number === number)
      : session.versions[session.versions.length - 1];
    if (!version) return fail(res, 404, 'not_found', ref);
    const theme = body?.theme === 'dark' ? 'dark' : 'light';
    if (!version.pngs[theme]) {
      await sleep(1500);
      renderVersion(session, version, theme);
    }
    const artifacts = ['light', 'dark']
      .filter(t => version.pngs[t])
      .map(t => `plot-${t}.png`)
      .concat(['plot.py', 'data.csv']);
    return json(res, 200, { status: 'ok', reason: null, artifacts }, ref);
  }
  const artifactMatch = rest.match(/^\/artifacts\/([a-z.-]+)$/);
  if (method === 'GET' && artifactMatch) {
    const number = Number(url.searchParams.get('v') || 0);
    const version = number
      ? session.versions.find(v => v.number === number)
      : session.versions[session.versions.length - 1];
    if (!version) return fail(res, 404, 'not_found', ref);
    const name = artifactMatch[1];
    const headers = {
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Request-Id': ref,
    };
    if (name === 'plot.py') {
      res.writeHead(200, { ...headers, 'Content-Type': 'text/x-python; charset=utf-8' });
      res.end(plotPy(session, version));
      return;
    }
    if (name === 'data.csv') {
      res.writeHead(200, { ...headers, 'Content-Type': 'text/csv; charset=utf-8' });
      res.end(csvText(version));
      return;
    }
    const pngTheme = { 'plot-light.png': 'light', 'plot-dark.png': 'dark' }[name];
    if (!pngTheme || !version.pngs[pngTheme]) return fail(res, 404, 'not_found', ref);
    res.writeHead(200, { ...headers, 'Content-Type': 'image/png' });
    res.end(version.pngs[pngTheme]);
    return;
  }
  if (method === 'GET' && rest === '/bundle') {
    // `.save()`: the feedback case, as the BFF relays the agents service's bundle.
    const flag = (url.searchParams.get('include_data') ?? 'false').toLowerCase();
    const includeData = ['true', '1', 'yes', 'on'].includes(flag);
    const rawVersion = url.searchParams.get('version');
    const number = rawVersion === null ? 0 : Number(rawVersion);
    if (
      (!includeData && !['false', '0', 'no', 'off'].includes(flag)) ||
      !Number.isInteger(number) ||
      number < 0 ||
      number > 999
    )
      return fail(res, 422, 'invalid', ref);
    const versions = number ? session.versions.filter(v => v.number === number) : session.versions;
    if (number && versions.length === 0) return fail(res, 404, 'not_found', ref);
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Content-Disposition': `attachment; filename="anyplot-session-${sid.slice(0, 8)}.json"`,
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Request-Id': ref,
    });
    res.end(JSON.stringify(sessionBundle(session, versions, includeData)));
    return;
  }
  if (method === 'POST' && rest === '/feedback') {
    // The quick feedback: the BFF stores the version's case in the private bucket.
    const problem = feedbackProblem(body);
    if (problem) return json(res, 422, { detail: [{ msg: problem }] }, ref);
    const version = session.versions.find(v => v.number === body.result_version);
    if (!version) return fail(res, 404, 'not_found', ref);
    const message = typeof body.message === 'string' ? body.message.trim() || null : null;
    await sleep(600);
    if (message?.includes('502')) return fail(res, 502, 'storage', ref);
    const caseId = `${new Date()
      .toISOString()
      .replace(/[-:]/g, '')
      .replace(/\.\d+Z$/, 'Z')}-${randomBytes(4).toString('hex')}`;
    const stored = [
      ...['light', 'dark'].filter(theme => version.pngs[theme]).map(theme => `plot-${theme}.png`),
      'plot.py',
      ...(body.include_data ? ['data.csv'] : []),
      'manifest.json',
    ];
    session.feedback[version.number] = {
      case_id: caseId,
      reaction: body.reaction,
      message,
      include_data: body.include_data,
    };
    return json(res, 201, { case_id: caseId, stored }, ref);
  }
  return fail(res, 404, 'not_found', ref);
}

const FEEDBACK_REACTIONS = ['thumbs_up', 'thumbs_down', 'bug', 'idea'];
const FEEDBACK_FIELDS = new Set(['reaction', 'message', 'include_data', 'result_version']);

/** Why the BFF would refuse a feedback body with a 422, or `null` when it takes it. */
function feedbackProblem(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'a JSON object is required';
  const extra = Object.keys(body).filter(key => !FEEDBACK_FIELDS.has(key));
  if (extra.length) return `unknown field ${extra[0]}`;
  if (!FEEDBACK_REACTIONS.includes(body.reaction)) return 'reaction must be one of the set';
  if (body.message != null && typeof body.message !== 'string') return 'message must be text';
  if (typeof body.message === 'string' && body.message.trim().length > 500)
    return 'message must be 500 characters or fewer';
  if (typeof body.include_data !== 'boolean') return 'include_data is required';
  const version = body.result_version;
  if (!Number.isInteger(version) || version < 1 || version > 999)
    return 'result_version must be 1 to 999';
  return null;
}

/**
 * The agents service's feedback case (`GET /v1/sessions/{sid}/bundle`) from the mock's
 * state: the same top-level keys, the PNGs the artifact route serves as base64, and the
 * mock's one code form standing in for the working, run and exported code.
 */
function sessionBundle(session, versions, includeData) {
  return {
    session: { spec_id: session.specId, library: session.library, locale: 'en' },
    snapshot: { spec_id: session.specId, library_version: '3.10.0' },
    transcript: session.transcript,
    versions: versions.map(version => {
      const code = plotPy(session, version);
      return {
        number: version.number,
        title: SPECS[session.specId].title,
        working: code,
        run_form: code,
        plot_py: code,
        plan: null,
        result: version.result,
        theme: version.theme,
        themes: Object.fromEntries(
          Object.keys(version.pngs).map(theme => [theme, { status: 'ok', reason: null }])
        ),
        images: Object.fromEntries(
          Object.entries(version.pngs).map(([theme, png]) => [theme, png.toString('base64')])
        ),
        data_csv: includeData ? csvText(version) : null,
      };
    }),
    profile: session.dataset ? session.dataset.profile : null,
    bindings: session.bindings,
    config: {
      provider: 'mock',
      model: 'claude-haiku-5-5',
      judge_model: 'claude-haiku-5-5',
      location: 'eu',
      adk_version: 'mock',
      service_version: 'mock',
      prompt_hashes: {},
    },
  };
}

http
  .createServer((req, res) => {
    route(req, res).catch(err => {
      console.error(err);
      if (!res.headersSent) fail(res, 500, 'internal');
      else res.end();
    });
  })
  // Loopback only: the mock echoes pasted data back as images, so it must not
  // be reachable from the local network.
  .listen(PORT, '127.0.0.1', () => {
    console.log(
      `agent BFF mock on ${BASE} (step ${STEP_MS} ms, queue ${QUEUE_START} x ${QUEUE_MS} ms)`
    );
  });
