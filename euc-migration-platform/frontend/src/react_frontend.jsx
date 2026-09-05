import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Check,
  ChevronRight,
  CircleDot,
  Code2,
  Download,
  FileCode2,
  FileSpreadsheet,
  FileText,
  Gauge,
  LayoutDashboard,
  ListChecks,
  LoaderCircle,
  Menu,
  Play,
  RefreshCw,
  ScrollText,
  Server,
  Settings2,
  ShieldCheck,
  Upload,
  X,
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

const navItems = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'upload', label: 'Upload & Run', icon: Upload },
  { id: 'rules', label: 'Business Rules', icon: ListChecks },
  { id: 'code', label: 'Generated Code', icon: Code2 },
  { id: 'validation', label: 'Validation', icon: ShieldCheck },
  { id: 'execution', label: 'Execution Results', icon: Activity },
  { id: 'reports', label: 'Reports', icon: FileSpreadsheet },
  { id: 'usage', label: 'LLM Usage', icon: Gauge },
  { id: 'logs', label: 'Logs & Status', icon: ScrollText },
];

const stages = [
  ['Extract VBA', 'Raw modules'],
  ['Parse procedures', 'Control flow'],
  ['Analyse logic', 'LLM review'],
  ['Formalise rules', 'Rule register'],
  ['Generate Python', 'Target code'],
  ['Validate code', 'Static checks'],
  ['Execute reports', 'Outputs'],
];

function Logo({ compact = false }) {
  return (
    <div className={`wordmark ${compact ? 'wordmark-compact' : ''}`} aria-label="Deloitte">
      <span>Deloitte</span><b>.</b>
    </div>
  );
}

function StatusPill({ status = 'IDLE' }) {
  const tone = status.toLowerCase();
  return <span className={`status-pill ${tone}`}><span className="status-dot" />{status}</span>;
}

function Metric({ label, value, detail, icon: Icon, accent = '' }) {
  return (
    <article className={`metric ${accent}`}>
      <div className="metric-icon"><Icon size={17} strokeWidth={1.8} /></div>
      <div><span className="eyebrow">{label}</span><strong>{value}</strong><small>{detail}</small></div>
    </article>
  );
}

function ProgressRail({ status }) {
  const current = String(status?.current_step || '').toLowerCase();
  const isComplete = status?.status === 'COMPLETED';
  const isFailed = status?.status === 'FAILED';
  const activeIndex = stages.findIndex(([name]) => current.includes(name.split(' ')[0].toLowerCase()));
  const completed = isComplete ? stages.length : Math.max(0, activeIndex);
  return (
    <section className="progress-panel panel">
      <div className="panel-heading"><div><span className="eyebrow">Workflow control</span><h2>Migration progress</h2></div><strong>{status?.progress || 0}%</strong></div>
      <div className="rail">
        <div className="rail-line"><i style={{ width: `${isComplete ? 100 : Math.min(100, (completed / (stages.length - 1)) * 100)}%` }} /></div>
        {stages.map(([name, detail], index) => {
          const failed = isFailed && index === activeIndex;
          const done = index < completed || (isComplete && index === stages.length - 1);
          const active = index === activeIndex && !done && !failed;
          return <div className={`rail-step ${done ? 'done' : ''} ${active ? 'active' : ''} ${failed ? 'failed' : ''}`} key={name}>
            <div className="rail-node">{done ? <Check size={13} /> : failed ? <X size={13} /> : index + 1}</div><span>{name}</span><small>{detail}</small>
          </div>;
        })}
      </div>
      <div className="progress-message"><span>{status?.current_step || 'Upload a workbook to begin the migration.'}</span><StatusPill status={status?.status || 'IDLE'} /></div>
    </section>
  );
}

function EmptyState({ icon: Icon = FileText, title, detail }) {
  return <div className="empty-state"><Icon size={30} /><h3>{title}</h3><p>{detail}</p></div>;
}

function App() {
  const [page, setPage] = useState('dashboard');
  const [runId, setRunId] = useState(null);
  const [status, setStatus] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [file, setFile] = useState(null);
  const [rules, setRules] = useState([]);
  const [code, setCode] = useState('');
  const [validation, setValidation] = useState(null);
  const [execution, setExecution] = useState(null);
  const [logs, setLogs] = useState('');
  const [mobileNav, setMobileNav] = useState(false);
  const [error, setError] = useState('');
  const fileInput = useRef(null);

  async function api(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `Request failed (${response.status})`);
    return response;
  }

  async function refreshStatus(id = runId) {
    if (!id) return null;
    try {
      const response = await api(`/pipeline/status/${id}`);
      const next = await response.json();
      setStatus(next); setApiOnline(true); return next;
    } catch (err) { setApiOnline(false); setError(err.message); return null; }
  }

  useEffect(() => { api('/health').then(() => setApiOnline(true)).catch(() => setApiOnline(false)); }, []);

  useEffect(() => {
    if (!runId || !status || ['COMPLETED', 'FAILED'].includes(status.status)) return undefined;
    const timer = setInterval(() => refreshStatus(), 1200);
    return () => clearInterval(timer);
  }, [runId, status?.status]);

  useEffect(() => {
    if (!runId || status?.status !== 'COMPLETED') return;
    api(`/pipeline/rules/${runId}`).then(r => r.json()).then(data => setRules(data.rules || [])).catch(() => {});
    api(`/files/${runId}/generated_python`).then(r => r.text()).then(setCode).catch(() => {});
    api(`/files/${runId}/python_validation`).then(r => r.json()).then(setValidation).catch(() => {});
    api(`/files/${runId}/python_execution`).then(r => r.json()).then(setExecution).catch(() => {});
    api(`/pipeline/logs/${runId}`).then(r => r.json()).then(data => setLogs(data.content || '')).catch(() => {});
  }, [runId, status?.status]);

  async function startMigration() {
    if (!file) return;
    setError('');
    try {
      const body = new FormData(); body.append('file', file);
      const response = await api('/pipeline/run', { method: 'POST', body });
      const result = await response.json();
      setRunId(result.run_id); setStatus({ status: 'QUEUED', progress: 0, current_step: 'Queued', workbook: file.name }); setPage('dashboard');
    } catch (err) { setError(err.message); }
  }

  function artifactUrl(name) { return `${API_BASE}/files/${runId}/${name}`; }
  const summary = status?.summary || {};
  const outputs = status?.artifacts?.generated_outputs || [];
  const procedures = summary.procedure_count ?? '-';
  const ruleCount = (summary.business_rule_count ?? rules.length) || '-';
  const isRunning = status && ['QUEUED', 'RUNNING'].includes(status.status);

  function pageContent() {
    if (page === 'upload') return <UploadPage file={file} setFile={setFile} fileInput={fileInput} onStart={startMigration} />;
    if (!runId) return <EmptyState icon={Upload} title="No migration run selected" detail="Upload an XLSB or XLSM workbook to populate this workspace." />;
    if (page === 'rules') return <RulesPage rules={rules} />;
    if (page === 'code') return <CodePage code={code} url={artifactUrl('generated_python')} />;
    if (page === 'validation') return <ValidationPage validation={validation} url={artifactUrl('python_validation')} />;
    if (page === 'execution') return <ExecutionPage execution={execution} />;
    if (page === 'reports') return <ReportsPage outputs={outputs} url={artifactUrl} />;
    if (page === 'usage') return <UsagePage summary={summary} url={artifactUrl('token_usage')} />;
    if (page === 'logs') return <LogsPage status={status} logs={logs} />;
    return <><ProgressRail status={status} /><div className="metrics-grid"><Metric label="Workbook" value={status?.workbook || '-'} detail="Source macro file" icon={FileSpreadsheet} /><Metric label="Procedures" value={procedures} detail="Discovered dynamically" icon={FileCode2} /><Metric label="Business rules" value={ruleCount} detail="Preserved and traceable" icon={ListChecks} accent="mint" /><Metric label="Reports" value={outputs.length || summary.output_count || '-'} detail="Generated outputs" icon={BarChart3} /><Metric label="LLM tokens" value={summary.total_llm_tokens ?? '-'} detail="Analysis and generation" icon={Gauge} /></div><section className="panel insight"><div><span className="eyebrow">Run briefing</span><h2>{status?.status === 'COMPLETED' ? 'Migration is ready for review' : isRunning ? 'Migration is in progress' : 'Migration workspace'}</h2><p>{status?.status === 'COMPLETED' ? 'Review the preserved business rules, generated code, validation evidence, and report outputs from the navigation.' : status?.current_step || 'Start a workbook migration from Upload & Run.'}</p></div><button className="button button-quiet" onClick={() => setPage('logs')}>Open run log <ChevronRight size={16} /></button></section></>;
  }

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
      <div className="brand-block"><Logo /><span className="brand-subtitle">EUC modernisation platform</span></div>
      <div className="sidebar-label">Workspace</div>
      <nav>{navItems.map(({ id, label, icon: Icon }) => <button className={page === id ? 'nav-item selected' : 'nav-item'} onClick={() => { setPage(id); setMobileNav(false); }} key={id}><Icon size={17} /><span>{label}</span>{page === id && <ChevronRight size={14} />}</button>)}</nav>
      <div className="sidebar-bottom"><div className="api-state"><span className={apiOnline ? 'online-dot' : 'offline-dot'} /><div><strong>{apiOnline ? 'API connected' : 'API unavailable'}</strong><small>{API_BASE.replace('http://', '')}</small></div><RefreshCw size={14} /></div><Logo compact /></div>
    </aside>
    {mobileNav && <button className="scrim" onClick={() => setMobileNav(false)} aria-label="Close menu" />}
    <main className="main-content">
      <header className="topbar"><button className="icon-button menu-button" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu size={20} /></button><div><span className="eyebrow">Enterprise user computing</span><h1>VBA to Python migration</h1></div><div className="topbar-actions"><button className="icon-button" onClick={() => refreshStatus()} title="Refresh status"><RefreshCw size={17} /></button>{runId && <div className="run-chip"><CircleDot size={14} /><span>{runId}</span><StatusPill status={status?.status || 'QUEUED'} /></div>}</div></header>
      <section className="page-intro"><div><span className="eyebrow">Control center</span><h2>{page === 'dashboard' ? 'Control center' : navItems.find(item => item.id === page)?.label}</h2><p>Traceable migration from spreadsheet logic to governed Python workflows.</p></div><button className="button button-primary" onClick={() => setPage('upload')}><Upload size={16} /> New migration</button></section>
      {error && <div className="error-banner"><AlertCircle size={17} /><span>{error}</span><button onClick={() => setError('')}><X size={15} /></button></div>}
      {pageContent()}
      <footer><span>Internal migration workspace</span><span>© Deloitte</span></footer>
    </main>
  </div>;
}

function UploadPage({ file, setFile, fileInput, onStart }) {
  return <section className="upload-layout"><div className="upload-card panel"><div className="upload-icon"><Upload size={25} /></div><span className="eyebrow">Source workbook</span><h2>Bring an EUC into the workflow</h2><p>Upload an Excel macro workbook to extract procedures, preserve rules, generate Python, and validate the result.</p><button className="drop-zone" onClick={() => fileInput.current?.click()}><FileSpreadsheet size={25} /><strong>{file ? file.name : 'Choose an XLSB or XLSM file'}</strong><small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB selected` : 'Drag and drop is supported in the browser'}</small></button><input ref={fileInput} type="file" accept=".xlsb,.xlsm" hidden onChange={event => setFile(event.target.files?.[0] || null)} /><button className="button button-primary start-button" disabled={!file} onClick={onStart}><Play size={16} /> Start migration</button></div><div className="upload-side"><div className="panel"><span className="eyebrow">What happens next</span>{['Extract macro modules', 'Map procedure dependencies', 'Capture business rules', 'Generate and validate Python'].map((item, i) => <div className="check-row" key={item}><span>{i + 1}</span><p>{item}</p><Check size={15} /></div>)}</div></div></section>;
}

function RulesPage({ rules }) { return <section className="content-stack">{rules.length ? rules.map((rule, i) => <article className="rule-card panel" key={`${rule.name}-${i}`}><div className="rule-number">0{i + 1}</div><div><span className="eyebrow">{rule.source_procedure || 'Business rule'}</span><h3>{rule.name || 'Business rule'}</h3><p>{rule.description || 'No description supplied.'}</p></div></article>) : <EmptyState icon={ListChecks} title="No business rules available" detail="Rules will appear here after a completed migration." />}</section>; }
function CodePage({ code, url }) { return <section className="content-stack"><div className="panel code-panel"><div className="panel-heading"><div><span className="eyebrow">Generated artifact</span><h2>generated_euc.py</h2></div><a className="button button-quiet" href={url} download><Download size={16} /> Download</a></div><pre>{code || '# Generated Python will appear after the migration completes.'}</pre></div></section>; }
function ValidationPage({ validation, url }) { const pass = validation?.status === 'PASS'; return <section className="content-stack"><div className={`validation-banner ${pass ? 'pass' : ''}`}><div className="validation-icon">{pass ? <Check /> : <ShieldCheck />}</div><div><span className="eyebrow">Static validation</span><h2>{pass ? 'Validation passed' : validation ? 'Validation needs attention' : 'Validation pending'}</h2><p>{validation?.message || 'The validation report will be available after the generated code is checked.'}</p></div><a className="button button-quiet" href={url} download><Download size={16} /> JSON report</a></div></section>; }
function ExecutionPage({ execution }) { const results = execution?.results || []; return <section className="content-stack"><div className="metrics-grid compact"><Metric label="Procedures" value={results.length || '-'} detail="Execution attempts" icon={FileCode2} /><Metric label="Succeeded" value={results.filter(item => ['SUCCESS', 'PASS', 'COMPLETED'].includes(String(item.status).toUpperCase())).length || '-'} detail="Completed successfully" icon={Check} accent="mint" /><Metric label="Failed" value={results.filter(item => !['SUCCESS', 'PASS', 'COMPLETED'].includes(String(item.status).toUpperCase())).length || '-'} detail="Needs review" icon={AlertCircle} /></div>{results.length ? <div className="panel table-wrap"><table><thead><tr><th>Procedure</th><th>Status</th><th>Message</th></tr></thead><tbody>{results.map((item, i) => <tr key={i}><td>{item.procedure || item.name || '-'}</td><td><StatusPill status={String(item.status || 'UNKNOWN').toUpperCase()} /></td><td>{item.message || item.error || '-'}</td></tr>)}</tbody></table></div> : <EmptyState icon={Activity} title="No execution results" detail="Generated procedure results will appear here." />}</section>; }
function ReportsPage({ outputs, url }) { return <section className="content-stack"><div className="artifact-row panel"><div className="file-icon"><FileText size={19} /></div><div><strong>business_rules.docx</strong><small>Business rules document</small></div><a className="button button-quiet" href={url('business_rules_docx')} download><Download size={16} /> Download</a></div>{outputs.length ? outputs.map((output, i) => { const name = output.split(/[\\/]/).pop(); return <div className="artifact-row panel" key={name}><div className="file-icon"><FileSpreadsheet size={19} /></div><div><strong>{name}</strong><small>Generated Excel report</small></div><a className="button button-quiet" href={url(name)} download><Download size={16} /> Download</a></div>; }) : <EmptyState icon={FileSpreadsheet} title="No Excel reports available" detail="Generated Excel outputs will appear after execution." />}</section>; }
function UsagePage({ summary, url }) { return <section className="content-stack"><div className="panel usage-card"><div className="metric-icon"><Gauge size={18} /></div><div><span className="eyebrow">Total LLM tokens</span><strong>{summary.total_llm_tokens ?? '-'}</strong><p>Usage is recorded across procedure analysis, business rules, and Python generation.</p></div><a className="button button-quiet" href={url} download><Download size={16} /> Usage JSON</a></div></section>; }
function LogsPage({ status, logs }) { return <section className="content-stack"><div className="panel log-panel"><div className="panel-heading"><div><span className="eyebrow">Run telemetry</span><h2>Pipeline log</h2></div><StatusPill status={status?.status || 'IDLE'} /></div><pre>{logs || 'No log available for this run.'}</pre></div></section>; }

createRoot(document.getElementById('root')).render(<App />);

export default App;
