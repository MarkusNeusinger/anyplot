// anyplot.ai
// scatter-map-geographic: Scatter Map with Geographic Points
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const WORLD = { lonMin: -180, lonMax: 180, latMin: -90, latMax: 90 }; // the whole globe, in degrees
const PAD_SHARE = 0.025; // map padding on each side as a share of the globe's span, so markers on its edge stay inside
const GRATICULE_LON_STEP = 60; // degrees between meridians
const GRATICULE_LAT_STEP = 30; // degrees between parallels
const MARKER_RADIUS = [4, 16]; // px for the smallest and the largest size value
const POINT_OPACITY = 0.82;

// Columns: set these to your data's column names
const LATITUDE = "Latitude"; // role: latitude
const LONGITUDE = "Longitude"; // role: longitude
const DEPTH = "Depth (km)"; // role: value
const MAGNITUDE = "Magnitude (Mw)"; // role: size
const ZONE = "Seismic zone"; // role: label

// Data: replace this block with your own records, one object per row
// Simplified land outlines ([lon, lat] rings) for the basemap, and simulated
// M5.0+ earthquake epicentres along the plate boundaries of major subduction,
// transform and collision zones (Ring of Fire, Alpide belt).
const LAND_OUTLINES = [
  // North and Central America
  [
    [-168, 65.6], [-166, 68.9], [-156.8, 71.3], [-141, 69.6], [-128, 70], [-117, 68.9],
    [-108, 68], [-96, 67.5], [-89, 68.5], [-82, 66.5], [-86, 64], [-92, 62.5], [-94.5, 59],
    [-92.5, 57], [-87, 55.5], [-82, 55], [-82.5, 52.5], [-79, 51.5], [-78.5, 55], [-77, 58],
    [-78, 60.5], [-74, 62.3], [-70, 61], [-65, 60.3], [-61, 56], [-56, 52.5], [-59.5, 50.4],
    [-64.5, 49.2], [-64, 48], [-61, 45.5], [-66, 43.8], [-70, 43.7], [-70.5, 41.8], [-74, 40.5],
    [-75.5, 38], [-76, 35], [-78.5, 33.8], [-81, 31.5], [-80.5, 28], [-80.1, 25.5], [-81.1, 25.1],
    [-82.7, 27.8], [-84, 30], [-87.5, 30.3], [-89.5, 30], [-90, 29], [-94, 29.6], [-97.2, 27.5],
    [-97.5, 24], [-97.7, 21.5], [-96.5, 19.3], [-94.5, 18.2], [-91, 18.8], [-90.4, 21], [-87, 21.5],
    [-87.5, 18.5], [-88.2, 16], [-84, 15.8], [-83.3, 15], [-83.7, 11], [-81.5, 9], [-79.5, 9.5],
    [-77.4, 8.6], [-78.2, 7.5], [-80, 7.4], [-82.5, 8.2], [-85.7, 10], [-85.8, 11.2], [-87.6, 13],
    [-91.5, 14], [-94.5, 16], [-96.5, 15.7], [-99.8, 16.8], [-103.5, 18.3], [-105.5, 20.5],
    [-105.3, 22.5], [-108.5, 25.5], [-111, 27.9], [-112.8, 31.5], [-114.7, 31.7], [-112.5, 27.5],
    [-110, 24], [-109.5, 23], [-112, 24.8], [-114.3, 27.5], [-115.8, 30.4], [-117.1, 32.5],
    [-118.5, 34], [-120.6, 34.6], [-122.5, 37.5], [-123.8, 39.5], [-124.3, 42], [-124, 46.3],
    [-124.7, 48.4], [-123, 49], [-125, 50], [-127.5, 51], [-130, 54.5], [-133, 57.5], [-136.5, 58.5],
    [-140, 59.8], [-145, 60.3], [-148, 60], [-151, 59.2], [-154, 58], [-158, 56.5], [-162, 55],
    [-164.5, 54.5], [-161, 56], [-158, 57.5], [-157.5, 58.7], [-162, 59.8], [-165, 61], [-164.5, 63],
    [-161, 64.5], [-165, 64.5], [-168, 65.6],
  ],
  // Aleutian Islands
  [[-178, 51.5], [-170, 52.5], [-165, 54], [-164.5, 54.6], [-170, 53.1], [-178, 52.1], [-178, 51.5]],
  // Canadian Arctic Archipelago (Baffin, Victoria, Banks, Ellesmere)
  [
    [-80, 73.7], [-73, 71.5], [-67, 69.5], [-62, 66.8], [-64, 63.5], [-66, 62], [-71, 62.8],
    [-78, 64.4], [-73, 67.8], [-78, 70], [-85, 70], [-90, 71.5], [-86, 73.5], [-80, 73.7],
  ],
  [[-118, 69], [-106, 68.8], [-101, 69.6], [-104, 71], [-107, 73.5], [-114, 73], [-119, 71.5], [-118, 69]],
  [[-125, 71.8], [-120, 71.5], [-117, 74.5], [-124, 74], [-125, 71.8]],
  [[-90, 76.5], [-80, 76.3], [-75, 79], [-62, 82], [-70, 83], [-85, 82], [-92, 80.5], [-90, 76.5]],
  // Greenland, Iceland, Newfoundland
  [
    [-73, 78.5], [-67, 76], [-58, 75.5], [-55, 72], [-53, 68], [-51, 64], [-48, 61], [-44, 60],
    [-42, 61.5], [-40, 65], [-35, 66.5], [-26, 68.5], [-22, 70.5], [-22, 73.5], [-19, 76], [-18, 79],
    [-12, 81.5], [-25, 83], [-40, 83.5], [-55, 82.5], [-62, 81.8], [-68, 80.5], [-73, 78.5],
  ],
  [[-24, 65.5], [-22, 66.4], [-17, 66.5], [-14, 65.5], [-15, 64.3], [-18.5, 63.4], [-22, 63.8], [-24, 65.5]],
  [[-59.3, 47.6], [-56, 47.5], [-53, 46.6], [-52.7, 47.8], [-55.5, 49.8], [-55.5, 51.6], [-57.5, 50.7], [-59.3, 47.6]],
  // Cuba, Hispaniola
  [[-85, 21.9], [-82, 23.2], [-77.5, 22], [-74.2, 20.2], [-77.5, 19.9], [-80, 21.7], [-82.5, 21.6], [-85, 21.9]],
  [[-74.4, 18.4], [-72.8, 19.9], [-69.5, 19.5], [-68.4, 18.6], [-71, 18], [-74.4, 18.4]],
  // South America, Tierra del Fuego
  [
    [-77.4, 8.6], [-76, 9.4], [-75.5, 10.6], [-74, 11.3], [-71.5, 12.4], [-70, 11.5], [-68, 10.5],
    [-64, 10.6], [-61.5, 10.5], [-60, 8.5], [-57, 6], [-54, 5.7], [-51.5, 4.2], [-50, 1.7], [-49, 0],
    [-47, -0.8], [-44, -2.5], [-41, -2.9], [-38.5, -3.7], [-35.2, -5.5], [-34.8, -7.5], [-35.5, -9.5],
    [-37.5, -11.5], [-39, -13.5], [-39.2, -17.5], [-40.5, -20.5], [-42, -23], [-44.5, -23.3],
    [-48, -25.8], [-48.6, -28.5], [-50.5, -31], [-53.4, -33.7], [-55, -35], [-57.2, -35.5],
    [-57.5, -38.2], [-62, -39], [-62.3, -40.6], [-65, -41], [-64.5, -42.5], [-65.5, -45],
    [-67.5, -46.5], [-65.8, -48], [-68.5, -50.5], [-68.4, -52.3], [-70, -52.8], [-71.5, -53.8],
    [-74, -52], [-75.5, -49], [-74.5, -46], [-73.5, -43], [-73.7, -39.5], [-73.2, -37], [-71.6, -33],
    [-71.4, -30], [-70.8, -27], [-70.4, -23.5], [-70.2, -20], [-70.4, -18.4], [-72.5, -17],
    [-76, -14.2], [-77.2, -12], [-79, -8.5], [-81, -6], [-81.2, -4.5], [-80, -2.5], [-80.9, -1],
    [-80, 1], [-78.8, 1.6], [-77.4, 4], [-77.4, 6.8], [-77.4, 8.6],
  ],
  [[-68.6, -52.6], [-65.2, -54.8], [-68.5, -55.5], [-72, -54.5], [-70, -53], [-68.6, -52.6]],
  // Africa (with Sinai), Madagascar
  [
    [32.3, 31.2], [29, 30.9], [25, 31.6], [23, 32.6], [21, 32.8], [20, 32], [19.5, 30.5], [17, 31],
    [15.3, 32.3], [13, 32.9], [11.2, 33.2], [10.2, 34.5], [11, 35.5], [10.3, 36.8], [11, 37.1],
    [9.7, 37.3], [8, 36.9], [3, 36.8], [-1, 35.4], [-2, 35.1], [-5.4, 35.9], [-6.2, 35.8],
    [-9.6, 30.4], [-11.5, 28], [-13.2, 27.6], [-14.5, 26], [-16, 24], [-17.1, 21], [-16.3, 19.5],
    [-16.5, 16.2], [-17.5, 14.7], [-16.7, 12.5], [-15, 11], [-13.5, 9.5], [-12, 7.5], [-9.5, 5.2],
    [-7.5, 4.4], [-4, 5.2], [-1, 5], [1.6, 6.2], [4.5, 6.3], [6, 4.3], [7.5, 4.5], [9.5, 3.8],
    [9.8, 2.5], [9.4, 0], [8.8, -1], [11.1, -3.8], [12.2, -5.8], [13.2, -8.6], [13.6, -12.2],
    [11.8, -15.8], [12.4, -19], [14.5, -22.9], [15.2, -27], [16.5, -28.6], [18.2, -32], [18.4, -34.1],
    [20, -34.8], [22.5, -34], [25.6, -34], [27.5, -33.2], [30.1, -31.1], [32.5, -28.5], [32.9, -26],
    [35.5, -24], [35.4, -22.1], [34.7, -19.9], [36.8, -17.9], [40.5, -15], [40.5, -10.5], [39.3, -7],
    [39.2, -4.7], [41.6, -1.7], [44, 1.6], [47.5, 4.9], [50.5, 9.5], [51.3, 11.8], [49, 11.2],
    [45, 10.4], [43.3, 11.5], [41.5, 14], [39.5, 15.5], [38.5, 18], [37.3, 21], [36.9, 22],
    [35.6, 23.9], [34, 26.5], [32.5, 29.9], [34.2, 27.8], [34.9, 29.5], [34.2, 31.3], [32.3, 31.2],
  ],
  [
    [49.3, -12], [50.5, -15.5], [49.8, -17], [48.5, -20.5], [47.2, -24.8], [45.2, -25.5], [43.6, -23.5],
    [43.3, -21.8], [44.4, -19.5], [44, -17], [46.3, -15.8], [47.9, -13.6], [49.3, -12],
  ],
  // Eurasia
  [
    [-5.6, 36], [-6.5, 37], [-8.9, 37], [-8.8, 40], [-8.8, 42], [-9.3, 43], [-8, 43.7], [-4, 43.4],
    [-1.5, 43.4], [-1.2, 46], [-2.5, 47.3], [-4.6, 48.3], [-1.5, 48.7], [-1.3, 49.7], [1.5, 50.1],
    [2.5, 51.1], [4.2, 51.9], [5, 53.3], [8.5, 53.6], [8.6, 55], [8.1, 56.6], [10.5, 57.7],
    [10.5, 56.2], [9.8, 55], [10.9, 54], [12.5, 54.4], [14.3, 53.9], [18, 54.8], [21, 55], [21.1, 57],
    [24, 57.3], [23.5, 59.2], [28, 59.5], [23, 59.9], [21.3, 60.8], [21.5, 63], [24.5, 64.8],
    [25.5, 65.5], [22, 65.8], [21, 64.5], [17.5, 62.5], [17.2, 61], [18.8, 59.8], [16.8, 58.5],
    [16.4, 56.5], [14, 55.4], [12.7, 56], [11.8, 58], [11, 59], [8, 58.1], [5.6, 58.8], [5, 61],
    [6.5, 62.6], [10, 64], [13, 66.5], [16, 68.5], [19, 69.9], [23.5, 70.8], [28, 71], [31, 70],
    [33, 69.3], [41, 67.4], [44, 66.3], [44, 68.5], [53, 68.5], [59, 68.8], [66, 69.5], [69, 73],
    [73, 72.5], [80, 73.5], [87, 74.5], [100, 76.5], [105, 77.6], [113, 73.6], [120, 73], [128, 72.5],
    [132, 71.8], [140, 72.6], [150, 71.5], [160, 70], [170, 69.9], [178, 69.4], [180, 68.9], [180, 65],
    [178, 64.5], [177, 62.5], [173, 61.5], [170, 60], [166, 60], [163, 57], [162, 56], [160, 53],
    [156.7, 51], [156, 57], [160, 61.5], [155, 59.3], [152, 59.2], [148, 59.3], [143, 59.3], [141, 58],
    [137, 54.5], [141, 53], [140.5, 48.5], [136, 44], [132, 42.8], [129.7, 41], [129.4, 37],
    [129.2, 35.2], [126.5, 34.4], [126.4, 37], [125, 37.8], [124.5, 39.8], [121.5, 39], [121.6, 40.9],
    [118, 39], [118, 37.5], [122.5, 37.2], [119.5, 35], [121, 32], [122, 30], [120, 26], [116, 22.8],
    [113.5, 22.2], [110, 21.5], [108.5, 21.6], [106.5, 20], [105.7, 18.5], [107.5, 16.5], [109.3, 13],
    [109, 11.5], [106.5, 10.4], [105, 8.7], [104.7, 10.4], [102.5, 12.2], [100.9, 12.6], [100, 13.5],
    [99.2, 10], [100.4, 7.2], [101.5, 6.8], [103.4, 4.5], [103.5, 1.5], [101.3, 2.5], [100.4, 5],
    [98.3, 8], [98.5, 13], [97.6, 16.5], [96.5, 16.6], [94.3, 16], [94.2, 19.5], [92.3, 21],
    [91.8, 22.6], [90, 21.9], [88.2, 21.7], [86.5, 20], [85, 19.3], [82.3, 16.6], [80.2, 15.2],
    [80.1, 13], [79.8, 10.3], [78.2, 8.9], [77.3, 8.1], [76.3, 9.8], [75, 12.8], [73.5, 16],
    [72.8, 19.3], [72.7, 21.2], [72.6, 22.3], [70, 21], [69, 22.5], [68.3, 23.6], [66.8, 24.8],
    [64.5, 25.2], [61.6, 25.2], [57.3, 25.8], [56.4, 27.1], [54.7, 26.5], [51.5, 27.9], [50.2, 29.8],
    [48, 29.9], [48.4, 28.4], [49.6, 26.8], [51.6, 24.2], [54, 24.1], [56.3, 26.2], [56.4, 24.5],
    [58.5, 23.6], [59.8, 22.5], [58.5, 20.5], [57.7, 19], [55.4, 17.7], [52.3, 16.3], [48.7, 14],
    [45, 12.8], [43.4, 12.7], [42.8, 15], [42.7, 16.5], [41.2, 19], [39.1, 21.5], [38, 24], [36.5, 26],
    [35.2, 28.1], [34.9, 29.5], [34.2, 31.3], [34.9, 32.8], [35.5, 34], [36, 35.8], [35.8, 36.8],
    [34.5, 36.8], [32.5, 36.1], [30.5, 36.4], [28.2, 36.7], [27.3, 37.8], [26.3, 38.8], [26.6, 40.2],
    [29, 41.1], [31.5, 41.2], [35, 42], [38.5, 40.9], [41.5, 41.5], [41.7, 42.6], [40, 43.4],
    [38, 44.6], [36.7, 45.2], [35, 45], [33.5, 44.5], [32.5, 45.3], [33.6, 46], [31, 46.6], [30, 45.5],
    [29.6, 45], [28.7, 44.2], [28, 42.5], [28.9, 41.3], [27, 40.6], [26.2, 40.6], [24, 40.8],
    [23, 40.3], [23.5, 39.5], [23, 38], [24, 37.7], [22.8, 36.5], [21.7, 36.8], [21.1, 38.3],
    [20.7, 39.2], [19.4, 40.4], [19.4, 41.8], [18.5, 42.5], [16, 43.5], [14.5, 45.2], [13.7, 45.7],
    [12.3, 45.4], [12.4, 44.2], [13.6, 43.5], [14.8, 42.1], [16.2, 41.8], [18.5, 40.2], [17, 39],
    [16.6, 38], [15.7, 38], [16.1, 39.5], [15.6, 40.1], [14, 41], [12.3, 41.7], [11, 42.6], [10.1, 44],
    [8.8, 44.4], [7.5, 43.8], [6.2, 43.1], [4.5, 43.4], [3.1, 43], [3.2, 41.9], [0.9, 41], [0, 39.8],
    [-0.4, 38.4], [-0.8, 37.6], [-2.2, 36.8], [-4.4, 36.7], [-5.6, 36],
  ],
  // Chukotka east of the antimeridian
  [[-180, 68.9], [-175, 67.5], [-171, 66.8], [-169.7, 66], [-171.5, 65], [-173, 64.3], [-176.5, 65.3], [-180, 65], [-180, 68.9]],
  // Great Britain, Ireland, Sicily, Sardinia, Crete, Svalbard, Novaya Zemlya
  [
    [-5.7, 50.1], [-3, 50.6], [1.3, 51.1], [1.7, 52.6], [0.3, 53.5], [-1.3, 54.7], [-2, 55.9],
    [-2.5, 56.6], [-1.8, 57.6], [-3.4, 58.6], [-5, 58.6], [-6.2, 57.5], [-5.7, 56], [-4.8, 55],
    [-3.2, 54.9], [-3.3, 54.2], [-3, 53.4], [-4.6, 53.3], [-4.1, 52.5], [-5.1, 51.8], [-3.2, 51.4],
    [-5.7, 50.1],
  ],
  [[-6, 52.1], [-6.2, 53.5], [-5.6, 54.5], [-6.4, 55.2], [-8.3, 55.2], [-10, 54.2], [-9.7, 53], [-10.3, 51.9], [-8.5, 51.6], [-6, 52.1]],
  [[12.4, 38.1], [15.6, 38.3], [15.1, 36.7], [12.4, 37.6], [12.4, 38.1]],
  [[8.4, 39], [9.6, 39.1], [9.8, 41], [8.2, 41], [8.4, 39]],
  [[23.5, 35.3], [26.3, 35.2], [24.8, 34.9], [23.5, 35.3]],
  [[11, 78.5], [17, 80.2], [27, 80], [22, 78], [16, 76.6], [11, 78.5]],
  [[52, 71.5], [56, 73.5], [61, 76.3], [68, 76.8], [60, 75], [56, 71], [52, 71.5]],
  // Sri Lanka, Hainan, Taiwan, Sakhalin
  [[79.8, 7], [80, 9.8], [81.4, 8.5], [81.8, 7], [80.6, 6], [79.8, 7]],
  [[108.6, 19.2], [110.5, 20.1], [111, 19.6], [109.6, 18.2], [108.6, 19.2]],
  [[120.1, 23], [121.5, 25.3], [121.9, 24.8], [120.8, 22], [120.1, 23]],
  [[142, 46], [143.5, 49.3], [143, 54], [142.7, 54.4], [142, 51], [142, 46]],
  // Japan (Honshu, Hokkaido, Kyushu, Shikoku)
  [
    [130.9, 34], [132.5, 35.4], [135.5, 35.7], [136.8, 37.3], [138.5, 37.4], [140, 39.5], [140, 41.4],
    [141.5, 41.4], [142, 39.5], [141, 37], [140.9, 35.7], [139.8, 35], [138.8, 34.6], [137, 34.6],
    [135.2, 33.8], [133, 34.3], [130.9, 34],
  ],
  [[140, 41.5], [141, 43.2], [141.6, 45.4], [145.5, 44.3], [145.8, 43.3], [144, 42.9], [141.5, 42.5], [140, 41.5]],
  [[129.6, 33.3], [130.9, 33.9], [131.9, 33], [131.2, 31.4], [130.2, 31.2], [129.6, 33.3]],
  [[132.5, 33.5], [134.3, 34.2], [134.7, 33.8], [133, 32.8], [132.5, 33.5]],
  // Philippines (Luzon, Visayas, Mindanao, Palawan)
  [[120.6, 18.5], [122.2, 18.5], [122, 16.3], [121.6, 14.2], [124, 13], [123.3, 12.6], [120.9, 13.7], [120.1, 15], [120.4, 16.6], [120.6, 18.5]],
  [[122, 11.8], [124.3, 12.6], [125.7, 11.2], [125, 10], [123.5, 9.5], [122.4, 10], [122, 11.8]],
  [[122, 7], [123.5, 7.8], [125.4, 9.8], [126.5, 7.3], [126, 6], [125.3, 5.6], [124, 6.3], [122, 7]],
  [[117.2, 8.4], [119.5, 11.3], [119.7, 10.5], [118, 8.3], [117.2, 8.4]],
  // Indonesia (Sumatra, Java, Lesser Sunda, Timor, Borneo, Sulawesi) and New Guinea
  [
    [95.3, 5.6], [97.5, 5.2], [100.4, 2.3], [103.5, -0.8], [106, -3.2], [105.8, -5.8], [104.5, -5.9],
    [102, -4], [100.3, -1], [98.6, 1.7], [96, 4], [95.3, 5.6],
  ],
  [[105.2, -6.8], [106.5, -6], [108.5, -6.4], [111, -6.4], [112.7, -6.9], [114.5, -7.8], [114.4, -8.7], [111, -8.2], [108, -7.8], [105.2, -6.8]],
  [[115, -8.2], [119, -8.3], [123, -8.2], [122.8, -8.8], [119, -8.8], [115, -8.8], [115, -8.2]],
  [[123.5, -10.2], [125, -8.4], [127.3, -8.4], [124.2, -10.2], [123.5, -10.2]],
  [
    [109, 1.5], [110.5, 1.8], [113, 3.2], [115.5, 5.3], [117, 7], [119.2, 5.3], [118, 4.5], [117.9, 1],
    [117.6, 0.5], [116.5, -1.5], [116.4, -3.8], [114.5, -4], [111.8, -3.5], [110.2, -2.9], [109.1, -0.5],
    [109, 1.5],
  ],
  [
    [119.4, -5.5], [119.5, -3.4], [118.8, -2.5], [119.8, 0.1], [120.8, 1.3], [124.5, 1.6], [125.2, 1.5],
    [124.3, 0.4], [121, 0.5], [120.2, 0], [120.6, -1], [123.4, -0.9], [121.5, -1.9], [122.9, -4.5],
    [121.5, -4.7], [120.5, -2.9], [120.3, -5.5], [119.4, -5.5],
  ],
  [
    [131, -1], [134, -0.9], [135.5, -3.3], [138, -1.6], [141, -2.6], [144.5, -3.8], [147.5, -6],
    [147.8, -6.7], [146.5, -7.7], [148.2, -8.6], [150, -10.4], [147.2, -10], [144, -7.7], [142.6, -9.3],
    [141, -9.1], [139, -8.1], [138, -8.4], [137.6, -5.2], [135, -4.4], [133, -4], [132, -2.8], [131, -1],
  ],
  // Australia, Tasmania, New Zealand
  [
    [113.4, -22], [114, -26], [115, -30], [115, -34], [117.8, -35], [123, -33.8], [126, -32.3],
    [131, -31.5], [134, -32.8], [135.6, -34.8], [137.5, -33], [137.8, -35.6], [140, -37.8],
    [143.5, -38.8], [146.3, -39], [150, -37.5], [150.8, -34.5], [152.5, -32], [153.6, -28.5],
    [153, -25], [150.8, -22.5], [149, -20.5], [146.3, -18.8], [145.4, -15], [143.5, -14],
    [142.5, -10.7], [141.6, -12.8], [141.5, -16.5], [140.2, -17.7], [138, -16.2], [135.5, -15],
    [136.8, -12.3], [133, -11.3], [131, -12.2], [129.5, -15], [127, -14], [125, -15], [122.5, -17],
    [121.5, -19.5], [118, -20.4], [114.5, -21.8], [113.4, -22],
  ],
  [[144.6, -40.7], [148.3, -40.9], [148, -43.2], [146, -43.6], [144.6, -40.7]],
  [
    [172.7, -34.4], [174.8, -36.8], [176, -37.6], [178.5, -37.7], [177.9, -39.2], [176.9, -39.6],
    [175.2, -41.6], [174.6, -41.3], [175, -39.9], [173.8, -39.2], [174.6, -38], [172.7, -34.4],
  ],
  [
    [172.7, -40.5], [174.3, -41.7], [173.3, -43.2], [171.2, -44.5], [170.7, -45.9], [169, -46.7],
    [166.5, -46], [166.7, -45.2], [168.4, -44], [170.8, -42.7], [172.1, -41.2], [172.7, -40.5],
  ],
  // Antarctica
  [
    [-180, -90], [-180, -78], [-165, -78.5], [-150, -77], [-140, -75], [-125, -73.5], [-110, -74],
    [-100, -73], [-90, -72.5], [-80, -73], [-75, -71], [-68, -67], [-58, -63.3], [-62, -66],
    [-61, -70], [-60, -74], [-50, -77.5], [-35, -78], [-30, -76], [-20, -73], [-10, -71], [0, -70],
    [10, -70], [20, -70], [30, -69.5], [40, -68.5], [50, -67], [60, -67.5], [70, -68], [75, -69.5],
    [80, -67.5], [90, -66.5], [100, -66], [110, -66], [120, -66.8], [130, -66.2], [140, -66.8],
    [150, -68.5], [160, -70], [170, -71.5], [167, -77.5], [180, -78], [180, -90], [-180, -90],
  ],
];

const data = (() => {
  let seed = 8831;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  // Each zone follows its plate boundary as a [lon, lat] line through the forearc, traced so that
  // the overriding plate lies on the left of the direction of travel. Epicentres are spread along
  // the whole line (one per equal stretch), scattered `width` ground degrees across it, and in a
  // subduction zone the deeper ones lie up to `slab` degrees landward, above the dipping plate.
  // Depth and magnitude lean towards their low ends, as real catalogues do.
  const zones = [
    {
      name: "Japan-Kuril arc",
      path: [[141.2, 35], [142.3, 37.5], [142.8, 39.5], [144.5, 41.8], [147.5, 43.2], [151, 45.5], [154.5, 48], [157.5, 51], [160.5, 54]],
      count: 12, mag: [5.0, 7.2], depth: [10, 300], width: 0.7, slab: 3.5,
    },
    {
      name: "Aleutian-Alaska arc",
      path: [[-178.5, 51], [-173, 51.6], [-168, 52.8], [-163.5, 54], [-158.5, 55.3], [-154.5, 57], [-150.5, 59.3]],
      count: 8, mag: [5.0, 7.5], depth: [10, 150], width: 0.5, slab: 1.5,
    },
    {
      // Cascadia subduction, the San Andreas transform, the Gulf of California rift and the Middle America trench
      name: "Cascadia-Mexico coast",
      path: [
        [-127.5, 49.8], [-125.8, 47.5], [-125.2, 45], [-125, 42.5], [-124.6, 40.4], [-123.3, 38.6], [-122, 37],
        [-120.5, 35.7], [-118.6, 34.6], [-116.8, 33.9], [-115.6, 32.8], [-114.6, 31.5], [-113, 29], [-111, 26.8],
        [-109, 24.2], [-106.8, 21.7], [-105.4, 19.6], [-103.2, 18], [-100.5, 16.8], [-98, 15.9], [-95.5, 15.4],
        [-93, 14.6], [-91, 13.5], [-88.5, 12.5], [-86.5, 11.2],
      ],
      count: 12, mag: [5.0, 6.9], depth: [5, 60], width: 0.4, slab: 0.8,
    },
    {
      name: "Andes subduction",
      path: [
        [-80.6, -1], [-81.2, -5], [-79.8, -8], [-77.8, -11.5], [-76.2, -14], [-73.5, -16.4], [-71.2, -18.5],
        [-70.6, -21.5], [-70.8, -25], [-71.6, -30], [-72.4, -33.5], [-73.4, -36.8], [-73.9, -40],
      ],
      count: 12, mag: [5.0, 7.8], depth: [10, 600], width: 0.6, slab: 7,
    },
    {
      // Sunda trench, Banda arc, Molucca Sea and Philippine trench
      name: "Indonesia-Philippines arc",
      path: [
        [95, 5], [96.8, 2], [99.5, -1.8], [102.5, -4.8], [105.8, -7.2], [110, -8.6], [114, -9.3], [118, -9.6],
        [122, -9.7], [125.5, -8.8], [129, -7.8], [131.2, -6.3], [130.6, -4.2], [128, -3.4], [126.6, -1.6],
        [126.6, 1.2], [126.9, 4.5], [126.6, 8], [125.9, 11.2], [124.8, 13.8],
      ],
      count: 14, mag: [5.0, 7.6], depth: [10, 400], width: 0.6, slab: 3,
    },
    {
      name: "Tonga-Kermadec trench",
      path: [[-178.2, -35], [-177.2, -31], [-176, -27.5], [-174.6, -23.5], [-173.6, -20], [-173.2, -17], [-173.9, -15.6]],
      count: 8, mag: [5.0, 7.4], depth: [10, 600], width: 0.5, slab: 6,
    },
    {
      // Ionian islands, the Hellenic arc south of Crete, the eastern Aegean and the North Anatolian fault
      name: "Anatolia-Aegean",
      path: [
        [20.4, 39.3], [21.2, 37.4], [22.6, 36], [24.6, 35], [26.6, 35.2], [27.9, 36.6], [27, 38.4], [25.6, 39.6],
        [26.6, 40.5], [29.4, 40.75], [31.5, 40.85], [34, 40.95], [36.5, 40.4], [39.4, 39.75], [41.5, 39.3],
      ],
      count: 8, mag: [5.0, 6.8], depth: [5, 40], width: 0.45, slab: 0,
    },
    {
      name: "Himalayan front",
      path: [[73.6, 34.4], [75.6, 32.8], [77.8, 31], [80.2, 29.6], [82.6, 28.6], [85, 27.9], [87.6, 27.5], [90.5, 27.3], [93.2, 27.6], [95.4, 28.3]],
      count: 8, mag: [5.0, 7.2], depth: [5, 40], width: 0.4, slab: 0.8,
    },
  ];
  return zones.flatMap((zone) => {
    // Legs in ground degrees: longitude shrinks by the cosine of the leg's mean latitude
    const legs = zone.path.slice(1).map((b, i) => {
      const a = zone.path[i];
      const kx = Math.cos((((a[1] + b[1]) / 2) * Math.PI) / 180);
      const dx = (b[0] - a[0]) * kx;
      const dy = b[1] - a[1];
      return { a, b, kx, dx, dy, len: Math.hypot(dx, dy) };
    });
    const total = legs.reduce((sum, leg) => sum + leg.len, 0);
    return Array.from({ length: zone.count }, (_, k) => {
      let along = ((k + rand()) / zone.count) * total;
      let j = 0;
      while (j < legs.length - 1 && along > legs[j].len) {
        along -= legs[j].len;
        j += 1;
      }
      const leg = legs[j];
      const f = Math.min(1, along / leg.len);
      const depthShare = rand() ** 2;
      const depth = zone.depth[0] + depthShare * (zone.depth[1] - zone.depth[0]);
      const magnitude = zone.mag[0] + rand() ** 2 * (zone.mag[1] - zone.mag[0]);
      const across = zone.slab * depthShare + (rand() - 0.5) * 2 * zone.width;
      // The left-hand normal of the leg, (-dy, dx), points landward
      const lat = leg.a[1] + f * (leg.b[1] - leg.a[1]) + (leg.dx / leg.len) * across;
      const lon = leg.a[0] + f * (leg.b[0] - leg.a[0]) - ((leg.dy / leg.len) * across) / leg.kx;
      return {
        [LATITUDE]: Number(lat.toFixed(2)),
        [LONGITUDE]: Number((((lon + 540) % 360) - 180).toFixed(2)), // wrapped across the antimeridian
        [DEPTH]: Math.round(depth),
        [MAGNITUDE]: Number(magnitude.toFixed(1)),
        [ZONE]: zone.name,
      };
    });
  });
})();

// Plot: reads only data and the constants above
const points = data.map((d, i) => ({
  id: `p-${i}`,
  x: d[LONGITUDE],
  y: d[LATITUDE],
  z: d[DEPTH],
  sizeValue: d[MAGNITUDE],
}));
const depths = data.map((d) => d[DEPTH]);
const depthMin = Math.min(...depths);
const depthMax = Math.max(...depths);
const magnitudes = data.map((d) => d[MAGNITUDE]);
const magMin = Math.min(...magnitudes);
const magMax = Math.max(...magnitudes);
// Size legend: the smallest, middle and largest magnitude, at the radii the linear size map gives them
const sizeLegend = [magMin, (magMin + magMax) / 2, magMax].map((value) => ({
  value,
  radius: MARKER_RADIUS[0] + ((MARKER_RADIUS[1] - MARKER_RADIUS[0]) * (value - magMin)) / (magMax - magMin || 1),
}));
// The size glyphs take the middle of the depth ramp, so they share the markers' fill, edge and alpha
const midRamp = `rgb(${[1, 3, 5]
  .map((i) => (parseInt(t.seq[0].slice(i, i + 2), 16) + parseInt(t.seq[1].slice(i, i + 2), 16)) / 2)
  .join(", ")})`;

const lonTicks = Array.from(
  { length: (WORLD.lonMax - WORLD.lonMin) / GRATICULE_LON_STEP + 1 },
  (_, k) => WORLD.lonMin + k * GRATICULE_LON_STEP,
);
const latTicks = Array.from(
  { length: (WORLD.latMax - WORLD.latMin) / GRATICULE_LAT_STEP + 1 },
  (_, k) => WORLD.latMin + k * GRATICULE_LAT_STEP,
);

const TITLE = "scatter-map-geographic · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} epicentres · colour: ${DEPTH} · size: ${MAGNITUDE} · equirectangular projection`;
const HEADER_HEIGHT = 70;
const LEGEND_HEIGHT = 64;
const X_AXIS_HEIGHT = 56;
const Y_AXIS_WIDTH = 72;
const chartWidth = window.ANYPLOT_SIZE.width;
const chartHeight = window.ANYPLOT_SIZE.height - HEADER_HEIGHT - LEGEND_HEIGHT;

// The axes run a padded share past the globe, so a marker centred on the antimeridian or a pole stays
// clear of the axis lines and their tick labels
const lonPad = (WORLD.lonMax - WORLD.lonMin) * PAD_SHARE;
const latPad = (WORLD.latMax - WORLD.latMin) * PAD_SHARE;
const extent = {
  lonMin: WORLD.lonMin - lonPad,
  lonMax: WORLD.lonMax + lonPad,
  latMin: WORLD.latMin - latPad,
  latMax: WORLD.latMax + latPad,
};

// Equirectangular: px per degree of latitude = px per degree of longitude / cos(mean latitude)
const meanLatitude = ((extent.latMin + extent.latMax) / 2) * (Math.PI / 180);
const mapAspect = ((extent.lonMax - extent.lonMin) * Math.cos(meanLatitude)) / (extent.latMax - extent.latMin);
const mapHeight = Math.min(chartHeight - X_AXIS_HEIGHT - 28, (chartWidth - Y_AXIS_WIDTH - 48) / mapAspect);
const mapWidth = mapHeight * mapAspect;
const marginX = (chartWidth - Y_AXIS_WIDTH - mapWidth) / 2;
const marginY = (chartHeight - X_AXIS_HEIGHT - mapHeight) / 2;

function Basemap() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {LAND_OUTLINES.map((ring, k) => (
        <path
          key={`land-${k}`}
          d={`M ${ring.map(([lon, lat]) => `${xScale(lon)},${yScale(lat)}`).join(" L ")} Z`}
          fill={t.grid}
          stroke={t.inkSoft}
          strokeOpacity={0.45}
          strokeWidth={1}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
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
      <ChartsDataProvider
        width={chartWidth}
        height={chartHeight}
        margin={{ top: marginY, bottom: marginY, left: marginX, right: marginX }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "epicentres",
            label: ZONE,
            data: points,
            markerSize: MARKER_RADIUS[0],
            colorAxisId: "depth",
            sizeAxisId: "magnitude",
            valueFormatter: (v, { dataIndex }) =>
              `${data[dataIndex][ZONE]} · ${MAGNITUDE} ${data[dataIndex][MAGNITUDE]} · ${DEPTH} ${data[dataIndex][DEPTH]}`,
          },
        ]}
        xAxis={[
          {
            id: "lon",
            scaleType: "linear",
            min: extent.lonMin,
            max: extent.lonMax,
            label: LONGITUDE,
            height: X_AXIS_HEIGHT,
            tickInterval: lonTicks,
            valueFormatter: (v: number) => (v === 0 ? "0°" : `${Math.abs(v)}°${v > 0 ? "E" : "W"}`),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "lat",
            scaleType: "linear",
            min: extent.latMin,
            max: extent.latMax,
            label: LATITUDE,
            width: Y_AXIS_WIDTH,
            tickInterval: latTicks,
            valueFormatter: (v: number) => (v === 0 ? "0°" : `${Math.abs(v)}°${v > 0 ? "N" : "S"}`),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            id: "depth",
            min: depthMin,
            max: depthMax,
            colorMap: { type: "continuous", min: depthMin, max: depthMax, color: [t.seq[0], t.seq[1]] },
          },
          {
            id: "magnitude",
            sizeMap: { type: "continuous", min: magMin, max: magMax, size: MARKER_RADIUS, interpolator: "linear" },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "bottom", horizontal: "center" }} legendDirection="horizontal">
          <div
            style={{
              gridArea: "legend",
              height: LEGEND_HEIGHT,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 72,
              color: t.inkSoft,
              fontSize: 15,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ color: t.ink, fontSize: 16 }}>{DEPTH}</span>
              <ContinuousColorLegend
                axisDirection="z"
                axisId="depth"
                direction="horizontal"
                thickness={14}
                labelPosition="end"
                sx={{ width: 300, color: t.inkSoft, fontSize: 14 }}
              />
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ color: t.ink, fontSize: 16 }}>{MAGNITUDE}</span>
              {sizeLegend.map(({ value, radius }) => (
                <span key={`size-${value}`} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <svg width={2 * MARKER_RADIUS[1] + 2} height={2 * MARKER_RADIUS[1] + 2}>
                    <circle
                      cx={MARKER_RADIUS[1] + 1}
                      cy={MARKER_RADIUS[1] + 1}
                      r={radius}
                      fill={midRamp}
                      fillOpacity={POINT_OPACITY}
                      stroke={t.pageBg}
                      strokeWidth={1}
                    />
                  </svg>
                  {value.toFixed(1)}
                </span>
              ))}
            </div>
          </div>
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY, stroke: t.pageBg, strokeWidth: 1 },
            }}
          >
            <Basemap />
            <ChartsGrid horizontal vertical />
            <ChartsReferenceLine
              x={0}
              label="Prime meridian"
              labelAlign="end"
              lineStyle={{ stroke: t.inkSoft, strokeOpacity: 0.7, strokeDasharray: "6 4", strokeWidth: 1.5 }}
              labelStyle={{ fontSize: 14, fill: t.inkSoft }}
            />
            <ChartsReferenceLine
              y={0}
              label="Equator"
              labelAlign="end"
              lineStyle={{ stroke: t.inkSoft, strokeOpacity: 0.7, strokeDasharray: "6 4", strokeWidth: 1.5 }}
              labelStyle={{ fontSize: 14, fill: t.inkSoft }}
            />
            <ChartsXAxis />
            <ChartsYAxis />
            <ScatterPlot />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
