"""The single-page form served at `/`.

Deliberately plain, and deliberately thin. Every number it shows comes from a
POST to /evaluate -- there is no physics here. That is the whole design
constraint: a JavaScript transfer-matrix solver would be a second
implementation of the model with nothing comparing the two, which is the defect
class this project has already been bitten by twice.
"""

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>pvdlowe</title>
<style>
 body{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;
      background:#f6f8fa;color:#16202e}
 .wrap{max-width:860px;margin:0 auto;padding:28px 20px 60px}
 h1{font-family:Georgia,serif;font-size:30px;margin:0 0 4px;color:#16202e}
 .sub{color:#7a8899;margin:0 0 24px;font-size:14px}
 .card{background:#fff;border:1px solid #e2e8ef;border-radius:8px;
       padding:20px 22px;margin-bottom:18px}
 label{display:block;font-size:12px;font-weight:600;color:#42505f;
       margin-bottom:4px;letter-spacing:.02em}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px}
 input,select{width:100%;padding:7px 9px;border:1px solid #cfd8e3;border-radius:5px;
              font:inherit;font-size:14px;box-sizing:border-box;background:#fff}
 button{background:#065a82;color:#fff;border:0;border-radius:5px;padding:9px 20px;
        font:inherit;font-weight:600;cursor:pointer;margin-top:16px}
 button:hover{background:#054a6c}
 button:disabled{background:#9fb3c2;cursor:default}
 table{border-collapse:collapse;width:100%;font-size:14px;margin-top:4px}
 th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;
    color:#065a82;border-bottom:1.5px solid #065a82;padding:5px 8px}
 td{padding:6px 8px;border-bottom:1px solid #eef2f6}
 td.n{text-align:right;font-variant-numeric:tabular-nums}
 .ok{color:#1f7a5c;font-weight:600}
 .bad{color:#b8532f;font-weight:600}
 .note{font-size:12.5px;color:#7a8899;margin-top:14px;line-height:1.5}
 .warn{background:#fcf6f3;border-left:3px solid #e8845c;padding:11px 14px;
       font-size:13px;border-radius:0 5px 5px 0;margin-top:14px;color:#42505f}
 .err{background:#fcf1ee;border-left:3px solid #b8532f;padding:11px 14px;
      font-size:13.5px;border-radius:0 5px 5px 0;color:#8f3f22}
 a{color:#065a82}
</style></head><body><div class="wrap">

<h1>pvdlowe</h1>
<p class="sub">Low-emissivity coating evaluation. Every figure is computed in
Python by the same code the CLI and test suite use &mdash; nothing is
calculated in this page.</p>

<div class="card">
  <div class="grid">
    <div><label>Dielectric</label><select id="dielectric">
      <option>AZO</option><option>Si3N4</option><option>ZnO</option>
      <option>SnO2</option><option>TiO2</option><option>ITO</option>
      <option>GZO</option><option>FTO</option></select></div>
    <div><label>Silver fraction (at.)</label>
      <input id="ag" type="number" value="1.0" min="0" max="1" step="0.05"></div>
    <div><label>Microstructure</label><select id="mix">
      <option value="solid_solution">solid solution</option>
      <option value="ema">segregated</option></select></div>
    <div><label>Metal (nm)</label>
      <input id="m" type="number" value="10" min="1" max="60" step="0.5"></div>
    <div><label>Bottom oxide (nm)</label>
      <input id="b" type="number" value="35" min="0" max="400" step="5"></div>
    <div><label>Top oxide (nm)</label>
      <input id="t" type="number" value="35" min="0" max="400" step="5"></div>
  </div>
  <button id="go" onclick="run()">Evaluate</button>
</div>

<div id="out"></div>

<p class="note">Specification: T<sub>vis</sub> &ge; 0.80, R<sub>s</sub> &le; 5.0
&Omega;/sq, &epsilon;<sub>h</sub> &le; 0.10. Also at
<a href="/docs">/docs</a>, <a href="/candidates">/candidates</a>,
<a href="/weight-sweep">/weight-sweep</a>, <a href="/validate">/validate</a>.</p>

<script>
const F = (x,n) => (x===null||x===undefined) ? "&mdash;" : Number(x).toFixed(n);

async function run(){
  const btn = document.getElementById('go');
  btn.disabled = true; btn.textContent = 'Evaluating\\u2026';
  const body = {
    dielectric: document.getElementById('dielectric').value,
    ag_fraction: parseFloat(document.getElementById('ag').value),
    mixing_model: document.getElementById('mix').value,
    metal_nm: parseFloat(document.getElementById('m').value),
    bottom_nm: parseFloat(document.getElementById('b').value),
    top_nm: parseFloat(document.getElementById('t').value)
  };
  let d;
  try{
    const r = await fetch('/evaluate', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    d = await r.json();
    if(!r.ok) throw new Error(d.error || 'request failed');
  }catch(e){
    document.getElementById('out').innerHTML =
      '<div class="card"><div class="err">'+e.message+'</div></div>';
    btn.disabled=false; btn.textContent='Evaluate'; return;
  }
  const p = d.performance, s = d.spec;
  const row = (k,v,unit,bad) =>
    `<tr><td>${k}</td><td class="n ${bad?'bad':''}">${v}</td><td>${unit||''}</td></tr>`;
  document.getElementById('out').innerHTML = `
   <div class="card">
    <table>
     <tr><th>Quantity</th><th style="text-align:right">Value</th><th></th></tr>
     ${row('Visible transmittance', F(p.T_vis,3), '', s.failures.includes('T_vis'))}
     ${row('Solar transmittance', F(p.T_sol,3), '')}
     ${row('Emissivity (hemispherical)', F(p.emissivity_hemispherical,4), '',
           s.failures.includes('emissivity'))}
     ${row('Sheet resistance', F(p.R_sheet,2), '\\u03a9/sq',
           s.failures.includes('R_sheet'))}
     ${row('Solar heat gain g', F(p.g_value,3), '')}
     ${row('Light-to-solar-gain', F(p.LSG,2), '')}
     ${row('U-value, centre pane', F(p.U_g,2), 'W/m\\u00b2K')}
     ${row('Silver', F(p.Ag_g_per_m2,4), 'g/m\\u00b2')}
     ${row('Score', F(d.score,1), '')}
    </table>
    <p class="note">
      <b class="${s.meets_spec?'ok':'bad'}">
        ${s.meets_spec ? 'Meets specification'
          : 'Fails: ' + (s.failures.join(', ') || 'percolation')}</b>
      ${s.note ? ' &mdash; ' + s.note : ''}<br>
      Limiting criterion: <b>${d.limiting_criterion || '\\u2014'}</b>
    </p>
    <div class="warn">${d.caveat}</div>
   </div>`;
  btn.disabled=false; btn.textContent='Evaluate';
}
run();
</script>
</div></body></html>
"""

__all__ = ["PAGE"]
