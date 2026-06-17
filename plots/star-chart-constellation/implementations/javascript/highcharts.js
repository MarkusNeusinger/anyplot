// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-17
//# anyplot-orientation: square

// A north-polar azimuthal-equidistant sky map. Stars are plotted by Right
// Ascension / Declination, sized by apparent magnitude (brighter = larger), with
// constellation stick-figure lines, an RA/Dec coordinate grid and the ecliptic.
//
// Imprint palette note: the spec asks for pale/white stars on a night sky, but
// anyplot's brand contract is stronger — the page surface is cream (#FAF8F1) on
// light and near-black (#1A1A17) on dark, and the first categorical series is
// ALWAYS brand green #009E73. Green is the one star colour that stays legible on
// BOTH surfaces, so the stars carry the brand green (identical across themes);
// constellation lines, grid, ticks and labels use theme-adaptive chrome tokens.

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME === "dark" ? "dark" : "light";
const BRAND = t.palette[0]; // #009E73 — first/only star series

// Soft theme-adaptive tone for the constellation stick-figures (structural).
const LINE_COL = THEME === "dark" ? "rgba(184,183,176,0.55)" : "rgba(74,74,68,0.50)";

// --- Projection -------------------------------------------------------------
// North-polar azimuthal equidistant: radius = co-latitude (90 - dec); the pole
// sits at the centre and the celestial equator (dec 0) is the outer boundary.
const DEG = Math.PI / 180;
function project(raH, dec) {
  const ang = raH * 15 * DEG; // RA hours -> radians
  const r = 90 - dec;
  return [r * Math.sin(ang), r * Math.cos(ang)];
}

// --- Bright catalog ---------------------------------------------------------
// [id, RA(hours), Dec(deg), apparent magnitude]. Real positions for 17 northern
// constellations; lower magnitude = brighter.
const STARS = [
  // Ursa Major
  ["Dubhe", 11.062, 61.75, 1.79], ["Merak", 11.030, 56.38, 2.37],
  ["Phecda", 11.897, 53.69, 2.44], ["Megrez", 12.257, 57.03, 3.31],
  ["Alioth", 12.900, 55.96, 1.77], ["Mizar", 13.399, 54.93, 2.04],
  ["Alkaid", 13.792, 49.31, 1.86],
  // Ursa Minor
  ["Polaris", 2.530, 89.26, 1.98], ["Yildun", 17.537, 86.59, 4.36],
  ["EpsUMi", 16.766, 82.04, 4.21], ["ZetUMi", 15.734, 77.79, 4.32],
  ["Pherkad", 15.345, 71.83, 3.05], ["Kochab", 14.845, 74.16, 2.08],
  // Cassiopeia
  ["Caph", 0.153, 59.15, 2.27], ["Schedar", 0.675, 56.54, 2.24],
  ["Cih", 0.945, 60.72, 2.47], ["Ruchbah", 1.430, 60.24, 2.68],
  ["Segin", 1.907, 63.67, 3.38],
  // Cepheus
  ["Alderamin", 21.310, 62.59, 2.45], ["Alfirk", 21.477, 70.56, 3.23],
  ["Errai", 23.656, 77.63, 3.21], ["ZetCep", 22.181, 58.20, 3.35],
  ["IotCep", 22.828, 66.20, 3.52], ["DelCep", 22.477, 58.42, 4.07],
  // Cygnus
  ["Deneb", 20.690, 45.28, 1.25], ["Sadr", 20.370, 40.26, 2.23],
  ["Gienah", 20.770, 33.97, 2.48], ["Fawaris", 19.750, 45.13, 2.87],
  ["Albireo", 19.512, 27.96, 3.18],
  // Lyra
  ["Vega", 18.615, 38.78, 0.03], ["Sheliak", 18.835, 33.36, 3.52],
  ["Sulafat", 18.982, 32.69, 3.25], ["DelLyr", 18.908, 36.90, 4.30],
  ["ZetLyr", 18.746, 37.60, 4.36],
  // Draco
  ["Eltanin", 17.943, 51.49, 2.23], ["Rastaban", 17.507, 52.30, 2.79],
  ["Grumium", 17.892, 56.87, 3.75], ["NuDra", 17.538, 55.18, 4.88],
  ["Altais", 19.209, 67.66, 3.07], ["ZetDra", 17.146, 65.71, 3.17],
  ["Edasich", 15.415, 58.97, 3.29], ["Thuban", 14.073, 64.38, 3.65],
  ["KapDra", 12.558, 69.79, 3.82], ["LamDra", 11.523, 69.33, 3.84],
  // Bootes
  ["Arcturus", 14.261, 19.18, -0.05], ["Nekkar", 15.032, 40.39, 3.49],
  ["Seginus", 14.535, 38.31, 3.03], ["Izar", 14.749, 27.07, 2.37],
  ["DelBoo", 15.258, 33.31, 3.46], ["Muphrid", 13.911, 18.40, 2.68],
  // Corona Borealis
  ["Alphecca", 15.578, 26.71, 2.22], ["BetCrB", 15.464, 29.10, 3.66],
  ["GamCrB", 15.713, 26.30, 3.81], ["TheCrB", 15.553, 31.36, 4.14],
  ["DelCrB", 15.827, 26.07, 4.59], ["EpsCrB", 15.958, 26.88, 4.13],
  // Hercules
  ["ZetHer", 16.688, 31.60, 2.81], ["EtaHer", 16.715, 38.92, 3.48],
  ["PiHer", 17.251, 36.81, 3.16], ["EpsHer", 17.005, 30.93, 3.92],
  ["Korneph", 16.504, 21.49, 2.78], ["DelHer", 17.250, 24.84, 3.12],
  // Pegasus + Andromeda
  ["Alpheratz", 0.140, 29.09, 2.06], ["Scheat", 23.063, 28.08, 2.42],
  ["Markab", 23.079, 15.21, 2.48], ["Algenib", 0.221, 15.18, 2.83],
  ["Mirach", 1.162, 35.62, 2.05], ["Almach", 2.065, 42.33, 2.10],
  ["DelAnd", 0.655, 30.86, 3.27],
  // Perseus
  ["Mirfak", 3.405, 49.86, 1.79], ["Algol", 3.136, 40.96, 2.12],
  ["GamPer", 3.080, 53.51, 2.91], ["DelPer", 3.715, 47.79, 3.01],
  ["EpsPer", 3.964, 40.01, 2.90], ["ZetPer", 3.902, 31.88, 2.85],
  // Auriga
  ["Capella", 5.278, 45.998, 0.08], ["Menkalinan", 5.992, 44.95, 1.90],
  ["Mahasim", 5.995, 37.21, 2.62], ["Hassaleh", 4.950, 33.17, 2.69],
  ["Almaaz", 5.033, 43.82, 2.99],
  // Gemini
  ["Castor", 7.577, 31.89, 1.58], ["Pollux", 7.755, 28.03, 1.16],
  ["Alhena", 6.629, 16.40, 1.92], ["Wasat", 7.335, 21.98, 3.53],
  ["Mebsuta", 6.732, 25.13, 3.06], ["Tejat", 6.383, 22.51, 2.87],
  // Leo
  ["Regulus", 10.139, 11.97, 1.40], ["Denebola", 11.818, 14.57, 2.14],
  ["Algieba", 10.333, 19.84, 2.08], ["Zosma", 11.235, 20.52, 2.56],
  ["EpsLeo", 9.764, 23.77, 2.97], ["EtaLeo", 10.122, 16.76, 3.49],
  ["TheLeo", 11.237, 15.43, 3.33],
];

const byId = {};
for (const s of STARS) byId[s[0]] = s;

// --- Constellation stick-figures (pairs of star ids) ------------------------
const EDGES = [
  // Ursa Major
  ["Dubhe", "Merak"], ["Merak", "Phecda"], ["Phecda", "Megrez"],
  ["Megrez", "Dubhe"], ["Megrez", "Alioth"], ["Alioth", "Mizar"],
  ["Mizar", "Alkaid"],
  // Ursa Minor
  ["Polaris", "Yildun"], ["Yildun", "EpsUMi"], ["EpsUMi", "ZetUMi"],
  ["ZetUMi", "Pherkad"], ["Pherkad", "Kochab"], ["Kochab", "ZetUMi"],
  // Cassiopeia
  ["Caph", "Schedar"], ["Schedar", "Cih"], ["Cih", "Ruchbah"],
  ["Ruchbah", "Segin"],
  // Cepheus
  ["Alderamin", "Alfirk"], ["Alfirk", "IotCep"], ["IotCep", "Errai"],
  ["Alderamin", "DelCep"], ["DelCep", "ZetCep"], ["ZetCep", "Alfirk"],
  // Cygnus
  ["Deneb", "Sadr"], ["Sadr", "Albireo"], ["Fawaris", "Sadr"],
  ["Sadr", "Gienah"],
  // Lyra
  ["Vega", "ZetLyr"], ["ZetLyr", "DelLyr"], ["DelLyr", "Sulafat"],
  ["Sulafat", "Sheliak"], ["Sheliak", "ZetLyr"],
  // Draco
  ["Eltanin", "Rastaban"], ["Rastaban", "NuDra"], ["NuDra", "Grumium"],
  ["Grumium", "Eltanin"], ["Grumium", "Altais"], ["Altais", "ZetDra"],
  ["ZetDra", "Edasich"], ["Edasich", "Thuban"], ["Thuban", "KapDra"],
  ["KapDra", "LamDra"],
  // Bootes
  ["Arcturus", "Muphrid"], ["Arcturus", "Izar"], ["Izar", "DelBoo"],
  ["DelBoo", "Nekkar"], ["Nekkar", "Seginus"], ["Seginus", "Arcturus"],
  // Corona Borealis
  ["TheCrB", "BetCrB"], ["BetCrB", "Alphecca"], ["Alphecca", "GamCrB"],
  ["GamCrB", "DelCrB"], ["DelCrB", "EpsCrB"],
  // Hercules
  ["ZetHer", "EtaHer"], ["EtaHer", "PiHer"], ["PiHer", "EpsHer"],
  ["EpsHer", "ZetHer"], ["ZetHer", "Korneph"], ["EpsHer", "DelHer"],
  // Pegasus + Andromeda
  ["Alpheratz", "Scheat"], ["Scheat", "Markab"], ["Markab", "Algenib"],
  ["Algenib", "Alpheratz"], ["Alpheratz", "DelAnd"], ["DelAnd", "Mirach"],
  ["Mirach", "Almach"],
  // Perseus
  ["GamPer", "Mirfak"], ["Mirfak", "DelPer"], ["DelPer", "EpsPer"],
  ["EpsPer", "ZetPer"], ["Mirfak", "Algol"],
  // Auriga
  ["Capella", "Almaaz"], ["Almaaz", "Hassaleh"], ["Hassaleh", "Mahasim"],
  ["Mahasim", "Menkalinan"], ["Menkalinan", "Capella"],
  // Gemini
  ["Castor", "Pollux"], ["Castor", "Mebsuta"], ["Mebsuta", "Tejat"],
  ["Pollux", "Wasat"], ["Wasat", "Alhena"],
  // Leo
  ["EpsLeo", "Algieba"], ["Algieba", "EtaLeo"], ["EtaLeo", "Regulus"],
  ["Regulus", "TheLeo"], ["TheLeo", "Denebola"], ["Denebola", "Zosma"],
  ["Zosma", "Algieba"],
];

// --- Magnitude -> marker radius (CSS px in the 1200px mount space) -----------
// Brighter (lower magnitude) -> larger point.
function radius(mag) {
  const v = Math.max(0, Math.min(1, (6.5 - mag) / 6.6));
  return 1.0 + 5.2 * Math.pow(v, 1.5);
}

// --- Bright stars + constellation lines -------------------------------------
const brightData = STARS.map(([id, ra, dec, mag]) => {
  const [x, y] = project(ra, dec);
  return { x, y, name: id, mag, marker: { radius: radius(mag) } };
});

const constLines = [];
for (const [a, b] of EDGES) {
  const sa = byId[a], sb = byId[b];
  const pa = project(sa[1], sa[2]);
  const pb = project(sb[1], sb[2]);
  constLines.push(pa, pb, [null, null]);
}

// --- Deterministic faint background field (no RNG in the browser; tiny LCG) --
let seed = 20260617;
function rnd() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
const fieldData = [];
for (let i = 0; i < 165; i++) {
  const r = 90 * Math.sqrt(rnd()); // uniform spatial density across the disc
  if (r > 88) continue; // keep clear of the boundary ring
  const ang = rnd() * 2 * Math.PI;
  const mag = 4.3 + rnd() * 2.1; // faint stars only
  fieldData.push({ x: r * Math.sin(ang), y: r * Math.cos(ang), marker: { radius: radius(mag) } });
}

// --- Coordinate grid: Dec parallels + RA meridians --------------------------
const gridData = [];
for (const dec of [30, 60]) {
  const r = 90 - dec;
  for (let a = 0; a <= 360; a += 4) {
    gridData.push([r * Math.sin(a * DEG), r * Math.cos(a * DEG)]);
  }
  gridData.push([null, null]);
}
for (let h = 0; h < 24; h += 2) {
  const ang = h * 15 * DEG;
  gridData.push([0, 0], [90 * Math.sin(ang), 90 * Math.cos(ang)], [null, null]);
}

// Boundary ring (celestial equator, dec 0) drawn a touch stronger.
const boundary = [];
for (let a = 0; a <= 360; a += 3) boundary.push([90 * Math.sin(a * DEG), 90 * Math.cos(a * DEG)]);

// --- Ecliptic (Sun's path), dashed amber ------------------------------------
const OBL = 23.4392811 * DEG;
const ecliptic = [];
for (let lon = 0; lon <= 360; lon += 2) {
  const lam = lon * DEG;
  const dec = Math.asin(Math.sin(OBL) * Math.sin(lam)) / DEG;
  if (dec < 0) {
    ecliptic.push([null, null]);
    continue;
  }
  const ang = Math.atan2(Math.cos(OBL) * Math.sin(lam), Math.cos(lam));
  const r = 90 - dec;
  ecliptic.push([r * Math.sin(ang), r * Math.cos(ang)]);
}

// --- Labels (invisible scatter carrying dataLabels) -------------------------
const conLabels = [
  ["UMa", 12.4, 56.5], ["UMi", 16.6, 80.0], ["Cas", 0.95, 60.5],
  ["Cep", 22.3, 66.5], ["Cyg", 20.2, 38.5], ["Lyr", 18.55, 35.0],
  ["Dra", 16.6, 60.5], ["Boo", 14.65, 30.5], ["CrB", 15.65, 23.5],
  ["Her", 16.95, 33.5], ["Peg", 23.55, 21.5], ["And", 1.45, 38.5],
  ["Per", 3.45, 45.5], ["Aur", 5.35, 40.5], ["Gem", 7.10, 24.5],
  ["Leo", 10.6, 18.0],
].map(([name, ra, dec]) => {
  const [x, y] = project(ra, dec);
  return { x, y, name };
});

const raTicks = [];
for (let h = 0; h < 24; h += 2) {
  const ang = h * 15 * DEG;
  const r = 96;
  raTicks.push({ x: r * Math.sin(ang), y: r * Math.cos(ang), name: h + "ʰ" });
}
const decTicks = [30, 60].map((d) => ({ x: 3.5, y: 90 - d, name: "+" + d + "°" }));

// --- Chart ------------------------------------------------------------------
const axis = {
  min: -103, max: 103, gridLineWidth: 0, lineWidth: 0, tickWidth: 0,
  minPadding: 0, maxPadding: 0, startOnTick: false, endOnTick: false,
  labels: { enabled: false }, title: { text: null },
};

Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent", animation: false, margin: [90, 70, 50, 70],
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "star-chart-constellation · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Northern sky · azimuthal-equidistant projection · point size ∝ brightness (apparent magnitude)",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  legend: { enabled: false },
  xAxis: axis,
  yAxis: Object.assign({}, axis),
  tooltip: {
    backgroundColor: t.elevatedBg, borderColor: t.grid,
    style: { color: t.ink, fontSize: "13px" },
  },
  plotOptions: {
    series: { animation: false, enableMouseTracking: false, states: { inactive: { opacity: 1 } } },
  },
  series: [
    // Bright stars first → the brand-green categorical series.
    {
      type: "scatter", name: "Stars", data: brightData, color: BRAND, zIndex: 6,
      enableMouseTracking: true,
      marker: { symbol: "circle", lineWidth: 0.5, lineColor: t.ink, fillColor: BRAND },
      tooltip: { headerFormat: "", pointFormatter() { return "<b>" + this.name + "</b><br/>mag " + this.mag.toFixed(2); } },
    },
    {
      type: "scatter", name: "Field", data: fieldData, color: BRAND, zIndex: 5,
      opacity: 0.5, marker: { symbol: "circle", lineWidth: 0 },
    },
    {
      type: "line", name: "Constellations", data: constLines, zIndex: 4,
      color: LINE_COL, lineWidth: 1.2, marker: { enabled: false }, dashStyle: "Solid",
    },
    {
      type: "line", name: "Ecliptic", data: ecliptic, zIndex: 3,
      color: t.amber, lineWidth: 1.4, dashStyle: "Dash", marker: { enabled: false },
    },
    {
      type: "line", name: "Equator", data: boundary, zIndex: 2,
      color: t.inkSoft, lineWidth: 1.6, marker: { enabled: false },
    },
    {
      type: "line", name: "Grid", data: gridData, zIndex: 1,
      color: t.grid, lineWidth: 1, marker: { enabled: false },
    },
    // Label layers (markers off; only dataLabels render).
    {
      type: "scatter", name: "conLabels", data: conLabels, zIndex: 7,
      marker: { enabled: false },
      dataLabels: {
        enabled: true, allowOverlap: true, format: "{point.name}",
        style: { color: t.ink, fontSize: "14px", fontWeight: "600", fontStyle: "italic", textOutline: "none" },
      },
    },
    {
      type: "scatter", name: "raTicks", data: raTicks, zIndex: 7,
      marker: { enabled: false },
      dataLabels: {
        enabled: true, allowOverlap: true, format: "{point.name}", align: "center", verticalAlign: "middle",
        style: { color: t.inkSoft, fontSize: "12px", fontWeight: "400", textOutline: "none" },
      },
    },
    {
      type: "scatter", name: "decTicks", data: decTicks, zIndex: 7,
      marker: { enabled: false },
      dataLabels: {
        enabled: true, allowOverlap: true, format: "{point.name}", align: "left", verticalAlign: "middle",
        style: { color: t.inkSoft, fontSize: "12px", fontWeight: "400", textOutline: "none" },
      },
    },
  ],
});
