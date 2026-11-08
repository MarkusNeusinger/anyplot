// anyplot.ai
// bubble-map-geographic: Bubble Map with Sized Geographic Markers
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-01
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MIN_RADIUS = 9; // px floor so the smallest values stay visible
const MAX_RADIUS = 46; // px radius of the largest value
const PAD_SHARE = 0.1; // map padding as a share of the data's longitude and latitude span
const BUBBLE_OPACITY = 0.6;

// Columns: set these to your data's column names
const CITY = "City"; // role: label
const LAT = "Latitude"; // role: latitude
const LON = "Longitude"; // role: longitude
const POPULATION = "Metro population (millions)"; // role: value
const REGION = "World region"; // role: category

// Data: replace this block with your own records, one object per row
// Approximate 2023 metro-area population of 20 major world cities.
const data = [
  { [CITY]: "Tokyo", [LON]: 139.7, [LAT]: 35.7, [POPULATION]: 37.4, [REGION]: "Asia-Pacific" },
  { [CITY]: "Delhi", [LON]: 77.2, [LAT]: 28.6, [POPULATION]: 32.9, [REGION]: "Asia-Pacific" },
  { [CITY]: "Shanghai", [LON]: 121.5, [LAT]: 31.2, [POPULATION]: 29.2, [REGION]: "Asia-Pacific" },
  { [CITY]: "Jakarta", [LON]: 106.8, [LAT]: -6.2, [POPULATION]: 33.4, [REGION]: "Asia-Pacific" },
  { [CITY]: "Sydney", [LON]: 151.2, [LAT]: -33.9, [POPULATION]: 5.3, [REGION]: "Asia-Pacific" },
  { [CITY]: "Moscow", [LON]: 37.6, [LAT]: 55.8, [POPULATION]: 12.6, [REGION]: "Europe" },
  { [CITY]: "Istanbul", [LON]: 29.0, [LAT]: 41.0, [POPULATION]: 15.5, [REGION]: "Europe" },
  { [CITY]: "Paris", [LON]: 2.35, [LAT]: 48.85, [POPULATION]: 11.1, [REGION]: "Europe" },
  { [CITY]: "London", [LON]: -0.1, [LAT]: 51.5, [POPULATION]: 9.6, [REGION]: "Europe" },
  { [CITY]: "Madrid", [LON]: -3.7, [LAT]: 40.4, [POPULATION]: 6.7, [REGION]: "Europe" },
  { [CITY]: "Cairo", [LON]: 31.2, [LAT]: 30.0, [POPULATION]: 21.3, [REGION]: "Africa" },
  { [CITY]: "Kinshasa", [LON]: 15.3, [LAT]: -4.3, [POPULATION]: 15.6, [REGION]: "Africa" },
  { [CITY]: "Lagos", [LON]: 3.4, [LAT]: 6.5, [POPULATION]: 15.4, [REGION]: "Africa" },
  { [CITY]: "Johannesburg", [LON]: 28.0, [LAT]: -26.2, [POPULATION]: 6.2, [REGION]: "Africa" },
  { [CITY]: "Nairobi", [LON]: 36.8, [LAT]: -1.3, [POPULATION]: 4.9, [REGION]: "Africa" },
  { [CITY]: "Sao Paulo", [LON]: -46.6, [LAT]: -23.5, [POPULATION]: 22.6, [REGION]: "Americas" },
  { [CITY]: "Mexico City", [LON]: -99.1, [LAT]: 19.4, [POPULATION]: 22.3, [REGION]: "Americas" },
  { [CITY]: "New York", [LON]: -74.0, [LAT]: 40.7, [POPULATION]: 18.9, [REGION]: "Americas" },
  { [CITY]: "Buenos Aires", [LON]: -58.4, [LAT]: -34.6, [POPULATION]: 15.4, [REGION]: "Americas" },
  { [CITY]: "Bogota", [LON]: -74.1, [LAT]: 4.7, [POPULATION]: 11.2, [REGION]: "Americas" },
];

// Basemap geometry: simplified coastlines as [longitude, latitude] rings
const LAND: { name: string; ring: [number, number][] }[] = [
  { name: "North America", ring: [
    [-166, 68.5], [-163, 70], [-156, 71.3], [-148, 70.3], [-141, 69.6], [-133, 69.5], [-128, 70], [-115, 68.5],
    [-108, 68], [-98, 67.8], [-94, 69], [-90, 68.5], [-85, 69.5], [-82, 67], [-86, 64], [-93, 61.5], [-94, 58.8],
    [-90, 57], [-82, 55], [-80, 51.5], [-79, 55], [-77, 60], [-78, 62.5], [-72, 62], [-65, 60], [-62, 57], [-58, 54],
    [-56, 52], [-60, 50], [-65, 49], [-64, 47], [-61, 45.5], [-66, 44], [-70, 43.5], [-70, 41.8], [-74, 40.5],
    [-76, 38], [-76, 35], [-78.5, 33.8], [-81, 31.5], [-80, 27], [-80.5, 25.2], [-82, 26.5], [-82.8, 28], [-84, 30],
    [-86, 30.4], [-89, 30.2], [-90, 29], [-94, 29.7], [-97.2, 27.5], [-97.5, 24], [-97.8, 22], [-96, 19],
    [-94.5, 18.2], [-91, 18.7], [-90.5, 21], [-87, 21.5], [-87.5, 18.5], [-88.5, 16], [-86, 15.8], [-83.3, 15],
    [-83.5, 11], [-81.5, 9], [-79.5, 9.5], [-77.4, 8.6], [-77.9, 7.2], [-80, 7.3], [-82.5, 8.2], [-85.7, 10],
    [-86, 11.5], [-87.5, 13], [-91.5, 14], [-94.5, 16], [-96.5, 15.7], [-99.7, 16.8], [-103.5, 18.3], [-105.5, 20.5],
    [-105.3, 22.5], [-108, 25.5], [-112.7, 31.5], [-114.8, 31.8], [-112.5, 28.5], [-110, 24], [-109.5, 23],
    [-112, 24.8], [-114.2, 28], [-115.8, 30.4], [-117.1, 32.5], [-118.5, 34], [-120.6, 34.6], [-122.5, 37.7],
    [-124, 40.4], [-124.2, 43], [-124, 46.2], [-124.7, 48.4], [-123, 49], [-127.5, 50.5], [-130, 54.5], [-133, 57.5],
    [-137, 58.8], [-140, 59.8], [-146, 60.8], [-150, 59.5], [-152, 60.5], [-154, 58.5], [-158, 56.7], [-162, 55],
    [-164.5, 54.5], [-158, 58.7], [-162, 59.8], [-165, 60.5], [-164.8, 63], [-161, 64.5], [-166, 65.3], [-168, 65.6],
    [-164, 67],
  ] },
  { name: "Baffin Island", ring: [
    [-62, 66.5], [-66, 68.5], [-70, 70.5], [-78, 72.8], [-88, 73.5], [-84, 70], [-80, 69], [-73, 68], [-77, 65.5],
    [-73, 64], [-66, 62], [-64, 64],
  ] },
  { name: "Victoria Island", ring: [
    [-118, 72.8], [-110, 73], [-102, 72.5], [-101, 69.5], [-108, 68.8], [-117, 69.5],
  ] },
  { name: "Ellesmere Island", ring: [
    [-90, 76.5], [-78, 76.5], [-74, 79], [-62, 82], [-70, 83], [-88, 81.5], [-92, 79.5],
  ] },
  { name: "Greenland", ring: [
    [-45, 60], [-43, 60], [-38, 65.5], [-32, 68], [-22, 70.5], [-21.5, 74], [-18, 77], [-19, 80], [-12, 81.5],
    [-20, 82.5], [-32, 83.5], [-45, 82.7], [-60, 82], [-65, 80.5], [-73, 78.5], [-66, 76], [-58, 75.8], [-55, 72],
    [-53, 69], [-51.5, 64], [-48, 61],
  ] },
  { name: "Iceland", ring: [
    [-24, 65.5], [-22, 66.4], [-16, 66.5], [-13.6, 65.2], [-15, 64.3], [-18.5, 63.4], [-22.5, 63.8],
  ] },
  { name: "Cuba", ring: [
    [-85, 21.9], [-82, 23.2], [-77.2, 22.2], [-74.2, 20.3], [-77.7, 19.9], [-80.5, 21.7], [-83.5, 22],
  ] },
  { name: "Hispaniola", ring: [[-74.4, 18.5], [-72.7, 19.9], [-69.6, 19.7], [-68.4, 18.6], [-71.5, 17.6]] },
  { name: "South America", ring: [
    [-77.4, 8.6], [-76, 9.5], [-75.5, 10.8], [-73, 11.5], [-71.5, 12.4], [-71.5, 10.8], [-68, 10.5], [-64, 10.6],
    [-61.8, 10.7], [-60.5, 8.5], [-57, 6], [-54, 5.8], [-51.5, 4.5], [-50, 1.8], [-48.5, -1.2], [-44.5, -2.5],
    [-40, -3], [-35.2, -5.5], [-35, -9], [-38.5, -13], [-39, -17.5], [-40.8, -22], [-44, -23], [-48.5, -26],
    [-48.8, -28.5], [-51, -31], [-53.5, -34], [-56, -34.9], [-57.5, -36.2], [-57.5, -38.2], [-62.2, -38.8],
    [-62.3, -40.6], [-65, -41], [-64.5, -42.5], [-67.5, -46], [-65.8, -47.8], [-69, -51], [-68.5, -52.4],
    [-68.6, -54.8], [-67.5, -54.8], [-71, -55], [-74.5, -52.5], [-75.5, -48], [-74, -44], [-73.5, -40], [-73.5, -37],
    [-71.6, -33], [-71.4, -28], [-70.4, -23.5], [-70.3, -18.4], [-71.4, -17.5], [-76.2, -14], [-78.5, -10],
    [-79.9, -7], [-81.2, -5.5], [-80.4, -3.4], [-80.9, -1], [-80, 0.8], [-79, 1.7], [-77.8, 4], [-77.4, 7],
  ] },
  { name: "Eurasia", ring: [
    [-5.6, 36], [-6.4, 36.8], [-7.4, 37.2], [-8.9, 37], [-8.8, 38.7], [-9.5, 39.4], [-8.7, 41.2], [-8.9, 42.6],
    [-9.3, 43], [-7.7, 43.7], [-4.5, 43.4], [-1.8, 43.4], [-1.2, 44.6], [-1.2, 46.2], [-2.3, 47.2], [-4.6, 48],
    [-3, 48.8], [-1.6, 48.6], [-1.4, 49.7], [0.2, 49.5], [1.6, 50.2], [2.5, 51.1], [3.6, 51.5], [4.6, 52.9],
    [5.9, 53.4], [8, 53.6], [8.6, 54.9], [8.1, 55.5], [8.2, 56.8], [10.6, 57.7], [10.3, 56.5], [10.9, 56.3],
    [9.9, 55], [10.9, 54], [12.5, 54.4], [14.2, 53.9], [16.5, 54.5], [18.6, 54.7], [19.6, 54.4], [21.1, 55.2],
    [21, 56.8], [21.6, 57.4], [23.4, 59.1], [24, 59.3], [28, 59.5], [29.9, 59.9], [28, 60.5], [25, 60.2],
    [22.9, 59.8], [21.4, 60.8], [21.6, 63.2], [23.5, 64.6], [25.3, 65.1], [24.6, 65.8], [22.3, 65.8], [21.2, 64.6],
    [19, 63.4], [17.4, 62.4], [17.2, 61], [18.6, 60.2], [18.9, 59.4], [17, 57.5], [16.4, 56.5], [14.7, 56],
    [13, 55.4], [12.8, 56.6], [11.8, 58.1], [10.9, 59], [10.6, 59.9], [9.8, 59], [8.1, 58.1], [6.6, 58.1],
    [5.6, 58.9], [5, 60.5], [5.1, 61.9], [6.5, 62.7], [9, 63.7], [10.8, 64.8], [12.6, 66.1], [14.2, 67.5],
    [16, 68.5], [18.8, 69.8], [22.5, 70.6], [25.8, 71.1], [28.5, 70.9], [31, 70], [33, 69.3], [36.5, 69], [41, 67],
    [38, 66], [35, 64.5], [37.5, 63.8], [40.5, 64.6], [44, 66.3], [44.2, 68.3], [46.5, 68], [53, 68.6], [59, 68.6],
    [61, 69.8], [66, 69.3], [68.5, 71], [70.5, 73.2], [73, 71.5], [73.5, 68.5], [76.5, 72], [80.5, 73.6],
    [86.5, 74.5], [87.5, 75.5], [95, 76.1], [104, 77.7], [108, 76.7], [113, 75.9], [113.5, 73.5], [119, 73],
    [127, 73.5], [129, 72], [132.5, 71.6], [139, 72.3], [146, 72.3], [152, 70.9], [160, 70], [161.5, 69.4],
    [167, 69.7], [170.5, 70.1], [176, 69.6], [179.9, 68.9], [179.9, 65], [177, 64.7], [174.5, 61.8], [170.5, 60],
    [166, 60.3], [163.5, 59.8], [162, 56.2], [160, 54], [158.3, 53], [156.7, 51], [156, 52.8], [155.5, 55.5],
    [156.8, 57.8], [161, 60.5], [159.5, 61.7], [154, 59.3], [151, 59.2], [143, 59.4], [140, 58], [137, 54],
    [140.5, 53], [141.3, 51.5], [140.5, 50], [140, 48], [138.5, 46.5], [135.5, 43.8], [132, 43.1], [130.7, 42.3],
    [129.7, 41], [128, 39.5], [129.4, 37.5], [129.4, 35.4], [127.5, 34.6], [126.3, 34.7], [126.6, 37.2],
    [125.2, 37.7], [125.2, 39.5], [124.4, 40], [122.2, 40.5], [121, 40.8], [119, 39.2], [118, 39.2], [117.7, 38.5],
    [118.9, 37.3], [120.5, 37.8], [122.5, 37.4], [120.5, 36], [119.4, 35], [120.3, 34.3], [121.8, 31.8],
    [121.5, 30.8], [122, 29.9], [120.5, 27.2], [119.5, 25.6], [117.5, 23.6], [114.2, 22.3], [111, 21.5],
    [110.3, 20.3], [109.7, 21.6], [108, 21.6], [106.7, 20.5], [105.8, 19], [106.5, 17.6], [108.8, 15.2],
    [109.3, 12.5], [109, 11.4], [106.8, 10.4], [104.8, 8.6], [105, 10], [104.4, 10.4], [103, 11.6], [101, 12.7],
    [100, 13.5], [99.2, 10.5], [100.4, 8], [101.3, 6.9], [103.4, 4], [104.2, 1.4], [103.5, 1.3], [101.3, 2.8],
    [100.3, 5.5], [98.3, 8.2], [98.5, 10.5], [97.8, 14.9], [97.6, 16.5], [95.3, 15.8], [94.3, 16.4], [94.4, 19],
    [92.3, 20.7], [91.8, 22.4], [90.3, 21.9], [88.5, 21.7], [86.9, 20.8], [86, 19.9], [84.2, 18.3], [82.3, 16.6],
    [80.3, 15.5], [80.1, 13.3], [79.8, 11], [79.3, 10.3], [78.2, 8.9], [77.5, 8.1], [76.4, 9.5], [75.6, 11.6],
    [74.4, 14.6], [73.4, 16.5], [72.8, 19.2], [72.6, 21.3], [70.4, 20.9], [69, 22.3], [68.4, 23.6], [67.3, 24.7],
    [66.7, 25.4], [64, 25.3], [61.5, 25.1], [58.8, 25.5], [57.3, 26.9], [56.4, 27.1], [54.7, 26.5], [51.5, 27.9],
    [50.2, 29.9], [48.5, 30], [48, 29.2], [48.5, 28], [49.6, 26.8], [50.2, 26], [50.8, 24.8], [51.6, 24.2], [52, 24],
    [54, 24.2], [55.8, 25.3], [56.3, 26.3], [56.4, 24.9], [57.8, 23.7], [59.8, 22.4], [58.5, 20.5], [57.8, 18.9],
    [55.4, 17.7], [52.2, 15.6], [48.8, 14], [45, 12.8], [43.5, 12.7], [42.7, 15.6], [41.2, 19], [39.2, 21.5],
    [38.5, 23.6], [36.5, 26], [35, 28.1], [34.9, 29.5], [34.3, 28], [32.6, 29.9], [32.3, 31.2], [34.2, 31.3],
    [35, 32.8], [35.9, 34.6], [36.1, 36.8], [34.6, 36.8], [32.5, 36.1], [30.5, 36.4], [28, 36.7], [27.3, 37.5],
    [26.3, 38.3], [26.6, 39.5], [26.2, 40.1], [29, 41.1], [31.5, 41.2], [34, 42], [35.2, 42], [37.5, 41], [40, 41],
    [41.6, 41.5], [41.5, 42.6], [39.5, 44], [37.4, 44.8], [38.3, 47.2], [36.6, 45.3], [35, 45], [33.5, 44.5],
    [32.5, 45.4], [33.6, 46.1], [31.7, 46.6], [30.7, 46.4], [29.6, 45.4], [28.7, 44.4], [28, 43.3], [27.9, 42],
    [28.9, 41.3], [28, 41], [26.2, 40.6], [24, 40.9], [23.5, 40.2], [22.6, 40.5], [22.8, 39.3], [23.3, 38.2],
    [24, 38], [22.9, 37], [22.6, 36.4], [21.7, 36.8], [21.1, 37.8], [21.4, 38.5], [20.7, 39.1], [20, 39.7],
    [19.4, 40.3], [19.5, 41.8], [18.5, 42.4], [17, 43.2], [15.9, 43.6], [15.2, 44.3], [14.3, 45.3], [13.6, 45.7],
    [12.4, 45.4], [12.3, 44.6], [13.6, 43.5], [14.6, 42.1], [16, 41.4], [18.5, 40.1], [17, 39.4], [16.6, 38.4],
    [16.1, 37.9], [15.7, 38.2], [15.6, 40.1], [14.4, 40.6], [12.6, 41.4], [11.2, 42.4], [10.5, 43], [10.2, 43.9],
    [8.8, 44.4], [7.6, 43.8], [6.2, 43.1], [4.6, 43.4], [3.1, 43.1], [3.2, 42], [2.1, 41.2], [0.8, 41], [0, 39.9],
    [-0.3, 39.4], [0.2, 38.7], [-0.7, 37.6], [-2.1, 36.7], [-4.4, 36.7],
  ] },
  { name: "Great Britain", ring: [
    [-5.7, 50.1], [-3, 50.7], [1.4, 51.2], [1.7, 52.7], [0.3, 53.4], [-0.1, 54.5], [-1.6, 55.6], [-2.1, 57.1],
    [-1.8, 57.6], [-4, 57.6], [-3.1, 58.6], [-5, 58.6], [-6.2, 56.8], [-5.6, 55.3], [-4.9, 54.8], [-3.2, 54.6],
    [-3, 53.4], [-4.6, 53.3], [-4, 52.3], [-5.1, 51.8], [-3.2, 51.4],
  ] },
  { name: "Ireland", ring: [
    [-6, 52.2], [-6.2, 53.9], [-5.8, 54.6], [-7.3, 55.3], [-8.5, 54.4], [-10, 54.2], [-9.6, 53.3], [-10.3, 52],
    [-9, 51.6], [-7.5, 52],
  ] },
  { name: "Novaya Zemlya", ring: [[52, 71.5], [56, 73], [60, 75.5], [68, 76.8], [64, 75.2], [57, 72.5], [55, 70.6]] },
  { name: "Africa", ring: [
    [32.3, 31.2], [31, 31.6], [29.8, 31.1], [27.3, 31.4], [25.1, 31.6], [23, 32.6], [21, 32.8], [20, 30.8],
    [18.5, 30.4], [15.5, 31.6], [13, 32.9], [11.1, 33.3], [10.1, 34.3], [11, 35.6], [10.2, 37.2], [8.6, 36.9],
    [5, 36.8], [1, 36.5], [-1.3, 35.3], [-3, 35.3], [-5.9, 35.8], [-6.5, 34.2], [-9, 32.6], [-9.8, 30.6],
    [-11.5, 28.2], [-13.2, 27.6], [-14.5, 26.2], [-16, 23.8], [-17.1, 21], [-16, 19.5], [-16.5, 16.6], [-17.5, 14.7],
    [-16.7, 13.1], [-16.7, 12.3], [-15.1, 11.2], [-13.7, 9.8], [-13.2, 8.9], [-12.2, 7.4], [-10.5, 6.2], [-7.6, 4.4],
    [-5, 5.1], [-2, 4.8], [1, 6.1], [2.7, 6.4], [4.4, 6.3], [5.9, 4.3], [7.1, 4.4], [8.5, 4.6], [9.6, 3.6],
    [9.4, 2.2], [9.6, 1], [9.3, -0.8], [10.1, -2.8], [11.8, -4.4], [12.3, -6.1], [13.4, -8.6], [13.6, -11.3],
    [12, -15], [11.8, -17.3], [13.4, -21], [14.5, -22.9], [15.2, -26.6], [16.5, -28.6], [17.9, -31.5], [18.4, -34],
    [20, -34.8], [22.5, -34], [25.6, -34], [27.8, -33.2], [30, -31.3], [32.6, -28.6], [32.9, -26], [35.4, -24.1],
    [35.5, -21.3], [34.7, -19.8], [36.9, -17.6], [40.6, -14], [40.5, -10.5], [39, -6.5], [39.8, -3.8], [41, -2],
    [43.5, 0.5], [46, 2], [48, 4.5], [49.8, 7.5], [51.2, 10.5], [51.3, 11.8], [49, 11.3], [45.5, 10.6], [43.4, 11.5],
    [42.8, 12.5], [41.2, 14], [39.3, 15.9], [38.5, 18], [37.3, 22], [35.8, 23.9], [35.1, 24.8], [33.9, 27],
    [32.6, 29.9],
  ] },
  { name: "Madagascar", ring: [
    [49.3, -12], [50.3, -15.4], [49.9, -17], [48.4, -21.5], [47.1, -24.9], [45.2, -25.6], [43.7, -23.5],
    [43.3, -21.5], [44.4, -19], [44, -17], [46.3, -15.8], [48, -13.6],
  ] },
  { name: "Sri Lanka", ring: [[79.9, 6], [79.7, 8.2], [80.1, 9.8], [81.2, 8.5], [81.9, 7.2], [80.6, 5.9]] },
  { name: "Taiwan", ring: [[120.1, 23], [121, 25], [121.9, 25], [121.5, 23], [120.8, 21.9]] },
  { name: "Honshu, Kyushu & Shikoku", ring: [
    [130.2, 31.3], [131.4, 31.4], [132, 33], [133, 33.3], [134.7, 33.8], [135.8, 33.5], [136.9, 34.3], [138.8, 34.6],
    [139.8, 35], [140.9, 36.3], [141, 38.3], [142, 39.6], [141.5, 40.5], [141.4, 41.4], [140, 40.8], [139.9, 39.5],
    [139.5, 38.2], [138.5, 37.4], [137, 36.8], [136, 35.7], [133, 35.5], [131.5, 34.6], [130.9, 34], [129.7, 33.2],
  ] },
  { name: "Hokkaido", ring: [
    [140, 41.5], [141.3, 42.4], [143.3, 42], [145.5, 43.3], [144.5, 44], [142, 45.5], [141.6, 44.3], [140.3, 43.2],
  ] },
  { name: "Sakhalin", ring: [
    [142, 46], [143.5, 46.8], [142.7, 49.5], [143.2, 51.5], [142.5, 54.2], [141.7, 52], [142.2, 49],
  ] },
  { name: "Luzon", ring: [
    [120.6, 18.5], [122.2, 18.5], [121.5, 15.5], [124.2, 12.6], [123.2, 13.5], [120.6, 14.2], [119.8, 16.3],
  ] },
  { name: "Mindanao", ring: [[122, 7], [123.6, 8.6], [125.4, 9.8], [126.6, 7.3], [125.5, 5.6], [124, 6.4]] },
  { name: "Borneo", ring: [
    [109, 1.5], [109.6, 2], [111.3, 2.7], [113, 3.2], [115.4, 5], [116.8, 7], [119.3, 5.4], [118, 4.3], [117.6, 0.8],
    [116.5, -1.5], [116.4, -3.5], [114.5, -4], [111.7, -3], [110.2, -2.9], [109.5, -0.5],
  ] },
  { name: "Sumatra", ring: [
    [95.3, 5.6], [97.5, 5.2], [100.4, 2.3], [103.7, -0.8], [106, -3.2], [105.8, -5.8], [104.5, -5.9], [102.3, -4],
    [100.4, -0.8], [98.6, 1.8],
  ] },
  { name: "Java", ring: [
    [105.2, -6.8], [106.5, -6], [108.5, -6.4], [110.4, -6.9], [112.6, -6.9], [114.4, -7.8], [112, -8.4],
    [108.8, -7.8], [106.4, -7.4],
  ] },
  { name: "Sulawesi", ring: [
    [119.4, -5.5], [118.8, -2.8], [119.9, 0.6], [124.9, 1.5], [121, 0.3], [123.3, -0.9], [121.3, -1.9],
    [122.8, -4.6], [121, -4.8], [120.4, -5.6],
  ] },
  { name: "New Guinea", ring: [
    [131, -1.2], [134, -0.9], [135, -3.3], [138, -1.6], [141, -2.6], [144.5, -3.8], [146, -5.5], [147.6, -6.1],
    [147.2, -7.4], [148.4, -8.6], [150, -10.4], [147, -10.1], [144, -7.6], [142.6, -9.3], [141, -9.1], [139, -8.1],
    [138, -8.4], [137.6, -5.2], [134.4, -3.9], [132, -2.8],
  ] },
  { name: "Australia", ring: [
    [113.4, -22], [114.2, -21.8], [116.7, -20.6], [119, -20], [121, -19.5], [122.3, -17.2], [124, -16.3],
    [125.8, -14.2], [127.8, -14.3], [129.6, -15], [130.4, -12.7], [132.6, -12.1], [136.7, -12.2], [135.9, -15.1],
    [139.2, -17.4], [140.8, -17.4], [141.6, -15], [141.5, -12.6], [142.5, -10.7], [143.5, -12.8], [145.3, -14.9],
    [146.3, -19], [149.3, -21.7], [150.9, -23.5], [153.1, -25.6], [153.6, -28.8], [153, -31], [151.3, -33.9],
    [150.1, -36.3], [149.9, -37.6], [147, -38.6], [144.6, -38.2], [143.5, -38.8], [140.6, -38], [139.6, -36.9],
    [138.1, -35.4], [138.5, -34.4], [137.8, -33], [137.4, -34.5], [136, -34.9], [134.2, -32.8], [131.1, -31.5],
    [128, -32.2], [124, -33], [121.2, -33.9], [118, -35.1], [115, -34.3], [115.6, -31.6], [114.9, -29.1],
    [113.4, -26.3], [114, -24.9],
  ] },
  { name: "Tasmania", ring: [[144.6, -40.7], [148.3, -40.9], [148, -43.2], [146.6, -43.6], [145.2, -42.2]] },
  { name: "New Zealand North Island", ring: [
    [172.7, -34.4], [174.6, -35.8], [175.9, -37.5], [178.5, -37.7], [177.9, -39.2], [176.9, -39.6], [175.3, -41.6],
    [174.6, -41.2], [175, -39.9], [173.8, -39.3], [174.6, -38], [174.3, -36.6],
  ] },
  { name: "New Zealand South Island", ring: [
    [172.6, -40.5], [174.2, -41.6], [173.3, -43], [172.7, -43.8], [171.2, -44.4], [170.6, -45.9], [169, -46.6],
    [166.5, -46], [168.4, -44], [170.6, -42.9], [172.1, -41],
  ] },
];

// Plot: reads only data, the geometry and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const TITLE_H = 80;
const LEGEND_H = 44; // the region legend above the map adds its own height
const SIZE_LEGEND_W = 220;
const X_AXIS_H = 56;
const Y_AXIS_W = 72;
const MARGIN = { top: 12, right: 24, bottom: 12, left: 16 };
const CHART_W = W - SIZE_LEGEND_W;
const CHART_H = H - TITLE_H - LEGEND_H;
const DRAW_W = CHART_W - MARGIN.left - MARGIN.right - Y_AXIS_W;
const DRAW_H = CHART_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;

// Equirectangular view at the data's mean latitude: px per degree of latitude is
// px per degree of longitude divided by cos(mean latitude); the padded data extent
// grows along one axis until it fills the drawing area
const lons = data.map((d) => d[LON]);
const lats = data.map((d) => d[LAT]);
const lonMin = Math.min(...lons);
const lonMax = Math.max(...lons);
const latMin = Math.min(...lats);
const latMax = Math.max(...lats);
const cosMeanLat = Math.cos(((lats.reduce((s, v) => s + v, 0) / lats.length) * Math.PI) / 180);
const lonSpan0 = (lonMax - lonMin) * (1 + 2 * PAD_SHARE);
const latSpan0 = (latMax - latMin) * (1 + 2 * PAD_SHARE);
const latSpanFill = (DRAW_H * cosMeanLat * lonSpan0) / DRAW_W;
const lonSpan = latSpanFill >= latSpan0 ? lonSpan0 : (latSpan0 * DRAW_W) / (DRAW_H * cosMeanLat);
const latSpan = latSpanFill >= latSpan0 ? latSpanFill : latSpan0;
const lonCenter = (lonMin + lonMax) / 2;
const latCenter = (latMin + latMax) / 2;

// Bubble area is proportional to the value: radius grows with the square root of its share of the maximum
const maxValue = Math.max(...data.map((d) => d[POPULATION]));
const bubbleRadius = (share: number) => Math.max(MIN_RADIUS, MAX_RADIUS * Math.sqrt(share));

// One series per category in order of first appearance; within each region larger bubbles come first so
// smaller ones draw on top (series draw in order, so a later region's bubble can cover an earlier one's)
const regions = [...new Set(data.map((d) => d[REGION]))];
const series = regions.map((region, i) => ({
  type: "scatter" as const,
  id: `region-${i}`,
  label: region,
  color: t.palette[i],
  sizeAxisId: "population",
  data: data
    .filter((d) => d[REGION] === region)
    .sort((a, b) => b[POPULATION] - a[POPULATION])
    .map((d) => ({ id: d[CITY], x: d[LON], y: d[LAT], sizeValue: d[POPULATION] })),
  valueFormatter: (v: { id: string; sizeValue: number }) => `${v.id} · ${POPULATION} ${v.sizeValue}`,
}));

// Size legend: three reference values, the largest rounded down to one significant digit
const magnitude = 10 ** Math.floor(Math.log10(maxValue));
const topRef = Math.floor(maxValue / magnitude) * magnitude;
const sizeRefs = [topRef / 10, topRef / 3, topRef].map((v) => Number(v.toPrecision(1)));
const sizeRefRadii = sizeRefs.map((v) => bubbleRadius(v / maxValue));

const TITLE = "bubble-map-geographic · javascript · muix · anyplot.ai";
const subtitle = `${data.length} cities · bubble area proportional to ${POPULATION.toLowerCase()} · color by ${REGION.toLowerCase()}`;

function Basemap() {
  const xScale = useXScale();
  const yScale = useYScale();
  const area = useDrawingArea();
  return (
    <g clipPath="url(#bubble-map-clip)">
      <defs>
        <clipPath id="bubble-map-clip">
          <rect x={area.left} y={area.top} width={area.width} height={area.height} />
        </clipPath>
      </defs>
      {LAND.map((land) => (
        <path
          key={land.name}
          d={`M${land.ring.map(([lon, lat]) => `${xScale(lon)},${yScale(lat)}`).join("L")}Z`}
          fill={t.grid}
          stroke={t.inkSoft}
          strokeOpacity={0.55}
          strokeWidth={0.8}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <div style={{ width: W, height: H, display: "flex", flexDirection: "column", background: t.pageBg }}>
      <div style={{ height: TITLE_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 10 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <div style={{ display: "flex", flexDirection: "row" }}>
        <ChartsDataProvider
          width={CHART_W}
          height={CHART_H}
          margin={MARGIN}
          series={series}
          xAxis={[
            {
              min: lonCenter - lonSpan / 2,
              max: lonCenter + lonSpan / 2,
              label: LON,
              height: X_AXIS_H,
              tickNumber: 10,
              valueFormatter: (v: number) => `${Math.round(Math.abs(v))}°${v < 0 ? "W" : "E"}`,
              labelStyle: { fontSize: 16, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          yAxis={[
            {
              min: latCenter - latSpan / 2,
              max: latCenter + latSpan / 2,
              label: LAT,
              width: Y_AXIS_W,
              tickNumber: 8,
              valueFormatter: (v: number) => `${Math.round(Math.abs(v))}°${v < 0 ? "S" : "N"}`,
              labelStyle: { fontSize: 16, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          zAxis={[{ id: "population", sizeMap: { type: "continuous", min: 0, max: maxValue, size: bubbleRadius } }]}
          skipAnimation
        >
          <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
            <ChartsLegend sx={{ fontSize: 15, color: t.inkSoft }} />
            <ChartsSurface
              sx={{
                "& .MuiChartsAxis-line": { stroke: t.inkSoft },
                "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
                "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
                "& .MuiScatterChart-marker": { fillOpacity: BUBBLE_OPACITY, stroke: t.pageBg, strokeWidth: 1.2 },
              }}
            >
              <Basemap />
              <ChartsGrid horizontal vertical />
              <ScatterPlot />
              <ChartsXAxis />
              <ChartsYAxis />
            </ChartsSurface>
            <ChartsTooltip trigger="item" />
          </ChartsWrapper>
        </ChartsDataProvider>
        <div
          style={{
            width: SIZE_LEGEND_W,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            paddingRight: 24,
            boxSizing: "border-box",
          }}
        >
          <div style={{ fontSize: 15, color: t.inkSoft, marginBottom: 14 }}>{POPULATION}</div>
          {sizeRefs.map((v, i) => (
            <div key={v} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
              <svg width={2 * MAX_RADIUS + 2} height={2 * sizeRefRadii[i] + 2}>
                <circle
                  cx={MAX_RADIUS + 1}
                  cy={sizeRefRadii[i] + 1}
                  r={sizeRefRadii[i]}
                  fill={t.inkSoft}
                  fillOpacity={BUBBLE_OPACITY}
                  stroke={t.pageBg}
                  strokeWidth={1.2}
                />
              </svg>
              <span style={{ fontSize: 15, color: t.inkSoft }}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
