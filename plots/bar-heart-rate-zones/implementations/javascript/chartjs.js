// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 92/100 | Created: 2026-06-14
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const isDark = window.ANYPLOT_THEME === 'dark';

// Zone semantic colors: conventional HR zone palette mapped to Imprint anchors
// Z1=grey(muted anchor), Z2=blue(#4467A3), Z3=green(brand #009E73),
// Z4=ochre(#BD8233), Z5=red(#AE3030)
const ZONE_COLORS = [
  isDark ? '#A8A79F' : '#6B6A63',
  '#4467A3',
  '#009E73',
  '#BD8233',
  '#AE3030',
];

// Data: 60-minute threshold run (tempo session)
const labels = [
  ['Z1 Recovery', '< 115 bpm'],
  ['Z2 Endurance', '115–135 bpm'],
  ['Z3 Aerobic', '135–155 bpm'],
  ['Z4 Threshold', '155–170 bpm'],
  ['Z5 Maximum', '> 170 bpm'],
];
const minutes = [5, 18, 20, 14, 3];
const yMax = Math.ceil(Math.max(...minutes) * 1.3 / 5) * 5;

// Mount canvas
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

// Plugin: fill canvas background with theme surface color
const bgPlugin = {
  id: 'canvasBg',
  beforeDraw(chart) {
    const ctx = chart.ctx;
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, chart.width, chart.height);
    ctx.restore();
  },
};

// Plugin: duration labels above each bar
const valueLabelPlugin = {
  id: 'valueLabels',
  afterDatasetsDraw(chart) {
    const ctx = chart.ctx;
    const meta = chart.getDatasetMeta(0);
    meta.data.forEach((bar, idx) => {
      const val = minutes[idx];
      ctx.save();
      ctx.fillStyle = t.ink;
      ctx.font = 'bold 16px system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(`${val} min`, bar.x, bar.y - 8);
      ctx.restore();
    });
  },
};

new Chart(canvas, {
  type: 'bar',
  data: {
    labels,
    datasets: [{
      label: 'Time in Zone',
      data: minutes,
      backgroundColor: ZONE_COLORS,
      borderWidth: 0,
      borderRadius: 6,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 40, right: 60, bottom: 20, left: 20 } },
    plugins: {
      title: {
        display: true,
        text: 'bar-heart-rate-zones · javascript · chartjs · anyplot.ai',
        color: t.ink,
        font: { size: 22, weight: 'bold' },
        padding: { top: 16, bottom: 6 },
      },
      subtitle: {
        display: true,
        text: '60-Minute Threshold Run',
        color: t.inkSoft,
        font: { size: 16, style: 'italic' },
        padding: { bottom: 24 },
      },
      legend: { display: false },
      tooltip: { enabled: true },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          maxRotation: 0,
        },
        grid: { display: false },
        border: { color: t.grid },
      },
      y: {
        title: {
          display: true,
          text: 'Time (minutes)',
          color: t.ink,
          font: { size: 16 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 5,
        },
        grid: { color: t.grid },
        border: { display: false },
        beginAtZero: true,
        max: yMax,
      },
    },
  },
  plugins: [bgPlugin, valueLabelPlugin],
});
