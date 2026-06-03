//# anyplot-orientation: landscape
// anyplot.ai
// waveform-audio: Audio Waveform Plot
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-03

const t = window.ANYPLOT_TOKENS;

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

// Synthetic speech-like waveform: 5000 samples over 1 second
const N = 5000;
const duration = 1.0;
const waveData = [];

for (let i = 0; i < N; i++) {
    const time = (i / N) * duration;

    // Three Gaussian envelopes mimicking syllabic bursts at 0.14s, 0.47s, 0.81s
    const env1 = Math.exp(-32 * Math.pow(time - 0.14, 2));
    const env2 = Math.exp(-28 * Math.pow(time - 0.47, 2));
    const env3 = Math.exp(-38 * Math.pow(time - 0.81, 2));
    const envelope = (env1 + 0.88 * env2 + 0.72 * env3) * 0.85;

    // Harmonic carrier at 175 Hz fundamental with four overtones
    const f0 = 175;
    const carrier =
        0.48 * Math.sin(2 * Math.PI * f0 * time) +
        0.26 * Math.sin(2 * Math.PI * 2 * f0 * time) +
        0.14 * Math.sin(2 * Math.PI * 3 * f0 * time) +
        0.09 * Math.sin(2 * Math.PI * 4 * f0 * time) +
        0.03 * Math.sin(2 * Math.PI * 5 * f0 * time);

    waveData.push([time, Math.max(-1, Math.min(1, carrier * envelope))]);
}

const waveColor = t.palette[0];

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
            type: "line",
            data: waveData,
            symbol: "none",
            smooth: false,
            lineStyle: { color: waveColor, width: 1, opacity: 0.9 },
            areaStyle: {
                origin: 0,
                color: {
                    type: "linear",
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [
                        { offset: 0,   color: hexToRgba(waveColor, 0.55) },
                        { offset: 0.5, color: hexToRgba(waveColor, 0.08) },
                        { offset: 1,   color: hexToRgba(waveColor, 0.55) }
                    ]
                }
            },
            markLine: {
                silent: true,
                data: [{ yAxis: 0 }],
                lineStyle: { color: t.inkSoft, width: 1.5, type: "solid", opacity: 0.5 },
                label: { show: false },
                symbol: ["none", "none"]
            }
        }
    ]
});
