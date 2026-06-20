// anyplot.ai
// line-parametric: Parametric Curve Plot
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 82/100 | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// Linearly interpolate between two hex colors
function lerpHex(hex1, hex2, f) {
  const p = (h) => [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
  const [a, b] = [p(hex1), p(hex2)];
  return `rgb(${Math.round(a[0]+(b[0]-a[0])*f)},${Math.round(a[1]+(b[1]-a[1])*f)},${Math.round(a[2]+(b[2]-a[2])*f)})`;
}

// --- Data -------------------------------------------------------------------

// Lissajous figure: x = sin(3t), y = sin(2t), t ∈ [0, 2π]
const N_LISS = 1200;
const lissPoints = Array.from({ length: N_LISS }, (_, i) => {
  const ti = (i / (N_LISS - 1)) * 2 * Math.PI;
  return [Math.sin(3 * ti), Math.sin(2 * ti)];
});

// Archimedean spiral: x = t·cos(t), y = t·sin(t), t ∈ [0, 4π]
const N_SPIRAL = 1200;
const spiralPoints = Array.from({ length: N_SPIRAL }, (_, i) => {
  const ti = (i / (N_SPIRAL - 1)) * 4 * Math.PI;
  return [ti * Math.cos(ti), ti * Math.sin(ti)];
});
const spiralEnd = spiralPoints[N_SPIRAL - 1];

// --- Imprint palette (cool → warm gradient per curve) ----------------------
const C_LISS_START = t.palette[0];  // #009E73 brand green — cool start
const C_LISS_END   = t.palette[3];  // #BD8233 ochre       — warm end
const C_SPIR_START = t.palette[2];  // #4467A3 blue        — cool start
const C_SPIR_END   = t.palette[1];  // #C475FD lavender    — warm end

// --- Chart ------------------------------------------------------------------
const chart = echarts.init(document.getElementById('container'));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: 'transparent',

  title: [
    {
      text: 'line-parametric · javascript · echarts · anyplot.ai',
      left: 'center',
      top: 14,
      textStyle: { color: t.ink, fontSize: 22, fontWeight: 'bold' }
    },
    {
      text: 'Lissajous Figure\nx = sin(3t)  y = sin(2t)',
      left: 90,
      top: 58,
      textStyle: { color: t.inkSoft, fontSize: 13, lineHeight: 20 }
    },
    {
      text: 'Archimedean Spiral\nx = t·cos(t)  y = t·sin(t)',
      left: 870,
      top: 58,
      textStyle: { color: t.inkSoft, fontSize: 13, lineHeight: 20 }
    }
  ],

  // Two square 670×670 CSS-px plot areas side by side on a 1600×900 mount
  grid: [
    { left: 90,  right: 840, top: 150, bottom: 80 },
    { left: 870, right: 60,  top: 150, bottom: 80 }
  ],

  xAxis: [
    {
      gridIndex: 0,
      type: 'value',
      name: 'x(t)',
      nameLocation: 'center',
      nameGap: 36,
      nameTextStyle: { color: t.inkSoft, fontSize: 14 },
      min: -1.2,
      max: 1.2,
      axisLabel: { color: t.inkSoft, fontSize: 11 },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } }
    },
    {
      gridIndex: 1,
      type: 'value',
      name: 'x(t)',
      nameLocation: 'center',
      nameGap: 36,
      nameTextStyle: { color: t.inkSoft, fontSize: 14 },
      min: -14,
      max: 14,
      axisLabel: { color: t.inkSoft, fontSize: 11 },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } }
    }
  ],

  yAxis: [
    {
      gridIndex: 0,
      type: 'value',
      name: 'y(t)',
      nameLocation: 'center',
      nameGap: 46,
      nameTextStyle: { color: t.inkSoft, fontSize: 14 },
      min: -1.2,
      max: 1.2,
      axisLabel: { color: t.inkSoft, fontSize: 11 },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } }
    },
    {
      gridIndex: 1,
      type: 'value',
      name: 'y(t)',
      nameLocation: 'center',
      nameGap: 46,
      nameTextStyle: { color: t.inkSoft, fontSize: 14 },
      min: -14,
      max: 14,
      axisLabel: { color: t.inkSoft, fontSize: 11 },
      axisLine: { show: true, lineStyle: { color: t.inkSoft } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: t.grid } }
    }
  ],

  series: [
    // Lissajous curve — scatter points simulate a gradient-colored line
    {
      type: 'scatter',
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: lissPoints,
      symbolSize: 4,
      itemStyle: {
        color: (params) => lerpHex(C_LISS_START, C_LISS_END, params.dataIndex / (N_LISS - 1))
      },
      z: 2
    },
    // Lissajous origin marker — closed curve: t=0 and t=2π both pass through (0,0)
    {
      type: 'scatter',
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: [[0, 0]],
      symbolSize: 18,
      itemStyle: { color: C_LISS_START, borderColor: t.ink, borderWidth: 2 },
      label: {
        show: true,
        formatter: 't = 0, 2π',
        position: 'top',
        color: t.inkSoft,
        fontSize: 12
      },
      z: 4
    },

    // Archimedean spiral — cool-blue to warm-lavender gradient
    {
      type: 'scatter',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: spiralPoints,
      symbolSize: 4,
      itemStyle: {
        color: (params) => lerpHex(C_SPIR_START, C_SPIR_END, params.dataIndex / (N_SPIRAL - 1))
      },
      z: 2
    },
    // Spiral start marker at origin
    {
      type: 'scatter',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: [[0, 0]],
      symbolSize: 18,
      itemStyle: { color: C_SPIR_START, borderColor: t.ink, borderWidth: 2 },
      label: {
        show: true,
        formatter: 't = 0',
        position: 'right',
        color: t.inkSoft,
        fontSize: 12
      },
      z: 4
    },
    // Spiral end marker at t = 4π
    {
      type: 'scatter',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: [spiralEnd],
      symbolSize: 14,
      symbol: 'diamond',
      itemStyle: { color: C_SPIR_END },
      label: {
        show: true,
        formatter: 't = 4π',
        position: 'top',
        color: t.inkSoft,
        fontSize: 12
      },
      z: 4
    }
  ]
});
