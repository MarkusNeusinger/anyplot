// anyplot.ai
// line-stress-strain: Engineering Stress-Strain Curve
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-21

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Mild steel stress-strain data (deterministic)
// Regions: elastic (0–0.00125), yield plateau (0.00125–0.015), strain hardening (0.015–0.22), necking (0.22–0.295)
const curve = [
    // Elastic region — linear, E = 200,000 MPa
    [0.0000,   0], [0.0002,  40], [0.0004,  80], [0.0006, 120],
    [0.0008, 160], [0.0010, 200], [0.00125, 250],
    // Yield plateau (Lüders bands) — mild steel characteristic
    [0.0015, 248], [0.0020, 245], [0.0040, 245],
    [0.0060, 246], [0.0080, 247], [0.0100, 248],
    [0.0120, 249], [0.0150, 250],
    // Strain hardening — stress rises from 250 to 400 MPa
    [0.0200, 255], [0.0300, 268], [0.0450, 285],
    [0.0600, 300], [0.0800, 318], [0.1000, 334],
    [0.1200, 348], [0.1500, 368], [0.1800, 385],
    [0.2000, 395], [0.2200, 400],
    // Necking — stress falls to fracture
    [0.2400, 390], [0.2600, 370], [0.2800, 342], [0.2950, 310],
];

// 0.2% offset line — parallel to elastic slope, offset by 0.002 strain
// Intersection with yield plateau at strain ≈ 0.00325 (stress = 250 MPa)
const offsetLine = [
    [0.0020,   0],
    [0.0050, 600],  // clipped by yAxis max; shows the full slope for reference
];

// Key mechanical property markers
const yieldX = 0.00325;
const yieldY = 250;
const utsX   = 0.2200;
const utsY   = 400;
const fracX  = 0.2950;
const fracY  = 310;

let _annotated = false;

Highcharts.chart('container', {
    chart: {
        type: 'line',
        backgroundColor: 'transparent',
        animation: false,
        style: { fontFamily: 'inherit' },
        marginRight: 40,
        events: {
            render: function () {
                if (_annotated) return;
                _annotated = true;

                const ch   = this;
                const xAx  = ch.xAxis[0];
                const yAx  = ch.yAxis[0];
                const toX  = (v) => xAx.toPixels(v, false);
                const toY  = (v) => yAx.toPixels(v, false);
                const soft = { color: t.inkSoft, fontSize: '12px', fontStyle: 'italic' };

                // Region labels — positioned above plot area (y = plotTop - 10)
                const labelY = ch.plotTop - 12;

                // Elastic region label (narrow — place just right of y-axis)
                ch.renderer.text('Elastic', toX(0.0006), labelY)
                    .css(soft).attr({ align: 'center', zIndex: 6 }).add();

                // Strain Hardening label
                ch.renderer.text('Strain Hardening', toX(0.11), labelY)
                    .css(soft).attr({ align: 'center', zIndex: 6 }).add();

                // Necking label
                ch.renderer.text('Necking', toX(0.257), labelY)
                    .css(soft).attr({ align: 'center', zIndex: 6 }).add();

                // Young's modulus annotation near elastic slope
                ch.renderer.text('E = 200 GPa', toX(0.0003), toY(175))
                    .css({ color: t.inkSoft, fontSize: '11px' })
                    .attr({ align: 'left', zIndex: 6 }).add();

                // Vertical boundary lines at yield plateau start and UTS
                [0.00125, 0.22].forEach(function (xVal) {
                    const px = toX(xVal);
                    ch.renderer.path(['M', px, toY(0), 'L', px, ch.plotTop])
                        .attr({
                            stroke: t.grid,
                            'stroke-width': 1,
                            'stroke-dasharray': '5,4',
                            zIndex: 3,
                        }).add();
                });

                // Key point markers — circle + label
                const points = [
                    { x: yieldX, y: yieldY, label: 'Yield Point\n250 MPa', ax: 12, ay: -18 },
                    { x: utsX,   y: utsY,   label: 'UTS\n400 MPa',          ax: 12, ay: -18 },
                    { x: fracX,  y: fracY,  label: 'Fracture\n310 MPa',      ax: -10, ay: -18 },
                ];

                points.forEach(function (p) {
                    const px = toX(p.x);
                    const py = toY(p.y);

                    // Circle marker
                    ch.renderer.circle(px, py, 6)
                        .attr({
                            fill: t.palette[3],  // ochre — distinct from main curve
                            stroke: t.pageBg,
                            'stroke-width': 1.5,
                            zIndex: 7,
                        }).add();

                    // Text label (two lines via two separate text calls)
                    const lines = p.label.split('\n');
                    const align = p.ax > 0 ? 'left' : 'right';
                    lines.forEach(function (line, i) {
                        ch.renderer.text(line, px + p.ax, py + p.ay + i * 15)
                            .css({ color: t.ink, fontSize: '12px', fontWeight: i === 0 ? 'bold' : 'normal' })
                            .attr({ align: align, zIndex: 7 }).add();
                    });
                });
            },
        },
    },

    credits: { enabled: false },
    colors: t.palette,

    title: {
        text: 'line-stress-strain · javascript · highcharts · anyplot.ai',
        style: { color: t.ink, fontSize: '22px', fontWeight: '600' },
    },

    xAxis: {
        title: {
            text: 'Engineering Strain, ε (dimensionless)',
            style: { color: t.inkSoft, fontSize: '16px' },
            margin: 12,
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: '14px' }, format: '{value:.2f}' },
        min: 0,
        max: 0.32,
        tickInterval: 0.05,
        startOnTick: true,
    },

    yAxis: {
        title: {
            text: 'Engineering Stress, σ (MPa)',
            style: { color: t.inkSoft, fontSize: '16px' },
            margin: 12,
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
        min: 0,
        max: 450,
        tickInterval: 50,
        // Reference lines at yield and UTS
        plotLines: [
            {
                value: 250,
                color: t.grid,
                dashStyle: 'ShortDash',
                width: 1,
                zIndex: 2,
                label: {
                    text: 'σₙ = 250 MPa',
                    style: { color: t.inkSoft, fontSize: '11px' },
                    align: 'right',
                    x: -6,
                    y: -4,
                },
            },
            {
                value: 400,
                color: t.grid,
                dashStyle: 'ShortDash',
                width: 1,
                zIndex: 2,
                label: {
                    text: 'UTS = 400 MPa',
                    style: { color: t.inkSoft, fontSize: '11px' },
                    align: 'right',
                    x: -6,
                    y: -4,
                },
            },
        ],
    },

    legend: {
        itemStyle: { color: t.inkSoft, fontSize: '14px' },
        itemHoverStyle: { color: t.ink },
        backgroundColor: t.elevatedBg,
        borderRadius: 4,
        padding: 10,
    },

    tooltip: { enabled: false },

    plotOptions: {
        series: { animation: false },
        line: { enableMouseTracking: false },
    },

    series: [
        {
            name: 'Mild Steel',
            type: 'line',
            data: curve,
            color: t.palette[0],  // brand green #009E73 — first series
            lineWidth: 3,
            marker: { enabled: false },
            zIndex: 5,
        },
        {
            name: '0.2% Offset Line',
            type: 'line',
            data: offsetLine,
            color: t.palette[2],  // blue #4467A3
            lineWidth: 1.5,
            dashStyle: 'ShortDash',
            marker: { enabled: false },
            zIndex: 4,
        },
    ],
});
