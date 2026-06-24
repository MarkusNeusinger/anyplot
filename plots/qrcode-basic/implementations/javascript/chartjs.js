// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 82/100 | Created: 2026-06-24
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// ── GF(256) arithmetic for Reed-Solomon (primitive poly 0x11D) ───────────────
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

// Compute nEC Reed-Solomon error-correction codewords
function rsEncode(data, nEC) {
  let g = [1];
  for (let i = 0; i < nEC; i++) {
    const ng = new Array(g.length + 1).fill(0);
    for (let j = 0; j < g.length; j++) {
      ng[j] ^= g[j];
      ng[j + 1] ^= gfMul(g[j], GF_EXP[i]);
    }
    g = ng;
  }
  const rem = [...data, ...new Array(nEC).fill(0)];
  for (let i = 0; i < data.length; i++) {
    const c = rem[i];
    if (c === 0) continue;
    for (let j = 1; j <= nEC; j++) rem[i + j] ^= gfMul(c, g[j]);
  }
  return rem.slice(data.length);
}

// Byte mode, Version 2 M: 22 data codewords, 16 EC codewords
function encodeData(text) {
  const bytes = Array.from(new TextEncoder().encode(text));
  const bits = [];
  const push = (v, n) => { for (let i = n - 1; i >= 0; i--) bits.push((v >> i) & 1); };
  push(4, 4);            // Byte mode indicator
  push(bytes.length, 8); // Character count
  for (const b of bytes) push(b, 8);
  push(0, 4);            // Terminator
  while (bits.length % 8) bits.push(0);
  const cw = [];
  for (let i = 0; i < bits.length; i += 8)
    cw.push(bits.slice(i, i + 8).reduce((acc, b, j) => acc | (b << (7 - j)), 0));
  for (let p = 0; cw.length < 22; p++) cw.push(p % 2 === 0 ? 0xec : 0x11);
  return cw;
}

// BCH(15,5) format info, EC level M (00), XOR mask 0x5412
function formatInfo(maskIdx) {
  let rem = maskIdx << 10;
  for (let i = 14; i >= 10; i--)
    if ((rem >> i) & 1) rem ^= 0x537 << (i - 10);
  return ((maskIdx << 10) | (rem & 0x3ff)) ^ 0x5412;
}

// Build 25×25 QR matrix (ISO 18004 Version 2)
function buildMatrix(text, maskIdx) {
  const N = 25;
  const mat = Array.from({ length: N }, () => new Int8Array(N).fill(-1));
  const set = (r, c, v) => { mat[r][c] = v; };

  function placeFinder(r0, c0) {
    for (let r = 0; r < 7; r++)
      for (let c = 0; c < 7; c++) {
        const v = (r === 0 || r === 6 || c === 0 || c === 6 ||
                   (r >= 2 && r <= 4 && c >= 2 && c <= 4)) ? 1 : 0;
        set(r0 + r, c0 + c, v);
      }
  }
  placeFinder(0, 0);
  placeFinder(0, N - 7);
  placeFinder(N - 7, 0);

  for (let i = 0; i < 8; i++) {
    if (mat[7][i] < 0) set(7, i, 0);
    if (mat[i][7] < 0) set(i, 7, 0);
    if (mat[7][N - 1 - i] < 0) set(7, N - 1 - i, 0);
    if (mat[i][N - 8] < 0) set(i, N - 8, 0);
    if (mat[N - 8][i] < 0) set(N - 8, i, 0);
    if (mat[N - 1 - i][7] < 0) set(N - 1 - i, 7, 0);
  }

  for (let i = 8; i <= N - 9; i++) {
    const v = i % 2 === 0 ? 1 : 0;
    if (mat[6][i] < 0) set(6, i, v);
    if (mat[i][6] < 0) set(i, 6, v);
  }

  for (let dr = -2; dr <= 2; dr++)
    for (let dc = -2; dc <= 2; dc++)
      if (mat[18 + dr][18 + dc] < 0) {
        const v = (Math.abs(dr) === 2 || Math.abs(dc) === 2 ||
                   (dr === 0 && dc === 0)) ? 1 : 0;
        set(18 + dr, 18 + dc, v);
      }

  set(4 * 2 + 9, 8, 1); // dark module

  for (let i = 0; i <= 8; i++) {
    if (mat[8][i] < 0) set(8, i, 0);
    if (mat[i][8] < 0) set(i, 8, 0);
  }
  for (let i = 0; i < 8; i++) {
    if (mat[8][N - 1 - i] < 0) set(8, N - 1 - i, 0);
  }
  for (let i = 0; i < 7; i++) {
    if (mat[N - 1 - i][8] < 0) set(N - 1 - i, 8, 0);
  }

  const dataCW = encodeData(text);
  const ecCW = rsEncode(dataCW, 16);
  const allBits = [];
  for (const cw of [...dataCW, ...ecCW])
    for (let i = 7; i >= 0; i--) allBits.push((cw >> i) & 1);

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
    if (col === 6) col--;
    const rows = upward
      ? Array.from({ length: N }, (_, i) => N - 1 - i)
      : Array.from({ length: N }, (_, i) => i);
    for (const r of rows) {
      for (const dc of [0, -1]) {
        const c = col + dc;
        if (c < 0 || mat[r][c] !== -1) continue;
        const bit = bitIdx < allBits.length ? allBits[bitIdx++] : 0;
        set(r, c, maskFn(r, c) ? bit ^ 1 : bit);
      }
    }
    upward = !upward;
  }

  const fmt = formatInfo(maskIdx);
  const copy1 = [
    [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8],
    [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
  ];
  for (let i = 0; i < 15; i++) set(copy1[i][0], copy1[i][1], (fmt >> (14 - i)) & 1);
  const copy2 = [
    [8, N - 1], [8, N - 2], [8, N - 3], [8, N - 4],
    [8, N - 5], [8, N - 6], [8, N - 7], [8, N - 8],
    [N - 7, 8], [N - 6, 8], [N - 5, 8], [N - 4, 8],
    [N - 3, 8], [N - 2, 8], [N - 1, 8],
  ];
  for (let i = 0; i < 15; i++) set(copy2[i][0], copy2[i][1], (fmt >> i) & 1);

  return mat;
}

// ── Build QR matrix ───────────────────────────────────────────────────────────
const QR_TEXT = "https://anyplot.ai";
const QR_N = 25;
const MASK_IDX = 0; // mask pattern 0: (row+col) % 2 === 0
const matrix = buildMatrix(QR_TEXT, MASK_IDX);

// ── Chart.js plugin: renders QR code inside the chart canvas ─────────────────
const qrPlugin = {
  id: 'qrcode',
  beforeDraw(chart) {
    // Fill page background before Chart.js draws anything
    chart.ctx.fillStyle = t.pageBg;
    chart.ctx.fillRect(0, 0, chart.width, chart.height);
  },
  afterDraw(chart) {
    const ctx = chart.ctx;
    const ca = chart.chartArea;
    const caW = ca.right - ca.left;
    const caH = ca.bottom - ca.top;

    const QUIET = 4;
    const totalModules = QR_N + QUIET * 2; // 33 modules (incl. quiet zone)
    const PAD = 16;
    const LABEL_H = 72; // vertical space for URL + version note below QR

    const availForQR = Math.min(caW - PAD * 2, caH - LABEL_H - PAD);
    const cellSize = Math.floor(availForQR / totalModules);
    const qrPx = totalModules * cellSize;
    const qrLeft = ca.left + Math.round((caW - qrPx) / 2);
    const qrTop = ca.top + PAD;

    // White card required for QR scannability
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(qrLeft, qrTop, qrPx, qrPx);

    // QR modules: black on white
    ctx.fillStyle = "#000000";
    for (let r = 0; r < QR_N; r++) {
      for (let c = 0; c < QR_N; c++) {
        if (matrix[r][c] === 1) {
          ctx.fillRect(
            qrLeft + (QUIET + c) * cellSize,
            qrTop + (QUIET + r) * cellSize,
            cellSize,
            cellSize
          );
        }
      }
    }

    // Brand accent: thin #009E73 border framing the QR card
    const bp = 5;
    ctx.strokeStyle = t.palette[0]; // #009E73
    ctx.lineWidth = 3;
    ctx.strokeRect(qrLeft - bp + 0.5, qrTop - bp + 0.5, qrPx + bp * 2 - 1, qrPx + bp * 2 - 1);

    // URL label below QR
    const centerX = ca.left + caW / 2;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = t.inkSoft;
    ctx.font = `16px "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace`;
    ctx.fillText(QR_TEXT, centerX, qrTop + qrPx + 30);

    // Version + EC level note
    ctx.font = `14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillText("Version 2 · Error Correction M (15%)", centerX, qrTop + qrPx + 56);
  }
};

// ── Mount canvas and instantiate Chart.js ─────────────────────────────────────
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
  type: 'scatter',
  data: { datasets: [] },
  plugins: [qrPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { bottom: 20 }
    },
    plugins: {
      title: {
        display: true,
        text: "qrcode-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: '600' },
        padding: { top: 16, bottom: 12 }
      },
      legend: { display: false },
    },
    scales: {
      x: { display: false },
      y: { display: false },
    },
  },
});
