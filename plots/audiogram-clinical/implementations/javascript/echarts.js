// anyplot.ai
// audiogram-clinical: Clinical Audiogram
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-15

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Data — noise-induced high-frequency sensorineural notch (classic 4 kHz dip)
const freqLabels = ["125", "250", "500", "1k", "2k", "4k", "8k"];

// Right ear (O markers, red) — 4 kHz notch, thresholds in dB HL
const rightThresholds = [15, 15, 20, 25, 35, 60, 50];
// Left ear (X markers, blue) — similar pattern, slightly asymmetric
const leftThresholds  = [10, 15, 25, 30, 45, 65, 55];

// Clinical convention: right=red, left=blue (semantic exception from canonical palette order)
const RED  = "#AE3030";  // Imprint matte red — right ear
const BLUE = "#4467A3";  // Imprint steel blue — left ear

// Severity grading bands (WHO/ASHA, dB HL ranges)
const severityBands = [
  { name: "Normal (≤25 dB)",       yMin: -10, yMax: 25,  fill: "rgba(0,158,115,0.07)"   },
  { name: "Mild (26–40 dB)",        yMin: 25,  yMax: 40,  fill: "rgba(189,130,51,0.09)"  },
  { name: "Moderate (41–55 dB)",    yMin: 40,  yMax: 55,  fill: "rgba(221,204,119,0.12)" },
  { name: "Mod. Severe (56–70 dB)", yMin: 55,  yMax: 70,  fill: "rgba(196,117,253,0.09)" },
  { name: "Severe (71–90 dB)",      yMin: 70,  yMax: 90,  fill: "rgba(174,48,48,0.09)"   },
  { name: "Profound (>90 dB)",      yMin: 90,  yMax: 120, fill: "rgba(68,103,163,0.10)"  },
];

// X-cross symbol: two diagonal strokes — faithful to clinical audiogram convention
const crossPath = "path://M-8,-8 L8,8 M8,-8 L-8,8";

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: "audiogram-clinical · javascript · echarts · anyplot.ai",
    left: "center",
    top: 28,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
  },

  legend: {
    data: ["Right Ear (O)", "Left Ear (X)"],
    bottom: 32,
    itemGap: 40,
    textStyle: { color: t.ink, fontSize: 16 },
  },

  grid: {
    left: 100,
    right: 50,
    top: 100,
    bottom: 140,
  },

  xAxis: {
    type: "category",
    data: freqLabels,
    name: "Frequency (Hz)",
    nameLocation: "middle",
    nameGap: 52,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },

  yAxis: {
    type: "value",
    inverse: true,
    min: -10,
    max: 120,
    interval: 10,
    name: "Hearing Level (dB HL)",
    nameLocation: "middle",
    nameGap: 68,
    nameRotate: 90,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: "{value}" },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },

  series: [
    {
      name: "Right Ear (O)",
      type: "line",
      data: rightThresholds,
      symbol: "circle",
      symbolSize: 16,
      lineStyle: { color: RED, width: 2.5 },
      itemStyle: { color: "transparent", borderColor: RED, borderWidth: 2.5 },
      markArea: {
        silent: true,
        itemStyle: { borderWidth: 0 },
        data: severityBands.map(b => [
          {
            yAxis: b.yMin,
            itemStyle: { color: b.fill },
            label: {
              show: true,
              position: "insideTopRight",
              color: t.inkSoft,
              fontSize: 12,
              formatter: b.name,
            },
          },
          { yAxis: b.yMax },
        ]),
      },
    },
    {
      name: "Left Ear (X)",
      type: "line",
      data: leftThresholds,
      symbol: crossPath,
      symbolSize: 20,
      lineStyle: { color: BLUE, width: 2.5, type: "dashed" },
      itemStyle: { color: "transparent", borderColor: BLUE, borderWidth: 2.5 },
    },
  ],
});
