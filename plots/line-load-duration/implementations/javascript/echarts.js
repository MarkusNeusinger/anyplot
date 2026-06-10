// anyplot.ai
// line-load-duration: Load Duration Curve for Energy Systems
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-10

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG random number generator (seed 42)
let _s = 42;
function rnd() {
    _s = (Math.imul(_s, 1664525) + 1013904223) >>> 0;
    return _s / 4294967295;
}

// Synthetic annual hourly load: seasonal + daily patterns + noise
const raw = Array.from({length: 8760}, function(_, h) {
    const seasonal = 250 * Math.cos((Math.floor(h / 24) / 365) * 2 * Math.PI);
    const daily    =  90 * Math.sin(((h % 24 - 3) / 24) * 2 * Math.PI);
    return Math.max(380, 790 + seasonal + daily + (rnd() - 0.5) * 190);
});

// Sort descending → load duration curve
raw.sort(function(a, b) { return b - a; });
const load = raw.map(function(v) { return Math.round(v); });

// Total annual energy (MWh — one value per hour)
const totalMWh = load.reduce(function(s, v) { return s + v; }, 0);
const totalTWh = (totalMWh / 1e6).toFixed(2);

// Region boundaries where load crosses generation capacity thresholds
const PEAK_CAP = 900;   // MW — peaking plant threshold
const BASE_CAP = 600;   // MW — base-load plant threshold
const peakEnd  = load.findIndex(function(v) { return v < PEAK_CAP; });
const interEnd = load.findIndex(function(v) { return v < BASE_CAP; });

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
    animation: false,
    color: t.palette,
    backgroundColor: "transparent",

    title: {
        text: "line-load-duration · javascript · echarts · anyplot.ai",
        left: "center",
        top: 22,
        textStyle: { color: t.ink, fontSize: 22, fontWeight: "500" }
    },

    grid: { left: 105, right: 185, top: 88, bottom: 88 },

    xAxis: {
        type: "value",
        name: "Duration (hours per year)",
        nameLocation: "middle",
        nameGap: 48,
        min: 0,
        max: 8760,
        interval: 1000,
        nameTextStyle: { color: t.inkSoft, fontSize: 16 },
        axisLabel:  { color: t.inkSoft, fontSize: 13 },
        axisLine:   { lineStyle: { color: t.inkSoft } },
        axisTick:   { show: false },
        splitLine:  { show: false },
    },

    yAxis: {
        type: "value",
        name: "Load (MW)",
        nameLocation: "middle",
        nameGap: 65,
        min: 300,
        max: 1350,
        nameTextStyle: { color: t.inkSoft, fontSize: 16 },
        axisLabel:  { color: t.inkSoft, fontSize: 13 },
        axisLine:   { lineStyle: { color: t.inkSoft } },
        axisTick:   { show: false },
        splitLine:  { lineStyle: { color: t.grid, width: 1 } },
    },

    series: [{
        type: "line",
        data: load.map(function(v, i) { return [i, v]; }),
        showSymbol: false,
        lineStyle: { color: t.palette[0], width: 3 },

        markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { type: "dashed", color: t.inkSoft, width: 1.5 },
            label: {
                show: true,
                position: "end",
                fontSize: 12,
                color: t.inkSoft,
                backgroundColor: t.elevatedBg,
                padding: [3, 7],
                borderRadius: 2,
            },
            data: [
                { yAxis: PEAK_CAP, label: { formatter: "Intermediate cap: " + PEAK_CAP + " MW" } },
                { yAxis: BASE_CAP, label: { formatter: "Base cap: "         + BASE_CAP + " MW" } },
            ]
        },

        markArea: {
            silent: true,
            data: [
                [
                    { xAxis: 0,       itemStyle: { color: "rgba(174,48,48,0.12)"  } },
                    { xAxis: peakEnd }
                ],
                [
                    { xAxis: peakEnd,  itemStyle: { color: "rgba(189,130,51,0.11)" } },
                    { xAxis: interEnd }
                ],
                [
                    { xAxis: interEnd, itemStyle: { color: "rgba(68,103,163,0.13)" } },
                    { xAxis: 8760 }
                ],
            ]
        },
    }],

    graphic: [
        {
            type: "text",
            left: "9%",
            top: "48%",
            style: { text: "Peak Load",    fontSize: 15, fontWeight: "bold", fill: "rgba(174,48,48,0.85)"  }
        },
        {
            type: "text",
            left: "38%",
            top: "58%",
            style: { text: "Intermediate", fontSize: 15, fontWeight: "bold", fill: "rgba(189,130,51,0.85)" }
        },
        {
            type: "text",
            left: "73%",
            top: "73%",
            style: { text: "Base Load",    fontSize: 15, fontWeight: "bold", fill: "rgba(68,103,163,0.85)" }
        },
        {
            type: "text",
            left: "56%",
            top: "78%",
            style: { text: "Total annual energy: " + totalTWh + " TWh", fontSize: 14, fill: t.inkSoft }
        },
    ],
});
