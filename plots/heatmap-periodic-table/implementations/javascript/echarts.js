// anyplot.ai
// heatmap-periodic-table: Periodic Table Property Heatmap
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 83/100 | Created: 2026-06-15
//# anyplot-orientation: square
// anyplot.ai
// heatmap-periodic-table: Periodic Table Property Heatmap
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-15

const t = window.ANYPLOT_TOKENS;
const W = window.ANYPLOT_SIZE.width;
const H = window.ANYPLOT_SIZE.height;

// --- Data: First Ionization Energy (kJ/mol) --------------------------------
// col 0-17 = groups 1-18 (0-indexed)
// row 0-6  = periods 1-7; row 7.5 = lanthanides; row 8.5 = actinides
const ELEMENTS = [
  // Period 1
  {s:"H",  z:1,   col:0,  row:0,   v:1312.0},
  {s:"He", z:2,   col:17, row:0,   v:2372.3},
  // Period 2
  {s:"Li", z:3,   col:0,  row:1,   v:520.2},
  {s:"Be", z:4,   col:1,  row:1,   v:899.5},
  {s:"B",  z:5,   col:12, row:1,   v:800.6},
  {s:"C",  z:6,   col:13, row:1,   v:1086.5},
  {s:"N",  z:7,   col:14, row:1,   v:1402.3},
  {s:"O",  z:8,   col:15, row:1,   v:1313.9},
  {s:"F",  z:9,   col:16, row:1,   v:1681.0},
  {s:"Ne", z:10,  col:17, row:1,   v:2080.7},
  // Period 3
  {s:"Na", z:11,  col:0,  row:2,   v:495.8},
  {s:"Mg", z:12,  col:1,  row:2,   v:737.7},
  {s:"Al", z:13,  col:12, row:2,   v:577.5},
  {s:"Si", z:14,  col:13, row:2,   v:786.5},
  {s:"P",  z:15,  col:14, row:2,   v:1011.8},
  {s:"S",  z:16,  col:15, row:2,   v:999.6},
  {s:"Cl", z:17,  col:16, row:2,   v:1251.2},
  {s:"Ar", z:18,  col:17, row:2,   v:1520.6},
  // Period 4
  {s:"K",  z:19,  col:0,  row:3,   v:418.8},
  {s:"Ca", z:20,  col:1,  row:3,   v:589.8},
  {s:"Sc", z:21,  col:2,  row:3,   v:633.1},
  {s:"Ti", z:22,  col:3,  row:3,   v:658.8},
  {s:"V",  z:23,  col:4,  row:3,   v:650.9},
  {s:"Cr", z:24,  col:5,  row:3,   v:652.9},
  {s:"Mn", z:25,  col:6,  row:3,   v:717.3},
  {s:"Fe", z:26,  col:7,  row:3,   v:762.5},
  {s:"Co", z:27,  col:8,  row:3,   v:760.4},
  {s:"Ni", z:28,  col:9,  row:3,   v:737.1},
  {s:"Cu", z:29,  col:10, row:3,   v:745.5},
  {s:"Zn", z:30,  col:11, row:3,   v:906.4},
  {s:"Ga", z:31,  col:12, row:3,   v:578.8},
  {s:"Ge", z:32,  col:13, row:3,   v:762.0},
  {s:"As", z:33,  col:14, row:3,   v:947.0},
  {s:"Se", z:34,  col:15, row:3,   v:941.0},
  {s:"Br", z:35,  col:16, row:3,   v:1139.9},
  {s:"Kr", z:36,  col:17, row:3,   v:1350.8},
  // Period 5
  {s:"Rb", z:37,  col:0,  row:4,   v:403.0},
  {s:"Sr", z:38,  col:1,  row:4,   v:549.5},
  {s:"Y",  z:39,  col:2,  row:4,   v:600.0},
  {s:"Zr", z:40,  col:3,  row:4,   v:640.1},
  {s:"Nb", z:41,  col:4,  row:4,   v:652.1},
  {s:"Mo", z:42,  col:5,  row:4,   v:684.3},
  {s:"Tc", z:43,  col:6,  row:4,   v:702.0},
  {s:"Ru", z:44,  col:7,  row:4,   v:710.2},
  {s:"Rh", z:45,  col:8,  row:4,   v:719.7},
  {s:"Pd", z:46,  col:9,  row:4,   v:804.4},
  {s:"Ag", z:47,  col:10, row:4,   v:731.0},
  {s:"Cd", z:48,  col:11, row:4,   v:867.8},
  {s:"In", z:49,  col:12, row:4,   v:558.3},
  {s:"Sn", z:50,  col:13, row:4,   v:708.6},
  {s:"Sb", z:51,  col:14, row:4,   v:834.0},
  {s:"Te", z:52,  col:15, row:4,   v:869.3},
  {s:"I",  z:53,  col:16, row:4,   v:1008.4},
  {s:"Xe", z:54,  col:17, row:4,   v:1170.4},
  // Period 6 (main; col 2 gap reserved for lanthanide reference)
  {s:"Cs", z:55,  col:0,  row:5,   v:375.7},
  {s:"Ba", z:56,  col:1,  row:5,   v:502.9},
  {s:"Hf", z:72,  col:3,  row:5,   v:658.5},
  {s:"Ta", z:73,  col:4,  row:5,   v:761.0},
  {s:"W",  z:74,  col:5,  row:5,   v:770.0},
  {s:"Re", z:75,  col:6,  row:5,   v:760.0},
  {s:"Os", z:76,  col:7,  row:5,   v:840.0},
  {s:"Ir", z:77,  col:8,  row:5,   v:880.0},
  {s:"Pt", z:78,  col:9,  row:5,   v:870.0},
  {s:"Au", z:79,  col:10, row:5,   v:890.1},
  {s:"Hg", z:80,  col:11, row:5,   v:1007.1},
  {s:"Tl", z:81,  col:12, row:5,   v:589.4},
  {s:"Pb", z:82,  col:13, row:5,   v:715.6},
  {s:"Bi", z:83,  col:14, row:5,   v:703.0},
  {s:"Po", z:84,  col:15, row:5,   v:812.1},
  {s:"At", z:85,  col:16, row:5,   v:920.0},
  {s:"Rn", z:86,  col:17, row:5,   v:1037.0},
  // Period 7 (main; col 2 gap reserved for actinide reference)
  {s:"Fr", z:87,  col:0,  row:6,   v:380.0},
  {s:"Ra", z:88,  col:1,  row:6,   v:509.3},
  {s:"Rf", z:104, col:3,  row:6,   v:null},
  {s:"Db", z:105, col:4,  row:6,   v:null},
  {s:"Sg", z:106, col:5,  row:6,   v:null},
  {s:"Bh", z:107, col:6,  row:6,   v:null},
  {s:"Hs", z:108, col:7,  row:6,   v:null},
  {s:"Mt", z:109, col:8,  row:6,   v:null},
  {s:"Ds", z:110, col:9,  row:6,   v:null},
  {s:"Rg", z:111, col:10, row:6,   v:null},
  {s:"Cn", z:112, col:11, row:6,   v:null},
  {s:"Nh", z:113, col:12, row:6,   v:null},
  {s:"Fl", z:114, col:13, row:6,   v:null},
  {s:"Mc", z:115, col:14, row:6,   v:null},
  {s:"Lv", z:116, col:15, row:6,   v:null},
  {s:"Ts", z:117, col:16, row:6,   v:null},
  {s:"Og", z:118, col:17, row:6,   v:null},
  // Lanthanide row (row 7.5)
  {s:"La", z:57,  col:2,  row:7.5, v:538.1},
  {s:"Ce", z:58,  col:3,  row:7.5, v:534.4},
  {s:"Pr", z:59,  col:4,  row:7.5, v:527.0},
  {s:"Nd", z:60,  col:5,  row:7.5, v:533.1},
  {s:"Pm", z:61,  col:6,  row:7.5, v:540.0},
  {s:"Sm", z:62,  col:7,  row:7.5, v:544.5},
  {s:"Eu", z:63,  col:8,  row:7.5, v:547.1},
  {s:"Gd", z:64,  col:9,  row:7.5, v:593.4},
  {s:"Tb", z:65,  col:10, row:7.5, v:565.8},
  {s:"Dy", z:66,  col:11, row:7.5, v:573.0},
  {s:"Ho", z:67,  col:12, row:7.5, v:581.0},
  {s:"Er", z:68,  col:13, row:7.5, v:589.3},
  {s:"Tm", z:69,  col:14, row:7.5, v:596.7},
  {s:"Yb", z:70,  col:15, row:7.5, v:603.4},
  {s:"Lu", z:71,  col:16, row:7.5, v:523.5},
  // Actinide row (row 8.5)
  {s:"Ac", z:89,  col:2,  row:8.5, v:499.0},
  {s:"Th", z:90,  col:3,  row:8.5, v:587.0},
  {s:"Pa", z:91,  col:4,  row:8.5, v:568.0},
  {s:"U",  z:92,  col:5,  row:8.5, v:597.6},
  {s:"Np", z:93,  col:6,  row:8.5, v:604.5},
  {s:"Pu", z:94,  col:7,  row:8.5, v:584.7},
  {s:"Am", z:95,  col:8,  row:8.5, v:578.0},
  {s:"Cm", z:96,  col:9,  row:8.5, v:581.0},
  {s:"Bk", z:97,  col:10, row:8.5, v:601.0},
  {s:"Cf", z:98,  col:11, row:8.5, v:608.0},
  {s:"Es", z:99,  col:12, row:8.5, v:619.0},
  {s:"Fm", z:100, col:13, row:8.5, v:627.0},
  {s:"Md", z:101, col:14, row:8.5, v:635.0},
  {s:"No", z:102, col:15, row:8.5, v:642.0},
  {s:"Lr", z:103, col:16, row:8.5, v:470.0},
];

// --- Color utilities -------------------------------------------------------
function hexToRgb(hex) {
  return [parseInt(hex.slice(1,3),16), parseInt(hex.slice(3,5),16), parseInt(hex.slice(5,7),16)];
}

function lerpColor(h1, h2, frac) {
  const [r1,g1,b1] = hexToRgb(h1);
  const [r2,g2,b2] = hexToRgb(h2);
  const r = Math.round(r1 + (r2-r1)*frac);
  const g = Math.round(g1 + (g2-g1)*frac);
  const b = Math.round(b1 + (b2-b1)*frac);
  return `rgb(${r},${g},${b})`;
}

function srgbLinear(c) {
  const s = c / 255;
  return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
}

function rgbLuminance(r, g, b) {
  return 0.2126 * srgbLinear(r) + 0.7152 * srgbLinear(g) + 0.0722 * srgbLinear(b);
}

function getTextColor(bgColor) {
  let r, g, b;
  if (bgColor.startsWith('#')) {
    [r, g, b] = hexToRgb(bgColor);
  } else {
    const m = bgColor.match(/\d+/g);
    [r, g, b] = [+m[0], +m[1], +m[2]];
  }
  return rgbLuminance(r, g, b) > 0.30 ? '#1A1A17' : '#F0EFE8';
}

// --- Value range and color mapping -----------------------------------------
const vals = ELEMENTS.filter(e => e.v != null).map(e => e.v);
const vMin = Math.min(...vals);   // ~376 (Cs)
const vMax = Math.max(...vals);   // ~2372 (He)

const GREY_TILE = window.ANYPLOT_THEME === 'light' ? '#C4C3BC' : '#3C3C38';

function valueToColor(v) {
  if (v == null) return GREY_TILE;
  return lerpColor(t.seq[0], t.seq[1], (v - vMin) / (vMax - vMin));
}

// --- Layout ----------------------------------------------------------------
const NCOLS = 18;
const NROWS = 9.5;  // 7 main + 0.5 gap + 2 f-block rows
const margin = {top: 78, bottom: 105, left: 22, right: 22};
const availW = W - margin.left - margin.right;
const availH = H - margin.top - margin.bottom;
const TILE = Math.floor(Math.min(availW / NCOLS, availH / NROWS));
const GAP = Math.max(2, Math.round(TILE * 0.05));
const gridW = TILE * NCOLS;
const ox = margin.left + Math.floor((availW - gridW) / 2);  // center grid horizontally
const oy = margin.top;

function tilePx(col, row) {
  return {
    x: ox + col * TILE + GAP,
    y: oy + row * TILE + GAP,
    w: TILE - 2 * GAP,
    h: TILE - 2 * GAP,
    cx: ox + col * TILE + TILE * 0.5,
    cy: oy + row * TILE + TILE * 0.5,
  };
}

const symFont   = `bold ${Math.floor(TILE * 0.34)}px sans-serif`;
const znFont    = `${Math.floor(TILE * 0.17)}px sans-serif`;
const valFont   = `${Math.max(6, Math.floor(TILE * 0.13))}px sans-serif`;

// --- Build graphic elements ------------------------------------------------
const graphic = [];

// Background fill
graphic.push({
  type: 'rect',
  left: 0, top: 0, right: 0, bottom: 0,
  style: {fill: t.pageBg},
});

// Title
graphic.push({
  type: 'text',
  left: 'center', top: 20,
  style: {
    text: 'heatmap-periodic-table · javascript · echarts · anyplot.ai',
    font: 'bold 20px sans-serif',
    fill: t.ink,
    textAlign: 'center',
    textBaseline: 'top',
  },
});

// Property subtitle
graphic.push({
  type: 'text',
  left: 'center', top: 48,
  style: {
    text: 'First Ionization Energy (kJ/mol)',
    font: '14px sans-serif',
    fill: t.inkSoft,
    textAlign: 'center',
    textBaseline: 'top',
  },
});

// Draw each element tile
for (const el of ELEMENTS) {
  const {x, y, w, h, cx, cy} = tilePx(el.col, el.row);
  const bgColor = valueToColor(el.v);
  const textCol = getTextColor(bgColor);

  // Tile background
  graphic.push({
    type: 'rect',
    shape: {x, y, width: w, height: h},
    style: {fill: bgColor, lineWidth: 0},
  });

  // Atomic number (top-left)
  graphic.push({
    type: 'text',
    style: {
      x: x + 3,
      y: y + 2,
      text: String(el.z),
      font: znFont,
      fill: textCol,
      opacity: 0.85,
      textAlign: 'left',
      textBaseline: 'top',
    },
  });

  // Element symbol (center)
  graphic.push({
    type: 'text',
    style: {
      x: cx,
      y: cy + TILE * 0.03,
      text: el.s,
      font: symFont,
      fill: textCol,
      textAlign: 'center',
      textBaseline: 'middle',
    },
  });

  // IE value (bottom, small) — only for elements with data
  if (el.v != null) {
    graphic.push({
      type: 'text',
      style: {
        x: cx,
        y: y + h - 2,
        text: el.v.toFixed(0),
        font: valFont,
        fill: textCol,
        opacity: 0.80,
        textAlign: 'center',
        textBaseline: 'bottom',
      },
    });
  }
}

// Reference tiles at period 6/7, group 3 (canonical f-block gap markers)
const refFont = `${Math.max(6, Math.floor(TILE * 0.13))}px sans-serif`;
[
  {col: 2, row: 5, label: '57-71'},
  {col: 2, row: 6, label: '89-103'},
].forEach(({col, row, label}) => {
  const {x, y, w, h, cx, cy} = tilePx(col, row);
  graphic.push({
    type: 'rect',
    shape: {x, y, width: w, height: h},
    style: {fill: 'none', stroke: t.inkSoft, lineWidth: 1, lineDash: [3, 2]},
  });
  graphic.push({
    type: 'text',
    style: {x: cx, y: cy, text: label, font: refFont, fill: t.inkSoft, textAlign: 'center', textBaseline: 'middle'},
  });
});

// --- Colorbar -------------------------------------------------------------
const cbBarY = oy + 9.5 * TILE + 18;
const cbBarH = 15;
const cbBarW = Math.floor(gridW * 0.68);
const cbBarX = ox + Math.floor((gridW - cbBarW) / 2);
const cbSteps = 160;

for (let i = 0; i < cbSteps; i++) {
  const f = i / cbSteps;
  graphic.push({
    type: 'rect',
    shape: {x: cbBarX + f * cbBarW, y: cbBarY, width: Math.ceil(cbBarW / cbSteps) + 1, height: cbBarH},
    style: {fill: lerpColor(t.seq[0], t.seq[1], f), lineWidth: 0},
  });
}

// Colorbar border
graphic.push({
  type: 'rect',
  shape: {x: cbBarX, y: cbBarY, width: cbBarW, height: cbBarH},
  style: {fill: 'none', stroke: t.inkSoft, lineWidth: 1},
});

// Colorbar tick labels and unit
const cbFont = `${Math.max(10, Math.floor(TILE * 0.18))}px sans-serif`;
graphic.push({type:'text', style:{x:cbBarX, y:cbBarY+cbBarH+4, text:vMin.toFixed(0), font:cbFont, fill:t.inkSoft, textAlign:'left', textBaseline:'top'}});
graphic.push({type:'text', style:{x:cbBarX+cbBarW, y:cbBarY+cbBarH+4, text:vMax.toFixed(0), font:cbFont, fill:t.inkSoft, textAlign:'right', textBaseline:'top'}});
graphic.push({type:'text', style:{x:cbBarX+cbBarW*0.5, y:cbBarY+cbBarH+4, text:'kJ/mol', font:cbFont, fill:t.inkSoft, textAlign:'center', textBaseline:'top'}});

// Colorbar end labels (low / high)
const cbLabelFont = `${Math.max(9, Math.floor(TILE * 0.15))}px sans-serif`;
graphic.push({type:'text', style:{x:cbBarX, y:cbBarY-4, text:'low IE', font:cbLabelFont, fill:t.inkSoft, textAlign:'left', textBaseline:'bottom', opacity:0.7}});
graphic.push({type:'text', style:{x:cbBarX+cbBarW, y:cbBarY-4, text:'high IE', font:cbLabelFont, fill:t.inkSoft, textAlign:'right', textBaseline:'bottom', opacity:0.7}});

// --- Render ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: t.pageBg,
  graphic,
});
