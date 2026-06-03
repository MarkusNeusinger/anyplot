// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-03
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Inline RGB components for gradient stops (palette[0] = #009E73)
const waveColor = t.palette[0];
const wR = parseInt(waveColor.slice(1, 3), 16);
const wG = parseInt(waveColor.slice(3, 5), 16);
const wB = parseInt(waveColor.slice(5, 7), 16);

// Synthetic speech-like waveform: 5000 samples over 1 second
const N = 5000;
const duration = 1.0;
const rawData = [];

for (let i = 0; i < N; i++) {
    const time = (i / N) * duration;
    // Three Gaussian syllabic envelopes at 0.14 s, 0.47 s, 0.81 s
    const env1 = Math.exp(-32 * Math.pow(time - 0.14, 2));
    const env2 = Math.exp(-28 * Math.pow(time - 0.47, 2));
    const env3 = Math.exp(-38 * Math.pow(time - 0.81, 2));
    const envelope = (env1 + 0.88 * env2 + 0.72 * env3) * 0.85;
    // 175 Hz fundamental with four harmonics
    const f0 = 175;
    const carrier =
        0.48 * Math.sin(2 * Math.PI * f0 * time) +
        0.26 * Math.sin(2 * Math.PI * 2 * f0 * time) +
        0.14 * Math.sin(2 * Math.PI * 3 * f0 * time) +
        0.09 * Math.sin(2 * Math.PI * 4 * f0 * time) +
        0.03 * Math.sin(2 * Math.PI * 5 * f0 * time);
    rawData.push(Math.max(-1, Math.min(1, carrier * envelope)));
}

// Downsample to 300-bin min/max envelope to avoid aliasing
const BINS = 300;
const binSize = Math.floor(N / BINS);
const maxEnv = [], minEnv = [];
for (let b = 0; b < BINS; b++) {
    const start = b * binSize;
    const end = Math.min(start + binSize, N);
    const tCenter = ((start + end) / 2 / N) * duration;
    let bMax = -Infinity, bMin = Infinity;
    for (let k = start; k < end; k++) {
        if (rawData[k] > bMax) bMax = rawData[k];
        if (rawData[k] < bMin) bMin = rawData[k];
    }
    maxEnv.push([tCenter, bMax]);
    minEnv.push([tCenter, bMin]);
}

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
    animation: false,
    backgroundColor: "transparent",
    title: {
        text: "waveform-audio · javascript · echarts · anyplot.ai",
        left: "center",
        top: 18,
        textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" }
    },
    grid: { left: 95, right: 50, top: 80, bottom: 85, containLabel: true },
    xAxis: {
        type: "value",
        name: "Time (s)",
        nameLocation: "middle",
        nameGap: 46,
        nameTextStyle: { color: t.inkSoft, fontSize: 18 },
        axisLabel: {
            color: t.inkSoft,
            fontSize: 14,
            formatter: (v) => (v === 0 ? "0" : v.toFixed(2))
        },
        axisLine: { show: true, lineStyle: { color: t.inkSoft } },
        axisTick: { lineStyle: { color: t.inkSoft } },
        splitLine: { show: false },
        min: 0,
        max: 1.0
    },
    yAxis: {
        type: "value",
        name: "Amplitude",
        nameLocation: "middle",
        nameGap: 52,
        nameTextStyle: { color: t.inkSoft, fontSize: 18 },
        axisLabel: {
            color: t.inkSoft,
            fontSize: 14,
            formatter: (v) => (v === 0 ? "0" : v.toFixed(1))
        },
        axisLine: { show: true, lineStyle: { color: t.inkSoft } },
        axisTick: { lineStyle: { color: t.inkSoft } },
        splitLine: { lineStyle: { color: t.grid } },
        min: -1.0,
        max: 1.0
    },
    series: [
        {
            // Upper envelope: max amplitude per bin
            type: "line",
            data: maxEnv,
            symbol: "none",
            smooth: false,
            lineStyle: { color: waveColor, width: 0.8, opacity: 0.9 },
            areaStyle: {
                origin: 0,
                color: {
                    type: "linear",
                    x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [
                        { offset: 0, color: `rgba(${wR},${wG},${wB},0.62)` },
                        { offset: 1, color: `rgba(${wR},${wG},${wB},0.05)` }
                    ]
                }
            },
            markLine: {
                silent: true,
                data: [{ yAxis: 0 }],
                lineStyle: { color: t.inkSoft, width: 1.5, type: "solid", opacity: 0.5 },
                label: { show: false },
                symbol: ["none", "none"]
            },
            markArea: {
                silent: true,
                label: {
                    show: true,
                    position: "insideTop",
                    color: t.inkSoft,
                    fontSize: 12
                },
                itemStyle: {
                    color: `rgba(${wR},${wG},${wB},0.07)`,
                    borderColor: `rgba(${wR},${wG},${wB},0.22)`,
                    borderWidth: 1
                },
                data: [
                    [{ name: "Syllable 1", xAxis: 0.05 }, { xAxis: 0.24 }],
                    [{ name: "Syllable 2", xAxis: 0.36 }, { xAxis: 0.58 }],
                    [{ name: "Syllable 3", xAxis: 0.70 }, { xAxis: 0.92 }]
                ]
            }
        },
        {
            // Lower envelope: min amplitude per bin
            type: "line",
            data: minEnv,
            symbol: "none",
            smooth: false,
            lineStyle: { color: waveColor, width: 0.8, opacity: 0.9 },
            areaStyle: {
                origin: 0,
                color: {
                    type: "linear",
                    x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [
                        { offset: 0, color: `rgba(${wR},${wG},${wB},0.05)` },
                        { offset: 1, color: `rgba(${wR},${wG},${wB},0.62)` }
                    ]
                }
            }
        }
    ]
});
