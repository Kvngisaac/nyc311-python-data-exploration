(function(root) {
  'use strict';
  function selectView(data, agency='all', borough='all') {
    if(!['all',...data.agencies].includes(agency) || !['all',...data.boroughs].includes(borough)) throw new Error('Unknown report filter');
    const view=data.views[agency+'|'+borough];
    if(!view) throw new Error('Validated report view unavailable');
    return view;
  }
  function csvText(value) {
    let s=value==null?'':String(value);
    if(typeof value==='string' && /^[\s]*[=+@-]/.test(s)) s="'"+s;
    return '"'+s.replace(/"/g,'""')+'"';
  }
  function reportCsv(view, scope, snapshot) {
    const rows=[['section','item','requests','timing_eligible','median_hours','p90_hours','within_24h','closed_status','snapshot_utc','scope']];
    const add=(section,item,row)=>rows.push([section,item,row.requests??'',row.timing_eligible??'',row.median_hours??'',row.p90_hours??'',row.within_24h??'',row.closed_status??'',snapshot,scope]);
    add('summary','All requests in selected slice',view.metrics);
    rows.push(['definition','Timing requires Closed status, usable UTC-adjusted dates, nonnegative duration, and closure no later than snapshot','','','','','','',snapshot,scope]);
    rows.push(['definition','Closed is an administrative status; 24 hours is an exploratory threshold, not an SLA','','','','','','',snapshot,scope]);
    for(const row of view.daily) add('created_day',row.day,row);
    for(const row of view.hourly) add('created_hour',row.hour,row);
    for(const row of view.problems) add('problem',row.name,row);
    for(const row of view.channels) add('channel',row.name,row);
    for(const row of view.statuses) add('status',row.name,row);
    for(const row of view.duration_bins) add('eligible_duration_bin',row.label,row);
    return '\uFEFF'+rows.map(row=>row.map(csvText).join(',')).join('\r\n')+'\r\n';
  }
  const api={selectView,csvText,reportCsv};
  if(typeof module==='object' && module.exports) module.exports=api;
  root.NYC311Core=api;
})(typeof globalThis==='object'?globalThis:this);
