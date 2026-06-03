// anyplot.ai
// spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-03

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic 1H NMR of Ethanol (CH3-CH2-OH) at 300 MHz ---
// CH3 triplet ~1.17 ppm, CH2 quartet ~3.69 ppm, OH broad singlet ~2.61 ppm, TMS at 0.00
const nPts = 6001;
const ppmLo = -0.5;
const ppmHi = 12.0;
const J = 7 / 300; // 7 Hz coupling constant → 0.0233 ppm at 300 MHz

function lorentz(x, x0, amp, hw) {
  return amp * hw * hw / ((x - x0) * (x - x0) + hw * hw);
}

const lw = 0.008; // sharp Lorentzian linewidth (ppm half-width)
const specData = [];
for (let i = 0; i < nPts; i++) {
  const ppm = ppmLo + i * (ppmHi - ppmLo) / (nPts - 1);
  let y = 0;
  // TMS reference singlet (0.00 ppm)
  y += lorentz(ppm, 0.00, 20, lw);
  // CH3 triplet: 1:2:1 intensity ratio, J = 7 Hz
  y += lorentz(ppm, 1.17 - J, 40, lw);
  y += lorentz(ppm, 1.17,     80, lw);
  y += lorentz(ppm, 1.17 + J, 40, lw);
  // OH broad singlet (exchangeable proton, broadened by H-bonding)
  y += lorentz(ppm, 2.61, 28, 0.055);
  // CH2 quartet: 1:3:3:1 intensity ratio, J = 7 Hz
  y += lorentz(ppm, 3.69 - 1.5 * J, 26, lw);
  y += lorentz(ppm, 3.69 - 0.5 * J, 78, lw);
  y += lorentz(ppm, 3.69 + 0.5 * J, 78, lw);
  y += lorentz(ppm, 3.69 + 1.5 * J, 26, lw);
  specData.push([parseFloat(ppm.toFixed(4)), parseFloat(y.toFixed(3))]);
}

// --- Init ---
const chart = echarts.init(document.getElementById("container"));

// --- Option ---
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: "spectrum-nmr · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "500" },
  },

  grid: { left: 90, right: 60, top: 110, bottom: 90 },

  xAxis: {
    type: "value",
    inverse: true,
    min: ppmLo,
    max: ppmHi,
    interval: 1,
    name: "Chemical Shift (ppm)",
    nameLocation: "middle",
    nameGap: 55,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },

  yAxis: {
    type: "value",
    name: "Intensity (a.u.)",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: -4,
    max: 96,
    axisLabel: { show: false },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },

  series: [
    {
      type: "line",
      data: specData,
      showSymbol: false,
      lineStyle: { color: t.palette[0], width: 2 },
      areaStyle: {
        color: {
          type: "linear",
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: t.palette[0] + "30" },
            { offset: 1, color: t.palette[0] + "06" },
          ],
        },
      },
      markPoint: {
        symbol: "circle",
        symbolSize: 7,
        itemStyle: { color: t.palette[0] },
        label: {
          show: true,
          position: "top",
          distance: 10,
          fontSize: 13,
          fontWeight: "500",
          color: t.ink,
          formatter: "{b}",
        },
        data: [
          { name: "TMS (0.00 ppm)", coord: [0.00, 20] },
          { name: "CH₃ (1.17 ppm)", coord: [1.17, 80] },
          { name: "OH (2.61 ppm)", coord: [2.61, 28] },
          { name: "CH₂ (3.69 ppm)", coord: [3.69 - 0.5 * J, 78] },
        ],
      },
    },
  ],
});
