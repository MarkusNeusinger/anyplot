// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 91/100 | Created: 2026-06-17
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Projection -------------------------------------------------------------
// Azimuthal-equidistant map centred on the north celestial pole: declination
// maps linearly to radius (pole at the centre) and right ascension to angle, so
// the sky boundary is a true circle. Showing the northern sky down to dec -35
// keeps Orion and the winter stars in frame.
const DEC_LIMIT = -35;
const R_MAX = 90 - DEC_LIMIT; // 125 — radius of the visible boundary

function project(raHours, decDeg) {
  const r = 90 - decDeg; // 0 at the pole, R_MAX at the boundary
  const theta = (raHours / 24) * 2 * Math.PI; // RA 0h points up, increases CW
  return [r * Math.sin(theta), r * Math.cos(theta)];
}

// --- Constellation catalogue (real bright stars, approx. J2000) -------------
// Each star is [name, RA hours, Dec degrees, apparent magnitude]; edges index
// into the constellation's own star list to form the stick figure.
const CONSTELLATIONS = [
  { abbr: "UMa", stars: [["Dubhe", 11.06, 61.75, 1.79], ["Merak", 11.03, 56.38, 2.37], ["Phecda", 11.90, 53.69, 2.44], ["Megrez", 12.26, 57.03, 3.31], ["Alioth", 12.90, 55.96, 1.77], ["Mizar", 13.40, 54.93, 2.04], ["Alkaid", 13.79, 49.31, 1.86]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 0], [3, 4], [4, 5], [5, 6]] },
  { abbr: "UMi", stars: [["Polaris", 2.53, 89.26, 1.98], ["Yildun", 17.54, 86.59, 4.36], ["Eps UMi", 16.77, 82.04, 4.21], ["Zeta UMi", 15.73, 77.79, 4.32], ["Eta UMi", 16.29, 75.76, 4.95], ["Pherkad", 15.35, 71.83, 3.05], ["Kochab", 14.85, 74.16, 2.08]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 3]] },
  { abbr: "Cas", stars: [["Caph", 0.15, 59.15, 2.28], ["Schedar", 0.68, 56.54, 2.24], ["Gamma Cas", 0.95, 60.72, 2.47], ["Ruchbah", 1.43, 60.24, 2.68], ["Segin", 1.91, 63.67, 3.38]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4]] },
  { abbr: "Cyg", stars: [["Deneb", 20.69, 45.28, 1.25], ["Sadr", 20.37, 40.26, 2.23], ["Gienah", 20.77, 33.97, 2.48], ["Delta Cyg", 19.75, 45.13, 2.87], ["Albireo", 19.51, 27.96, 3.18]],
    edges: [[0, 1], [1, 4], [2, 1], [1, 3]] },
  { abbr: "Lyr", stars: [["Vega", 18.62, 38.78, 0.03], ["Zeta Lyr", 18.75, 37.60, 4.36], ["Delta Lyr", 18.90, 36.90, 4.30], ["Sulafat", 18.98, 32.69, 3.26], ["Sheliak", 18.83, 33.36, 3.52]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 1]] },
  { abbr: "Boo", stars: [["Arcturus", 14.26, 19.18, -0.05], ["Muphrid", 13.91, 18.40, 2.68], ["Izar", 14.75, 27.07, 2.35], ["Delta Boo", 15.26, 33.31, 3.46], ["Nekkar", 15.03, 40.39, 3.49], ["Seginus", 14.53, 38.31, 3.03]],
    edges: [[0, 1], [0, 2], [2, 3], [3, 4], [4, 5], [5, 2]] },
  { abbr: "CrB", stars: [["Theta CrB", 15.55, 31.36, 4.14], ["Nusakan", 15.46, 29.11, 3.66], ["Alphecca", 15.58, 26.71, 2.22], ["Gamma CrB", 15.71, 26.30, 3.81], ["Delta CrB", 15.82, 26.07, 4.59], ["Eps CrB", 15.96, 26.88, 4.13]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]] },
  { abbr: "Leo", stars: [["Regulus", 10.14, 11.97, 1.36], ["Eta Leo", 10.12, 16.76, 3.48], ["Algieba", 10.33, 19.84, 2.08], ["Adhafera", 10.28, 23.42, 3.43], ["Eps Leo", 9.76, 23.77, 2.98], ["Zosma", 11.24, 20.52, 2.56], ["Chort", 11.24, 15.43, 3.33], ["Denebola", 11.82, 14.57, 2.14]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [2, 5], [5, 6], [6, 0], [5, 7], [7, 6]] },
  { abbr: "Gem", stars: [["Pollux", 7.76, 28.03, 1.14], ["Castor", 7.58, 31.89, 1.58], ["Mebsuta", 6.73, 25.13, 3.06], ["Propus", 6.25, 22.51, 3.30], ["Wasat", 7.34, 21.98, 3.53], ["Mekbuda", 7.07, 20.57, 3.90], ["Alhena", 6.63, 16.40, 1.92], ["Tejat", 6.38, 22.51, 2.87]],
    edges: [[1, 0], [1, 2], [2, 3], [0, 4], [4, 5], [5, 6], [2, 7]] },
  { abbr: "Aur", stars: [["Capella", 5.28, 45.99, 0.08], ["Menkalinan", 5.99, 44.95, 1.90], ["Mahasim", 5.99, 37.21, 2.62], ["Elnath", 5.44, 28.61, 1.65], ["Hassaleh", 4.95, 33.17, 2.69], ["Almaaz", 5.03, 43.82, 2.99]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]] },
  { abbr: "Per", stars: [["Mirfak", 3.41, 49.86, 1.79], ["Gamma Per", 3.08, 53.51, 2.91], ["Delta Per", 3.72, 47.79, 3.01], ["Eps Per", 3.96, 40.01, 2.89], ["Zeta Per", 3.90, 31.88, 2.85], ["Algol", 3.14, 40.96, 2.12]],
    edges: [[1, 0], [0, 2], [2, 3], [3, 4], [0, 5]] },
  { abbr: "And", stars: [["Alpheratz", 0.14, 29.09, 2.06], ["Delta And", 0.66, 30.86, 3.27], ["Mirach", 1.16, 35.62, 2.05], ["Almach", 2.06, 42.33, 2.10]],
    edges: [[0, 1], [1, 2], [2, 3]] },
  { abbr: "Peg", stars: [["Markab", 23.08, 15.21, 2.49], ["Scheat", 23.06, 28.08, 2.42], ["Alpheratz", 0.14, 29.09, 2.06], ["Algenib", 0.22, 15.18, 2.83], ["Enif", 21.74, 9.88, 2.39]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 0], [0, 4]] },
  { abbr: "Dra", stars: [["Eltanin", 17.94, 51.49, 2.36], ["Grumium", 17.89, 56.87, 3.73], ["Rastaban", 17.51, 52.30, 2.79], ["Altais", 19.21, 67.66, 3.07], ["Aldhibah", 17.15, 65.71, 3.17], ["Edasich", 15.42, 58.97, 3.29], ["Thuban", 14.07, 64.38, 3.65]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6]] },
  { abbr: "Cep", stars: [["Alderamin", 21.31, 62.59, 2.45], ["Alfirk", 21.48, 70.56, 3.23], ["Errai", 23.66, 77.63, 3.21], ["Iota Cep", 22.83, 66.20, 3.52], ["Zeta Cep", 22.18, 58.20, 3.39]],
    edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]] },
  { abbr: "Ori", stars: [["Betelgeuse", 5.92, 7.41, 0.45], ["Bellatrix", 5.42, 6.35, 1.64], ["Meissa", 5.59, 9.93, 3.39], ["Mintaka", 5.53, -0.30, 2.23], ["Alnilam", 5.60, -1.20, 1.69], ["Alnitak", 5.68, -1.94, 1.74], ["Saiph", 5.80, -9.67, 2.07], ["Rigel", 5.24, -8.20, 0.18]],
    edges: [[1, 0], [0, 2], [2, 1], [1, 3], [3, 4], [4, 5], [5, 0], [5, 6], [6, 7], [7, 3]] },
  { abbr: "Tau", stars: [["Aldebaran", 4.60, 16.51, 0.87], ["Ain", 4.48, 19.18, 3.53], ["Elnath", 5.44, 28.61, 1.65], ["Hyadum", 4.33, 15.63, 3.65], ["Lambda Tau", 4.01, 12.49, 3.41], ["Zeta Tau", 5.63, 21.14, 3.00]],
    edges: [[4, 3], [3, 0], [0, 1], [1, 2], [0, 5]] },
  { abbr: "Ari", stars: [["Hamal", 2.12, 23.46, 2.00], ["Sheratan", 1.91, 20.81, 2.64], ["Mesarthim", 1.89, 19.29, 3.86], ["41 Ari", 2.83, 27.26, 3.61]],
    edges: [[0, 1], [1, 2], [0, 3]] },
  { abbr: "Tri", stars: [["Beta Tri", 2.16, 34.99, 3.00], ["Mothallah", 1.88, 29.59, 3.42], ["Gamma Tri", 2.29, 33.85, 4.01]],
    edges: [[1, 0], [0, 2], [2, 1]] },
  { abbr: "CMi", stars: [["Procyon", 7.66, 5.22, 0.34], ["Gomeisa", 7.45, 8.29, 2.89]],
    edges: [[0, 1]] },
  { abbr: "CVn", stars: [["Cor Caroli", 12.93, 38.32, 2.89], ["Chara", 12.56, 41.36, 4.24]],
    edges: [[0, 1]] },
];

// Flatten the catalogue into scatter points, line segments and centroid labels.
const namedStars = [];
const constLines = [];
const constLabels = [];
for (const c of CONSTELLATIONS) {
  const pts = c.stars.map(([name, ra, dec, mag]) => {
    const [x, y] = project(ra, dec);
    namedStars.push([x, y, mag, name]);
    return [x, y];
  });
  for (const [a, b] of c.edges) constLines.push({ coords: [pts[a], pts[b]] });
  const cx = pts.reduce((s, p) => s + p[0], 0) / pts.length;
  const cy = pts.reduce((s, p) => s + p[1], 0) / pts.length;
  constLabels.push({ value: [cx, cy], name: c.abbr });
}

// --- Background field stars (deterministic, area-uniform in the sky disk) ----
let seed = 1234567;
const rng = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
const fieldStars = [];
for (let i = 0; i < 280; i++) {
  const theta = rng() * 2 * Math.PI;
  const r = R_MAX * Math.sqrt(rng()); // sqrt → uniform density across the disk
  const mag = 4.0 + rng() * 1.6; // faint background, all <= 5.6
  const size = Math.max(1.3, 3.4 - (mag - 4.0) * 1.3);
  fieldStars.push([r * Math.cos(theta), r * Math.sin(theta), size]);
}

// --- Coordinate grid (dec circles + RA radials + boundary) ------------------
const decCircle = (dec) => {
  const pts = [];
  for (let ra = 0; ra <= 24.0001; ra += 0.2) pts.push(project(ra, dec));
  return { coords: pts };
};
const gridLines = [60, 30, 0, -30].map(decCircle);
for (let ra = 0; ra < 24; ra += 3) gridLines.push({ coords: [project(ra, 86), project(ra, DEC_LIMIT)] });

// --- Ecliptic (dashed) ------------------------------------------------------
const eps = (23.4393 * Math.PI) / 180;
const ecliptic = [];
for (let lam = 0; lam <= 360; lam += 2) {
  const L = (lam * Math.PI) / 180;
  let ra = Math.atan2(Math.cos(eps) * Math.sin(L), Math.cos(L));
  if (ra < 0) ra += 2 * Math.PI;
  const dec = (Math.asin(Math.sin(eps) * Math.sin(L)) * 180) / Math.PI;
  ecliptic.push(project((ra / (2 * Math.PI)) * 24, dec));
}

// --- RA / Dec tick labels ---------------------------------------------------
const raTicks = [];
for (let ra = 0; ra < 24; ra += 3) {
  const [x, y] = project(ra, 90 - (R_MAX + 8)); // r = R_MAX + 8, just outside the boundary
  raTicks.push({ value: [x, y], name: `${ra}h` });
}
const decTicks = [60, 30, 0, -30].map((dec) => ({ value: [7, 90 - dec], name: `${dec >= 0 ? "+" : ""}${dec}°` }));

// --- Render -----------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));
const glow = window.ANYPLOT_THEME === "dark" ? 7 : 0;

const series = [
  { id: "grid", type: "lines", coordinateSystem: "cartesian2d", polyline: true, silent: true,
    lineStyle: { color: t.grid, width: 1 }, data: gridLines },
  { id: "boundary", type: "lines", coordinateSystem: "cartesian2d", polyline: true, silent: true,
    lineStyle: { color: t.inkSoft, width: 1.6, opacity: 0.55 }, data: [decCircle(DEC_LIMIT)] },
  { id: "ecliptic", type: "lines", coordinateSystem: "cartesian2d", polyline: true, silent: true,
    lineStyle: { color: t.inkSoft, width: 1.6, opacity: 0.55, type: "dashed" }, data: [{ coords: ecliptic }] },
  { id: "constlines", type: "lines", coordinateSystem: "cartesian2d", polyline: true, silent: true,
    lineStyle: { color: t.inkSoft, width: 1.2, opacity: 0.40 }, data: constLines },
  { id: "field", type: "scatter", coordinateSystem: "cartesian2d", silent: true,
    symbolSize: (d) => d[2], itemStyle: { color: t.inkSoft, opacity: 0.5 }, data: fieldStars },
  { id: "named-stars", type: "scatter", coordinateSystem: "cartesian2d",
    emphasis: { disabled: true },
    itemStyle: { borderColor: t.pageBg, borderWidth: 0.5, shadowBlur: glow, shadowColor: t.inkSoft },
    data: namedStars },
  { id: "const-labels", type: "scatter", coordinateSystem: "cartesian2d", silent: true,
    symbolSize: 6, itemStyle: { color: "transparent" },
    label: { show: true, formatter: "{b}", color: t.inkSoft, fontSize: 15, fontWeight: 500,
             fontStyle: "italic", textShadowColor: t.pageBg, textShadowBlur: 6 }, data: constLabels },
  { id: "ra-ticks", type: "scatter", coordinateSystem: "cartesian2d", silent: true,
    symbolSize: 6, itemStyle: { color: "transparent" },
    label: { show: true, formatter: "{b}", color: t.inkSoft, fontSize: 13,
             textShadowColor: t.pageBg, textShadowBlur: 6 }, data: raTicks },
  { id: "dec-ticks", type: "scatter", coordinateSystem: "cartesian2d", silent: true,
    symbolSize: 6, itemStyle: { color: "transparent" },
    label: { show: true, position: "right", formatter: "{b}", color: t.inkSoft, fontSize: 13,
             textShadowColor: t.pageBg, textShadowBlur: 6 }, data: decTicks },
];

const starsIndex = series.findIndex((s) => s.id === "named-stars");

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "star-chart-constellation · javascript · echarts · anyplot.ai",
    left: "center", top: 24, textStyle: { color: t.ink, fontSize: 22, fontWeight: 600 },
  },
  grid: { left: 60, right: 60, top: 100, bottom: 20 },
  // Magnitude → point size and the Imprint sequential colormap (bright = brand
  // green #009E73, faint = blue). Continuous data, so imprint_seq is used.
  visualMap: {
    type: "continuous", min: -0.5, max: 5.0, dimension: 2, seriesIndex: starsIndex,
    calculable: false, orient: "vertical", left: 28, bottom: 36,
    itemWidth: 18, itemHeight: 150,
    text: ["bright\n−0.5", "5.0\nfaint"], textGap: 10,
    textStyle: { color: t.inkSoft, fontSize: 13 },
    inRange: { symbolSize: [26, 4], color: t.seq },
  },
  xAxis: { type: "value", min: -145, max: 145, show: false },
  yAxis: { type: "value", min: -145, max: 145, show: false },
  series,
});

chart.on("finished", () => { window.__anyplotReady = true; });
