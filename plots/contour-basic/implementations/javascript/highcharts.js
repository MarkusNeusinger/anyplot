// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-25

const t = window.ANYPLOT_TOKENS;

// --- Data (deterministic elevation field with two Gaussian peaks) -----------
const N = 80;
const xMin = -5, xMax = 5, yMin = -4, yMax = 4;
const xs = Array.from({ length: N }, (_, i) => xMin + (xMax - xMin) * i / (N - 1));
const ys = Array.from({ length: N }, (_, i) => yMin + (yMax - yMin) * i / (N - 1));

function rawElev(x, y) {
    const p1 = Math.exp(-((x - 1.2) ** 2 + (y - 0.8) ** 2) / 4);
    const p2 = 0.70 * Math.exp(-((x + 1.8) ** 2 + (y + 0.6) ** 2) / 5);
    const p3 = 0.42 * Math.exp(-(((x - 0.3) ** 2) / 6 + ((y - 2.2) ** 2) / 2));
    return p1 + p2 + p3;
}

const grid = [];
let zMin = Infinity, zMax = -Infinity;
for (let i = 0; i < N; i++) {
    grid[i] = [];
    for (let j = 0; j < N; j++) {
        const z = 100 + 900 * rawElev(xs[i], ys[j]);
        grid[i][j] = z;
        if (z < zMin) zMin = z;
        if (z > zMax) zMax = z;
    }
}

const NUM_LEVELS = 10;
const levels = Array.from({ length: NUM_LEVELS }, (_, k) =>
    zMin + (k + 0.5) * (zMax - zMin) / NUM_LEVELS
);

// Color interpolation: Imprint seq (#009E73 → #4467A3)
function lerpColor(c1, c2, tt) {
    const parse = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const [r1, g1, b1] = parse(c1);
    const [r2, g2, b2] = parse(c2);
    return '#' + [r1 + tt * (r2 - r1), g1 + tt * (g2 - g1), b1 + tt * (b2 - b1)]
        .map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
}

// Marching squares: return list of [[x1,y1],[x2,y2]] segment pairs
function contourSegments(level) {
    const segs = [];
    for (let i = 0; i < N - 1; i++) {
        for (let j = 0; j < N - 1; j++) {
            const a = grid[i][j],     b = grid[i + 1][j];
            const c = grid[i + 1][j + 1], d = grid[i][j + 1];
            const code = (a >= level ? 1 : 0) | (b >= level ? 2 : 0) |
                         (c >= level ? 4 : 0) | (d >= level ? 8 : 0);
            if (code === 0 || code === 15) continue;

            function ep(x1, y1, v1, x2, y2, v2) {
                const s = (level - v1) / (v2 - v1);
                return [x1 + s * (x2 - x1), y1 + s * (y2 - y1)];
            }

            const eAB = ep(xs[i], ys[j], a, xs[i + 1], ys[j], b);
            const eBC = ep(xs[i + 1], ys[j], b, xs[i + 1], ys[j + 1], c);
            const eCD = ep(xs[i + 1], ys[j + 1], c, xs[i], ys[j + 1], d);
            const eDA = ep(xs[i], ys[j + 1], d, xs[i], ys[j], a);

            const lookup = {
                1: [[eDA, eAB]], 14: [[eDA, eAB]],
                2: [[eAB, eBC]], 13: [[eAB, eBC]],
                3: [[eDA, eBC]], 12: [[eDA, eBC]],
                4: [[eBC, eCD]], 11: [[eBC, eCD]],
                6: [[eAB, eCD]],  9: [[eAB, eCD]],
                7: [[eDA, eCD]],  8: [[eDA, eCD]],
                5: [[eDA, eAB], [eBC, eCD]],
                10: [[eDA, eCD], [eAB, eBC]],
            }[code];

            if (lookup) segs.push(...lookup);
        }
    }
    return segs;
}

// Dummy series (empty data) just to populate the legend
const legendSeries = levels.map((level, k) => ({
    type: 'line',
    name: Math.round(level) + ' m',
    color: lerpColor(t.seq[0], t.seq[1], k / (NUM_LEVELS - 1)),
    data: [],
    lineWidth: 2,
    marker: { enabled: false },
    showInLegend: true,
    enableMouseTracking: false,
}));

// --- Chart ------------------------------------------------------------------
const chart = Highcharts.chart('container', {
    chart: {
        backgroundColor: 'transparent',
        animation: false,
        style: { fontFamily: 'inherit' },
    },
    credits: { enabled: false },
    title: {
        text: 'contour-basic · javascript · highcharts · anyplot.ai',
        style: { color: t.ink, fontSize: '22px', fontWeight: '600' },
    },
    xAxis: {
        min: xMin,
        max: xMax,
        title: { text: 'X (km)', style: { color: t.inkSoft, fontSize: '16px' } },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
    },
    yAxis: {
        min: yMin,
        max: yMax,
        title: { text: 'Y (km)', style: { color: t.inkSoft, fontSize: '16px' } },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
    },
    legend: {
        title: { text: 'Elevation', style: { color: t.inkSoft, fontSize: '13px' } },
        itemStyle: { color: t.inkSoft, fontSize: '13px' },
        itemHoverStyle: { color: t.ink },
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
    },
    tooltip: { enabled: false },
    plotOptions: {
        series: { animation: false },
    },
    series: legendSeries,
});

// --- Draw contour lines via SVG renderer ------------------------------------
// Clip to the plot area so lines don't overflow axes/title
const clipRect = chart.renderer.clipRect(
    chart.plotLeft, chart.plotTop, chart.plotWidth, chart.plotHeight
);
const contourGroup = chart.renderer.g('contour-lines').clip(clipRect).add();

levels.forEach((level, k) => {
    const color = lerpColor(t.seq[0], t.seq[1], k / (NUM_LEVELS - 1));
    const segs = contourSegments(level);

    segs.forEach(([p1, p2]) => {
        const px1 = chart.xAxis[0].toPixels(p1[0]);
        const py1 = chart.yAxis[0].toPixels(p1[1]);
        const px2 = chart.xAxis[0].toPixels(p2[0]);
        const py2 = chart.yAxis[0].toPixels(p2[1]);

        chart.renderer.path(['M', px1, py1, 'L', px2, py2])
            .attr({ stroke: color, 'stroke-width': 1.5, zIndex: 5 })
            .add(contourGroup);
    });
});
