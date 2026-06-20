// anyplot.ai
// line-parametric: Parametric Curve Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;
const TWO_PI = 2 * Math.PI;
const N = 600;

// Color interpolation for gradient-along-curve direction encoding
function hexToRgb(hex) {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

function lerpColor(hex1, hex2, ratio) {
  const r = ratio < 0 ? 0 : ratio > 1 ? 1 : ratio;
  const [r1, g1, b1] = hexToRgb(hex1);
  const [r2, g2, b2] = hexToRgb(hex2);
  return `rgb(${Math.round(r1 + (r2 - r1) * r)},${Math.round(g1 + (g2 - g1) * r)},${Math.round(b1 + (b2 - b1) * r)})`;
}

// Parametric curve sampler
function makeCurve(xFn, yFn, tMin, tMax, n) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const ti = tMin + (tMax - tMin) * (i / (n - 1));
    pts.push({ x: xFn(ti), y: yFn(ti) });
  }
  return pts;
}

// Curve 1: Lissajous figure — 3:2 frequency ratio, phase shift π/4
const lissData = makeCurve(
  ti => Math.sin(3 * ti + Math.PI / 4),
  ti => Math.sin(2 * ti),
  0, TWO_PI, N
);

// Curve 2: Archimedean spiral — 3 revolutions, radius normalized to [0, 1]
const spiralData = makeCurve(
  ti => (ti / (3 * TWO_PI)) * Math.cos(ti),
  ti => (ti / (3 * TWO_PI)) * Math.sin(ti),
  0, 3 * TWO_PI, N
);

// Layout: two square panels side-by-side inside the 1600×900 CSS mount
const container = document.getElementById("container");
container.style.cssText = `
  display: flex;
  flex-direction: column;
  background: ${t.pageBg};
  padding: 0 40px;
  box-sizing: border-box;
`;

// Main title
const titleDiv = document.createElement("div");
titleDiv.style.cssText = `
  text-align: center;
  color: ${t.ink};
  font: 600 22px/1.4 sans-serif;
  padding: 18px 0 6px;
  flex-shrink: 0;
`;
titleDiv.textContent = "line-parametric · javascript · chartjs · anyplot.ai";
container.appendChild(titleDiv);

// Chart row
const row = document.createElement("div");
row.style.cssText = `
  display: flex;
  flex: 1;
  justify-content: space-evenly;
  align-items: center;
`;
container.appendChild(row);

// Direction legend
const legendDiv = document.createElement("div");
legendDiv.style.cssText = `
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
  padding: 8px 0 14px;
  flex-shrink: 0;
`;
const gradBar = `linear-gradient(to right, ${t.seq[0]}, ${t.seq[1]})`;
legendDiv.innerHTML = `
  <div style="display:flex;align-items:center;gap:10px;font:14px sans-serif;color:${t.inkSoft};">
    <span style="display:inline-block;width:90px;height:5px;background:${gradBar};border-radius:3px;"></span>
    <span>color encodes direction of t: start &#8594; end</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;font:14px sans-serif;color:${t.inkSoft};">
    <span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:${t.seq[0]};border:2px solid ${t.pageBg};"></span>
    <span>t = 0</span>
    <span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:${t.seq[1]};border:2px solid ${t.pageBg};margin-left:10px;"></span>
    <span>t = T</span>
  </div>
`;
container.appendChild(legendDiv);

// Build a single parametric panel (square canvas div + Chart.js scatter/line)
function buildPanel(data, subtitle, axisRange) {
  const n = data.length;
  const colorStart = t.seq[0]; // #009E73 — Imprint palette position 1
  const colorEnd = t.seq[1];   // #4467A3 — Imprint sequential end

  const div = document.createElement("div");
  div.style.cssText = "width: 700px; height: 700px;";
  const canvas = document.createElement("canvas");
  div.appendChild(canvas);
  row.appendChild(div);

  new Chart(canvas, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: subtitle,
          data,
          showLine: true,
          pointRadius: 0,
          borderWidth: 2.5,
          segment: {
            borderColor: ctx => lerpColor(colorStart, colorEnd, ctx.p0DataIndex / (n - 2)),
          },
        },
        // Start marker (t = 0)
        {
          data: [data[0]],
          pointRadius: 8,
          pointHoverRadius: 8,
          pointBackgroundColor: colorStart,
          pointBorderColor: t.pageBg,
          pointBorderWidth: 2,
          showLine: false,
          label: "t = 0",
        },
        // End marker (t = T)
        {
          data: [data[n - 1]],
          pointRadius: 8,
          pointHoverRadius: 8,
          pointBackgroundColor: colorEnd,
          pointBorderColor: t.pageBg,
          pointBorderWidth: 2,
          showLine: false,
          label: "t = T",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        title: {
          display: true,
          text: subtitle,
          color: t.ink,
          font: { size: 15, weight: "600" },
          padding: { bottom: 10 },
        },
        legend: { display: false },
      },
      scales: {
        x: {
          min: axisRange[0],
          max: axisRange[1],
          ticks: { color: t.inkSoft, font: { size: 13 }, maxTicksLimit: 7 },
          grid: { color: t.grid },
          title: { display: true, text: "x(t)", color: t.ink, font: { size: 14 } },
          border: { color: t.inkSoft },
        },
        y: {
          min: axisRange[0],
          max: axisRange[1],
          ticks: { color: t.inkSoft, font: { size: 13 }, maxTicksLimit: 7 },
          grid: { color: t.grid },
          title: { display: true, text: "y(t)", color: t.ink, font: { size: 14 } },
          border: { color: t.inkSoft },
        },
      },
      layout: { padding: 12 },
    },
  });
}

buildPanel(lissData, "Lissajous — x = sin(3t + π/4), y = sin(2t)", [-1.25, 1.25]);
buildPanel(spiralData, "Archimedean Spiral — 3 revolutions", [-1.1, 1.1]);
