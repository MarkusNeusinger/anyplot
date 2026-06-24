// anyplot.ai
// line-reaction-coordinate: Reaction Coordinate Energy Diagram
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-24

const t = window.ANYPLOT_TOKENS;

// --- Data -------------------------------------------------------------------
// Single-step exothermic reaction: reactants=50 kJ/mol, TS=120 kJ/mol, products=20 kJ/mol
const POINTS = 200;
const curveData = [];
for (let i = 0; i <= POINTS; i++) {
  const x = i / POINTS;
  const base = 50 - 30 * x;
  const barrier = 85 * Math.exp(-0.5 * Math.pow((x - 0.5) / 0.15, 2));
  curveData.push({ x, y: parseFloat((base + barrier).toFixed(3)) });
}

// Dashed horizontal reference lines at reactant and product energy levels
const reactantRef = [{ x: 0, y: 50 }, { x: 0.28, y: 50 }];
const productRef  = [{ x: 0.72, y: 20 }, { x: 1.0, y: 20 }];

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Background plugin ------------------------------------------------------
const bgPlugin = {
  id: "bg",
  beforeDraw(chart) {
    const { ctx, width, height } = chart;
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, width, height);
    ctx.restore();
  },
};

// --- Arrow helper -----------------------------------------------------------
function arrowHead(ctx, fromX, fromY, toX, toY, size) {
  const angle = Math.atan2(toY - fromY, toX - fromX);
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(
    toX - size * Math.cos(angle - Math.PI / 6),
    toY - size * Math.sin(angle - Math.PI / 6)
  );
  ctx.lineTo(
    toX - size * Math.cos(angle + Math.PI / 6),
    toY - size * Math.sin(angle + Math.PI / 6)
  );
  ctx.closePath();
  ctx.fill();
}

// --- Annotation plugin: state labels + Ea and ΔH double-headed arrows ------
const annotPlugin = {
  id: "annot",
  afterDraw(chart) {
    const ctx = chart.ctx;
    const xS  = chart.scales.x;
    const yS  = chart.scales.y;
    const px  = (xv, yv) => ({ x: xS.getPixelForValue(xv), y: yS.getPixelForValue(yv) });

    ctx.save();
    ctx.fillStyle   = t.ink;
    ctx.strokeStyle = t.ink;

    // State labels
    ctx.font         = "bold 16px sans-serif";
    ctx.textAlign    = "center";
    ctx.textBaseline = "bottom";

    const rPos = px(0.06, 50);
    ctx.fillText("Reactants", rPos.x, rPos.y - 14);

    const tsPos = px(0.5, 120);
    ctx.fillText("Transition State ‡", tsPos.x, tsPos.y - 14);

    const pPos = px(0.94, 20);
    ctx.fillText("Products", pPos.x, pPos.y - 14);

    // Ea double-headed arrow (reactant energy level → transition state peak)
    const EA_X  = 0.34;
    const eaBot = px(EA_X, 50);
    const eaTop = px(EA_X, 120);

    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(eaBot.x, eaBot.y);
    ctx.lineTo(eaTop.x, eaTop.y);
    ctx.stroke();
    arrowHead(ctx, eaBot.x, eaBot.y, eaTop.x, eaTop.y, 9);
    arrowHead(ctx, eaTop.x, eaTop.y, eaBot.x, eaBot.y, 9);

    const eaMid = px(EA_X, 85);
    ctx.font         = "italic 16px sans-serif";
    ctx.textAlign    = "right";
    ctx.textBaseline = "middle";
    ctx.fillText("Ea = 70 kJ/mol", eaMid.x - 10, eaMid.y);

    // ΔH double-headed arrow (reactant energy level → product energy level)
    const DH_X  = 0.91;
    const dhTop = px(DH_X, 50);
    const dhBot = px(DH_X, 20);

    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(dhTop.x, dhTop.y);
    ctx.lineTo(dhBot.x, dhBot.y);
    ctx.stroke();
    arrowHead(ctx, dhBot.x, dhBot.y, dhTop.x, dhTop.y, 9);
    arrowHead(ctx, dhTop.x, dhTop.y, dhBot.x, dhBot.y, 9);

    const dhMid = px(DH_X, 35);
    ctx.font         = "italic 16px sans-serif";
    ctx.textAlign    = "left";
    ctx.textBaseline = "middle";
    ctx.fillText("ΔH = −30 kJ/mol", dhMid.x + 10, dhMid.y);

    ctx.restore();
  },
};

// --- Chart ------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  plugins: [bgPlugin, annotPlugin],
  data: {
    datasets: [
      {
        label: "Potential Energy",
        data: curveData,
        borderColor: t.palette[0],
        backgroundColor: "transparent",
        borderWidth: 3,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 0,
        fill: false,
      },
      {
        label: "Reactant level",
        data: reactantRef,
        borderColor: t.inkSoft,
        backgroundColor: "transparent",
        borderWidth: 1.5,
        borderDash: [10, 6],
        tension: 0,
        pointRadius: 0,
        pointHoverRadius: 0,
        fill: false,
      },
      {
        label: "Product level",
        data: productRef,
        borderColor: t.inkSoft,
        backgroundColor: "transparent",
        borderWidth: 1.5,
        borderDash: [10, 6],
        tension: 0,
        pointRadius: 0,
        pointHoverRadius: 0,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { top: 20, right: 140, bottom: 10, left: 10 },
    },
    plugins: {
      title: {
        display: true,
        text: "line-reaction-coordinate · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 20 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 1,
        title: {
          display: true,
          text: "Reaction Coordinate",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 8 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          maxTicksLimit: 6,
        },
        grid: { color: t.grid },
        border: { display: false },
      },
      y: {
        min: 0,
        max: 145,
        title: {
          display: true,
          text: "Potential Energy (kJ/mol)",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 8 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
        },
        grid: { color: t.grid },
        border: { display: false },
      },
    },
  },
});
