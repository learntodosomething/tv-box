# -*- coding: utf-8 -*-
"""A telefonon megnyíló távirányító-oldal (egyetlen, önálló HTML; nincs külső betöltés)."""

PAGE = r"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#0A0F1A">
<title>TV Box távirányító</title>
<style>
:root{--bg:#0A0F1A;--card:#141B2B;--card2:#1B2438;--line:rgba(255,255,255,.08);--txt:#F3F7FC;--dim:#9BAAC0;--acc:#12A6FF;--acc2:#7C5CFF;--bad:#FF5D6C;--ok:#34D399}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent;touch-action:manipulation}
html,body{margin:0;height:100%;background:var(--bg);color:var(--txt);font:16px/1.35 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;overscroll-behavior:none}
body{display:flex;flex-direction:column;padding:env(safe-area-inset-top) 0 env(safe-area-inset-bottom)}
header{padding:12px 14px 8px;display:flex;align-items:center;gap:12px}
#dot{width:10px;height:10px;border-radius:50%;background:var(--bad);flex:none;transition:background .3s}
#dot.on{background:var(--ok)}
#badge{min-width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,var(--acc),var(--acc2));display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;padding:0 8px}
#nowname{font-weight:700;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#nowsub{color:var(--dim);font-size:13px}
#nowbox{min-width:0;flex:1}
#modes{display:flex;gap:8px;padding:4px 14px 8px}
#modes button{flex:1;padding:10px 6px;border-radius:14px;border:1px solid var(--line);background:var(--card);color:var(--txt);font-size:15px;font-weight:600}
#modes button.act{background:linear-gradient(135deg,var(--acc),var(--acc2));border-color:transparent}
main{flex:1;overflow:auto;padding:6px 14px 14px;-webkit-overflow-scrolling:touch}
section{display:none}section.show{display:block}
.btn{border:1px solid var(--line);background:var(--card);color:var(--txt);border-radius:16px;font-size:18px;font-weight:700;padding:0;min-height:56px;user-select:none;-webkit-user-select:none}
.btn:active{background:var(--card2);transform:scale(.97)}
.btn.acc{background:linear-gradient(135deg,var(--acc),var(--acc2));border-color:transparent}
.btn.small{font-size:14px;min-height:46px;font-weight:600}
.pad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;max-width:320px;margin:10px auto}
.pad .btn{min-height:68px;font-size:26px}
.row{display:grid;gap:10px;margin:10px 0}
.r2{grid-template-columns:repeat(2,1fr)}.r3{grid-template-columns:repeat(3,1fr)}.r4{grid-template-columns:repeat(4,1fr)}
.lbl{color:var(--dim);font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin:16px 2px 4px}
input[type=search],input[type=text]{width:100%;padding:14px;border-radius:14px;border:1px solid var(--line);background:var(--card);color:var(--txt);font-size:17px;outline:none}
input:focus{border-color:var(--acc)}
.cat{color:var(--dim);font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin:16px 4px 6px}
.ch{display:flex;align-items:center;gap:12px;width:100%;text-align:left;padding:12px;border-radius:14px;border:1px solid var(--line);background:var(--card);color:var(--txt);font-size:16px;margin-bottom:6px}
.ch.cur{border-color:var(--acc);background:var(--card2)}
.ch b{min-width:38px;color:var(--acc);font-variant-numeric:tabular-nums}
.note{color:var(--dim);font-size:14px;padding:10px 4px}
footer{display:flex;border-top:1px solid var(--line);background:var(--card)}
footer button{flex:1;padding:12px 4px 10px;background:none;border:0;color:var(--dim);font-size:13px;font-weight:600}
footer button.act{color:var(--acc)}
footer button span{display:block;font-size:20px}
#banner{display:none;position:fixed;left:12px;right:12px;top:calc(10px + env(safe-area-inset-top));padding:12px 14px;border-radius:14px;background:var(--bad);color:#fff;font-weight:600;z-index:9}
#numpad{display:none}#numpad.show{display:grid}
</style>
</head>
<body>
<div id="banner"></div>
<header>
  <div id="dot"></div>
  <div id="badge">–</div>
  <div id="nowbox"><div id="nowname">Csatlakozás…</div><div id="nowsub"></div></div>
</header>
<div id="modes"></div>

<main>
<section id="tab-remote" class="show">
  <div class="pad">
    <span></span><button class="btn" data-rep data-cmd='{"cmd":"key","name":"up"}'>▲</button><span></span>
    <button class="btn" data-rep data-cmd='{"cmd":"key","name":"left"}'>◀</button>
    <button class="btn acc" data-cmd='{"cmd":"key","name":"enter"}'>OK</button>
    <button class="btn" data-rep data-cmd='{"cmd":"key","name":"right"}'>▶</button>
    <span></span><button class="btn" data-rep data-cmd='{"cmd":"key","name":"down"}'>▼</button><span></span>
  </div>
  <div class="row r2">
    <button class="btn small" data-cmd='{"cmd":"key","name":"back"}'>↩ Vissza</button>
    <button class="btn small" data-cmd='{"cmd":"key","name":"esc"}'>✕ Bezár</button>
  </div>
  <div class="row r3">
    <button class="btn small" data-cmd='{"cmd":"key","name":"menu"}'>☰ Lista</button>
    <button class="btn small" data-cmd='{"cmd":"key","name":"source"}'>⇄ Forrás</button>
    <button class="btn small" data-cmd='{"cmd":"key","name":"settings"}'>⚙ Beállítás</button>
  </div>

  <div class="lbl">Hangerő <span id="vol"></span></div>
  <div class="row r3">
    <button class="btn" data-rep data-cmd='{"cmd":"volume","delta":-5}'>🔉 −</button>
    <button class="btn" data-cmd='{"cmd":"mute"}' id="mutebtn">🔇</button>
    <button class="btn" data-rep data-cmd='{"cmd":"volume","delta":5}'>🔊 +</button>
  </div>

  <div class="lbl">Csatorna</div>
  <div class="row r2">
    <button class="btn" data-cmd='{"cmd":"zap","dir":-1}'>CH ▼</button>
    <button class="btn" data-cmd='{"cmd":"zap","dir":1}'>CH ▲</button>
  </div>
  <button class="btn small" style="width:100%" id="numtoggle">123 Számbillentyűk</button>
  <div id="numpad" class="row r3">
    <button class="btn" data-cmd='{"cmd":"digit","value":"1"}'>1</button><button class="btn" data-cmd='{"cmd":"digit","value":"2"}'>2</button><button class="btn" data-cmd='{"cmd":"digit","value":"3"}'>3</button>
    <button class="btn" data-cmd='{"cmd":"digit","value":"4"}'>4</button><button class="btn" data-cmd='{"cmd":"digit","value":"5"}'>5</button><button class="btn" data-cmd='{"cmd":"digit","value":"6"}'>6</button>
    <button class="btn" data-cmd='{"cmd":"digit","value":"7"}'>7</button><button class="btn" data-cmd='{"cmd":"digit","value":"8"}'>8</button><button class="btn" data-cmd='{"cmd":"digit","value":"9"}'>9</button>
    <span></span><button class="btn" data-cmd='{"cmd":"digit","value":"0"}'>0</button><button class="btn acc" data-cmd='{"cmd":"key","name":"enter"}'>OK</button>
  </div>
</section>

<section id="tab-channels">
  <div class="row r2" id="listmodes"></div>
  <input type="search" id="filter" placeholder="Keresés a csatornák között…" autocomplete="off" autocapitalize="off">
  <div id="chlist"></div>
</section>

<section id="tab-youtube">
  <div class="lbl">Keresés a YouTube-on</div>
  <input type="search" id="ytq" placeholder="Mit keresel? (vagy illessz be egy YouTube-linket)" enterkeyhint="search" autocomplete="off">
  <div class="row r2">
    <button class="btn acc" id="ytgo">🔍 Keresés / megnyitás</button>
    <button class="btn" id="ythome" data-mode="youtube">▶ YouTube kezdőlap</button>
  </div>
  <div class="note" id="ytnote"></div>
  <div class="note">A találatok a TV-n jelennek meg; a „Távirányító” fülön a nyilakkal és az OK gombbal választhatsz.</div>
</section>
</main>

<footer id="tabs">
  <button data-tab="remote" class="act"><span>🎮</span>Távirányító</button>
  <button data-tab="channels"><span>📺</span>Csatornák</button>
  <button data-tab="youtube" id="tabyt"><span>▶️</span>YouTube</button>
</footer>

<script>
(function(){
"use strict";
var $=function(s){return document.querySelector(s)},$$=function(s){return Array.prototype.slice.call(document.querySelectorAll(s))};
var token=null,catalog=null,state=null,listMode=null,failures=0,fetching=false;

try{var q=new URLSearchParams(location.search).get("t");
  if(q){localStorage.setItem("tvbox_t",q);history.replaceState(null,"",location.pathname);token=q}
  else token=localStorage.getItem("tvbox_t")}catch(e){}

function banner(msg){var b=$("#banner");if(!msg){b.style.display="none";return}b.textContent=msg;b.style.display="block"}
function vib(){try{navigator.vibrate&&navigator.vibrate(8)}catch(e){}}

function api(path,body){
  var opt={headers:{"X-Token":token||""},cache:"no-store"};
  if(body){opt.method="POST";opt.headers["Content-Type"]="application/json";opt.body=JSON.stringify(body)}
  return fetch(path,opt).then(function(r){
    if(r.status===401){banner("Az engedély érvénytelen – olvasd be újra a QR-kódot a TV-n (R gomb).");throw new Error("401")}
    if(r.status===429){banner("Túl sok hibás próbálkozás – várj egy percet.");throw new Error("429")}
    if(!r.ok)throw new Error(String(r.status));
    return r.json()});
}
function send(cmd){vib();api("/api/cmd",cmd).then(function(){setTimeout(poll,180)}).catch(function(){})}

function bindRepeat(el,fn){
  var t=null,i=null;function stop(){clearTimeout(t);clearInterval(i);t=i=null}
  el.addEventListener("pointerdown",function(e){e.preventDefault();fn();t=setTimeout(function(){i=setInterval(fn,130)},380)});
  ["pointerup","pointerleave","pointercancel"].forEach(function(ev){el.addEventListener(ev,stop)});
  el.addEventListener("contextmenu",function(e){e.preventDefault()});
}
$$("[data-cmd]").forEach(function(b){
  var cmd=JSON.parse(b.getAttribute("data-cmd"));
  if(b.hasAttribute("data-rep"))bindRepeat(b,function(){send(cmd)});
  else b.addEventListener("click",function(){send(cmd)});
});
$("#numtoggle").addEventListener("click",function(){$("#numpad").classList.toggle("show")});

function showTab(name){
  $$("section").forEach(function(s){s.classList.toggle("show",s.id==="tab-"+name)});
  $$("#tabs button").forEach(function(b){b.classList.toggle("act",b.getAttribute("data-tab")===name)});
  if(name==="channels")renderList();
}
$$("#tabs button").forEach(function(b){b.addEventListener("click",function(){showTab(b.getAttribute("data-tab"))})});

function setMode(m){send({cmd:"mode",mode:m})}
$("#ythome").addEventListener("click",function(){setMode("youtube");showTab("remote")});

function renderModes(){
  if(!catalog)return;var box=$("#modes");
  if(box.childNodes.length!==catalog.modes.length){
    box.innerHTML="";
    catalog.modes.forEach(function(m){var b=document.createElement("button");b.setAttribute("data-m",m.key);
      b.textContent=m.icon+" "+m.label;b.addEventListener("click",function(){vib();setMode(m.key)});box.appendChild(b)});
  }
  $$("#modes button").forEach(function(b){b.classList.toggle("act",!!state&&b.getAttribute("data-m")===state.active)});
}

function renderList(){
  if(!catalog)return;
  var modes=catalog.modes.filter(function(m){return catalog.channels[m.key]});
  if(!listMode||!catalog.channels[listMode])listMode=(state&&catalog.channels[state.mode])?state.mode:(modes[0]&&modes[0].key);
  var lm=$("#listmodes");lm.innerHTML="";
  modes.forEach(function(m){var b=document.createElement("button");b.className="btn small"+(m.key===listMode?" acc":"");
    b.textContent=m.icon+" "+m.label;b.addEventListener("click",function(){listMode=m.key;renderList()});lm.appendChild(b)});
  var f=$("#filter").value.trim().toLowerCase(),box=$("#chlist");box.innerHTML="";
  (catalog.channels[listMode]||[]).forEach(function(cat){
    var items=cat.items.filter(function(it){return !f||it.n.toLowerCase().indexOf(f)>=0||it.k===f});
    if(!items.length)return;
    var h=document.createElement("div");h.className="cat";h.textContent=cat.cat;box.appendChild(h);
    items.forEach(function(it){var b=document.createElement("button");
      var cur=state&&state.active===listMode&&state.mode===listMode&&state.now&&state.now.key===it.k;
      b.className="ch"+(cur?" cur":"");
      var n=document.createElement("b");n.textContent=it.k;var t=document.createElement("span");t.textContent=it.n;
      b.appendChild(n);b.appendChild(t);
      b.addEventListener("click",function(){send({cmd:"channel",mode:listMode,key:it.k});showTab("remote")});
      box.appendChild(b)});
  });
}
$("#filter").addEventListener("input",renderList);

function youtubeUI(){
  var yt=state?state.youtube:"off",has=!!catalog&&catalog.modes.some(function(m){return m.key==="youtube"});
  $("#tabyt").style.display=has?"":"none";
  var note=$("#ytnote"),go=$("#ytgo"),q=$("#ytq");
  var ok=(yt==="embedded");go.disabled=!ok;q.disabled=!ok;go.style.opacity=ok?"1":".5";
  note.textContent=ok?"":"A YouTube külön böngészőablakban fut, ezért a keresés innen nem érhető el (a beépített mód a YOUTUBE_EMBEDDED beállítással kapcsolható be).";
}
function ytSearch(){var t=$("#ytq").value.trim();if(!t)return;send({cmd:"youtube",text:t});$("#ytq").blur();showTab("remote")}
$("#ytgo").addEventListener("click",ytSearch);
$("#ytq").addEventListener("keydown",function(e){if(e.key==="Enter")ytSearch()});

var STATUS={loading:"Csatlakozás…",buffering:"Pufferelés…",error:"Nem érhető el",web:"YouTube"};
function render(){
  if(!state)return;
  var dot=$("#dot");dot.classList.add("on");
  var now=state.now||{};
  $("#badge").textContent=state.active==="youtube"?"▶":(now.key||"–");
  $("#nowname").textContent=state.active==="youtube"?"YouTube":(now.name||"–");
  var sub=[];if(state.status&&STATUS[state.status]&&state.active!=="youtube")sub.push(STATUS[state.status]);
  if(state.preview)sub.push("Váltás erre: "+state.preview.key+" "+state.preview.name);
  $("#nowsub").textContent=sub.join(" · ");
  $("#vol").textContent=state.muted?"· némítva":("· "+state.volume+"%");
  $("#mutebtn").textContent=state.muted?"🔈":"🔇";
  renderModes();youtubeUI();
  if($("#tab-channels").classList.contains("show"))renderList();
}

function poll(){
  if(fetching||document.hidden)return;fetching=true;
  api("/api/state").then(function(s){failures=0;banner("");state=s;
    if(!catalog)return api("/api/channels").then(function(c){catalog=c});
  }).then(render).catch(function(e){
    failures++;$("#dot").classList.remove("on");
    if(failures>=3&&String(e.message)!=="401"&&String(e.message)!=="429")banner("Nincs kapcsolat a TV Box-szal…");
  }).then(function(){fetching=false});
}
document.addEventListener("visibilitychange",function(){if(!document.hidden)poll()});
if(!token){banner("Nincs engedély – olvasd be a QR-kódot a TV-n (R gomb).");}
else{poll();setInterval(poll,1000)}
})();
</script>
</body>
</html>
"""
