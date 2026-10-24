// anyplot.ai
// flowmap-origin-destination: Origin-Destination Flow Map
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 88/100 | Updated: 2026-10-24
import { useState } from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "flowmap-origin-destination · javascript · muix · anyplot.ai";
const LON_AXIS_LABEL = "Longitude (°)";
const LAT_AXIS_LABEL = "Latitude (°)";
const LEGEND_NOTE = "Node size = total throughput · arrowheads indicate flow direction";

const LON_PAD_SHARE = 0.09;
const LAT_PAD_SHARE = 0.14;
const HUB_TOP_SHARE = 0.3;
const MIN_ARC_WIDTH = 2.2;
const MAX_ARC_WIDTH = 9.2;
const MIN_NODE_R = 7;
const MAX_NODE_R = 22;

const MARGIN = { top: 88, right: 48, bottom: 108, left: 20 };
const X_AXIS_HEIGHT = 50;
const Y_AXIS_WIDTH = 68;

const LABEL_ARC_STEP = 4;

// Simplified coastlines as lon,lat rings; filled even-odd, so the Black Sea and Caspian rings cut water
const COASTLINE_RINGS = [
  // North America
  "-166,68.9 -156.5,71.3 -148,70.3 -141,69.6 -135,69.5 -128,70 -120,69 -110,68 -100,67.8 -96,68.5 -94,68 -90,68.5 -86,68 -82,66.5 -90,63.5 -92,62.8 -94,61 -94,59 -92.5,57 -88,56.5 -85,55.2 -82.3,52.9 -79.5,51.5 -78.8,54.5 -77,58 -78,60.5 -77.5,62.4 -73,62 -71,61 -69.5,59 -66,58.5 -64.5,60.2 -62,57.5 -60.5,55.5 -57.5,54 -55.7,52 -57,51.4 -60,50.2 -64.5,50.2 -66.5,49.8 -70,48 -66,49.2 -64.4,48.8 -64.8,47.5 -63.5,46.2 -61,45.8 -60,45.7 -63.5,44.6 -66,43.8 -67,44.7 -70,43.7 -70.5,41.8 -72,41.2 -74,40.6 -74,39.5 -75.5,38.5 -76,37 -75.6,35.2 -77,34.6 -79,33.3 -81,32 -81.3,30 -80.1,26.5 -80.4,25.2 -81.8,26 -82.7,28 -83.5,29.8 -85,29.7 -87.5,30.3 -89.5,30.2 -89.2,29.2 -91,29.3 -94,29.6 -97.2,27.6 -97.5,25.5 -97.8,22.5 -96,19 -94.5,18.2 -91.5,18.5 -90.3,21 -87,21.5 -87.5,18.5 -88.3,16 -84,15.8 -83.3,15 -83.6,11 -82,9 -79.5,9.5 -77.4,8.7 -78,8 -80,7.3 -82.8,8.3 -85.7,10 -85.7,11.2 -87.5,13 -91,13.9 -94,16 -96.5,15.7 -101,17.5 -105.5,20.5 -105.7,22.5 -108,25.5 -111,28 -114.7,31.7 -113,29 -111.5,26.5 -110,24 -109.5,23 -112,24.8 -114,27.5 -115.7,30.3 -117.1,32.5 -118.3,33.8 -120.6,34.6 -121.9,36.6 -122.5,37.8 -123.8,39.8 -124.2,42 -124,46.2 -124.7,48.4 -125.5,49.5 -128,50.8 -128,52.5 -130.5,54.5 -133,57 -136,58.5 -139.5,59.7 -144,60 -147.5,60.8 -150,59.4 -152,58.5 -154,57.5 -158,56 -162,55 -164.5,54.5 -157.5,57.5 -158,58.7 -162,59.8 -165,60.5 -165,62.3 -164,63.2 -161,64.5 -164.5,64.5 -166.5,65.2 -168,65.6 -164,66.5 -166,68.9",
  // Newfoundland, Baffin Island, Greenland, Iceland
  "-59.3,47.6 -55.5,46.7 -52.7,47.5 -53.5,49.5 -55.5,51.6 -57.5,50.5 -59.3,47.6",
  "-61.5,66.5 -64.5,63 -68,62.2 -72,63.5 -78,64.3 -74,66.8 -76,68.5 -80,70 -85,71.5 -88,73.5 -80,74 -72,72 -67,69.5 -61.5,66.5",
  "-43.5,59.8 -48,61 -51,64 -53.5,66.5 -53,68.5 -55,70.5 -58,75 -66,77 -20,75 -22,70.5 -25,68.5 -32,68 -38,65.5 -41,63 -43.5,59.8",
  "-24,65.5 -22,66.4 -16,66.5 -13.5,65 -18,63.4 -22.5,63.8 -24,65.5",
  // Cuba, Hispaniola
  "-84.9,21.9 -82,23.2 -80,23.1 -77,21.6 -74.2,20.2 -77.7,19.9 -78.5,21.5 -81,22 -84,21.8 -84.9,21.9",
  "-74.4,18.4 -72.8,19.9 -70,19.7 -68.4,18.6 -71,18 -74.4,18.4",
  // South America
  "-77.2,8.5 -76,9.5 -75.5,10.5 -74,11.3 -71.5,12.4 -71.5,11 -68,10.5 -64,10.6 -61.5,10.7 -60,8.5 -57,6 -54,5.7 -51.5,4.2 -50,1.8 -50,0 -48,-1 -44.5,-2.5 -41,-2.9 -38.5,-3.7 -35.2,-5.5 -34.8,-7.5 -35.5,-9.7 -37,-11 -38.5,-13 -39,-17.5 -40,-20 -41,-22 -43,-23 -46.3,-24.1 -48.5,-26 -48.6,-28.5 -50.5,-31 -53,-33.7 -55,-34.9 -58.4,-34.6 -57,-36.3 -57.5,-38.2 -62,-39 -62.3,-40.6 -65,-41 -63.5,-42.6 -65,-45 -67.5,-46.5 -66,-48 -68.3,-50.2 -68.5,-52.3 -66.5,-55 -70,-55 -74,-52.5 -75.5,-48 -73.7,-44 -74,-41.5 -73.5,-37 -71.7,-33 -71.4,-29 -70.4,-23.5 -70.2,-18.5 -71.4,-17.7 -75,-15.3 -76.3,-13.5 -77.8,-11 -79.5,-7.5 -81.2,-6 -81,-4.3 -80.3,-2.3 -80.9,-1 -80,0.9 -79,1.6 -77.5,4 -77.3,6.5 -77.5,7 -77.2,8.5",
  // Eurasia
  "-5.6,36 -4.4,36.7 -2,36.8 -0.5,38.2 0.2,38.8 -0.3,39.5 0.9,41 3.2,42 3.1,43.1 4.8,43.4 6.5,43.1 7.5,43.8 8.8,44.4 10.2,43.9 11,42.6 12.5,41.6 14,41 15.6,40 16,38.5 15.7,38 16.6,38.5 17.2,39.4 16.6,40.1 17.5,40.3 18.5,40.1 17.5,40.8 16,41.5 14.2,42.5 13.6,43.5 12.3,44.5 12.4,45.4 13.7,45.7 13.8,44.9 15.2,44.2 16.4,43.5 18,42.6 19.4,41.8 19.4,40.4 20.2,39.5 21.1,38.3 21.7,36.8 22.5,36.4 23.2,36.5 22.8,37.6 23.6,37.85 24.1,37.7 24,38.2 23.5,38.6 22.9,39.4 22.6,40.2 23.9,40.8 25.5,40.9 26.3,40.6 26.2,39.5 27,38.4 27.3,37 28.3,36.7 30.5,36.5 32.5,36.1 34.5,36.8 36,36.8 35.9,35 35.5,33.9 35.1,33 34.5,31.6 34.2,31.3 32.4,31.1 32.5,29.9 33.5,28.3 34.2,27.8 34.9,29.5 35,28 36.5,26 38,24 39.1,21.5 41,18.5 42.6,16 43.2,13.3 43.5,12.7 45,12.8 48,13.9 51,15.2 52.2,15.6 55,17.1 56.8,18.5 57.8,19 58.8,20.5 59.8,22.5 58.6,23.6 56.7,24.4 56.3,26.3 55.5,25.5 55,24.95 54.5,24.3 52,24 51.3,24.3 51.6,25.9 50.8,25.3 50.2,26.4 49.5,27.2 48.4,28.5 47.9,30 49,30.3 50.3,29.3 51.5,27.9 54,26.6 56.3,27.2 57.4,25.7 59,25.4 61.5,25.1 64,25.3 66.6,25.4 67.2,24.7 68.3,23.6 70.1,22.5 69,22.2 70.8,20.8 72.6,21.2 72.8,20 72.85,18.9 73.3,17 73.8,15.5 74.4,14 74.8,12.8 75.5,11.5 76.3,9.8 77.5,8.1 78.2,8.9 79.3,10.3 79.8,12 80.3,13.1 80.3,15.8 81.3,16.4 82.3,17 83.5,18.2 85,19.5 86.4,20 86.9,21.5 88.2,21.7 89.5,21.9 90.6,22.5 91.8,22.4 92.3,20.7 93.6,19 94.5,16.6 94.3,16.1 95.4,15.7 97,16.6 97.6,16.2 98.2,13.5 98.6,10 98.3,8 100.3,6.5 100.4,5 101.3,2.8 103.5,1.35 104.2,1.4 103.4,3.9 103.4,4.9 102.3,6.2 101.2,6.9 100.4,7.4 100,9.3 99.2,10.3 99.9,12.6 100.6,13.5 101,12.6 102.5,12 103,11 104.5,10.4 105,8.6 106.7,10 107.5,10.5 109.2,11.6 109.3,13 109,15.3 108.2,16.1 106.6,17.5 105.7,19 106.6,20.4 107.5,21.4 108.5,21.6 109.7,21 110.4,20.3 111,21.5 112.5,21.8 113.6,22.2 114.2,22.25 115.5,22.8 117,23.5 118.5,24.5 119.6,25.7 119.8,26.7 121,28 121.9,29.9 121.9,30.9 121.6,31.5 120.9,32.6 120.3,34.3 119.3,35 120.5,36.1 122.5,36.9 121,37.7 119,37.2 118.8,38.1 117.7,38.6 117.7,39.1 119.5,39.9 121.5,40.9 121.2,38.8 123.5,39.8 124.7,38 126.2,36.6 126.5,35 126.5,34.3 127.5,34.6 128.6,35 129.1,35.1 129.5,36 129.4,37 128.6,38.3 127.5,39.8 128.5,40.4 129.7,40.9 129.8,41.8 130.7,42.3 132,43.2 133.5,42.8 135.5,43.9 137.8,45.7 138.5,47 140.3,48.5 140.5,50.2 141.4,52.2 140.5,53.3 137.3,54 135.2,54.7 137,55.4 139,56.5 141.5,58.5 143,59.3 146,59.4 149,59.7 152,59.1 154.5,59.6 155.9,61 160,61.8 163,62.5 156.7,57.5 155.6,55 156.6,51 158.6,52.9 160,54 162,56.2 163.3,58 165,60 170,60 173,61.7 177,62.5 180,65 180,69 170,70 160,69.7 150,71.5 140,72.5 130,71 120,73 113,73.7 105,77 95,76 87,74 80,72.5 72,72.5 68,69 60,69 54,68.4 44,68 43.5,66.3 40.3,64.6 37,65 34.8,64.5 33,66.7 41,66.8 40,68 33,69.3 28.5,70.9 24,71 19,70.2 15,68.5 13,67.2 12.3,65.9 10.5,64.2 7,62.7 5,61.5 5,59.5 5.6,58.6 7,58 8.3,58.1 10,59 11,59.2 11.2,58.4 12.5,56.6 12.9,55.4 14.4,55.6 16,56.5 16.5,57.5 16.8,58.8 18.5,59.5 17.3,61.5 17.5,62.4 21,64 22.2,65.6 24.6,65.8 25.3,64.9 21.5,62.5 21.5,61 22.9,59.8 25,60.3 28,60.5 30.2,59.9 28,59.5 24,59.4 23.5,59.1 21.5,57.4 21,56 21.1,55.3 19.9,54.6 18.6,54.4 17.3,54.8 14.2,53.9 12.4,54.3 11,54 10.8,54.6 10.5,55 10.6,56.5 10.6,57.7 9,57.1 8.2,56.6 8.1,55.5 8.6,54.9 8.7,53.9 8,53.6 7,53.4 6,53.4 4.8,52.9 4.5,52.2 4.1,51.95 3.4,51.4 2.5,51.1 1.6,50.9 1.6,50.2 0.2,49.7 -1.1,49.4 -1.9,49.7 -1.6,48.7 -3,48.8 -4.7,48.4 -4.2,47.8 -2.5,47.3 -1.2,46.1 -1.2,44.7 -1.5,43.5 -3.5,43.5 -5.7,43.6 -8,43.7 -9.3,43 -8.9,41.9 -8.8,40.5 -9.5,38.8 -8.9,37.9 -8.9,37 -7.4,37.2 -6.3,36.6 -5.6,36",
  // Black Sea and Caspian Sea (holes in Eurasia)
  "28.9,41.3 28,42 27.6,43.2 28.6,44.3 29.7,45.2 30.5,46.4 31.7,46.6 33.5,46 32.6,45.4 33.6,44.5 35.4,45 36.5,45.3 38.2,46.7 39.2,47.1 38,45.7 37.3,44.9 38.8,44.2 40,43.4 41.6,41.6 40,41 38,40.9 36.5,41.3 35.2,42 33.5,42 31.5,41.2 29.9,41.1 28.9,41.3",
  "47.5,45.5 49,46.4 51.5,47 53,46.8 53,45.2 51.3,44.5 51.5,43.2 52.7,42 52.9,41 54.5,40.9 53.9,39 53.9,37.4 51,36.7 49,37.6 48.8,38.8 49.5,40.3 49.2,40.9 48.5,42 47.5,43 47.4,44.6 47.5,45.5",
  // Mediterranean islands, British Isles
  "12.4,38.1 15.6,38.3 15.1,36.7 12.4,37.6 12.4,38.1",
  "8.4,39.1 9.6,39.1 9.8,41.1 8.2,41 8.4,39.1",
  "23.5,35.3 26.3,35.2 24.5,34.9 23.5,35.3",
  "-5.7,50.1 -3.5,50.4 -1,50.8 1.4,51.2 1.3,52 1.7,52.7 0.3,53.4 -0.2,54.1 -1.2,54.6 -1.6,55.6 -2.6,56.1 -1.9,57.5 -4,57.6 -3.1,58.6 -5,58.6 -5.7,57.6 -5.6,56.5 -6.2,56.3 -5.5,55.4 -5,54.9 -3.2,54.4 -3,53.4 -4.5,53.3 -4.5,52.8 -4.2,52.2 -5.2,51.8 -4,51.6 -3,51.5 -4.2,51.2 -5.2,50.6 -5.7,50.1",
  "-6,52.2 -6.1,53.4 -6,54.2 -5.6,55 -7.4,55.4 -8.5,54.6 -10,54.2 -9.5,53.3 -10.3,52.1 -9.6,51.5 -8,51.7 -6.4,52.1 -6,52.2",
  // Africa, Madagascar
  "32.3,31.25 29.9,31.2 25.2,31.6 20,32.1 19,30.3 15.6,31.4 13,32.8 11.1,33.2 10.3,33.8 10.8,35.6 11.1,37 9.8,37.3 7,37 3,36.8 0,35.8 -2,35.1 -5.3,35.9 -6,35.8 -6.8,34 -8.5,33.3 -9.8,31.4 -9.6,30.4 -10,29 -13,27.6 -14.5,26.2 -16,24 -17,21 -16.3,19.5 -16.5,16.2 -17.5,14.7 -16.8,13.2 -15.5,11.7 -13.5,9.6 -12.5,7.8 -11.2,6.8 -8.5,4.7 -6,4.3 -2,4.8 1.2,6.1 3.4,6.4 5,5.6 6,4.3 7.5,4.5 8.8,4.4 9.6,3.5 9.8,2.1 9.5,0.5 9.3,-0.7 10.6,-2.8 11.8,-4.5 12.3,-6 13.3,-8.8 13,-12.6 11.8,-17 12.8,-19.3 14.4,-22.9 15.2,-26.7 16.5,-28.6 18,-31.7 18.4,-34.1 20,-34.8 22.5,-34 25.6,-34 27.9,-33.1 30,-31.3 31,-29.9 32.5,-28.5 32.9,-26 33.5,-25.4 35.5,-24 35.3,-22 35,-20 36.8,-18.6 39.2,-16.8 40.7,-14.6 40.5,-10.5 39.3,-8 39.2,-6.8 39.3,-4.8 40.2,-2.7 41.5,-1.5 42.5,-0.5 44,1.5 46,2.5 48,4.6 49.5,7.3 50.8,9.6 51.3,11.8 49.5,11.3 46.2,10.8 44,10.5 43.3,11.5 42.7,12.6 41.6,13.5 40,15.5 39.3,15.8 38.5,18 37.4,19.8 37.2,21 36.5,22.2 35.5,23.7 34.6,25.8 33.6,27.3 32.6,29.7 32.5,29.9 32.3,31.25",
  "49.3,-12 50.4,-15.5 49.4,-17.8 48.8,-20.5 47.1,-24.9 45.2,-25.5 44,-24 43.6,-21.3 44.4,-19 44,-17 46.3,-15.7 47.9,-13.6 49.3,-12",
  // Sri Lanka, Hainan, Taiwan, Japan, Sakhalin, Philippines
  "79.9,9.7 80.2,9.8 81.4,8.5 81.9,7.3 81.6,6.4 80.6,5.95 80,6.5 79.8,8 79.9,9.7",
  "108.7,19.3 109.5,18.2 110.5,18.7 111,19.6 110.2,20.1 108.7,19.3",
  "120.1,23 120.7,22 121.9,24.6 121.5,25.3 120.3,24 120.1,23",
  "130.9,34 132.4,34.3 133.9,34.4 135.2,34.6 135.1,33.8 135.8,33.5 136.9,34.3 137,34.7 138.8,34.6 139.8,35 140.9,35.7 140.6,36.9 141,38.3 141.9,39.6 141.5,41.4 140.3,41.2 139.9,40.5 140,39.4 139.4,38.2 138.5,37.5 137.3,36.9 136.8,37.4 136.1,36.2 135.4,35.6 133.4,35.5 132.3,35.2 130.9,34.4 130.9,34",
  "129.6,33.4 130.4,33.9 131.6,33.4 131.9,32.6 131.3,31.4 130.6,31.1 130.1,32.2 129.7,32.9 129.6,33.4",
  "132.5,33.2 133,33.9 134.6,34.2 134.7,33.8 134.2,33.3 133,32.8 132.5,33.2",
  "140,41.5 141.2,41.8 143.2,42 145.5,43.3 145.3,44.3 142,45.4 141.6,43.6 140.4,43.3 140,42.3 140,41.5",
  "142,46 143.5,49 144.5,49 143.2,51.8 143,54.3 142.2,54.2 142,51 142.1,48 141.9,46.6 142,46",
  "120,16 120.6,18.5 122.2,18.5 122.1,16.5 121.6,15 122,14 124,13 123,13.7 121.5,13.6 120.6,14.4 120,16",
  "122,7 123.5,8.5 125.5,9.7 126.6,7.3 125.4,5.6 124.1,6.5 122,7",
  // Sumatra, Java, Borneo, Sulawesi, New Guinea
  "95.3,5.6 97.5,5.2 100,2.5 103.7,-1 104.5,-2.5 105.9,-5.8 104.5,-5.9 102.3,-4 100.5,-1.3 98.7,1.7 96.5,3.7 95.3,5.6",
  "105.2,-6.8 106,-5.9 108.3,-6.3 110.4,-6.9 112.6,-6.9 114.4,-7.8 114.5,-8.7 111,-8.2 108,-7.8 105.5,-7 105.2,-6.8",
  "109,1.8 109.6,2 111,1.6 113,3.2 115.5,5.4 117,7 118.5,5 119.2,5.2 118,4.2 117.7,3 118.9,1 117.6,0 117.5,-0.8 116.5,-2.5 116,-4 114.5,-3.6 113,-3.1 111,-3 110.2,-2.7 110,-1.2 109,0 109,1.8",
  "119.5,-5.5 120.4,-5.5 120.6,-2.7 121.3,-4.8 122.8,-4.7 121.3,-1.9 123.3,-0.9 120.3,-0.9 120.3,0.5 124.9,1.5 124.3,0.4 121,0.5 119.8,0 119.4,-3.5 119.5,-5.5",
  "131,-1.3 134,-0.9 135.5,-3.3 138,-1.6 141,-2.6 145,-4.3 146,-5.6 147.5,-6.3 147.7,-8 150,-10.3 148,-10.2 146,-8.3 143.7,-9 142.6,-9.3 141,-9.1 139,-8.1 138,-8.4 137.6,-5.2 135.2,-4.4 133.4,-4 132,-2.8 131,-1.3",
  // Australia, Tasmania
  "114.1,-21.8 116.7,-20.6 119,-20 121,-19.4 122.2,-17 123.5,-16.3 125,-14.6 126.9,-13.8 129.5,-14.9 130.2,-12.5 132.6,-11.6 135.8,-12.2 136.5,-12.8 135.5,-14.9 137.7,-16.3 139.5,-17.6 141,-16.7 141.5,-13 142.5,-10.7 143.5,-12.5 144.5,-14.3 145.4,-16 146.1,-19 148.8,-20.4 150.8,-22.6 153.1,-25.2 153.6,-28.5 153,-31 151.3,-33.9 150,-37.5 147.8,-37.9 146.3,-39.1 144.5,-38.2 141,-38.1 139.6,-37.2 138.9,-35.6 138,-34.5 137.5,-35.1 136.8,-35.3 137.7,-34 137.8,-32.7 136,-34.8 134.1,-32.7 131.2,-31.5 128,-32.2 124,-33.8 120,-33.9 117.9,-35.1 115,-34.3 115.7,-32 114.9,-29.5 113.4,-26.5 113.8,-24 114.1,-21.8",
  "144.6,-40.7 148.3,-40.9 148,-43.2 146.8,-43.6 145.2,-42.2 144.6,-40.7",
];

// Columns: set these to your data's column names
const ORIGIN_NAME = "Origin"; // role: origin_name
const ORIGIN_LAT = "Origin latitude (°)"; // role: origin_lat
const ORIGIN_LON = "Origin longitude (°)"; // role: origin_lon
const DEST_NAME = "Destination"; // role: dest_name
const DEST_LAT = "Destination latitude (°)"; // role: dest_lat
const DEST_LON = "Destination longitude (°)"; // role: dest_lon
const FLOW = "Container flow (thousand TEU/year)"; // role: flow

// Data: replace this block with your own records
const data: Record<string, string | number>[] = [
  { [ORIGIN_NAME]: "Shanghai", [ORIGIN_LAT]: 31.23, [ORIGIN_LON]: 121.47, [DEST_NAME]: "Los Angeles", [DEST_LAT]: 33.73, [DEST_LON]: -118.26, [FLOW]: 1450 },
  { [ORIGIN_NAME]: "Shanghai", [ORIGIN_LAT]: 31.23, [ORIGIN_LON]: 121.47, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 980 },
  { [ORIGIN_NAME]: "Shanghai", [ORIGIN_LAT]: 31.23, [ORIGIN_LON]: 121.47, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 620 },
  { [ORIGIN_NAME]: "Singapore", [ORIGIN_LAT]: 1.29, [ORIGIN_LON]: 103.85, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 710 },
  { [ORIGIN_NAME]: "Singapore", [ORIGIN_LAT]: 1.29, [ORIGIN_LON]: 103.85, [DEST_NAME]: "Jebel Ali", [DEST_LAT]: 25.01, [DEST_LON]: 55.06, [FLOW]: 540 },
  { [ORIGIN_NAME]: "Singapore", [ORIGIN_LAT]: 1.29, [ORIGIN_LON]: 103.85, [DEST_NAME]: "Mumbai", [DEST_LAT]: 18.95, [DEST_LON]: 72.95, [FLOW]: 460 },
  { [ORIGIN_NAME]: "Hong Kong", [ORIGIN_LAT]: 22.32, [ORIGIN_LON]: 114.17, [DEST_NAME]: "Los Angeles", [DEST_LAT]: 33.73, [DEST_LON]: -118.26, [FLOW]: 890 },
  { [ORIGIN_NAME]: "Hong Kong", [ORIGIN_LAT]: 22.32, [ORIGIN_LON]: 114.17, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 520 },
  { [ORIGIN_NAME]: "Busan", [ORIGIN_LAT]: 35.18, [ORIGIN_LON]: 129.08, [DEST_NAME]: "Los Angeles", [DEST_LAT]: 33.73, [DEST_LON]: -118.26, [FLOW]: 780 },
  { [ORIGIN_NAME]: "Busan", [ORIGIN_LAT]: 35.18, [ORIGIN_LON]: 129.08, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 410 },
  { [ORIGIN_NAME]: "Rotterdam", [ORIGIN_LAT]: 51.92, [ORIGIN_LON]: 4.48, [DEST_NAME]: "New York", [DEST_LAT]: 40.67, [DEST_LON]: -74.13, [FLOW]: 630 },
  { [ORIGIN_NAME]: "Jebel Ali", [ORIGIN_LAT]: 25.01, [ORIGIN_LON]: 55.06, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 590 },
  { [ORIGIN_NAME]: "Jebel Ali", [ORIGIN_LAT]: 25.01, [ORIGIN_LON]: 55.06, [DEST_NAME]: "Mumbai", [DEST_LAT]: 18.95, [DEST_LON]: 72.95, [FLOW]: 350 },
  { [ORIGIN_NAME]: "Mumbai", [ORIGIN_LAT]: 18.95, [ORIGIN_LON]: 72.95, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 480 },
  { [ORIGIN_NAME]: "Mumbai", [ORIGIN_LAT]: 18.95, [ORIGIN_LON]: 72.95, [DEST_NAME]: "Colombo", [DEST_LAT]: 6.95, [DEST_LON]: 79.84, [FLOW]: 260 },
  { [ORIGIN_NAME]: "Colombo", [ORIGIN_LAT]: 6.95, [ORIGIN_LON]: 79.84, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 300 },
  { [ORIGIN_NAME]: "Hamburg", [ORIGIN_LAT]: 53.55, [ORIGIN_LON]: 9.99, [DEST_NAME]: "New York", [DEST_LAT]: 40.67, [DEST_LON]: -74.13, [FLOW]: 410 },
  { [ORIGIN_NAME]: "Piraeus", [ORIGIN_LAT]: 37.94, [ORIGIN_LON]: 23.65, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 330 },
  { [ORIGIN_NAME]: "Santos", [ORIGIN_LAT]: -23.96, [ORIGIN_LON]: -46.33, [DEST_NAME]: "Rotterdam", [DEST_LAT]: 51.92, [DEST_LON]: 4.48, [FLOW]: 360 },
  { [ORIGIN_NAME]: "Vancouver", [ORIGIN_LAT]: 49.29, [ORIGIN_LON]: -123.11, [DEST_NAME]: "Shanghai", [DEST_LAT]: 31.23, [DEST_LON]: 121.47, [FLOW]: 520 },
  { [ORIGIN_NAME]: "Vancouver", [ORIGIN_LAT]: 49.29, [ORIGIN_LON]: -123.11, [DEST_NAME]: "Singapore", [DEST_LAT]: 1.29, [DEST_LON]: 103.85, [FLOW]: 300 },
];

// Plot: reads only data and the constants above
type PortInfo = {
  name: string;
  lat: number;
  lon: number;
  throughput: number;
};

const portMap = new Map<string, PortInfo>();
for (const row of data) {
  const oName = String(row[ORIGIN_NAME]);
  const oLat = Number(row[ORIGIN_LAT]);
  const oLon = Number(row[ORIGIN_LON]);
  const dName = String(row[DEST_NAME]);
  const dLat = Number(row[DEST_LAT]);
  const dLon = Number(row[DEST_LON]);
  const vol = Number(row[FLOW]);

  if (!portMap.has(oName)) {
    portMap.set(oName, { name: oName, lat: oLat, lon: oLon, throughput: 0 });
  }
  portMap.get(oName)!.throughput += vol;

  if (!portMap.has(dName)) {
    portMap.set(dName, { name: dName, lat: dLat, lon: dLon, throughput: 0 });
  }
  portMap.get(dName)!.throughput += vol;
}

const portList = Array.from(portMap.values());
const volumes = data.map((r) => Number(r[FLOW]));
const minVolume = Math.min(...volumes);
const maxVolume = Math.max(...volumes);
const totalVolume = volumes.reduce((s, v) => s + v, 0);

const throughputs = portList.map((p) => p.throughput);
const minThroughput = Math.min(...throughputs);
const maxThroughput = Math.max(...throughputs);

const hubCount = Math.round(portList.length * HUB_TOP_SHARE);
const hubNames = new Set(
  [...portList]
    .sort((a, b) => b.throughput - a.throughput)
    .slice(0, hubCount)
    .map((p) => p.name),
);

const sortedFlows = [...data].sort((a, b) => Number(a[FLOW]) - Number(b[FLOW]));

const allLons = portList.map((p) => p.lon);
const allLats = portList.map((p) => p.lat);
const rawLonMin = Math.min(...allLons);
const rawLonMax = Math.max(...allLons);
const rawLatMin = Math.min(...allLats);
const rawLatMax = Math.max(...allLats);
const rawLonSpan = rawLonMax - rawLonMin;
const rawLatSpan = rawLatMax - rawLatMin;

const baseLonMin = rawLonMin - rawLonSpan * LON_PAD_SHARE;
const baseLonMax = rawLonMax + rawLonSpan * LON_PAD_SHARE;
const baseLatMin = rawLatMin - rawLatSpan * LAT_PAD_SHARE;
const baseLatMax = rawLatMax + rawLatSpan * LAT_PAD_SHARE;

const meanLatRad = (((rawLatMin + rawLatMax) / 2) * Math.PI) / 180;
const cosMeanLat = Math.cos(meanLatRad);
const plotW = window.ANYPLOT_SIZE.width - MARGIN.left - MARGIN.right - Y_AXIS_WIDTH;
const plotH = window.ANYPLOT_SIZE.height - MARGIN.top - MARGIN.bottom - X_AXIS_HEIGHT;

const baseLonSpan = baseLonMax - baseLonMin;
const baseLatSpan = baseLatMax - baseLatMin;
const targetLonSpanForLat = (plotW / plotH) * (baseLatSpan / cosMeanLat);

const lonMid = (baseLonMin + baseLonMax) / 2;
const latMid = (baseLatMin + baseLatMax) / 2;
const finalLonSpan = Math.max(baseLonSpan, targetLonSpanForLat);
const finalLatSpan = (finalLonSpan * cosMeanLat * plotH) / plotW;

const lonMin = Math.round(lonMid - finalLonSpan / 2);
const lonMax = Math.round(lonMid + finalLonSpan / 2);
const latMin = Math.max(-85, Math.round(latMid - finalLatSpan / 2));
const latMax = Math.min(85, Math.round(latMid + finalLatSpan / 2));

const seqStartInt = parseInt(t.seq[0].slice(1), 16);
const seqEndInt = parseInt(t.seq[1].slice(1), 16);

const coastlineRings = COASTLINE_RINGS.map((ring) =>
  ring.split(" ").map((pair) => {
    const [lonStr, latStr] = pair.split(",");
    return [Number(lonStr), Number(latStr)] as [number, number];
  }),
);

type HoverInfo = {
  label: string;
  detail: string;
  x: number;
  y: number;
} | null;

function FlowMapLayer({
  hover,
  onHoverChange,
}: {
  hover: HoverInfo;
  onHoverChange: (h: HoverInfo) => void;
}) {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const drawingArea = useDrawingArea();

  const positionedPorts = portList.map((p) => {
    const cx = xScale(p.lon);
    const cy = yScale(p.lat);
    const tRatio = (p.throughput - minThroughput) / (maxThroughput - minThroughput);
    const radius = MIN_NODE_R + tRatio * (MAX_NODE_R - MIN_NODE_R);
    const isHub = hubNames.has(p.name);
    return { ...p, cx, cy, radius, isHub };
  });

  const positionedFlows = sortedFlows.map((flow, i) => {
    const x1 = xScale(Number(flow[ORIGIN_LON]));
    const y1 = yScale(Number(flow[ORIGIN_LAT]));
    const x2 = xScale(Number(flow[DEST_LON]));
    const y2 = yScale(Number(flow[DEST_LAT]));
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dist = Math.hypot(dx, dy);
    const bowSign = i % 2 === 0 ? 1 : -1;
    const bowMagnitude = 0.09 + ((i * 53) % 7) * 0.015;
    const bow = dist * bowMagnitude * bowSign;
    const controlX = (x1 + x2) / 2 + (-dy / dist) * bow;
    const controlY = (y1 + y2) / 2 + (dx / dist) * bow;
    const ratio = (Number(flow[FLOW]) - minVolume) / (maxVolume - minVolume);
    const strokeWidth = MIN_ARC_WIDTH + ratio * (MAX_ARC_WIDTH - MIN_ARC_WIDTH);
    return { flow, x1, y1, x2, y2, dx, dy, dist, controlX, controlY, ratio, strokeWidth };
  });

  // Points along every arc, so label slots can avoid covering flows
  const arcSamples = positionedFlows.flatMap((a) => {
    const steps = Math.ceil(a.dist / LABEL_ARC_STEP);
    return Array.from({ length: steps + 1 }, (_, k) => {
      const s = k / steps;
      return {
        x: (1 - s) ** 2 * a.x1 + 2 * (1 - s) * s * a.controlX + s ** 2 * a.x2,
        y: (1 - s) ** 2 * a.y1 + 2 * (1 - s) * s * a.controlY + s ** 2 * a.y2,
        hw: a.strokeWidth / 2,
      };
    });
  });

  const labelBoxes: { x0: number; y0: number; x1: number; y1: number }[] = positionedPorts.map((p) => ({
    x0: p.cx - p.radius - 2,
    y0: p.cy - p.radius - 2,
    x1: p.cx + p.radius + 2,
    y1: p.cy + p.radius + 2,
  }));

  const labelOffsets = new Map<string, { lx: number; ly: number; anchor: "middle" | "start" | "end" }>();
  const portsBySize = [...positionedPorts].sort((a, b) => b.throughput - a.throughput);

  for (const p of portsBySize) {
    const fs = p.isHub ? 15 : 14;
    const textW = p.name.length * fs * 0.56;
    const textH = fs + 4;
    const gap = p.radius + 8;

    const candidates: { lx: number; ly: number; anchor: "middle" | "start" | "end"; bx0: number; by0: number; bx1: number; by1: number }[] = [
      {
        lx: p.cx,
        ly: p.cy - gap,
        anchor: "middle",
        bx0: p.cx - textW / 2,
        by0: p.cy - gap - textH,
        bx1: p.cx + textW / 2,
        by1: p.cy - gap,
      },
      {
        lx: p.cx,
        ly: p.cy + gap + fs - 2,
        anchor: "middle",
        bx0: p.cx - textW / 2,
        by0: p.cy + gap,
        bx1: p.cx + textW / 2,
        by1: p.cy + gap + textH,
      },
      {
        lx: p.cx + gap,
        ly: p.cy + 5,
        anchor: "start",
        bx0: p.cx + gap,
        by0: p.cy - textH / 2,
        bx1: p.cx + gap + textW,
        by1: p.cy + textH / 2,
      },
      {
        lx: p.cx - gap,
        ly: p.cy + 5,
        anchor: "end",
        bx0: p.cx - gap - textW,
        by0: p.cy - textH / 2,
        bx1: p.cx - gap,
        by1: p.cy + textH / 2,
      },
      {
        lx: p.cx + gap * 0.8,
        ly: p.cy - gap * 0.65,
        anchor: "start",
        bx0: p.cx + gap * 0.8,
        by0: p.cy - gap * 0.65 - textH,
        bx1: p.cx + gap * 0.8 + textW,
        by1: p.cy - gap * 0.65,
      },
      {
        lx: p.cx - gap * 0.8,
        ly: p.cy - gap * 0.65,
        anchor: "end",
        bx0: p.cx - gap * 0.8 - textW,
        by0: p.cy - gap * 0.65 - textH,
        bx1: p.cx - gap * 0.8,
        by1: p.cy - gap * 0.65,
      },
    ];
    // Lower slots and farther copies of every slot, tried after the near ones
    candidates.push(
      { lx: p.cx + gap * 0.8, ly: p.cy + gap * 0.65 + fs - 2, anchor: "start", bx0: p.cx + gap * 0.8, by0: p.cy + gap * 0.65, bx1: p.cx + gap * 0.8 + textW, by1: p.cy + gap * 0.65 + textH },
      { lx: p.cx - gap * 0.8, ly: p.cy + gap * 0.65 + fs - 2, anchor: "end", bx0: p.cx - gap * 0.8 - textW, by0: p.cy + gap * 0.65, bx1: p.cx - gap * 0.8, by1: p.cy + gap * 0.65 + textH },
    );
    for (const c of [...candidates]) {
      const ox = (c.bx0 + c.bx1) / 2 - p.cx;
      const oy = (c.by0 + c.by1) / 2 - p.cy;
      const len = Math.hypot(ox, oy);
      const sx = (ox / len) * gap * 0.9;
      const sy = (oy / len) * gap * 0.9;
      candidates.push({ ...c, lx: c.lx + sx, ly: c.ly + sy, bx0: c.bx0 + sx, by0: c.by0 + sy, bx1: c.bx1 + sx, by1: c.by1 + sy });
    }

    let best = candidates[0];
    let bestCost = Infinity;

    for (const [ci, c] of candidates.entries()) {
      let cost = ci * 2;
      for (const b of labelBoxes) {
        const ox = Math.max(0, Math.min(c.bx1, b.x1) - Math.max(c.bx0, b.x0));
        const oy = Math.max(0, Math.min(c.by1, b.y1) - Math.max(c.by0, b.y0));
        cost += ox * oy * 4;
      }
      for (const s of arcSamples) {
        if (s.x > c.bx0 - s.hw && s.x < c.bx1 + s.hw && s.y > c.by0 - s.hw && s.y < c.by1 + s.hw) {
          cost += LABEL_ARC_STEP * s.hw * 2;
        }
      }
      const outside =
        c.bx0 < drawingArea.left ||
        c.bx1 > drawingArea.left + drawingArea.width ||
        c.by0 < drawingArea.top ||
        c.by1 > drawingArea.top + drawingArea.height;
      if (outside) cost += 1e6;
      if (cost < bestCost) {
        bestCost = cost;
        best = c;
      }
    }

    labelOffsets.set(p.name, { lx: best.lx, ly: best.ly, anchor: best.anchor });
    labelBoxes.push({ x0: best.bx0 - 3, y0: best.by0 - 2, x1: best.bx1 + 3, y1: best.by1 + 2 });
  }

  const barX = drawingArea.left;
  const barY = drawingArea.top + drawingArea.height + X_AXIS_HEIGHT + 28;
  const barWidth = 260;
  const barHeight = 14;

  return (
    <g>
      <defs>
        <clipPath id="worldClip">
          <rect
            x={drawingArea.left}
            y={drawingArea.top}
            width={drawingArea.width}
            height={drawingArea.height}
          />
        </clipPath>
        <linearGradient id="flowLegendGradient" x1="0%" x2="100%" y1="0%" y2="0%">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>

      {/* Simplified coastlines */}
      <g clipPath="url(#worldClip)">
        <path
          d={coastlineRings
            .map(
              (points) =>
                points.map(([lon, lat], j) => `${j === 0 ? "M" : "L"} ${xScale(lon)},${yScale(lat)}`).join(" ") + " Z",
            )
            .join(" ")}
          fillRule="evenodd"
          fill={t.inkSoft}
          fillOpacity={0.12}
          stroke={t.inkSoft}
          strokeWidth={1}
          strokeOpacity={0.35}
          strokeLinejoin="round"
        />
      </g>

      {/* Curved origin-destination flow arcs */}
      {positionedFlows.map(({ flow, x1, y1, x2, y2, dx, dy, controlX, controlY, ratio, strokeWidth }, i) => {
        const oName = String(flow[ORIGIN_NAME]);
        const dName = String(flow[DEST_NAME]);
        const vol = Number(flow[FLOW]);
        const strokeOpacity = 0.4 + ratio * 0.35;

        const rCh = Math.round(((seqStartInt >> 16) & 255) + (((seqEndInt >> 16) & 255) - ((seqStartInt >> 16) & 255)) * ratio);
        const gCh = Math.round(((seqStartInt >> 8) & 255) + (((seqEndInt >> 8) & 255) - ((seqStartInt >> 8) & 255)) * ratio);
        const bCh = Math.round((seqStartInt & 255) + ((seqEndInt & 255) - (seqStartInt & 255)) * ratio);
        const color = `rgb(${rCh}, ${gCh}, ${bCh})`;

        const arrowX = 0.25 * x1 + 0.5 * controlX + 0.25 * x2;
        const arrowY = 0.25 * y1 + 0.5 * controlY + 0.25 * y2;
        const angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;

        const flowTooltip = {
          label: `${oName} → ${dName}`,
          detail: `${FLOW}: ${vol.toLocaleString()}`,
          x: arrowX,
          y: arrowY,
        };

        return (
          <g key={`${oName}-${dName}-${i}`}>
            <path
              d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeOpacity={strokeOpacity}
              strokeLinecap="round"
            />
            <path
              d={`M ${x1},${y1} Q ${controlX},${controlY} ${x2},${y2}`}
              fill="none"
              stroke="transparent"
              strokeWidth={Math.max(strokeWidth, 16)}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(flowTooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <polygon
              points="-7,-4.5 7,0 -7,4.5"
              transform={`translate(${arrowX}, ${arrowY}) rotate(${angleDeg})`}
              fill={color}
              fillOpacity={Math.min(strokeOpacity + 0.15, 0.92)}
            />
          </g>
        );
      })}

      {/* Port nodes and collision-checked labels */}
      {positionedPorts.map((port) => {
        const pos = labelOffsets.get(port.name)!;
        const portTooltip = {
          label: port.name,
          detail: `Throughput: ${port.throughput.toLocaleString()}`,
          x: port.cx,
          y: port.cy - port.radius - 8,
        };
        return (
          <g key={port.name}>
            <circle
              cx={port.cx}
              cy={port.cy}
              r={port.radius}
              fill={t.palette[0]}
              stroke={t.pageBg}
              strokeWidth={2.5}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => onHoverChange(portTooltip)}
              onMouseLeave={() => onHoverChange(null)}
            />
            <text
              x={pos.lx}
              y={pos.ly}
              textAnchor={pos.anchor}
              fontSize={port.isHub ? 15 : 14}
              fontWeight={port.isHub ? 700 : 600}
              fill={t.ink}
              stroke={t.pageBg}
              strokeWidth={3.5}
              paintOrder="stroke"
              style={{ pointerEvents: "none" }}
            >
              {port.name}
            </text>
          </g>
        );
      })}

      {/* Legend and usage key */}
      <g>
        <text x={barX} y={barY - 10} textAnchor="start" fontSize={14} fontWeight={600} fill={t.inkSoft}>
          {FLOW}
        </text>
        <rect x={barX} y={barY} width={barWidth} height={barHeight} fill="url(#flowLegendGradient)" rx={3} />
        <text x={barX} y={barY + barHeight + 18} textAnchor="start" fontSize={14} fill={t.inkSoft}>
          {minVolume.toLocaleString()}
        </text>
        <text x={barX + barWidth} y={barY + barHeight + 18} textAnchor="end" fontSize={14} fill={t.inkSoft}>
          {maxVolume.toLocaleString()}
        </text>
        <text
          x={drawingArea.left + drawingArea.width}
          y={barY + 12}
          textAnchor="end"
          fontSize={14}
          fill={t.inkSoft}
        >
          {LEGEND_NOTE}
        </text>
      </g>

      {/* Interactive hover tooltip */}
      {hover &&
        (() => {
          const charWidth = 7.8;
          const boxW = Math.max(hover.label.length, hover.detail.length) * charWidth + 24;
          const boxH = 48;
          const bx = hover.x - boxW / 2;
          const by = hover.y - boxH - 12;
          return (
            <g style={{ pointerEvents: "none" }}>
              <rect
                x={bx}
                y={by}
                width={boxW}
                height={boxH}
                rx={6}
                fill={t.elevatedBg}
                stroke={t.inkSoft}
                strokeOpacity={0.4}
              />
              <text x={hover.x} y={by + 20} textAnchor="middle" fontSize={14} fontWeight={600} fill={t.ink}>
                {hover.label}
              </text>
              <text x={hover.x} y={by + 38} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
                {hover.detail}
              </text>
            </g>
          );
        })()}
    </g>
  );
}

export default function Chart() {
  const [hover, setHover] = useState<HoverInfo>(null);
  const { width, height } = window.ANYPLOT_SIZE;
  const subtitle = `${data.length} flows across ${portList.length} locations · total ${FLOW}: ${totalVolume.toLocaleString()}`;

  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      series={[]}
      skipAnimation
      disableAxisListener
      xAxis={[
        {
          scaleType: "linear",
          min: lonMin,
          max: lonMax,
          height: X_AXIS_HEIGHT,
          label: LON_AXIS_LABEL,
          valueFormatter: (v: number) => `${v}°`,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: latMin,
          max: latMax,
          width: Y_AXIS_WIDTH,
          label: LAT_AXIS_LABEL,
          valueFormatter: (v: number) => `${v}°`,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        },
      ]}
    >
      <ChartsGrid horizontal />
      <FlowMapLayer hover={hover} onHoverChange={setHover} />
      <ChartsXAxis />
      <ChartsYAxis />
      <text x={width / 2} y={38} textAnchor="middle" fontSize={22} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={width / 2} y={64} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        {subtitle}
      </text>
    </ChartsContainer>
  );
}
