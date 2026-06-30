// anyplot.ai
// area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
// Library: chartjs 4.4.7 | JavaScript 22.23.0
// Quality: 88/100 | Created: 2026-06-30
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const theme = window.ANYPLOT_THEME;

// --- Data: Valais Alps panorama from Gornergrat, sweeping W to E ----------
// Piecewise-linear ridgeline control points [bearing_deg, elevation_m]
// Sharp triangular flanks with explicit saddle control points between peaks
const ctrlPts = [
  [0, 3100], [5, 3300], [8, 3550],
  [12, 4506],  // Weisshorn
  [15, 3800], [17, 3350], [19, 3150],
  [20, 4221],  // Zinalrothorn
  [22, 3700], [25, 3050], [27, 3150],
  [30, 4063],  // Ober Gabelhorn
  [33, 3600], [36, 3200],
  [40, 4358],  // Dent Blanche
  [44, 3500], [47, 3100], [52, 2950], [56, 3200],
  [58, 3650],
  [60, 4478],  // Matterhorn (focal summit)
  [62, 3800], [65, 3100], [68, 2900], [72, 3050],
  [75, 3600], [78, 3850],
  [80, 4164],  // Breithorn
  [84, 3800], [87, 3650],
  [90, 4092],  // Pollux
  [93, 3900],
  [95, 4223],  // Castor
  [98, 3900], [102, 3700],
  [105, 4527], // Liskamm
  [109, 4100], [113, 3800],
  [120, 4634], // Monte Rosa / Dufourspitze (highest)
  [126, 4000], [129, 3700],
  [135, 4190], // Strahlhorn
  [138, 3700], [140, 3500],
  [142, 4199], // Rimpfischhorn
  [145, 3650], [148, 3400],
  [150, 4027], // Allalinhorn
  [153, 3700],
  [158, 4206], // Alphubel
  [161, 3800], [164, 3700],
  [168, 4545], // Dom
  [171, 4350],
  [175, 4491], // Täschhorn
  [177, 4000], [180, 3100],
];

function lerpElev(angle) {
  for (let i = 0; i < ctrlPts.length - 1; i++) {
    const [a0, e0] = ctrlPts[i];
    const [a1, e1] = ctrlPts[i + 1];
    if (angle >= a0 && angle <= a1) {
      return e0 + ((angle - a0) / (a1 - a0)) * (e1 - e0);
    }
  }
  return ctrlPts[0][1];
}

// Deterministic sine-hash noise — avoids Math.random() non-reproducibility
function sinNoise(i, salt) {
  const v = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
  return v - Math.floor(v);
}

const N     = 720;
const Y_MIN = 2500;
const Y_MAX = 5100;
const mainPts = [];
const bgPts   = [];

for (let i = 0; i < N; i++) {
  const angle  = (i / (N - 1)) * 180;
  const base   = lerpElev(angle);
  const noise  = (sinNoise(i, 1) - 0.5) * 50;
  mainPts.push({ x: angle, y: Math.max(Y_MIN, Math.round(base + noise)) });

  // Background (distance) ridge: scaled lower for atmospheric depth
  const bgNoise = (sinNoise(i, 7) - 0.5) * 80;
  bgPts.push({ x: angle, y: Math.max(Y_MIN, Math.round(base * 0.70 + 780 + bgNoise)) });
}

// Annotated summits — staggered yOff (px above summit) to prevent overlap
const summits = [
  { name: "Weisshorn",      angle: 12,  elev: 4506, yOff: 72  },
  { name: "Zinalrothorn",   angle: 20,  elev: 4221, yOff: 102 },
  { name: "Ober Gabelhorn", angle: 30,  elev: 4063, yOff: 72  },
  { name: "Dent Blanche",   angle: 40,  elev: 4358, yOff: 108 },
  { name: "Matterhorn",     angle: 60,  elev: 4478, yOff: 55  },
  { name: "Breithorn",      angle: 80,  elev: 4164, yOff: 82  },
  { name: "Liskamm",        angle: 105, elev: 4527, yOff: 68  },
  { name: "Monte Rosa",     angle: 120, elev: 4634, yOff: 55  },
  { name: "Rimpfischhorn",  angle: 142, elev: 4199, yOff: 90  },
  { name: "Alphubel",       angle: 158, elev: 4206, yOff: 72  },
  { name: "Dom",            angle: 168, elev: 4545, yOff: 55  },
  { name: "Täschhorn",      angle: 175, elev: 4491, yOff: 87  },
];

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Theme colors -----------------------------------------------------------
const skyHigh  = theme === 'light' ? '#2e6fa8' : '#080d1f';
const skyMid   = theme === 'light' ? '#7fb3d8' : '#0f1a36';
const skyLow   = theme === 'light' ? '#d6eaf8' : '#1A1A17';
const mtFill   = theme === 'light' ? 'rgba(26,24,20,0.94)' : 'rgba(10,9,7,0.96)';
const bgFill   = theme === 'light' ? 'rgba(95,115,135,0.28)' : 'rgba(30,45,65,0.36)';
const dotColor = t.palette[0];  // #009E73 brand green — summit markers

// --- Plugins ----------------------------------------------------------------
const skyPlugin = {
  id: 'skyGradient',
  // beforeDraw ensures gradient is under gridlines and dataset fills
  beforeDraw(chart) {
    const { ctx, chartArea: { left, top, right, bottom } } = chart;
    const g = ctx.createLinearGradient(0, top, 0, bottom);
    g.addColorStop(0,    skyHigh);
    g.addColorStop(0.42, skyMid);
    g.addColorStop(1,    skyLow);
    ctx.save();
    ctx.fillStyle = g;
    ctx.fillRect(left, top, right - left, bottom - top);
    ctx.restore();
  },
};

const annotPlugin = {
  id: 'peakAnnotations',
  afterDraw(chart) {
    const { ctx, scales: { x: xSc, y: ySc } } = chart;
    ctx.save();
    ctx.textAlign = 'center';

    summits.forEach((s) => {
      const px = xSc.getPixelForValue(s.angle);
      const py = ySc.getPixelForValue(s.elev);
      const ly = py - s.yOff;  // label baseline y (above summit dot)

      // Dashed leader line from just above dot to just below elevation label
      ctx.strokeStyle = 'rgba(250,248,241,0.48)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.moveTo(px, py - 6);
      ctx.lineTo(px, ly + 16);
      ctx.stroke();
      ctx.setLineDash([]);

      // Summit dot (brand green Imprint position 1)
      ctx.fillStyle = dotColor;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fill();

      // Peak name
      ctx.fillStyle = '#FAF8F1';
      ctx.font = 'bold 13px system-ui, sans-serif';
      ctx.fillText(s.name, px, ly);

      // Elevation in meters below name
      ctx.font = '11px system-ui, sans-serif';
      ctx.fillStyle = 'rgba(250,248,241,0.80)';
      ctx.fillText(`${s.elev.toLocaleString()} m`, px, ly + 15);
    });

    ctx.restore();
  },
};

// --- Chart ------------------------------------------------------------------
const TITLE = "area-mountain-panorama · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: 'line',
  data: {
    datasets: [
      {
        label: 'Background Ridge',
        data: bgPts,
        parsing: false,
        fill: 'start',
        backgroundColor: bgFill,
        borderColor: 'transparent',
        borderWidth: 0,
        pointRadius: 0,
        tension: 0,
      },
      {
        label: 'Main Ridgeline',
        data: mainPts,
        parsing: false,
        fill: 'start',
        backgroundColor: mtFill,
        borderColor: theme === 'light' ? 'rgba(195,208,220,0.40)' : 'rgba(70,85,105,0.40)',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0,
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
        font: { size: 22 },
        padding: { top: 10, bottom: 6 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: 'linear',
        min: 0,
        max: 180,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          stepSize: 30,
          callback: (v) => ({ 0: 'W', 30: 'WSW', 60: 'SW', 90: 'S', 120: 'SSE', 150: 'SE', 180: 'E' })[v] || `${v}°`,
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: 'Bearing — Panorama from Gornergrat',
          color: t.ink,
          font: { size: 14 },
        },
      },
      y: {
        min: Y_MIN,
        max: Y_MAX,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          callback: (v) => `${v.toLocaleString()} m`,
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: 'Elevation (m)',
          color: t.ink,
          font: { size: 14 },
        },
      },
    },
  },
  plugins: [skyPlugin, annotPlugin],
});
