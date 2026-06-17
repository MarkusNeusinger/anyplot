//# anyplot-orientation: square
// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: d3 7.9.0 | JavaScript 22
// Quality: pending | Created: 2026-06-17

const t = window.ANYPLOT_TOKENS;
const { width, height } = window.ANYPLOT_SIZE;

// The night sky is a constant dark sphere on BOTH themes (the spec requires a
// dark navy/black field). Chrome drawn ON the sphere therefore uses constant
// pale tones for legibility; only the page-surface title flips with the theme.
const SKY_MID = "#16223A"; // sphere centre (radial gradient)
const SKY = "#0E1726"; // sphere body
const SKY_EDGE = "#090F1C"; // sphere rim
const GRID_LINE = "rgba(238,235,222,0.16)"; // RA/Dec graticule
const GRID_TXT = "rgba(238,235,222,0.50)"; // dec tick labels (inside the sphere)
const PAGE_TXT = t.inkSoft; // RA tick labels (outside, on the page surface)
const RING = "rgba(238,235,222,0.34)"; // horizon boundary ring
const CON_LABEL = "rgba(238,235,222,0.62)"; // constellation names
const STAR_LABEL = "rgba(244,238,222,0.92)"; // bright-star names
const STAR = t.amber; // pale-yellow stars (#DDCC77, Imprint anchor)
const LINE = t.palette[0]; // constellation stick-figures — brand green #009E73

// --- Geometry: north-polar azimuthal-equidistant projection ------------------
const cx = width / 2;
const cy = height / 2 + 30;
const R = Math.min(width, height) / 2 - 100; // sphere radius
const DEC_EDGE = -10; // declination at the horizon ring
const decToR = (dec) => (R * (90 - dec)) / (90 - DEC_EDGE);
const project = (raHours, dec) => {
  const ang = (raHours / 24) * 2 * Math.PI; // 0h points up, RA winds clockwise
  const r = decToR(dec);
  return [cx + r * Math.sin(ang), cy - r * Math.cos(ang)];
};

// Apparent magnitude → point radius (brighter = lower mag = larger)
const MAG_LIMIT = 6.5;
const MAG_BRIGHT = -1.5;
const magToRadius = (m) => {
  const u = Math.max(0, Math.min(1, (MAG_LIMIT - m) / (MAG_LIMIT - MAG_BRIGHT)));
  return 0.6 + 7.0 * Math.pow(u, 1.5);
};

// --- Data: 15 northern constellations [ra(h), dec(deg), mag, label?] ----------
const cons = [
  { name: "Ursa Major",
    stars: { dubhe: [11.062, 61.75, 1.79], merak: [11.030, 56.38, 2.37],
      phecda: [11.897, 53.69, 2.44], megrez: [12.257, 57.03, 3.31],
      alioth: [12.900, 55.96, 1.77], mizar: [13.399, 54.93, 2.04],
      alkaid: [13.792, 49.31, 1.86] },
    edges: [["dubhe", "merak"], ["merak", "phecda"], ["phecda", "megrez"],
      ["megrez", "dubhe"], ["megrez", "alioth"], ["alioth", "mizar"],
      ["mizar", "alkaid"]] },
  { name: "Ursa Minor",
    stars: { polaris: [2.530, 89.26, 1.98, "Polaris"], yildun: [17.537, 86.59, 4.36],
      eps_umi: [16.766, 82.04, 4.23], zeta_umi: [15.734, 77.79, 4.32],
      eta_umi: [16.291, 75.76, 4.95], pherkad: [15.345, 71.83, 3.00],
      kochab: [14.845, 74.16, 2.07] },
    edges: [["polaris", "yildun"], ["yildun", "eps_umi"], ["eps_umi", "zeta_umi"],
      ["zeta_umi", "eta_umi"], ["eta_umi", "pherkad"], ["pherkad", "kochab"],
      ["kochab", "zeta_umi"]] },
  { name: "Cassiopeia",
    stars: { segin: [1.906, 63.67, 3.35], ruchbah: [1.430, 60.24, 2.68],
      gamma_cas: [0.945, 60.72, 2.47], schedar: [0.675, 56.54, 2.24],
      caph: [0.153, 59.15, 2.28] },
    edges: [["segin", "ruchbah"], ["ruchbah", "gamma_cas"],
      ["gamma_cas", "schedar"], ["schedar", "caph"]] },
  { name: "Cepheus",
    stars: { alderamin: [21.310, 62.59, 2.45], alfirk: [21.477, 70.56, 3.23],
      gamma_cep: [23.656, 77.63, 3.21], iota_cep: [22.828, 66.20, 3.52],
      zeta_cep: [22.181, 58.20, 3.35] },
    edges: [["alderamin", "alfirk"], ["alfirk", "gamma_cep"],
      ["gamma_cep", "iota_cep"], ["iota_cep", "alderamin"],
      ["alderamin", "zeta_cep"]] },
  { name: "Cygnus",
    stars: { deneb: [20.690, 45.28, 1.25, "Deneb"], sadr: [20.370, 40.26, 2.23],
      gienah_cyg: [20.770, 33.97, 2.48], delta_cyg: [19.749, 45.13, 2.87],
      albireo: [19.512, 27.96, 3.18] },
    edges: [["deneb", "sadr"], ["sadr", "albireo"], ["sadr", "gienah_cyg"],
      ["sadr", "delta_cyg"]] },
  { name: "Lyra",
    stars: { vega: [18.616, 38.78, 0.03, "Vega"], eps_lyr: [18.737, 39.67, 3.90],
      zeta_lyr: [18.746, 37.60, 4.30], sheliak: [18.835, 33.36, 3.52],
      sulafat: [18.982, 32.69, 3.25], delta_lyr: [18.908, 36.90, 4.30] },
    edges: [["vega", "eps_lyr"], ["vega", "zeta_lyr"], ["zeta_lyr", "delta_lyr"],
      ["delta_lyr", "sulafat"], ["sulafat", "sheliak"], ["sheliak", "zeta_lyr"]] },
  { name: "Boötes",
    stars: { arcturus: [14.261, 19.18, -0.05, "Arcturus"], izar: [14.749, 27.07, 2.35],
      eta_boo: [13.911, 18.40, 2.68], gamma_boo: [14.534, 38.31, 3.00],
      delta_boo: [15.258, 33.31, 3.46], nekkar: [15.032, 40.39, 3.49] },
    edges: [["arcturus", "eta_boo"], ["arcturus", "izar"], ["izar", "delta_boo"],
      ["delta_boo", "nekkar"], ["nekkar", "gamma_boo"], ["gamma_boo", "arcturus"]] },
  { name: "Corona Borealis",
    stars: { alphecca: [15.578, 26.71, 2.22], beta_crb: [15.464, 29.11, 3.66],
      gamma_crb: [15.711, 26.30, 3.81], delta_crb: [15.825, 26.07, 4.59],
      theta_crb: [15.548, 31.36, 4.14] },
    edges: [["theta_crb", "beta_crb"], ["beta_crb", "alphecca"],
      ["alphecca", "gamma_crb"], ["gamma_crb", "delta_crb"]] },
  { name: "Gemini",
    stars: { pollux: [7.755, 28.03, 1.14, "Pollux"], castor: [7.577, 31.89, 1.58, "Castor"],
      alhena: [6.629, 16.40, 1.93], mu_gem: [6.383, 22.51, 2.87],
      eps_gem: [6.732, 25.13, 3.00], delta_gem: [7.335, 21.98, 3.53] },
    edges: [["castor", "pollux"], ["castor", "eps_gem"], ["eps_gem", "mu_gem"],
      ["pollux", "delta_gem"], ["delta_gem", "alhena"]] },
  { name: "Auriga",
    stars: { capella: [5.278, 45.998, 0.08, "Capella"], menkalinan: [5.992, 44.95, 1.90],
      theta_aur: [5.995, 37.21, 2.62], iota_aur: [4.950, 33.17, 2.69],
      eps_aur: [5.033, 43.82, 3.00] },
    edges: [["capella", "menkalinan"], ["menkalinan", "theta_aur"],
      ["theta_aur", "iota_aur"], ["iota_aur", "eps_aur"], ["eps_aur", "capella"]] },
  { name: "Perseus",
    stars: { mirfak: [3.405, 49.86, 1.79, "Mirfak"], algol: [3.136, 40.96, 2.12, "Algol"],
      gamma_per: [3.080, 53.51, 2.93], delta_per: [3.715, 47.79, 3.01],
      eps_per: [3.964, 40.01, 2.89], zeta_per: [3.902, 31.88, 2.85] },
    edges: [["gamma_per", "mirfak"], ["mirfak", "delta_per"], ["delta_per", "eps_per"],
      ["eps_per", "zeta_per"], ["mirfak", "algol"]] },
  { name: "Andromeda",
    stars: { alpheratz: [0.140, 29.09, 2.06], delta_and: [0.655, 30.86, 3.27],
      mirach: [1.162, 35.62, 2.05], almach: [2.065, 42.33, 2.10] },
    edges: [["alpheratz", "delta_and"], ["delta_and", "mirach"],
      ["mirach", "almach"]] },
  { name: "Pegasus",
    stars: { markab: [23.079, 15.21, 2.48], scheat: [23.063, 28.08, 2.42],
      algenib: [0.220, 15.18, 2.83] },
    edges: [["markab", "scheat"], ["scheat", "alpheratz"],
      ["alpheratz", "algenib"], ["algenib", "markab"]] },
  { name: "Leo",
    stars: { regulus: [10.139, 11.97, 1.36, "Regulus"], denebola: [11.818, 14.57, 2.11],
      algieba: [10.333, 19.84, 2.01], zosma: [11.235, 20.52, 2.56],
      eps_leo: [9.764, 23.77, 2.97], theta_leo: [11.237, 15.43, 3.33],
      eta_leo: [10.122, 16.76, 3.48] },
    edges: [["regulus", "eta_leo"], ["eta_leo", "algieba"], ["algieba", "eps_leo"],
      ["regulus", "theta_leo"], ["theta_leo", "denebola"], ["denebola", "zosma"],
      ["zosma", "algieba"]] },
  { name: "Triangulum",
    stars: { mothallah: [1.885, 29.58, 3.41], beta_tri: [2.159, 34.99, 3.00],
      gamma_tri: [2.288, 33.85, 4.01] },
    edges: [["mothallah", "beta_tri"], ["beta_tri", "gamma_tri"],
      ["gamma_tri", "mothallah"]] },
];

// Flatten constellation stars into a lookup + a render list
const starMap = {};
const namedStars = [];
for (const c of cons) {
  for (const [id, s] of Object.entries(c.stars)) {
    const [ra, dec, mag, label] = s;
    const [x, y] = project(ra, dec);
    starMap[id] = { x, y, mag };
    namedStars.push({ x, y, mag, label });
  }
}

// Constellation stick-figure segments
const edgeData = [];
for (const c of cons) {
  for (const [a, b] of c.edges) {
    if (starMap[a] && starMap[b]) edgeData.push([starMap[a], starMap[b]]);
  }
}

// Constellation labels at the centroid of each star group
const conLabels = cons.map((c) => {
  const pts = Object.keys(c.stars).map((id) => starMap[id]);
  return { name: c.name, x: d3.mean(pts, (p) => p.x), y: d3.mean(pts, (p) => p.y) };
});

// --- Faint background field stars (deterministic LCG, area-uniform on disk) ---
let seed = 20260617;
const rand = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
const fieldStars = [];
for (let i = 0; i < 165; i++) {
  const ang = rand() * 2 * Math.PI;
  const r = R * Math.sqrt(0.01 + 0.98 * rand());
  fieldStars.push({
    x: cx + r * Math.cos(ang),
    y: cy + r * Math.sin(ang),
    mag: 3.8 + rand() * 2.6,
    twinkle: 0.4 + rand() * 0.45,
  });
}

// --- SVG mount ---------------------------------------------------------------
const svg = d3.select("#container").append("svg").attr("width", width).attr("height", height);

const defs = svg.append("defs");
const sky = defs.append("radialGradient").attr("id", "sky").attr("cx", "50%").attr("cy", "42%").attr("r", "62%");
sky.append("stop").attr("offset", "0%").attr("stop-color", SKY_MID);
sky.append("stop").attr("offset", "62%").attr("stop-color", SKY);
sky.append("stop").attr("offset", "100%").attr("stop-color", SKY_EDGE);

const glow = defs.append("filter").attr("id", "glow")
  .attr("x", "-150%").attr("y", "-150%").attr("width", "400%").attr("height", "400%");
glow.append("feGaussianBlur").attr("stdDeviation", 3.4).attr("result", "b");
const merge = glow.append("feMerge");
merge.append("feMergeNode").attr("in", "b");
merge.append("feMergeNode").attr("in", "SourceGraphic");

const clip = defs.append("clipPath").attr("id", "disk");
clip.append("circle").attr("cx", cx).attr("cy", cy).attr("r", R);

// Night-sky sphere
svg.append("circle").attr("cx", cx).attr("cy", cy).attr("r", R).attr("fill", "url(#sky)");

const inner = svg.append("g").attr("clip-path", "url(#disk)");

// --- Coordinate grid: Dec circles + RA spokes --------------------------------
const decCircles = [0, 30, 60, 80];
inner.selectAll("circle.dec").data(decCircles).join("circle")
  .attr("cx", cx).attr("cy", cy).attr("r", (d) => decToR(d))
  .attr("fill", "none").attr("stroke", GRID_LINE).attr("stroke-width", 1);

const raSpokes = d3.range(0, 24, 2);
inner.selectAll("line.ra").data(raSpokes).join("line")
  .attr("x1", cx).attr("y1", cy)
  .attr("x2", (h) => project(h, DEC_EDGE)[0])
  .attr("y2", (h) => project(h, DEC_EDGE)[1])
  .attr("stroke", GRID_LINE).attr("stroke-width", 1);

// --- Constellation stick-figure lines (brand green) --------------------------
inner.selectAll("line.con").data(edgeData).join("line")
  .attr("x1", (d) => d[0].x).attr("y1", (d) => d[0].y)
  .attr("x2", (d) => d[1].x).attr("y2", (d) => d[1].y)
  .attr("stroke", LINE).attr("stroke-width", 1.6).attr("stroke-opacity", 0.55)
  .attr("stroke-linecap", "round");

// --- Field stars (faint background) ------------------------------------------
inner.selectAll("circle.field").data(fieldStars).join("circle")
  .attr("cx", (d) => d.x).attr("cy", (d) => d.y)
  .attr("r", (d) => magToRadius(d.mag))
  .attr("fill", STAR).attr("fill-opacity", (d) => d.twinkle);

// --- Bright-star bloom + named stars -----------------------------------------
inner.selectAll("circle.bloom").data(namedStars.filter((s) => s.mag < 2.4)).join("circle")
  .attr("cx", (d) => d.x).attr("cy", (d) => d.y)
  .attr("r", (d) => magToRadius(d.mag) * 1.9)
  .attr("fill", STAR).attr("fill-opacity", 0.35).attr("filter", "url(#glow)");

inner.selectAll("circle.star").data(namedStars).join("circle")
  .attr("cx", (d) => d.x).attr("cy", (d) => d.y)
  .attr("r", (d) => magToRadius(d.mag))
  .attr("fill", STAR);

// --- Constellation name labels (centroids) -----------------------------------
inner.selectAll("text.con").data(conLabels).join("text")
  .attr("x", (d) => d.x).attr("y", (d) => d.y - 14)
  .attr("text-anchor", "middle").attr("fill", CON_LABEL)
  .style("font-size", "12px").style("font-weight", "500")
  .style("letter-spacing", "1.5px").style("text-transform", "uppercase")
  .text((d) => d.name);

// --- Bright-star name labels --------------------------------------------------
inner.selectAll("text.star").data(namedStars.filter((s) => s.label)).join("text")
  .attr("x", (d) => d.x + magToRadius(d.mag) + 6).attr("y", (d) => d.y + 4)
  .attr("fill", STAR_LABEL).style("font-size", "12.5px").style("font-weight", "500")
  .text((d) => d.label);

// --- Horizon boundary ring ---------------------------------------------------
svg.append("circle").attr("cx", cx).attr("cy", cy).attr("r", R)
  .attr("fill", "none").attr("stroke", RING).attr("stroke-width", 2);

// --- Graticule tick labels (outside the ring & along the meridian) -----------
const raLabels = svg.append("g");
raSpokes.forEach((h) => {
  const [x, y] = project(h, DEC_EDGE);
  const ux = (x - cx) / R;
  const uy = (y - cy) / R;
  raLabels.append("text")
    .attr("x", cx + ux * (R + 22)).attr("y", cy + uy * (R + 22) + 5)
    .attr("text-anchor", "middle").attr("fill", PAGE_TXT)
    .style("font-size", "13px").text(`${h}h`);
});

decCircles.filter((d) => d > 0).forEach((d) => {
  svg.append("text")
    .attr("x", cx + 6).attr("y", cy - decToR(d) + 16)
    .attr("fill", GRID_TXT).style("font-size", "11.5px").text(`+${d}°`);
});

// --- Title -------------------------------------------------------------------
svg.append("text").attr("x", width / 2).attr("y", 46).attr("text-anchor", "middle")
  .attr("fill", t.ink).style("font-size", "22px").style("font-weight", "600")
  .text("star-chart-constellation · javascript · d3 · anyplot.ai");
