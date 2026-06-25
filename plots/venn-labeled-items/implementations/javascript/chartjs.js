// anyplot.ai
// venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
// Library: chartjs 4.4.7 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;

// --- Data ------------------------------------------------------------------
const circles = [
  { name: "Hyped Online",     color: t.palette[0] },  // #009E73 — Imprint palette pos 1
  { name: "Actually Useful",  color: t.palette[1] },  // #C475FD — Imprint palette pos 2
  { name: "Secretly Beloved", color: t.palette[2] },  // #4467A3 — Imprint palette pos 3
];

const items = [
  { label: "NFTs",           zone: "A"   },
  { label: "Metaverse",      zone: "A"   },
  { label: "Spreadsheets",   zone: "B"   },
  { label: "Google Maps",    zone: "B"   },
  { label: "RSS Feeds",      zone: "C"   },
  { label: "Fax Machines",   zone: "C"   },
  { label: "ChatGPT",        zone: "AB"  },
  { label: "Slack",          zone: "AB"  },
  { label: "TikTok",         zone: "AC"  },
  { label: "Vinyl Records",  zone: "AC"  },
  { label: "Wikipedia",      zone: "BC"  },
  { label: "Duct Tape",      zone: "BC"  },
  { label: "The Internet",   zone: "ABC" },
  { label: "Coffee",         zone: "ABC" },
];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Venn drawing plugin ---------------------------------------------------
const vennPlugin = {
  id: "vennLabeled",
  afterDraw(chart) {
    const ctx = chart.ctx;
    const W = chart.width;
    const H = chart.height;

    // Background
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, W, H);

    // Layout geometry
    const cx = W * 0.5;
    const cy = H * 0.50;
    const r  = Math.min(W, H) * 0.32;
    const d  = r * 0.58;

    // Circle centers — equilateral-triangle arrangement
    const A = { x: cx - d * Math.cos(Math.PI / 6), y: cy - d * 0.55 };
    const B = { x: cx + d * Math.cos(Math.PI / 6), y: cy - d * 0.55 };
    const C = { x: cx,                               y: cy + d * 0.80 };
    const ctrs = [A, B, C];

    // Semi-transparent circle fills
    for (let i = 0; i < 3; i++) {
      ctx.save();
      ctx.globalAlpha = 0.21;
      ctx.beginPath();
      ctx.arc(ctrs[i].x, ctrs[i].y, r, 0, 2 * Math.PI);
      ctx.fillStyle = circles[i].color;
      ctx.fill();
      ctx.restore();
    }

    // Circle outlines
    for (let i = 0; i < 3; i++) {
      ctx.save();
      ctx.globalAlpha = 0.60;
      ctx.beginPath();
      ctx.arc(ctrs[i].x, ctrs[i].y, r, 0, 2 * Math.PI);
      ctx.strokeStyle = circles[i].color;
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.restore();
    }

    // Zone centers — verified to lie inside the correct regions
    const z = {
      A:   { x: A.x - r * 0.50, y: A.y - r * 0.20 },
      B:   { x: B.x + r * 0.50, y: B.y - r * 0.20 },
      C:   { x: cx,              y: C.y + r * 0.40  },
      AB:  { x: cx,              y: cy - d * 1.10   },
      AC:  { x: cx - d * 0.75,  y: cy + d * 0.30   },
      BC:  { x: cx + d * 0.75,  y: cy + d * 0.30   },
      ABC: { x: cx,              y: cy              },
    };

    // Category name labels (outside each circle)
    const catFontSize = Math.round(r * 0.13);
    ctx.font = `bold ${catFontSize}px Georgia, serif`;
    ctx.textBaseline = "middle";
    const catPos = [
      { x: A.x - r * 0.95, y: A.y - r * 0.68, align: "center" },
      { x: B.x + r * 0.95, y: B.y - r * 0.68, align: "center" },
      { x: cx,              y: C.y + r * 1.05,  align: "center" },
    ];
    for (let i = 0; i < 3; i++) {
      ctx.fillStyle = circles[i].color;
      ctx.textAlign = catPos[i].align;
      ctx.fillText(circles[i].name, catPos[i].x, catPos[i].y);
    }

    // Group items by zone
    const byZone = {};
    for (const item of items) {
      (byZone[item.zone] = byZone[item.zone] || []).push(item.label);
    }

    // Item labels inside each zone
    const itemFontSize = Math.round(r * 0.095);
    const lineH = itemFontSize * 1.65;
    ctx.font = `${itemFontSize}px Georgia, serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = t.inkSoft;

    for (const [zone, labels] of Object.entries(byZone)) {
      const base = z[zone];
      if (!base) continue;
      const startY = base.y - ((labels.length - 1) * lineH) / 2;
      for (let i = 0; i < labels.length; i++) {
        ctx.fillText(labels[i], base.x, startY + i * lineH);
      }
    }

    // Title (scaled for length)
    const titleText = "Tech Zeitgeist · venn-labeled-items · javascript · chartjs · anyplot.ai";
    const titleSize = Math.max(12, Math.round(22 * 67 / titleText.length));
    ctx.font = `bold ${titleSize}px Georgia, serif`;
    ctx.fillStyle = t.ink;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(titleText, W / 2, H * 0.022);

    // Subtitle
    const subtitleSize = Math.max(10, Math.round(titleSize * 0.72));
    ctx.font = `italic ${subtitleSize}px Georgia, serif`;
    ctx.fillStyle = t.inkSoft;
    ctx.fillText("Where does it live — hype, utility, or quiet devotion?", W / 2, H * 0.022 + titleSize * 1.5);
  },
};

// --- Chart (blank scatter used as canvas container + custom Venn plugin) ---
new Chart(canvas, {
  type: "scatter",
  data: { datasets: [] },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 0 },
    plugins: {
      legend: { display: false },
      title:  { display: false },
    },
    scales: {
      x: { display: false },
      y: { display: false },
    },
  },
  plugins: [vennPlugin],
});
