// anyplot.ai
// circos-basic: Circos Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-04
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: structural-variant links across 8 chromosome segments -----------
// Segment arc length is proportional to chromosome size (Mb, approximate
// human karyotype lengths for chr1-chr8). An inner track carries a second
// data layer (differential expression, log2 fold-change) rendered as a
// diverging-color band, and ribbons bow through the centre to show
// inter-chromosomal structural-variant links (supporting read count).
const chromNames = ["Chr1", "Chr2", "Chr3", "Chr4", "Chr5", "Chr6", "Chr7", "Chr8"];
const segmentSizes = [248, 242, 198, 190, 181, 170, 159, 145]; // Mb
const expression = [1.8, -1.4, 0.6, -2.2, 1.1, -0.5, 2.4, -1.7]; // log2FC

// [from, to, supportingReads] — undirected structural-variant links.
const links = [
  [0, 1, 45], [0, 2, 12], [0, 4, 30], [0, 6, 8],
  [1, 3, 55], [1, 5, 22], [1, 7, 14],
  [2, 3, 18], [2, 5, 40], [2, 6, 10],
  [3, 4, 25], [3, 7, 33],
  [4, 5, 15], [4, 6, 48],
  [5, 7, 20],
  [6, 7, 28],
];

const n = chromNames.length;
const linkMatrix = Array.from({ length: n }, () => new Array(n).fill(0));
for (const [i, j, value] of links) {
  linkMatrix[i][j] = value;
  linkMatrix[j][i] = value;
}
const nodeTotal = linkMatrix.map((row) => row.reduce((a, b) => a + b, 0));

// Each chromosome keeps a distinct Imprint hue (brand green leads at slot 0).
const segmentColors = chromNames.map((_, i) => t.palette[i % t.palette.length]);

// --- Diverging colormap (imprint_div) for the expression track --------------
const hexToRgb = (hex) => {
  const h = hex.replace("#", "");
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
};
const rgbToHex = ([r, g, b]) =>
  `#${[r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
const lerpRgb = (a, b, f) => a.map((v, i) => v + (b[i] - v) * f);

const [divNeg, divMid, divPos] = t.div.map(hexToRgb);
const maxAbsExpression = Math.max(...expression.map(Math.abs));
const divergingColor = (value) => {
  const u = 0.5 + 0.5 * (value / maxAbsExpression); // 0..1, 0.5 = midpoint
  return u < 0.5 ? rgbToHex(lerpRgb(divNeg, divMid, u / 0.5)) : rgbToHex(lerpRgb(divMid, divPos, (u - 0.5) / 0.5));
};
const trackColors = expression.map(divergingColor);

const hexToRgba = (hex, alpha) => {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// --- Structural-variant ribbon plugin ---------------------------------------
// Chart.js has no native circos/chord type, but its plugin API exposes the
// live canvas plus the doughnut's computed arc geometry. Ribbons anchor to
// the inner edge of the expression track (dataset 1) and bow through the
// centre; ribbon end-width is proportional to link strength, drawn
// strongest-first so thin links stay visible on top. No external library,
// no community plugin: pure Chart.js extensibility (same technique used for
// chord-basic's ribbons, generalised here to a sparse link list plus a
// second concentric data track).
const circosRibbons = {
  id: "circosRibbons",
  afterDatasetsDraw(chart) {
    const segmentArcs = chart.getDatasetMeta(0).data;
    const trackArcs = chart.getDatasetMeta(1).data;
    if (!segmentArcs.length || !trackArcs.length) return;

    const { x: cx, y: cy } = segmentArcs[0].getProps(["x", "y"], true);
    const innerR = trackArcs[0].getProps(["innerRadius"], true).innerRadius;

    // Angular interval [a0, a1] of every ordered slot (i -> j) inside arc i,
    // sized proportional to that link's share of node i's total link value.
    const slot = segmentArcs.map((arc, i) => {
      const { startAngle, endAngle } = arc.getProps(["startAngle", "endAngle"], true);
      const span = endAngle - startAngle;
      let acc = 0;
      return linkMatrix[i].map((value) => {
        const a0 = startAngle + (acc / nodeTotal[i]) * span;
        acc += value;
        const a1 = startAngle + (acc / nodeTotal[i]) * span;
        return [a0, a1];
      });
    });

    const pointAt = (angle, r) => [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];

    const pairs = links.map(([i, j, value]) => [i, j, value]).sort((a, b) => b[2] - a[2]);

    const ctx = chart.ctx;
    ctx.save();
    ctx.lineJoin = "round";
    for (const [i, j] of pairs) {
      const [si0, si1] = slot[i][j];
      const [sj0, sj1] = slot[j][i];
      const [xi, yi] = pointAt(si0, innerR);
      const [xj, yj] = pointAt(sj0, innerR);

      ctx.beginPath();
      ctx.moveTo(xi, yi);
      ctx.arc(cx, cy, innerR, si0, si1);    // ride segment i's inner edge
      ctx.lineTo(xj, yj);
      ctx.arc(cx, cy, innerR, sj0, sj1);    // ride segment j's inner edge
      ctx.quadraticCurveTo(cx, cy, xi, yi); // bow back through the centre
      ctx.closePath();

      const dominant = linkMatrix[i][j] >= linkMatrix[j][i] ? i : j;
      ctx.fillStyle = hexToRgba(segmentColors[dominant], 0.5);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = hexToRgba(segmentColors[dominant], 0.85);
      ctx.fill();
      ctx.stroke();
    }
    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart: two concentric doughnut rings (segments + expression track) ----
// plus the structural-variant ribbon plugin bowing through the centre.
new Chart(canvas, {
  type: "doughnut",
  data: {
    labels: chromNames,
    datasets: [
      {
        label: "Chromosome",
        data: segmentSizes,
        backgroundColor: segmentColors,
        borderColor: t.pageBg,
        borderWidth: 3,
        radius: "100%",
        cutout: "80%",
      },
      {
        label: "Differential expression",
        data: segmentSizes,
        backgroundColor: trackColors,
        borderColor: t.pageBg,
        borderWidth: 2,
        radius: "78%",
        cutout: "64%",
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 28 },
    plugins: {
      title: {
        display: true,
        text: "circos-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { top: 4, bottom: 18 },
      },
      legend: {
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 16 },
          padding: 18,
          boxWidth: 16,
          boxHeight: 16,
        },
      },
      tooltip: {
        callbacks: {
          label: (item) =>
            item.datasetIndex === 0
              ? `${item.label}: ${item.parsed} Mb`
              : `${item.label} expression: ${expression[item.dataIndex].toFixed(1)} log2FC`,
        },
      },
    },
  },
  plugins: [circosRibbons],
});
