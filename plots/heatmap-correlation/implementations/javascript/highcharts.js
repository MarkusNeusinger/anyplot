// anyplot.ai
// heatmap-correlation: Correlation Matrix Heatmap
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-18
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: correlation matrix across outdoor air-quality sensor readings ---
// The core Highcharts bundle has no heatmap/colorAxis-mapping module loaded,
// so the grid is drawn cell-by-cell with the SVG renderer instead.
const LABELS = ['Temperature', 'Humidity', 'CO₂ Level', 'PM2.5', 'Noise Level', 'Wind Speed'];
const N = LABELS.length;

// Fixed chart geometry (square canvas, harness-guaranteed 1200x1200 CSS px) —
// a single source of truth for both the chart margin and the scatter-marker
// radius below, so the invisible hover layer lines up with the drawn grid
// without needing a runtime resync.
const CHART_MARGIN = [100, 60, 145, 185]; // [top, right, bottom, left]
const CELL_W = (window.ANYPLOT_SIZE.width - CHART_MARGIN[1] - CHART_MARGIN[3]) / N;
const CELL_H = (window.ANYPLOT_SIZE.height - CHART_MARGIN[0] - CHART_MARGIN[2]) / N;
const MARKER_RADIUS = Math.max(Math.min(CELL_W, CELL_H) / 2 - 3, 4);

// Symmetric Pearson correlation matrix, diagonal = 1.00. Only the lower
// triangle (col <= row) is drawn — masking the upper mirror image reduces
// redundancy, per the spec's "consider masking upper or lower triangle" note.
const CORR = [
  [1.00, -0.45, 0.15, 0.30, 0.05, -0.25],
  [-0.45, 1.00, 0.20, -0.35, -0.05, 0.10],
  [0.15, 0.20, 1.00, 0.55, 0.40, -0.50],
  [0.30, -0.35, 0.55, 1.00, 0.35, -0.60],
  [0.05, -0.05, 0.40, 0.35, 1.00, -0.15],
  [-0.25, 0.10, -0.50, -0.60, -0.15, 1.00],
];

// Strongest links (off-diagonal, lower triangle) — the most positive and most
// negative correlations get a heavier border so the matrix has a point of
// emphasis beyond the raw grid of numbers.
let maxPos = { value: -Infinity, row: -1, col: -1 };
let maxNeg = { value: Infinity, row: -1, col: -1 };
for (let row = 0; row < N; row++) {
  for (let col = 0; col < row; col++) {
    const value = CORR[row][col];
    if (value > maxPos.value) maxPos = { value, row, col };
    if (value < maxNeg.value) maxNeg = { value, row, col };
  }
}
function isStrongest(row, col) {
  return (row === maxPos.row && col === maxPos.col) || (row === maxNeg.row && col === maxNeg.col);
}

// --- Color: imprint_div — negative -1 (red) .. 0 (page bg) .. +1 (blue) ----
function hexToRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}

const DIV_NEG = hexToRgb(t.div[0]); // #AE3030
const DIV_MID = hexToRgb(t.div[1]); // page bg, theme-adaptive
const DIV_POS = hexToRgb(t.div[2]); // #4467A3

function lerp(a, b, f) {
  return a + (b - a) * f;
}

function corrRgb(value) {
  const a = value <= 0 ? DIV_NEG : DIV_MID;
  const b = value <= 0 ? DIV_MID : DIV_POS;
  const f = value <= 0 ? value + 1 : value;
  return [Math.round(lerp(a[0], b[0], f)), Math.round(lerp(a[1], b[1], f)), Math.round(lerp(a[2], b[2], f))];
}

function corrFill(value) {
  const [red, green, blue] = corrRgb(value);
  return `rgb(${red},${green},${blue})`;
}

// Relative luminance — pick text color for maximum contrast against the fill
function corrTextColor(value) {
  const [red, green, blue] = corrRgb(value);
  const lin = (c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  };
  const luminance = 0.2126 * lin(red) + 0.7152 * lin(green) + 0.0722 * lin(blue);
  return luminance > 0.4 ? '#1A1A17' : '#F0EFE8';
}

// --- Title (fontsize scaled off the 67-char baseline) ----------------------
const TITLE_TEXT = 'Air-Quality Sensor Correlations · heatmap-correlation · javascript · highcharts · anyplot.ai';
const TITLE_FS = Math.max(Math.round(22 * Math.min(1, 67 / TITLE_TEXT.length)), 14);

const drawn = [];

function clearDrawn() {
  drawn.forEach((el) => {
    try {
      el.destroy();
    } catch (_err) {
      // already removed
    }
  });
  drawn.length = 0;
}

function drawAll() {
  const chart = this;
  clearDrawn();
  const r = chart.renderer;

  const cellW = chart.plotWidth / N;
  const cellH = chart.plotHeight / N;

  // Lower-triangle + diagonal cells only.
  for (let row = 0; row < N; row++) {
    for (let col = 0; col <= row; col++) {
      const value = CORR[row][col];
      const x = chart.plotLeft + col * cellW;
      const y = chart.plotTop + row * cellH;
      const onDiagonal = row === col;
      const emphasize = isStrongest(row, col);
      const fill = onDiagonal ? t.elevatedBg : corrFill(value);
      const textColor = onDiagonal ? t.inkSoft : corrTextColor(value);

      drawn.push(
        r
          .rect(x + 1, y + 1, cellW - 2, cellH - 2, 3)
          .attr({
            fill,
            stroke: emphasize ? t.ink : onDiagonal ? t.inkSoft : 'none',
            'stroke-width': emphasize ? 2 : onDiagonal ? 1 : 0,
            zIndex: 2,
          })
          .add()
      );
      drawn.push(
        r
          .text(value.toFixed(2), x + cellW / 2, y + cellH / 2 + 6)
          .attr({ align: 'center', zIndex: 2 })
          .css({ color: textColor, fontSize: '18px', fontWeight: onDiagonal ? '500' : '600' })
          .add()
      );
    }
  }

  // Row labels (left, right-aligned against the grid).
  LABELS.forEach((lbl, row) => {
    const cy = chart.plotTop + (row + 0.5) * cellH + 5;
    drawn.push(
      r
        .text(lbl, chart.plotLeft - 12, cy)
        .attr({ align: 'right', zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '15px' })
        .add()
    );
  });

  // Column labels (bottom, rotated) — every column keeps at least its
  // diagonal cell, so all N labels stay anchored under real grid content.
  LABELS.forEach((lbl, col) => {
    const cx = chart.plotLeft + (col + 0.5) * cellW;
    drawn.push(
      r
        .text(lbl, cx, chart.plotTop + chart.plotHeight + 16)
        .attr({ align: 'right', rotation: -40, zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '15px' })
        .add()
    );
  });

  // Diverging colorbar, placed inside the freed upper-triangle void. For
  // N=6, rows {0,1} x cols {3,4,5} is always empty (minCol 3 > maxRow 1).
  const barLeft = chart.plotLeft + 3 * cellW + cellW * 0.3;
  const barWidth = 3 * cellW * 0.7;
  const barTop = chart.plotTop + 0.55 * cellH;
  const barHeight = 22;
  const segments = 60;
  const segW = barWidth / segments;

  for (let i = 0; i < segments; i++) {
    const value = -1 + (2 * i) / (segments - 1);
    drawn.push(
      r
        .rect(barLeft + i * segW, barTop, segW + 0.5, barHeight)
        .attr({ fill: corrFill(value), zIndex: 2 })
        .add()
    );
  }
  drawn.push(
    r
      .rect(barLeft, barTop, barWidth, barHeight)
      .attr({ fill: 'none', stroke: t.inkSoft, 'stroke-width': 1, zIndex: 2 })
      .add()
  );
  [
    [-1, 0],
    [0, 0.5],
    [1, 1],
  ].forEach(([value, frac]) => {
    drawn.push(
      r
        .text(value.toFixed(0), barLeft + frac * barWidth, barTop + barHeight + 20)
        .attr({ align: 'center', zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '13px' })
        .add()
    );
  });
  drawn.push(
    r
      .text('Correlation (r)', barLeft + barWidth / 2, barTop - 12)
      .attr({ align: 'center', zIndex: 2 })
      .css({ color: t.inkSoft, fontSize: '14px', fontWeight: '500' })
      .add()
  );
}

// Invisible scatter layer aligned to each drawn lower-triangle cell so
// hovering exposes a real Highcharts tooltip — the core bundle has no
// heatmap/colorAxis module, but a matched-axis scatter series recovers
// native hover interactivity without disturbing the hand-drawn grid above it.
const cellPoints = [];
for (let row = 0; row < N; row++) {
  for (let col = 0; col <= row; col++) {
    cellPoints.push({ x: col, y: row, corr: CORR[row][col], rowLabel: LABELS[row], colLabel: LABELS[col] });
  }
}

Highcharts.chart('container', {
  chart: {
    backgroundColor: 'transparent',
    animation: false,
    style: { fontFamily: 'inherit' },
    margin: CHART_MARGIN,
    events: { load: drawAll, redraw: drawAll },
  },
  credits: { enabled: false },
  title: {
    text: TITLE_TEXT,
    style: { color: t.ink, fontSize: TITLE_FS + 'px', fontWeight: '600' },
  },
  subtitle: {
    text: 'Pairwise Pearson correlation across 6 outdoor sensor readings (lower triangle shown)',
    style: { color: t.inkSoft, fontSize: '14px' },
  },
  xAxis: { visible: false, min: -0.5, max: N - 0.5 },
  yAxis: { visible: false, gridLineWidth: 0, min: -0.5, max: N - 0.5, reversed: true },
  legend: { enabled: false },
  tooltip: {
    enabled: true,
    backgroundColor: t.elevatedBg,
    borderColor: t.inkSoft,
    borderRadius: 6,
    style: { color: t.ink, fontSize: '13px' },
    formatter: function () {
      const p = this.point;
      return `<b>${p.rowLabel} × ${p.colLabel}</b><br/>r = ${p.corr.toFixed(2)}`;
    },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      enableMouseTracking: true,
      stickyTracking: false,
      marker: {
        enabled: true,
        symbol: 'circle',
        radius: MARKER_RADIUS,
        fillColor: 'rgba(0,0,0,0.001)',
        lineWidth: 0,
        states: { hover: { enabled: false } },
      },
    },
  },
  series: [
    {
      type: 'scatter',
      name: 'Correlation',
      data: cellPoints,
    },
  ],
});
