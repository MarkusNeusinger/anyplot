// anyplot.ai
// climograph-walter-lieth: Walter-Lieth Climate Diagram
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-15

const t = window.ANYPLOT_TOKENS;

// Barcelona, Spain — Mediterranean climate normal 1991–2020
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const temp   = [9.3, 10.2, 12.2, 14.4, 17.7, 21.4, 24.3, 24.5, 21.5, 17.3, 12.8, 9.7];
const precip = [46, 41, 47, 48, 52, 32, 20, 60, 79, 91, 62, 47];

// Walter-Lieth 1:2 axis convention: 10°C ↔ 20 mm
// Transform precipitation to temperature-equivalent units for plotting on shared axis
const precipNorm = precip.map(p => p / 2);

const annualTemp   = (temp.reduce((a, b) => a + b, 0) / 12).toFixed(1);
const annualPrecip = precip.reduce((a, b) => a + b, 0);

// Band fill data: humid where P_norm > T (blue), arid where T > P_norm (red)
const humidBase = temp.map((T, i) => Math.min(T, precipNorm[i]));
const humidFill = temp.map((T, i) => Math.max(0, precipNorm[i] - T));
const aridBase  = precipNorm.map((P, i) => Math.min(temp[i], P));
const aridFill  = temp.map((T, i) => Math.max(0, T - precipNorm[i]));

// Imprint palette — semantic exception: temperature = matte-red, precipitation = blue
const TEMP_COLOR   = '#AE3030'; // Imprint palette[4] matte-red — thermal/heat convention
const PRECIP_COLOR = '#4467A3'; // Imprint palette[2] blue — water/precipitation convention

const chart = echarts.init(document.getElementById('container'));

chart.setOption({
  animation: false,
  backgroundColor: 'transparent',

  title: {
    text: 'climograph-walter-lieth · javascript · echarts · anyplot.ai',
    left: 'center',
    top: 16,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 'bold' }
  },

  graphic: [
    {
      type: 'group',
      left: '8%',
      top: 66,
      children: [
        {
          type: 'text',
          style: { text: 'Barcelona', fontSize: 22, fontWeight: 'bold', fill: t.ink }
        },
        {
          type: 'text',
          top: 30,
          style: {
            text: `5 m a.s.l.  ·  ${annualTemp} °C  ·  ${annualPrecip} mm yr⁻¹`,
            fontSize: 15,
            fill: t.inkSoft
          }
        }
      ]
    }
  ],

  grid: { left: 95, right: 100, top: 135, bottom: 65 },

  xAxis: {
    type: 'category',
    data: months,
    boundaryGap: false,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false }
  },

  yAxis: [
    {
      // Left axis: temperature scale (°C)
      type: 'value',
      name: 'Temperature (°C)',
      nameLocation: 'middle',
      nameGap: 60,
      nameTextStyle: { color: TEMP_COLOR, fontSize: 14 },
      position: 'left',
      min: -10, max: 50, interval: 10,
      axisLabel: {
        color: TEMP_COLOR,
        fontSize: 13,
        formatter: v => v + '°'
      },
      axisLine: { show: true, lineStyle: { color: TEMP_COLOR } },
      axisTick: { lineStyle: { color: TEMP_COLOR } },
      splitLine: { lineStyle: { color: t.grid, type: 'solid' } }
    },
    {
      // Right axis: precipitation scale (mm), visually aligned via 10°C ↔ 20 mm rule
      type: 'value',
      name: 'Precipitation (mm)',
      nameLocation: 'middle',
      nameGap: 68,
      nameTextStyle: { color: PRECIP_COLOR, fontSize: 14 },
      position: 'right',
      min: -10, max: 50, interval: 10,
      axisLabel: {
        color: PRECIP_COLOR,
        fontSize: 13,
        formatter: v => v >= 0 ? (v * 2) + ' mm' : ''
      },
      axisLine: { show: true, lineStyle: { color: PRECIP_COLOR } },
      axisTick: { lineStyle: { color: PRECIP_COLOR } },
      splitLine: { show: false }
    }
  ],

  legend: {
    data: [
      { name: 'Temperature', icon: 'roundRect', itemStyle: { color: TEMP_COLOR } },
      { name: 'Precipitation', icon: 'roundRect', itemStyle: { color: PRECIP_COLOR } }
    ],
    top: 70,
    right: '8%',
    textStyle: { color: t.ink, fontSize: 14 }
  },

  tooltip: {
    trigger: 'axis',
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    textStyle: { color: t.ink, fontSize: 13 },
    formatter: params => {
      const month  = params[0] ? params[0].axisValue : '';
      const tParam = params.find(p => p.seriesName === 'Temperature');
      const pParam = params.find(p => p.seriesName === 'Precipitation');
      let html = `<b>${month}</b><br/>`;
      if (tParam) html += `${tParam.marker} Temp: ${tParam.value} °C<br/>`;
      if (pParam) html += `${pParam.marker} Precip: ${(pParam.value * 2).toFixed(0)} mm`;
      return html;
    }
  },

  series: [
    // Humid fill baseline — transparent area from axis floor up to min(T, P_norm)
    {
      name: '_humid_base',
      type: 'line',
      data: humidBase,
      yAxisIndex: 0,
      stack: 'humid',
      symbol: 'none',
      lineStyle: { width: 0 },
      areaStyle: { color: 'rgba(0,0,0,0)' },
      legendHoverLink: false,
      silent: true
    },
    // Humid fill — blue where precipitation exceeds temperature curve (humid period)
    {
      name: '_humid_fill',
      type: 'line',
      data: humidFill,
      yAxisIndex: 0,
      stack: 'humid',
      symbol: 'none',
      lineStyle: { width: 0 },
      areaStyle: { color: 'rgba(68,103,163,0.28)' },
      legendHoverLink: false,
      silent: true
    },
    // Arid fill baseline — transparent area from axis floor up to min(T, P_norm)
    {
      name: '_arid_base',
      type: 'line',
      data: aridBase,
      yAxisIndex: 0,
      stack: 'arid',
      symbol: 'none',
      lineStyle: { width: 0 },
      areaStyle: { color: 'rgba(0,0,0,0)' },
      legendHoverLink: false,
      silent: true
    },
    // Arid fill — red where temperature curve exceeds precipitation (arid/drought period)
    {
      name: '_arid_fill',
      type: 'line',
      data: aridFill,
      yAxisIndex: 0,
      stack: 'arid',
      symbol: 'none',
      lineStyle: { width: 0 },
      areaStyle: { color: 'rgba(174,48,48,0.25)' },
      legendHoverLink: false,
      silent: true
    },
    // Temperature line (red, left axis)
    {
      name: 'Temperature',
      type: 'line',
      data: temp,
      yAxisIndex: 0,
      lineStyle: { color: TEMP_COLOR, width: 3 },
      itemStyle: { color: TEMP_COLOR },
      symbol: 'circle',
      symbolSize: 7,
      z: 10,
      markLine: {
        silent: true,
        symbol: ['none', 'none'],
        data: [{ yAxis: 0 }],
        lineStyle: { color: t.inkSoft, type: 'dashed', width: 1, opacity: 0.4 },
        label: { show: false }
      }
    },
    // Precipitation line (blue, plotted as P/2 on temperature axis per Walter-Lieth convention)
    {
      name: 'Precipitation',
      type: 'line',
      data: precipNorm,
      yAxisIndex: 0,
      lineStyle: { color: PRECIP_COLOR, width: 3 },
      itemStyle: { color: PRECIP_COLOR },
      symbol: 'circle',
      symbolSize: 7,
      z: 10
    }
  ]
});
