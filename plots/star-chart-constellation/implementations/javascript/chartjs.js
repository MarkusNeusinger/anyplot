// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-17
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

// --- Theme-adaptive chrome --------------------------------------------------
const INK = t.ink;
const INK_SOFT = t.inkSoft;
const GRID = t.grid;
const LINE_COL = THEME === "light" ? "rgba(74,74,68,0.45)" : "rgba(184,183,176,0.45)";

// --- Named constellation stars: [RA hours, Dec degrees, apparent magnitude] -
// Real bright northern-sky stars (J2000). The northern celestial hemisphere is
// projected onto a circular azimuthal-equidistant sky map below.
const namedStars = {
  // Ursa Major (Big Dipper)
  Dubhe: [11.062, 61.75, 1.79], Merak: [11.030, 56.38, 2.37],
  Phecda: [11.897, 53.69, 2.44], Megrez: [12.257, 57.03, 3.31],
  Alioth: [12.900, 55.96, 1.77], Mizar: [13.399, 54.93, 2.27],
  Alkaid: [13.792, 49.31, 1.86],
  // Ursa Minor (Little Dipper)
  Polaris: [2.530, 89.26, 1.98], Yildun: [17.537, 86.59, 4.36],
  EpsUMi: [16.766, 82.04, 4.21], ZetaUMi: [15.734, 77.79, 4.32],
  Kochab: [14.845, 74.16, 2.08], Pherkad: [15.345, 71.83, 3.05],
  // Cassiopeia (the W)
  Segin: [1.906, 63.67, 3.35], Ruchbah: [1.430, 60.24, 2.68],
  Navi: [0.945, 60.72, 2.47], Schedar: [0.675, 56.54, 2.24],
  Caph: [0.153, 59.15, 2.28],
  // Cepheus (house)
  Alderamin: [21.310, 62.59, 2.45], Alfirk: [21.477, 70.56, 3.23],
  Errai: [23.656, 77.63, 3.21], CepIota: [22.828, 66.20, 3.52],
  CepZeta: [22.181, 58.20, 3.35],
  // Cygnus (Northern Cross)
  Deneb: [20.690, 45.28, 1.25], Sadr: [20.370, 40.26, 2.23],
  Gienah: [20.770, 33.97, 2.48], CygDelta: [19.749, 45.13, 2.87],
  Albireo: [19.512, 27.96, 3.05],
  // Lyra
  Vega: [18.615, 38.78, 0.03], Sheliak: [18.835, 33.36, 3.52],
  Sulafat: [18.982, 32.69, 3.25], LyrZeta: [18.746, 37.60, 4.36],
  // Bootes (kite)
  Arcturus: [14.261, 19.18, -0.05], Izar: [14.750, 27.07, 2.35],
  Seginus: [14.534, 38.31, 3.03], Nekkar: [15.032, 40.39, 3.49],
  BooDelta: [15.258, 33.31, 3.46], BooRho: [14.532, 30.37, 3.58],
  // Corona Borealis (arc)
  Alphecca: [15.578, 26.71, 2.22], CrBBeta: [15.464, 29.11, 3.66],
  CrBTheta: [15.553, 31.36, 4.14], CrBGamma: [15.713, 26.30, 3.81],
  CrBDelta: [15.825, 26.07, 4.59],
  // Gemini
  Pollux: [7.755, 28.03, 1.14], Castor: [7.577, 31.89, 1.58],
  Alhena: [6.629, 16.40, 1.93], Wasat: [7.335, 21.98, 3.53],
  Mebsuta: [6.382, 25.13, 3.06], Tejat: [6.383, 22.51, 2.87],
  // Auriga (pentagon)
  Capella: [5.278, 45.998, 0.08], Menkalinan: [5.992, 44.95, 1.90],
  AurTheta: [5.995, 37.21, 2.62], ElNath: [5.438, 28.61, 1.65],
  AurIota: [4.950, 33.17, 2.69],
  // Leo
  Regulus: [10.139, 11.97, 1.40], Denebola: [11.818, 14.57, 2.14],
  Algieba: [10.333, 19.84, 2.08], Zosma: [11.235, 20.52, 2.56],
  LeoTheta: [11.237, 15.43, 3.34], LeoEps: [9.879, 23.77, 2.98],
  LeoEta: [10.122, 16.76, 3.48],
  // Andromeda
  Alpheratz: [0.140, 29.09, 2.06], Mirach: [1.162, 35.62, 2.05],
  Almach: [2.065, 42.33, 2.10], AndDelta: [0.655, 30.86, 3.27],
  // Perseus
  Mirfak: [3.405, 49.86, 1.79], Algol: [3.136, 40.96, 2.12],
  PerZeta: [3.902, 31.88, 2.85], PerEps: [3.964, 40.01, 2.89],
  PerGamma: [3.080, 53.51, 2.91], PerDelta: [3.715, 47.79, 3.01],
  // Draco (head + body)
  Eltanin: [17.943, 51.49, 2.36], Rastaban: [17.507, 52.30, 2.79],
  Grumium: [17.892, 56.87, 3.73], DraNu: [17.690, 55.18, 4.88],
  Altais: [19.209, 67.66, 3.07], DraZeta: [17.146, 65.71, 3.17],
  Edasich: [15.415, 58.97, 3.29], DraEta: [16.400, 61.51, 2.73],
  // Triangulum
  TriBeta: [2.159, 34.99, 3.00], TriGamma: [2.288, 33.85, 4.01],
  TriAlpha: [1.884, 29.58, 3.41],
  // Aries
  Hamal: [2.119, 23.46, 2.00], Sheratan: [1.911, 20.81, 2.64],
  Mesarthim: [1.892, 19.29, 3.86],
  // Pegasus (great square, with shared Alpheratz)
  Markab: [23.079, 15.21, 2.48], Scheat: [23.063, 28.08, 2.42],
  Algenib: [0.220, 15.18, 2.83],
  // Hercules (keystone)
  HerZeta: [16.688, 31.60, 2.81], HerEta: [16.715, 38.92, 3.48],
  HerPi: [17.251, 36.81, 3.16], HerEps: [17.005, 30.93, 3.92],
  // Canes Venatici
  CorCaroli: [12.934, 38.32, 2.89], Chara: [12.563, 41.36, 4.24],
  // Delphinus
  Sualocin: [20.660, 15.91, 3.77], Rotanev: [20.626, 14.60, 3.64],
  DelGamma: [20.776, 16.12, 4.27], DelDelta: [20.725, 15.07, 4.43],
};

// Constellation stick-figures: name + edges between named stars.
const constellations = [
  { name: "Ursa Major", edges: [["Dubhe", "Merak"], ["Merak", "Phecda"], ["Phecda", "Megrez"], ["Megrez", "Dubhe"], ["Megrez", "Alioth"], ["Alioth", "Mizar"], ["Mizar", "Alkaid"]] },
  { name: "Ursa Minor", edges: [["Polaris", "Yildun"], ["Yildun", "EpsUMi"], ["EpsUMi", "ZetaUMi"], ["ZetaUMi", "Kochab"], ["Kochab", "Pherkad"], ["Pherkad", "EpsUMi"]] },
  { name: "Cassiopeia", edges: [["Segin", "Ruchbah"], ["Ruchbah", "Navi"], ["Navi", "Schedar"], ["Schedar", "Caph"]] },
  { name: "Cepheus", edges: [["Alderamin", "Alfirk"], ["Alfirk", "Errai"], ["Errai", "CepIota"], ["CepIota", "CepZeta"], ["CepZeta", "Alderamin"]] },
  { name: "Cygnus", edges: [["Deneb", "Sadr"], ["Sadr", "Albireo"], ["CygDelta", "Sadr"], ["Sadr", "Gienah"]] },
  { name: "Lyra", edges: [["Vega", "LyrZeta"], ["LyrZeta", "Sulafat"], ["Sulafat", "Sheliak"], ["Sheliak", "LyrZeta"]] },
  { name: "Bootes", edges: [["Arcturus", "Izar"], ["Izar", "Nekkar"], ["Nekkar", "Seginus"], ["Seginus", "BooRho"], ["BooRho", "Arcturus"], ["Izar", "BooDelta"]] },
  { name: "Corona Borealis", edges: [["CrBTheta", "CrBBeta"], ["CrBBeta", "Alphecca"], ["Alphecca", "CrBGamma"], ["CrBGamma", "CrBDelta"]] },
  { name: "Gemini", edges: [["Pollux", "Castor"], ["Pollux", "Wasat"], ["Wasat", "Alhena"], ["Castor", "Mebsuta"], ["Mebsuta", "Tejat"]] },
  { name: "Auriga", edges: [["Capella", "Menkalinan"], ["Menkalinan", "AurTheta"], ["AurTheta", "ElNath"], ["ElNath", "AurIota"], ["AurIota", "Capella"]] },
  { name: "Leo", edges: [["Regulus", "LeoEta"], ["LeoEta", "Algieba"], ["Algieba", "LeoEps"], ["Regulus", "LeoTheta"], ["LeoTheta", "Zosma"], ["Zosma", "Algieba"], ["Zosma", "Denebola"]] },
  { name: "Andromeda", edges: [["Alpheratz", "AndDelta"], ["AndDelta", "Mirach"], ["Mirach", "Almach"]] },
  { name: "Perseus", edges: [["Mirfak", "PerGamma"], ["Mirfak", "PerDelta"], ["PerDelta", "PerEps"], ["PerEps", "PerZeta"], ["Mirfak", "Algol"]] },
  { name: "Draco", edges: [["Eltanin", "Rastaban"], ["Rastaban", "Grumium"], ["Grumium", "DraNu"], ["DraNu", "Eltanin"], ["Eltanin", "Altais"], ["Altais", "DraZeta"], ["DraZeta", "DraEta"], ["DraEta", "Edasich"]] },
  { name: "Triangulum", edges: [["TriAlpha", "TriBeta"], ["TriBeta", "TriGamma"], ["TriGamma", "TriAlpha"]] },
  { name: "Aries", edges: [["Hamal", "Sheratan"], ["Sheratan", "Mesarthim"]] },
  { name: "Pegasus", edges: [["Markab", "Scheat"], ["Scheat", "Alpheratz"], ["Alpheratz", "Algenib"], ["Algenib", "Markab"]] },
  { name: "Hercules", edges: [["HerZeta", "HerEta"], ["HerEta", "HerPi"], ["HerPi", "HerEps"], ["HerEps", "HerZeta"]] },
  { name: "Canes Venatici", edges: [["CorCaroli", "Chara"]] },
  { name: "Delphinus", edges: [["Sualocin", "DelGamma"], ["DelGamma", "DelDelta"], ["DelDelta", "Rotanev"], ["Rotanev", "Sualocin"]] },
];

// --- Projection: azimuthal equidistant from the north celestial pole --------
// Radius = angular distance from pole (90 - dec); azimuth = right ascension.
// Disk boundary sits at the celestial equator (dec = 0, r = 90).
const project = (raHours, decDeg) => {
  const r = 90 - decDeg;
  const ang = (raHours / 24) * 2 * Math.PI;
  return { x: r * Math.sin(ang), y: r * Math.cos(ang) };
};

// --- Magnitude → continuous Imprint colour + point size ---------------------
// Continuous data (brightness), so use the Imprint sequential ramp: the
// brightest stars anchor at #009E73 (palette position 1), faint stars → blue.
const MAG_MIN = -0.1;
const MAG_MAX = 6.5;
const hexToRgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const seqA = hexToRgb(t.seq[0]);
const seqB = hexToRgb(t.seq[1]);
const magColor = (mag) => {
  const f = Math.min(1, Math.max(0, (mag - MAG_MIN) / (MAG_MAX - MAG_MIN)));
  const c = seqA.map((a, i) => Math.round(a + (seqB[i] - a) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
};
const magRadius = (mag) => 1.5 + (MAG_MAX - mag) * 1.45;

// --- Build the star point set -----------------------------------------------
const points = [];
const radii = [];
const colors = [];
const projected = {}; // name → {x, y} for the line/label plugin

for (const [name, [ra, dec, mag]] of Object.entries(namedStars)) {
  const p = project(ra, dec);
  projected[name] = p;
  points.push(p);
  radii.push(magRadius(mag));
  colors.push(magColor(mag));
}

// Deterministic faint field stars (fixed-seed LCG) for an even, areal sky fill.
let seed = 20260617;
const rng = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};
for (let i = 0; i < 240; i++) {
  const r = 90 * Math.sqrt(rng()); // uniform over the disk area
  const ang = rng() * 2 * Math.PI;
  const mag = 3.6 + rng() * 2.7;
  points.push({ x: r * Math.sin(ang), y: r * Math.cos(ang) });
  radii.push(magRadius(mag));
  colors.push(magColor(mag));
}

// --- Plugin: RA/Dec grid, constellation lines, labels, magnitude key --------
const skyPlugin = {
  id: "skyChart",
  beforeDatasetsDraw(chart) {
    const { ctx, scales: { x, y } } = chart;
    const toPx = (X, Y) => [x.getPixelForValue(X), y.getPixelForValue(Y)];

    // Dec circles (dec = 0, 30, 60) sampled through the projection so they stay
    // aligned with the star coordinates regardless of plot-area aspect.
    ctx.save();
    ctx.strokeStyle = GRID;
    ctx.lineWidth = 1;
    for (const decRing of [0, 30, 60]) {
      const rad = 90 - decRing;
      ctx.lineWidth = decRing === 0 ? 1.8 : 1;
      ctx.beginPath();
      for (let k = 0; k <= 120; k++) {
        const a = (k / 120) * 2 * Math.PI;
        const [px, py] = toPx(rad * Math.sin(a), rad * Math.cos(a));
        k === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // RA spokes every 2h from centre to the equator boundary.
    ctx.lineWidth = 1;
    const [cx, cy] = toPx(0, 0);
    for (let h = 0; h < 24; h += 2) {
      const a = (h / 24) * 2 * Math.PI;
      const [ex, ey] = toPx(90 * Math.sin(a), 90 * Math.cos(a));
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(ex, ey);
      ctx.stroke();
    }
    ctx.restore();

    // Constellation stick-figure lines (thin, semi-transparent).
    ctx.save();
    ctx.strokeStyle = LINE_COL;
    ctx.lineWidth = 1.6;
    ctx.lineCap = "round";
    for (const c of constellations) {
      for (const [a, b] of c.edges) {
        const [ax, ay] = toPx(projected[a].x, projected[a].y);
        const [bx, by] = toPx(projected[b].x, projected[b].y);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(bx, by);
        ctx.stroke();
      }
    }
    ctx.restore();
  },

  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales: { x, y } } = chart;
    const toPx = (X, Y) => [x.getPixelForValue(X), y.getPixelForValue(Y)];

    // RA labels (hours) just outside the boundary.
    ctx.save();
    ctx.fillStyle = INK_SOFT;
    ctx.font = "600 13px -apple-system, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (const h of [0, 3, 6, 9, 12, 15, 18, 21]) {
      const a = (h / 24) * 2 * Math.PI;
      const [px, py] = toPx(98 * Math.sin(a), 98 * Math.cos(a));
      ctx.fillText(`${h}h`, px, py);
    }

    // Dec ring labels along the 0h spoke (top); skip the boundary to avoid
    // colliding with the 0h RA label.
    ctx.font = "12px -apple-system, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "left";
    for (const decRing of [30, 60]) {
      const [px, py] = toPx(0, 90 - decRing);
      ctx.fillText(`+${decRing}°`, px + 5, py - 8);
    }
    ctx.restore();

    // Constellation name labels near each group's centroid.
    ctx.save();
    ctx.fillStyle = INK;
    ctx.font = "italic 600 13px -apple-system, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (const c of constellations) {
      const names = [...new Set(c.edges.flat())];
      let sx = 0, sy = 0;
      for (const n of names) { sx += projected[n].x; sy += projected[n].y; }
      const [px, py] = toPx(sx / names.length, sy / names.length);
      ctx.fillText(c.name, px, py);
    }
    ctx.restore();

    // Magnitude size key (bottom-left): a legend, not a fake control.
    ctx.save();
    const keyX = chartArea.left + 20;
    let keyY = chartArea.bottom - 96;
    ctx.fillStyle = INK;
    ctx.font = "600 14px -apple-system, Segoe UI, Roboto, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText("Apparent magnitude", keyX, keyY);
    keyY += 26;
    ctx.font = "12px -apple-system, Segoe UI, Roboto, sans-serif";
    for (const mag of [0, 2, 4]) {
      ctx.beginPath();
      ctx.fillStyle = magColor(mag);
      ctx.arc(keyX + 8, keyY, magRadius(mag), 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = INK_SOFT;
      const note = mag === 0 ? " · bright" : mag === 4 ? " · faint" : "";
      ctx.fillText(`mag ${mag}${note}`, keyX + 30, keyY);
      keyY += 24;
    }
    ctx.restore();
  },
};

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [{
      label: "Stars",
      data: points,
      pointRadius: radii,
      pointBackgroundColor: colors,
      pointBorderWidth: 0,
      pointHoverRadius: radii,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 12 },
    plugins: {
      title: {
        display: true,
        text: "star-chart-constellation · javascript · chartjs · anyplot.ai",
        color: INK,
        font: { size: 22, weight: "600" },
        padding: { top: 4, bottom: 14 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: { type: "linear", min: -98, max: 98, display: false },
      y: { type: "linear", min: -98, max: 98, display: false },
    },
  },
  plugins: [skyPlugin],
});
