// anyplot.ai
// bar-pareto: Pareto Chart with Cumulative Line
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-20

const t = window.ANYPLOT_TOKENS;

// Data — manufacturing defect counts (sorted descending by frequency)
const categories = ['Scratches', 'Dents', 'Cracks', 'Misalignment', 'Discoloration',
    'Warping', 'Incomplete Fill', 'Surface Bubbles', 'Other'];
const counts = [320, 180, 140, 95, 75, 52, 38, 25, 18];
const total = counts.reduce((a, b) => a + b, 0);

// Cumulative percentages at center of each bar (Pareto 80/20 rule)
const cumPct = [];
let running = 0;
for (const c of counts) {
    running += c;
    cumPct.push(parseFloat((running / total * 100).toFixed(1)));
}

// Title sizing — scale down linearly when title exceeds 67-char baseline
const title = 'Manufacturing Defects · bar-pareto · javascript · chartjs · anyplot.ai';
const titleSize = title.length > 67 ? Math.round(22 * 67 / title.length) : 22;

// Mount
const canvas = document.createElement('canvas');
document.getElementById('container').appendChild(canvas);

// Chart
new Chart(canvas, {
    type: 'bar',
    data: {
        labels: categories,
        datasets: [
            {
                type: 'bar',
                label: 'Defect Count',
                data: counts,
                backgroundColor: t.palette[0],   // #009E73 Imprint brand green
                borderWidth: 0,
                yAxisID: 'y',
                order: 2,
            },
            {
                type: 'line',
                label: 'Cumulative %',
                data: cumPct,
                borderColor: t.palette[1],        // #C475FD lavender
                backgroundColor: 'transparent',
                borderWidth: 2.5,
                pointRadius: 6,
                pointBackgroundColor: t.palette[1],
                pointBorderColor: t.pageBg,
                pointBorderWidth: 2,
                tension: 0,
                yAxisID: 'y2',
                order: 1,
            },
            {
                type: 'line',
                label: '80% Threshold',
                data: Array(categories.length).fill(80),
                borderColor: t.amber,             // #DDCC77 warning anchor
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [10, 5],
                pointRadius: 0,
                tension: 0,
                yAxisID: 'y2',
                order: 3,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            title: {
                display: true,
                text: title,
                color: t.ink,
                font: { size: titleSize, weight: 'bold' },
                padding: { top: 8, bottom: 20 },
            },
            legend: {
                labels: { color: t.inkSoft, font: { size: 14 }, boxWidth: 22, padding: 16 },
            },
        },
        scales: {
            x: {
                ticks: {
                    color: t.inkSoft,
                    font: { size: 13 },
                    maxRotation: 30,
                    minRotation: 0,
                },
                grid: { color: t.grid },
                title: {
                    display: true,
                    text: 'Defect Category',
                    color: t.ink,
                    font: { size: 14 },
                    padding: { top: 6 },
                },
            },
            y: {
                beginAtZero: true,
                ticks: { color: t.inkSoft, font: { size: 14 } },
                grid: { color: t.grid },
                title: {
                    display: true,
                    text: 'Defect Count',
                    color: t.ink,
                    font: { size: 14 },
                },
            },
            y2: {
                type: 'linear',
                position: 'right',
                min: 0,
                max: 100,
                ticks: {
                    color: t.inkSoft,
                    font: { size: 14 },
                    stepSize: 20,
                    callback: (v) => v + '%',
                },
                grid: { drawOnChartArea: false },
                title: {
                    display: true,
                    text: 'Cumulative Percentage',
                    color: t.ink,
                    font: { size: 14 },
                },
            },
        },
    },
    plugins: [{
        id: 'bg',
        beforeDraw(chart) {
            const ctx = chart.ctx;
            ctx.save();
            ctx.fillStyle = t.pageBg;
            ctx.fillRect(0, 0, chart.width, chart.height);
            ctx.restore();
        },
    }],
});
