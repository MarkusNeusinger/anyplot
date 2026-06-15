// anyplot.ai
// heatmap-periodic-table: Periodic Table Property Heatmap
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-15

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;
const THEME = window.ANYPLOT_THEME;

// --- Element data: [atomic_number, symbol, period, group, electronegativity]
// period 8 = lanthanide f-block row, period 9 = actinide f-block row
const elements = [
  // Period 1
  [1,"H",1,1,2.20],[2,"He",1,18,null],
  // Period 2
  [3,"Li",2,1,0.98],[4,"Be",2,2,1.57],
  [5,"B",2,13,2.04],[6,"C",2,14,2.55],[7,"N",2,15,3.04],
  [8,"O",2,16,3.44],[9,"F",2,17,3.98],[10,"Ne",2,18,null],
  // Period 3
  [11,"Na",3,1,0.93],[12,"Mg",3,2,1.31],
  [13,"Al",3,13,1.61],[14,"Si",3,14,1.90],[15,"P",3,15,2.19],
  [16,"S",3,16,2.58],[17,"Cl",3,17,3.16],[18,"Ar",3,18,null],
  // Period 4
  [19,"K",4,1,0.82],[20,"Ca",4,2,1.00],
  [21,"Sc",4,3,1.36],[22,"Ti",4,4,1.54],[23,"V",4,5,1.63],
  [24,"Cr",4,6,1.66],[25,"Mn",4,7,1.55],[26,"Fe",4,8,1.83],
  [27,"Co",4,9,1.88],[28,"Ni",4,10,1.91],[29,"Cu",4,11,1.90],
  [30,"Zn",4,12,1.65],[31,"Ga",4,13,1.81],[32,"Ge",4,14,2.01],
  [33,"As",4,15,2.18],[34,"Se",4,16,2.55],[35,"Br",4,17,2.96],
  [36,"Kr",4,18,3.00],
  // Period 5
  [37,"Rb",5,1,0.82],[38,"Sr",5,2,0.95],
  [39,"Y",5,3,1.22],[40,"Zr",5,4,1.33],[41,"Nb",5,5,1.60],
  [42,"Mo",5,6,2.16],[43,"Tc",5,7,1.90],[44,"Ru",5,8,2.20],
  [45,"Rh",5,9,2.28],[46,"Pd",5,10,2.20],[47,"Ag",5,11,1.93],
  [48,"Cd",5,12,1.69],[49,"In",5,13,1.78],[50,"Sn",5,14,1.96],
  [51,"Sb",5,15,2.05],[52,"Te",5,16,2.10],[53,"I",5,17,2.66],
  [54,"Xe",5,18,2.60],
  // Period 6 (main table — group 3 is lanthanide placeholder)
  [55,"Cs",6,1,0.79],[56,"Ba",6,2,0.89],
  [72,"Hf",6,4,1.30],[73,"Ta",6,5,1.50],[74,"W",6,6,2.36],
  [75,"Re",6,7,1.90],[76,"Os",6,8,2.20],[77,"Ir",6,9,2.20],
  [78,"Pt",6,10,2.28],[79,"Au",6,11,2.54],[80,"Hg",6,12,2.00],
  [81,"Tl",6,13,1.62],[82,"Pb",6,14,2.33],[83,"Bi",6,15,2.02],
  [84,"Po",6,16,2.00],[85,"At",6,17,2.20],[86,"Rn",6,18,null],
  // Period 7 (main table — group 3 is actinide placeholder)
  [87,"Fr",7,1,0.70],[88,"Ra",7,2,0.90],
  [104,"Rf",7,4,null],[105,"Db",7,5,null],[106,"Sg",7,6,null],
  [107,"Bh",7,7,null],[108,"Hs",7,8,null],[109,"Mt",7,9,null],
  [110,"Ds",7,10,null],[111,"Rg",7,11,null],[112,"Cn",7,12,null],
  [113,"Nh",7,13,null],[114,"Fl",7,14,null],[115,"Mc",7,15,null],
  [116,"Lv",7,16,null],[117,"Ts",7,17,null],[118,"Og",7,18,null],
  // Lanthanides (f-block row, period=8, group=position 1-15)
  [57,"La",8,1,1.10],[58,"Ce",8,2,1.12],[59,"Pr",8,3,1.13],
  [60,"Nd",8,4,1.14],[61,"Pm",8,5,1.13],[62,"Sm",8,6,1.17],
  [63,"Eu",8,7,null],[64,"Gd",8,8,1.20],[65,"Tb",8,9,null],
  [66,"Dy",8,10,1.22],[67,"Ho",8,11,1.23],[68,"Er",8,12,1.24],
  [69,"Tm",8,13,1.25],[70,"Yb",8,14,null],[71,"Lu",8,15,1.27],
  // Actinides (f-block row, period=9, group=position 1-15)
  [89,"Ac",9,1,1.10],[90,"Th",9,2,1.30],[91,"Pa",9,3,1.50],
  [92,"U",9,4,1.38],[93,"Np",9,5,1.36],[94,"Pu",9,6,1.28],
  [95,"Am",9,7,1.30],[96,"Cm",9,8,1.30],[97,"Bk",9,9,1.30],
  [98,"Cf",9,10,1.30],[99,"Es",9,11,1.30],[100,"Fm",9,12,1.30],
  [101,"Md",9,13,1.30],[102,"No",9,14,1.30],[103,"Lr",9,15,null],
];

// --- Layout (landscape 1600×900 CSS → 3200×1800 PNG at dpr=2)
const TILE = 70;
const INNER = 68;
const MAIN_LEFT = (width - 18 * TILE) / 2;   // (1600-1260)/2 = 170
const MAIN_TOP = 72;
const FB_LEFT = MAIN_LEFT + 2 * TILE;          // 310: f-block aligns under group-3 placeholder
const FB_TOP = MAIN_TOP + 7 * TILE + 30;       // 592: below main grid + gap
const CB_TOP = FB_TOP + 2 * TILE + 24;         // 756: below f-block rows
const CB_H = 20;

// --- Color scale: imprint_seq (green → blue) for Pauling electronegativity
const knownVals = elements.filter(d => d[4] !== null).map(d => d[4]);
const valMin = Math.min(...knownVals);  // Fr: 0.70
const valMax = Math.max(...knownVals);  // F:  3.98
const colorScale = d3.scaleSequential()
  .domain([valMin, valMax])
  .interpolator(d3.interpolateRgbBasis(t.seq));

// --- SVG
const svg = d3.select("#container")
  .append("svg").attr("width", width).attr("height", height);

// --- Title
svg.append("text")
  .attr("x", width / 2).attr("y", 45)
  .attr("text-anchor", "middle")
  .attr("fill", t.ink)
  .style("font-size", "22px").style("font-weight", "600")
  .style("font-family", "system-ui, sans-serif")
  .text("heatmap-periodic-table · javascript · d3 · anyplot.ai");

// --- Luminance-based text color for tile contrast (handles hex and rgb() strings)
function textOnFill(c) {
  let r, g, b;
  if (c[0] === "#") {
    r = parseInt(c.slice(1, 3), 16);
    g = parseInt(c.slice(3, 5), 16);
    b = parseInt(c.slice(5, 7), 16);
  } else {
    [r, g, b] = c.match(/\d+/g).map(Number);
  }
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 > 0.38 ? "#1A1A17" : "#F0EFE8";
}

const EMPTY_FILL = THEME === "light" ? "#CCCAC3" : "#3A3A36";

// --- Draw one element tile
function drawTile(x, y, an, sym, val) {
  const fill = val !== null ? colorScale(val) : EMPTY_FILL;
  const tc = textOnFill(fill);
  const g = svg.append("g").attr("transform", `translate(${x},${y})`);
  g.append("rect")
    .attr("width", INNER).attr("height", INNER)
    .attr("rx", 2).attr("fill", fill);
  // atomic number — top-left corner
  g.append("text").attr("x", 4).attr("y", 12)
    .style("font-size", "8px").style("font-family", "sans-serif")
    .attr("fill", tc).text(an);
  // element symbol — centered
  g.append("text").attr("x", INNER / 2).attr("y", INNER / 2 + 6)
    .attr("text-anchor", "middle")
    .style("font-size", "15px").style("font-weight", "700")
    .style("font-family", "sans-serif")
    .attr("fill", tc).text(sym);
  // electronegativity value — bottom center
  if (val !== null) {
    g.append("text").attr("x", INNER / 2).attr("y", INNER - 6)
      .attr("text-anchor", "middle")
      .style("font-size", "7px").style("font-family", "sans-serif")
      .attr("fill", tc).text(val.toFixed(2));
  }
}

// --- Draw f-block placeholder tile (in main table at group 3, periods 6-7)
function drawPlaceholder(x, y, label) {
  const fill = THEME === "light" ? "#DEDAD3" : "#2D2D29";
  const g = svg.append("g").attr("transform", `translate(${x},${y})`);
  g.append("rect")
    .attr("width", INNER).attr("height", INNER)
    .attr("rx", 2).attr("fill", fill)
    .attr("stroke", t.grid).attr("stroke-width", 0.8);
  g.append("text").attr("x", INNER / 2).attr("y", INNER / 2 + 4)
    .attr("text-anchor", "middle")
    .style("font-size", "8px").style("font-family", "sans-serif")
    .attr("fill", t.inkSoft).text(label);
}

// --- Main table: periods 1-7
elements.filter(d => d[2] <= 7).forEach(([an, sym, per, grp, val]) => {
  drawTile(
    MAIN_LEFT + (grp - 1) * TILE,
    MAIN_TOP + (per - 1) * TILE,
    an, sym, val
  );
});

// Lanthanide / actinide placeholders at group 3
drawPlaceholder(MAIN_LEFT + 2 * TILE, MAIN_TOP + 5 * TILE, "57-71");
drawPlaceholder(MAIN_LEFT + 2 * TILE, MAIN_TOP + 6 * TILE, "89-103");

// --- F-block rows (period 8 = lanthanides, period 9 = actinides)
elements.filter(d => d[2] >= 8).forEach(([an, sym, per, grp, val]) => {
  drawTile(
    FB_LEFT + (grp - 1) * TILE,
    FB_TOP + (per - 8) * TILE,
    an, sym, val
  );
});

// F-block row labels (left of main table, below period numbers)
[["Ln", 0], ["An", 1]].forEach(([label, i]) => {
  svg.append("text")
    .attr("x", MAIN_LEFT - 10)
    .attr("y", FB_TOP + i * TILE + INNER / 2 + 5)
    .attr("text-anchor", "end")
    .style("font-size", "11px").style("font-family", "sans-serif")
    .attr("fill", t.inkSoft).text(label);
});

// --- Period labels (1-7) left of main grid
for (let p = 1; p <= 7; p++) {
  svg.append("text")
    .attr("x", MAIN_LEFT - 10)
    .attr("y", MAIN_TOP + (p - 1) * TILE + INNER / 2 + 5)
    .attr("text-anchor", "end")
    .style("font-size", "11px").style("font-family", "sans-serif")
    .attr("fill", t.inkSoft).text(p);
}

// --- Group labels (1-18) above main grid
for (let grp = 1; grp <= 18; grp++) {
  svg.append("text")
    .attr("x", MAIN_LEFT + (grp - 1) * TILE + INNER / 2)
    .attr("y", MAIN_TOP - 10)
    .attr("text-anchor", "middle")
    .style("font-size", "9.5px").style("font-family", "sans-serif")
    .attr("fill", t.inkSoft).text(grp);
}

// --- Colorbar gradient
const CB_W = 18 * TILE;  // 1260
const nSteps = 260;
for (let i = 0; i < nSteps; i++) {
  const v = valMin + (i / (nSteps - 1)) * (valMax - valMin);
  svg.append("rect")
    .attr("x", MAIN_LEFT + i * (CB_W / nSteps))
    .attr("y", CB_TOP)
    .attr("width", CB_W / nSteps + 0.5)
    .attr("height", CB_H)
    .attr("fill", colorScale(v));
}
// Colorbar border
svg.append("rect")
  .attr("x", MAIN_LEFT).attr("y", CB_TOP)
  .attr("width", CB_W).attr("height", CB_H)
  .attr("fill", "none").attr("stroke", t.inkSoft).attr("stroke-width", 0.5);

// Colorbar axis
const cbScale = d3.scaleLinear()
  .domain([valMin, valMax])
  .range([MAIN_LEFT, MAIN_LEFT + CB_W]);
const cbAxisG = svg.append("g")
  .attr("transform", `translate(0,${CB_TOP + CB_H})`)
  .call(
    d3.axisBottom(cbScale)
      .tickValues([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
      .tickFormat(d3.format(".1f"))
      .tickSize(4)
  );
cbAxisG.selectAll("text")
  .attr("fill", t.inkSoft)
  .style("font-size", "12px")
  .style("font-family", "sans-serif");
cbAxisG.selectAll("line").attr("stroke", t.inkSoft);
cbAxisG.select(".domain").attr("stroke", t.inkSoft);

// Colorbar property label
svg.append("text")
  .attr("x", MAIN_LEFT + CB_W / 2)
  .attr("y", CB_TOP + CB_H + 44)
  .attr("text-anchor", "middle")
  .style("font-size", "14px").style("font-family", "sans-serif")
  .attr("fill", t.ink)
  .text("Electronegativity (Pauling scale)");
