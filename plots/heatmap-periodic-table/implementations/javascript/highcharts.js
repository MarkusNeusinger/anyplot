//# anyplot-orientation: square
// anyplot.ai
// heatmap-periodic-table: Periodic Table Property Heatmap
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-15

const t = window.ANYPLOT_TOKENS;
const isDark = window.ANYPLOT_THEME === 'dark';
const W = window.ANYPLOT_SIZE.width;   // 1200 (square)
const H = window.ANYPLOT_SIZE.height;  // 1200

// --- Color utilities ---
function hexToRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
}

function colorAt(frac) {
  const a = hexToRgb(t.seq[0]);   // #009E73 brand green
  const b = hexToRgb(t.seq[1]);   // #4467A3 blue
  const r = Math.round(a[0] + (b[0] - a[0]) * frac);
  const g = Math.round(a[1] + (b[1] - a[1]) * frac);
  const bl = Math.round(a[2] + (b[2] - a[2]) * frac);
  return 'rgb(' + r + ',' + g + ',' + bl + ')';
}

function lum(rgbStr) {
  return rgbStr.match(/\d+/g).map(Number).reduce((acc, c, i) => {
    const v = c / 255;
    const lin = v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    return acc + lin * [0.2126, 0.7152, 0.0722][i];
  }, 0);
}

// --- Element data: [symbol, Z, group, period, IE1 kJ/mol | null] ---
// period 8 = lanthanide f-block row; period 9 = actinide f-block row
// group in f-block rows: 3=La/Ac, 4=Ce/Th, ..., 17=Lu/Lr (matches group-3 column in main grid)
const elements = [
  // Period 1
  ['H', 1, 1, 1, 1312], ['He', 2, 18, 1, 2372],
  // Period 2
  ['Li', 3, 1, 2, 520], ['Be', 4, 2, 2, 900], ['B', 5, 13, 2, 800], ['C', 6, 14, 2, 1086],
  ['N', 7, 15, 2, 1402], ['O', 8, 16, 2, 1314], ['F', 9, 17, 2, 1681], ['Ne', 10, 18, 2, 2081],
  // Period 3
  ['Na', 11, 1, 3, 496], ['Mg', 12, 2, 3, 738], ['Al', 13, 13, 3, 578], ['Si', 14, 14, 3, 786],
  ['P', 15, 15, 3, 1012], ['S', 16, 16, 3, 1000], ['Cl', 17, 17, 3, 1251], ['Ar', 18, 18, 3, 1521],
  // Period 4
  ['K', 19, 1, 4, 419], ['Ca', 20, 2, 4, 590], ['Sc', 21, 3, 4, 633], ['Ti', 22, 4, 4, 659],
  ['V', 23, 5, 4, 651], ['Cr', 24, 6, 4, 653], ['Mn', 25, 7, 4, 717], ['Fe', 26, 8, 4, 762],
  ['Co', 27, 9, 4, 760], ['Ni', 28, 10, 4, 737], ['Cu', 29, 11, 4, 745], ['Zn', 30, 12, 4, 906],
  ['Ga', 31, 13, 4, 579], ['Ge', 32, 14, 4, 762], ['As', 33, 15, 4, 947], ['Se', 34, 16, 4, 941],
  ['Br', 35, 17, 4, 1140], ['Kr', 36, 18, 4, 1351],
  // Period 5
  ['Rb', 37, 1, 5, 403], ['Sr', 38, 2, 5, 550], ['Y', 39, 3, 5, 600], ['Zr', 40, 4, 5, 640],
  ['Nb', 41, 5, 5, 652], ['Mo', 42, 6, 5, 684], ['Tc', 43, 7, 5, 702], ['Ru', 44, 8, 5, 711],
  ['Rh', 45, 9, 5, 720], ['Pd', 46, 10, 5, 804], ['Ag', 47, 11, 5, 731], ['Cd', 48, 12, 5, 868],
  ['In', 49, 13, 5, 558], ['Sn', 50, 14, 5, 709], ['Sb', 51, 15, 5, 834], ['Te', 52, 16, 5, 869],
  ['I', 53, 17, 5, 1008], ['Xe', 54, 18, 5, 1170],
  // Period 6 main (group 3 left empty for La placeholder)
  ['Cs', 55, 1, 6, 376], ['Ba', 56, 2, 6, 503],
  ['Hf', 72, 4, 6, 659], ['Ta', 73, 5, 6, 761], ['W', 74, 6, 6, 770], ['Re', 75, 7, 6, 760],
  ['Os', 76, 8, 6, 840], ['Ir', 77, 9, 6, 880], ['Pt', 78, 10, 6, 870], ['Au', 79, 11, 6, 890],
  ['Hg', 80, 12, 6, 1007], ['Tl', 81, 13, 6, 589], ['Pb', 82, 14, 6, 716], ['Bi', 83, 15, 6, 703],
  ['Po', 84, 16, 6, 812], ['At', 85, 17, 6, 930], ['Rn', 86, 18, 6, 1037],
  // Period 7 main (group 3 left empty for Ac placeholder)
  ['Fr', 87, 1, 7, 380], ['Ra', 88, 2, 7, 509],
  ['Rf', 104, 4, 7, 580], ['Db', 105, 5, 7, null], ['Sg', 106, 6, 7, null], ['Bh', 107, 7, 7, null],
  ['Hs', 108, 8, 7, null], ['Mt', 109, 9, 7, null], ['Ds', 110, 10, 7, null], ['Rg', 111, 11, 7, null],
  ['Cn', 112, 12, 7, 1155], ['Nh', 113, 13, 7, null], ['Fl', 114, 14, 7, null], ['Mc', 115, 15, 7, null],
  ['Lv', 116, 16, 7, null], ['Ts', 117, 17, 7, null], ['Og', 118, 18, 7, null],
  // Lanthanides — period 8, group 3..17 (La=3, Ce=4, ..., Lu=17)
  ['La', 57, 3, 8, 538], ['Ce', 58, 4, 8, 528], ['Pr', 59, 5, 8, 523], ['Nd', 60, 6, 8, 530],
  ['Pm', 61, 7, 8, 536], ['Sm', 62, 8, 8, 543], ['Eu', 63, 9, 8, 547], ['Gd', 64, 10, 8, 593],
  ['Tb', 65, 11, 8, 565], ['Dy', 66, 12, 8, 572], ['Ho', 67, 13, 8, 581], ['Er', 68, 14, 8, 589],
  ['Tm', 69, 15, 8, 597], ['Yb', 70, 16, 8, 603], ['Lu', 71, 17, 8, 524],
  // Actinides — period 9, group 3..17 (Ac=3, Th=4, ..., Lr=17)
  ['Ac', 89, 3, 9, 499], ['Th', 90, 4, 9, 587], ['Pa', 91, 5, 9, 568], ['U', 92, 6, 9, 598],
  ['Np', 93, 7, 9, 605], ['Pu', 94, 8, 9, 585], ['Am', 95, 9, 9, 578], ['Cm', 96, 10, 9, 581],
  ['Bk', 97, 11, 9, 601], ['Cf', 98, 12, 9, 608], ['Es', 99, 13, 9, 619], ['Fm', 100, 14, 9, 627],
  ['Md', 101, 15, 9, 635], ['No', 102, 16, 9, 642], ['Lr', 103, 17, 9, 479],
];

const ieValues = elements.map(e => e[4]).filter(v => v !== null);
const minIE = Math.min(...ieValues);  // ~376 (Cs)
const maxIE = Math.max(...ieValues);  // 2372 (He)

// --- Layout (CSS px; mount = 1200×1200 square) ---
const PITCH = 64;
const TILE = PITCH - 2;   // 62px tiles with 2px gap
const GRID_LEFT = Math.round((W - 18 * PITCH) / 2);  // center 18-column grid

const TITLE_H = 68;
const MAIN_H = 7 * PITCH;         // 448px
const FGAP_H = Math.round(PITCH * 0.55);  // 35px separator before f-block
const FBLOCK_H = 2 * PITCH;       // 128px
const CB_H = 22;                   // colorbar rect height
const CB_LABEL_H = 22;             // space for colorbar labels
const CONTENT_H = TITLE_H + MAIN_H + FGAP_H + FBLOCK_H + 28 + CB_H + CB_LABEL_H;
const TOP = Math.round((H - CONTENT_H) / 2);

const TITLE_Y = TOP + Math.round(TITLE_H * 0.72);
const GRID_TOP = TOP + TITLE_H;
const FBLOCK_TOP = GRID_TOP + MAIN_H + FGAP_H;
const CB_TOP = FBLOCK_TOP + FBLOCK_H + 28;

// --- Render via Highcharts SVG renderer ---
const chart = Highcharts.chart('container', {
  chart: {
    backgroundColor: 'transparent',
    animation: false,
    style: { fontFamily: 'inherit' },
    margin: [0, 0, 0, 0],
    spacing: [0, 0, 0, 0],
  },
  title: { text: '' },
  credits: { enabled: false },
  xAxis: { visible: false },
  yAxis: { visible: false },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
});

const R = chart.renderer;

// --- Title ---
const titleText = 'First Ionization Energy · heatmap-periodic-table · javascript · highcharts · anyplot.ai';
const titleFS = Math.max(Math.round(22 * 67 / titleText.length), 12);
R.text(titleText, W / 2, TITLE_Y)
  .attr({ align: 'center', zIndex: 5 })
  .css({ color: t.ink, fontSize: titleFS + 'px', fontWeight: '600' })
  .add();

// --- Draw a single element tile ---
function drawTile(x, y, sym, z, ie) {
  const frac = ie !== null ? (ie - minIE) / (maxIE - minIE) : null;
  const fill = frac !== null
    ? colorAt(frac)
    : (isDark ? '#383834' : '#C0BFB8');
  const textCol = frac !== null
    ? (lum(fill) > 0.18 ? '#1A1A17' : '#F0EFE8')
    : (isDark ? '#6B6A63' : '#8A8A83');

  const numFS = Math.round(TILE * 0.145);  // ~9px
  const symFS = Math.round(TILE * 0.265);  // ~16px

  R.rect(x, y, TILE, TILE, 2)
    .attr({ fill: fill, zIndex: 1 })
    .add();

  // Atomic number — top-left corner
  R.text(String(z), x + 3, y + numFS + 2)
    .attr({ zIndex: 3 })
    .css({ color: textCol, fontSize: numFS + 'px', lineHeight: '1' })
    .add();

  // Element symbol — centered
  R.text(sym, x + TILE / 2, y + TILE / 2 + Math.round(symFS * 0.38))
    .attr({ align: 'center', zIndex: 3 })
    .css({ color: textCol, fontSize: symFS + 'px', fontWeight: '700' })
    .add();
}

// --- Main table and f-block tiles ---
elements.forEach(function(el) {
  var sym = el[0], z = el[1], grp = el[2], per = el[3], ie = el[4];
  var x, y;
  if (per <= 7) {
    x = GRID_LEFT + (grp - 1) * PITCH;
    y = GRID_TOP + (per - 1) * PITCH;
  } else {
    // f-block: group 3..17 shares x coords with main table group 3..17
    x = GRID_LEFT + (grp - 1) * PITCH;
    y = FBLOCK_TOP + (per - 8) * PITCH;
  }
  drawTile(x, y, sym, z, ie);
});

// --- Placeholder tiles at group 3 for periods 6 and 7 ---
[
  [6, '57–71'],
  [7, '89–103'],
].forEach(function(pair) {
  var per = pair[0], label = pair[1];
  var x = GRID_LEFT + 2 * PITCH;
  var y = GRID_TOP + (per - 1) * PITCH;
  var fill = isDark ? '#383834' : '#C0BFB8';
  var col = isDark ? '#6B6A63' : '#8A8A83';
  R.rect(x, y, TILE, TILE, 2)
    .attr({ fill: fill, zIndex: 1 })
    .add();
  R.text(label, x + TILE / 2, y + TILE / 2 + 5)
    .attr({ align: 'center', zIndex: 3 })
    .css({ color: col, fontSize: '9px' })
    .add();
});

// --- Colorbar ---
const CB_W = Math.round(W * 0.52);
const CB_LEFT = Math.round((W - CB_W) / 2);
const STOPS = 60;

for (var i = 0; i < STOPS; i++) {
  var frac = i / (STOPS - 1);
  R.rect(
    CB_LEFT + Math.round(i * CB_W / STOPS),
    CB_TOP,
    Math.ceil(CB_W / STOPS) + 1,
    CB_H,
    0
  )
    .attr({ fill: colorAt(frac), zIndex: 1 })
    .add();
}

// Colorbar border
R.rect(CB_LEFT, CB_TOP, CB_W, CB_H, 0)
  .attr({ fill: 'none', stroke: t.inkSoft, 'stroke-width': 1, zIndex: 2 })
  .add();

// Colorbar tick marks and labels
var labelY = CB_TOP + CB_H + 15;
R.text(minIE + ' kJ/mol', CB_LEFT, labelY)
  .attr({ align: 'left', zIndex: 3 })
  .css({ color: t.inkSoft, fontSize: '11px' })
  .add();
R.text(maxIE + ' kJ/mol', CB_LEFT + CB_W, labelY)
  .attr({ align: 'right', zIndex: 3 })
  .css({ color: t.inkSoft, fontSize: '11px' })
  .add();
R.text('First Ionization Energy (kJ/mol)', W / 2, labelY)
  .attr({ align: 'center', zIndex: 3 })
  .css({ color: t.inkSoft, fontSize: '11px' })
  .add();
