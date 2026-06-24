// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-24
//# anyplot-orientation: square

// anyplot.ai
// heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-24

const t = window.ANYPLOT_TOKENS;

// Pitch classes ordered C to B
const pitchClasses = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const numFrames = 80;
const framesPerChord = 20;

// C–G–Am–F progression (indices into pitchClasses)
// C major: C(0), E(4), G(7)
// G major: D(2), G(7), B(11)
// A minor: C(0), E(4), A(9)
// F major: C(0), F(5), A(9)
const progression = [
  [0, 4, 7],
  [2, 7, 11],
  [0, 4, 9],
  [0, 5, 9],
];

// Deterministic LCG for reproducible noise (seed 42)
let seed = 42;
const lcg = () => {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
};

// Build chromagram: [frameIdx, pitchClassIdx, energy]
const chromaData = [];
for (let f = 0; f < numFrames; f++) {
  const chordTones = progression[Math.floor(f / framesPerChord)];
  for (let p = 0; p < 12; p++) {
    const isChordTone = chordTones.includes(p);
    const energy = isChordTone ? 0.55 + lcg() * 0.45 : lcg() * 0.18;
    chromaData.push([f, p, parseFloat(energy.toFixed(3))]);
  }
}

// X-axis labels: show seconds only at chord boundaries (every 20 frames = 1 second)
const timeLabels = Array.from({ length: numFrames }, (_, i) =>
  i % 20 === 0 ? `${(i * 0.05).toFixed(1)}s` : ""
);

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: {
    text: "heatmap-chromagram · javascript · echarts · anyplot.ai",
    subtext: "C–G–Am–F chord progression  |  4 seconds, 80 analysis frames",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
    subtextStyle: { color: t.inkSoft, fontSize: 14 },
  },

  grid: { left: 82, right: 118, top: 100, bottom: 80 },

  xAxis: {
    type: "category",
    data: timeLabels,
    name: "Time (seconds)",
    nameLocation: "middle",
    nameGap: 44,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13, interval: 0 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },

  yAxis: {
    type: "category",
    data: pitchClasses,
    name: "Pitch Class",
    nameLocation: "middle",
    nameGap: 58,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },

  visualMap: {
    min: 0,
    max: 1,
    calculable: false,
    orient: "vertical",
    right: 18,
    top: "center",
    itemWidth: 22,
    itemHeight: 220,
    inRange: { color: t.seq },
    text: ["High", "Low"],
    textGap: 8,
    textStyle: { color: t.inkSoft, fontSize: 13 },
    outOfRange: { color: t.pageBg },
  },

  series: [
    {
      type: "heatmap",
      data: chromaData,
      itemStyle: {
        borderWidth: 0.5,
        borderColor: t.pageBg,
      },
      emphasis: { disabled: true },
    },
  ],
});
