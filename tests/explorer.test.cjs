'use strict';
// Executes real application handlers against a minimal DOM event harness.
// This is not browser rendering, native keyboard, or assistive-technology QA.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),site=path.join(root,'site');
const model=JSON.parse(fs.readFileSync(path.join(root,'results/analysis.json'),'utf8'));
const markup=fs.readFileSync(path.join(site,'index.html'),'utf8');
const ids=[...markup.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(new Set(ids).size,ids.length,'unique HTML IDs');
for(const id of ['agency-filter','borough-filter'])assert.ok(markup.includes('for="'+id+'"'),'select label');
assert.ok(markup.includes('aria-live="polite"'));assert.ok(markup.includes('Unaffected by filters')||markup.includes('UNAFFECTED BY FILTERS'));
class Element{
 constructor(id=''){this.id=id;this.innerHTML='';this.textContent='';this.value='';this.hidden=false;this.disabled=false;this.listeners={};this.href='';this.download=''}
 addEventListener(event,fn){(this.listeners[event]??=[]).push(fn)}
 emit(event){for(const fn of this.listeners[event]??[])fn({target:this})}
 focus(){document.activeElement=this}
 click(){downloads.push({href:this.href,name:this.download})}
 remove(){removed++}
}
const elements=Object.fromEntries(ids.map(id=>[id,new Element(id)]));let blobs=[],downloads=[],removed=0,revoked=[];
const document={activeElement:null,getElementById:id=>elements[id]??null,createElement:tag=>{assert.equal(tag,'a');return new Element()},body:{appendChild:()=>{}}};
class CaptureBlob{constructor(parts,options){this.text=parts.join('');this.type=options.type;blobs.push(this)}}
const context=vm.createContext({document,window:{},Intl,console,Blob:CaptureBlob,URL:{createObjectURL:b=>{assert.ok(blobs.includes(b));return 'blob:test-'+blobs.length},revokeObjectURL:u=>revoked.push(u)}});
vm.runInContext('window=globalThis',context);
for(const file of ['data.js','explorer-core.js','explorer.js'])vm.runInContext(fs.readFileSync(path.join(site,file),'utf8'),context,{filename:file});
const plain=x=>JSON.parse(JSON.stringify(x));
for(const key of ['cohort','snapshot_utc','source_url','source_raw_sha256','agencies','boroughs','views','quality','sensitivity','same_problem_comparisons'])assert.deepEqual(plain(context.window.NYC311_DATA[key]),model[key],key+' matches validated Python output');
const core=require(path.join(site,'explorer-core.js'));
assert.throws(()=>core.selectView(model,'unknown','all'));
assert.throws(()=>core.selectView(model,'all','unknown'));
function parseCsv(text){
 let rows=[],row=[],field='',quoted=false;let s=text.replace(/^\uFEFF/,'');
 for(let i=0;i<s.length;i++){const c=s[i];if(c==='"'){if(quoted&&s[i+1]==='"'){field+='"';i++}else quoted=!quoted}
 else if(c===','&&!quoted){row.push(field);field=''}else if((c==='\r'||c==='\n')&&!quoted){if(c==='\r'&&s[i+1]==='\n')i++;row.push(field);rows.push(row);row=[];field=''}else field+=c;}
 if(field||row.length){row.push(field);rows.push(row)}assert.equal(quoted,false);return rows;
}
const f=new Intl.NumberFormat('en-GB'),h=n=>n==null?'—':n.toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2})+' h';
let views=0,empty=0,csvDownloads=0;
const initialQuality=elements['quality-table-body'].innerHTML,initialComparison=elements['comparison-table-body'].innerHTML;
for(const agency of ['all',...model.agencies])for(const borough of ['all',...model.boroughs]){
 elements['agency-filter'].value=agency;elements['borough-filter'].value=borough;elements['borough-filter'].emit('change');
 const v=model.views[agency+'|'+borough],m=v.metrics;
 assert.deepEqual(plain(core.selectView(model,agency,borough)),v);
 assert.equal(elements['request-total'].textContent,f.format(m.requests));assert.equal(elements['timed-total'].textContent,f.format(m.timing_eligible));
 assert.equal(elements['median-time'].textContent,h(m.median_hours));assert.equal(elements['p90-time'].textContent,h(m.p90_hours));
 assert.equal(elements['empty-slice'].hidden,!!m.requests);assert.equal(elements['slice-panels'].hidden,!m.requests);assert.equal(elements['export-csv'].disabled,!m.requests);
 assert.equal(elements['reset-filters'].disabled,agency==='all'&&borough==='all');
 const countTags=id=>(elements[id].innerHTML.match(/<tr>/g)||[]).length;
 assert.equal(countTags('daily-table-body'),31);assert.equal(countTags('hourly-table-body'),24);assert.equal(countTags('problem-table-body'),v.problems.length);assert.equal(countTags('channel-table-body'),v.channels.length);
 for(const [id,rows,name]of [['daily-table-body',v.daily,'day'],['hourly-table-body',v.hourly,'hour'],['duration-table-body',v.duration_bins,'label'],['status-table-body',v.statuses,'name']]){
  const rendered=[...elements[id].innerHTML.matchAll(/<tr><th scope="row">([^<]*)<\/th><td>([^<]*)<\/td><\/tr>/g)];assert.equal(rendered.length,rows.length,id);
  rows.forEach((r,i)=>{assert.equal(rendered[i][2],f.format(r.requests),id+' count')});
 }
 for(const [id,rows]of [['problem-table-body',v.problems],['channel-table-body',v.channels]]){
  const rendered=[...elements[id].innerHTML.matchAll(/<tr><th scope="row">.*?<\/th><td>([^<]*)<\/td><td>([^<]*)<\/td><td>([^<]*)<\/td><td>([^<]*)<\/td><td>([^<]*)<\/td><\/tr>/g)];assert.equal(rendered.length,rows.length);
  rows.forEach((r,i)=>{assert.deepEqual(rendered[i].slice(1),[f.format(r.requests),(r.requests/m.requests*100).toFixed(2)+'%',f.format(r.timing_eligible),h(r.median_hours),h(r.p90_hours)])});
 }
 assert.equal(elements['quality-table-body'].innerHTML,initialQuality);assert.equal(elements['comparison-table-body'].innerHTML,initialComparison);
 const csv=core.reportCsv(v,'scope',model.snapshot_utc);const parsed=parseCsv(csv);assert.equal(parsed[0].length,10);for(const row of parsed)assert.equal(row.length,10);
 // Export values are exact model values, including full category lists, not rounded display strings.
 const summary=parsed.filter(r=>r[0]==='summary');assert.ok(summary.length>0);
 for(const [section,key] of [['created_day','daily'],['created_hour','hourly'],['problem','problems'],['channel','channels'],['status','statuses'],['eligible_duration_bin','duration_bins']]){
  const actual=parsed.filter(r=>r[0]===section),expected=v[key];assert.equal(actual.length,expected.length,section);
  expected.forEach((r,i)=>{assert.equal(Number(actual[i][2]),r.requests);if(r.timing_eligible!==undefined){assert.equal(Number(actual[i][3]),r.timing_eligible);assert.equal(actual[i][4],r.median_hours==null?'':String(r.median_hours));assert.equal(actual[i][5],r.p90_hours==null?'':String(r.p90_hours))}});
 }
 const before=downloads.length;elements['export-csv'].emit('click');
 if(m.requests){assert.equal(downloads.length,before+1);assert.equal(blobs.at(-1).text,core.reportCsv(v,elements['scope-title'].textContent,model.snapshot_utc));assert.equal(blobs.at(-1).type,'text/csv;charset=utf-8;');assert.ok(downloads.at(-1).name.endsWith('.csv'));csvDownloads++}
 else{assert.equal(downloads.length,before);empty++}
 views++;
}
assert.equal(views,105);assert.ok(empty>0);assert.equal(removed,csvDownloads);assert.equal(revoked.length,csvDownloads);
elements['reset-filters'].emit('click');assert.equal(elements['agency-filter'].value,'all');assert.equal(elements['borough-filter'].value,'all');assert.equal(document.activeElement,elements['agency-filter']);assert.equal(elements['request-total'].textContent,'287,186');
const emptyKey=Object.keys(model.views).find(k=>!model.views[k].metrics.requests);let [a,b]=emptyKey.split('|');elements['agency-filter'].value=a;elements['borough-filter'].value=b;elements['agency-filter'].emit('change');elements['empty-reset'].emit('click');assert.equal(elements['request-total'].textContent,'287,186');
// Spreadsheet formulas, commas, newlines and quotes must remain inert round-trippable text.
const fixture=[['=2+2',' +cmd','@SUM(A1)','-payload','a,b','a\nb','a"b',-12.5,0,'normal']];
const safe=parseCsv(fixture.map(row=>row.map(core.csvText).join(',')).join('\r\n'));assert.deepEqual(safe[0],["'=2+2","' +cmd","'@SUM(A1)","'-payload",'a,b','a\nb','a"b','-12.5','0','normal']);
const result={status:'passed',agency_borough_views:views,empty_views:empty,nonempty_csv_download_handlers:csvDownloads,all_selected_metrics_tables_and_csv_values_checked:true,global_scope_tables_stable:true,reset_and_focus_checked:true,csv_formula_and_quoting_boundaries_checked:true,execution:'Node DOM event harness; no browser rendering/native keyboard'};
fs.writeFileSync(path.join(root,'results/interaction-validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
