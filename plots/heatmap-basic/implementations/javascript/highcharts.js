// anyplot.ai
// heatmap-basic: Basic Heatmap
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-20
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data: dashboard page views by day of week and hour of day -------------
// The core Highcharts bundle has no heatmap/colorAxis-mapping module loaded,
// so the grid is drawn cell-by-cell with the SVG renderer instead.
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, h) => h);
const HOUR_LABELS = HOURS.map((h) => (h === 0 ? '12am' : h < 12 ? `${h}am` : h === 12 ? '12pm' : `${h - 12}pm`));
const N_ROWS = DAYS.length;
const N_COLS = HOURS.length;

// Deterministic LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Two-Gaussian daily curve — a morning login peak and a late-afternoon peak,
// shifted and damped on weekends to mimic a B2B SaaS dashboard's usage rhythm.
function gaussian(x, center, width) {
  return Math.exp(-((x - center) ** 2) / (2 * width * width));
}
function hourlyBase(hour, isWeekend) {
  const morningPeak = isWeekend ? 11 : 10;
  const afternoonPeak = isWeekend ? 14 : 16;
  const morning = gaussian(hour, morningPeak, 2.2);
  const afternoon = gaussian(hour, afternoonPeak, 3);
  return 0.04 + 0.75 * morning + (isWeekend ? 0.3 : 0.65) * afternoon;
}

const PEAK_VIEWS = 3200;
const VIEWS = DAYS.map((_, row) => {
  const isWeekend = row >= 5;
  const dayFactor = isWeekend ? 0.4 : 1.0;
  return HOURS.map((hour) => {
    const base = hourlyBase(hour, isWeekend) * dayFactor;
    const noise = 0.85 + rand() * 0.3;
    return Math.round(base * PEAK_VIEWS * noise);
  });
});

let minViews = Infinity;
let maxViews = -Infinity;
VIEWS.forEach((row) =>
  row.forEach((v) => {
    if (v < minViews) minViews = v;
    if (v > maxViews) maxViews = v;
  })
);

// --- Color: imprint_seq — single-polarity data (page views, always >= 0) ---
function hexToRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}
const SEQ_LO = hexToRgb(t.seq[0]); // #009E73
const SEQ_HI = hexToRgb(t.seq[1]); // #4467A3

function lerp(a, b, f) {
  return a + (b - a) * f;
}
function viewsRgb(value) {
  const f = (value - minViews) / (maxViews - minViews);
  return [Math.round(lerp(SEQ_LO[0], SEQ_HI[0], f)), Math.round(lerp(SEQ_LO[1], SEQ_HI[1], f)), Math.round(lerp(SEQ_LO[2], SEQ_HI[2], f))];
}
function viewsFill(value) {
  const [red, green, blue] = viewsRgb(value);
  return `rgb(${red},${green},${blue})`;
}

// --- Title (fontsize scaled off the 67-char baseline) ----------------------
const TITLE_TEXT = 'Dashboard Page Views · heatmap-basic · javascript · highcharts · anyplot.ai';
const TITLE_FS = Math.max(Math.round(22 * Math.min(1, 67 / TITLE_TEXT.length)), 14);

// Fixed chart geometry (landscape canvas, harness-guaranteed 1600x900 CSS px)
// — a single source of truth for the margin, the grid, and the invisible
// hover layer below, so everything lines up without a runtime resync.
const CHART_MARGIN = [130, 210, 100, 90]; // [top, right, bottom, left]
const CELL_W = (window.ANYPLOT_SIZE.width - CHART_MARGIN[1] - CHART_MARGIN[3]) / N_COLS;
const CELL_H = (window.ANYPLOT_SIZE.height - CHART_MARGIN[0] - CHART_MARGIN[2]) / N_ROWS;
const MARKER_RADIUS = Math.max(Math.min(CELL_W, CELL_H) / 2 - 2, 3);

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

  const cellW = chart.plotWidth / N_COLS;
  const cellH = chart.plotHeight / N_ROWS;

  // Grid cells — full N_ROWS x N_COLS matrix, no masking needed (unlike a
  // symmetric correlation matrix, this data has no mirror redundancy).
  for (let row = 0; row < N_ROWS; row++) {
    for (let col = 0; col < N_COLS; col++) {
      const value = VIEWS[row][col];
      const x = chart.plotLeft + col * cellW;
      const y = chart.plotTop + row * cellH;
      drawn.push(
        r
          .rect(x + 0.5, y + 0.5, cellW - 1, cellH - 1, 1)
          .attr({ fill: viewsFill(value), stroke: 'none', zIndex: 2 })
          .add()
      );
    }
  }

  // Row labels (left, right-aligned against the grid).
  DAYS.forEach((lbl, row) => {
    const cy = chart.plotTop + (row + 0.5) * cellH + 5;
    drawn.push(
      r
        .text(lbl, chart.plotLeft - 14, cy)
        .attr({ align: 'right', zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '15px' })
        .add()
    );
  });

  // Column labels — every 3rd hour to avoid crowding 24 narrow columns.
  HOUR_LABELS.forEach((lbl, col) => {
    if (col % 3 !== 0) return;
    const cx = chart.plotLeft + (col + 0.5) * cellW;
    drawn.push(
      r
        .text(lbl, cx, chart.plotTop + chart.plotHeight + 24)
        .attr({ align: 'center', zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '14px' })
        .add()
    );
  });

  // Vertical colorbar in the freed right margin.
  const barLeft = chart.plotLeft + chart.plotWidth + 55;
  const barTop = chart.plotTop + 10;
  const barWidth = 26;
  const barHeight = chart.plotHeight - 20;
  const segments = 50;
  const segH = barHeight / segments;

  for (let i = 0; i < segments; i++) {
    const value = maxViews - ((maxViews - minViews) * i) / (segments - 1);
    drawn.push(
      r
        .rect(barLeft, barTop + i * segH, barWidth, segH + 0.5)
        .attr({ fill: viewsFill(value), zIndex: 2 })
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
    [maxViews, 0],
    [minViews, 1],
  ].forEach(([value, frac]) => {
    drawn.push(
      r
        .text(Math.round(value).toLocaleString(), barLeft + barWidth + 10, barTop + frac * barHeight + 5)
        .attr({ align: 'left', zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '13px' })
        .add()
    );
  });
  drawn.push(
    r
      .text('Page views', barLeft, barTop - 16)
      .attr({ align: 'left', zIndex: 2 })
      .css({ color: t.inkSoft, fontSize: '14px', fontWeight: '500' })
      .add()
  );
}

// Invisible scatter layer aligned to each drawn cell so hovering exposes a
// real Highcharts tooltip — the core bundle has no heatmap/colorAxis module,
// but a matched-axis scatter series recovers native hover interactivity
// without disturbing the hand-drawn grid above it.
const cellPoints = [];
for (let row = 0; row < N_ROWS; row++) {
  for (let col = 0; col < N_COLS; col++) {
    cellPoints.push({ x: col, y: row, views: VIEWS[row][col], dayLabel: DAYS[row], hourLabel: HOUR_LABELS[col] });
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
    text: 'Simulated hourly logins to a B2B analytics dashboard across one week',
    style: { color: t.inkSoft, fontSize: '14px' },
  },
  xAxis: { visible: false, min: -0.5, max: N_COLS - 0.5 },
  yAxis: { visible: false, gridLineWidth: 0, min: -0.5, max: N_ROWS - 0.5, reversed: true },
  legend: { enabled: false },
  tooltip: {
    enabled: true,
    backgroundColor: t.elevatedBg,
    borderColor: t.inkSoft,
    borderRadius: 6,
    style: { color: t.ink, fontSize: '13px' },
    formatter: function () {
      const p = this.point;
      return `<b>${p.dayLabel} ${p.hourLabel}</b><br/>${p.views.toLocaleString()} views`;
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
      name: 'Page views',
      data: cellPoints,
    },
  ],
});
