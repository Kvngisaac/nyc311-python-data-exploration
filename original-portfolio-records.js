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
  { id: 'python', number: '02', title: 'Python data exploration', area: 'Data quality', areas: ['Data quality', 'Analysis'],
    tools: ['Python', 'Git'], preview: '.py', previewNote: 'Notebook preview to be added',
    previewFoot: 'inspect → clean → explore',
    description: 'A project slot for making raw data usable and exploring patterns in a reproducible notebook.',
    plannedSkills: 'Cleaning, quality checks, exploratory analysis',
    githubUrl: null, question: null, dataSource: null, approach: null, findings: null, validation: null, demonstratedSkills: null },
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


