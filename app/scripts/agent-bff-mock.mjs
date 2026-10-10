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
 * (agents/anyplot/render/backends/fake.py); no code runs.
 *
 * Scripted behaviour of a chat message:
 * - contains "weather" or "joke": the fixed out-of-scope refusal;
 * - contains "busy": `error {code: capacity}`;
 * - ends with "?": a reply only, no pipeline run;
 * - anything else: a refinement with a repair round, shipped as
 *   `needs_attention`; "dark" in the text renders the dark theme.
 * Pasted data containing "ignore previous" answers `403 data_refused`.
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

/** A plot-like PNG: axes, a light grid, and either a scatter of each series in `series` or bars. */
function drawPlot(theme, series, { width = 1600, height = 900, firstColor = 0 } = {}) {
  const { bg, ink, grid } = THEMES[theme];
  const canvas = new Canvas(width, height, bg);
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
    const numeric = present.length > 0 && present.every(cell => /^-?\d+(\.\d+)?$/.test(cell));
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
    return {
      name,
      dtype,
      missing,
      unique: counts.size,
      min: numeric ? Math.min(...values) : (present[0] ?? null),
      max: numeric ? Math.max(...values) : (present[present.length - 1] ?? null),
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

function csvText(session) {
  const quote = cell => (/[",\n]/.test(cell) ? `"${cell.replace(/"/g, '""')}"` : cell);
  return [session.dataset.header, ...session.dataset.rows]
    .map(row => row.map(quote).join(','))
    .join('\n')
    .concat('\n');
}

const columnOf = (session, name) => session.bindings.find(b => b.role === name)?.column;
/** The bound y columns: `y` of scatter-basic, or every member `y1, y2, ...` of line-multi. */
const yColumns = session => session.bindings.filter(b => /^y\d*$/.test(b.role)).map(b => b.column);

/** One point list per y column; a non-numeric x (a date) plots by row order. */
function points(session) {
  const names = session.dataset.header;
  const x = names.indexOf(columnOf(session, 'x'));
  if (x < 0) return null;
  return yColumns(session).map(column => {
    const y = names.indexOf(column);
    return session.dataset.rows
      .map((row, index) => [
        Number.isFinite(Number(row[x])) ? Number(row[x]) : index,
        Number(row[y]),
      ])
      .filter(([a, b]) => Number.isFinite(a) && Number.isFinite(b));
  });
}

function plotPy(session, version) {
  const x = columnOf(session, 'x') ?? 'x';
  const y = yColumns(session)[0] ?? 'y';
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
  version.pngs[theme] = drawPlot(theme, points(session), {
    firstColor: version.number > 1 ? 2 : 0,
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
    if (!closed) res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };
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
      if (text.trim().endsWith('?')) {
        await sleep(STEP_MS * 2);
        send('message', {
          text: 'The x axis uses the column you bound to x; the marker size is the s= argument of ax.scatter, line 18 of plot.py.',
        });
        return;
      }
      if (!session.dataset || !session.complete) {
        await sleep(STEP_MS);
        send('plot', {
          status: 'not_ready',
          reason: session.dataset ? 'incomplete_bindings' : 'no_dataset',
          attempts: 0,
          artifacts: [],
          changes: [],
          residual_defects: [],
        });
        send('message', { text: 'Paste your data and bind the required roles first.' });
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
        pngs: {},
      };
      renderVersion(session, version, theme);
      session.versions.push(version);
      const x = columnOf(session, 'x');
      const y = yColumns(session).join(', ');
      send('plot', {
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
      });
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
    send('done', { llm_calls: 4, tokens: 18734 });
    res.end();
  }
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
      versions: [],
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
      return fail(res, 422, 'unparseable', ref);
    }
    session.dataset = parsed;
    session.bindings = defaultBindings(session, parsed.profile);
    session.complete = checkBindings(session, session.bindings).complete;
    return json(
      res,
      200,
      {
        preview: parsed.preview,
        profile: parsed.profile,
        bindings: session.bindings,
        warnings: parsed.warnings,
        roles: SPECS[session.specId].roles,
      },
      ref
    );
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
    return json(res, 200, checked, ref);
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
      res.end(csvText(session));
      return;
    }
    const pngTheme = { 'plot-light.png': 'light', 'plot-dark.png': 'dark' }[name];
    if (!pngTheme || !version.pngs[pngTheme]) return fail(res, 404, 'not_found', ref);
    res.writeHead(200, { ...headers, 'Content-Type': 'image/png' });
    res.end(version.pngs[pngTheme]);
    return;
  }
  return fail(res, 404, 'not_found', ref);
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
