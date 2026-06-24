// anyplot.ai
// titration-curve: Acid-Base Titration Curve
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-24

const t = window.ANYPLOT_TOKENS;

// Strong acid/strong base titration: 25 mL 0.1 M HCl + 0.1 M NaOH
const C      = 0.1;               // mol/L (both acid and base)
const V_ACID = 25.0;              // mL initial acid volume
const N_ACID = C * V_ACID / 1000; // 0.0025 mol HCl

// Volumes: dense around the equivalence point at 25 mL for a smooth curve
const volumes = [];
for (let i = 0;   i <= 47;  i++) volumes.push(+(i * 0.5).toFixed(1));   // 0–23.5, step 0.5
for (let i = 236; i <= 264; i++) volumes.push(+(i / 10).toFixed(1));    // 23.6–26.4, step 0.1
for (let i = 53;  i <= 100; i++) volumes.push(+(i * 0.5).toFixed(1));   // 26.5–50.0, step 0.5

function calcPH(v) {
    const nBase  = C * v / 1000;
    const totVol = (V_ACID + v) / 1000;
    if (v < 24.999) return -Math.log10((N_ACID - nBase) / totVol);
    if (v > 25.001) return 14 + Math.log10((nBase - N_ACID) / totVol);
    return 7.0; // equivalence point: neutral pH for strong acid/strong base
}

const pHArr         = volumes.map(calcPH);
const titrationData = volumes.map((v, i) => [v, +pHArr[i].toFixed(3)]);

// Central-difference derivative dpH/dV — peaks sharply at the equivalence point
const derivData = [];
for (let i = 1; i < volumes.length - 1; i++) {
    const dphdv = (pHArr[i + 1] - pHArr[i - 1]) / (volumes[i + 1] - volumes[i - 1]);
    derivData.push([volumes[i], +dphdv.toFixed(3)]);
}

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
    animation: false,
    color:           t.palette,
    backgroundColor: "transparent",

    title: {
        text: "titration-curve · javascript · echarts · anyplot.ai",
        left: "center",
        top: 20,
        textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
    },

    legend: {
        data: ["pH", "dpH/dV"],
        top: 62,
        right: 120,
        textStyle: { color: t.inkSoft, fontSize: 14 },
        icon: "line",
    },

    grid: { left: 90, right: 115, top: 105, bottom: 90 },

    xAxis: {
        type: "value",
        name: "Volume of NaOH added (mL)",
        nameLocation: "middle",
        nameGap: 50,
        nameTextStyle: { color: t.inkSoft, fontSize: 14 },
        min: 0,
        max: 50,
        interval: 5,
        axisLabel: { color: t.inkSoft, fontSize: 14 },
        axisLine: { lineStyle: { color: t.inkSoft } },
        axisTick: { show: false },
        splitLine: { show: false },
    },

    yAxis: [
        {
            type: "value",
            name: "pH",
            nameLocation: "middle",
            nameGap: 50,
            nameTextStyle: { color: t.palette[0], fontSize: 14 },
            min: 0,
            max: 14,
            interval: 2,
            axisLabel: { color: t.inkSoft, fontSize: 14 },
            axisLine: { show: true, lineStyle: { color: t.palette[0] } },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: t.grid } },
        },
        {
            type: "value",
            name: "dpH/dV",
            nameLocation: "middle",
            nameGap: 60,
            nameTextStyle: { color: t.palette[1], fontSize: 14 },
            min: 0,
            max: 40,
            interval: 10,
            axisLabel: { color: t.inkSoft, fontSize: 14 },
            axisLine: { show: true, lineStyle: { color: t.palette[1] } },
            axisTick: { show: false },
            splitLine: { show: false },
        },
    ],

    series: [
        {
            name: "pH",
            type: "line",
            yAxisIndex: 0,
            data: titrationData,
            showSymbol: false,
            lineStyle: { color: t.palette[0], width: 3.5 },
            itemStyle: { color: t.palette[0] },
            markLine: {
                silent: true,
                symbol: ["none", "none"],
                lineStyle: { type: "dashed", color: t.inkSoft, width: 1.5 },
                label: {
                    show: true,
                    position: "end",
                    formatter: "EP: 25 mL, pH 7",
                    color: t.inkSoft,
                    fontSize: 13,
                },
                data: [{ xAxis: 25 }],
            },
            markPoint: {
                data: [{
                    coord: [25, 7],
                    symbol: "circle",
                    symbolSize: 14,
                    itemStyle: {
                        color: t.palette[0],
                        borderColor: t.pageBg,
                        borderWidth: 2.5,
                    },
                }],
                label: { show: false },
            },
        },
        {
            name: "dpH/dV",
            type: "line",
            yAxisIndex: 1,
            data: derivData,
            showSymbol: false,
            lineStyle: { color: t.palette[1], width: 2.5, opacity: 0.85 },
            itemStyle: { color: t.palette[1] },
            areaStyle: { color: t.palette[1], opacity: 0.08 },
        },
    ],
});
