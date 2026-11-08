// anyplot.ai
// star-chart-constellation: Star Chart with Constellations
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
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
const RA_LABEL_RADIUS = 1.07; // hour labels, in rim radii
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
// stick figures, plus stars to magnitude 5.0 outside the figures.
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
  // Stars outside the stick figures, down to magnitude 5.0
  ["Talitha", 8.99, 48.04, 3.14, "UMa"], ["KapUMa", 9.06, 47.16, 3.6, "UMa"],
  ["TaniaBorealis", 10.29, 42.91, 3.45, "UMa"], ["TaniaAustralis", 10.37, 41.5, 3.05, "UMa"],
  ["AlulaBorealis", 11.31, 33.09, 3.48, "UMa"], ["AlulaAustralis", 11.3, 31.53, 3.79, "UMa"],
  ["Muscida", 8.5, 60.72, 3.36, "UMa"], ["ThetUMa", 9.55, 51.68, 3.17, "UMa"],
  ["UpsUMa", 9.85, 59.04, 3.8, "UMa"], ["PsiUMa", 11.16, 44.5, 3.01, "UMa"],
  ["ChiUMa", 11.77, 47.78, 3.71, "UMa"], ["23UMa", 9.53, 63.06, 3.67, "UMa"],
  ["EtaUMi", 16.29, 75.76, 4.95, "UMi"],
  ["Achird", 0.82, 57.82, 3.44, "Cas"], ["ZetCas", 0.62, 53.9, 3.66, "Cas"],
  ["KapCas", 0.55, 62.93, 4.16, "Cas"], ["ThetCas", 1.19, 55.15, 4.33, "Cas"],
  ["50Cas", 2.05, 72.42, 3.95, "Cas"],
  ["DelCep", 22.49, 58.42, 4.07, "Cep"], ["EtaCep", 20.76, 61.84, 3.41, "Cep"],
  ["ThetCep", 20.5, 62.99, 4.21, "Cep"], ["EpsCep", 22.25, 57.04, 4.18, "Cep"],
  ["MuCep", 21.73, 58.78, 4.08, "Cep"],
  ["ChiDra", 18.35, 72.73, 3.55, "Dra"], ["EpsDra", 19.8, 70.27, 3.83, "Dra"],
  ["KapDra", 12.56, 69.79, 3.87, "Dra"], ["Giausar", 11.52, 69.33, 3.84, "Dra"],
  ["Athebyne", 16.4, 61.51, 2.73, "Dra"], ["NuDra", 17.54, 55.18, 4.88, "Dra"],
  ["PhiDra", 18.35, 71.34, 4.22, "Dra"],
  ["Kornephoros", 16.5, 21.49, 2.77, "Her"], ["Rasalgethi", 17.24, 14.39, 3.08, "Her"],
  ["DelHer", 17.25, 24.84, 3.14, "Her"], ["MuHer", 17.77, 27.72, 3.42, "Her"],
  ["XiHer", 17.96, 29.25, 3.7, "Her"], ["OmiHer", 18.13, 28.76, 3.83, "Her"],
  ["IotHer", 17.66, 46.01, 3.8, "Her"], ["ThetHer", 17.94, 37.25, 3.86, "Her"],
  ["TauHer", 16.33, 46.31, 3.89, "Her"], ["GamHer", 16.37, 19.15, 3.75, "Her"],
  ["SigHer", 16.57, 42.44, 4.2, "Her"],
  ["ZetCyg", 21.22, 30.23, 3.21, "Cyg"], ["IotCyg", 19.5, 51.73, 3.76, "Cyg"],
  ["KapCyg", 19.29, 53.37, 3.8, "Cyg"], ["EtaCyg", 19.94, 35.08, 3.89, "Cyg"],
  ["Omi1Cyg", 20.23, 46.74, 3.8, "Cyg"], ["XiCyg", 21.08, 43.93, 3.72, "Cyg"],
  ["NuCyg", 20.95, 41.17, 3.94, "Cyg"], ["TauCyg", 21.25, 38.05, 3.72, "Cyg"],
  ["RhoCyg", 21.57, 45.59, 4.02, "Cyg"],
  ["Anser", 19.48, 24.66, 4.44, "Vul"], ["23Vul", 20.26, 27.81, 4.52, "Vul"],
  ["GamSge", 19.98, 19.49, 3.47, "Sge"], ["DelSge", 19.79, 18.53, 3.82, "Sge"],
  ["AlpSge", 19.67, 18.01, 4.37, "Sge"],
  ["Rotanev", 20.63, 14.6, 3.63, "Del"], ["Sualocin", 20.66, 15.91, 3.77, "Del"],
  ["GamDel", 20.78, 16.12, 3.87, "Del"], ["EpsDel", 20.55, 11.3, 4.03, "Del"],
  ["Kitalpha", 21.26, 5.25, 3.92, "Equ"],
  ["LamAql", 19.1, -4.88, 3.43, "Aql"], ["ThetAql", 20.19, -0.82, 3.26, "Aql"],
  ["EtaAql", 19.87, 1.01, 3.87, "Aql"], ["EpsAql", 18.99, 15.07, 4.02, "Aql"],
  ["RhoBoo", 14.53, 30.37, 3.58, "Boo"], ["ZetBoo", 14.69, 13.73, 3.78, "Boo"],
  ["UpsBoo", 13.83, 15.8, 4.07, "Boo"], ["LamBoo", 14.27, 46.09, 4.18, "Boo"],
  ["ThetBoo", 14.42, 51.85, 4.05, "Boo"], ["Alkalurops", 15.41, 37.38, 4.31, "Boo"],
  ["EpsCrB", 15.96, 26.88, 4.15, "CrB"],
  ["Diadem", 13.17, 17.53, 4.32, "Com"], ["BetCom", 13.2, 27.88, 4.26, "Com"],
  ["GamCom", 12.45, 28.27, 4.35, "Com"],
  ["Spica", 13.42, -11.16, 0.97, "Vir"], ["Porrima", 12.69, -1.45, 2.74, "Vir"],
  ["Vindemiatrix", 13.04, 10.96, 2.83, "Vir"], ["Zavijava", 11.85, 1.76, 3.61, "Vir"],
  ["Zaniah", 12.33, -0.67, 3.89, "Vir"], ["DelVir", 12.93, 3.4, 3.38, "Vir"],
  ["Heze", 13.58, -0.6, 3.37, "Vir"], ["MuVir", 14.72, -5.66, 3.88, "Vir"],
  ["IotVir", 14.27, -6.0, 4.08, "Vir"], ["NuVir", 11.76, 6.53, 4.03, "Vir"],
  ["GienahCrv", 12.26, -17.54, 2.59, "Crv"], ["Kraz", 12.57, -23.4, 2.65, "Crv"],
  ["Algorab", 12.5, -16.52, 2.94, "Crv"], ["Minkar", 12.17, -22.62, 3.0, "Crv"],
  ["Alchiba", 12.14, -24.73, 4.02, "Crv"],
  ["DelCrt", 11.32, -14.78, 3.56, "Crt"], ["Alkes", 11.0, -18.3, 4.08, "Crt"],
  ["Alphard", 9.46, -8.66, 1.98, "Hya"], ["ZetHya", 8.92, 5.95, 3.11, "Hya"],
  ["EpsHya", 8.78, 6.42, 3.38, "Hya"], ["DelHya", 8.63, 5.7, 4.16, "Hya"],
  ["ThetHya", 9.24, 2.31, 3.88, "Hya"], ["IotHya", 9.66, -1.14, 3.91, "Hya"],
  ["NuHya", 10.83, -16.19, 3.11, "Hya"], ["LamHya", 10.18, -12.35, 3.61, "Hya"],
  ["Zubenelgenubi", 14.85, -16.04, 2.75, "Lib"], ["Zubeneschamali", 15.28, -9.38, 2.61, "Lib"],
  ["Brachium", 15.07, -25.28, 3.29, "Lib"], ["GamLib", 15.59, -14.79, 3.91, "Lib"],
  ["UpsLib", 15.62, -28.14, 3.58, "Lib"],
  ["Antares", 16.49, -26.43, 1.06, "Sco"], ["Dschubba", 16.01, -22.62, 2.29, "Sco"],
  ["Acrab", 16.09, -19.81, 2.62, "Sco"], ["PiSco", 15.98, -26.11, 2.89, "Sco"],
  ["SigSco", 16.35, -25.59, 2.89, "Sco"], ["TauSco", 16.6, -28.22, 2.82, "Sco"],
  ["Rasalhague", 17.58, 12.56, 2.08, "Oph"], ["Cebalrai", 17.72, 4.57, 2.77, "Oph"],
  ["YedPrior", 16.24, -3.69, 2.73, "Oph"], ["YedPosterior", 16.31, -4.69, 3.24, "Oph"],
  ["ZetOph", 16.62, -10.57, 2.56, "Oph"], ["Sabik", 17.17, -15.72, 2.43, "Oph"],
  ["KapOph", 16.96, 9.38, 3.2, "Oph"], ["GamOph", 17.8, 2.71, 3.75, "Oph"],
  ["NuOph", 17.98, -9.77, 3.32, "Oph"], ["LamOph", 16.52, 1.98, 3.82, "Oph"],
  ["ThetOph", 17.37, -25.0, 3.27, "Oph"],
  ["Unukalhai", 15.74, 6.43, 2.63, "Ser"], ["BetSer", 15.77, 15.42, 3.67, "Ser"],
  ["GamSer", 15.94, 15.66, 3.85, "Ser"], ["EpsSer", 15.85, 4.48, 3.71, "Ser"],
  ["DelSer", 15.58, 10.54, 3.8, "Ser"], ["MuSer", 15.83, -3.43, 3.53, "Ser"],
  ["EtaSer", 18.36, -2.9, 3.26, "Ser"], ["Alya", 18.94, 4.2, 4.1, "Ser"],
  ["XiSer", 17.63, -15.4, 3.54, "Ser"],
  ["AlpSct", 18.59, -8.24, 3.85, "Sct"],
  ["Nunki", 18.92, -26.3, 2.05, "Sgr"], ["KausBorealis", 18.47, -25.42, 2.81, "Sgr"],
  ["PhiSgr", 18.76, -26.99, 3.17, "Sgr"], ["TauSgr", 19.12, -27.67, 3.32, "Sgr"],
  ["Albaldah", 19.16, -21.02, 2.89, "Sgr"], ["Xi2Sgr", 18.96, -21.11, 3.51, "Sgr"],
  ["OmiSgr", 19.08, -21.74, 3.77, "Sgr"],
  ["DenebAlgedi", 21.78, -16.13, 2.87, "Cap"], ["Dabih", 20.35, -14.78, 3.08, "Cap"],
  ["Nashira", 21.67, -16.66, 3.68, "Cap"], ["Algedi", 20.3, -12.54, 3.57, "Cap"],
  ["ZetCap", 21.44, -22.41, 3.74, "Cap"],
  ["Sadalsuud", 21.53, -5.57, 2.87, "Aqr"], ["Sadalmelik", 22.1, -0.32, 2.94, "Aqr"],
  ["Skat", 22.91, -15.82, 3.27, "Aqr"], ["ZetAqr", 22.48, -0.02, 3.65, "Aqr"],
  ["LamAqr", 22.88, -7.58, 3.74, "Aqr"], ["Albali", 20.79, -9.5, 3.77, "Aqr"],
  ["Sadachbia", 22.36, -1.39, 3.84, "Aqr"], ["88Aqr", 23.16, -21.17, 3.66, "Aqr"],
  ["Homam", 22.69, 10.83, 3.4, "Peg"], ["Matar", 22.72, 30.22, 2.94, "Peg"],
  ["Biham", 22.17, 6.2, 3.53, "Peg"], ["LamPeg", 22.78, 23.57, 3.95, "Peg"],
  ["MuPeg", 22.83, 24.6, 3.48, "Peg"], ["IotPeg", 22.12, 25.35, 3.76, "Peg"],
  ["PiAnd", 0.61, 33.72, 4.36, "And"], ["MuAnd", 0.95, 38.5, 3.87, "And"],
  ["51And", 1.63, 48.63, 3.57, "And"], ["OmiAnd", 23.03, 42.33, 3.62, "And"],
  ["LamAnd", 23.63, 46.46, 3.82, "And"], ["KapAnd", 23.67, 44.33, 4.14, "And"],
  ["AlpLac", 22.52, 50.28, 3.77, "Lac"], ["1Lac", 22.27, 37.75, 4.13, "Lac"],
  ["Alpherg", 1.53, 15.35, 3.62, "Psc"], ["GamPsc", 23.29, 3.28, 3.69, "Psc"],
  ["OmePsc", 23.99, 6.86, 4.03, "Psc"], ["IotPsc", 23.67, 5.63, 4.13, "Psc"],
  ["Alrescha", 2.03, 2.76, 3.82, "Psc"], ["OmiPsc", 1.76, 9.16, 4.26, "Psc"],
  ["Menkar", 3.04, 4.09, 2.54, "Cet"], ["Diphda", 0.73, -17.99, 2.04, "Cet"],
  ["Kaffaljidhma", 2.72, 3.24, 3.47, "Cet"], ["TauCet", 1.73, -15.94, 3.5, "Cet"],
  ["EtaCet", 1.14, -10.18, 3.45, "Cet"], ["ThetCet", 1.4, -8.18, 3.6, "Cet"],
  ["BatenKaitos", 1.86, -10.34, 3.73, "Cet"], ["IotCet", 0.32, -8.82, 3.56, "Cet"],
  ["UpsCet", 2.0, -21.08, 4.0, "Cet"],
  ["Bharani", 2.83, 27.26, 3.63, "Ari"], ["Botein", 3.19, 19.73, 4.35, "Ari"],
  ["ZetPer", 3.9, 31.88, 2.85, "Per"], ["Menkib", 3.98, 35.79, 4.04, "Per"],
  ["Atik", 3.9, 32.29, 3.84, "Per"], ["RhoPer", 3.09, 38.84, 3.39, "Per"],
  ["KapPer", 3.16, 44.86, 3.8, "Per"], ["EtaPer", 2.85, 55.9, 3.76, "Per"],
  ["NuPer", 3.75, 42.58, 3.77, "Per"], ["MuPer", 4.25, 48.41, 4.14, "Per"],
  ["BetCam", 5.06, 60.44, 4.03, "Cam"], ["AlpCam", 4.9, 66.34, 4.29, "Cam"],
  ["GamCam", 3.84, 71.33, 4.63, "Cam"],
  ["Almaaz", 5.03, 43.82, 2.99, "Aur"], ["Haedus", 5.11, 41.23, 3.17, "Aur"],
  ["Saclateni", 5.04, 41.08, 3.75, "Aur"], ["DelAur", 5.99, 54.28, 3.72, "Aur"],
  ["NuAur", 5.86, 39.15, 3.97, "Aur"],
  ["Alcyone", 3.79, 24.11, 2.87, "Tau"], ["Atlas", 3.82, 24.05, 3.62, "Tau"],
  ["Electra", 3.75, 24.11, 3.7, "Tau"], ["Maia", 3.76, 24.37, 3.87, "Tau"],
  ["Del1Tau", 4.38, 17.54, 3.77, "Tau"], ["Thet2Tau", 4.48, 15.87, 3.4, "Tau"],
  ["OmiTau", 3.41, 9.03, 3.6, "Tau"], ["XiTau", 3.45, 9.73, 3.74, "Tau"],
  ["NuTau", 4.05, 5.99, 3.91, "Tau"],
  ["Meissa", 5.59, 9.93, 3.39, "Ori"], ["Pi3Ori", 4.83, 6.96, 3.19, "Ori"],
  ["EtaOri", 5.41, -2.4, 3.36, "Ori"], ["Hatysa", 5.59, -5.91, 2.77, "Ori"],
  ["MuOri", 6.04, 9.65, 4.12, "Ori"], ["Pi4Ori", 4.85, 5.61, 3.69, "Ori"],
  ["TauOri", 5.29, -6.84, 3.6, "Ori"], ["SigOri", 5.65, -2.6, 3.81, "Ori"],
  ["Propus", 6.25, 22.51, 3.28, "Gem"], ["KapGem", 7.74, 24.4, 3.57, "Gem"],
  ["LamGem", 7.3, 16.54, 3.58, "Gem"], ["XiGem", 6.75, 12.9, 3.35, "Gem"],
  ["IotGem", 7.43, 27.8, 3.79, "Gem"], ["ThetGem", 6.88, 33.96, 3.6, "Gem"],
  ["Mekbuda", 7.07, 20.57, 3.79, "Gem"],
  ["Procyon", 7.66, 5.22, 0.34, "CMi"], ["Gomeisa", 7.45, 8.29, 2.89, "CMi"],
  ["Altarf", 8.28, 9.19, 3.52, "Cnc"], ["AsellusAustralis", 8.74, 18.15, 3.94, "Cnc"],
  ["AsellusBorealis", 8.72, 21.47, 4.66, "Cnc"], ["Acubens", 8.97, 11.86, 4.26, "Cnc"],
  ["IotCnc", 8.78, 28.76, 4.02, "Cnc"],
  ["AlpLyn", 9.35, 34.39, 3.14, "Lyn"], ["38Lyn", 9.31, 36.8, 3.82, "Lyn"],
  ["31Lyn", 8.38, 43.19, 4.25, "Lyn"], ["15Lyn", 6.95, 58.42, 4.35, "Lyn"],
  ["Praecipua", 10.89, 34.21, 3.83, "LMi"], ["BetLMi", 10.46, 36.71, 4.21, "LMi"],
  ["Adhafera", 10.28, 23.42, 3.44, "Leo"], ["Rasalas", 9.88, 26.01, 3.88, "Leo"],
  ["Subra", 9.69, 9.89, 3.52, "Leo"], ["IotLeo", 11.4, 10.53, 3.94, "Leo"],
  ["SigLeo", 11.35, 6.03, 4.05, "Leo"], ["RhoLeo", 10.55, 9.31, 3.85, "Leo"],
  ["Muliphein", 7.06, -15.63, 4.12, "CMa"], ["Omi2CMa", 7.05, -23.83, 3.02, "CMa"],
  ["Omi1CMa", 6.9, -24.18, 3.87, "CMa"], ["Nu2CMa", 6.61, -19.26, 3.95, "CMa"],
  ["SigCMa", 7.03, -27.93, 3.47, "CMa"], ["ThetCMa", 6.9, -12.04, 4.07, "CMa"],
  ["Arneb", 5.55, -17.82, 2.58, "Lep"], ["Nihal", 5.47, -20.76, 2.84, "Lep"],
  ["EpsLep", 5.09, -22.37, 3.19, "Lep"], ["MuLep", 5.22, -16.21, 3.31, "Lep"],
  ["ZetLep", 5.78, -14.82, 3.55, "Lep"], ["GamLep", 5.74, -22.45, 3.59, "Lep"],
  ["BetMon", 6.48, -7.03, 3.76, "Mon"], ["AlpMon", 7.69, -9.55, 3.94, "Mon"],
  ["GamMon", 6.25, -6.27, 3.98, "Mon"], ["DelMon", 7.2, -0.49, 4.15, "Mon"],
  ["Cursa", 5.13, -5.09, 2.79, "Eri"], ["Zaurak", 3.97, -13.51, 2.95, "Eri"],
  ["Rana", 3.72, -9.76, 3.54, "Eri"], ["EpsEri", 3.55, -9.46, 3.73, "Eri"],
  ["Azha", 2.94, -8.9, 3.89, "Eri"], ["NuEri", 4.61, -3.35, 3.93, "Eri"],
  ["Tau4Eri", 3.32, -21.76, 3.69, "Eri"],
  ["RhoPup", 8.13, -24.3, 2.81, "Pup"], ["XiPup", 7.82, -24.86, 3.34, "Pup"],
];

const data: Record<string, string | number | null>[] = catalog.map(([star, ra, dec, mag, con]) => ({
  [STAR]: star,
  [RA]: ra,
  [DEC]: dec,
  [MAGNITUDE]: mag,
  [CONSTELLATION]: con,
}));

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

// Only constellations with a stick figure get a name
const constellations = [...new Set(sticks.flatMap(([a, b]) => [a.con, b.con]).filter((c) => c != null) as string[])];
const figured = new Set(constellations);
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
// The dec labels prefer the middle of the spoke sector holding the fewest stars
const turnGap = (a: number, b: number) => Math.abs(((a - b + 1.5) % 1) - 0.5);
const sectorTurns = Array.from({ length: RA_SPOKES }, (_, k) => (k + 0.5) / RA_SPOKES);
const sectorCrowding = sectorTurns.map(
  (turn) => stars.filter((s) => turnGap((Math.atan2(s.x, s.y) / (2 * Math.PI) + 1) % 1, turn) < 0.5 / RA_SPOKES).length,
);
const decLabelTurn = sectorTurns[sectorCrowding.indexOf(Math.min(...sectorCrowding))];
// Grid labels in rim radii: hour labels just outside the rim, declination labels on their circles
const raLabels = spokes.map((h) => ({
  h,
  text: `${h}${raUnit}`,
  x: RA_LABEL_RADIUS * Math.sin((h / RA_PERIOD) * 2 * Math.PI),
  y: RA_LABEL_RADIUS * Math.cos((h / RA_PERIOD) * 2 * Math.PI),
}));
const decLabelsAt = (turn: number) =>
  decRings.map((dec) => ({
    dec,
    text: `${dec > 0 ? "+" : ""}${dec}${decUnit}`,
    x: ((90 - dec) / rimDistance) * Math.sin(turn * 2 * Math.PI),
    y: ((90 - dec) / rimDistance) * Math.cos(turn * 2 * Math.PI),
  }));
const legendLo = Math.ceil(magMin);
const legendHi = Math.round(magMax);
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
// A constellation name takes the shift from its own stars' centroid (px), nearest first, whose box
// clears every star, every stick line and every name placed before it, and whose nearest figure
// mark (star or stick line) belongs to its own constellation, so no name sits closer to a
// neighbouring figure than to its own; names never overlap each other
const NAME_STEP_PX = 10;
const NAME_REACH_STEPS = 8;
const NAME_CHAR_PX = 7.2; // average glyph width of the 14 px italic names
const NAME_HALF_H_PX = 9;
const NAME_STAR_GAP_PX = 3;
const NAME_OWN_MARGIN_PX = 6; // how much nearer its own figure a name sits than any other figure
const NAME_GAP_X_PX = 16; // side by side, two labels this close would read as one string
const NAME_GAP_Y_PX = 4;
const STICK_SAMPLE_PX = 3; // spacing of the points a stick line is measured by
const nameShifts: { dx: number; dy: number }[] = [];
for (let i = -NAME_REACH_STEPS; i <= NAME_REACH_STEPS; i += 1) {
  for (let j = -NAME_REACH_STEPS; j <= NAME_REACH_STEPS; j += 1) {
    nameShifts.push({ dx: i * NAME_STEP_PX, dy: j * NAME_STEP_PX });
  }
}
nameShifts.sort((a, b) => Math.hypot(a.dx, a.dy) - Math.hypot(b.dx, b.dy));
const DEC_LABEL_STEPS = 144; // candidate angles for the declination label column
const DEC_LABEL_GAP_PX = 4;
const decTurns = Array.from({ length: DEC_LABEL_STEPS }, (_, k) => k / DEC_LABEL_STEPS)
  .filter((turn) => turnGap(turn * RA_SPOKES, 0) > 0.15) // keep the labels off the spokes
  .sort((a, b) => turnGap(a, decLabelTurn) - turnGap(b, decLabelTurn));

// Every mark in pixels, each tagged with its figure (stars outside the figures carry none): the
// stars, and the stick lines as points a few px apart. The declination labels take the angle
// nearest the preferred sector at which they clear all of them.
function useSkyMarks() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const magAxis = useZAxis("mag");
  const marks = [
    ...stars.map((s) => ({
      x: xs(s.x),
      y: ys(s.y),
      reach: magAxis.sizeScale(s.sizeValue) as number,
      con: s.con != null && figured.has(s.con) ? s.con : null,
    })),
    ...sticks.flatMap(([a, b]) => {
      const [ax, ay, bx, by] = [xs(a.x), ys(a.y), xs(b.x), ys(b.y)];
      const steps = Math.max(1, Math.ceil(Math.hypot(bx - ax, by - ay) / STICK_SAMPLE_PX));
      return Array.from({ length: steps + 1 }, (_, k) => ({
        x: ax + ((bx - ax) * k) / steps,
        y: ay + ((by - ay) * k) / steps,
        reach: 1,
        con: a.con,
      }));
    }),
  ];
  const clashes = (labels: { text: string; x: number; y: number }[]) =>
    labels.filter((l) => {
      const halfW = (l.text.length * NAME_CHAR_PX) / 2;
      return marks.some(
        (p) =>
          Math.hypot(Math.max(Math.abs(p.x - xs(l.x)) - halfW, 0), Math.max(Math.abs(p.y - ys(l.y)) - NAME_HALF_H_PX, 0)) <
          p.reach + DEC_LABEL_GAP_PX,
      );
    }).length;
  const options = decTurns.map((turn) => decLabelsAt(turn));
  const scores = options.map(clashes);
  const decLabels = options[scores.indexOf(Math.min(...scores))];
  return { xs, ys, magAxis, marks, decLabels };
}

// Declination circles, hour spokes, the rim and the constellation stick figures
function SkyGrid() {
  const { xs, ys, decLabels } = useSkyMarks();
  const unit = xs(1) - xs(0);
  const cx = xs(0);
  const cy = ys(0);
  return (
    <g>
      {raLabels.map((l) => (
        <g key={`ra-${l.h}`}>
          <line x1={cx} y1={cy} x2={xs(l.x / RA_LABEL_RADIUS)} y2={ys(l.y / RA_LABEL_RADIUS)} stroke={t.grid} strokeWidth={1} />
          <text x={xs(l.x)} y={ys(l.y)} fill={t.inkSoft} fontSize={15} textAnchor="middle" dominantBaseline="central">
            {l.text}
          </text>
        </g>
      ))}
      {decLabels.map((l) => (
        <g key={`dec-${l.dec}`}>
          <circle cx={cx} cy={cy} r={((90 - l.dec) / rimDistance) * unit} fill="none" stroke={t.grid} strokeWidth={1} />
          <text
            x={xs(l.x)}
            y={ys(l.y)}
            fill={t.inkSoft}
            fontSize={14}
            textAnchor="middle"
            dominantBaseline="central"
            {...labelHalo}
          >
            {l.text}
          </text>
        </g>
      ))}
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
  const { xs, ys, magAxis, marks: skyMarks, decLabels } = useSkyMarks();
  const { left, top, height } = useDrawingArea();
  const x0 = left + 12;
  const y0 = top + height - legendMags.length * 30 - 6;
  // Names keep a small gap to the stars
  const marks = skyMarks.map((m, i) => (i < stars.length ? { ...m, reach: m.reach + NAME_STAR_GAP_PX } : m));
  const figureMarks = marks.filter((m) => m.con != null);
  // The grid's hour and declination labels are taken space, like every name placed before
  const placedBoxes = [...raLabels, ...decLabels].map((l) => ({
    x0: xs(l.x) - (l.text.length * NAME_CHAR_PX) / 2,
    x1: xs(l.x) + (l.text.length * NAME_CHAR_PX) / 2,
    y0: ys(l.y) - NAME_HALF_H_PX,
    y1: ys(l.y) + NAME_HALF_H_PX,
  }));
  const names = centroids.map((c) => {
    const halfW = (c.name.length * NAME_CHAR_PX) / 2;
    const candidates = nameShifts.map(({ dx, dy }) => {
      const cx = xs(c.x) + dx;
      const cy = ys(c.y) + dy;
      const box = { x0: cx - halfW, x1: cx + halfW, y0: cy - NAME_HALF_H_PX, y1: cy + NAME_HALF_H_PX };
      const hits = marks.filter(
        (p) => p.x > box.x0 - p.reach && p.x < box.x1 + p.reach && p.y > box.y0 - p.reach && p.y < box.y1 + p.reach,
      ).length;
      const nameHit = placedBoxes.some(
        (b) =>
          b.x0 - NAME_GAP_X_PX < box.x1 &&
          b.x1 + NAME_GAP_X_PX > box.x0 &&
          b.y0 - NAME_GAP_Y_PX < box.y1 &&
          b.y1 + NAME_GAP_Y_PX > box.y0,
      );
      let ownGap = Infinity;
      let otherGap = Infinity;
      for (const p of figureMarks) {
        const gap = Math.hypot(Math.max(Math.abs(p.x - cx) - halfW, 0), Math.max(Math.abs(p.y - cy) - NAME_HALF_H_PX, 0));
        if (p.con === c.con) ownGap = Math.min(ownGap, gap);
        else otherGap = Math.min(otherGap, gap);
      }
      return { cx, cy, box, hits, nameHit, owned: ownGap + NAME_OWN_MARGIN_PX <= otherGap };
    });
    const free = candidates.filter((cand) => !cand.nameHit);
    const pool = free.length > 0 ? free : candidates;
    const best =
      pool.find((cand) => cand.hits === 0 && cand.owned) ??
      pool.find((cand) => cand.hits === 0) ??
      pool.reduce((a, b) => (b.hits < a.hits ? b : a));
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
