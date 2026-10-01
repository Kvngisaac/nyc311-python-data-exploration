'use strict';

// Published evidence is distinct from planned placeholders.
// The two retail artifacts share one private, verified source repository.
const projects = [
  { id: 'sql', number: '01', title: 'Retail sales analysis', area: 'Analysis', areas: ['Analysis', 'Data quality', 'Visualization'],
    tools: ['SQL', 'Python'], preview: '£9.75M', previewNote: 'Net invoice value across the full dataset',
    previewFoot: '2010–2011 · 541,909 original invoice lines', completed: true,
    description: 'A reproducible retail study with signed credits, an explicit duplicate policy, and interactive results.',
    plannedSkills: 'CTEs, joins, window functions, independent reconciliation',
    githubUrl: 'https://github.com/Kvngisaac/retail-sales-analysis',
    question: 'Which products and markets contribute the most net invoice value, and how does it vary by month after accounting for credits and data quality?',
    dataSource: 'UCI Online Retail, Chen (2015), DOI 10.24432/C5BW33, CC BY 4.0. 541,909 original invoice lines from 1 December 2010 to 9 December 2011. Values are in GBP. This is historical public data, not employer work.',
    approach: 'Use Python to extract the original workbook into SQLite. Preserve raw rows, remove 5,268 exact repeats under a stated policy, and exclude 2,512 nonpositive-price rows after deduplication. Retain negative quantities as credit lines and missing customer IDs in totals. Calculate each line in integer pence and use SQL for monthly, country, and product aggregation.',
    findings: 'Net invoice value is £9,748,131.07 across 19,960 sale invoices. The UK contributes 84.01%. November 2011 is the highest complete month at £1,456,145.80 net. REGENCY CAKESTAND 3 TIER leads merchandise-like SKUs at £164,459.49 net. These descriptive findings support follow-up planning questions, with no claimed causal impact or profitability.',
    validation: '14 reconciliation checks pass, including independent Python totals, every product total, no product-join fanout, and monthly/country totals. Three boundary tests cover subpenny prices, duplicates, credits, missing identifiers, and anomalies. Duplicate-policy sensitivity is reported. The final month is partial and is excluded from month-over-month growth comparisons.',
    demonstratedSkills: 'SQL CTEs, joins, GROUP BY, conditional aggregation, ROW_NUMBER, DENSE_RANK, and LAG; Python extraction, Decimal money handling, data-quality policies, and reproducibility; interactive charts with exact-value tables. AI-assisted implementation.' },
  {
    "id": "python",
    "number": "02",
    "title": "Python data exploration",
    "area": "Data quality",
    "areas": [
        "Data quality",
        "Analysis",
        "Visualization"
    ],
    "tools": [
        "Python",
        "Pandas",
        "Matplotlib",
        "Git"
    ],
    "preview": "19.10h",
    "previewNote": "Median recorded closure · eligible NYC311 records",
    "previewFoot": "287,186 requests · January 2024 creation cohort",
    "completed": true,
    "completedLabel": "PUBLISHED PYTHON STUDY",
    "link": "python-exploration/",
    "downloadFile": "downloads/nyc311-python-data-exploration.zip",
    "description": "An official NYC311 operations study: auditable Pandas cleaning, missingness and date checks, outlier investigation, and an interactive explorer.",
    "plannedSkills": "Pandas cleaning, grouping, timestamp handling, EDA, independent validation",
    "githubUrl": "https://github.com/Kvngisaac/nyc311-python-data-exploration",
    "question": "Where does service-request intake concentrate, what does recorded closure time look like, and which data-quality issues affect trustworthy operations reporting?",
    "dataSource": "City of New York / NYC311, 311 Service Requests from 2020 to Present (erm2-nwe9). All 287,186 requests created in January 2024, pinned on 1 October 2026 with 14 selected fields and source hashes. Closure may occur much later. Historical public portfolio data, not employer work.",
    "approach": "Inspect raw strings, missing tokens, duplicates, schema, and types. Normalize whitespace/nulls, retain IDs and ZIPs as text, parse New York timestamps and use UTC elapsed intervals. Keep all accepted requests in volume; calculate timing only for Closed records with valid nonnegative dates. Investigate IQR flags and zero durations without deleting valid values. Group by agency, borough, problem, channel, day, and hour; compare the same problem across boroughs.",
    "findings": "The top three problem categories account for 114,540 requests (39.88%). Among 284,017 timing-eligible records, median recorded closure is 19.10 hours, mean 317.63, and P90 668.55. There are 1,280 Closed records without a closure date and 75 negative intervals, all non-Closed. These findings support measurement audits and category review, not causal rankings, SLA compliance, or claims that problems were fixed.",
    "validation": "Independent stdlib raw-CSV calculations match 38,284 scalar comparisons and 8,105 distribution counts across all 105 filter views, group metrics, source quality audits, three sensitivity views, and 12 outlier traces. Six boundary tests, source-side controls, executed Python notebook cells, reproducible figures, and JavaScript handler/CSV tests are included. Browser rendering and native interaction QA remain unavailable.",
    "demonstratedSkills": "Python/Pandas inspection, missing-value policy, duplicate detection, string-safe IDs, datetime/timezone correction, quality flags, justified features, grouping/aggregation, quantiles, outlier sensitivity, Matplotlib figures, independent validation, reproducibility, and scope-aware interactive reporting. AI-assisted implementation."
},
  { id: 'dashboard', number: '03', title: 'Retail performance dashboard', area: 'Visualization', areas: ['Visualization', 'Analysis'],
    tools: ['JavaScript', 'SQL'], preview: '13', previewNote: 'Months of interactive retail reporting',
    previewFoot: 'country · period · measure · evidence', completed: true, completedLabel: 'PUBLISHED DASHBOARD',
    link: 'dashboard/', downloadFile: 'downloads/retail-dashboard.zip',
    description: 'An interactive report with month ranges, country filters, complete SKU rankings, and CSV export. A visualization extension of the retail SQL study.',
    plannedSkills: 'Reporting design, consistent filters, metric definitions, CSV export',
    githubUrl: 'https://github.com/Kvngisaac/retail-sales-analysis',
    question: 'How can a reviewer explore retail invoice performance by country and reporting period, inspect exact values, and export the same filtered evidence?',
    dataSource: 'The same UCI Online Retail dataset and verified cleaning policy as the retail SQL study. This dashboard is a second artifact from that case study. It is a JavaScript web dashboard, with SQL-produced aggregates. No Power BI or Excel implementation is claimed.',
    approach: 'Export all 66,939 merchandise-like SKU/country/month groups from SQLite, with compact indexed dictionaries. Use one filter predicate for KPIs, monthly values, and complete SKU rankings. Show market context across all countries in the same period and label its distinct scope. Preserve exact pence internally, partial-month flags, signed credits, and source attribution.',
    findings: 'The default view reconciles to £9,748,131.07 net invoice value and 19,960 sale invoices. Reviewers can inspect any month range and country, change the ranking measure, drill into a month, and export exact report values. Product rankings use all eligible SKUs in the selected slice, rather than a fixed overall top-20 subset.',
    validation: 'The base analysis passes 14 reconciliation checks. Dashboard totals and full SKU rankings are compared directly with SQLite across representative countries, month ranges, measures, and partial-month settings. Controls, drill-down, reset, CSV structure, and formula-safe text handling are tested. Browser visual QA remains unavailable.',
    demonstratedSkills: 'JavaScript aggregation and state management, month/country filtering, reporting scope design, accessible controls and value tables, safe CSV export, compact data modeling, and SQL reconciliation. AI-assisted implementation.' },
  { id: 'pipeline', number: '04', title: 'API-to-database pipeline', area: 'Pipelines', areas: ['Pipelines', 'Data quality'],
    tools: ['Python', 'SQL', 'Git'], preview: 'API', previewNote: 'Pipeline evidence to be added',
    previewFoot: 'extract → validate → load',
    description: 'A project slot for moving source data into a database with repeatable steps and validation.',
    plannedSkills: 'API ingestion, transformations, error handling',
    githubUrl: null, question: null, dataSource: null, approach: null, findings: null, validation: null, demonstratedSkills: null }
];

const linkIcon = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7 .1l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7-.1l-3 3a5 5 0 0 0 7 7l2-2"></path></svg>';
const grid = document.getElementById('project-grid');
const count = document.getElementById('result-count');
const areaSelect = document.getElementById('skill-filter');
const chips = [...document.querySelectorAll('[data-tool]')];
const reset = document.getElementById('reset-filters');
const empty = document.getElementById('empty-state');
const dialog = document.getElementById('project-dialog');
let selectedTool = 'all';
let selectedArea = 'all';
let lastTrigger = null;

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function safeRepoUrl(value) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'github.com' && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

function repoMarkup(project) {
  const url = safeRepoUrl(project.githubUrl);
  return url
    ? `<a class="github-link" href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${linkIcon}View code<span class="sr-only"> on GitHub (private repository; opens in a new tab)</span></a>`
    : `<span class="repo-pending">${linkIcon}GitHub link pending</span>`;
}

function cardMarkup(project) {
  return `<article class="project-card" data-id="${escapeHTML(project.id)}" aria-labelledby="title-${project.id}">
    <div class="card-preview" aria-label="${escapeHTML(project.previewNote)}">
      <div class="preview-top"><span class="preview-number">${project.number} / ${project.completed ? escapeHTML(project.completedLabel || 'PUBLISHED STUDY') : 'PROJECT SLOT'}</span><span class="preview-type">${escapeHTML(project.area.toUpperCase())}</span></div>
      <div class="preview-middle"><span class="preview-big" aria-hidden="true">${escapeHTML(project.preview)}</span><span class="preview-caption">${escapeHTML(project.previewNote)}</span></div>
      <span class="preview-footer">${escapeHTML(project.previewFoot)}</span>
    </div>
    <div class="card-body">
      <div class="card-eyebrow"><span class="placeholder-label ${project.completed ? 'published-status' : ''}">${project.completed ? escapeHTML(project.completedLabel || 'PUBLISHED STUDY') : 'PLACEHOLDER'}</span><span class="card-area">${project.completed ? 'Evidence published' : 'Evidence pending'}</span></div>
      <h3 id="title-${project.id}" class="card-title">${escapeHTML(project.title)}</h3>
      <p class="card-description">${escapeHTML(project.description)}</p>
      <div><span class="small-label">${project.completed ? 'Tools used' : 'Planned tools'}</span><div class="tools-row">${project.tools.map(tool=>`<span class="tool-tag">${escapeHTML(tool)}</span>`).join('')}</div></div>
      <div class="skills-preview"><span class="small-label">${project.completed ? 'Skills shown by this study' : 'Skills to demonstrate'}</span><p>${escapeHTML(project.plannedSkills)}</p></div>
    </div>
    <div class="card-bottom"><button type="button" class="outline-button" data-project="${project.id}" aria-haspopup="dialog" aria-label="Read ${escapeHTML(project.title)} write-up">Project write-up</button>${project.completed ? `<a class="github-link" href="${escapeHTML(project.link || '#retail-analysis')}">${project.id==='dashboard'?'Open dashboard':'Explore results'}</a>` + repoMarkup(project) : repoMarkup(project)}</div>
  </article>`;
}

function renderProjects() {
  const visible = projects.filter(project =>
    (selectedTool === 'all' || project.tools.includes(selectedTool)) &&
    (selectedArea === 'all' || project.areas.includes(selectedArea))
  );
  grid.innerHTML = visible.map(cardMarkup).join('');
  grid.hidden = visible.length === 0;
  empty.hidden = visible.length !== 0;
  const filtered = selectedTool !== 'all' || selectedArea !== 'all';
  count.textContent = filtered ? `${visible.length} of ${projects.length} projects` : `${projects.length} projects`;
  reset.hidden = !filtered;
  chips.forEach(chip => {
    const chosen = chip.dataset.tool === selectedTool;
    chip.classList.toggle('selected', chosen);
    chip.setAttribute('aria-pressed', String(chosen));
  });
}

function clearFilters() {
  selectedTool = 'all';
  selectedArea = 'all';
  areaSelect.value = 'all';
  renderProjects();
  chips[0].focus();
}

const writeUpFields = [
  ['question', 'Project question', 'To be added: the business question, intended audience, and why the answer matters.'],
  ['dataSource', 'Data source & scope', 'To be added: the dataset source, coverage, definitions, and any limitations.'],
  ['approach', 'Approach', 'To be added: the key steps, tool choices, and assumptions behind the analysis.'],
  ['findings', 'Findings & decision', 'To be added: verified results and the decision they support. No outcomes have been supplied yet.'],
  ['validation', 'Validation & reproducibility', 'To be added: quality checks, setup instructions, and how a reviewer can reproduce the work.'],
  ['demonstratedSkills', 'Skills demonstrated', 'Pending project evidence. Planned skills are listed above; completed work is required to demonstrate them.']
];

function openProject(projectId, trigger) {
  const project = projects.find(item => item.id === projectId);
  if (!project) return;
  lastTrigger = trigger;
  document.getElementById('dialog-number').textContent = `${project.number} / PROJECT WRITE-UP`;
  document.getElementById('dialog-title').textContent = project.title;
  document.getElementById('dialog-description').textContent = project.description;
  document.getElementById('dialog-state').textContent = project.completed ? (project.completedLabel || 'PUBLISHED STUDY') : 'PROJECT PLACEHOLDER';
  document.getElementById('dialog-state').classList.toggle('published-status', !!project.completed);
  document.getElementById('dialog-notice').textContent = project.completed ? 'Historical public-data study with an AI-assisted implementation. Results, code, and reproducibility checks are available for inspection.' : 'This is a write-up outline. No dataset, results, or completed project evidence has been provided yet.';
  document.getElementById('dialog-metadata').innerHTML = `<span class="small-label">${project.completed ? 'Tools used:' : 'Planned tools:'}</span>${project.tools.map(tool=>`<span class="tool-tag">${escapeHTML(tool)}</span>`).join('')}`;
  document.getElementById('write-up').innerHTML = writeUpFields.map(([field,title,placeholder])=>`<div><dt>${title}</dt><dd>${escapeHTML(project[field] || placeholder)}</dd></div>`).join('');
  document.getElementById('dialog-bottom').innerHTML = project.completed ? `<a class="outline-button download-action" href="${escapeHTML(project.downloadFile || 'downloads/retail-sales-analysis.zip')}" download>Download code & results</a><a class="github-link" href="${escapeHTML(project.link || '#retail-analysis')}" id="dialog-explore">${project.id==='dashboard'?'Open dashboard':'Explore analysis'}</a>${repoMarkup(project)}<span class="dialog-bottom-note">Private repository · access required.</span>` : `${repoMarkup(project)}<span class="dialog-bottom-note">Repository and supporting files not yet provided.</span>`;
  const explore = document.getElementById('dialog-explore');
  if (explore) explore.addEventListener('click', () => dialog.close());
  dialog.showModal();
  dialog.scrollTop = 0;
  document.body.classList.add('dialog-open');
  document.getElementById('close-dialog').focus();
}

chips.forEach(chip => chip.addEventListener('click', () => {
  selectedTool = chip.dataset.tool;
  renderProjects();
}));
areaSelect.addEventListener('change', () => {
  selectedArea = areaSelect.value;
  renderProjects();
});
reset.addEventListener('click', clearFilters);
document.getElementById('empty-reset').addEventListener('click', clearFilters);
grid.addEventListener('click', event => {
  const button = event.target.closest('[data-project]');
  if (button) openProject(button.dataset.project, button);
});
document.getElementById('close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});
dialog.addEventListener('close', () => {
  document.body.classList.remove('dialog-open');
  if (lastTrigger?.isConnected) lastTrigger.focus();
});

const navItems = [...document.querySelectorAll('.nav-item')];
function activateSection(sectionId) {
  navItems.forEach(item => {
    const active = item.getAttribute('href') === `#${sectionId}`;
    item.classList.toggle('active', active);
    if (active) item.setAttribute('aria-current', 'location');
    else item.removeAttribute('aria-current');
  });
}
document.querySelectorAll('a[href^="#"]').forEach(anchor => anchor.addEventListener('click', () => {
  const target = document.getElementById(anchor.hash.slice(1));
  if (!target) return;
  if (['projects','skills','about'].includes(target.id)) activateSection(target.id);
}));
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(entry=>entry.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
    if (visible) activateSection(visible.target.id);
  }, {rootMargin:'-10% 0px -55% 0px',threshold:0});
  ['projects','skills','about'].forEach(id => observer.observe(document.getElementById(id)));
}
document.getElementById('year').textContent = String(new Date().getFullYear());
renderProjects();
