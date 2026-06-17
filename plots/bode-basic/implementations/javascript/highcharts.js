// anyplot.ai
// bode-basic: Bode Plot for Frequency Response
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-17

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Transfer function data --------------------------------------------------
// Three-pole low-pass: H(s) = K / ((s/w1+1)(s/w2+1)(s/w3+1))
// K=10, pole frequencies: f1=1Hz, f2=10Hz, f3=100Hz
// Gives ~54deg phase margin and ~21dB gain margin — a well-tuned stable system
const K = 10, f1 = 1, f2 = 10, f3 = 100;
const N = 300, fMin = 0.05, fMax = 5000;
const magData = [], phaseData = [];

for (let i = 0; i < N; i++) {
    const f = fMin * Math.pow(10, i * Math.log10(fMax / fMin) / (N - 1));
    const denom = Math.sqrt(1 + (f / f1) ** 2) * Math.sqrt(1 + (f / f2) ** 2) * Math.sqrt(1 + (f / f3) ** 2);
    const magDb = 20 * Math.log10(K / denom);
    const phaseDeg = -(Math.atan(f / f1) + Math.atan(f / f2) + Math.atan(f / f3)) * (180 / Math.PI);
    magData.push([f, +magDb.toFixed(4)]);
    phaseData.push([f, +phaseDeg.toFixed(4)]);
}

// --- Stability margin computation (log-linear interpolation) -----------------
// Gain crossover: first frequency where magnitude crosses 0 dB from above
let fGc = null, phaseAtGc = null;
for (let i = 1; i < magData.length; i++) {
    if (magData[i - 1][1] >= 0 && magData[i][1] < 0) {
        const r = magData[i - 1][1] / (magData[i - 1][1] - magData[i][1]);
        fGc = magData[i - 1][0] * Math.pow(magData[i][0] / magData[i - 1][0], r);
        phaseAtGc = phaseData[i - 1][1] + (phaseData[i][1] - phaseData[i - 1][1]) * r;
        break;
    }
}

// Phase crossover: first frequency where phase crosses -180 degrees
let fPc = null, magAtPc = null;
for (let i = 1; i < phaseData.length; i++) {
    if (phaseData[i - 1][1] >= -180 && phaseData[i][1] < -180) {
        const r = (-180 - phaseData[i - 1][1]) / (phaseData[i][1] - phaseData[i - 1][1]);
        fPc = phaseData[i - 1][0] * Math.pow(phaseData[i][0] / phaseData[i - 1][0], r);
        magAtPc = magData[i - 1][1] + (magData[i][1] - magData[i - 1][1]) * r;
        break;
    }
}

const phaseMarginStr = phaseAtGc !== null ? (180 + phaseAtGc).toFixed(1) : null;
const gainMarginStr  = magAtPc   !== null ? (-magAtPc).toFixed(1) : null;

// Vertical marker lines at crossover frequencies
const xPlotLines = [];
if (fGc !== null) {
    xPlotLines.push({
        value: fGc,
        color: t.palette[3],       // ochre — gain crossover
        dashStyle: 'ShortDash',
        width: 1.5,
        zIndex: 3,
        label: {
            text: 'PM = ' + phaseMarginStr + '°',
            style: { color: t.palette[3], fontSize: '12px', fontWeight: '600' },
            rotation: 0,
            verticalAlign: 'middle',
            x: 5
        }
    });
}
if (fPc !== null) {
    xPlotLines.push({
        value: fPc,
        color: t.palette[4],       // matte red — phase crossover
        dashStyle: 'ShortDash',
        width: 1.5,
        zIndex: 3,
        label: {
            text: 'GM = ' + gainMarginStr + ' dB',
            style: { color: t.palette[4], fontSize: '12px', fontWeight: '600' },
            rotation: 0,
            verticalAlign: 'middle',
            x: 5
        }
    });
}

// --- Chart ------------------------------------------------------------------
Highcharts.chart('container', {
    chart: {
        type: 'line',
        backgroundColor: 'transparent',
        animation: false,
        style: { fontFamily: 'inherit' },
        marginLeft: 85,
        marginRight: 40,
        marginBottom: 70,
        marginTop: 65
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: 'bode-basic · javascript · highcharts · anyplot.ai',
        style: { color: t.ink, fontSize: '22px', fontWeight: '600' }
    },
    subtitle: {
        text: 'Three-pole system — K = 10,  f₁ = 1 Hz,  f₂ = 10 Hz,  f₃ = 100 Hz',
        style: { color: t.inkSoft, fontSize: '13px' }
    },
    legend: {
        enabled: true,
        verticalAlign: 'top',
        align: 'right',
        y: 6,
        itemStyle: { color: t.inkSoft, fontSize: '14px' },
        itemHoverStyle: { color: t.ink }
    },
    xAxis: {
        type: 'logarithmic',
        min: fMin,
        max: fMax,
        title: {
            text: 'Frequency (Hz)',
            style: { color: t.inkSoft, fontSize: '16px' }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
        plotLines: xPlotLines
    },
    yAxis: [
        {
            // Top panel — Magnitude
            title: {
                text: 'Magnitude (dB)',
                style: { color: t.inkSoft, fontSize: '16px' }
            },
            top: '3%',
            height: '43%',
            offset: 0,
            lineColor: t.inkSoft,
            gridLineColor: t.grid,
            labels: { style: { color: t.inkSoft, fontSize: '14px' } },
            plotLines: [{
                value: 0,
                color: t.inkSoft,
                dashStyle: 'Dot',
                width: 1.5,
                zIndex: 2,
                label: {
                    text: '0 dB',
                    style: { color: t.inkSoft, fontSize: '12px' },
                    align: 'right',
                    x: -6,
                    y: -6
                }
            }]
        },
        {
            // Bottom panel — Phase
            title: {
                text: 'Phase (°)',
                style: { color: t.inkSoft, fontSize: '16px' }
            },
            top: '54%',
            height: '43%',
            offset: 0,
            lineColor: t.inkSoft,
            gridLineColor: t.grid,
            labels: { style: { color: t.inkSoft, fontSize: '14px' } },
            plotLines: [{
                value: -180,
                color: t.inkSoft,
                dashStyle: 'Dot',
                width: 1.5,
                zIndex: 2,
                label: {
                    text: '−180°',
                    style: { color: t.inkSoft, fontSize: '12px' },
                    align: 'right',
                    x: -6,
                    y: -6
                }
            }]
        }
    ],
    plotOptions: {
        series: {
            animation: false,
            lineWidth: 2.5,
            marker: { enabled: false }
        }
    },
    series: [
        {
            name: 'Magnitude',
            data: magData,
            yAxis: 0,
            color: t.palette[0]    // #009E73 brand green — always first series
        },
        {
            name: 'Phase',
            data: phaseData,
            yAxis: 1,
            color: t.palette[2]    // #4467A3 blue
        }
    ]
});
