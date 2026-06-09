// anyplot.ai
// feynman-basic: Feynman Diagram for Particle Interactions
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 93/100 | Created: 2026-06-03

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

const W = 1600, H = 900;

// Imprint palette: four particle types, each a distinct Imprint colour
const C_FERMION = t.palette[0];  // #009E73 brand green
const C_PHOTON  = t.palette[2];  // #4467A3 blue
const C_GLUON   = t.palette[1];  // #DE8F05 amber
const C_BOSON   = t.palette[3];  // #CC4C38 red

const LW = 5, LW_OUT = 6.5;  // outgoing legs slightly thicker
const VR = 11, VR_RING = 20;

// ── wavy photon beziers ──────────────────────────────────────────────────────
function wavyBeziers(x1, y1, x2, y2, nWaves, amp, color, lw) {
  var dx = x2-x1, dy = y2-y1, len = Math.sqrt(dx*dx+dy*dy);
  var nx = -dy/len, ny = dx/len, n = nWaves*2, elems = [];
  for (var i = 0; i < n; i++) {
    var t0=i/n, t1=(i+1)/n, tm=(t0+t1)/2, sign=(i%2===0)?1:-1;
    elems.push({ type:"bezierCurve", shape:{
      x1:x1+dx*t0, y1:y1+dy*t0,
      cpx1:x1+dx*tm+nx*amp*sign, cpy1:y1+dy*tm+ny*amp*sign,
      x2:x1+dx*t1, y2:y1+dy*t1
    }, style:{stroke:color, lineWidth:lw, fill:"rgba(0,0,0,0)"} });
  }
  return elems;
}

// ── curly gluon beziers (loops bulging to one side) ──────────────────────────
function curlyBeziers(x1, y1, x2, y2, nLoops, amp, color, lw) {
  var dx = x2-x1, dy = y2-y1, len = Math.sqrt(dx*dx+dy*dy);
  var nx = -dy/len, ny = dx/len, elems = [];
  for (var i = 0; i < nLoops; i++) {
    var t0=i/nLoops, t1=(i+1)/nLoops;
    var ta=t0+(t1-t0)*0.25, tb=t0+(t1-t0)*0.75;
    elems.push({ type:"bezierCurve", shape:{
      x1:x1+dx*t0, y1:y1+dy*t0,
      cpx1:x1+dx*ta+nx*amp*2.2, cpy1:y1+dy*ta+ny*amp*2.2,
      cpx2:x1+dx*tb+nx*amp*2.2, cpy2:y1+dy*tb+ny*amp*2.2,
      x2:x1+dx*t1, y2:y1+dy*t1
    }, style:{stroke:color, lineWidth:lw, fill:"rgba(0,0,0,0)"} });
  }
  return elems;
}

// ── dashed scalar boson line ─────────────────────────────────────────────────
function dashedLine(x1, y1, x2, y2, dashLen, gapLen, color, lw) {
  var dx=x2-x1, dy=y2-y1, len=Math.sqrt(dx*dx+dy*dy);
  var ux=dx/len, uy=dy/len, elems=[], pos=0;
  while (pos < len) {
    var end=Math.min(pos+dashLen, len);
    elems.push({ type:"polyline", shape:{ points:[
      [x1+ux*pos, y1+uy*pos], [x1+ux*end, y1+uy*end]
    ]}, style:{stroke:color, lineWidth:lw, fill:"rgba(0,0,0,0)"} });
    pos += dashLen+gapLen;
  }
  return elems;
}

// ── arrowhead polygon ────────────────────────────────────────────────────────
function arrow(x1, y1, x2, y2, sz) {
  var dx=x2-x1, dy=y2-y1, len=Math.sqrt(dx*dx+dy*dy);
  var ux=dx/len, uy=dy/len, px=-uy, py=ux;
  var bx=x2-ux*sz, by=y2-uy*sz, w=sz*0.42;
  return [[x2,y2],[bx+px*w,by+py*w],[bx-px*w,by-py*w]];
}

function lerp(p, q, f) { return [p[0]+(q[0]-p[0])*f, p[1]+(q[1]-p[1])*f]; }

// ── vertex: semi-transparent highlight ring + solid dot ─────────────────────
function vertexDot(cx, cy, ringFill) {
  return [
    { type:"circle", shape:{cx,cy,r:VR_RING}, style:{fill:ringFill||"rgba(0,158,115,0.15)",stroke:"none"} },
    { type:"circle", shape:{cx,cy,r:VR}, style:{fill:t.ink} }
  ];
}

var elems = [];

// ════════════════════════════════════════════════════════════════════════════
// PANEL 1 — QED:  e⁻e⁺ → γ* → μ⁻μ⁺        (left half, x 0–950)
// ════════════════════════════════════════════════════════════════════════════
const V1=[365,476], V2=[585,476];
const E_IN=[155,240], P_IN=[155,712];
const MU_OUT=[795,240], AP_OUT=[795,712];

elems.push({ type:"text", style:{ text:"QED: Electron-Positron Annihilation", x:480, y:145,
  textAlign:"center", font:"bold 18px sans-serif", fill:t.inkSoft } });

// Incoming legs (particle forward, antiparticle reversed)
elems.push({ type:"polyline", shape:{points:[[E_IN[0],E_IN[1]],[V1[0],V1[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW,fill:"rgba(0,0,0,0)"} });
var a=lerp(E_IN,V1,0.47), b=lerp(E_IN,V1,0.53);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],24)}, style:{fill:C_FERMION,stroke:"none"} });

elems.push({ type:"polyline", shape:{points:[[P_IN[0],P_IN[1]],[V1[0],V1[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW,fill:"rgba(0,0,0,0)"} });
a=lerp(P_IN,V1,0.53); b=lerp(P_IN,V1,0.47);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],24)}, style:{fill:C_FERMION,stroke:"none"} });

// Outgoing legs — slightly thicker to differentiate final-state particles
elems.push({ type:"polyline", shape:{points:[[V2[0],V2[1]],[MU_OUT[0],MU_OUT[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW_OUT,fill:"rgba(0,0,0,0)"} });
a=lerp(V2,MU_OUT,0.47); b=lerp(V2,MU_OUT,0.53);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],24)}, style:{fill:C_FERMION,stroke:"none"} });

elems.push({ type:"polyline", shape:{points:[[V2[0],V2[1]],[AP_OUT[0],AP_OUT[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW_OUT,fill:"rgba(0,0,0,0)"} });
a=lerp(V2,AP_OUT,0.53); b=lerp(V2,AP_OUT,0.47);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],24)}, style:{fill:C_FERMION,stroke:"none"} });

// Virtual photon propagator (wavy)
elems = elems.concat(wavyBeziers(V1[0],V1[1],V2[0],V2[1],7,28,C_PHOTON,LW));

// Interaction vertices (ring highlights draw eye to interaction points)
elems = elems.concat(vertexDot(V1[0],V1[1]));
elems = elems.concat(vertexDot(V2[0],V2[1]));

// Particle labels — shifted well inward from canvas edges
elems.push({ type:"text", style:{ text:"e⁻", x:E_IN[0]-14, y:E_IN[1]-42,
  font:"bold 28px sans-serif", fill:C_FERMION, textAlign:"right" } });
elems.push({ type:"text", style:{ text:"e⁺", x:P_IN[0]-14, y:P_IN[1]+14,
  font:"bold 28px sans-serif", fill:C_FERMION, textAlign:"right" } });
elems.push({ type:"text", style:{ text:"μ⁻", x:MU_OUT[0]+14, y:MU_OUT[1]-42,
  font:"bold 28px sans-serif", fill:C_FERMION } });
elems.push({ type:"text", style:{ text:"μ⁺", x:AP_OUT[0]+14, y:AP_OUT[1]+14,
  font:"bold 28px sans-serif", fill:C_FERMION } });
elems.push({ type:"text", style:{ text:"γ*", x:(V1[0]+V2[0])/2-14, y:V1[1]-50,
  font:"bold 30px sans-serif", fill:C_PHOTON } });
elems.push({ type:"text", style:{ text:"e⁻e⁺ → γ* → μ⁻μ⁺", x:480, y:810,
  textAlign:"center", font:"19px sans-serif", fill:t.inkSoft } });

// ── Vertical panel divider ───────────────────────────────────────────────────
elems.push({ type:"polyline", shape:{points:[[956,125],[956,830]]},
  style:{stroke:t.grid,lineWidth:1.5,fill:"rgba(0,0,0,0)"} });

// ════════════════════════════════════════════════════════════════════════════
// PANEL 2a — QCD: Quark-Gluon Exchange       (right top, y 125–498)
// ════════════════════════════════════════════════════════════════════════════
const V1g=[1110,312], V2g=[1390,312];
const q1in=[1000,192], q2in=[1000,432];
const q1out=[1490,192], q2out=[1490,432];

elems.push({ type:"text", style:{ text:"QCD: Quark-Gluon Exchange", x:1274, y:145,
  textAlign:"center", font:"bold 18px sans-serif", fill:t.inkSoft } });

// Incoming quarks
elems.push({ type:"polyline", shape:{points:[[q1in[0],q1in[1]],[V1g[0],V1g[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW,fill:"rgba(0,0,0,0)"} });
a=lerp(q1in,V1g,0.47); b=lerp(q1in,V1g,0.53);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],20)}, style:{fill:C_FERMION,stroke:"none"} });

elems.push({ type:"polyline", shape:{points:[[q2in[0],q2in[1]],[V1g[0],V1g[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW,fill:"rgba(0,0,0,0)"} });
a=lerp(q2in,V1g,0.53); b=lerp(q2in,V1g,0.47);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],20)}, style:{fill:C_FERMION,stroke:"none"} });

// Outgoing quarks
elems.push({ type:"polyline", shape:{points:[[V2g[0],V2g[1]],[q1out[0],q1out[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW_OUT,fill:"rgba(0,0,0,0)"} });
a=lerp(V2g,q1out,0.47); b=lerp(V2g,q1out,0.53);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],20)}, style:{fill:C_FERMION,stroke:"none"} });

elems.push({ type:"polyline", shape:{points:[[V2g[0],V2g[1]],[q2out[0],q2out[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW_OUT,fill:"rgba(0,0,0,0)"} });
a=lerp(V2g,q2out,0.53); b=lerp(V2g,q2out,0.47);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],20)}, style:{fill:C_FERMION,stroke:"none"} });

// Gluon propagator (curly)
elems = elems.concat(curlyBeziers(V1g[0],V1g[1],V2g[0],V2g[1],6,22,C_GLUON,LW));

// Vertices
elems = elems.concat(vertexDot(V1g[0],V1g[1],"rgba(222,143,5,0.18)"));
elems = elems.concat(vertexDot(V2g[0],V2g[1],"rgba(222,143,5,0.18)"));

// Labels
elems.push({ type:"text", style:{ text:"q",  x:q1in[0]-12, y:q1in[1]-36,
  font:"bold 22px sans-serif", fill:C_FERMION, textAlign:"right" } });
elems.push({ type:"text", style:{ text:"q̄", x:q2in[0]-12, y:q2in[1]+12,
  font:"bold 22px sans-serif", fill:C_FERMION, textAlign:"right" } });
elems.push({ type:"text", style:{ text:"q",  x:q1out[0]+12, y:q1out[1]-36,
  font:"bold 22px sans-serif", fill:C_FERMION } });
elems.push({ type:"text", style:{ text:"q̄", x:q2out[0]+12, y:q2out[1]+12,
  font:"bold 22px sans-serif", fill:C_FERMION } });
elems.push({ type:"text", style:{ text:"g",  x:(V1g[0]+V2g[0])/2-10, y:V1g[1]-44,
  font:"bold 24px sans-serif", fill:C_GLUON } });

// ── Horizontal mini-panel divider ────────────────────────────────────────────
elems.push({ type:"polyline", shape:{points:[[960,502],[1582,502]]},
  style:{stroke:t.grid,lineWidth:1.5,fill:"rgba(0,0,0,0)"} });

// ════════════════════════════════════════════════════════════════════════════
// PANEL 2b — EW: Higgs Scalar Boson Decay  H → ff̄  (right bottom, y 510–830)
// ════════════════════════════════════════════════════════════════════════════
const VH=[1240,660];
const Hstart=[1000,660];
const fout=[1490,548], fbout=[1490,772];

elems.push({ type:"text", style:{ text:"EW: Higgs Scalar Boson  H → ff̄", x:1274, y:522,
  textAlign:"center", font:"bold 18px sans-serif", fill:t.inkSoft } });

// Incoming Higgs (dashed scalar boson)
elems = elems.concat(dashedLine(Hstart[0],Hstart[1],VH[0],VH[1],16,10,C_BOSON,LW));

// Outgoing fermion pair
elems.push({ type:"polyline", shape:{points:[[VH[0],VH[1]],[fout[0],fout[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW_OUT,fill:"rgba(0,0,0,0)"} });
a=lerp(VH,fout,0.47); b=lerp(VH,fout,0.53);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],20)}, style:{fill:C_FERMION,stroke:"none"} });

elems.push({ type:"polyline", shape:{points:[[VH[0],VH[1]],[fbout[0],fbout[1]]]},
  style:{stroke:C_FERMION,lineWidth:LW_OUT,fill:"rgba(0,0,0,0)"} });
a=lerp(VH,fbout,0.53); b=lerp(VH,fbout,0.47);
elems.push({ type:"polygon", shape:{points:arrow(a[0],a[1],b[0],b[1],20)}, style:{fill:C_FERMION,stroke:"none"} });

// Vertex
elems = elems.concat(vertexDot(VH[0],VH[1],"rgba(204,76,56,0.18)"));

// Labels
elems.push({ type:"text", style:{ text:"H",  x:Hstart[0]-12, y:Hstart[1]-8,
  font:"bold 24px sans-serif", fill:C_BOSON, textAlign:"right" } });
elems.push({ type:"text", style:{ text:"f",  x:fout[0]+12, y:fout[1]-34,
  font:"bold 22px sans-serif", fill:C_FERMION } });
elems.push({ type:"text", style:{ text:"f̄", x:fbout[0]+12, y:fbout[1]+10,
  font:"bold 22px sans-serif", fill:C_FERMION } });

// ════════════════════════════════════════════════════════════════════════════
// LEGEND — all four particle line styles
// ════════════════════════════════════════════════════════════════════════════
const LY = 856;

// Fermion (solid + arrow)
elems.push({ type:"polyline", shape:{points:[[55,LY],[125,LY]]},
  style:{stroke:C_FERMION,lineWidth:LW,fill:"rgba(0,0,0,0)"} });
elems.push({ type:"polygon", shape:{points:arrow(83,LY,93,LY,18)}, style:{fill:C_FERMION,stroke:"none"} });
elems.push({ type:"text", style:{ text:"fermion", x:136, y:LY-11, font:"19px sans-serif", fill:t.inkSoft } });

// Photon (wavy)
elems = elems.concat(wavyBeziers(360,LY,430,LY,3,14,C_PHOTON,LW));
elems.push({ type:"text", style:{ text:"photon (γ*)", x:440, y:LY-11, font:"19px sans-serif", fill:t.inkSoft } });

// Gluon (curly)
elems = elems.concat(curlyBeziers(700,LY,770,LY,4,12,C_GLUON,LW));
elems.push({ type:"text", style:{ text:"gluon (g)", x:780, y:LY-11, font:"19px sans-serif", fill:t.inkSoft } });

// Scalar boson (dashed)
elems = elems.concat(dashedLine(1040,LY,1110,LY,14,9,C_BOSON,LW));
elems.push({ type:"text", style:{ text:"scalar boson (H)", x:1120, y:LY-11, font:"19px sans-serif", fill:t.inkSoft } });

// Time axis
elems.push({ type:"polyline", shape:{points:[[1390,LY],[1525,LY]]},
  style:{stroke:t.inkSoft,lineWidth:2,fill:"rgba(0,0,0,0)"} });
elems.push({ type:"polygon", shape:{points:arrow(1503,LY,1525,LY,12)}, style:{fill:t.inkSoft,stroke:"none"} });
elems.push({ type:"text", style:{ text:"time", x:1380, y:LY-11, font:"18px sans-serif",
  fill:t.inkSoft, textAlign:"right" } });

// ── Render ───────────────────────────────────────────────────────────────────
const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: t.pageBg,
  title: {
    text: "feynman-basic · javascript · echarts · anyplot.ai",
    left: "center", top: 22,
    textStyle: { color: t.ink, fontSize: 30, fontWeight: "normal" }
  },
  graphic: elems,
});
