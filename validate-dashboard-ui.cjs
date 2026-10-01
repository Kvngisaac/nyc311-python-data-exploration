const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=(process.env.PORTFOLIO_CHECKOUT||'/workspace/sites/justin-data-portfolio')+'/dist/dashboard/';
class Element{
 constructor(id=''){this.id=id;this.innerHTML='';this.textContent='';this.value='';this.checked=false;this.hidden=false;this.disabled=false;this.listeners={};this.dataset={};this.removed=false;this.clicked=false}
 addEventListener(n,f){(this.listeners[n]??=[]).push(f)}emit(n,e={}){for(const f of this.listeners[n]??[])f(e)}focus(){document.activeElement=this}click(){this.clicked=true;this.emit('click')}remove(){this.removed=true}
}
const html=fs.readFileSync(base+'index.html','utf8');
const elements=Object.fromEntries([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new Element(m[1])]));
let anchor,exportBlob,revoked=false;
const document={activeElement:null,getElementById:id=>elements[id],createElement:()=>new Element(),body:{appendChild:a=>anchor=a}};
const url={createObjectURL:blob=>{exportBlob=blob;return 'blob:test'},revokeObjectURL:()=>revoked=true};
const ctx=vm.createContext({document,window:{},Intl,Date,console,Blob,URL:url,setTimeout:f=>f()});
for(const file of ['data.js','dashboard-core.js','dashboard.js'])vm.runInContext(fs.readFileSync(base+file,'utf8'),ctx);
assert.equal(elements['net-kpi'].textContent,'£9,748,131.07');assert.equal(elements['invoice-kpi'].textContent,'19,960');assert.equal(elements['empty-range'].hidden,true);
const countries=ctx.window.DASHBOARD_DATA.countries;
elements['country'].value=String(countries.indexOf('United Kingdom'));elements['country'].emit('change');assert.equal(elements['net-kpi'].textContent,'£8,189,252.30');
elements['start-month'].value='10';elements['start-month'].emit('change');elements['end-month'].value='11';elements['end-month'].emit('change');assert.ok(elements['report-status'].textContent.includes('2 included months'));
elements['start-month'].value='12';elements['start-month'].emit('change');assert.equal(elements['end-month'].value,'12');
elements['complete-only'].checked=true;elements['complete-only'].emit('change');assert.equal(elements['net-kpi'].textContent,'—');assert.equal(elements['export'].disabled,true);assert.equal(elements['empty-range'].hidden,false);
elements['complete-only'].checked=false;elements['complete-only'].emit('change');assert.equal(elements['export'].disabled,false);assert.ok(elements['monthly-body'].innerHTML.includes('(partial)'));
elements['end-month'].value='5';elements['end-month'].emit('change');assert.equal(elements['start-month'].value,'5');
elements['measure'].value='credits';elements['measure'].emit('change');assert.ok(elements['trend-title'].textContent.includes('negative-line'));
elements['reset'].emit('click');assert.equal(elements['country'].value,'all');assert.equal(elements['start-month'].value,'0');assert.equal(elements['end-month'].value,'12');assert.equal(elements['measure'].value,'net');assert.equal(document.activeElement,elements['country']);
const monthButton=new Element();monthButton.dataset.month='11';elements['monthly-chart'].emit('click',{target:{closest:()=>monthButton}});assert.equal(elements['start-month'].value,'11');assert.equal(elements['end-month'].value,'11');assert.equal(elements['net-kpi'].textContent,'£1,456,145.80');assert.equal(document.activeElement,elements['start-month']);
elements['export'].emit('click');assert.ok(anchor.clicked&&anchor.removed&&revoked);assert.equal(anchor.download,'retail-report-2011-11-to-2011-11.csv');
(async()=>{const csv=await exportBlob.text();assert.ok(csv.includes('1456145.80'));assert.ok(csv.includes('Market context'));console.log('PASS: dashboard default totals, country changes, month-range normalization, partial-only empty state, measure selection, reset/focus, month drill-down, and actual CSV Blob/download contents. Native browser rendering/keyboard behavior not executed.');})().catch(e=>{console.error(e);process.exitCode=1});
