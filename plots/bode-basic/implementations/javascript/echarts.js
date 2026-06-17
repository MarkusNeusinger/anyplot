// anyplot.ai
// bode-basic: Bode Plot for Frequency Response
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-17
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Open-loop transfer function: G(f) = K / ((1 + jf/f1)(1 + jf/f2)(1 + jf/f3))
// Three poles at f1=10 Hz, f2=100 Hz, f3=1000 Hz; DC gain K=30 (~29.5 dB)
const K_tf = 30, pole1 = 10, pole2 = 100, pole3 = 1000;
const N = 600;
const magData = [], phaseData = [];

for (let i = 0; i < N; i++) {
    const f = Math.pow(10, -1 + 5 * i / (N - 1));
    const r1 = f / pole1, r2 = f / pole2, r3 = f / pole3;
    const magLin = K_tf / (Math.sqrt(1 + r1 * r1) * Math.sqrt(1 + r2 * r2) * Math.sqrt(1 + r3 * r3));
    const magDb  = 20 * Math.log10(magLin);
    const phase  = -(Math.atan(r1) + Math.atan(r2) + Math.atan(r3)) * 180 / Math.PI;
    magData.push([f, +magDb.toFixed(3)]);
    phaseData.push([f, +phase.toFixed(3)]);
}

// Interpolate gain crossover (|G| = 0 dB) and phase crossover (phase = -180°)
let gcFreq = null, gcPhase = null, pcFreq = null, pcMagDb = null;
for (let i = 0; i < N - 1; i++) {
    if (magData[i][1] >= 0 && magData[i + 1][1] < 0 && gcFreq === null) {
        const a = -magData[i][1] / (magData[i + 1][1] - magData[i][1]);
        gcFreq  = Math.pow(10, Math.log10(magData[i][0]) + a * Math.log10(magData[i + 1][0] / magData[i][0]));
        gcPhase = phaseData[i][1] + a * (phaseData[i + 1][1] - phaseData[i][1]);
    }
    if (phaseData[i][1] >= -180 && phaseData[i + 1][1] < -180 && pcFreq === null) {
        const a = (-180 - phaseData[i][1]) / (phaseData[i + 1][1] - phaseData[i][1]);
        pcFreq  = Math.pow(10, Math.log10(phaseData[i][0]) + a * Math.log10(phaseData[i + 1][0] / phaseData[i][0]));
        pcMagDb = magData[i][1] + a * (magData[i + 1][1] - magData[i][1]);
    }
}

const gainMarginDb   = pcMagDb  !== null ? +(-pcMagDb).toFixed(1)     : null;
const phaseMarginDeg = gcPhase  !== null ? +(180 + gcPhase).toFixed(1) : null;

const chart = echarts.init(document.getElementById("container"));

const LAVENDER = t.palette[1];
const BLUE     = t.palette[2];
const RED      = t.palette[4];

chart.setOption({
    animation: false,
    color: t.palette,
    backgroundColor: "transparent",

    title: {
        text: "bode-basic · javascript · echarts · anyplot.ai",
        left: "center",
        top: 16,
        textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" }
    },

    grid: [
        { left: 95, right: 55, top: 65,  height: "38%" },
        { left: 95, right: 55, bottom: 68, height: "29%" }
    ],

    xAxis: [
        {
            gridIndex: 0, type: "log", min: 0.1, max: 10000,
            axisLabel: { show: false },
            axisLine: { lineStyle: { color: t.inkSoft } },
            axisTick: { lineStyle: { color: t.inkSoft } },
            minorTick: { show: true, splitNumber: 9, lineStyle: { color: t.grid } },
            splitLine: { lineStyle: { color: t.grid, width: 1 } },
            minorSplitLine: { show: true, lineStyle: { color: t.grid, width: 0.5 } }
        },
        {
            gridIndex: 1, type: "log", min: 0.1, max: 10000,
            name: "Frequency  (Hz)",
            nameLocation: "center", nameGap: 44,
            nameTextStyle: { color: t.inkSoft, fontSize: 14 },
            axisLabel: {
                color: t.inkSoft, fontSize: 13,
                formatter: (v) => ({ 0.1: "0.1", 1: "1", 10: "10", 100: "100", 1000: "1k", 10000: "10k" }[v] || "")
            },
            axisLine: { lineStyle: { color: t.inkSoft } },
            axisTick: { lineStyle: { color: t.inkSoft } },
            minorTick: { show: true, splitNumber: 9, lineStyle: { color: t.grid } },
            splitLine: { lineStyle: { color: t.grid, width: 1 } },
            minorSplitLine: { show: true, lineStyle: { color: t.grid, width: 0.5 } }
        }
    ],

    yAxis: [
        {
            gridIndex: 0, type: "value", min: -70, max: 40, interval: 20,
            name: "Magnitude  (dB)",
            nameLocation: "center", nameGap: 60,
            nameTextStyle: { color: t.inkSoft, fontSize: 14 },
            axisLabel: { color: t.inkSoft, fontSize: 13 },
            axisLine: { lineStyle: { color: t.inkSoft } },
            axisTick: { lineStyle: { color: t.inkSoft } },
            splitLine: { lineStyle: { color: t.grid, width: 1 } }
        },
        {
            gridIndex: 1, type: "value", min: -270, max: 0, interval: 90,
            name: "Phase  (°)",
            nameLocation: "center", nameGap: 60,
            nameTextStyle: { color: t.inkSoft, fontSize: 14 },
            axisLabel: { color: t.inkSoft, fontSize: 13, formatter: (v) => v + "°" },
            axisLine: { lineStyle: { color: t.inkSoft } },
            axisTick: { lineStyle: { color: t.inkSoft } },
            splitLine: { lineStyle: { color: t.grid, width: 1 } }
        }
    ],

    series: [
        // Magnitude response — Imprint palette position 1 (brand green)
        {
            name: "Magnitude",
            type: "line",
            xAxisIndex: 0, yAxisIndex: 0,
            data: magData,
            lineStyle: { color: t.palette[0], width: 3 },
            symbol: "none",
            markLine: {
                silent: true,
                symbol: ["none", "none"],
                data: [
                    {
                        yAxis: 0,
                        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5, opacity: 0.6 },
                        label: { show: true, position: "insideEndTop",
                                 formatter: "0 dB", color: t.inkSoft, fontSize: 12 }
                    },
                    ...(gcFreq !== null ? [{
                        xAxis: gcFreq,
                        lineStyle: { color: LAVENDER, type: "dashed", width: 1.5, opacity: 0.8 },
                        label: { show: false }
                    }] : []),
                    ...(pcFreq !== null ? [{
                        xAxis: pcFreq,
                        lineStyle: { color: RED, type: "dashed", width: 1.5, opacity: 0.8 },
                        label: { show: false }
                    }] : [])
                ]
            },
            markPoint: {
                symbol: "circle",
                symbolSize: 12,
                data: pcFreq !== null ? [{
                    coord: [pcFreq, pcMagDb],
                    itemStyle: { color: RED, borderColor: t.pageBg, borderWidth: 2 },
                    label: {
                        show: true,
                        position: "top",
                        distance: 10,
                        formatter: `GM = ${gainMarginDb} dB`,
                        color: RED,
                        fontSize: 14,
                        fontWeight: "bold",
                        backgroundColor: t.elevatedBg,
                        padding: [4, 8],
                        borderRadius: 4
                    }
                }] : []
            }
        },
        // Phase response — Imprint palette position 3 (blue)
        {
            name: "Phase",
            type: "line",
            xAxisIndex: 1, yAxisIndex: 1,
            data: phaseData,
            lineStyle: { color: BLUE, width: 3 },
            symbol: "none",
            markLine: {
                silent: true,
                symbol: ["none", "none"],
                data: [
                    {
                        yAxis: -180,
                        lineStyle: { color: t.inkSoft, type: "dashed", width: 1.5, opacity: 0.6 },
                        label: { show: true, position: "insideEndTop",
                                 formatter: "−180°", color: t.inkSoft, fontSize: 12 }
                    },
                    ...(gcFreq !== null ? [{
                        xAxis: gcFreq,
                        lineStyle: { color: LAVENDER, type: "dashed", width: 1.5, opacity: 0.8 },
                        label: { show: false }
                    }] : []),
                    ...(pcFreq !== null ? [{
                        xAxis: pcFreq,
                        lineStyle: { color: RED, type: "dashed", width: 1.5, opacity: 0.8 },
                        label: { show: false }
                    }] : [])
                ]
            },
            markPoint: {
                symbol: "circle",
                symbolSize: 12,
                data: gcFreq !== null ? [{
                    coord: [gcFreq, gcPhase],
                    itemStyle: { color: LAVENDER, borderColor: t.pageBg, borderWidth: 2 },
                    label: {
                        show: true,
                        position: "top",
                        distance: 10,
                        formatter: `PM = ${phaseMarginDeg}°`,
                        color: LAVENDER,
                        fontSize: 14,
                        fontWeight: "bold",
                        backgroundColor: t.elevatedBg,
                        padding: [4, 8],
                        borderRadius: 4
                    }
                }] : []
            }
        }
    ]
});
