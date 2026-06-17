// anyplot.ai
// nyquist-basic: Nyquist Plot for Control Systems
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-17
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (deterministic Nyquist curve for a 3rd-order system) ---------------
// Transfer function: G(s) = 1 / (s(s+1)(s+2))
// G(jw) = 1 / (jw * (jw+1) * (jw+2))
// Denominator: D = jw*(1+jw)*(2+jw)
//   jw*(1+jw) = -w^2 + jw
//   (-w^2+jw)*(2+jw) = -3w^2 + j(2w - w^3)
// G(jw) = 1/D => multiply by conjugate: Re = -3w^2 / |D|^2, Im = -(2w-w^3)/|D|^2

function logspace(start, end, n) {
  const result = [];
  const logStart = Math.log10(start);
  const logEnd = Math.log10(end);
  for (let i = 0; i < n; i++) {
    result.push(Math.pow(10, logStart + (i / (n - 1)) * (logEnd - logStart)));
  }
  return result;
}

const freqs = logspace(0.01, 100, 500);
const realParts = [];
const imagParts = [];

for (let i = 0; i < freqs.length; i++) {
  const w = freqs[i];
  const denom = Math.pow(3 * w * w, 2) + Math.pow(2 * w - w * w * w, 2);
  realParts.push((-3 * w * w) / denom);
  imagParts.push(-(2 * w - w * w * w) / denom);
}

const curveData = realParts.map((r, i) => [r, imagParts[i]]);

// Unit circle (101 points)
const unitCircle = [];
for (let i = 0; i <= 100; i++) {
  const angle = (i / 100) * 2 * Math.PI;
  unitCircle.push([Math.cos(angle), Math.sin(angle)]);
}

// Frequency annotation points at key frequencies
const annotFreqs = [0.1, 0.5, 1.0, 2.0, 5.0];
const annotPoints = annotFreqs.map((fw) => {
  let bestIdx = 0;
  let bestDiff = Infinity;
  for (let i = 0; i < freqs.length; i++) {
    const diff = Math.abs(freqs[i] - fw);
    if (diff < bestDiff) { bestDiff = diff; bestIdx = i; }
  }
  return { freq: fw, re: realParts[bestIdx], im: imagParts[bestIdx] };
});

// Arrow direction indices (evenly spaced along visible curve segment)
const arrowIndices = [60, 150, 250];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: "nyquist-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 20, fontWeight: "bold" }
  },

  legend: {
    data: ["Nyquist Curve", "Unit Circle"],
    top: 60,
    left: "center",
    textStyle: { color: t.ink, fontSize: 14 },
    itemWidth: 22,
    itemHeight: 3,
  },

  grid: { left: 130, right: 80, top: 110, bottom: 110 },

  xAxis: {
    type: "value",
    name: "Real",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
    min: -2.0,
    max: 1.5,
  },

  yAxis: {
    type: "value",
    name: "Imaginary",
    nameLocation: "middle",
    nameGap: 65,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
    min: -1.75,
    max: 1.75,
  },

  tooltip: {
    trigger: "item",
    formatter: (params) => {
      if (params.seriesName === "Nyquist Curve") {
        return `Re: ${params.data[0].toFixed(4)}<br/>Im: ${params.data[1].toFixed(4)}`;
      }
      return "";
    },
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 13 }
  },

  series: [
    // Main Nyquist curve
    {
      name: "Nyquist Curve",
      type: "line",
      data: curveData,
      smooth: false,
      symbol: "none",
      lineStyle: { color: t.palette[0], width: 2.5 },
      emphasis: { disabled: true },
    },

    // Unit circle reference
    {
      name: "Unit Circle",
      type: "line",
      data: unitCircle,
      smooth: false,
      symbol: "none",
      lineStyle: { color: t.inkSoft, width: 1.5, type: "dashed", opacity: 0.55 },
      emphasis: { disabled: true },
    },

    // Critical point (-1, 0) — red diamond marker with label
    {
      name: "Critical Point",
      type: "scatter",
      data: [[-1, 0]],
      symbol: "diamond",
      symbolSize: 18,
      itemStyle: { color: t.palette[4], borderColor: t.palette[4], borderWidth: 2 },
      label: {
        show: true,
        formatter: "(-1, 0)",
        position: "right",
        color: t.palette[4],
        fontSize: 14,
        fontWeight: "bold",
        offset: [8, 0],
      },
      emphasis: { disabled: true },
    },

    // Frequency annotation markers with labels
    {
      name: "Frequency Markers",
      type: "scatter",
      data: annotPoints.map((pt) => [pt.re, pt.im]),
      symbol: "circle",
      symbolSize: 9,
      itemStyle: { color: t.palette[2], borderColor: t.pageBg, borderWidth: 1.5 },
      label: {
        show: true,
        formatter: (params) => `${annotPoints[params.dataIndex].freq} rad/s`,
        position: "top",
        color: t.inkSoft,
        fontSize: 12,
        offset: [0, -4],
      },
      emphasis: { disabled: true },
    },

    // Direction arrows showing increasing frequency
    {
      name: "Direction",
      type: "scatter",
      data: arrowIndices.map((idx) => curveData[idx]),
      symbol: "arrow",
      symbolSize: 13,
      symbolRotate: (value, params) => {
        const idx = arrowIndices[params.dataIndex];
        const dx = realParts[Math.min(idx + 2, freqs.length - 1)] - realParts[Math.max(idx - 2, 0)];
        const dy = imagParts[Math.min(idx + 2, freqs.length - 1)] - imagParts[Math.max(idx - 2, 0)];
        return (Math.atan2(dy, dx) * 180) / Math.PI;
      },
      itemStyle: { color: t.palette[0], opacity: 0.9 },
      emphasis: { disabled: true },
    },
  ],
});
