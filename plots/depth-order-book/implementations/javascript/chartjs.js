// anyplot.ai
// depth-order-book: Order Book Depth Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-15

const t = window.ANYPLOT_TOKENS;

// --- Data: BTC/USD order book snapshot, mid price $60,000 ---
const MID = 60000;
const BEST_BID = 59995;
const BEST_ASK = 60005;
const SPREAD = BEST_ASK - BEST_BID;
const TICK = 10;
const N = 50;

// XORshift LCG — deterministic, seed 42
let _s = 42;
function rng() {
  _s ^= _s << 13;
  _s ^= _s >> 17;
  _s ^= _s << 5;
  return (_s >>> 0) / 4294967296;
}

// Bid levels: index 0 = worst bid (lowest price), index N-1 = best bid
const bidLevels = [];
for (let i = 0; i < N; i++) {
  const price = BEST_BID - (N - 1 - i) * TICK;
  const distTicks = N - 1 - i; // 0 at best bid, N-1 at worst
  const base = 0.25 + (distTicks / N) * 1.8;
  const wall = (distTicks === 15 || distTicks === 32) ? 3.0 + rng() * 2.0 : 0;
  bidLevels.push({ price, qty: base * (0.6 + rng() * 0.7) + wall });
}

// Cumulate bid from best bid outward (index N-1 → 0)
let cBid = 0;
for (let i = N - 1; i >= 0; i--) {
  cBid += bidLevels[i].qty;
  bidLevels[i].cum = cBid;
}
const bidData = bidLevels.map(l => ({ x: l.price, y: l.cum }));

// Ask levels: index 0 = best ask (lowest price), index N-1 = worst ask
const askLevels = [];
for (let i = 0; i < N; i++) {
  const price = BEST_ASK + i * TICK;
  const distTicks = i; // 0 at best ask, N-1 at worst
  const base = 0.25 + (distTicks / N) * 1.8;
  const wall = (distTicks === 15 || distTicks === 32) ? 3.0 + rng() * 2.0 : 0;
  askLevels.push({ price, qty: base * (0.6 + rng() * 0.7) + wall });
}

// Cumulate ask from best ask outward (index 0 → N-1)
let cAsk = 0;
for (let i = 0; i < N; i++) {
  cAsk += askLevels[i].qty;
  askLevels[i].cum = cAsk;
}
const askData = askLevels.map(l => ({ x: l.price, y: l.cum }));

// --- Mount ---
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

// --- Plugins ---
const bgPlugin = {
  id: 'bgPlugin',
  beforeDraw(chart) {
    chart.ctx.save();
    chart.ctx.fillStyle = t.pageBg;
    chart.ctx.fillRect(0, 0, chart.width, chart.height);
    chart.ctx.restore();
  },
};

const midLinePlugin = {
  id: 'midLinePlugin',
  afterDatasetsDraw(chart) {
    const { ctx, scales: { x: xs, y: ys } } = chart;
    const mx = xs.getPixelForValue(MID);

    // Dashed vertical line at mid price
    ctx.save();
    ctx.setLineDash([10, 7]);
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(mx, ys.top);
    ctx.lineTo(mx, ys.bottom);
    ctx.stroke();
    ctx.restore();

    // Mid price and spread labels
    ctx.save();
    ctx.textAlign = 'center';
    ctx.font = 'bold 14px sans-serif';
    ctx.fillStyle = t.ink;
    ctx.fillText('$' + MID.toLocaleString(), mx, ys.top + 26);
    ctx.font = '13px sans-serif';
    ctx.fillStyle = t.inkSoft;
    ctx.fillText('Spread: $' + SPREAD.toFixed(2), mx, ys.top + 46);
    ctx.restore();
  },
};

// --- Chart ---
new Chart(canvas, {
  type: 'line',
  data: {
    datasets: [
      {
        label: 'Bids (Buy)',
        data: bidData,
        stepped: 'before',
        fill: 'origin',
        backgroundColor: 'rgba(0,158,115,0.28)',
        borderColor: t.palette[0],
        borderWidth: 2.5,
        pointRadius: 0,
      },
      {
        label: 'Asks (Sell)',
        data: askData,
        stepped: 'before',
        fill: 'origin',
        backgroundColor: 'rgba(174,48,48,0.28)',
        borderColor: t.palette[4],
        borderWidth: 2.5,
        pointRadius: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    plugins: {
      title: {
        display: true,
        text: 'depth-order-book · javascript · chartjs · anyplot.ai',
        color: t.ink,
        font: { size: 22, weight: '500' },
        padding: { top: 20, bottom: 16 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          boxWidth: 24,
          padding: 20,
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        min: BEST_BID - (N - 1) * TICK - 60,
        max: BEST_ASK + (N - 1) * TICK + 60,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: v => '$' + Number(v).toLocaleString(),
          maxTicksLimit: 11,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: 'Price (USD)',
          color: t.ink,
          font: { size: 16 },
          padding: { top: 10 },
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: v => Number(v).toFixed(1) + ' BTC',
          maxTicksLimit: 8,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: 'Cumulative Volume (BTC)',
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 10 },
        },
      },
    },
  },
  plugins: [bgPlugin, midLinePlugin],
});
