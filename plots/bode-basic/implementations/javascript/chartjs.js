// anyplot.ai
// bode-basic: Bode Plot for Frequency Response
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-17

const t = window.ANYPLOT_TOKENS;

// Open-loop transfer function G(jω) = 1 / (jω · (1 + jω/a) · (1 + jω/b))
// Poles at ω=1 and ω=10 rad/s — classic third-order system with clear stability margins
const a = 1, b = 10;
const N = 500;
const W_MIN = 0.01, W_MAX = 1000;

const magData = [], phaseData = [];
let gainCrossFreq = null, phaseCrossFreq = null;
let phaseMargin = null, gainMargin = null;

for (let i = 0; i < N; i++) {
  const w = Math.pow(10, Math.log10(W_MIN) + (i / (N - 1)) * (Math.log10(W_MAX) - Math.log10(W_MIN)));
  const mag = 1 / (w * Math.sqrt(1 + (w / a) * (w / a)) * Math.sqrt(1 + (w / b) * (w / b)));
  const magDb = 20 * Math.log10(mag);
  const phase = -90 - (Math.atan(w / a) * 180 / Math.PI) - (Math.atan(w / b) * 180 / Math.PI);

  magData.push({ x: w, y: magDb });
  phaseData.push({ x: w, y: phase });

  if (i > 0) {
    // Gain crossover: magnitude crosses 0 dB (above → below)
    if (gainCrossFreq === null && magData[i - 1].y > 0 && magDb <= 0) {
      gainCrossFreq = w;
      phaseMargin = 180 + phase;
    }
    // Phase crossover: phase crosses -180° (above → below)
    if (phaseCrossFreq === null && phaseData[i - 1].y > -180 && phase <= -180) {
      phaseCrossFreq = w;
      gainMargin = -magDb;
    }
  }
}

// --- Layout: flex column, top = magnitude, bottom = phase ---
const container = document.getElementById('container');
// Set individual style properties so the harness's width/height are preserved
container.style.display = 'flex';
container.style.flexDirection = 'column';
container.style.background = t.pageBg;
container.style.boxSizing = 'border-box';

function addPanel() {
  const wrap = document.createElement('div');
  wrap.style.cssText = 'position:relative;flex:1;width:100%;min-height:0;overflow:hidden';
  container.appendChild(wrap);
  const canvas = document.createElement('canvas');
  wrap.appendChild(canvas);
  return canvas;
}

const magCanvas = addPanel();
const phaseCanvas = addPanel();

// Custom log-axis tick formatter: show powers of 10 only
const logTickCallback = (val) => {
  const exp = Math.log10(val);
  const rounded = Math.round(exp);
  if (Math.abs(exp - rounded) < 0.02) {
    if (rounded >= 0) return String(Math.round(Math.pow(10, rounded)));
    return (Math.pow(10, rounded)).toFixed(-rounded);
  }
  return '';
};

const logXBase = {
  type: 'logarithmic',
  min: W_MIN,
  max: W_MAX,
  grid: { color: t.grid },
  ticks: { color: t.inkSoft, font: { size: 14 }, callback: logTickCallback }
};

// Custom afterDraw plugin for margin labels
function makeMarginPlugin(annotations) {
  return {
    id: 'marginLabels',
    afterDraw(chart) {
      const ctx = chart.ctx;
      const xScale = chart.scales.x;
      const yScale = chart.scales.y;
      ctx.save();
      ctx.font = 'bold 13px sans-serif';
      ctx.textBaseline = 'bottom';
      for (const ann of annotations) {
        if (ann.xValue == null) continue;
        const xPx = xScale.getPixelForValue(ann.xValue);
        const yPx = yScale.getPixelForValue(ann.yValue);
        ctx.fillStyle = ann.color;
        ctx.textAlign = ann.align || 'left';
        ctx.fillText(ann.text, xPx + (ann.dx || 6), yPx + (ann.dy || -4));
      }
      ctx.restore();
    }
  };
}

// Scale bounds
const MAG_MIN = -80, MAG_MAX = 40;
const PHASE_MIN = -270, PHASE_MAX = 0;

// ---- Magnitude chart datasets ----
const magDatasets = [
  {
    label: 'Magnitude',
    data: magData,
    borderColor: t.palette[0],
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 3
  },
  {
    label: '0 dB',
    data: [{ x: W_MIN, y: 0 }, { x: W_MAX, y: 0 }],
    borderColor: t.inkSoft,
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1,
    borderDash: [8, 5]
  }
];

if (gainCrossFreq !== null) {
  magDatasets.push({
    label: 'Phase margin',
    data: [{ x: gainCrossFreq, y: MAG_MIN }, { x: gainCrossFreq, y: MAG_MAX }],
    borderColor: t.palette[1],
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1.5,
    borderDash: [5, 5]
  });
}

if (phaseCrossFreq !== null) {
  magDatasets.push({
    label: 'Gain margin',
    data: [{ x: phaseCrossFreq, y: MAG_MIN }, { x: phaseCrossFreq, y: MAG_MAX }],
    borderColor: t.palette[2],
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1.5,
    borderDash: [5, 5]
  });
}

const magAnnotations = [];
if (gainCrossFreq !== null && phaseMargin !== null) {
  magAnnotations.push({
    xValue: gainCrossFreq,
    yValue: 8,
    text: 'PM = ' + phaseMargin.toFixed(1) + '°',
    color: t.palette[1],
    align: 'left',
    dx: 8,
    dy: 0
  });
}
if (phaseCrossFreq !== null && gainMargin !== null) {
  magAnnotations.push({
    xValue: phaseCrossFreq,
    yValue: -gainMargin / 2,
    text: 'GM = ' + gainMargin.toFixed(1) + ' dB',
    color: t.palette[2],
    align: 'left',
    dx: 8,
    dy: 0
  });
}

new Chart(magCanvas, {
  type: 'scatter',
  data: { datasets: magDatasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: 'bode-basic · javascript · chartjs · anyplot.ai',
        color: t.ink,
        font: { size: 22, weight: '500' },
        padding: { top: 12, bottom: 4 }
      },
      legend: { display: false },
      tooltip: { enabled: false }
    },
    scales: {
      x: Object.assign({}, logXBase, {
        ticks: Object.assign({}, logXBase.ticks, { display: false })
      }),
      y: {
        min: MAG_MIN,
        max: MAG_MAX,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: 'Magnitude (dB)', color: t.ink, font: { size: 16 } }
      }
    }
  },
  plugins: [makeMarginPlugin(magAnnotations)]
});

// ---- Phase chart datasets ----
const phaseDatasets = [
  {
    label: 'Phase',
    data: phaseData,
    borderColor: t.palette[0],
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 3
  },
  {
    label: '-180°',
    data: [{ x: W_MIN, y: -180 }, { x: W_MAX, y: -180 }],
    borderColor: t.inkSoft,
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1,
    borderDash: [8, 5]
  }
];

if (gainCrossFreq !== null) {
  phaseDatasets.push({
    label: 'Phase margin',
    data: [{ x: gainCrossFreq, y: PHASE_MIN }, { x: gainCrossFreq, y: PHASE_MAX }],
    borderColor: t.palette[1],
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1.5,
    borderDash: [5, 5]
  });
}

if (phaseCrossFreq !== null) {
  phaseDatasets.push({
    label: 'Gain margin',
    data: [{ x: phaseCrossFreq, y: PHASE_MIN }, { x: phaseCrossFreq, y: PHASE_MAX }],
    borderColor: t.palette[2],
    backgroundColor: 'transparent',
    showLine: true,
    pointRadius: 0,
    borderWidth: 1.5,
    borderDash: [5, 5]
  });
}

const phaseAnnotations = [];
if (gainCrossFreq !== null && phaseMargin !== null) {
  phaseAnnotations.push({
    xValue: gainCrossFreq,
    yValue: -180 + phaseMargin / 2,
    text: 'PM = ' + phaseMargin.toFixed(1) + '°',
    color: t.palette[1],
    align: 'left',
    dx: 8,
    dy: 0
  });
}
if (phaseCrossFreq !== null) {
  phaseAnnotations.push({
    xValue: phaseCrossFreq,
    yValue: -200,
    text: 'GM freq',
    color: t.palette[2],
    align: 'left',
    dx: 8,
    dy: 0
  });
}

new Chart(phaseCanvas, {
  type: 'scatter',
  data: { datasets: phaseDatasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: { display: false },
      legend: { display: false },
      tooltip: { enabled: false }
    },
    scales: {
      x: Object.assign({}, logXBase, {
        title: { display: true, text: 'Frequency (rad/s)', color: t.ink, font: { size: 16 } }
      }),
      y: {
        min: PHASE_MIN,
        max: PHASE_MAX,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: 'Phase (°)', color: t.ink, font: { size: 16 } }
      }
    }
  },
  plugins: [makeMarginPlugin(phaseAnnotations)]
});
