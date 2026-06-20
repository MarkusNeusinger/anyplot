// anyplot.ai
// lightcurve-transit: Astronomical Light Curve
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// Deterministic 31-bit LCG (seed=1337) — avoids Math.random()
let _seed = 1337;
const rand = () => {
  _seed = (_seed * 214013 + 2531011) & 0x7fffffff;
  return _seed / 0x80000000;
};

// Box-Muller transform for Gaussian noise (uses deterministic rand())
const randn = () => {
  const u1 = Math.max(rand(), 1e-10);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

// Simplified quadratic limb-darkened transit profile
const T_DEPTH = 0.0108;  // 1.08% dip
const T_HALF  = 0.042;   // half-duration in phase units
const T_ING   = 0.015;   // ingress half-width

const transitFlux = ph => {
  const a = Math.abs(ph);
  if (a >= T_HALF) return 1.0;
  if (a <= T_HALF - T_ING) {
    return 1.0 - T_DEPTH * (1.0 - 0.07 * ((a / (T_HALF - T_ING)) ** 2));
  }
  const u = (a - (T_HALF - T_ING)) / T_ING;
  return 1.0 - T_DEPTH * (1.0 - u * u);
};

// 320 phase-folded TESS-like photometric measurements with Gaussian noise
const N_OBS = 320;
const obsData = Array.from({ length: N_OBS }, (_, i) => {
  const ph  = Math.max(-0.499, Math.min(0.499, -0.5 + i / N_OBS + (rand() - 0.5) * 0.5 / N_OBS));
  const err = 0.0016 + rand() * 0.0012;
  return { x: ph, y: transitFlux(ph) + randn() * err, err };
}).sort((a, b) => a.x - b.x);

// 800-point smooth model curve (no noise)
const modelData = Array.from({ length: 800 }, (_, i) => ({
  x: -0.5 + i / 799,
  y: transitFlux(-0.5 + i / 799),
}));

// Plugin: canvas background + per-point error bars drawn on dataset[0]
Chart.register({
  id: 'lightcurveExtras',
  beforeDraw({ ctx, width, height }) {
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  },
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales: { y: ySc } } = chart;
    const meta = chart.getDatasetMeta(0);
    if (meta.hidden) return;

    ctx.save();
    ctx.beginPath();
    ctx.rect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);
    ctx.clip();
    ctx.strokeStyle = t.inkSoft + 'a0';
    ctx.lineWidth   = 1.5;
    const CAP = 3.5;

    obsData.forEach((d, i) => {
      const pt = meta.data[i];
      if (!pt) return;
      const px  = pt.x;
      const py1 = ySc.getPixelForValue(d.y + d.err);
      const py2 = ySc.getPixelForValue(d.y - d.err);
      ctx.beginPath(); ctx.moveTo(px, py1);       ctx.lineTo(px, py2);       ctx.stroke();
      ctx.beginPath(); ctx.moveTo(px - CAP, py1); ctx.lineTo(px + CAP, py1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(px - CAP, py2); ctx.lineTo(px + CAP, py2); ctx.stroke();
    });

    ctx.restore();
  },
});

// Mount canvas into harness-provided #container
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

const TITLE    = 'lightcurve-transit · javascript · chartjs · anyplot.ai';
const titleSize = Math.max(16, Math.round(22 * Math.min(1.0, 67 / TITLE.length)));

new Chart(canvas, {
  type: 'scatter',
  data: {
    datasets: [
      {
        label: 'Photometric data',
        data: obsData,
        type: 'scatter',
        backgroundColor: t.palette[0] + 'bb',
        borderColor:     t.palette[0],
        borderWidth: 0.5,
        pointRadius: 3,
        pointHoverRadius: 4,
        order: 2,
      },
      {
        label: 'Transit model',
        data: modelData,
        type: 'line',
        borderColor:     t.palette[2],
        backgroundColor: 'transparent',
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.2,
        order: 1,
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
        text: TITLE,
        color: t.ink,
        font: { size: titleSize, weight: '500' },
        padding: { bottom: 16 },
      },
      legend: {
        position: 'top',
        align: 'end',
        labels: {
          color: t.ink,
          font: { size: 14 },
          usePointStyle: true,
          padding: 20,
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        title: {
          display: true,
          text: 'Orbital Phase',
          color: t.ink,
          font: { size: 15 },
        },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { color: t.grid },
        min: -0.5,
        max: 0.5,
      },
      y: {
        type: 'linear',
        title: {
          display: true,
          text: 'Relative Flux',
          color: t.ink,
          font: { size: 15 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          callback: v => v.toFixed(4),
        },
        grid: { color: t.grid },
      },
    },
  },
});
