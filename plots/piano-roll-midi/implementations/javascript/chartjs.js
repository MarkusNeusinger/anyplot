// anyplot.ai
// piano-roll-midi: MIDI Piano Roll Visualization
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 82/100 | Created: 2026-06-03

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

// Note name helpers
const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const pitchName = (p) => NOTE_NAMES[p % 12] + (Math.floor(p / 12) - 1);
const isBlackKey = (p) => [1, 3, 6, 8, 10].includes(p % 12);

// Imprint sequential colormap: green (#009E73) → blue (#4467A3) for velocity
const lerpColor = (hex1, hex2, ratio) => {
  const parse = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const [r1, g1, b1] = parse(hex1);
  const [r2, g2, b2] = parse(hex2);
  return [Math.round(r1 + (r2 - r1) * ratio), Math.round(g1 + (g2 - g1) * ratio), Math.round(b1 + (b2 - b1) * ratio)];
};

// MIDI data: 8-measure classical phrase in C major (4/4 time, 32 beats total)
// Fields: start (beat), duration (beats), pitch (MIDI number), velocity (0–127)
const notes = [
  // Measure 1: C major — rising arpeggio melody over held bass 5th
  { start: 0,    duration: 4,    pitch: 48, velocity: 72 },  // C3 whole
  { start: 0,    duration: 4,    pitch: 55, velocity: 68 },  // G3 whole
  { start: 0,    duration: 0.5,  pitch: 60, velocity: 90 },  // C4
  { start: 0.5,  duration: 0.5,  pitch: 64, velocity: 82 },  // E4
  { start: 1,    duration: 0.5,  pitch: 67, velocity: 87 },  // G4
  { start: 1.5,  duration: 0.5,  pitch: 72, velocity: 93 },  // C5
  { start: 2,    duration: 0.5,  pitch: 74, velocity: 98 },  // D5
  { start: 2.5,  duration: 0.5,  pitch: 72, velocity: 88 },  // C5
  { start: 3,    duration: 0.5,  pitch: 69, velocity: 82 },  // A4
  { start: 3.5,  duration: 0.5,  pitch: 67, velocity: 77 },  // G4

  // Measure 2: A minor — stepwise melody with lyrical shaping
  { start: 4,    duration: 4,    pitch: 45, velocity: 70 },  // A2 whole
  { start: 4,    duration: 4,    pitch: 52, velocity: 65 },  // E3 whole
  { start: 4,    duration: 0.5,  pitch: 64, velocity: 83 },  // E4
  { start: 4.5,  duration: 0.5,  pitch: 65, velocity: 78 },  // F4
  { start: 5,    duration: 0.5,  pitch: 67, velocity: 86 },  // G4
  { start: 5.5,  duration: 0.5,  pitch: 69, velocity: 91 },  // A4
  { start: 6,    duration: 1,    pitch: 72, velocity: 94 },  // C5 quarter
  { start: 7,    duration: 0.5,  pitch: 69, velocity: 80 },  // A4
  { start: 7.5,  duration: 0.5,  pitch: 67, velocity: 74 },  // G4

  // Measure 3: F major — wider leap to high register
  { start: 8,    duration: 4,    pitch: 41, velocity: 73 },  // F2 whole
  { start: 8,    duration: 4,    pitch: 53, velocity: 68 },  // F3 whole
  { start: 8,    duration: 0.5,  pitch: 65, velocity: 87 },  // F4
  { start: 8.5,  duration: 0.5,  pitch: 67, velocity: 82 },  // G4
  { start: 9,    duration: 0.5,  pitch: 69, velocity: 89 },  // A4
  { start: 9.5,  duration: 0.5,  pitch: 72, velocity: 84 },  // C5
  { start: 10,   duration: 1,    pitch: 74, velocity: 96 },  // D5 quarter
  { start: 11,   duration: 0.5,  pitch: 72, velocity: 84 },  // C5
  { start: 11.5, duration: 0.5,  pitch: 69, velocity: 76 },  // A4

  // Measure 4: G dominant — leading tone tension to first climax
  { start: 12,   duration: 4,    pitch: 43, velocity: 78 },  // G2 whole
  { start: 12,   duration: 4,    pitch: 50, velocity: 70 },  // D3 whole
  { start: 12,   duration: 1,    pitch: 67, velocity: 88 },  // G4 quarter
  { start: 13,   duration: 0.5,  pitch: 69, velocity: 84 },  // A4
  { start: 13.5, duration: 0.5,  pitch: 71, velocity: 87 },  // B4
  { start: 14,   duration: 1,    pitch: 72, velocity: 100 }, // C5 — forte
  { start: 15,   duration: 1,    pitch: 71, velocity: 79 },  // B4 quarter

  // Measure 5: C major — harmonized dyads (parallel 3rds)
  { start: 16,   duration: 4,    pitch: 48, velocity: 68 },  // C3 whole
  { start: 16,   duration: 4,    pitch: 55, velocity: 63 },  // G3 whole
  { start: 16,   duration: 1,    pitch: 60, velocity: 83 },  // C4 with E4
  { start: 16,   duration: 1,    pitch: 64, velocity: 80 },  // E4
  { start: 17,   duration: 1,    pitch: 64, velocity: 78 },  // E4 with G4
  { start: 17,   duration: 1,    pitch: 67, velocity: 76 },  // G4
  { start: 18,   duration: 2,    pitch: 67, velocity: 86 },  // G4 half with C5
  { start: 18,   duration: 2,    pitch: 72, velocity: 84 },  // C5

  // Measure 6: A minor — 16th-note ornament + descending close
  { start: 20,   duration: 4,    pitch: 45, velocity: 66 },  // A2 whole
  { start: 20,   duration: 4,    pitch: 52, velocity: 62 },  // E3 whole
  { start: 20,   duration: 0.25, pitch: 72, velocity: 92 },  // C5 16th
  { start: 20.25,duration: 0.25, pitch: 74, velocity: 88 },  // D5 16th
  { start: 20.5, duration: 0.25, pitch: 72, velocity: 85 },  // C5 16th
  { start: 20.75,duration: 0.25, pitch: 69, velocity: 80 },  // A4 16th
  { start: 21,   duration: 0.5,  pitch: 67, velocity: 83 },  // G4
  { start: 21.5, duration: 0.5,  pitch: 65, velocity: 78 },  // F4
  { start: 22,   duration: 1,    pitch: 64, velocity: 82 },  // E4 quarter
  { start: 23,   duration: 1,    pitch: 60, velocity: 72 },  // C4 quarter

  // Measure 7: F → G — building intensity toward final climax
  { start: 24,   duration: 2,    pitch: 41, velocity: 78 },  // F2 half
  { start: 24,   duration: 2,    pitch: 53, velocity: 73 },  // F3 half
  { start: 26,   duration: 2,    pitch: 43, velocity: 83 },  // G2 half
  { start: 26,   duration: 2,    pitch: 50, velocity: 76 },  // D3 half
  { start: 24,   duration: 0.5,  pitch: 69, velocity: 88 },  // A4
  { start: 24.5, duration: 0.5,  pitch: 71, velocity: 92 },  // B4
  { start: 25,   duration: 0.5,  pitch: 72, velocity: 96 },  // C5
  { start: 25.5, duration: 0.5,  pitch: 74, velocity: 100 }, // D5
  { start: 26,   duration: 1,    pitch: 76, velocity: 105 }, // E5 — peak
  { start: 27,   duration: 0.5,  pitch: 74, velocity: 93 },  // D5
  { start: 27.5, duration: 0.5,  pitch: 72, velocity: 87 },  // C5

  // Measure 8: C major — descending resolution over final chord
  { start: 28,   duration: 4,    pitch: 48, velocity: 83 },  // C3 whole
  { start: 28,   duration: 4,    pitch: 55, velocity: 78 },  // G3 whole
  { start: 28,   duration: 4,    pitch: 60, velocity: 72 },  // C4 whole (chord)
  { start: 28,   duration: 0.5,  pitch: 72, velocity: 88 },  // C5
  { start: 28.5, duration: 0.5,  pitch: 71, velocity: 84 },  // B4
  { start: 29,   duration: 0.5,  pitch: 69, velocity: 80 },  // A4
  { start: 29.5, duration: 0.5,  pitch: 67, velocity: 75 },  // G4
  { start: 30,   duration: 2,    pitch: 64, velocity: 82 },  // E4 half
  { start: 30,   duration: 2,    pitch: 67, velocity: 80 },  // G4 half (chord)
  { start: 30,   duration: 2,    pitch: 72, velocity: 86 },  // C5 half (chord)
];

// Pitch display range with margins
const MIN_PITCH = Math.min(...notes.map((n) => n.pitch)) - 1;
const MAX_PITCH = Math.max(...notes.map((n) => n.pitch)) + 1;
const MIN_VEL = Math.min(...notes.map((n) => n.velocity));
const MAX_VEL = Math.max(...notes.map((n) => n.velocity));

// Velocity → rgba: hue shifts green→blue, alpha scales with loudness (soft=60%, loud=100%)
const velColor = (vel) => {
  const ratio = (vel - MIN_VEL) / (MAX_VEL - MIN_VEL);
  const [r, g, b] = lerpColor(t.seq[0], t.seq[1], ratio);
  const alpha = (0.60 + 0.40 * ratio).toFixed(2);
  return `rgba(${r},${g},${b},${alpha})`;
};

// Integer bounds so stepSize:1 generates integer ticks (non-integer min+stepSize = non-integer ticks)
const DISPLAY_MIN = MIN_PITCH - 1;
const DISPLAY_MAX = MAX_PITCH + 1;

// Mount
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

// Custom plugin: piano key backgrounds + beat grid + note rectangles
const pianoRollPlugin = {
  id: 'pianoRoll',
  beforeDraw(chart) {
    const { ctx, chartArea: { left, right, top, bottom }, scales: { x, y } } = chart;

    // Black key row shading
    for (let p = Math.floor(y.min); p <= Math.ceil(y.max); p++) {
      if (isBlackKey(p)) {
        const rowTop = y.getPixelForValue(p + 0.5);
        const rowBottom = y.getPixelForValue(p - 0.5);
        ctx.fillStyle = THEME === 'light'
          ? 'rgba(26,26,23,0.07)'
          : 'rgba(240,239,232,0.07)';
        ctx.fillRect(left, rowTop, right - left, rowBottom - rowTop);
      }
    }

    // Beat gridlines (between measure boundaries)
    ctx.lineWidth = 0.5;
    ctx.strokeStyle = THEME === 'light'
      ? 'rgba(26,26,23,0.10)'
      : 'rgba(240,239,232,0.10)';
    for (let beat = 1; beat < 32; beat++) {
      if (beat % 4 !== 0) {
        const px = x.getPixelForValue(beat);
        ctx.beginPath();
        ctx.moveTo(px, top);
        ctx.lineTo(px, bottom);
        ctx.stroke();
      }
    }

    // Measure boundary lines (stronger)
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = THEME === 'light'
      ? 'rgba(26,26,23,0.22)'
      : 'rgba(240,239,232,0.22)';
    for (let m = 0; m <= 8; m++) {
      const px = x.getPixelForValue(m * 4);
      ctx.beginPath();
      ctx.moveTo(px, top);
      ctx.lineTo(px, bottom);
      ctx.stroke();
    }
  },
  afterDraw(chart) {
    const { ctx, chartArea: { left, right }, scales: { x, y } } = chart;
    const borderCol = THEME === 'light' ? 'rgba(0,0,0,0.30)' : 'rgba(0,0,0,0.55)';

    notes.forEach((note) => {
      const x1 = x.getPixelForValue(note.start) + 1;
      const x2 = x.getPixelForValue(note.start + note.duration) - 1;
      const y1 = y.getPixelForValue(note.pitch + 0.38);
      const y2 = y.getPixelForValue(note.pitch - 0.38);
      const nw = Math.max(x2 - x1, 2);
      const nh = y2 - y1;

      ctx.fillStyle = velColor(note.velocity);
      ctx.fillRect(x1, y1, nw, nh);
      ctx.strokeStyle = borderCol;
      ctx.lineWidth = 0.5;
      ctx.strokeRect(x1, y1, nw, nh);
    });

    // --- Velocity colorbar ---
    const cbW = right - left;
    const cbH = 16;
    const cbTop = chart.height - 52;

    const grad = ctx.createLinearGradient(left, 0, left + cbW, 0);
    grad.addColorStop(0, t.seq[0]);
    grad.addColorStop(1, t.seq[1]);
    ctx.fillStyle = grad;
    ctx.fillRect(left, cbTop, cbW, cbH);
    ctx.strokeStyle = THEME === 'light' ? 'rgba(26,26,23,0.20)' : 'rgba(240,239,232,0.20)';
    ctx.lineWidth = 0.5;
    ctx.strokeRect(left, cbTop, cbW, cbH);

    // Labels: "ppp" left, title center, "fff" right
    const labelY = cbTop + cbH + 5;
    ctx.fillStyle = t.inkSoft;
    ctx.font = '12px sans-serif';
    ctx.textBaseline = 'top';
    ctx.textAlign = 'left';
    ctx.fillText('ppp', left, labelY);
    ctx.textAlign = 'center';
    ctx.fillText('Velocity (dynamics)', left + cbW / 2, labelY);
    ctx.textAlign = 'right';
    ctx.fillText('fff', left + cbW, labelY);
  },
};

// Title length scaling (per plot-generator.md)
const title = 'piano-roll-midi · javascript · chartjs · anyplot.ai';
const titleSize = Math.max(18, Math.round(22 * Math.min(1, 67 / title.length)));

new Chart(canvas, {
  type: 'scatter',
  // Invisible anchor points force Chart.js to initialize the scales and generate ticks
  data: {
    datasets: [{
      data: [{ x: 0, y: DISPLAY_MIN }, { x: 32, y: DISPLAY_MAX }],
      pointRadius: 0,
      borderWidth: 0,
      backgroundColor: 'transparent',
    }],
  },
  plugins: [pianoRollPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 16, right: 32, bottom: 65, left: 0 } },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: titleSize },
        padding: { bottom: 14 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: 'linear',
        min: 0,
        max: 32,
        grid: { display: false },
        border: { color: t.inkSoft },
        ticks: {
          stepSize: 4,
          callback: (val) => (val % 4 === 0 && val < 32) ? `M${val / 4 + 1}` : null,
          color: t.inkSoft,
          font: { size: 14 },
          maxRotation: 0,
          autoSkip: false,
        },
        title: {
          display: true,
          text: 'Time (Measures, 4/4)',
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        type: 'linear',
        min: DISPLAY_MIN,
        max: DISPLAY_MAX,
        grid: { display: false },
        border: { color: t.inkSoft },
        ticks: {
          stepSize: 1,
          callback: (val) => (Number.isInteger(val) && !isBlackKey(val)) ? pitchName(val) : null,
          color: t.inkSoft,
          font: { size: 13 },
          autoSkip: false,
          maxTicksLimit: 100,
        },
        title: {
          display: true,
          text: 'Pitch',
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
