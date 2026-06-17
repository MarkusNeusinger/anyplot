// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 94/100 | Created: 2026-06-17
//# anyplot-orientation: square
// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-17
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

// --- Theme tokens (chrome is theme-adaptive; data colours are not) -----------
const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;
// Continuous brightness → Imprint sequential ramp (brand green → blue).
const SEQ = t.seq; // ["#009E73", "#4467A3"]

// --- Projection: north-pole azimuthal equidistant ----------------------------
// dec = +90 maps to the centre, the rim sits at DEC_MIN. RA spins the angle.
const DEC_MIN = -52;
const R_MAX = 90 - DEC_MIN; // angular distance (deg) from the pole at the rim
function project(raHours, decDeg) {
  const theta = (raHours / 24) * 2 * Math.PI;
  const rr = (90 - decDeg) / R_MAX;
  return { x: rr * Math.sin(theta), y: rr * Math.cos(theta) };
}

// --- Star catalogue (real bright stars, RA in hours, Dec in degrees) ---------
// con = IAU constellation abbreviation. Coordinates are approximate J2000.
const CATALOG = [
  // Ursa Major — the Big Dipper
  { name: "Dubhe", ra: 11.06, dec: 61.75, mag: 1.79, con: "UMa" },
  { name: "Merak", ra: 11.03, dec: 56.38, mag: 2.37, con: "UMa" },
  { name: "Phecda", ra: 11.90, dec: 53.69, mag: 2.44, con: "UMa" },
  { name: "Megrez", ra: 12.26, dec: 57.03, mag: 3.31, con: "UMa" },
  { name: "Alioth", ra: 12.90, dec: 55.96, mag: 1.77, con: "UMa" },
  { name: "Mizar", ra: 13.40, dec: 54.93, mag: 2.04, con: "UMa" },
  { name: "Alkaid", ra: 13.79, dec: 49.31, mag: 1.86, con: "UMa" },
  // Ursa Minor — the Little Dipper
  { name: "Polaris", ra: 2.53, dec: 89.26, mag: 1.98, con: "UMi" },
  { name: "Yildun", ra: 17.54, dec: 86.59, mag: 4.36, con: "UMi" },
  { name: "EpsUMi", ra: 16.77, dec: 82.04, mag: 4.21, con: "UMi" },
  { name: "ZetUMi", ra: 15.73, dec: 77.79, mag: 4.32, con: "UMi" },
  { name: "Kochab", ra: 14.85, dec: 74.16, mag: 2.07, con: "UMi" },
  { name: "Pherkad", ra: 15.35, dec: 71.83, mag: 3.05, con: "UMi" },
  // Cassiopeia — the W
  { name: "Caph", ra: 0.15, dec: 59.15, mag: 2.28, con: "Cas" },
  { name: "Schedar", ra: 0.68, dec: 56.54, mag: 2.24, con: "Cas" },
  { name: "GamCas", ra: 0.95, dec: 60.72, mag: 2.47, con: "Cas" },
  { name: "Ruchbah", ra: 1.43, dec: 60.24, mag: 2.68, con: "Cas" },
  { name: "Segin", ra: 1.91, dec: 63.67, mag: 3.35, con: "Cas" },
  // Cepheus — the house
  { name: "Alderamin", ra: 21.31, dec: 62.59, mag: 2.45, con: "Cep" },
  { name: "BetCep", ra: 21.48, dec: 70.56, mag: 3.23, con: "Cep" },
  { name: "GamCep", ra: 23.66, dec: 77.63, mag: 3.21, con: "Cep" },
  { name: "IotCep", ra: 22.83, dec: 66.20, mag: 3.52, con: "Cep" },
  { name: "ZetCep", ra: 22.18, dec: 58.20, mag: 3.35, con: "Cep" },
  // Cygnus — the Northern Cross
  { name: "Deneb", ra: 20.69, dec: 45.28, mag: 1.25, con: "Cyg" },
  { name: "Sadr", ra: 20.37, dec: 40.26, mag: 2.23, con: "Cyg" },
  { name: "Gienah", ra: 20.77, dec: 33.97, mag: 2.48, con: "Cyg" },
  { name: "DelCyg", ra: 19.75, dec: 45.13, mag: 2.87, con: "Cyg" },
  { name: "Albireo", ra: 19.51, dec: 27.96, mag: 3.18, con: "Cyg" },
  // Lyra
  { name: "Vega", ra: 18.62, dec: 38.78, mag: 0.03, con: "Lyr" },
  { name: "Sheliak", ra: 18.83, dec: 33.36, mag: 3.52, con: "Lyr" },
  { name: "Sulafat", ra: 18.98, dec: 32.69, mag: 3.26, con: "Lyr" },
  { name: "ZetLyr", ra: 18.75, dec: 37.60, mag: 4.36, con: "Lyr" },
  { name: "DelLyr", ra: 18.90, dec: 36.90, mag: 4.30, con: "Lyr" },
  // Aquila
  { name: "Altair", ra: 19.85, dec: 8.87, mag: 0.76, con: "Aql" },
  { name: "Tarazed", ra: 19.77, dec: 10.61, mag: 2.72, con: "Aql" },
  { name: "Alshain", ra: 19.92, dec: 6.41, mag: 3.71, con: "Aql" },
  { name: "DelAql", ra: 19.42, dec: 3.11, mag: 3.36, con: "Aql" },
  { name: "ZetAql", ra: 19.09, dec: 13.86, mag: 2.99, con: "Aql" },
  // Bootes — the kite
  { name: "Arcturus", ra: 14.26, dec: 19.18, mag: -0.05, con: "Boo" },
  { name: "Izar", ra: 14.75, dec: 27.07, mag: 2.35, con: "Boo" },
  { name: "Seginus", ra: 14.53, dec: 38.31, mag: 3.03, con: "Boo" },
  { name: "Nekkar", ra: 15.03, dec: 40.39, mag: 3.49, con: "Boo" },
  { name: "Muphrid", ra: 13.91, dec: 18.40, mag: 2.68, con: "Boo" },
  // Corona Borealis — the crown arc
  { name: "ThetCrB", ra: 15.55, dec: 31.36, mag: 4.13, con: "CrB" },
  { name: "BetCrB", ra: 15.46, dec: 29.10, mag: 3.66, con: "CrB" },
  { name: "Alphecca", ra: 15.58, dec: 26.71, mag: 2.22, con: "CrB" },
  { name: "GamCrB", ra: 15.71, dec: 26.30, mag: 3.80, con: "CrB" },
  { name: "DelCrB", ra: 15.82, dec: 26.07, mag: 4.59, con: "CrB" },
  // Hercules — the keystone
  { name: "ZetHer", ra: 16.69, dec: 31.60, mag: 2.81, con: "Her" },
  { name: "EtaHer", ra: 16.72, dec: 38.92, mag: 3.48, con: "Her" },
  { name: "PiHer", ra: 17.25, dec: 36.81, mag: 3.16, con: "Her" },
  { name: "EpsHer", ra: 17.00, dec: 30.93, mag: 3.92, con: "Her" },
  // Draco — winding tail
  { name: "Eltanin", ra: 17.94, dec: 51.49, mag: 2.36, con: "Dra" },
  { name: "Rastaban", ra: 17.51, dec: 52.30, mag: 2.79, con: "Dra" },
  { name: "Grumium", ra: 17.89, dec: 56.87, mag: 3.75, con: "Dra" },
  { name: "DelDra", ra: 19.21, dec: 67.66, mag: 3.07, con: "Dra" },
  { name: "ZetDra", ra: 17.15, dec: 65.71, mag: 3.17, con: "Dra" },
  { name: "Edasich", ra: 15.42, dec: 58.97, mag: 3.29, con: "Dra" },
  { name: "Thuban", ra: 14.07, dec: 64.38, mag: 3.65, con: "Dra" },
  // Perseus
  { name: "Mirfak", ra: 3.41, dec: 49.86, mag: 1.79, con: "Per" },
  { name: "Algol", ra: 3.14, dec: 40.96, mag: 2.12, con: "Per" },
  { name: "GamPer", ra: 3.08, dec: 53.51, mag: 2.93, con: "Per" },
  { name: "DelPer", ra: 3.72, dec: 47.79, mag: 3.01, con: "Per" },
  { name: "EpsPer", ra: 3.96, dec: 40.01, mag: 2.89, con: "Per" },
  // Auriga — the pentagon
  { name: "Capella", ra: 5.28, dec: 46.00, mag: 0.08, con: "Aur" },
  { name: "Menkalinan", ra: 5.99, dec: 44.95, mag: 1.90, con: "Aur" },
  { name: "ThetAur", ra: 6.00, dec: 37.21, mag: 2.62, con: "Aur" },
  { name: "IotAur", ra: 4.95, dec: 33.17, mag: 2.69, con: "Aur" },
  // Andromeda
  { name: "Alpheratz", ra: 0.14, dec: 29.09, mag: 2.06, con: "And" },
  { name: "Mirach", ra: 1.16, dec: 35.62, mag: 2.05, con: "And" },
  { name: "Almach", ra: 2.07, dec: 42.33, mag: 2.10, con: "And" },
  { name: "DelAnd", ra: 0.66, dec: 30.86, mag: 3.27, con: "And" },
  // Pegasus — the Great Square
  { name: "Markab", ra: 23.08, dec: 15.21, mag: 2.49, con: "Peg" },
  { name: "Scheat", ra: 23.06, dec: 28.08, mag: 2.42, con: "Peg" },
  { name: "Algenib", ra: 0.22, dec: 15.18, mag: 2.83, con: "Peg" },
  { name: "Enif", ra: 21.74, dec: 9.88, mag: 2.39, con: "Peg" },
  // Triangulum
  { name: "BetTri", ra: 2.16, dec: 34.99, mag: 3.00, con: "Tri" },
  { name: "AlpTri", ra: 1.88, dec: 29.59, mag: 3.42, con: "Tri" },
  { name: "GamTri", ra: 2.29, dec: 33.85, mag: 4.01, con: "Tri" },
  // Aries
  { name: "Hamal", ra: 2.12, dec: 23.46, mag: 2.00, con: "Ari" },
  { name: "Sheratan", ra: 1.91, dec: 20.81, mag: 2.64, con: "Ari" },
  { name: "Mesarthim", ra: 1.89, dec: 19.29, mag: 3.86, con: "Ari" },
  // Gemini — the twins
  { name: "Pollux", ra: 7.76, dec: 28.03, mag: 1.14, con: "Gem" },
  { name: "Castor", ra: 7.58, dec: 31.89, mag: 1.58, con: "Gem" },
  { name: "Alhena", ra: 6.63, dec: 16.40, mag: 1.92, con: "Gem" },
  { name: "Wasat", ra: 7.34, dec: 21.98, mag: 3.53, con: "Gem" },
  { name: "Mebsuta", ra: 6.73, dec: 25.13, mag: 3.06, con: "Gem" },
  { name: "MuGem", ra: 6.38, dec: 22.51, mag: 2.87, con: "Gem" },
  // Leo — the sickle and triangle
  { name: "Regulus", ra: 10.14, dec: 11.97, mag: 1.36, con: "Leo" },
  { name: "Denebola", ra: 11.82, dec: 14.57, mag: 2.14, con: "Leo" },
  { name: "Algieba", ra: 10.33, dec: 19.84, mag: 2.08, con: "Leo" },
  { name: "Zosma", ra: 11.24, dec: 20.52, mag: 2.56, con: "Leo" },
  { name: "ThetLeo", ra: 11.24, dec: 15.43, mag: 3.33, con: "Leo" },
  { name: "EpsLeo", ra: 9.76, dec: 23.77, mag: 2.98, con: "Leo" },
  { name: "EtaLeo", ra: 10.12, dec: 16.76, mag: 3.48, con: "Leo" },
  // Canes Venatici
  { name: "CorCaroli", ra: 12.93, dec: 38.32, mag: 2.89, con: "CVn" },
  { name: "BetCVn", ra: 12.56, dec: 41.36, mag: 4.24, con: "CVn" },
  // Taurus — the V and horns (Elnath shared with Auriga)
  { name: "Aldebaran", ra: 4.60, dec: 16.51, mag: 0.87, con: "Tau" },
  { name: "Elnath", ra: 5.44, dec: 28.61, mag: 1.65, con: "Tau" },
  { name: "ZetTau", ra: 5.63, dec: 21.14, mag: 3.00, con: "Tau" },
  { name: "GamTau", ra: 4.33, dec: 15.63, mag: 3.65, con: "Tau" },
  { name: "EpsTau", ra: 4.48, dec: 19.18, mag: 3.53, con: "Tau" },
  { name: "LamTau", ra: 4.01, dec: 12.49, mag: 3.47, con: "Tau" },
  // Orion — the hunter
  { name: "Betelgeuse", ra: 5.92, dec: 7.41, mag: 0.45, con: "Ori" },
  { name: "Rigel", ra: 5.24, dec: -8.20, mag: 0.18, con: "Ori" },
  { name: "Bellatrix", ra: 5.42, dec: 6.35, mag: 1.64, con: "Ori" },
  { name: "Saiph", ra: 5.80, dec: -9.67, mag: 2.07, con: "Ori" },
  { name: "Alnitak", ra: 5.68, dec: -1.94, mag: 1.77, con: "Ori" },
  { name: "Alnilam", ra: 5.60, dec: -1.20, mag: 1.69, con: "Ori" },
  { name: "Mintaka", ra: 5.53, dec: -0.30, mag: 2.23, con: "Ori" },
  // Canis Major — Sirius and the dog
  { name: "Sirius", ra: 6.75, dec: -16.72, mag: -1.46, con: "CMa" },
  { name: "Mirzam", ra: 6.38, dec: -17.96, mag: 1.98, con: "CMa" },
  { name: "Wezen", ra: 7.14, dec: -26.39, mag: 1.83, con: "CMa" },
  { name: "Adhara", ra: 6.98, dec: -28.97, mag: 1.50, con: "CMa" },
  { name: "Aludra", ra: 7.40, dec: -29.30, mag: 2.45, con: "CMa" },
];

// --- Constellation stick figures (pairs of catalogue names) ------------------
const EDGES = [
  // Ursa Major
  ["Dubhe", "Merak"], ["Merak", "Phecda"], ["Phecda", "Megrez"], ["Megrez", "Dubhe"],
  ["Megrez", "Alioth"], ["Alioth", "Mizar"], ["Mizar", "Alkaid"],
  // Ursa Minor
  ["Polaris", "Yildun"], ["Yildun", "EpsUMi"], ["EpsUMi", "ZetUMi"], ["ZetUMi", "Kochab"],
  ["Kochab", "Pherkad"], ["Pherkad", "EpsUMi"],
  // Cassiopeia
  ["Caph", "Schedar"], ["Schedar", "GamCas"], ["GamCas", "Ruchbah"], ["Ruchbah", "Segin"],
  // Cepheus
  ["Alderamin", "BetCep"], ["BetCep", "GamCep"], ["GamCep", "IotCep"], ["IotCep", "ZetCep"],
  ["ZetCep", "Alderamin"],
  // Cygnus
  ["Deneb", "Sadr"], ["Sadr", "Albireo"], ["Sadr", "Gienah"], ["Sadr", "DelCyg"],
  // Lyra
  ["Vega", "ZetLyr"], ["ZetLyr", "Sheliak"], ["Sheliak", "Sulafat"], ["Sulafat", "DelLyr"],
  ["DelLyr", "ZetLyr"],
  // Aquila
  ["Tarazed", "Altair"], ["Altair", "Alshain"], ["Altair", "DelAql"], ["DelAql", "ZetAql"],
  // Bootes
  ["Arcturus", "Izar"], ["Izar", "Nekkar"], ["Nekkar", "Seginus"], ["Seginus", "Arcturus"],
  ["Arcturus", "Muphrid"],
  // Corona Borealis
  ["ThetCrB", "BetCrB"], ["BetCrB", "Alphecca"], ["Alphecca", "GamCrB"], ["GamCrB", "DelCrB"],
  // Hercules
  ["ZetHer", "EtaHer"], ["EtaHer", "PiHer"], ["PiHer", "EpsHer"], ["EpsHer", "ZetHer"],
  // Draco
  ["Eltanin", "Rastaban"], ["Rastaban", "Grumium"], ["Grumium", "Eltanin"],
  ["Grumium", "DelDra"], ["DelDra", "ZetDra"], ["ZetDra", "Edasich"], ["Edasich", "Thuban"],
  // Perseus
  ["GamPer", "Mirfak"], ["Mirfak", "DelPer"], ["DelPer", "EpsPer"], ["Mirfak", "Algol"],
  // Auriga
  ["Capella", "Menkalinan"], ["Menkalinan", "ThetAur"], ["ThetAur", "Elnath"],
  ["Elnath", "IotAur"], ["IotAur", "Capella"],
  // Andromeda
  ["Alpheratz", "DelAnd"], ["DelAnd", "Mirach"], ["Mirach", "Almach"],
  // Pegasus
  ["Markab", "Scheat"], ["Scheat", "Alpheratz"], ["Alpheratz", "Algenib"], ["Algenib", "Markab"],
  ["Markab", "Enif"],
  // Triangulum
  ["BetTri", "AlpTri"], ["AlpTri", "GamTri"], ["GamTri", "BetTri"],
  // Aries
  ["Hamal", "Sheratan"], ["Sheratan", "Mesarthim"],
  // Gemini
  ["Castor", "Pollux"], ["Pollux", "Wasat"], ["Wasat", "Alhena"],
  ["Castor", "Mebsuta"], ["Mebsuta", "MuGem"],
  // Leo
  ["Regulus", "EtaLeo"], ["EtaLeo", "Algieba"], ["Algieba", "EpsLeo"],
  ["Regulus", "ThetLeo"], ["ThetLeo", "Zosma"], ["Zosma", "Denebola"], ["Denebola", "ThetLeo"],
  ["Zosma", "Algieba"],
  // Canes Venatici
  ["CorCaroli", "BetCVn"],
  // Taurus
  ["LamTau", "GamTau"], ["GamTau", "EpsTau"], ["EpsTau", "Aldebaran"], ["Aldebaran", "ZetTau"],
  ["EpsTau", "Elnath"],
  // Orion
  ["Betelgeuse", "Bellatrix"], ["Betelgeuse", "Alnitak"], ["Bellatrix", "Mintaka"],
  ["Mintaka", "Alnilam"], ["Alnilam", "Alnitak"], ["Alnitak", "Saiph"], ["Saiph", "Rigel"],
  ["Rigel", "Mintaka"],
  // Canis Major
  ["Sirius", "Mirzam"], ["Sirius", "Wezen"], ["Wezen", "Adhara"], ["Wezen", "Aludra"],
];

// Display names placed near each constellation's centroid.
const CON_NAMES = {
  UMa: "Ursa Major", UMi: "Ursa Minor", Cas: "Cassiopeia", Cep: "Cepheus",
  Cyg: "Cygnus", Lyr: "Lyra", Aql: "Aquila", Boo: "Boötes", CrB: "Corona Borealis",
  Her: "Hercules", Dra: "Draco", Per: "Perseus", Aur: "Auriga", And: "Andromeda",
  Peg: "Pegasus", Tri: "Triangulum", Ari: "Aries", Gem: "Gemini", Leo: "Leo",
  CVn: "Canes Venatici", Tau: "Taurus", Ori: "Orion", CMa: "Canis Major",
};

// --- Background field of faint stars (deterministic LCG, no network) ---------
let _seed = 1337;
function rand() {
  _seed = (_seed * 1103515245 + 12345) & 0x7fffffff;
  return _seed / 0x7fffffff;
}
const FIELD = [];
for (let i = 0; i < 230; i += 1) {
  const rr = Math.sqrt(rand()) * 0.99; // sqrt → uniform across the disk area
  const theta = rand() * 2 * Math.PI;
  FIELD.push({
    name: `field-${i}`,
    x: rr * Math.sin(theta),
    y: rr * Math.cos(theta),
    mag: 3.6 + rand() * 2.8, // faint background population
    con: "",
  });
}

// --- Assemble every star with projected coordinates --------------------------
const STARS = CATALOG.map((s) => ({ ...s, ...project(s.ra, s.dec) })).concat(FIELD);
const STAR_BY_NAME = {};
STARS.forEach((s) => { STAR_BY_NAME[s.name] = s; });

// --- Brightness → colour (Imprint sequential) and → marker radius ------------
function lerpHex(a, b, f) {
  const ca = [parseInt(a.slice(1, 3), 16), parseInt(a.slice(3, 5), 16), parseInt(a.slice(5, 7), 16)];
  const cb = [parseInt(b.slice(1, 3), 16), parseInt(b.slice(3, 5), 16), parseInt(b.slice(5, 7), 16)];
  const mix = ca.map((c, i) => Math.round(c + (cb[i] - c) * f));
  return `#${mix.map((c) => c.toString(16).padStart(2, "0")).join("")}`;
}
// Group stars into integer magnitude bands so each band is one scatter series
// (MUI X sizes/colours markers per series). Brighter band = larger, greener.
const MAG_LO = -1;
const MAG_HI = 6;
const bands = new Map();
STARS.forEach((s) => {
  const g = Math.max(MAG_LO, Math.min(MAG_HI, Math.round(s.mag)));
  if (!bands.has(g)) bands.set(g, []);
  bands.get(g).push({ x: s.x, y: s.y, id: s.name });
});
// Fainter bands first so the brightest stars paint on top.
const SERIES = [...bands.keys()].sort((a, b) => b - a).map((g) => {
  const f = (g - MAG_LO) / (MAG_HI - MAG_LO);
  return {
    type: "scatter",
    data: bands.get(g),
    markerSize: 11 - f * 9, // radius in CSS px: ~11 (bright) → ~2 (faint)
    color: lerpHex(SEQ[0], SEQ[1], f),
    disableHover: true,
  };
});

// --- Custom SVG layers (read the chart scales via hooks) ---------------------
const GRID = "rgba(120,140,170,0.30)"; // faint cool grid, reads on both themes
const RIM = t.inkSoft;
const LINE = t.inkSoft; // constellation sticks — subtle chrome

function SkyGrid() {
  const xScale = useXScale();
  const yScale = useYScale();
  const cx = xScale(0);
  const cy = yScale(0);
  const rOf = (rr) => Math.abs(xScale(rr) - xScale(0));
  // Declination circles + their labels (+60°, +30°, 0°, -30°).
  const decCircles = [60, 30, 0, -30].map((dec) => {
    const rr = (90 - dec) / R_MAX;
    const p = project(20.0, dec); // label sits along the 20h spoke
    return (
      <g key={`dec-${dec}`}>
        <circle cx={cx} cy={cy} r={rOf(rr)} fill="none" stroke={GRID} strokeWidth={1} />
        <text
          x={xScale(p.x)}
          y={yScale(p.y)}
          fill={t.inkSoft}
          fontSize={12}
          textAnchor="middle"
          opacity={0.85}
        >
          {dec > 0 ? `+${dec}°` : `${dec}°`}
        </text>
      </g>
    );
  });
  // Right-ascension spokes every 2h + hour labels just outside the rim.
  const rim = (90 - DEC_MIN) / R_MAX; // = 1.0
  const spokes = [];
  for (let h = 0; h < 24; h += 2) {
    const edge = project(h, DEC_MIN);
    const lab = { x: 1.08 * Math.sin((h / 24) * 2 * Math.PI), y: 1.08 * Math.cos((h / 24) * 2 * Math.PI) };
    spokes.push(
      <g key={`ra-${h}`}>
        <line x1={cx} y1={cy} x2={xScale(edge.x)} y2={yScale(edge.y)} stroke={GRID} strokeWidth={0.8} />
        <text
          x={xScale(lab.x)}
          y={yScale(lab.y)}
          fill={t.inkSoft}
          fontSize={13}
          textAnchor="middle"
          dominantBaseline="middle"
          opacity={0.9}
        >
          {h}h
        </text>
      </g>,
    );
  }
  return (
    <g>
      {spokes}
      {decCircles}
      <circle cx={cx} cy={cy} r={rOf(rim)} fill="none" stroke={RIM} strokeWidth={1.8} opacity={0.6} />
    </g>
  );
}

function ConstellationLines() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g stroke={LINE} strokeWidth={1.1} strokeOpacity={0.42} strokeLinecap="round">
      {EDGES.map(([a, b], i) => {
        const pa = STAR_BY_NAME[a];
        const pb = STAR_BY_NAME[b];
        if (!pa || !pb) return null;
        return (
          <line key={i} x1={xScale(pa.x)} y1={yScale(pa.y)} x2={xScale(pb.x)} y2={yScale(pb.y)} />
        );
      })}
    </g>
  );
}

function ConstellationLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const groups = {};
  CATALOG.forEach((s) => {
    (groups[s.con] = groups[s.con] || []).push(STAR_BY_NAME[s.name]);
  });
  return (
    <g>
      {Object.entries(groups).map(([con, list]) => {
        const mx = list.reduce((acc, s) => acc + s.x, 0) / list.length;
        const my = list.reduce((acc, s) => acc + s.y, 0) / list.length;
        return (
          <text
            key={con}
            x={xScale(mx)}
            y={yScale(my)}
            fill={t.inkSoft}
            fontSize={13}
            fontStyle="italic"
            textAnchor="middle"
            opacity={0.78}
          >
            {CON_NAMES[con]}
          </text>
        );
      })}
    </g>
  );
}

function ChartTitle() {
  const { left, top, width } = useDrawingArea();
  return (
    <text
      x={left + width / 2}
      y={top - 42}
      fill={t.ink}
      fontSize={22}
      fontWeight={600}
      textAnchor="middle"
    >
      star-chart-constellation · javascript · muix · anyplot.ai
    </text>
  );
}

function MagnitudeLegend() {
  const { left, top, height } = useDrawingArea();
  const x0 = left + 14;
  const y0 = top + height - 96;
  const samples = [-1, 1, 3, 5];
  return (
    <g>
      <text x={x0} y={y0 - 14} fill={t.inkSoft} fontSize={13} fontWeight={600}>
        Apparent magnitude
      </text>
      {samples.map((mag, i) => {
        const f = (mag - MAG_LO) / (MAG_HI - MAG_LO);
        const cy = y0 + i * 23;
        return (
          <g key={mag}>
            <circle cx={x0 + 8} cy={cy} r={11 - f * 9} fill={lerpHex(SEQ[0], SEQ[1], f)} />
            <text x={x0 + 30} y={cy + 4} fill={t.inkSoft} fontSize={12}>
              {`mag ${mag > 0 ? "+" : ""}${mag}${mag === -1 ? "  (brightest)" : mag === 5 ? "  (faintest)" : ""}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) --------------
export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      series={SERIES}
      margin={{ top: 96, bottom: 56, left: 76, right: 76 }}
      xAxis={[{ id: "x", min: -1.12, max: 1.12 }]}
      yAxis={[{ id: "y", min: -1.12, max: 1.12 }]}
      skipAnimation
    >
      <SkyGrid />
      <ConstellationLines />
      <ScatterPlot />
      <ConstellationLabels />
      <ChartTitle />
      <MagnitudeLegend />
    </ChartContainer>
  );
}
