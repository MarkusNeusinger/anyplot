// anyplot.ai
// line-reaction-coordinate: Reaction Coordinate Energy Diagram
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (deterministic smooth energy profile via smoothstep) ---
// Single-step exothermic: reactants=50 kJ/mol, TS=120 kJ/mol, products=20 kJ/mol
const energyData = [];
for (let i = 0; i <= 100; i++) {
    let energy;
    if (i <= 40) {
        const s = i / 40;
        energy = 50 + 70 * (3 * s * s - 2 * s * s * s);
    } else {
        const s = (i - 40) / 60;
        energy = 120 - 100 * (3 * s * s - 2 * s * s * s);
    }
    energyData.push([i, parseFloat(energy.toFixed(3))]);
}

// --- Chart ---
Highcharts.chart("container", {
    chart: {
        type: "spline",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        margin: [70, 60, 80, 80],
        events: {
            load: function () {
                const chart = this;
                const renderer = chart.renderer;
                const xA = chart.xAxis[0];
                const yA = chart.yAxis[0];

                // Pixel positions for key energy levels
                const y50  = yA.toPixels(50);
                const y120 = yA.toPixels(120);
                const y20  = yA.toPixels(20);

                // Pixel positions for key x locations
                const xLeft    = xA.toPixels(2);
                const xPeak    = xA.toPixels(40);
                const xRight   = xA.toPixels(88);
                const eaX      = xA.toPixels(13);
                const dhX      = xA.toPixels(74);

                const ink = t.ink;
                const soft = t.inkSoft;
                const lw = 1.5;
                const arrowSize = 6;

                // --- Ea double-headed arrow (reactant level → TS peak) ---
                renderer.path(["M", eaX, y50, "L", eaX, y120])
                    .attr({ stroke: ink, "stroke-width": lw })
                    .add();
                // top arrowhead (pointing up toward TS)
                renderer.path(["M", eaX - arrowSize, y120 + arrowSize * 1.5,
                                "L", eaX, y120,
                                "L", eaX + arrowSize, y120 + arrowSize * 1.5])
                    .attr({ stroke: ink, "stroke-width": lw, fill: "none" })
                    .add();
                // bottom arrowhead (pointing down toward reactant)
                renderer.path(["M", eaX - arrowSize, y50 - arrowSize * 1.5,
                                "L", eaX, y50,
                                "L", eaX + arrowSize, y50 - arrowSize * 1.5])
                    .attr({ stroke: ink, "stroke-width": lw, fill: "none" })
                    .add();
                renderer.text("Ea = 70 kJ/mol", eaX + 9, (y50 + y120) / 2 + 5)
                    .css({ color: ink, fontSize: "13px", fontFamily: "inherit" })
                    .add();

                // --- ΔH double-headed arrow (reactant level → product level) ---
                renderer.path(["M", dhX, y50, "L", dhX, y20])
                    .attr({ stroke: ink, "stroke-width": lw })
                    .add();
                // top arrowhead (pointing up toward reactant)
                renderer.path(["M", dhX - arrowSize, y50 + arrowSize * 1.5,
                                "L", dhX, y50,
                                "L", dhX + arrowSize, y50 + arrowSize * 1.5])
                    .attr({ stroke: ink, "stroke-width": lw, fill: "none" })
                    .add();
                // bottom arrowhead (pointing down toward products)
                renderer.path(["M", dhX - arrowSize, y20 - arrowSize * 1.5,
                                "L", dhX, y20,
                                "L", dhX + arrowSize, y20 - arrowSize * 1.5])
                    .attr({ stroke: ink, "stroke-width": lw, fill: "none" })
                    .add();
                renderer.text("ΔH = −30 kJ/mol", dhX + 9, (y50 + y20) / 2 + 5)
                    .css({ color: ink, fontSize: "13px", fontFamily: "inherit" })
                    .add();

                // --- Direct labels ---
                renderer.text("Reactants", xLeft, y50 - 14)
                    .css({ color: ink, fontSize: "14px", fontWeight: "600", fontFamily: "inherit" })
                    .add();
                renderer.text("50 kJ/mol", xLeft, y50 - 1)
                    .css({ color: soft, fontSize: "12px", fontFamily: "inherit" })
                    .add();

                renderer.text("Transition State", xPeak + 8, y120 - 14)
                    .css({ color: ink, fontSize: "14px", fontWeight: "600", fontFamily: "inherit" })
                    .add();
                renderer.text("120 kJ/mol", xPeak + 8, y120 - 1)
                    .css({ color: soft, fontSize: "12px", fontFamily: "inherit" })
                    .add();

                renderer.text("Products", xRight, y20 - 14)
                    .css({ color: ink, fontSize: "14px", fontWeight: "600", fontFamily: "inherit" })
                    .add();
                renderer.text("20 kJ/mol", xRight, y20 - 1)
                    .css({ color: soft, fontSize: "12px", fontFamily: "inherit" })
                    .add();
            }
        }
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "line-reaction-coordinate · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    xAxis: {
        title: {
            text: "Reaction Coordinate",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickLength: 0,
        tickPositions: [],
        min: 0,
        max: 100,
        labels: { enabled: false }
    },
    yAxis: {
        title: {
            text: "Potential Energy (kJ/mol)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        gridLineColor: t.grid,
        lineColor: t.inkSoft,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        min: 0,
        max: 145,
        tickInterval: 20,
        plotLines: [
            {
                value: 50,
                color: t.inkSoft,
                dashStyle: "ShortDash",
                width: 1.5,
                zIndex: 3
            },
            {
                value: 20,
                color: t.inkSoft,
                dashStyle: "ShortDash",
                width: 1.5,
                zIndex: 3
            }
        ]
    },
    legend: { enabled: false },
    tooltip: { enabled: false },
    plotOptions: {
        series: {
            animation: false,
            lineWidth: 3,
            marker: { enabled: false }
        }
    },
    series: [{
        name: "Potential Energy",
        data: energyData,
        color: t.palette[0]
    }]
});
