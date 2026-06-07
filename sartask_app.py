import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
 
from satellite import Satellite
from target import Target
from pass_finder import find_passes
from reports.pass_quality import generate_pass_quality_report
from tle_fetcher import fetch_all_sar_satellites
import pandas as pd
from datetime import datetime, timezone
 
st.set_page_config(
    page_title="SARTASK — SAR Mission Tasking Engine",
    page_icon="🛰️",
    layout="wide"
)
 
# ── OPS ROOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');
 
:root {
    --phosphor: #00ff41;
    --phosphor-dim: #00aa2b;
    --phosphor-dark: #003d0f;
    --cyan: #00d4ff;
    --cyan-dim: #0088aa;
    --amber: #ffaa00;
    --red-alert: #ff3333;
    --bg-primary: #020d04;
    --bg-secondary: #050f06;
    --bg-panel: #040c05;
    --grid-color: rgba(0,255,65,0.06);
    --border: rgba(0,255,65,0.25);
    --border-bright: rgba(0,255,65,0.6);
}
 
html, body, [class*="css"] {
    font-family: 'Share Tech Mono', monospace !important;
    background-color: var(--bg-primary) !important;
    color: var(--phosphor) !important;
}
 
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.08) 2px, rgba(0,0,0,0.08) 4px
    );
    pointer-events: none;
    z-index: 9999;
}
 
.stApp {
    background-color: var(--bg-primary) !important;
    background-image:
        linear-gradient(var(--grid-color) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
    background-size: 40px 40px;
}
 
h1 {
    font-family: 'Orbitron', monospace !important;
    color: var(--phosphor) !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    text-shadow: 0 0 10px rgba(0,255,65,0.8), 0 0 20px rgba(0,255,65,0.4);
    letter-spacing: 4px !important;
    border-bottom: 1px solid var(--border-bright);
    padding-bottom: 8px;
}
 
h2, h3 {
    font-family: 'Orbitron', monospace !important;
    color: var(--cyan) !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    text-shadow: 0 0 8px rgba(0,212,255,0.6);
    border-left: 3px solid var(--cyan);
    padding-left: 10px !important;
    margin-top: 1.5rem !important;
}
 
[data-testid="stSidebar"] {
    background-color: #020c03 !important;
    border-right: 1px solid var(--border-bright) !important;
}
[data-testid="stSidebar"] * {
    color: var(--phosphor) !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stSlider label {
    color: var(--phosphor-dim) !important;
    font-size: 0.75rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'Orbitron', monospace !important;
    color: var(--phosphor) !important;
    font-size: 0.8rem !important;
    border-left: 2px solid var(--phosphor) !important;
    text-shadow: 0 0 6px rgba(0,255,65,0.5);
}
 
.stTextInput input, .stNumberInput input {
    background-color: var(--phosphor-dark) !important;
    border: 1px solid var(--border) !important;
    color: var(--phosphor) !important;
    font-family: 'Share Tech Mono', monospace !important;
    border-radius: 0 !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--phosphor) !important;
    box-shadow: 0 0 8px rgba(0,255,65,0.3) !important;
}
 
.stSelectbox > div > div {
    background-color: var(--phosphor-dark) !important;
    border: 1px solid var(--border) !important;
    color: var(--phosphor) !important;
    border-radius: 0 !important;
}
 
.stButton > button[kind="primary"] {
    background: transparent !important;
    border: 2px solid var(--phosphor) !important;
    color: var(--phosphor) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    border-radius: 0 !important;
    padding: 12px 24px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 10px rgba(0,255,65,0.2) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(0,255,65,0.1) !important;
    box-shadow: 0 0 20px rgba(0,255,65,0.5), inset 0 0 20px rgba(0,255,65,0.05) !important;
}
 
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--cyan) !important;
    color: var(--cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    border-radius: 0 !important;
    letter-spacing: 2px !important;
}
 
[data-testid="stMetric"] {
    background-color: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-top: 2px solid var(--phosphor) !important;
    padding: 16px !important;
    border-radius: 0 !important;
}
[data-testid="stMetric"] label {
    color: var(--phosphor-dim) !important;
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: var(--phosphor) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 1.4rem !important;
    text-shadow: 0 0 8px rgba(0,255,65,0.5) !important;
}
 
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; }
.stDataFrame thead tr th {
    background-color: var(--phosphor-dark) !important;
    color: var(--cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-size: 0.7rem !important;
    border-bottom: 1px solid var(--border-bright) !important;
}
.stDataFrame tbody tr td {
    color: var(--phosphor) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    border-bottom: 1px solid var(--grid-color) !important;
}
.stDataFrame tbody tr:hover td { background-color: rgba(0,255,65,0.05) !important; }
 
.stAlert {
    background-color: var(--phosphor-dark) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    color: var(--phosphor) !important;
    font-family: 'Share Tech Mono', monospace !important;
}
 
.stMarkdown p, .stMarkdown li {
    color: var(--phosphor-dim) !important;
    font-size: 0.85rem !important;
    line-height: 1.8 !important;
}
.stMarkdown strong { color: var(--phosphor) !important; }
.stMarkdown blockquote {
    border-left: 3px solid var(--amber) !important;
    color: var(--amber) !important;
    background: rgba(255,170,0,0.05) !important;
    padding: 8px 16px !important;
}
 
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--phosphor-dark); }
::-webkit-scrollbar-thumb:hover { background: var(--phosphor); }
 
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
.status-live {
    color: var(--phosphor);
    animation: blink 2s infinite;
    font-size: 0.7rem;
    letter-spacing: 2px;
}
 
/* iframe strip for the orbit canvas */
.orbit-frame iframe {
    border: none !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)
 
# ── ORBIT ANIMATION HTML ──────────────────────────────────────────────────────
ORBIT_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@700;900&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#020d04;overflow:hidden;font-family:'Share Tech Mono',monospace}
#wrap{display:grid;grid-template-columns:1fr 220px;height:420px;width:100%}
#cw{position:relative;overflow:hidden}
canvas{display:block;width:100%;height:100%}
.scanline{position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,65,0.015) 2px,rgba(0,255,65,0.015) 4px);pointer-events:none}
.tlabel{position:absolute;pointer-events:none;display:flex;flex-direction:column;align-items:center;gap:3px;transform:translate(-50%,-50%)}
.ch{width:24px;height:24px;position:relative}
.ch::before,.ch::after{content:'';position:absolute;background:#ff3333}
.ch::before{width:1px;height:100%;left:50%;top:0}
.ch::after{width:100%;height:1px;top:50%;left:0}
.ch-ring{position:absolute;inset:-7px;border:1px solid #ff3333;border-radius:50%;animation:pr 2s ease-in-out infinite}
@keyframes pr{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.15)}}
.ttag{font-size:8px;color:#ff3333;letter-spacing:2px;white-space:nowrap}
.statusbar{position:absolute;bottom:6px;left:8px;font-size:8px;color:#005515;letter-spacing:1px}
.statusbar em{color:#00ff41;font-style:normal}
/* sidebar */
.sidebar{border-left:1px solid #003d0f;display:flex;flex-direction:column;padding:10px 10px;gap:8px;overflow:hidden}
.stitle{font-family:'Orbitron',monospace;font-size:9px;color:#00aa2b;letter-spacing:3px;border-bottom:1px solid #003d0f;padding-bottom:4px;margin-bottom:4px}
.sat-row{display:flex;justify-content:space-between;align-items:center;font-size:9px;padding:2px 0}
.dot{width:5px;height:5px;border-radius:50%;display:inline-block;margin-right:5px}
.tbox{background:rgba(0,255,65,0.04);border:1px solid #003d0f;padding:5px 7px;flex:1}
.tlabel2{font-size:7px;color:#005515;letter-spacing:2px}
.tval{font-size:12px;color:#00ff41;margin-top:1px}
.tval.b{color:#00d4ff}.tval.a{color:#ffaa00}
.tgrid{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px}
.spark-label{font-size:7px;color:#005515;letter-spacing:1px;margin-bottom:2px}
svg.spark{width:100%;height:22px;display:block}
.blink{animation:bl 1s step-end infinite}
@keyframes bl{0%,100%{opacity:1}50%{opacity:0}}
/* bottom strip */
#bottom{display:grid;grid-template-columns:1fr 1fr 1fr;border-top:1px solid #003d0f;height:100px;background:rgba(2,13,4,0.98)}
.cp{padding:6px 10px;border-right:1px solid #003d0f}
.cp:last-child{border-right:none}
.ctitle{font-size:7px;color:#005515;letter-spacing:2px;margin-bottom:3px}
svg.mc{width:100%;height:72px;display:block}
</style>
</head>
<body>
<div style="display:flex;flex-direction:column;height:100vh">
  <div style="padding:5px 10px;border-bottom:1px solid #003d0f;display:flex;align-items:center;justify-content:space-between">
    <div style="font-family:'Orbitron',monospace;font-size:11px;letter-spacing:4px;color:#00ff41">SAR<span style="color:#00cc33">TASK</span> <span style="font-size:8px;color:#003d0f;letter-spacing:2px">◈ SAR GEOMETRY VISUALIZER</span></div>
    <div style="font-size:8px;color:#003d0f;letter-spacing:1px">S1A <span style="color:#00ff41" id="h-s1a">---</span> km &nbsp;|&nbsp; S1C <span style="color:#00d4ff" id="h-s1c">---</span> km &nbsp;|&nbsp; S1D <span style="color:#ffaa00" id="h-s1d">---</span> km &nbsp;|&nbsp; INC <span style="color:#00ff41" id="h-inc">--</span>°</div>
  </div>
 
  <div id="wrap" style="flex:1">
    <div id="cw">
      <canvas id="c"></canvas>
      <div class="scanline"></div>
      <div class="tlabel" id="tl">
        <div class="ch"><div class="ch-ring"></div></div>
        <div class="ttag">◈ OKMOK VOLCANO ◈</div>
      </div>
      <div class="statusbar">MODE: <em>IW-SLC</em> &nbsp;|&nbsp; C-BAND 5.6CM &nbsp;|&nbsp; ALT: <em>693KM</em> &nbsp;|&nbsp; INC: <em id="sb-inc">--</em>°<span class="blink">_</span></div>
    </div>
    <div class="sidebar">
      <div class="stitle">◈ CONSTELLATIONS</div>
      <div class="sat-row"><span><span class="dot" style="background:#00ff41"></span>SENTINEL-1A</span><span id="sv0" style="color:#00ff41">--</span></div>
      <div class="sat-row"><span><span class="dot" style="background:#00d4ff"></span>SENTINEL-1C</span><span id="sv1" style="color:#00d4ff">--</span></div>
      <div class="sat-row"><span><span class="dot" style="background:#ffaa00"></span>SENTINEL-1D</span><span id="sv2" style="color:#ffaa00">--</span></div>
      <div class="stitle" style="margin-top:4px">◈ TELEMETRY — S1A</div>
      <div class="tgrid">
        <div class="tbox"><div class="tlabel2">SLANT RNG</div><div class="tval" id="t-sl">---</div></div>
        <div class="tbox"><div class="tlabel2">INC ANGLE</div><div class="tval b" id="t-ic">---</div></div>
        <div class="tbox"><div class="tlabel2">DOPPLER</div><div class="tval a" id="t-dp">---</div></div>
        <div class="tbox"><div class="tlabel2">ORBIT θ</div><div class="tval" id="t-th">---</div></div>
      </div>
      <div class="spark-label">SLANT RANGE HISTORY</div>
      <svg class="spark" id="spark" viewBox="0 0 200 22" preserveAspectRatio="none"></svg>
      <div class="stitle" style="margin-top:4px">◈ ORBITAL ELEMENTS</div>
      <div style="font-size:8px;color:#005515;line-height:1.9">
        ALT <span style="color:#00ff41;float:right">693 KM</span><br>
        INCL <span style="color:#00ff41;float:right">98.18°</span><br>
        RAAN S1A <span style="color:#00ff41;float:right">0°</span><br>
        RAAN S1C <span style="color:#00d4ff;float:right">120°</span><br>
        RAAN S1D <span style="color:#ffaa00;float:right">240°</span>
      </div>
    </div>
  </div>
 
  <div id="bottom">
    <div class="cp"><div class="ctitle">◈ SLANT RANGE (KM)</div><svg class="mc" id="ch-sr" viewBox="0 0 220 60" preserveAspectRatio="none"></svg></div>
    <div class="cp"><div class="ctitle">◈ INCIDENCE ANGLE (°)</div><svg class="mc" id="ch-ia" viewBox="0 0 220 60" preserveAspectRatio="none"></svg></div>
    <div class="cp"><div class="ctitle">◈ DOPPLER SHIFT (HZ)</div><svg class="mc" id="ch-dp" viewBox="0 0 220 60" preserveAspectRatio="none"></svg></div>
  </div>
</div>
 
<script>
const SC=['#00ff41','#00d4ff','#ffaa00'];
const RAANS=[0,120,240];
const Re=6378,ALT=693,A=Re+ALT,E=0.0001306,INCL=98.18*Math.PI/180,OM=0.1,WL=0.056,GM=398600.4418,N=200;
let TLat=53.43,TLon=-168.13;
 
function ecef(lat,lon){
  const la=lat*Math.PI/180,lo=lon*Math.PI/180;
  return[Re*Math.cos(la)*Math.cos(lo),Re*Math.cos(la)*Math.sin(lo),Re*Math.sin(la)];
}
 
function sp(raan,nu){
  const r=raan*Math.PI/180,p=(A*(1-E*E))/(1+E*Math.cos(nu));
  return[
    p*(Math.cos(r)*Math.cos(OM+nu)-Math.sin(r)*Math.sin(OM+nu)*Math.cos(INCL)),
    p*(Math.sin(r)*Math.cos(OM+nu)+Math.cos(r)*Math.sin(OM+nu)*Math.cos(INCL)),
    p*(Math.sin(OM+nu)*Math.sin(INCL))
  ];
}
 
function compute(){
  const G=ecef(TLat,TLon);
  return{G,sats:RAANS.map(raan=>{
    const pos=[],sl=[],inc=[],dop=[],th=[];
    for(let k=0;k<N;k++){
      let M=2*Math.PI*k/N,Ea=M;
      for(let j=0;j<5;j++) Ea=M+E*Math.sin(Ea);
      const nu=2*Math.atan2(Math.sqrt(1+E)*Math.sin(Ea/2),Math.sqrt(1-E)*Math.cos(Ea/2));
      const p=sp(raan,nu); pos.push(p);
      const dx=p[0]-G[0],dy=p[1]-G[1],dz=p[2]-G[2],s=Math.sqrt(dx*dx+dy*dy+dz*dz);
      sl.push(s);
      const gn=Math.sqrt(G[0]**2+G[1]**2+G[2]**2);
      const gh=[G[0]/gn,G[1]/gn,G[2]/gn],lh=[dx/s,dy/s,dz/s];
      inc.push(Math.acos(-(lh[0]*gh[0]+lh[1]*gh[1]+lh[2]*gh[2]))*180/Math.PI);
      const pn=Math.sqrt(p[0]**2+p[1]**2+p[2]**2),vd=[p[0]/pn,p[1]/pn,p[2]/pn],vorb=Math.sqrt(GM/A);
      dop.push((2*vorb/WL)*(vd[0]*lh[0]+vd[1]*lh[1]+vd[2]*lh[2]));
      th.push(nu*180/Math.PI);
    }
    return{pos,sl,inc,dop,th};
  })};
}
 
let state=compute(),frame=0,rotY=0.3,rotX=0.4;
const sparkH=[];
const canvas=document.getElementById('c');
const ctx=canvas.getContext('2d');
 
function resize(){
  const cw=document.getElementById('cw');
  canvas.width=cw.offsetWidth; canvas.height=cw.offsetHeight;
}
 
function proj(x,y,z,cx,cy,sc,rx,ry){
  const x2=x*Math.cos(ry)+z*Math.sin(ry),z2=-x*Math.sin(ry)+z*Math.cos(ry);
  const y2=y*Math.cos(rx)-z2*Math.sin(rx),z3=y*Math.sin(rx)+z2*Math.cos(rx);
  const f=sc/(sc+z3*0.0002);
  return[cx+x2*f,cy-y2*f];
}
 
function norm(arr){const mn=Math.min(...arr),mx=Math.max(...arr);return arr.map(v=>mx===mn?.5:(v-mn)/(mx-mn));}
 
function polysvg(idxs,yn,w,h,color){
  if(idxs.length<2) return'';
  const pts=idxs.map((x,i)=>`${(x/(N-1))*w},${h-yn[i]*h}`).join(' ');
  return`<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.1" opacity="0.9"/>`;
}
 
function updateCharts(f){
  const {sats}=state;
  const srN=sats.map(s=>norm(s.sl)),iaN=sats.map(s=>norm(s.inc)),dpN=sats.map(s=>norm(s.dop));
  const idx=Array.from({length:N},(_,i)=>i);
  let sr='',ia='',dp='';
  for(let i=0;i<3;i++){
    sr+=polysvg(idx,srN[i],220,52,SC[i]);
    ia+=polysvg(idx,iaN[i],220,52,SC[i]);
    dp+=polysvg(idx,dpN[i],220,52,SC[i]);
    const fx=(f/(N-1))*220;
    sr+=`<circle cx="${fx}" cy="${52-srN[i][f]*52}" r="2.5" fill="${SC[i]}"/>`;
    ia+=`<circle cx="${fx}" cy="${52-iaN[i][f]*52}" r="2.5" fill="${SC[i]}"/>`;
    dp+=`<circle cx="${fx}" cy="${52-dpN[i][f]*52}" r="2.5" fill="${SC[i]}"/>`;
  }
  const g='<line x1="0" y1="26" x2="220" y2="26" stroke="#001a05" stroke-width="0.4"/>';
  document.getElementById('ch-sr').innerHTML=g+sr;
  document.getElementById('ch-ia').innerHTML=g+ia;
  document.getElementById('ch-dp').innerHTML=g+dp;
  sparkH.push(sats[0].sl[f]);
  if(sparkH.length>70) sparkH.shift();
  const smn=Math.min(...sparkH),smx=Math.max(...sparkH);
  const sp2=sparkH.map((v,i)=>`${(i/69)*200},${22-(((v-smn)/(smx-smn||1)))*20}`).join(' ');
  document.getElementById('spark').innerHTML=`<polyline points="${sp2}" fill="none" stroke="#00ff41" stroke-width="1.1" opacity="0.85"/>`;
}
 
function updateTelem(f){
  const s=state.sats[0];
  document.getElementById('t-sl').textContent=Math.round(s.sl[f])+' km';
  document.getElementById('t-ic').textContent=s.inc[f].toFixed(1)+'°';
  document.getElementById('t-dp').textContent=(s.dop[f]/1000).toFixed(1)+' kHz';
  document.getElementById('t-th').textContent=s.th[f].toFixed(1)+'°';
  document.getElementById('sb-inc').textContent=s.inc[f].toFixed(1);
  for(let i=0;i<3;i++) document.getElementById('sv'+i).textContent=Math.round(state.sats[i].sl[f])+' km';
  document.getElementById('h-s1a').textContent=Math.round(state.sats[0].sl[f]);
  document.getElementById('h-s1c').textContent=Math.round(state.sats[1].sl[f]);
  document.getElementById('h-s1d').textContent=Math.round(state.sats[2].sl[f]);
  document.getElementById('h-inc').textContent=s.inc[f].toFixed(1);
}
 
function draw(){
  const W=canvas.width,H=canvas.height,cx=W*.5,cy=H*.5;
  const sc=Math.min(W,H)*.38,sk=sc/Re;
  ctx.clearRect(0,0,W,H);
  const f=frame%N;
  const {G,sats}=state;
 
  // earth grid
  const np=50;
  ctx.strokeStyle='rgba(0,61,15,0.45)';ctx.lineWidth=0.5;
  for(let la=-60;la<=60;la+=30){
    ctx.beginPath();
    for(let i=0;i<=np;i++){
      const lo=(i/np)*360-180,lar=la*Math.PI/180,lor=lo*Math.PI/180;
      const [px,py]=proj(Re*Math.cos(lar)*Math.cos(lor)*sk,Re*Math.cos(lar)*Math.sin(lor)*sk,Re*Math.sin(lar)*sk,cx,cy,sc,rotX,rotY);
      i===0?ctx.moveTo(px,py):ctx.lineTo(px,py);
    }
    ctx.stroke();
  }
  for(let lo=-180;lo<=180;lo+=60){
    ctx.beginPath();
    for(let i=0;i<=np;i++){
      const la=(i/np)*180-90,lar=la*Math.PI/180,lor=lo*Math.PI/180;
      const [px,py]=proj(Re*Math.cos(lar)*Math.cos(lor)*sk,Re*Math.cos(lar)*Math.sin(lor)*sk,Re*Math.sin(lar)*sk,cx,cy,sc,rotX,rotY);
      i===0?ctx.moveTo(px,py):ctx.lineTo(px,py);
    }
    ctx.stroke();
  }
 
  // target
  const [gx,gy]=proj(G[0]*sk,G[1]*sk,G[2]*sk,cx,cy,sc,rotX,rotY);
  document.getElementById('tl').style.left=gx+'px';
  document.getElementById('tl').style.top=gy+'px';
  ctx.fillStyle='#ff3333';ctx.beginPath();ctx.arc(gx,gy,4.5,0,Math.PI*2);ctx.fill();
 
  for(let si=0;si<3;si++){
    const d=sats[si],col=SC[si];
    ctx.strokeStyle=col+'1a';ctx.lineWidth=0.6;
    ctx.beginPath();
    d.pos.forEach((p,i)=>{
      const [px,py]=proj(p[0]*sk,p[1]*sk,p[2]*sk,cx,cy,sc,rotX,rotY);
      i===0?ctx.moveTo(px,py):ctx.lineTo(px,py);
    });
    ctx.stroke();
 
    const TRAIL=28;
    for(let j=Math.max(0,f-TRAIL);j<=f;j++){
      if(j===Math.max(0,f-TRAIL)) continue;
      const t=(j-Math.max(0,f-TRAIL))/TRAIL;
      const [px,py]=proj(d.pos[j][0]*sk,d.pos[j][1]*sk,d.pos[j][2]*sk,cx,cy,sc,rotX,rotY);
      const [px2,py2]=proj(d.pos[j-1][0]*sk,d.pos[j-1][1]*sk,d.pos[j-1][2]*sk,cx,cy,sc,rotX,rotY);
      ctx.strokeStyle=col+Math.floor(t*210).toString(16).padStart(2,'0');
      ctx.lineWidth=1.8;
      ctx.beginPath();ctx.moveTo(px2,py2);ctx.lineTo(px,py);ctx.stroke();
    }
 
    const [sx,sy]=proj(d.pos[f][0]*sk,d.pos[f][1]*sk,d.pos[f][2]*sk,cx,cy,sc,rotX,rotY);
    ctx.fillStyle=col;ctx.beginPath();ctx.arc(sx,sy,5,0,Math.PI*2);ctx.fill();
    ctx.setLineDash([3,3]);ctx.strokeStyle=col+'77';ctx.lineWidth=0.7;
    ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(gx,gy);ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle=col;ctx.font='8px Share Tech Mono,monospace';
    ctx.fillText(['S-1A','S-1C','S-1D'][si],sx+7,sy-3);
  }
 
  rotY+=0.003;
  frame++;
  updateTelem(f);
  updateCharts(f);
  requestAnimationFrame(draw);
}
 
window.addEventListener('resize',resize);
resize();
setTimeout(()=>{resize();draw();},80);
</script>
</body>
</html>
"""
 
# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:4px;">
    <div style="font-family:'Orbitron',monospace;font-size:0.65rem;
                color:#00ff41;letter-spacing:3px;opacity:0.6;">
        CLASSIFICATION: UNCLASSIFIED // FOR DEMONSTRATION ONLY
    </div>
    <div class="status-live">◉ SYSTEM ONLINE</div>
</div>
""", unsafe_allow_html=True)
 
st.title("SARTASK")
st.markdown("""
<div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
            color:#00aa2b;letter-spacing:4px;margin-top:-12px;margin-bottom:16px;">
    SAR MISSION TASKING ENGINE &nbsp;|&nbsp;
    ORBITAL PASS QUALITY ASSESSMENT &nbsp;|&nbsp;
    LIVE TLE DATA
</div>
""", unsafe_allow_html=True)
 
# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="font-family:'Orbitron',monospace;font-size:0.9rem;
            color:#00ff41;letter-spacing:3px;padding:8px 0;
            border-bottom:1px solid rgba(0,255,65,0.3);margin-bottom:16px;">
    ◈ MISSION PARAMETERS
</div>
""", unsafe_allow_html=True)
 
sat_option = st.sidebar.selectbox(
    "SENSOR PLATFORM",
    ["SENTINEL-1A", "SENTINEL-1C", "SENTINEL-1D",
     "TERRASAR-X", "COSMO-SKYMED 1", "RADARSAT-2", "NISAR"]
)
 
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
            color:#00aa2b;letter-spacing:2px;">◈ TARGET COORDINATES</div>
""", unsafe_allow_html=True)
 
target_name = st.sidebar.text_input("DESIGNATION", "Okmok Volcano")
target_lat  = st.sidebar.number_input("LATITUDE (°N)", value=53.43, min_value=-90.0, max_value=90.0)
target_lon  = st.sidebar.number_input("LONGITUDE (°E)", value=-168.13, min_value=-180.0, max_value=180.0)
target_desc = st.sidebar.text_input("NOTES", "Alaska — high latitude volcanic target")
 
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
            color:#00aa2b;letter-spacing:2px;">◈ PRESET TARGETS</div>
""", unsafe_allow_html=True)
 
preset = st.sidebar.selectbox("SELECT TARGET", [
    "Custom",
    "Okmok Volcano (Alaska)",
    "Nyiragongo Volcano (Congo)",
    "Mundra Port (India)",
    "Fukushima (Japan)"
])
 
presets = {
    "Okmok Volcano (Alaska)"    : (53.43,  -168.13, "Alaska — high latitude"),
    "Nyiragongo Volcano (Congo)": (-1.52,    29.25,  "DR Congo — equatorial"),
    "Mundra Port (India)"       : (22.84,    69.70,  "Gujarat, India — port monitoring"),
    "Fukushima (Japan)"         : (37.42,   141.03,  "Japan — disaster monitoring"),
}
 
if preset != "Custom":
    target_lat, target_lon, target_desc = presets[preset]
    target_name = preset.split(" (")[0]
 
st.sidebar.markdown("---")
hours = st.sidebar.slider("ANALYSIS WINDOW (HRS)", 24, 72, 72)
run   = st.sidebar.button("⬡ EXECUTE TASKING", type="primary")
 
st.sidebar.markdown(f"""
<div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
            color:#003d0f;letter-spacing:1px;margin-top:16px;
            border-top:1px solid rgba(0,255,65,0.1);padding-top:8px;">
    UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}<br>
    ENGINE: SGP4 + C GEOMETRY<br>
    SOURCE: CELESTRAK LIVE
</div>
""", unsafe_allow_html=True)
 
# ── TARGET / SAT INFO ─────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"""
    <div style="border:1px solid rgba(0,255,65,0.25);padding:16px;
                background:rgba(0,255,65,0.02);">
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                    color:#00aa2b;letter-spacing:3px;margin-bottom:8px;">
            ◈ TARGET PACKAGE
        </div>
        <div style="font-family:'Orbitron',monospace;font-size:1rem;
                    color:#00ff41;text-shadow:0 0 8px rgba(0,255,65,0.5);">
            {target_name.upper()}
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
                    color:#00aa2b;margin-top:4px;">
            LAT {target_lat:+.4f}° &nbsp; LON {target_lon:+.4f}°
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
                    color:#003d0f;margin-top:4px;">
            {target_desc}
        </div>
    </div>
    """, unsafe_allow_html=True)
 
with col2:
    st.markdown(f"""
    <div style="border:1px solid rgba(0,212,255,0.25);padding:16px;
                background:rgba(0,212,255,0.02);">
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                    color:#0088aa;letter-spacing:3px;margin-bottom:8px;">
            ◈ SENSOR PLATFORM
        </div>
        <div style="font-family:'Orbitron',monospace;font-size:1rem;
                    color:#00d4ff;text-shadow:0 0 8px rgba(0,212,255,0.5);">
            {sat_option}
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
                    color:#0088aa;margin-top:4px;">
            SAR · C-BAND · SUN-SYNC · ~693KM ALT
        </div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
                    color:#004455;margin-top:4px;">
            TLE: CELESTRAK LIVE · PROPAGATOR: SGP4
        </div>
    </div>
    """, unsafe_allow_html=True)
 
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
 
 
def build_ground_track_map(satellite, target, passes, hours=6):
    from propagator import propagate, eci_to_latlon
 
    m = folium.Map(
        location=[target.lat, target.lon],
        zoom_start=3,
        tiles="CartoDB dark_matter"
    )
 
    m.get_root().html.add_child(folium.Element("""
    <style>
    .leaflet-container { background: #020d04 !important; font-family: 'Share Tech Mono', monospace; }
    </style>
    """))
 
    folium.Marker(
        location=[target.lat, target.lon],
        popup=folium.Popup(
            f"<div style='font-family:monospace;background:#020d04;color:#00ff41;"
            f"border:1px solid #00ff41;padding:8px;'>"
            f"<b>◈ {target.name.upper()}</b><br>"
            f"LAT {target.lat:+.4f}°<br>LON {target.lon:+.4f}°<br>"
            f"{target.description}</div>", max_width=220
        ),
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
        tooltip=f"◈ {target.name.upper()}"
    ).add_to(m)
 
    states = propagate(satellite, hours=hours, step_seconds=60)
    track_points = []
    for state in states:
        lat, lon, alt = eci_to_latlon(state["x"], state["y"], state["z"], state["time"])
        track_points.append([lat, lon])
 
    segment = []
    for i, pt in enumerate(track_points):
        if i > 0 and abs(pt[1] - track_points[i-1][1]) > 180:
            if len(segment) > 1:
                folium.PolyLine(segment, color="#00ff41", weight=1.2, opacity=0.6, dash_array="4 4").add_to(m)
            segment = [pt]
            continue
        segment.append(pt)
    if len(segment) > 1:
        folium.PolyLine(segment, color="#00ff41", weight=1.2, opacity=0.6, dash_array="4 4").add_to(m)
 
    sorted_passes = sorted(passes, key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(sorted_passes):
        if p["score"] >= 45:   color, quality, sym = "#00ff41", "OPTIMAL", "●"
        elif p["score"] >= 30: color, quality, sym = "#ffaa00", "GOOD", "◉"
        elif p["score"] >= 20: color, quality, sym = "#ff6600", "MARGINAL", "◎"
        else:                  color, quality, sym = "#ff3333", "POOR", "○"
 
        folium.CircleMarker(
            location=[target.lat, target.lon],
            radius=6 + (p["score"] / 12),
            color=color, fill=True, fill_color=color,
            fill_opacity=0.12 + (0.04 * min(i, 4)),
            popup=folium.Popup(
                f"<div style='font-family:monospace;background:#020d04;"
                f"color:{color};border:1px solid {color};padding:8px;min-width:200px;'>"
                f"<b>{sym} PASS #{i+1} — {quality}</b><br>"
                f"<span style='color:#888'>START:</span> {p['start'].strftime('%Y-%m-%d %H:%M UTC')}<br>"
                f"<span style='color:#888'>DURATION:</span> {p['duration_min']}m<br>"
                f"<span style='color:#888'>ELEVATION:</span> {p['max_elevation']}°<br>"
                f"<span style='color:#888'>INCIDENCE:</span> {p['incidence']}°<br>"
                f"<span style='color:#888'>SCORE:</span> {p['score']}/100"
                f"</div>", max_width=240
            ),
            tooltip=f"{sym} PASS #{i+1} — {quality} [{p['score']}/100]"
        ).add_to(m)
 
    if states:
        ns = states[0]
        nlat, nlon, nalt = eci_to_latlon(ns["x"], ns["y"], ns["z"], ns["time"])
        folium.Marker(
            location=[nlat, nlon],
            popup=folium.Popup(
                f"<div style='font-family:monospace;background:#020d04;"
                f"color:#00d4ff;border:1px solid #00d4ff;padding:8px;'>"
                f"<b>◈ {satellite.name}</b><br>ALT: {nalt:.1f} KM<br>"
                f"SPD: {ns['speed']:.3f} KM/S<br>POS: {nlat:.2f}°N {nlon:.2f}°E</div>",
                max_width=200
            ),
            icon=folium.DivIcon(
                html='<div style="background:#00d4ff;border:2px solid #020d04;'
                     'border-radius:50%;width:10px;height:10px;'
                     'box-shadow:0 0 8px #00d4ff;margin-top:-5px;margin-left:-5px;"></div>',
                icon_size=(10, 10)
            ),
            tooltip=f"◈ {satellite.name} — CURRENT POSITION"
        ).add_to(m)
 
    legend_html = """
    <div style="position:fixed;bottom:20px;left:20px;
        background:rgba(2,13,4,0.95);border:1px solid rgba(0,255,65,0.4);
        padding:12px 16px;font-family:'Share Tech Mono',monospace;
        font-size:11px;color:#00ff41;z-index:1000;">
        <div style="color:#00d4ff;letter-spacing:2px;margin-bottom:6px;font-size:10px;">◈ SARTASK LEGEND</div>
        <div><span style="color:#00ff41">- - -</span> Ground track</div>
        <div><span style="color:#00ff41">●</span> OPTIMAL (≥45)</div>
        <div><span style="color:#ffaa00">◉</span> GOOD (30-44)</div>
        <div><span style="color:#ff6600">◎</span> MARGINAL (20-29)</div>
        <div><span style="color:#ff3333">○</span> POOR (&lt;20)</div>
        <div><span style="color:#00d4ff">●</span> Current position</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m
 
 
# ── MAIN LOGIC ────────────────────────────────────────────────────────────────
if run:
    with st.spinner("INITIALIZING TASKING SEQUENCE..."):
        tle_raw = fetch_all_sar_satellites()
 
        if sat_option not in tle_raw:
            st.error(f"TLE ACQUISITION FAILED: {sat_option}")
            st.stop()
 
        raw   = tle_raw[sat_option]
        line1 = raw["line1"]
        line2 = raw["line2"]
 
        inclination  = float(line2[8:16])
        raan         = float(line2[17:25])
        eccentricity = float("0." + line2[26:33])
        mean_motion  = float(line2[52:63])
 
        sat = Satellite(
            name=sat_option, line1=line1, line2=line2,
            inclination=inclination, raan=raan,
            eccentricity=eccentricity, mean_motion=mean_motion
        )
 
        target = Target(target_name, target_lat, target_lon, target_desc)
        passes = find_passes(sat, target, hours=hours)
 
    if not passes:
        st.warning("NO PASSES DETECTED IN ANALYSIS WINDOW")
        st.stop()
 
    best          = max(passes, key=lambda x: x["score"])
    optimal_count = sum(1 for p in passes if p["score"] >= 45)
    good_count    = sum(1 for p in passes if 30 <= p["score"] < 45)
    poor_count    = sum(1 for p in passes if p["score"] < 30)
    avg_dur       = sum(p["duration_min"] for p in passes) / len(passes)
 
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL PASSES",    len(passes))
    m2.metric("BEST SCORE",      f"{best['score']}/100")
    m3.metric("OPTIMAL WINDOWS", optimal_count)
    m4.metric("BEST ACQUISITION",best["start"].strftime("%b %d %H:%M UTC"))
 
    st.markdown(f"""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                color:#003d0f;letter-spacing:2px;margin-bottom:8px;">
        TLE SOURCE: {tle_raw[sat_option]['source'].upper()} &nbsp;|&nbsp;
        EPOCH: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp;
        PROPAGATOR: SGP4 (VALLADO 2006) &nbsp;|&nbsp; GEOMETRY: C-ENGINE v1.0
    </div>
    """, unsafe_allow_html=True)
 
    st.markdown("<hr>", unsafe_allow_html=True)
 
    st.subheader("TACTICAL GROUND TRACK DISPLAY")
    st.caption("PHOSPHOR GREEN = GROUND TRACK (NEXT 6HRS) · CIRCLES = PASS QUALITY · CLICK FOR PASS DATA")
    with st.spinner("RENDERING TACTICAL DISPLAY..."):
        ground_map = build_ground_track_map(sat, target, passes)
        st_folium(ground_map, width=None, height=520, returned_objects=[])
 
    st.markdown("<hr>", unsafe_allow_html=True)
 
    st.subheader("PASS QUALITY ASSESSMENT — RANKED")
    sorted_passes = sorted(passes, key=lambda x: x["score"], reverse=True)
    rows = []
    for i, p in enumerate(sorted_passes):
        if p["score"] >= 45:   rec = "● OPTIMAL"
        elif p["score"] >= 30: rec = "◉ GOOD"
        elif p["score"] >= 20: rec = "◎ MARGINAL"
        else:                  rec = "○ POOR"
        rows.append({
            "RNK":i+1, "START (UTC)":p["start"].strftime("%Y-%m-%d %H:%M"),
            "DUR":f"{p['duration_min']}m", "MAX EL":f"{p['max_elevation']}°",
            "INC":f"{p['incidence']}°", "SCORE":f"{p['score']}/100", "STATUS":rec
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
 
    st.subheader("PASS QUALITY TIMELINE")
    chart_data = pd.DataFrame({
        "PASS START": [p["start"].strftime("%m-%d %H:%M") for p in sorted_passes],
        "SCORE"     : [p["score"] for p in sorted_passes],
    })
    st.bar_chart(chart_data.set_index("PASS START"))
 
    st.markdown("<hr>", unsafe_allow_html=True)
 
    st.subheader("MISSION COVERAGE SUMMARY")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
                    color:#00aa2b;line-height:2;">
            TOTAL PASSES &nbsp;&nbsp;&nbsp; : {len(passes)}<br>
            OPTIMAL (≥45) &nbsp; : {optimal_count}<br>
            GOOD (30-44) &nbsp;&nbsp; : {good_count}<br>
            POOR (&lt;30) &nbsp;&nbsp;&nbsp;&nbsp; : {poor_count}<br>
            AVG DURATION &nbsp;&nbsp; : {avg_dur:.1f} MIN
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
                    color:#00aa2b;line-height:2;">
            BEST PASS &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; : {best['start'].strftime('%Y-%m-%d %H:%M UTC')}<br>
            BEST SCORE &nbsp;&nbsp;&nbsp;&nbsp; : {best['score']}/100<br>
            PLATFORM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; : {sat_option}<br>
            TARGET &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; : {target_name.upper()}<br>
            ANALYSIS WIN &nbsp; : {hours}H
        </div>""", unsafe_allow_html=True)
 
    st.markdown("<hr>", unsafe_allow_html=True)
 
    os.makedirs("outputs", exist_ok=True)
    pdf_path = f"outputs/pass_quality_{target_name.replace(' ','_').lower()}.pdf"
    generate_pass_quality_report(sat, target, passes, pdf_path)
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬡ DOWNLOAD MISSION REPORT (PDF)",
            data=f,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf"
        )
 
else:
    # ── LANDING STATE: LIVE ORBIT ANIMATION ──────────────────────────────────
    st.components.v1.html(ORBIT_HTML, height=540, scrolling=False)
 
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("SYSTEM CAPABILITIES")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div style="border:1px solid rgba(0,255,65,0.15);padding:16px;background:rgba(0,255,65,0.01);">
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#00aa2b;letter-spacing:2px;margin-bottom:8px;">◈ ORBITAL MECHANICS</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#003d0f;line-height:1.8;">
                SGP4 propagation<br>Live Celestrak TLEs<br>ECI/ECEF transforms<br>Pass detection
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="border:1px solid rgba(0,212,255,0.15);padding:16px;background:rgba(0,212,255,0.01);">
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#0088aa;letter-spacing:2px;margin-bottom:8px;">◈ SAR GEOMETRY</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#004455;line-height:1.8;">
                C physics engine<br>Incidence angle<br>Doppler centroid<br>Slant range
            </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style="border:1px solid rgba(255,170,0,0.15);padding:16px;background:rgba(255,170,0,0.01);">
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#aa7000;letter-spacing:2px;margin-bottom:8px;">◈ COVERAGE INTEL</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#553500;line-height:1.8;">
                72hr pass schedule<br>Quality ranking<br>Coverage inequality<br>PDF mission report
            </div>
        </div>""", unsafe_allow_html=True)
 
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("COVERAGE INEQUALITY — KEY FINDING")
    st.markdown("""
    <div style="border-left:3px solid #ffaa00;padding:16px;background:rgba(255,170,0,0.03);margin:16px 0;">
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;color:#ffaa00;line-height:2;">
            OKMOK VOLCANO &nbsp;&nbsp;&nbsp; [53°N — ALASKA] &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; → 19 PASSES / 72HRS<br>
            NYIRAGONGO VOL &nbsp;&nbsp; [-1.5° — DR CONGO] &nbsp;&nbsp; → 10 PASSES / 72HRS<br>
            <br>
            <span style="color:#aa7000;">
            SAME PLATFORM. SAME WINDOW. HIGH LATITUDE = 2× IMAGING OPPORTUNITY.<br>
            THIS IS THE ORBITAL GEOMETRY REALITY AFFECTING EVERY SAR MISSION.
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
