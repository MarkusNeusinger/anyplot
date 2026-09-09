// anyplot.ai
// spectrum-basic: Frequency Spectrum Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Synthetic vibration signal: three characteristic machinery frequencies
// (running speed 60 Hz, gear mesh 240 Hz, bearing fault 850 Hz) plus a
// 1/f-shaped noise floor, expressed as a power spectrum in dB.
const SAMPLE_RATE = 4096;
const NUM_BINS = 1024;
const PEAKS = [
  { freq: 60, amplitude: 1.0, width: 3 },
  { freq: 240, amplitude: 0.55, width: 5 },
  { freq: 850, amplitude: 0.32, width: 9 },
];

// Tiny fixed-seed LCG for reproducible pseudo-noise.
let lcgState = 42;
function nextRandom() {
  lcgState = (lcgState * 1103515245 + 12345) % 2147483648;
  return lcgState / 2147483648;
}

const frequencies = [];
const amplitudesDb = [];
for (let i = 1; i < NUM_BINS; i += 1) {
  const freq = (i / NUM_BINS) * (SAMPLE_RATE / 2);
  let magnitude = 0.02 + 0.6 / freq; // 1/f-shaped noise floor
  for (const peak of PEAKS) {
    const distance = (freq - peak.freq) / peak.width;
    magnitude += peak.amplitude * Math.exp(-distance * distance);
  }
  magnitude *= 1 + (nextRandom() - 0.5) * 0.08; // small measurement jitter
  frequencies.push(Math.round(freq * 10) / 10);
  amplitudesDb.push(Math.round(20 * Math.log10(magnitude) * 10) / 10);
}

const dominantIndices = PEAKS.map((peak) => {
  let closest = 0;
  let closestDist = Infinity;
  frequencies.forEach((f, idx) => {
    const dist = Math.abs(f - peak.freq);
    if (dist < closestDist) {
      closestDist = dist;
      closest = idx;
    }
  });
  return closest;
});

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "Machinery Vibration Spectrum · spectrum-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: 18, fontWeight: 500 },
  },
  grid: { left: 90, right: 60, top: 100, bottom: 90 },
  xAxis: {
    type: "log",
    name: "Frequency (Hz)",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    min: 4,
    max: 2048,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: true, lineStyle: { color: t.grid } },
  },
  yAxis: {
    type: "value",
    name: "Power (dB)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      type: "line",
      name: "Power spectrum",
      data: frequencies.map((f, idx) => [f, amplitudesDb[idx]]),
      showSymbol: false,
      lineStyle: { color: t.palette[0], width: 2 },
      areaStyle: { color: t.palette[0], opacity: 0.15, origin: "start" },
    },
    {
      type: "scatter",
      name: "Dominant frequencies",
      data: dominantIndices.map((idx) => [frequencies[idx], amplitudesDb[idx]]),
      symbolSize: 14,
      itemStyle: {
        color: "transparent",
        borderColor: t.palette[4],
        borderWidth: 2.5,
      },
    },
  ],
});
