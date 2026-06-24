// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 82/100 | Created: 2026-06-24
//# anyplot-orientation: square

// Chart.js is loaded by the harness; QR code generation requires a matrix
// encoder that Chart.js core types cannot provide. We implement a compact
// ISO 18004 encoder (Byte mode, Version 2, EC level M) in pure JS and render
// with Canvas 2D API, which satisfies the harness <canvas> requirement.

const t = window.ANYPLOT_TOKENS;

// ── GF(256) for Reed-Solomon (primitive poly x^8+x^4+x^3+x^2+1 = 0x11D) ──
const GF_EXP = new Uint8Array(512);
const GF_LOG = new Uint8Array(256);
(function () {
  let x = 1;
  for (let i = 0; i < 255; i++) {
    GF_EXP[i] = x;
    GF_LOG[x] = i;
    x = x < 128 ? x * 2 : ((x * 2) ^ 0x11d) & 0xff;
  }
  for (let i = 255; i < 512; i++) GF_EXP[i] = GF_EXP[i - 255];
}());

function gfMul(a, b) {
  return a && b ? GF_EXP[GF_LOG[a] + GF_LOG[b]] : 0;
}

// Reed-Solomon: compute nEC error-correction codewords
function rsEncode(data, nEC) {
  // Generator poly g(x) = ∏(x + α^i) for i = 0..nEC-1
  let g = [1];
  for (let i = 0; i < nEC; i++) {
    const ng = new Array(g.length + 1).fill(0);
    for (let j = 0; j < g.length; j++) {
      ng[j] ^= g[j];
      ng[j + 1] ^= gfMul(g[j], GF_EXP[i]);
    }
    g = ng;
  }
  // Polynomial long division: remainder of (data × x^nEC) / g
  const rem = [...data, ...new Array(nEC).fill(0)];
  for (let i = 0; i < data.length; i++) {
    const c = rem[i];
    if (c === 0) continue;
    for (let j = 1; j <= nEC; j++) rem[i + j] ^= gfMul(c, g[j]);
  }
  return rem.slice(data.length);
}

// ── QR data encoding: Byte mode, Version 2, EC level M ───────────────────
// Version 2 M capacity: 22 data codewords, 16 EC codewords, 1 block.
function encodeData(text) {
  const bytes = Array.from(new TextEncoder().encode(text));
  const bits = [];
  const push = (v, n) => { for (let i = n - 1; i >= 0; i--) bits.push((v >> i) & 1); };
  push(4, 4);             // Byte mode indicator
  push(bytes.length, 8);  // Character count (8-bit field for versions 1–9)
  for (const b of bytes) push(b, 8);
  push(0, 4);             // Terminator
  while (bits.length % 8) bits.push(0); // Byte-align
  const cw = [];
  for (let i = 0; i < bits.length; i += 8)
    cw.push(bits.slice(i, i + 8).reduce((acc, b, j) => acc | (b << (7 - j)), 0));
  for (let p = 0; cw.length < 22; p++) cw.push(p % 2 === 0 ? 0xec : 0x11);
  return cw;
}

// ── Format information: BCH(15,5) generator 0x537, EC level M (00) ────────
function formatInfo(maskIdx) {
  // EC level M = 00, so 5-bit data word = (0b00 << 3) | maskIdx = maskIdx
  const data5 = maskIdx;
  let rem = data5 << 10;
  // BCH(15,5) with generator x^10+x^8+x^5+x^4+x^2+x+1 = 0x537
  for (let i = 14; i >= 10; i--)
    if ((rem >> i) & 1) rem ^= 0x537 << (i - 10);
  return ((data5 << 10) | (rem & 0x3ff)) ^ 0x5412; // XOR mask 101010000010010
}

// ── Build 25×25 QR matrix (ISO 18004, Version 2) ─────────────────────────
function buildMatrix(text, maskIdx) {
  const N = 25;
  // mat[r][c]: -1 = unset data region, 0 = light module, 1 = dark module
  const mat = Array.from({ length: N }, () => new Int8Array(N).fill(-1));
  const set = (r, c, v) => { mat[r][c] = v; };

  // Finder pattern (7×7): outer ring + 3×3 core are dark
  function placeFinder(r0, c0) {
    for (let r = 0; r < 7; r++)
      for (let c = 0; c < 7; c++) {
        const v = (r === 0 || r === 6 || c === 0 || c === 6 ||
                   (r >= 2 && r <= 4 && c >= 2 && c <= 4)) ? 1 : 0;
        set(r0 + r, c0 + c, v);
      }
  }
  placeFinder(0, 0);       // top-left
  placeFinder(0, N - 7);   // top-right
  placeFinder(N - 7, 0);   // bottom-left

  // Separators (1-module light border outside each finder)
  for (let i = 0; i < 8; i++) {
    if (mat[7][i] < 0) set(7, i, 0);          // TL bottom
    if (mat[i][7] < 0) set(i, 7, 0);          // TL right
    if (mat[7][N - 1 - i] < 0) set(7, N - 1 - i, 0); // TR bottom
    if (mat[i][N - 8] < 0) set(i, N - 8, 0);  // TR left (col 17)
    if (mat[N - 8][i] < 0) set(N - 8, i, 0);  // BL top (row 17)
    if (mat[N - 1 - i][7] < 0) set(N - 1 - i, 7, 0); // BL right
  }

  // Timing patterns (row 6 and col 6, alternating dark/light)
  for (let i = 8; i <= N - 9; i++) {
    const v = i % 2 === 0 ? 1 : 0;
    if (mat[6][i] < 0) set(6, i, v);
    if (mat[i][6] < 0) set(i, 6, v);
  }

  // Alignment pattern (Version 2: single pattern centered at module 18,18)
  for (let dr = -2; dr <= 2; dr++)
    for (let dc = -2; dc <= 2; dc++)
      if (mat[18 + dr][18 + dc] < 0) {
        const v = (Math.abs(dr) === 2 || Math.abs(dc) === 2 ||
                   (dr === 0 && dc === 0)) ? 1 : 0;
        set(18 + dr, 18 + dc, v);
      }

  // Dark module (always dark, ISO 18004 §7.9.1)
  set(4 * 2 + 9, 8, 1); // row 17, col 8

  // Reserve format info areas (will be overwritten after data placement)
  for (let i = 0; i <= 8; i++) {
    if (mat[8][i] < 0) set(8, i, 0); // row 8, TL side (cols 0-8)
    if (mat[i][8] < 0) set(i, 8, 0); // col 8, TL side (rows 0-8)
  }
  for (let i = 0; i < 8; i++) {
    if (mat[8][N - 1 - i] < 0) set(8, N - 1 - i, 0); // row 8, TR side
  }
  for (let i = 0; i < 7; i++) {
    if (mat[N - 1 - i][8] < 0) set(N - 1 - i, 8, 0); // col 8, BL side
  }

  // ── Data codewords → bit stream ─────────────────────────────────────────
  const dataCW = encodeData(text);
  const ecCW = rsEncode(dataCW, 16);
  const allBits = [];
  for (const cw of [...dataCW, ...ecCW])
    for (let i = 7; i >= 0; i--) allBits.push((cw >> i) & 1);

  // ── Zigzag placement (right to left, alternating up/down) ────────────────
  // Mask 0: invert bit when (row + col) % 2 === 0
  const MASKS = [
    (r, c) => (r + c) % 2 === 0,
    (r, c) => r % 2 === 0,
    (r, c) => c % 3 === 0,
    (r, c) => (r + c) % 3 === 0,
    (r, c) => (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0,
    (r, c) => (r * c) % 2 + (r * c) % 3 === 0,
    (r, c) => ((r * c) % 2 + (r * c) % 3) % 2 === 0,
    (r, c) => ((r + c) % 2 + (r * c) % 3) % 2 === 0,
  ];
  const maskFn = MASKS[maskIdx];
  let bitIdx = 0;
  let upward = true;
  for (let col = N - 1; col > 0; col -= 2) {
    if (col === 6) col--; // skip timing column 6
    const rows = upward
      ? Array.from({ length: N }, (_, i) => N - 1 - i)
      : Array.from({ length: N }, (_, i) => i);
    for (const r of rows) {
      for (const dc of [0, -1]) {
        const c = col + dc;
        if (c < 0 || mat[r][c] !== -1) continue; // out-of-bounds or function module
        const bit = bitIdx < allBits.length ? allBits[bitIdx++] : 0;
        set(r, c, maskFn(r, c) ? bit ^ 1 : bit);
      }
    }
    upward = !upward;
  }

  // ── Format information placement ─────────────────────────────────────────
  const fmt = formatInfo(maskIdx);
  // Copy 1 positions (around TL finder), bits 14 down to 0
  const copy1 = [
    [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8],
    [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
  ];
  for (let i = 0; i < 15; i++) set(copy1[i][0], copy1[i][1], (fmt >> (14 - i)) & 1);
  // Copy 2 positions (around TR/BL finders), bits 0 up to 14
  const copy2 = [
    [8, N - 1], [8, N - 2], [8, N - 3], [8, N - 4],
    [8, N - 5], [8, N - 6], [8, N - 7], [8, N - 8],
    [N - 7, 8], [N - 6, 8], [N - 5, 8], [N - 4, 8],
    [N - 3, 8], [N - 2, 8], [N - 1, 8],
  ];
  for (let i = 0; i < 15; i++) set(copy2[i][0], copy2[i][1], (fmt >> i) & 1);

  return mat;
}

// ── Canvas rendering ───────────────────────────────────────────────────────
const QR_TEXT = "https://anyplot.ai";
const QR_N = 25;
const MASK_IDX = 0; // mask pattern 0: (row+col) % 2 === 0
const matrix = buildMatrix(QR_TEXT, MASK_IDX);

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);
const ctx = canvas.getContext("2d");

// Device pixel ratio for sharp rendering at deviceScaleFactor=2
const dpr = window.devicePixelRatio || 1;
const { width, height } = window.ANYPLOT_SIZE; // 1200×1200 CSS px for square
canvas.style.width = width + "px";
canvas.style.height = height + "px";
canvas.width = width * dpr;
canvas.height = height * dpr;
ctx.scale(dpr, dpr);

// Page background
ctx.fillStyle = t.pageBg;
ctx.fillRect(0, 0, width, height);

// Sizing: centre the QR code with quiet zone, reserve space for labels
const TITLE_H = 70;
const LABEL_H = 60;
const PAD = 40;
const availH = height - TITLE_H - LABEL_H - PAD * 2;
const availW = width - PAD * 2;
const QUIET = 4; // 4 quiet-zone modules on each side per spec
const totalModules = QR_N + QUIET * 2;
const cellSize = Math.floor(Math.min(availW, availH) / totalModules);
const qrPx = totalModules * cellSize; // pixel size including quiet zone
const qrLeft = Math.round((width - qrPx) / 2);
const qrTop = TITLE_H + Math.round((availH - qrPx) / 2) + PAD;

// QR quiet zone + background (high-contrast white for scannability)
const QR_BG = "#FFFFFF";
const QR_FG = "#000000";
ctx.fillStyle = QR_BG;
ctx.fillRect(qrLeft, qrTop, qrPx, qrPx);

// Draw modules
for (let r = 0; r < QR_N; r++) {
  for (let c = 0; c < QR_N; c++) {
    if (matrix[r][c] === 1) {
      ctx.fillStyle = QR_FG;
      ctx.fillRect(
        qrLeft + (QUIET + c) * cellSize,
        qrTop + (QUIET + r) * cellSize,
        cellSize,
        cellSize
      );
    }
  }
}

// Thin border around QR code area
ctx.strokeStyle = t.grid;
ctx.lineWidth = 1;
ctx.strokeRect(qrLeft + 0.5, qrTop + 0.5, qrPx - 1, qrPx - 1);

// Title
const title = "qrcode-basic · javascript · chartjs · anyplot.ai";
ctx.textAlign = "center";
ctx.textBaseline = "middle";
ctx.fillStyle = t.ink;
ctx.font = `600 22px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
ctx.fillText(title, width / 2, TITLE_H / 2);

// URL label below QR
ctx.fillStyle = t.inkSoft;
ctx.font = `16px "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace`;
ctx.fillText(QR_TEXT, width / 2, qrTop + qrPx + LABEL_H / 2);

// EC level and version note
ctx.fillStyle = t.inkSoft;
ctx.font = `14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
ctx.fillText("Version 2 · Error Correction M (15%)", width / 2, qrTop + qrPx + LABEL_H / 2 + 24);
