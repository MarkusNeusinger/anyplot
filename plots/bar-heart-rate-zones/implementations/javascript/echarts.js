// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-14

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

// Semantic zone colors mapped to Imprint palette
// Fitness-platform convention (grey→blue→green→ochre→red) is a widely-shared
// expectation — the semantic exception in default-style-guide.md applies here.
const Z1_GREY = THEME === "light" ? "#6B6A63" : "#A8A79F"; // Imprint muted
const zoneColors = [
  Z1_GREY,    // Z1 Recovery  — muted grey (lowest intensity)
  "#4467A3",  // Z2 Endurance — Imprint blue (pos 3)
  "#009E73",  // Z3 Aerobic   — Imprint green (pos 1, brand)
  "#BD8233",  // Z4 Threshold — Imprint ochre (pos 4, nearest orange)
  "#AE3030",  // Z5 Maximum   — Imprint red (pos 5, semantic high-effort)
];

// Data — 60-minute tempo run (polarized training example)
const zoneNames  = ["Z1\nRecovery", "Z2\nEndurance", "Z3\nAerobic", "Z4\nThreshold", "Z5\nMaximum"];
const hrRanges   = ["< 111 bpm", "111–130 bpm", "130–148 bpm", "148–167 bpm", "> 167 bpm"];
const minutes    = [8, 22, 15, 12, 3];

const barData = minutes.map((m, i) => ({
  value: m,
  itemStyle: { color: zoneColors[i] },
}));

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: {
    text: "bar-heart-rate-zones · javascript · echarts · anyplot.ai",
    subtext: "60-min Tempo Run  ·  Total: 60 min  ·  Max HR: 185 bpm",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
    subtextStyle: { color: t.inkSoft, fontSize: 14 },
  },

  tooltip: {
    trigger: "axis",
    axisPointer: { type: "none" },
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 14 },
    formatter: (params) => {
      const idx = params[0].dataIndex;
      return (
        `<b>${zoneNames[idx].replace("\n", " ")}</b><br/>` +
        `Duration: <b>${minutes[idx]} min</b><br/>` +
        `HR range: ${hrRanges[idx]}`
      );
    },
  },

  grid: {
    left: 90,
    right: 60,
    top: 118,
    bottom: 165,
  },

  xAxis: {
    type: "category",
    data: zoneNames,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      lineHeight: 21,
      margin: 14,
      // Add HR boundary range as a third line below zone name
      formatter: (value, index) => `${value}\n{hr|${hrRanges[index]}}`,
      rich: {
        hr: { color: t.inkSoft, fontSize: 11, align: "center" },
      },
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
  },

  yAxis: {
    type: "value",
    name: "Time (minutes)",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 15 },
    min: 0,
    max: 27,
    axisLabel: {
      color: t.inkSoft,
      fontSize: 14,
      formatter: "{value}",
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: t.grid } },
  },

  series: [
    {
      type: "bar",
      data: barData,
      barWidth: "52%",
      itemStyle: { borderRadius: [4, 4, 0, 0] },
      label: {
        show: true,
        position: "top",
        formatter: (params) => `${params.value} min`,
        color: t.ink,
        fontSize: 16,
        fontWeight: "bold",
        distance: 8,
      },
      // Highlight Z4+Z5 as the high-intensity tempo-run signature
      markArea: {
        silent: true,
        data: [
          [
            {
              xAxis: "Z4\nThreshold",
              itemStyle: {
                color: THEME === "light"
                  ? "rgba(174, 48, 48, 0.07)"
                  : "rgba(174, 48, 48, 0.13)",
              },
              label: {
                show: true,
                formatter: "High Intensity",
                position: "insideTop",
                color: t.inkSoft,
                fontSize: 11,
                fontStyle: "italic",
                distance: 8,
              },
            },
            { xAxis: "Z5\nMaximum" },
          ],
        ],
      },
    },
  ],
});
