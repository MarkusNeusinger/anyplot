// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea, useXScale, useYScale, useZAxis } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAG_LIMIT = 5.0; // faintest magnitude drawn, to keep the chart readable
const RA_PERIOD = 24; // right ascension of a full turn (24 for hours, 360 for degrees)
const RA_SPOKES = 12; // hour-circle spokes around the pole
const DEC_GRID_DEG = 30; // declination circles on the fixed -90..+90 degree domain
const RIM_PAD_SHARE = 0.015; // room between the southernmost star and the rim
const SKY_LIMIT = 1.12; // drawing extent in rim radii, leaving room for the hour labels
const STAR_RADIUS = [11, 2]; // px, brightest to faintest
const LEGEND_SAMPLES = 4;
const IAU_NAMES: Record<string, string> = {
  And: "Andromeda", Ant: "Antlia", Aps: "Apus", Aqr: "Aquarius", Aql: "Aquila", Ara: "Ara",
  Ari: "Aries", Aur: "Auriga", Boo: "Boötes", Cae: "Caelum", Cam: "Camelopardalis",
  Cnc: "Cancer", CVn: "Canes Venatici", CMa: "Canis Major", CMi: "Canis Minor",
  Cap: "Capricornus", Car: "Carina", Cas: "Cassiopeia", Cen: "Centaurus", Cep: "Cepheus",
  Cet: "Cetus", Cha: "Chamaeleon", Cir: "Circinus", Col: "Columba", Com: "Coma Berenices",
  CrA: "Corona Australis", CrB: "Corona Borealis", Crv: "Corvus", Crt: "Crater", Cru: "Crux",
  Cyg: "Cygnus", Del: "Delphinus", Dor: "Dorado", Dra: "Draco", Equ: "Equuleus",
  Eri: "Eridanus", For: "Fornax", Gem: "Gemini", Gru: "Grus", Her: "Hercules",
  Hor: "Horologium", Hya: "Hydra", Hyi: "Hydrus", Ind: "Indus", Lac: "Lacerta", Leo: "Leo",
  LMi: "Leo Minor", Lep: "Lepus", Lib: "Libra", Lup: "Lupus", Lyn: "Lynx", Lyr: "Lyra",
  Men: "Mensa", Mic: "Microscopium", Mon: "Monoceros", Mus: "Musca", Nor: "Norma",
  Oct: "Octans", Oph: "Ophiuchus", Ori: "Orion", Pav: "Pavo", Peg: "Pegasus", Per: "Perseus",
  Phe: "Phoenix", Pic: "Pictor", Psc: "Pisces", PsA: "Piscis Austrinus", Pup: "Puppis",
  Pyx: "Pyxis", Ret: "Reticulum", Sge: "Sagitta", Sgr: "Sagittarius", Sco: "Scorpius",
  Scl: "Sculptor", Sct: "Scutum", Ser: "Serpens", Sex: "Sextans", Tau: "Taurus",
  Tel: "Telescopium", Tri: "Triangulum", TrA: "Triangulum Australe", Tuc: "Tucana",
  UMa: "Ursa Major", UMi: "Ursa Minor", Vel: "Vela", Vir: "Virgo", Vol: "Volans",
  Vul: "Vulpecula",
};

// Columns: set these to your data's column names
const STAR = "Star"; // role: star_id
const RA = "Right ascension (h)"; // role: ra
const DEC = "Declination (°)"; // role: dec
const MAGNITUDE = "Apparent magnitude"; // role: magnitude
const CONSTELLATION = "Constellation"; // role: constellation
const FROM_STAR = "From star"; // role: edges
const TO_STAR = "To star"; // role: edges

// Data: replace this block with your own records, one object per row
// Bright stars of the northern sky (approximate J2000 positions) with their
// stick figures, plus a deterministic field of faint background stars.
const edges = [
  ["Dubhe", "Merak"], ["Merak", "Phecda"], ["Phecda", "Megrez"], ["Megrez", "Dubhe"],
  ["Megrez", "Alioth"], ["Alioth", "Mizar"], ["Mizar", "Alkaid"],
  ["Polaris", "Yildun"], ["Yildun", "EpsUMi"], ["EpsUMi", "ZetUMi"], ["ZetUMi", "Kochab"],
  ["Kochab", "Pherkad"], ["Pherkad", "EpsUMi"],
  ["Caph", "Schedar"], ["Schedar", "GamCas"], ["GamCas", "Ruchbah"], ["Ruchbah", "Segin"],
  ["Alderamin", "BetCep"], ["BetCep", "GamCep"], ["GamCep", "IotCep"], ["IotCep", "ZetCep"],
  ["ZetCep", "Alderamin"],
  ["Deneb", "Sadr"], ["Sadr", "Albireo"], ["Sadr", "Gienah"], ["Sadr", "DelCyg"],
  ["Vega", "ZetLyr"], ["ZetLyr", "Sheliak"], ["Sheliak", "Sulafat"], ["Sulafat", "DelLyr"],
  ["DelLyr", "ZetLyr"],
  ["Tarazed", "Altair"], ["Altair", "Alshain"], ["Altair", "DelAql"], ["DelAql", "ZetAql"],
  ["Arcturus", "Izar"], ["Izar", "Nekkar"], ["Nekkar", "Seginus"], ["Seginus", "Arcturus"],
  ["Arcturus", "Muphrid"],
  ["ThetCrB", "BetCrB"], ["BetCrB", "Alphecca"], ["Alphecca", "GamCrB"], ["GamCrB", "DelCrB"],
  ["ZetHer", "EtaHer"], ["EtaHer", "PiHer"], ["PiHer", "EpsHer"], ["EpsHer", "ZetHer"],
  ["Eltanin", "Rastaban"], ["Rastaban", "Grumium"], ["Grumium", "Eltanin"],
  ["Grumium", "DelDra"], ["DelDra", "ZetDra"], ["ZetDra", "Edasich"], ["Edasich", "Thuban"],
  ["GamPer", "Mirfak"], ["Mirfak", "DelPer"], ["DelPer", "EpsPer"], ["Mirfak", "Algol"],
  ["Capella", "Menkalinan"], ["Menkalinan", "ThetAur"], ["ThetAur", "Elnath"],
  ["Elnath", "IotAur"], ["IotAur", "Capella"],
  ["Alpheratz", "DelAnd"], ["DelAnd", "Mirach"], ["Mirach", "Almach"],
  ["Markab", "Scheat"], ["Scheat", "Alpheratz"], ["Alpheratz", "Algenib"], ["Algenib", "Markab"],
  ["Markab", "Enif"],
  ["BetTri", "AlpTri"], ["AlpTri", "GamTri"], ["GamTri", "BetTri"],
  ["Hamal", "Sheratan"], ["Sheratan", "Mesarthim"],
  ["Castor", "Pollux"], ["Pollux", "Wasat"], ["Wasat", "Alhena"],
  ["Castor", "Mebsuta"], ["Mebsuta", "MuGem"],
  ["Regulus", "EtaLeo"], ["EtaLeo", "Algieba"], ["Algieba", "EpsLeo"],
  ["Regulus", "ThetLeo"], ["ThetLeo", "Zosma"], ["Zosma", "Denebola"], ["Denebola", "ThetLeo"],
  ["Zosma", "Algieba"],
  ["CorCaroli", "BetCVn"],
  ["LamTau", "GamTau"], ["GamTau", "EpsTau"], ["EpsTau", "Aldebaran"], ["Aldebaran", "ZetTau"],
  ["EpsTau", "Elnath"],
  ["Betelgeuse", "Bellatrix"], ["Betelgeuse", "Alnitak"], ["Bellatrix", "Mintaka"],
  ["Mintaka", "Alnilam"], ["Alnilam", "Alnitak"], ["Alnitak", "Saiph"], ["Saiph", "Rigel"],
  ["Rigel", "Mintaka"],
  ["Sirius", "Mirzam"], ["Sirius", "Wezen"], ["Wezen", "Adhara"], ["Wezen", "Aludra"],
].map(([a, b]) => ({ [FROM_STAR]: a, [TO_STAR]: b }));

const catalog: [string, number, number, number, string][] = [
  ["Dubhe", 11.06, 61.75, 1.79, "UMa"], ["Merak", 11.03, 56.38, 2.37, "UMa"],
  ["Phecda", 11.9, 53.69, 2.44, "UMa"], ["Megrez", 12.26, 57.03, 3.31, "UMa"],
  ["Alioth", 12.9, 55.96, 1.77, "UMa"], ["Mizar", 13.4, 54.93, 2.04, "UMa"],
  ["Alkaid", 13.79, 49.31, 1.86, "UMa"],
  ["Polaris", 2.53, 89.26, 1.98, "UMi"], ["Yildun", 17.54, 86.59, 4.36, "UMi"],
  ["EpsUMi", 16.77, 82.04, 4.21, "UMi"], ["ZetUMi", 15.73, 77.79, 4.32, "UMi"],
  ["Kochab", 14.85, 74.16, 2.07, "UMi"], ["Pherkad", 15.35, 71.83, 3.05, "UMi"],
  ["Caph", 0.15, 59.15, 2.28, "Cas"], ["Schedar", 0.68, 56.54, 2.24, "Cas"],
  ["GamCas", 0.95, 60.72, 2.47, "Cas"], ["Ruchbah", 1.43, 60.24, 2.68, "Cas"],
  ["Segin", 1.91, 63.67, 3.35, "Cas"],
  ["Alderamin", 21.31, 62.59, 2.45, "Cep"], ["BetCep", 21.48, 70.56, 3.23, "Cep"],
  ["GamCep", 23.66, 77.63, 3.21, "Cep"], ["IotCep", 22.83, 66.2, 3.52, "Cep"],
  ["ZetCep", 22.18, 58.2, 3.35, "Cep"],
  ["Deneb", 20.69, 45.28, 1.25, "Cyg"], ["Sadr", 20.37, 40.26, 2.23, "Cyg"],
  ["Gienah", 20.77, 33.97, 2.48, "Cyg"], ["DelCyg", 19.75, 45.13, 2.87, "Cyg"],
  ["Albireo", 19.51, 27.96, 3.18, "Cyg"],
  ["Vega", 18.62, 38.78, 0.03, "Lyr"], ["Sheliak", 18.83, 33.36, 3.52, "Lyr"],
  ["Sulafat", 18.98, 32.69, 3.26, "Lyr"], ["ZetLyr", 18.75, 37.6, 4.36, "Lyr"],
  ["DelLyr", 18.9, 36.9, 4.3, "Lyr"],
  ["Altair", 19.85, 8.87, 0.76, "Aql"], ["Tarazed", 19.77, 10.61, 2.72, "Aql"],
  ["Alshain", 19.92, 6.41, 3.71, "Aql"], ["DelAql", 19.42, 3.11, 3.36, "Aql"],
  ["ZetAql", 19.09, 13.86, 2.99, "Aql"],
  ["Arcturus", 14.26, 19.18, -0.05, "Boo"], ["Izar", 14.75, 27.07, 2.35, "Boo"],
  ["Seginus", 14.53, 38.31, 3.03, "Boo"], ["Nekkar", 15.03, 40.39, 3.49, "Boo"],
  ["Muphrid", 13.91, 18.4, 2.68, "Boo"],
  ["ThetCrB", 15.55, 31.36, 4.13, "CrB"], ["BetCrB", 15.46, 29.1, 3.66, "CrB"],
  ["Alphecca", 15.58, 26.71, 2.22, "CrB"], ["GamCrB", 15.71, 26.3, 3.8, "CrB"],
  ["DelCrB", 15.82, 26.07, 4.59, "CrB"],
  ["ZetHer", 16.69, 31.6, 2.81, "Her"], ["EtaHer", 16.72, 38.92, 3.48, "Her"],
  ["PiHer", 17.25, 36.81, 3.16, "Her"], ["EpsHer", 17.0, 30.93, 3.92, "Her"],
  ["Eltanin", 17.94, 51.49, 2.36, "Dra"], ["Rastaban", 17.51, 52.3, 2.79, "Dra"],
  ["Grumium", 17.89, 56.87, 3.75, "Dra"], ["DelDra", 19.21, 67.66, 3.07, "Dra"],
  ["ZetDra", 17.15, 65.71, 3.17, "Dra"], ["Edasich", 15.42, 58.97, 3.29, "Dra"],
  ["Thuban", 14.07, 64.38, 3.65, "Dra"],
  ["Mirfak", 3.41, 49.86, 1.79, "Per"], ["Algol", 3.14, 40.96, 2.12, "Per"],
  ["GamPer", 3.08, 53.51, 2.93, "Per"], ["DelPer", 3.72, 47.79, 3.01, "Per"],
  ["EpsPer", 3.96, 40.01, 2.89, "Per"],
  ["Capella", 5.28, 46.0, 0.08, "Aur"], ["Menkalinan", 5.99, 44.95, 1.9, "Aur"],
  ["ThetAur", 6.0, 37.21, 2.62, "Aur"], ["IotAur", 4.95, 33.17, 2.69, "Aur"],
  ["Alpheratz", 0.14, 29.09, 2.06, "And"], ["Mirach", 1.16, 35.62, 2.05, "And"],
  ["Almach", 2.07, 42.33, 2.1, "And"], ["DelAnd", 0.66, 30.86, 3.27, "And"],
  ["Markab", 23.08, 15.21, 2.49, "Peg"], ["Scheat", 23.06, 28.08, 2.42, "Peg"],
  ["Algenib", 0.22, 15.18, 2.83, "Peg"], ["Enif", 21.74, 9.88, 2.39, "Peg"],
  ["BetTri", 2.16, 34.99, 3.0, "Tri"], ["AlpTri", 1.88, 29.59, 3.42, "Tri"],
  ["GamTri", 2.29, 33.85, 4.01, "Tri"],
  ["Hamal", 2.12, 23.46, 2.0, "Ari"], ["Sheratan", 1.91, 20.81, 2.64, "Ari"],
  ["Mesarthim", 1.89, 19.29, 3.86, "Ari"],
  ["Pollux", 7.76, 28.03, 1.14, "Gem"], ["Castor", 7.58, 31.89, 1.58, "Gem"],
  ["Alhena", 6.63, 16.4, 1.92, "Gem"], ["Wasat", 7.34, 21.98, 3.53, "Gem"],
  ["Mebsuta", 6.73, 25.13, 3.06, "Gem"], ["MuGem", 6.38, 22.51, 2.87, "Gem"],
  ["Regulus", 10.14, 11.97, 1.36, "Leo"], ["Denebola", 11.82, 14.57, 2.14, "Leo"],
  ["Algieba", 10.33, 19.84, 2.08, "Leo"], ["Zosma", 11.24, 20.52, 2.56, "Leo"],
  ["ThetLeo", 11.24, 15.43, 3.33, "Leo"], ["EpsLeo", 9.76, 23.77, 2.98, "Leo"],
  ["EtaLeo", 10.12, 16.76, 3.48, "Leo"],
  ["CorCaroli", 12.93, 38.32, 2.89, "CVn"], ["BetCVn", 12.56, 41.36, 4.24, "CVn"],
  ["Aldebaran", 4.6, 16.51, 0.87, "Tau"], ["Elnath", 5.44, 28.61, 1.65, "Tau"],
  ["ZetTau", 5.63, 21.14, 3.0, "Tau"], ["GamTau", 4.33, 15.63, 3.65, "Tau"],
  ["EpsTau", 4.48, 19.18, 3.53, "Tau"], ["LamTau", 4.01, 12.49, 3.47, "Tau"],
  ["Betelgeuse", 5.92, 7.41, 0.45, "Ori"], ["Rigel", 5.24, -8.2, 0.18, "Ori"],
  ["Bellatrix", 5.42, 6.35, 1.64, "Ori"], ["Saiph", 5.8, -9.67, 2.07, "Ori"],
  ["Alnitak", 5.68, -1.94, 1.77, "Ori"], ["Alnilam", 5.6, -1.2, 1.69, "Ori"],
  ["Mintaka", 5.53, -0.3, 2.23, "Ori"],
  ["Sirius", 6.75, -16.72, -1.46, "CMa"], ["Mirzam", 6.38, -17.96, 1.98, "CMa"],
  ["Wezen", 7.14, -26.39, 1.83, "CMa"], ["Adhara", 6.98, -28.97, 1.5, "CMa"],
  ["Aludra", 7.4, -29.3, 2.45, "CMa"],
];

const data: Record<string, string | number | null>[] = catalog.map(([star, ra, dec, mag, con]) => ({
  [STAR]: star,
  [RA]: ra,
  [DEC]: dec,
  [MAGNITUDE]: mag,
  [CONSTELLATION]: con,
}));
let seed = 1337;
for (let i = 0; i < 230; i += 1) {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const area = seed / 0x7fffffff;
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const turn = seed / 0x7fffffff;
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  const faint = seed / 0x7fffffff;
  data.push({
    [STAR]: `Field star ${i + 1}`,
    [RA]: Number((turn * 24).toFixed(3)),
    [DEC]: Number((90 - Math.sqrt(area) * 0.99 * 142).toFixed(2)),
    [MAGNITUDE]: Number((3.6 + faint * 2.8).toFixed(2)),
    [CONSTELLATION]: null,
  });
}

// Plot: reads only data and the constants above
// North-pole azimuthal equidistant projection: the pole sits at the centre, the
// angular distance from it grows linearly to the rim, and right ascension turns
// clockwise from the top, as the sky looks when facing the pole.
const shown = data
  .filter((d) => d[MAGNITUDE] != null && (d[MAGNITUDE] as number) <= MAG_LIMIT)
  .sort((a, b) => (b[MAGNITUDE] as number) - (a[MAGNITUDE] as number));
const decs = shown.map((d) => d[DEC] as number);
const mags = shown.map((d) => d[MAGNITUDE] as number);
const magMin = Math.min(...mags);
const magMax = Math.max(...mags);
const decSouth = Math.min(...decs);
const rimDec = decSouth - (90 - decSouth) * RIM_PAD_SHARE;
const rimDistance = 90 - rimDec;

const stars = shown.map((d) => {
  const theta = ((d[RA] as number) / RA_PERIOD) * 2 * Math.PI;
  const rr = (90 - (d[DEC] as number)) / rimDistance;
  return {
    id: d[STAR] as string,
    con: d[CONSTELLATION] as string | null,
    x: rr * Math.sin(theta),
    y: rr * Math.cos(theta),
    sizeValue: d[MAGNITUDE] as number,
  };
});
const starById = new Map(stars.map((s) => [s.id, s]));
const sticks = edges
  .map((e) => [starById.get(e[FROM_STAR]), starById.get(e[TO_STAR])])
  .filter(([a, b]) => a && b);

const constellations = [...new Set(stars.filter((s) => s.con != null).map((s) => s.con as string))];
const centroids = constellations.map((con) => {
  const members = stars.filter((s) => s.con === con);
  return {
    con,
    name: IAU_NAMES[con] ?? con,
    x: members.reduce((acc, s) => acc + s.x, 0) / members.length,
    y: members.reduce((acc, s) => acc + s.y, 0) / members.length,
  };
});

const raUnit = RA.match(/\(([^)]+)\)/)?.[1] ?? "";
const decUnit = DEC.match(/\(([^)]+)\)/)?.[1] ?? "";
const spokes = Array.from({ length: RA_SPOKES }, (_, k) => (k * RA_PERIOD) / RA_SPOKES);
const decRings: number[] = [];
for (let dec = Math.ceil(rimDec / DEC_GRID_DEG) * DEC_GRID_DEG; dec < 90; dec += DEC_GRID_DEG) {
  if (dec > rimDec) decRings.push(dec);
}
// The dec labels run through the middle of the spoke sector holding the fewest constellation stars
const sectorTurns = Array.from({ length: RA_SPOKES }, (_, k) => (k + 0.5) / RA_SPOKES);
const sectorCrowding = sectorTurns.map(
  (turn) =>
    stars.filter((s) => {
      const starTurn = (Math.atan2(s.x, s.y) / (2 * Math.PI) + 1) % 1;
      return s.con != null && Math.abs(((starTurn - turn + 1.5) % 1) - 0.5) < 0.5 / RA_SPOKES;
    }).length,
);
const decLabelTurn = sectorTurns[sectorCrowding.indexOf(Math.min(...sectorCrowding))];
const legendLo = Math.ceil(magMin);
const legendHi = Math.floor(magMax);
const legendMags = [
  ...new Set(
    Array.from({ length: LEGEND_SAMPLES }, (_, k) =>
      Math.round(legendLo + (k * (legendHi - legendLo)) / (LEGEND_SAMPLES - 1)),
    ),
  ),
];

const TITLE = "star-chart-constellation · javascript · muix · anyplot.ai";
const SUBTITLE = `${stars.length} stars to magnitude ${MAG_LIMIT.toFixed(1)} · ${constellations.length} constellations · azimuthal equidistant projection, north celestial pole at the centre`;
const HEADER_H = 76;
const V_MARGIN = 26;
const labelHalo = { stroke: t.pageBg, strokeWidth: 4, paintOrder: "stroke" as const, strokeLinejoin: "round" as const };
// A constellation name takes the shift from its centroid (px), nearest first, whose box
// clears every star, every stick line and every name placed before it; names never overlap each other
const NAME_STEP_PX = 10;
const NAME_REACH_STEPS = 6;
const NAME_CHAR_PX = 7.2; // average glyph width of the 14 px italic names
const NAME_HALF_H_PX = 9;
const NAME_STAR_GAP_PX = 3;
const nameShifts: { dx: number; dy: number }[] = [];
for (let i = -NAME_REACH_STEPS; i <= NAME_REACH_STEPS; i += 1) {
  for (let j = -NAME_REACH_STEPS; j <= NAME_REACH_STEPS; j += 1) {
    nameShifts.push({ dx: i * NAME_STEP_PX, dy: j * NAME_STEP_PX });
  }
}
nameShifts.sort((a, b) => Math.hypot(a.dx, a.dy) - Math.hypot(b.dx, b.dy));

type Box = { x0: number; x1: number; y0: number; y1: number };
// Liang–Barsky clip: does the segment p→q pass through the box?
function segmentHitsBox(px: number, py: number, qx: number, qy: number, box: Box) {
  const dx = qx - px;
  const dy = qy - py;
  let lo = 0;
  let hi = 1;
  const edgesPQ = [
    [-dx, px - box.x0],
    [dx, box.x1 - px],
    [-dy, py - box.y0],
    [dy, box.y1 - py],
  ];
  for (const [p, q] of edgesPQ) {
    if (p === 0) {
      if (q < 0) return false;
    } else {
      const r = q / p;
      if (p < 0) lo = Math.max(lo, r);
      else hi = Math.min(hi, r);
      if (lo > hi) return false;
    }
  }
  return true;
}

// Declination circles, hour spokes, the rim and the constellation stick figures
function SkyGrid() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const unit = xs(1) - xs(0);
  const cx = xs(0);
  const cy = ys(0);
  const labelTheta = decLabelTurn * 2 * Math.PI;
  return (
    <g>
      {spokes.map((h) => {
        const theta = (h / RA_PERIOD) * 2 * Math.PI;
        return (
          <g key={`ra-${h}`}>
            <line x1={cx} y1={cy} x2={xs(Math.sin(theta))} y2={ys(Math.cos(theta))} stroke={t.grid} strokeWidth={1} />
            <text
              x={xs(1.07 * Math.sin(theta))}
              y={ys(1.07 * Math.cos(theta))}
              fill={t.inkSoft}
              fontSize={15}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {`${h}${raUnit}`}
            </text>
          </g>
        );
      })}
      {decRings.map((dec) => {
        const rr = (90 - dec) / rimDistance;
        return (
          <g key={`dec-${dec}`}>
            <circle cx={cx} cy={cy} r={rr * unit} fill="none" stroke={t.grid} strokeWidth={1} />
            <text
              x={xs(rr * Math.sin(labelTheta))}
              y={ys(rr * Math.cos(labelTheta))}
              fill={t.inkSoft}
              fontSize={14}
              textAnchor="middle"
              dominantBaseline="central"
              {...labelHalo}
            >
              {`${dec > 0 ? "+" : ""}${dec}${decUnit}`}
            </text>
          </g>
        );
      })}
      <circle cx={cx} cy={cy} r={unit} fill="none" stroke={t.inkSoft} strokeWidth={1.8} opacity={0.7} />
      <g stroke={t.inkSoft} strokeWidth={1.2} strokeOpacity={0.45} strokeLinecap="round">
        {sticks.map(([a, b], i) => (
          <line key={i} x1={xs(a.x)} y1={ys(a.y)} x2={xs(b.x)} y2={ys(b.y)} />
        ))}
      </g>
    </g>
  );
}

// Constellation names near their star centroids, shifted off the stars, and the
// magnitude key, read from the size axis
function SkyLabels() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const { left, top, height } = useDrawingArea();
  const magAxis = useZAxis("mag");
  const x0 = left + 12;
  const y0 = top + height - legendMags.length * 30 - 6;
  const starDots = stars.map((s) => ({
    x: xs(s.x),
    y: ys(s.y),
    reach: (magAxis.sizeScale(s.sizeValue) as number) + NAME_STAR_GAP_PX,
  }));
  const stickPx = sticks.map(([a, b]) => [xs(a.x), ys(a.y), xs(b.x), ys(b.y)]);
  const placedBoxes: Box[] = [];
  const names = centroids.map((c) => {
    const halfW = (c.name.length * NAME_CHAR_PX) / 2;
    const candidates = nameShifts.map(({ dx, dy }) => {
      const cx = xs(c.x) + dx;
      const cy = ys(c.y) + dy;
      const box = { x0: cx - halfW, x1: cx + halfW, y0: cy - NAME_HALF_H_PX, y1: cy + NAME_HALF_H_PX };
      const starHits = starDots.filter(
        (p) => p.x > box.x0 - p.reach && p.x < box.x1 + p.reach && p.y > box.y0 - p.reach && p.y < box.y1 + p.reach,
      ).length;
      const stickHits = stickPx.filter(([ax, ay, bx, by]) => segmentHitsBox(ax, ay, bx, by, box)).length;
      const hits = starHits + stickHits;
      const nameHit = placedBoxes.some((b) => b.x0 < box.x1 && b.x1 > box.x0 && b.y0 < box.y1 && b.y1 > box.y0);
      return { cx, cy, box, hits, nameHit };
    });
    const free = candidates.filter((cand) => !cand.nameHit);
    const pool = free.length > 0 ? free : candidates;
    const best = pool.find((cand) => cand.hits === 0) ?? pool.reduce((a, b) => (b.hits < a.hits ? b : a));
    placedBoxes.push(best.box);
    return { con: c.con, name: c.name, x: best.cx, y: best.cy };
  });
  return (
    <g>
      {names.map((c) => (
        <text
          key={c.con}
          x={c.x}
          y={c.y}
          fill={t.inkSoft}
          fontSize={14}
          fontStyle="italic"
          textAnchor="middle"
          dominantBaseline="central"
          {...labelHalo}
        >
          {c.name}
        </text>
      ))}
      <text x={x0} y={y0 - 20} fill={t.ink} fontSize={15} fontWeight={600}>
        {MAGNITUDE}
      </text>
      {legendMags.map((mag, i) => {
        const cy = y0 + i * 30;
        const note = i === 0 ? "  (brightest)" : i === legendMags.length - 1 ? "  (faintest)" : "";
        return (
          <g key={mag}>
            <circle cx={x0 + 11} cy={cy} r={magAxis.sizeScale(mag)} fill={t.ink} />
            <text x={x0 + 32} y={cy} fill={t.inkSoft} fontSize={14} dominantBaseline="central">
              {`${mag > 0 ? "+" : ""}${mag}${note}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;
  const chartH = H - HEADER_H;
  const side = Math.min(W, chartH) - 2 * V_MARGIN;
  const hMargin = (W - side) / 2;
  const vMargin = (chartH - side) / 2;

  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        margin={{ top: vMargin, bottom: vMargin, left: hMargin, right: hMargin }}
        xAxis={[{ id: "x", min: -SKY_LIMIT, max: SKY_LIMIT, position: "none" }]}
        yAxis={[{ id: "y", min: -SKY_LIMIT, max: SKY_LIMIT, position: "none" }]}
        zAxis={[
          {
            id: "mag",
            sizeMap: { type: "continuous", min: magMin, max: magMax, size: STAR_RADIUS as [number, number], interpolator: "linear" },
          },
        ]}
        series={[
          {
            type: "scatter",
            id: "stars",
            label: STAR,
            data: stars,
            // stars in ink: light on the dark night sky, dark on the light atlas page
            color: t.ink,
            sizeAxisId: "mag",
            markerSize: STAR_RADIUS[1],
          },
        ]}
      >
        <SkyGrid />
        <ScatterPlot />
        <SkyLabels />
      </ChartsContainer>
    </div>
  );
}
