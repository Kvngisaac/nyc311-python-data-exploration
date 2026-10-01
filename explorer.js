'use strict';
const data=window.NYC311_DATA,core=window.NYC311Core;
const $=id=>document.getElementById(id);
const agency=$('agency-filter'),borough=$('borough-filter');
const fmt=new Intl.NumberFormat('en-GB');
const count=n=>fmt.format(n);
const hours=n=>n==null?'—':n.toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2})+' h';
const pct=n=>n==null?'—':(n*100).toFixed(2)+'%';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
agency.innerHTML='<option value="all">All agencies</option>'+data.agencies.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');
borough.innerHTML='<option value="all">All boroughs</option>'+data.boroughs.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');
agency.value='all';borough.value='all';
let activeView=core.selectView(data),activeScope='All agencies · All boroughs';

function countRows(rows,nameField='name') {return rows.map(r=>`<tr><th scope="row">${esc(r[nameField])}</th><td>${count(r.requests)}</td></tr>`).join('');}
function reportRows(rows) {return rows.map(r=>`<tr><th scope="row">${esc(r.name)}</th><td>${count(r.requests)}</td><td>${pct(r.requests/activeView.metrics.requests)}</td><td>${count(r.timing_eligible)}</td><td>${hours(r.median_hours)}</td><td>${hours(r.p90_hours)}</td></tr>`).join('');}
function bars(rows,labelField) {
 const max=Math.max(1,...rows.map(r=>r.requests));
 return rows.map(r=>`<div class="bar-row"><span class="bar-label">${esc(r[labelField])}</span><div class="bar-track" aria-hidden="true"><span style="width:${r.requests/max*100}%"></span></div><strong>${count(r.requests)}</strong></div>`).join('');
}
function render() {
 activeView=core.selectView(data,agency.value,borough.value);
 activeScope=(agency.value==='all'?'All agencies':agency.value)+' · '+(borough.value==='all'?'All boroughs':borough.value);
 const v=activeView,m=v.metrics;
 $('scope-title').textContent=activeScope;
 $('request-total').textContent=count(m.requests);
 $('timed-total').textContent=count(m.timing_eligible);
 $('median-time').textContent=hours(m.median_hours);
 $('p90-time').textContent=hours(m.p90_hours);
 $('coverage-note').textContent=m.requests?`${pct(m.timing_eligible/m.requests)} of requests have usable closure times`:'No requests in this slice';
 $('scope-detail').textContent=m.requests?`${count(m.closed_status)} recorded Closed; ${count(m.closed_excluded_from_timing)} Closed records excluded from timing; ${count(m.not_closed_status)} have another status. ${pct(m.within_24h_share_of_eligible)} of eligible closed records are within 24 hours. Mean: ${hours(m.mean_hours)}. Zero durations: ${count(m.zero_duration)}. Long durations remain included.`:'This agency/borough combination has no requests in the pinned January cohort. Timing metrics are unavailable.';
 $('empty-slice').hidden=!!m.requests;
 $('slice-panels').hidden=!m.requests;
 $('export-csv').disabled=!m.requests;
 $('reset-filters').disabled=agency.value==='all'&&borough.value==='all';
 const dailyMax=Math.max(1,...v.daily.map(r=>r.requests));
 $('daily-chart').innerHTML=v.daily.map((r,i)=>`<div class="day-column"><span class="day-value" aria-hidden="true" style="height:${r.requests/dailyMax*100}%" title="${esc(r.day)}: ${count(r.requests)} requests"></span><span class="day-label" aria-hidden="true">${i===0||i===30||((i+1)%5===0)?i+1:''}</span></div>`).join('');
 $('daily-table-body').innerHTML=countRows(v.daily,'day');
 $('hourly-table-body').innerHTML=countRows(v.hourly,'hour');
 $('problem-chart').innerHTML=bars(v.problems.slice(0,8),'name');
 $('problem-table-body').innerHTML=reportRows(v.problems);
 $('channel-table-body').innerHTML=reportRows(v.channels);
 $('duration-chart').innerHTML=bars(v.duration_bins,'label');
 $('duration-table-body').innerHTML=countRows(v.duration_bins,'label');
 $('status-table-body').innerHTML=countRows(v.statuses);
 $('duration-note').textContent=`${count(m.timing_eligible)} eligible records. ${count(m.upper_iqr_outliers)} exceed the whole-cohort IQR fence; they remain in the metrics. ${count(m.negative_duration)} records in this slice have a negative date interval; none are used for timing.`;
 $('report-status').textContent=`Showing ${count(m.requests)} requests for ${activeScope}.`;
}
agency.addEventListener('change',render);borough.addEventListener('change',render);
$('reset-filters').addEventListener('click',()=>{agency.value='all';borough.value='all';render();agency.focus();});
$('empty-reset').addEventListener('click',()=>{agency.value='all';borough.value='all';render();agency.focus();});
$('export-csv').addEventListener('click',()=>{
 if(!activeView.metrics.requests)return;
 const text=core.reportCsv(activeView,activeScope,data.snapshot_utc);
 const blob=new Blob([text],{type:'text/csv;charset=utf-8;'}),url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='nyc311-jan2024-'+agency.value.replace(/[^a-z0-9]+/gi,'-')+'-'+borough.value.replace(/[^a-z0-9]+/gi,'-')+'.csv';
 document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
});
$('snapshot-date').textContent=data.snapshot_utc.slice(0,10);
const q=data.quality;
$('quality-table-body').innerHTML=Object.entries(q.normalized_missing_count).map(([field,n])=>`<tr><th scope="row">${esc(field)}</th><td>${count(q.raw_blank_count[field])}</td><td>${count(n)}</td><td>${pct(n/q.raw_rows)}</td></tr>`).join('');
const comparisons=data.same_problem_comparisons['HEAT/HOT WATER'];
$('comparison-table-body').innerHTML=comparisons.map(r=>`<tr><th scope="row">${esc(r.name)}</th><td>${count(r.requests)}</td><td>${count(r.timing_eligible)}</td><td>${hours(r.median_hours)}</td><td>${hours(r.p90_hours)}</td></tr>`).join('');
render();
