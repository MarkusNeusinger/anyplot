// anyplot.ai
// venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-25
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Geometry (CSS px in 1200×1200 mount → 2400×2400 PNG at dpr=2) ---------
// Three-circle Venn: equilateral triangle arrangement, R=225, D=145 from centroid
// Diagram shifted down ~90px vs initial to vertically center on the canvas
const R   = 225;
const cAx = 600, cAy = 515;   // Overhyped      (top)
const cBx = 474, cBy = 733;   // Actually Useful (bottom-left)
const cCx = 726, cCy = 733;   // Secretly Loved  (bottom-right)

// --- Data -------------------------------------------------------------------
// Zone item placement centers — each verified to sit inside the correct region(s)
//   A-only : dist<R from A, dist>R from B and C
//   AB-only : dist<R from A and B, dist>R from C
//   ABC    : dist<R from all three
const ITEM_FS = 14;   // item font size (CSS px)
const ITEM_LS = 24;   // vertical line spacing

const zoneData = [
  { x: 600, y: 398, items: ['NFTs', 'Metaverse', 'Web3'] },           // A only
  { x: 370, y: 818, items: ['Google Maps', 'Spreadsheets', 'Git'] },  // B only
  { x: 830, y: 818, items: ['Wikipedia', 'RSS Feeds', 'Notepad'] },   // C only
  { x: 500, y: 565, items: ['AI Assistants', 'Cloud Storage'] },      // AB only
  { x: 700, y: 565, items: ['Twitter / X', 'Crypto Wallets'] },       // AC only
  { x: 600, y: 816, items: ['Linux Terminal', 'Plain Text'] },        // BC only
  { x: 600, y: 658, items: ['Markdown'] },                            // ABC
];

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById('container'));

// --- Graphic elements -------------------------------------------------------

// Semi-transparent overlapping circles (Imprint palette, positions 1-3)
const circleGraphics = [
  { cx: cAx, cy: cAy, stroke: '#009E73', fill: 'rgba(0,158,115,0.18)' },
  { cx: cBx, cy: cBy, stroke: '#C475FD', fill: 'rgba(196,117,253,0.18)' },
  { cx: cCx, cy: cCy, stroke: '#4467A3', fill: 'rgba(68,103,163,0.18)' },
].map(c => ({
  type: 'circle',
  shape: { cx: c.cx, cy: c.cy, r: R },
  style: { fill: c.fill, stroke: c.stroke, lineWidth: 2.5 },
  z: 5,
}));

// Category labels outside each circle — serif for editorial feel
const catLabelGraphics = [
  { text: 'Overhyped',       x: 600, y: 256, color: '#009E73' },
  { text: 'Actually Useful', x: 330, y: 985, color: '#C475FD' },
  { text: 'Secretly Loved',  x: 870, y: 985, color: '#4467A3' },
].map(l => ({
  type: 'text',
  z: 20,
  style: {
    text: l.text,
    x: l.x,
    y: l.y,
    textAlign: 'center',
    textVerticalAlign: 'middle',
    fill: l.color,
    fontSize: 17,
    fontWeight: 'bold',
    fontFamily: 'Georgia, "Times New Roman", serif',
  },
}));

// Item labels — stacked vertically within each zone center
const itemGraphics = [];
zoneData.forEach(zone => {
  const n = zone.items.length;
  zone.items.forEach((item, i) => {
    itemGraphics.push({
      type: 'text',
      z: 20,
      style: {
        text: '· ' + item,
        x: zone.x,
        y: zone.y + (i - (n - 1) / 2) * ITEM_LS,
        textAlign: 'center',
        textVerticalAlign: 'middle',
        fill: t.inkSoft,
        fontSize: ITEM_FS,
        fontFamily: '"Helvetica Neue", Arial, sans-serif',
        fontWeight: 'normal',
      },
    });
  });
});

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: t.pageBg,
  title: {
    text: 'venn-labeled-items · javascript · echarts · anyplot.ai',
    subtext: 'Where hype, utility, and cult status overlap',
    left: 'center',
    top: 22,
    textStyle: {
      color: t.ink,
      fontSize: 22,
      fontWeight: 'normal',
    },
    subtextStyle: {
      color: t.inkSoft,
      fontSize: 14,
      fontFamily: 'Georgia, "Times New Roman", serif',
      fontStyle: 'italic',
    },
  },
  graphic: [
    ...circleGraphics,
    ...catLabelGraphics,
    ...itemGraphics,
  ],
});
