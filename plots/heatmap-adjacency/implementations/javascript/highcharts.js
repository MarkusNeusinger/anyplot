// anyplot.ai
// heatmap-adjacency: Network Adjacency Matrix Heatmap
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: co-authorship network across five university research labs ------
// The core Highcharts bundle has no heatmap/colorAxis module loaded, so the
// matrix is drawn cell-by-cell with the SVG renderer, same as any other
// vector shape Highcharts can draw natively.
const LABS = ['Neuroscience', 'Robotics', 'Genomics', 'Climate Science', 'Materials Science'];
const LAB_SIZE = 8;
const N = LABS.length * LAB_SIZE; // 40 researchers total across five labs
const labOf = (i) => Math.floor(i / LAB_SIZE);
const NODE_NAMES = Array.from({ length: N }, (_, i) => `${LABS[labOf(i)].slice(0, 2).toUpperCase()}${(i % LAB_SIZE) + 1}`);

// Deterministic LCG — the browser has no seeded RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

// Nodes are already ordered by lab (cluster) so the block-diagonal structure
// is visible without a separate reordering step. Intra-lab pairs collaborate
// far more often and more deeply than cross-lab pairs, which is what produces
// the dense diagonal blocks against a sparse off-diagonal background.
const WEIGHT = Array.from({ length: N }, () => new Array(N).fill(0));
for (let i = 0; i < N; i++) {
  for (let j = i + 1; j < N; j++) {
    const sameLab = labOf(i) === labOf(j);
    const edgeProbability = sameLab ? 0.6 : 0.07;
    if (rand() < edgeProbability) {
      const maxPapers = sameLab ? 12 : 4;
      const papers = 1 + Math.round(rand() * (maxPapers - 1));
      WEIGHT[i][j] = papers;
      WEIGHT[j][i] = papers; // undirected graph — fill both triangles
    }
  }
}
// Diagonal (self-pairs) carries no meaning; it is hatched (see drawAll) to
// disambiguate "not applicable" from a genuine zero-weight absent edge.

let maxWeight = 0;
WEIGHT.forEach((row) => row.forEach((w) => { if (w > maxWeight) maxWeight = w; }));

// --- Color: imprint_seq — single-polarity data (joint-paper count >= 0) ----
function hexToRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}
const SEQ_LO = hexToRgb(t.seq[0]); // #009E73
const SEQ_HI = hexToRgb(t.seq[1]); // #4467A3
function lerp(a, b, f) {
  return a + (b - a) * f;
}
function weightFill(w) {
  if (w === 0) return t.elevatedBg; // absent edge — distinct from the color scale
  const f = w / maxWeight;
  const [red, green, blue] = [lerp(SEQ_LO[0], SEQ_HI[0], f), lerp(SEQ_LO[1], SEQ_HI[1], f), lerp(SEQ_LO[2], SEQ_HI[2], f)];
  return `rgb(${Math.round(red)},${Math.round(green)},${Math.round(blue)})`;
}

// --- Title (fontsize scaled off the 67-char baseline) -----------------------
const TITLE_TEXT = 'Co-authorship Network by Lab · heatmap-adjacency · javascript · highcharts · anyplot.ai';
const TITLE_FS = Math.max(Math.round(22 * Math.min(1, 67 / TITLE_TEXT.length)), 14);

// Fixed chart geometry (square canvas, harness-guaranteed 1200x1200 CSS px) —
// a single source of truth for the margin, the grid, and the invisible hover
// layer below, so everything lines up without a runtime resync. A fixed
// column is reserved to the right of the grid for the colorbar + its labels
// so long strings like "Joint papers" never run past the canvas edge.
const CHART_MARGIN = [130, 10, 175, 150]; // [top, right, bottom, left]
const COLORBAR_COLUMN = 200;
const size = window.ANYPLOT_SIZE;
const gridSpan = Math.min(
  size.width - CHART_MARGIN[1] - CHART_MARGIN[3] - COLORBAR_COLUMN,
  size.height - CHART_MARGIN[0] - CHART_MARGIN[2]
);
const CELL = gridSpan / N;
const MARKER_RADIUS = Math.max(CELL / 2 - 1, 2);

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
  const gridLeft = chart.plotLeft + (chart.plotWidth - COLORBAR_COLUMN - gridSpan) / 2;
  const gridTop = chart.plotTop + (chart.plotHeight - gridSpan) / 2;

  // Matrix cells — full N x N grid, both triangles filled (undirected graph).
  // Diagonal (self-pair) cells get a hatch overlay so "not applicable" reads
  // as visually distinct from a genuine zero-weight absent edge.
  for (let row = 0; row < N; row++) {
    for (let col = 0; col < N; col++) {
      const w = WEIGHT[row][col];
      const x = gridLeft + col * CELL;
      const y = gridTop + row * CELL;
      drawn.push(
        r
          .rect(x + 0.5, y + 0.5, CELL - 1, CELL - 1, 0)
          .attr({ fill: weightFill(w), stroke: 'none', zIndex: 2 })
          .add()
      );
      if (row === col) {
        const pad = Math.max(CELL * 0.15, 1);
        drawn.push(
          r.path(['M', x + pad, y + pad, 'L', x + CELL - pad, y + CELL - pad]).attr({ stroke: t.inkSoft, 'stroke-width': 1, opacity: 0.4, zIndex: 3 }).add()
        );
        drawn.push(
          r.path(['M', x + CELL - pad, y + pad, 'L', x + pad, y + CELL - pad]).attr({ stroke: t.inkSoft, 'stroke-width': 1, opacity: 0.4, zIndex: 3 }).add()
        );
      }
    }
  }

  // Block-boundary dividers between labs — thicker lines so the cluster
  // structure the node ordering encodes is immediately legible.
  for (let b = 1; b < LABS.length; b++) {
    const pos = gridLeft + b * LAB_SIZE * CELL;
    drawn.push(
      r.path(['M', pos, gridTop, 'L', pos, gridTop + gridSpan]).attr({ stroke: t.inkSoft, 'stroke-width': 1.5, zIndex: 3 }).add()
    );
    const posY = gridTop + b * LAB_SIZE * CELL;
    drawn.push(
      r.path(['M', gridLeft, posY, 'L', gridLeft + gridSpan, posY]).attr({ stroke: t.inkSoft, 'stroke-width': 1.5, zIndex: 3 }).add()
    );
  }
  // Outer frame around the full matrix.
  drawn.push(
    r.rect(gridLeft, gridTop, gridSpan, gridSpan).attr({ fill: 'none', stroke: t.inkSoft, 'stroke-width': 1.5, zIndex: 3 }).add()
  );

  // Sparse tick marks halfway through each block — full per-node labels would
  // crowd a 40x40 grid, but a light mid-block tick gives orientation within
  // each lab's rows/columns without adding text.
  for (let i = LAB_SIZE / 2; i < N; i += LAB_SIZE) {
    const x = gridLeft + i * CELL;
    drawn.push(r.path(['M', x, gridTop + gridSpan, 'L', x, gridTop + gridSpan + 6]).attr({ stroke: t.grid, 'stroke-width': 1, zIndex: 2 }).add());
    const y = gridTop + i * CELL;
    drawn.push(r.path(['M', gridLeft - 6, y, 'L', gridLeft, y]).attr({ stroke: t.grid, 'stroke-width': 1, zIndex: 2 }).add());
  }

  // Lab labels centered on each block — per-node tick labels would crowd a
  // 40x40 grid, so only the group boundaries are labeled (x below, y left).
  LABS.forEach((lab, b) => {
    const center = gridLeft + (b + 0.5) * LAB_SIZE * CELL;
    drawn.push(
      r.text(lab, center, gridTop + gridSpan + 34).attr({ align: 'center', zIndex: 2 }).css({ color: t.inkSoft, fontSize: '16px', fontWeight: '500' }).add()
    );
    const centerY = gridTop + (b + 0.5) * LAB_SIZE * CELL;
    drawn.push(
      r
        .text(lab, gridLeft - 14, centerY + 5)
        .attr({ align: 'right', zIndex: 2 })
        .css({ color: t.inkSoft, fontSize: '16px', fontWeight: '500' })
        .add()
    );
  });

  // Vertical colorbar in the freed right margin.
  const barLeft = gridLeft + gridSpan + 34;
  const barTop = gridTop;
  const barWidth = 22;
  const barHeight = gridSpan;
  const segments = 50;
  const segH = barHeight / segments;
  for (let i = 0; i < segments; i++) {
    const w = maxWeight - ((maxWeight * i) / (segments - 1));
    drawn.push(r.rect(barLeft, barTop + i * segH, barWidth, segH + 0.5).attr({ fill: weightFill(Math.max(w, 0.01)), zIndex: 2 }).add());
  }
  drawn.push(r.rect(barLeft, barTop, barWidth, barHeight).attr({ fill: 'none', stroke: t.inkSoft, 'stroke-width': 1, zIndex: 3 }).add());
  [
    [maxWeight, 0],
    [1, 1],
  ].forEach(([w, frac]) => {
    drawn.push(
      r.text(String(w), barLeft + barWidth + 10, barTop + frac * barHeight + 5).attr({ align: 'left', zIndex: 2 }).css({ color: t.inkSoft, fontSize: '13px' }).add()
    );
  });
  drawn.push(r.text('Joint papers', barLeft, barTop - 16).attr({ align: 'left', zIndex: 2 }).css({ color: t.inkSoft, fontSize: '14px', fontWeight: '500' }).add());
  // "No collaboration" swatch below the colorbar for the absent-edge fill.
  const swatchTop = barTop + barHeight + 22;
  drawn.push(r.rect(barLeft, swatchTop, barWidth, barWidth).attr({ fill: t.elevatedBg, stroke: t.inkSoft, 'stroke-width': 1, zIndex: 3 }).add());
  drawn.push(
    r.text('No papers', barLeft + barWidth + 10, swatchTop + barWidth / 2 + 5).attr({ align: 'left', zIndex: 2 }).css({ color: t.inkSoft, fontSize: '13px' }).add()
  );
  // "Self-pair" swatch — same hatch pattern drawn on the matrix diagonal, so
  // the legend disambiguates "not applicable" from a genuine absent edge.
  const swatch2Top = swatchTop + barWidth + 14;
  drawn.push(r.rect(barLeft, swatch2Top, barWidth, barWidth).attr({ fill: t.elevatedBg, stroke: t.inkSoft, 'stroke-width': 1, zIndex: 3 }).add());
  const hp = barWidth * 0.15;
  drawn.push(
    r.path(['M', barLeft + hp, swatch2Top + hp, 'L', barLeft + barWidth - hp, swatch2Top + barWidth - hp]).attr({ stroke: t.inkSoft, 'stroke-width': 1, opacity: 0.4, zIndex: 3 }).add()
  );
  drawn.push(
    r.path(['M', barLeft + barWidth - hp, swatch2Top + hp, 'L', barLeft + hp, swatch2Top + barWidth - hp]).attr({ stroke: t.inkSoft, 'stroke-width': 1, opacity: 0.4, zIndex: 3 }).add()
  );
  drawn.push(
    r.text('Self-pair (n/a)', barLeft + barWidth + 10, swatch2Top + barWidth / 2 + 5).attr({ align: 'left', zIndex: 2 }).css({ color: t.inkSoft, fontSize: '13px' }).add()
  );
}

// Invisible scatter layer aligned to each cell so hovering exposes a real
// Highcharts tooltip — the core bundle has no heatmap/colorAxis module, but a
// matched-axis scatter series recovers native hover interactivity without
// disturbing the hand-drawn matrix above it.
const cellPoints = [];
for (let row = 0; row < N; row++) {
  for (let col = 0; col < N; col++) {
    cellPoints.push({ x: col, y: row, papers: WEIGHT[row][col], from: NODE_NAMES[row], to: NODE_NAMES[col] });
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
    text: '40 researchers across five labs, ordered by lab to expose block-diagonal collaboration clusters',
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
      if (p.from === p.to) return `<b>${p.from}</b><br/>Self-pair — not applicable`;
      return p.papers > 0 ? `<b>${p.from} ↔ ${p.to}</b><br/>${p.papers} joint paper${p.papers === 1 ? '' : 's'}` : `<b>${p.from} ↔ ${p.to}</b><br/>No collaboration`;
    },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      enableMouseTracking: true,
      stickyTracking: false,
      marker: {
        enabled: true,
        symbol: 'square',
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
      name: 'Collaboration',
      data: cellPoints,
    },
  ],
});
