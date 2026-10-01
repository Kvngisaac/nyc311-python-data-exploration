const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=(process.env.PORTFOLIO_CHECKOUT||'/workspace/sites/justin-data-portfolio')+'/dist/';
class Element {
 constructor(id=''){this.id=id;this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.checked=false;this.attrs={};this.dataset={};this.listeners={};this.isConnected=true;this.classes=new Set();this.classList={toggle:(n,on)=>on?this.classes.add(n):this.classes.delete(n),add:n=>this.classes.add(n),remove:n=>this.classes.delete(n)}}
 setAttribute(k,v){this.attrs[k]=v}getAttribute(k){return this.attrs[k]}removeAttribute(k){delete this.attrs[k]}
 addEventListener(n,fn){(this.listeners[n]??=[]).push(fn)}emit(n,e={}){for(const f of this.listeners[n]??[])f(e)}focus(){document.activeElement=this}showModal(){this.open=true}close(){this.open=false;this.emit('close')}getBoundingClientRect(){return {left:10,top:10,right:600,bottom:600}}
}
const markup=fs.readFileSync(base+'index.html','utf8');
const elements=Object.fromEntries([...markup.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new Element(m[1])]));
const chips=['all','SQL','Python','Pandas','JavaScript','Git'].map(tool=>{const e=new Element();e.dataset.tool=tool;return e});
const measures=['net_pence','gross_pence','credit_pence'].map(key=>{const e=new Element();e.dataset.measure=key;return e});
const nav=['projects','skills','about'].map(id=>{const e=new Element();e.attrs.href='#'+id;e.hash='#'+id;return e});
const document={activeElement:null,body:new Element('body'),getElementById:id=>elements[id]??null,querySelectorAll:s=>s==='[data-tool]'?chips:s==='[data-measure]'?measures:nav};
const context=vm.createContext({document,window:{},URL,Date,Intl,console});
for(const file of ['retail-data.js','app.js','retail.js'])vm.runInContext(fs.readFileSync(base+file,'utf8'),context);
const cards=()=>[...elements['project-grid'].innerHTML.matchAll(/<article[^>]*data-id="([^"]+)"/g)].map(m=>m[1]);
assert.deepEqual(cards(),['sql','python','dashboard','pipeline']);
// Private repository link checks: completed cards and write-ups only.
const repo='https://github.com/Kvngisaac/retail-sales-analysis';
assert.equal((elements['project-grid'].innerHTML.match(new RegExp('href="'+repo+'"','g'))||[]).length,2);
assert.equal((elements['project-grid'].innerHTML.match(/GitHub link pending/g)||[]).length,1);
assert.ok(markup.includes('href="'+repo+'"'));
assert.equal(vm.runInContext("safeRepoUrl('javascript:alert(1)')",context),null);
assert.equal(vm.runInContext("safeRepoUrl('https://user:secret@github.com/Kvngisaac/retail-sales-analysis')",context),null);

assert.equal((elements['project-grid'].innerHTML.match(/PUBLISHED STUDY/g)||[]).length,2); // preview + badge
assert.equal((elements['project-grid'].innerHTML.match(/PUBLISHED DASHBOARD/g)||[]).length,2);
assert.equal((elements['project-grid'].innerHTML.match(/>PLACEHOLDER</g)||[]).length,1);
for(const [tool,ids] of Object.entries({SQL:['sql','dashboard','pipeline'],Python:['sql','python','pipeline'],Pandas:['python'],JavaScript:['dashboard'],Git:['python','pipeline']})){chips.find(e=>e.dataset.tool===tool).emit('click');assert.deepEqual(cards(),ids)}
elements['reset-filters'].emit('click');
for(const [area,ids]of Object.entries({Analysis:['sql','python','dashboard'],'Data quality':['sql','python','pipeline'],Visualization:['sql','python','dashboard'],Pipelines:['pipeline']})){elements['skill-filter'].value=area;elements['skill-filter'].emit('change');assert.deepEqual(cards(),ids)}
chips.find(e=>e.dataset.tool==='JavaScript').emit('click');assert.equal(cards().length,0);assert.equal(elements['empty-state'].hidden,false);elements['empty-reset'].emit('click');assert.equal(cards().length,4);
for(const id of ['sql','python','dashboard','pipeline']){const trigger=new Element();trigger.dataset.project=id;elements['project-grid'].emit('click',{target:{closest:()=>trigger}});assert.ok(elements['project-dialog'].open);assert.equal((elements['write-up'].innerHTML.match(/<dt>/g)||[]).length,6);if(['sql','dashboard'].includes(id)){assert.ok(elements['dialog-bottom'].innerHTML.includes('href="'+repo+'"'));assert.ok(elements['dialog-bottom'].innerHTML.includes('noopener noreferrer'));assert.ok(elements['dialog-bottom'].innerHTML.includes('Private repository'));}else{assert.ok(!elements['dialog-bottom'].innerHTML.includes(repo));}if(id==='sql'){assert.equal(elements['dialog-state'].textContent,'PUBLISHED STUDY');assert.ok(elements['write-up'].innerHTML.includes('£9,748,131.07'));assert.ok(elements['dialog-bottom'].innerHTML.includes('download'))}else if(id==='dashboard'){assert.equal(elements['dialog-state'].textContent,'PUBLISHED DASHBOARD');assert.ok(elements['dialog-bottom'].innerHTML.includes('downloads/retail-dashboard.zip'));assert.ok(elements['dialog-bottom'].innerHTML.includes('href="dashboard/"'));assert.ok(elements['write-up'].innerHTML.includes('66,939'));}else if(id==='python'){assert.equal(elements['dialog-state'].textContent,'PUBLISHED PYTHON STUDY');assert.ok(elements['dialog-bottom'].innerHTML.includes('https://github.com/Kvngisaac/nyc311-python-data-exploration'));assert.ok(elements['dialog-bottom'].innerHTML.includes('downloads/nyc311-python-data-exploration.zip'));assert.ok(elements['dialog-bottom'].innerHTML.includes('href="python-exploration/"'));assert.ok(elements['write-up'].innerHTML.includes('284,017'));}else{assert.equal(elements['dialog-state'].textContent,'PROJECT PLACEHOLDER');assert.ok(elements['dialog-notice'].textContent.includes('No dataset'))}elements['close-dialog'].emit('click');assert.equal(document.activeElement,trigger);assert.ok(!elements['project-dialog'].open)}
const expected=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'retail-ui-controls.json'),'utf8'));
let views=0;
for(const [key,control]of Object.entries(expected)){
 const [country,fullString]=key.split('|');const full=fullString==='true';
 for(const measure of ['net_pence','gross_pence','credit_pence']){
  const view=vm.runInContext('filteredRetail('+JSON.stringify(country)+','+full+','+JSON.stringify(measure)+')',context);
  assert.deepEqual(JSON.parse(JSON.stringify(view.totals)),control,key);
  assert.equal(view.monthly.length,full?12:13);
  if(full)assert.ok(!view.monthly.some(m=>m.partial));
  assert.ok(view.products.length<=5);
  for(let i=1;i<view.products.length;i++)assert.ok(view.products[i-1].value>=view.products[i].value);
  views++;
 }
}
assert.equal(elements['retail-net'].textContent,'£9,748,131.07');
assert.equal((elements['monthly-bars'].innerHTML.match(/class="month-bar-row/g)||[]).length,13);
elements['retail-country'].value='United Kingdom';elements['retail-country'].emit('change');assert.equal(elements['retail-net'].textContent,'£8,189,252.30');
elements['retail-full-months'].checked=true;elements['retail-full-months'].emit('change');assert.equal((elements['monthly-bars'].innerHTML.match(/class="month-bar-row/g)||[]).length,12);assert.ok(!elements['monthly-table-body'].innerHTML.includes('(partial)'));
measures[2].emit('click');assert.ok(elements['monthly-chart-title'].textContent.includes('credit'));assert.equal(measures[2].attrs['aria-pressed'],'true');
elements['retail-reset'].emit('click');assert.equal(elements['retail-country'].value,'all');assert.equal(elements['retail-full-months'].checked,false);assert.equal(elements['retail-net'].textContent,'£9,748,131.07');assert.equal(measures[0].attrs['aria-pressed'],'true');assert.equal(document.activeElement,elements['retail-country']);
console.log('PASS: portfolio tool/skill filters, empty and reset states, published versus placeholder write-ups, modal close/focus, '+views+' country-period-measure views checked against independent SQLite totals, metric controls, partial-month toggle, and dashboard reset.');
console.log('Browser visual rendering/native keyboard behavior were not executed; checks used a DOM event harness.');
