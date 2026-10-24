// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 94/100 | Created: 2026-06-17
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DEC_MIN = -52;
const R_MAX = 90 - DEC_MIN;
const MAG_LO = -1;
const MAG_HI = 6;
const GRID = "rgba(120,140,170,0.30)";
const CON_NAMES: Record<string, string> = {
  UMa: "Ursa Major",
  UMi: "Ursa Minor",
  Cas: "Cassiopeia",
  Cep: "Cepheus",
  Cyg: "Cygnus",
  Lyr: "Lyra",
  Aql: "Aquila",
  Boo: "Boötes",
  CrB: "Corona Borealis",
  Her: "Hercules",
  Dra: "Draco",
  Per: "Perseus",
  Aur: "Auriga",
  And: "Andromeda",
  Peg: "Pegasus",
  Tri: "Triangulum",
  Ari: "Aries",
  Gem: "Gemini",
  Leo: "Leo",
  CVn: "Canes Venatici",
  Tau: "Taurus",
  Ori: "Orion",
  CMa: "Canis Major",
};

// Columns: set these to your data's column names
const STAR_ID = "Star Name"; // role: star_id
const RA = "Right Ascension (h)"; // role: ra
const DEC = "Declination (°)"; // role: dec
const MAGNITUDE = "Apparent Magnitude"; // role: magnitude
const CONSTELLATION = "Constellation"; // role: constellation
const EDGES = "Connected Stars"; // role: edges

// Data: replace this block with your own records
const catalogRows: Array<Record<string, string | number>> = [
  // Ursa Major
  { [STAR_ID]: "Dubhe", [RA]: 11.06, [DEC]: 61.75, [MAGNITUDE]: 1.79, [CONSTELLATION]: "UMa", [EDGES]: "Merak" },
  { [STAR_ID]: "Merak", [RA]: 11.03, [DEC]: 56.38, [MAGNITUDE]: 2.37, [CONSTELLATION]: "UMa", [EDGES]: "Phecda" },
  { [STAR_ID]: "Phecda", [RA]: 11.9, [DEC]: 53.69, [MAGNITUDE]: 2.44, [CONSTELLATION]: "UMa", [EDGES]: "Megrez" },
  { [STAR_ID]: "Megrez", [RA]: 12.26, [DEC]: 57.03, [MAGNITUDE]: 3.31, [CONSTELLATION]: "UMa", [EDGES]: "Dubhe|Alioth" },
  { [STAR_ID]: "Alioth", [RA]: 12.9, [DEC]: 55.96, [MAGNITUDE]: 1.77, [CONSTELLATION]: "UMa", [EDGES]: "Mizar" },
  { [STAR_ID]: "Mizar", [RA]: 13.4, [DEC]: 54.93, [MAGNITUDE]: 2.04, [CONSTELLATION]: "UMa", [EDGES]: "Alkaid" },
  { [STAR_ID]: "Alkaid", [RA]: 13.79, [DEC]: 49.31, [MAGNITUDE]: 1.86, [CONSTELLATION]: "UMa", [EDGES]: "" },
  // Ursa Minor
  { [STAR_ID]: "Polaris", [RA]: 2.53, [DEC]: 89.26, [MAGNITUDE]: 1.98, [CONSTELLATION]: "UMi", [EDGES]: "Yildun" },
  { [STAR_ID]: "Yildun", [RA]: 17.54, [DEC]: 86.59, [MAGNITUDE]: 4.36, [CONSTELLATION]: "UMi", [EDGES]: "EpsUMi" },
  { [STAR_ID]: "EpsUMi", [RA]: 16.77, [DEC]: 82.04, [MAGNITUDE]: 4.21, [CONSTELLATION]: "UMi", [EDGES]: "ZetUMi" },
  { [STAR_ID]: "ZetUMi", [RA]: 15.73, [DEC]: 77.79, [MAGNITUDE]: 4.32, [CONSTELLATION]: "UMi", [EDGES]: "Kochab" },
  { [STAR_ID]: "Kochab", [RA]: 14.85, [DEC]: 74.16, [MAGNITUDE]: 2.07, [CONSTELLATION]: "UMi", [EDGES]: "Pherkad" },
  { [STAR_ID]: "Pherkad", [RA]: 15.35, [DEC]: 71.83, [MAGNITUDE]: 3.05, [CONSTELLATION]: "UMi", [EDGES]: "EpsUMi" },
  // Cassiopeia
  { [STAR_ID]: "Caph", [RA]: 0.15, [DEC]: 59.15, [MAGNITUDE]: 2.28, [CONSTELLATION]: "Cas", [EDGES]: "Schedar" },
  { [STAR_ID]: "Schedar", [RA]: 0.68, [DEC]: 56.54, [MAGNITUDE]: 2.24, [CONSTELLATION]: "Cas", [EDGES]: "GamCas" },
  { [STAR_ID]: "GamCas", [RA]: 0.95, [DEC]: 60.72, [MAGNITUDE]: 2.47, [CONSTELLATION]: "Cas", [EDGES]: "Ruchbah" },
  { [STAR_ID]: "Ruchbah", [RA]: 1.43, [DEC]: 60.24, [MAGNITUDE]: 2.68, [CONSTELLATION]: "Cas", [EDGES]: "Segin" },
  { [STAR_ID]: "Segin", [RA]: 1.91, [DEC]: 63.67, [MAGNITUDE]: 3.35, [CONSTELLATION]: "Cas", [EDGES]: "" },
  // Cepheus
  { [STAR_ID]: "Alderamin", [RA]: 21.31, [DEC]: 62.59, [MAGNITUDE]: 2.45, [CONSTELLATION]: "Cep", [EDGES]: "BetCep" },
  { [STAR_ID]: "BetCep", [RA]: 21.48, [DEC]: 70.56, [MAGNITUDE]: 3.23, [CONSTELLATION]: "Cep", [EDGES]: "GamCep" },
  { [STAR_ID]: "GamCep", [RA]: 23.66, [DEC]: 77.63, [MAGNITUDE]: 3.21, [CONSTELLATION]: "Cep", [EDGES]: "IotCep" },
  { [STAR_ID]: "IotCep", [RA]: 22.83, [DEC]: 66.2, [MAGNITUDE]: 3.52, [CONSTELLATION]: "Cep", [EDGES]: "ZetCep" },
  { [STAR_ID]: "ZetCep", [RA]: 22.18, [DEC]: 58.2, [MAGNITUDE]: 3.35, [CONSTELLATION]: "Cep", [EDGES]: "Alderamin" },
  // Cygnus
  { [STAR_ID]: "Deneb", [RA]: 20.69, [DEC]: 45.28, [MAGNITUDE]: 1.25, [CONSTELLATION]: "Cyg", [EDGES]: "Sadr" },
  { [STAR_ID]: "Sadr", [RA]: 20.37, [DEC]: 40.26, [MAGNITUDE]: 2.23, [CONSTELLATION]: "Cyg", [EDGES]: "Albireo|Gienah|DelCyg" },
  { [STAR_ID]: "Gienah", [RA]: 20.77, [DEC]: 33.97, [MAGNITUDE]: 2.48, [CONSTELLATION]: "Cyg", [EDGES]: "" },
  { [STAR_ID]: "DelCyg", [RA]: 19.75, [DEC]: 45.13, [MAGNITUDE]: 2.87, [CONSTELLATION]: "Cyg", [EDGES]: "" },
  { [STAR_ID]: "Albireo", [RA]: 19.51, [DEC]: 27.96, [MAGNITUDE]: 3.18, [CONSTELLATION]: "Cyg", [EDGES]: "" },
  // Lyra
  { [STAR_ID]: "Vega", [RA]: 18.62, [DEC]: 38.78, [MAGNITUDE]: 0.03, [CONSTELLATION]: "Lyr", [EDGES]: "ZetLyr" },
  { [STAR_ID]: "Sheliak", [RA]: 18.83, [DEC]: 33.36, [MAGNITUDE]: 3.52, [CONSTELLATION]: "Lyr", [EDGES]: "Sulafat" },
  { [STAR_ID]: "Sulafat", [RA]: 18.98, [DEC]: 32.69, [MAGNITUDE]: 3.26, [CONSTELLATION]: "Lyr", [EDGES]: "DelLyr" },
  { [STAR_ID]: "ZetLyr", [RA]: 18.75, [DEC]: 37.6, [MAGNITUDE]: 4.36, [CONSTELLATION]: "Lyr", [EDGES]: "Sheliak" },
  { [STAR_ID]: "DelLyr", [RA]: 18.9, [DEC]: 36.9, [MAGNITUDE]: 4.3, [CONSTELLATION]: "Lyr", [EDGES]: "ZetLyr" },
  // Aquila
  { [STAR_ID]: "Altair", [RA]: 19.85, [DEC]: 8.87, [MAGNITUDE]: 0.76, [CONSTELLATION]: "Aql", [EDGES]: "Alshain|DelAql" },
  { [STAR_ID]: "Tarazed", [RA]: 19.77, [DEC]: 10.61, [MAGNITUDE]: 2.72, [CONSTELLATION]: "Aql", [EDGES]: "Altair" },
  { [STAR_ID]: "Alshain", [RA]: 19.92, [DEC]: 6.41, [MAGNITUDE]: 3.71, [CONSTELLATION]: "Aql", [EDGES]: "" },
  { [STAR_ID]: "DelAql", [RA]: 19.42, [DEC]: 3.11, [MAGNITUDE]: 3.36, [CONSTELLATION]: "Aql", [EDGES]: "ZetAql" },
  { [STAR_ID]: "ZetAql", [RA]: 19.09, [DEC]: 13.86, [MAGNITUDE]: 2.99, [CONSTELLATION]: "Aql", [EDGES]: "" },
  // Bootes
  { [STAR_ID]: "Arcturus", [RA]: 14.26, [DEC]: 19.18, [MAGNITUDE]: -0.05, [CONSTELLATION]: "Boo", [EDGES]: "Izar|Muphrid" },
  { [STAR_ID]: "Izar", [RA]: 14.75, [DEC]: 27.07, [MAGNITUDE]: 2.35, [CONSTELLATION]: "Boo", [EDGES]: "Nekkar" },
  { [STAR_ID]: "Seginus", [RA]: 14.53, [DEC]: 38.31, [MAGNITUDE]: 3.03, [CONSTELLATION]: "Boo", [EDGES]: "Arcturus" },
  { [STAR_ID]: "Nekkar", [RA]: 15.03, [DEC]: 40.39, [MAGNITUDE]: 3.49, [CONSTELLATION]: "Boo", [EDGES]: "Seginus" },
  { [STAR_ID]: "Muphrid", [RA]: 13.91, [DEC]: 18.4, [MAGNITUDE]: 2.68, [CONSTELLATION]: "Boo", [EDGES]: "" },
  // Corona Borealis
  { [STAR_ID]: "ThetCrB", [RA]: 15.55, [DEC]: 31.36, [MAGNITUDE]: 4.13, [CONSTELLATION]: "CrB", [EDGES]: "BetCrB" },
  { [STAR_ID]: "BetCrB", [RA]: 15.46, [DEC]: 29.1, [MAGNITUDE]: 3.66, [CONSTELLATION]: "CrB", [EDGES]: "Alphecca" },
  { [STAR_ID]: "Alphecca", [RA]: 15.58, [DEC]: 26.71, [MAGNITUDE]: 2.22, [CONSTELLATION]: "CrB", [EDGES]: "GamCrB" },
  { [STAR_ID]: "GamCrB", [RA]: 15.71, [DEC]: 26.3, [MAGNITUDE]: 3.8, [CONSTELLATION]: "CrB", [EDGES]: "DelCrB" },
  { [STAR_ID]: "DelCrB", [RA]: 15.82, [DEC]: 26.07, [MAGNITUDE]: 4.59, [CONSTELLATION]: "CrB", [EDGES]: "" },
  // Hercules
  { [STAR_ID]: "ZetHer", [RA]: 16.69, [DEC]: 31.6, [MAGNITUDE]: 2.81, [CONSTELLATION]: "Her", [EDGES]: "EtaHer" },
  { [STAR_ID]: "EtaHer", [RA]: 16.72, [DEC]: 38.92, [MAGNITUDE]: 3.48, [CONSTELLATION]: "Her", [EDGES]: "PiHer" },
  { [STAR_ID]: "PiHer", [RA]: 17.25, [DEC]: 36.81, [MAGNITUDE]: 3.16, [CONSTELLATION]: "Her", [EDGES]: "EpsHer" },
  { [STAR_ID]: "EpsHer", [RA]: 17.0, [DEC]: 30.93, [MAGNITUDE]: 3.92, [CONSTELLATION]: "Her", [EDGES]: "ZetHer" },
  // Draco
  { [STAR_ID]: "Eltanin", [RA]: 17.94, [DEC]: 51.49, [MAGNITUDE]: 2.36, [CONSTELLATION]: "Dra", [EDGES]: "Rastaban" },
  { [STAR_ID]: "Rastaban", [RA]: 17.51, [DEC]: 52.3, [MAGNITUDE]: 2.79, [CONSTELLATION]: "Dra", [EDGES]: "Grumium" },
  { [STAR_ID]: "Grumium", [RA]: 17.89, [DEC]: 56.87, [MAGNITUDE]: 3.75, [CONSTELLATION]: "Dra", [EDGES]: "Eltanin|DelDra" },
  { [STAR_ID]: "DelDra", [RA]: 19.21, [DEC]: 67.66, [MAGNITUDE]: 3.07, [CONSTELLATION]: "Dra", [EDGES]: "ZetDra" },
  { [STAR_ID]: "ZetDra", [RA]: 17.15, [DEC]: 65.71, [MAGNITUDE]: 3.17, [CONSTELLATION]: "Dra", [EDGES]: "Edasich" },
  { [STAR_ID]: "Edasich", [RA]: 15.42, [DEC]: 58.97, [MAGNITUDE]: 3.29, [CONSTELLATION]: "Dra", [EDGES]: "Thuban" },
  { [STAR_ID]: "Thuban", [RA]: 14.07, [DEC]: 64.38, [MAGNITUDE]: 3.65, [CONSTELLATION]: "Dra", [EDGES]: "" },
  // Perseus
  { [STAR_ID]: "Mirfak", [RA]: 3.41, [DEC]: 49.86, [MAGNITUDE]: 1.79, [CONSTELLATION]: "Per", [EDGES]: "DelPer|Algol" },
  { [STAR_ID]: "Algol", [RA]: 3.14, [DEC]: 40.96, [MAGNITUDE]: 2.12, [CONSTELLATION]: "Per", [EDGES]: "" },
  { [STAR_ID]: "GamPer", [RA]: 3.08, [DEC]: 53.51, [MAGNITUDE]: 2.93, [CONSTELLATION]: "Per", [EDGES]: "Mirfak" },
  { [STAR_ID]: "DelPer", [RA]: 3.72, [DEC]: 47.79, [MAGNITUDE]: 3.01, [CONSTELLATION]: "Per", [EDGES]: "EpsPer" },
  { [STAR_ID]: "EpsPer", [RA]: 3.96, [DEC]: 40.01, [MAGNITUDE]: 2.89, [CONSTELLATION]: "Per", [EDGES]: "" },
  // Auriga
  { [STAR_ID]: "Capella", [RA]: 5.28, [DEC]: 46.0, [MAGNITUDE]: 0.08, [CONSTELLATION]: "Aur", [EDGES]: "Menkalinan" },
  { [STAR_ID]: "Menkalinan", [RA]: 5.99, [DEC]: 44.95, [MAGNITUDE]: 1.9, [CONSTELLATION]: "Aur", [EDGES]: "ThetAur" },
  { [STAR_ID]: "ThetAur", [RA]: 6.0, [DEC]: 37.21, [MAGNITUDE]: 2.62, [CONSTELLATION]: "Aur", [EDGES]: "Elnath" },
  { [STAR_ID]: "IotAur", [RA]: 4.95, [DEC]: 33.17, [MAGNITUDE]: 2.69, [CONSTELLATION]: "Aur", [EDGES]: "Capella" },
  // Andromeda
  { [STAR_ID]: "Alpheratz", [RA]: 0.14, [DEC]: 29.09, [MAGNITUDE]: 2.06, [CONSTELLATION]: "And", [EDGES]: "DelAnd|Algenib" },
  { [STAR_ID]: "Mirach", [RA]: 1.16, [DEC]: 35.62, [MAGNITUDE]: 2.05, [CONSTELLATION]: "And", [EDGES]: "Almach" },
  { [STAR_ID]: "Almach", [RA]: 2.07, [DEC]: 42.33, [MAGNITUDE]: 2.1, [CONSTELLATION]: "And", [EDGES]: "" },
  { [STAR_ID]: "DelAnd", [RA]: 0.66, [DEC]: 30.86, [MAGNITUDE]: 3.27, [CONSTELLATION]: "And", [EDGES]: "Mirach" },
  // Pegasus
  { [STAR_ID]: "Markab", [RA]: 23.08, [DEC]: 15.21, [MAGNITUDE]: 2.49, [CONSTELLATION]: "Peg", [EDGES]: "Scheat|Enif" },
  { [STAR_ID]: "Scheat", [RA]: 23.06, [DEC]: 28.08, [MAGNITUDE]: 2.42, [CONSTELLATION]: "Peg", [EDGES]: "Alpheratz" },
  { [STAR_ID]: "Algenib", [RA]: 0.22, [DEC]: 15.18, [MAGNITUDE]: 2.83, [CONSTELLATION]: "Peg", [EDGES]: "Markab" },
  { [STAR_ID]: "Enif", [RA]: 21.74, [DEC]: 9.88, [MAGNITUDE]: 2.39, [CONSTELLATION]: "Peg", [EDGES]: "" },
  // Triangulum
  { [STAR_ID]: "BetTri", [RA]: 2.16, [DEC]: 34.99, [MAGNITUDE]: 3.0, [CONSTELLATION]: "Tri", [EDGES]: "AlpTri" },
  { [STAR_ID]: "AlpTri", [RA]: 1.88, [DEC]: 29.59, [MAGNITUDE]: 3.42, [CONSTELLATION]: "Tri", [EDGES]: "GamTri" },
  { [STAR_ID]: "GamTri", [RA]: 2.29, [DEC]: 33.85, [MAGNITUDE]: 4.01, [CONSTELLATION]: "Tri", [EDGES]: "BetTri" },
  // Aries
  { [STAR_ID]: "Hamal", [RA]: 2.12, [DEC]: 23.46, [MAGNITUDE]: 2.0, [CONSTELLATION]: "Ari", [EDGES]: "Sheratan" },
  { [STAR_ID]: "Sheratan", [RA]: 1.91, [DEC]: 20.81, [MAGNITUDE]: 2.64, [CONSTELLATION]: "Ari", [EDGES]: "Mesarthim" },
  { [STAR_ID]: "Mesarthim", [RA]: 1.89, [DEC]: 19.29, [MAGNITUDE]: 3.86, [CONSTELLATION]: "Ari", [EDGES]: "" },
  // Gemini
  { [STAR_ID]: "Pollux", [RA]: 7.76, [DEC]: 28.03, [MAGNITUDE]: 1.14, [CONSTELLATION]: "Gem", [EDGES]: "Wasat" },
  { [STAR_ID]: "Castor", [RA]: 7.58, [DEC]: 31.89, [MAGNITUDE]: 1.58, [CONSTELLATION]: "Gem", [EDGES]: "Pollux|Mebsuta" },
  { [STAR_ID]: "Alhena", [RA]: 6.63, [DEC]: 16.4, [MAGNITUDE]: 1.92, [CONSTELLATION]: "Gem", [EDGES]: "" },
  { [STAR_ID]: "Wasat", [RA]: 7.34, [DEC]: 21.98, [MAGNITUDE]: 3.53, [CONSTELLATION]: "Gem", [EDGES]: "Alhena" },
  { [STAR_ID]: "Mebsuta", [RA]: 6.73, [DEC]: 25.13, [MAGNITUDE]: 3.06, [CONSTELLATION]: "Gem", [EDGES]: "MuGem" },
  { [STAR_ID]: "MuGem", [RA]: 6.38, [DEC]: 22.51, [MAGNITUDE]: 2.87, [CONSTELLATION]: "Gem", [EDGES]: "" },
  // Leo
  { [STAR_ID]: "Regulus", [RA]: 10.14, [DEC]: 11.97, [MAGNITUDE]: 1.36, [CONSTELLATION]: "Leo", [EDGES]: "EtaLeo|ThetLeo" },
  { [STAR_ID]: "Denebola", [RA]: 11.82, [DEC]: 14.57, [MAGNITUDE]: 2.14, [CONSTELLATION]: "Leo", [EDGES]: "ThetLeo" },
  { [STAR_ID]: "Algieba", [RA]: 10.33, [DEC]: 19.84, [MAGNITUDE]: 2.08, [CONSTELLATION]: "Leo", [EDGES]: "EpsLeo" },
  { [STAR_ID]: "Zosma", [RA]: 11.24, [DEC]: 20.52, [MAGNITUDE]: 2.56, [CONSTELLATION]: "Leo", [EDGES]: "Denebola|Algieba" },
  { [STAR_ID]: "ThetLeo", [RA]: 11.24, [DEC]: 15.43, [MAGNITUDE]: 3.33, [CONSTELLATION]: "Leo", [EDGES]: "Zosma" },
  { [STAR_ID]: "EpsLeo", [RA]: 9.76, [DEC]: 23.77, [MAGNITUDE]: 2.98, [CONSTELLATION]: "Leo", [EDGES]: "" },
  { [STAR_ID]: "EtaLeo", [RA]: 10.12, [DEC]: 16.76, [MAGNITUDE]: 3.48, [CONSTELLATION]: "Leo", [EDGES]: "Algieba" },
  // Canes Venatici
  { [STAR_ID]: "CorCaroli", [RA]: 12.93, [DEC]: 38.32, [MAGNITUDE]: 2.89, [CONSTELLATION]: "CVn", [EDGES]: "BetCVn" },
  { [STAR_ID]: "BetCVn", [RA]: 12.56, [DEC]: 41.36, [MAGNITUDE]: 4.24, [CONSTELLATION]: "CVn", [EDGES]: "" },
  // Taurus
  { [STAR_ID]: "Aldebaran", [RA]: 4.6, [DEC]: 16.51, [MAGNITUDE]: 0.87, [CONSTELLATION]: "Tau", [EDGES]: "ZetTau" },
  { [STAR_ID]: "Elnath", [RA]: 5.44, [DEC]: 28.61, [MAGNITUDE]: 1.65, [CONSTELLATION]: "Tau", [EDGES]: "IotAur" },
  { [STAR_ID]: "ZetTau", [RA]: 5.63, [DEC]: 21.14, [MAGNITUDE]: 3.0, [CONSTELLATION]: "Tau", [EDGES]: "" },
  { [STAR_ID]: "GamTau", [RA]: 4.33, [DEC]: 15.63, [MAGNITUDE]: 3.65, [CONSTELLATION]: "Tau", [EDGES]: "EpsTau" },
  { [STAR_ID]: "EpsTau", [RA]: 4.48, [DEC]: 19.18, [MAGNITUDE]: 3.53, [CONSTELLATION]: "Tau", [EDGES]: "Aldebaran|Elnath" },
  { [STAR_ID]: "LamTau", [RA]: 4.01, [DEC]: 12.49, [MAGNITUDE]: 3.47, [CONSTELLATION]: "Tau", [EDGES]: "GamTau" },
  // Orion
  { [STAR_ID]: "Betelgeuse", [RA]: 5.92, [DEC]: 7.41, [MAGNITUDE]: 0.45, [CONSTELLATION]: "Ori", [EDGES]: "Bellatrix|Alnitak" },
  { [STAR_ID]: "Rigel", [RA]: 5.24, [DEC]: -8.2, [MAGNITUDE]: 0.18, [CONSTELLATION]: "Ori", [EDGES]: "Mintaka" },
  { [STAR_ID]: "Bellatrix", [RA]: 5.42, [DEC]: 6.35, [MAGNITUDE]: 1.64, [CONSTELLATION]: "Ori", [EDGES]: "Mintaka" },
  { [STAR_ID]: "Saiph", [RA]: 5.8, [DEC]: -9.67, [MAGNITUDE]: 2.07, [CONSTELLATION]: "Ori", [EDGES]: "Rigel" },
  { [STAR_ID]: "Alnitak", [RA]: 5.68, [DEC]: -1.94, [MAGNITUDE]: 1.77, [CONSTELLATION]: "Ori", [EDGES]: "Saiph" },
  { [STAR_ID]: "Alnilam", [RA]: 5.6, [DEC]: -1.2, [MAGNITUDE]: 1.69, [CONSTELLATION]: "Ori", [EDGES]: "Alnitak" },
  { [STAR_ID]: "Mintaka", [RA]: 5.53, [DEC]: -0.3, [MAGNITUDE]: 2.23, [CONSTELLATION]: "Ori", [EDGES]: "Alnilam" },
  // Canis Major
  { [STAR_ID]: "Sirius", [RA]: 6.75, [DEC]: -16.72, [MAGNITUDE]: -1.46, [CONSTELLATION]: "CMa", [EDGES]: "Mirzam|Wezen" },
  { [STAR_ID]: "Mirzam", [RA]: 6.38, [DEC]: -17.96, [MAGNITUDE]: 1.98, [CONSTELLATION]: "CMa", [EDGES]: "" },
  { [STAR_ID]: "Wezen", [RA]: 7.14, [DEC]: -26.39, [MAGNITUDE]: 1.83, [CONSTELLATION]: "CMa", [EDGES]: "Adhara|Aludra" },
  { [STAR_ID]: "Adhara", [RA]: 6.98, [DEC]: -28.97, [MAGNITUDE]: 1.5, [CONSTELLATION]: "CMa", [EDGES]: "" },
  { [STAR_ID]: "Aludra", [RA]: 7.4, [DEC]: -29.3, [MAGNITUDE]: 2.45, [CONSTELLATION]: "CMa", [EDGES]: "" },
];

let fieldSeed = 1337;
const fieldRows: Array<Record<string, string | number>> = [];
for (let i = 0; i < 230; i += 1) {
  fieldSeed = (fieldSeed * 1103515245 + 12345) & 0x7fffffff;
  const u1 = fieldSeed / 0x7fffffff;
  fieldSeed = (fieldSeed * 1103515245 + 12345) & 0x7fffffff;
  const u2 = fieldSeed / 0x7fffffff;
  fieldSeed = (fieldSeed * 1103515245 + 12345) & 0x7fffffff;
  const u3 = fieldSeed / 0x7fffffff;
  const rr = Math.sqrt(u1) * 0.99;
  const decDeg = 90 - rr * R_MAX;
  const raHours = u2 * 24;
  fieldRows.push({
    [STAR_ID]: `field-${i}`,
    [RA]: raHours,
    [DEC]: decDeg,
    [MAGNITUDE]: 3.6 + u3 * 2.8,
    [CONSTELLATION]: "",
    [EDGES]: "",
  });
}

const data = catalogRows.concat(fieldRows);

// Plot: reads only data and the constants above
const stars = data.map((row) => {
  const name = String(row[STAR_ID]);
  const raHours = Number(row[RA]);
  const decDeg = Number(row[DEC]);
  const mag = Number(row[MAGNITUDE]);
  const con = String(row[CONSTELLATION]);
  const edgesStr = String(row[EDGES]);
  const theta = (raHours / 24) * 2 * Math.PI;
  const rr = (90 - decDeg) / R_MAX;
  return {
    name,
    ra: raHours,
    dec: decDeg,
    mag,
    con,
    edges: edgesStr ? edgesStr.split("|") : [],
    x: rr * Math.sin(theta),
    y: rr * Math.cos(theta),
  };
});

const starByName: Record<string, (typeof stars)[number]> = {};
for (const s of stars) {
  starByName[s.name] = s;
}

const edgePairs: Array<[string, string]> = [];
for (const s of stars) {
  for (const target of s.edges) {
    if (target) edgePairs.push([s.name, target]);
  }
}

const seqR1 = parseInt(t.seq[0].slice(1, 3), 16);
const seqG1 = parseInt(t.seq[0].slice(3, 5), 16);
const seqB1 = parseInt(t.seq[0].slice(5, 7), 16);
const seqR2 = parseInt(t.seq[1].slice(1, 3), 16);
const seqG2 = parseInt(t.seq[1].slice(3, 5), 16);
const seqB2 = parseInt(t.seq[1].slice(5, 7), 16);

const bands = new Map<number, Array<{ x: number; y: number; id: string }>>();
for (const s of stars) {
  const g = Math.max(MAG_LO, Math.min(MAG_HI, Math.round(s.mag)));
  const bucket = bands.get(g) ?? [];
  bucket.push({ x: s.x, y: s.y, id: s.name });
  bands.set(g, bucket);
}

const series = [...bands.keys()]
  .sort((a, b) => b - a)
  .map((g) => {
    const f = (g - MAG_LO) / (MAG_HI - MAG_LO);
    const r = Math.round(seqR1 + (seqR2 - seqR1) * f)
      .toString(16)
      .padStart(2, "0");
    const gr = Math.round(seqG1 + (seqG2 - seqG1) * f)
      .toString(16)
      .padStart(2, "0");
    const b = Math.round(seqB1 + (seqB2 - seqB1) * f)
      .toString(16)
      .padStart(2, "0");
    return {
      type: "scatter" as const,
      data: bands.get(g)!,
      markerSize: 11 - f * 9,
      color: `#${r}${gr}${b}`,
    };
  });

function SkyGrid() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const cx = xScale(0);
  const cy = yScale(0);

  const decCircles = [60, 30, 0, -30].map((dec) => {
    const rr = (90 - dec) / R_MAX;
    const radPx = Math.abs(xScale(rr) - cx);
    const theta20 = (20.0 / 24) * 2 * Math.PI;
    const px = xScale(rr * Math.sin(theta20));
    const py = yScale(rr * Math.cos(theta20));
    return (
      <g key={`dec-${dec}`}>
        <circle
          cx={cx}
          cy={cy}
          r={radPx}
          fill="none"
          stroke={GRID}
          strokeWidth={1}
        />
        <text
          x={px}
          y={py}
          fill={t.inkSoft}
          fontSize={14}
          textAnchor="middle"
          opacity={0.85}
        >
          {dec > 0 ? `+${dec}°` : `${dec}°`}
        </text>
      </g>
    );
  });

  const rim = (90 - DEC_MIN) / R_MAX;
  const rimPx = Math.abs(xScale(rim) - cx);
  const spokes = [];
  for (let h = 0; h < 24; h += 2) {
    const theta = (h / 24) * 2 * Math.PI;
    const edgeX = rim * Math.sin(theta);
    const edgeY = rim * Math.cos(theta);
    const labX = 1.075 * Math.sin(theta);
    const labY = 1.075 * Math.cos(theta);
    spokes.push(
      <g key={`ra-${h}`}>
        <line
          x1={cx}
          y1={cy}
          x2={xScale(edgeX)}
          y2={yScale(edgeY)}
          stroke={GRID}
          strokeWidth={0.8}
        />
        <text
          x={xScale(labX)}
          y={yScale(labY)}
          fill={t.inkSoft}
          fontSize={14}
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
      <circle
        cx={cx}
        cy={cy}
        r={rimPx}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={1.8}
        opacity={0.6}
      />
    </g>
  );
}

function ConstellationLines() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  return (
    <g
      stroke={t.inkSoft}
      strokeWidth={1.2}
      strokeOpacity={0.44}
      strokeLinecap="round"
    >
      {edgePairs.map(([a, b], i) => {
        const pa = starByName[a];
        const pb = starByName[b];
        return (
          <line
            key={i}
            x1={xScale(pa.x)}
            y1={yScale(pa.y)}
            x2={xScale(pb.x)}
            y2={yScale(pb.y)}
          />
        );
      })}
    </g>
  );
}

function ConstellationLabels() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const groups: Record<string, typeof stars> = {};
  for (const s of stars) {
    if (s.con) {
      (groups[s.con] = groups[s.con] || []).push(s);
    }
  }
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
            fontSize={14}
            fontStyle="italic"
            textAnchor="middle"
            opacity={0.82}
          >
            {CON_NAMES[con] || con}
          </text>
        );
      })}
    </g>
  );
}

function ChartTitleAndLegend() {
  const { left, top, width, height } = useDrawingArea();
  const x0 = left + 14;
  const y0 = top + height - 98;
  const samples = [-1, 1, 3, 5];
  return (
    <g>
      <text
        x={left + width / 2}
        y={top - 42}
        fill={t.ink}
        fontSize={22}
        fontWeight={600}
        textAnchor="middle"
      >
        Northern Celestial Hemisphere · star-chart-constellation · javascript · muix · anyplot.ai
      </text>
      <text
        x={x0}
        y={y0 - 16}
        fill={t.inkSoft}
        fontSize={14}
        fontWeight={600}
      >
        Apparent magnitude
      </text>
      {samples.map((mag, i) => {
        const f = (mag - MAG_LO) / (MAG_HI - MAG_LO);
        const r = Math.round(seqR1 + (seqR2 - seqR1) * f)
          .toString(16)
          .padStart(2, "0");
        const gr = Math.round(seqG1 + (seqG2 - seqG1) * f)
          .toString(16)
          .padStart(2, "0");
        const b = Math.round(seqB1 + (seqB2 - seqB1) * f)
          .toString(16)
          .padStart(2, "0");
        const cy = y0 + i * 24;
        return (
          <g key={mag}>
            <circle
              cx={x0 + 8}
              cy={cy}
              r={11 - f * 9}
              fill={`#${r}${gr}${b}`}
            />
            <text x={x0 + 30} y={cy + 5} fill={t.inkSoft} fontSize={14}>
              {`mag ${mag > 0 ? "+" : ""}${mag}${mag === -1 ? " (brightest)" : mag === 5 ? " (faintest)" : ""}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg }}>
      <ChartsContainer
        width={width}
        height={height}
        series={series}
        margin={{ top: 96, bottom: 56, left: 76, right: 76 }}
        xAxis={[{ id: "x", min: -1.12, max: 1.12, position: "none" }]}
        yAxis={[{ id: "y", min: -1.12, max: 1.12, position: "none" }]}
      >
        <SkyGrid />
        <ConstellationLines />
        <ScatterPlot skipAnimation />
        <ConstellationLabels />
        <ChartTitleAndLegend />
      </ChartsContainer>
    </div>
  );
}
