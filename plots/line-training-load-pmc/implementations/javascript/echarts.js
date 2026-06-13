// anyplot.ai
// line-training-load-pmc: Training Load Performance Management Chart
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-13

const t = window.ANYPLOT_TOKENS;

// Deterministic data (xorshift RNG — no Math.random())
let seed = 12345;
const rand = () => {
  seed ^= seed << 13;
  seed ^= seed >> 17;
  seed ^= seed << 5;
  return (seed >>> 0) / 0x100000000;
};

// Generate 180 days starting Dec 16 2025, ending ~Jun 13 2026
const N = 180;
const dates = [];
const tssArr = [];
const ctlArr = [];
const atlArr = [];
const tsbArr = [];

let ctl = 38;
let atl = 42;

for (let i = 0; i < N; i++) {
  const d = new Date(2025, 11, 16 + i); // Dec 16 2025 + i days (JS handles overflow)
  dates.push(d.toLocaleDateString("en-US", { month: "short", day: "numeric" }));

  // TSB = yesterday's CTL - yesterday's ATL (form going into the day)
  tsbArr.push(+(ctl - atl).toFixed(1));

  // Training phase determines TSS distribution
  const phase = i / N;
  const dow = d.getDay(); // 0 = Sunday

  let tss = 0;
  if (dow !== 0) {
    const r = rand();
    const restChance = dow === 6 ? 0.3 : 0.15;
    if (r >= restChance) {
      let baseTSS;
      if (phase < 0.35) {
        baseTSS = 55 + phase * 70;           // base build: 55 → 79
      } else if (phase < 0.65) {
        baseTSS = 79 + (phase - 0.35) * 130; // intensity: 79 → 118
      } else if (phase < 0.82) {
        baseTSS = 118 + (phase - 0.65) * 30; // peak: 118 → 123
      } else {
        baseTSS = 123 * Math.max(0.22, 1 - (phase - 0.82) * 4.3); // taper
      }
      tss = Math.round(baseTSS * (0.65 + rand() * 0.70));
    } else {
      rand(); // consume RNG slot to keep sequence consistent
    }
  }

  tssArr.push(tss);

  // EWMA: CTL ≈ 42-day constant, ATL ≈ 7-day constant
  ctl = ctl + (tss - ctl) / 42;
  atl = atl + (tss - atl) / 7;
  ctlArr.push(+ctl.toFixed(1));
  atlArr.push(+atl.toFixed(1));
}

// Two-tone TSB: positive clipped to [0, ∞) and negative clipped to (-∞, 0]
// This avoids visualMap piecewise (which has coord-access issues with category axes)
const tsbPos = tsbArr.map(v => Math.max(v, 0));
const tsbNeg = tsbArr.map(v => Math.min(v, 0));
const zeroLine = tsbArr.map(() => 0);

const chart = echarts.init(document.getElementById("container"));

const titleText =
  "Training Load PMC · line-training-load-pmc · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * 67 / titleText.length));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: {
    text: titleText,
    left: "center",
    top: 14,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: "bold" },
  },

  legend: {
    data: ["Fitness (CTL)", "Fatigue (ATL)", "Form (TSB)", "Daily TSS"],
    bottom: 14,
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemWidth: 24,
    itemHeight: 12,
  },

  grid: { left: 80, right: 90, top: 80, bottom: 62 },

  xAxis: {
    type: "category",
    data: dates,
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 13, interval: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },

  yAxis: [
    {
      // Primary — CTL, ATL, raw TSS bars
      name: "Load (TSS units)",
      nameTextStyle: { color: t.inkSoft, fontSize: 13, padding: [0, 0, 6, 44] },
      type: "value",
      min: 0,
      max: 185,
      axisLabel: { color: t.inkSoft, fontSize: 13 },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } },
    },
    {
      // Secondary — TSB oscillates around zero
      name: "Form (TSB)",
      nameTextStyle: { color: t.inkSoft, fontSize: 13, padding: [0, 36, 6, 0] },
      type: "value",
      position: "right",
      axisLabel: { color: t.inkSoft, fontSize: 13 },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      axisTick: { show: false },
      splitLine: { show: false },
    },
  ],

  series: [
    // --- Primary axis series ---
    {
      name: "Fitness (CTL)",
      type: "line",
      data: ctlArr,
      smooth: 0.4,
      symbol: "none",
      lineStyle: { width: 3.5, color: t.palette[2] }, // blue — long-term fitness
      itemStyle: { color: t.palette[2] },
      yAxisIndex: 0,
      z: 5,
    },
    {
      name: "Fatigue (ATL)",
      type: "line",
      data: atlArr,
      smooth: 0.3,
      symbol: "none",
      lineStyle: { width: 2.5, color: t.palette[1] }, // purple — acute fatigue
      itemStyle: { color: t.palette[1] },
      yAxisIndex: 0,
      z: 4,
    },
    {
      // Raw daily training load — muted vertical bars
      name: "Daily TSS",
      type: "bar",
      data: tssArr,
      yAxisIndex: 0,
      barMaxWidth: 4,
      itemStyle: { color: t.inkSoft, opacity: 0.35 },
      z: 1,
    },

    // --- Secondary axis: TSB two-tone area ---
    {
      // TSB zero baseline
      name: "_tsb_zero",
      type: "line",
      data: zeroLine,
      symbol: "none",
      lineStyle: { width: 1, color: t.inkSoft, opacity: 0.55 },
      itemStyle: { color: t.inkSoft },
      yAxisIndex: 1,
      z: 2,
      legendHoverLink: false,
      tooltip: { show: false },
    },
    {
      // Positive TSB (fresh / peak form) — brand green fill
      name: "Form (TSB)",
      type: "line",
      data: tsbPos,
      smooth: 0.4,
      symbol: "none",
      lineStyle: { width: 0 },
      areaStyle: { color: t.palette[0], opacity: 0.45 }, // green
      itemStyle: { color: t.palette[0] },
      yAxisIndex: 1,
      z: 3,
    },
    {
      // Negative TSB (fatigued) — matte red fill; shares legend entry via same name trick
      name: "_tsb_neg",
      type: "line",
      data: tsbNeg,
      smooth: 0.4,
      symbol: "none",
      lineStyle: { width: 0 },
      areaStyle: { color: "#AE3030", opacity: 0.40 }, // matte red
      itemStyle: { color: "#AE3030" },
      yAxisIndex: 1,
      z: 3,
      legendHoverLink: false,
      tooltip: { show: false },
    },
  ],
});
