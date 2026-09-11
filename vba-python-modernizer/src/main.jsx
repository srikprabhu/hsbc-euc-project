import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowRight, BarChart3, Check, ChevronDown, ChevronLeft, ChevronRight,
  Clock3, Code2, Copy, Download, Eye, File, FileJson, FileSpreadsheet,
  FileText, Layers3, LogOut, Play, Search, Settings2, UploadCloud, Zap
} from 'lucide-react';
import './styles.css';

const steps = [
  { name: 'Extract VBA', duration: '2.4 sec' },
  { name: 'Parse Procedures', duration: '3.1 sec' },
  { name: 'Analyse (LLM)', duration: '18.5 sec' },
  { name: 'Business Rules (LLM)', duration: '22.7 sec' },
  { name: 'Generate Python (LLM)', duration: '25.3 sec' },
  { name: 'Validate Code', duration: '4.2 sec' },
  { name: 'Execute & Compare', duration: '36.8 sec' }
];

const codeText = `
import pandas as pd
from openpyxl import load_workbook
from pathlib import Path


def process_pm_file(input_file_path, output_path):
    """Import previous month data into PM sheet."""
    src_wb = load_workbook(input_file_path, data_only=True)
    src_ws = src_wb.active

    data = pd.DataFrame(src_ws.values)
    data.columns = data.iloc[0]
    data = data[1:]

    tgt_wb = load_workbook(output_path)
    pm_ws = tgt_wb["PM"]

    for row in data.itertuples(index=False, name=None):
        pm_ws.append(row)

    tgt_wb.save(output_path)
    return Path(output_path)`;

const files = [
  { name: 'Maturity_Variance_Report.xlsx', desc: 'Generated output file', size: '245 KB', kind: 'excel' },
  { name: 'Data_Summary.csv', desc: 'Summary of processed data', size: '56 KB', kind: 'csv' },
  { name: 'validation_report.json', desc: 'Validation results', size: '12 KB', kind: 'json' },
  { name: 'business_rules.json', desc: 'Extracted business rules', size: '18 KB', kind: 'json' }
];

const rows = [
  ['Bond A', '15-Dec-2024', '1,250,000', 'OK'],
  ['Bond B', '20-Jan-2025', '-320,000', 'Review'],
  ['Bond C', '15-Mar-2025', '540,000', 'OK'],
  ['Bond D', '30-Apr-2025', '-150,000', 'Review'],
  ['Bond E', '12-Jun-2025', '890,000', 'OK']
];

function IconBox({ color = 'blue', children }) {
  return <span className={`icon-box ${color}`}>{children}</span>;
}

function downloadText(name, content, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement('a');
  a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url);
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const pythonTokenPattern = /(""".*?"""|'''[^']*'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#.*$|\b(?:and|as|class|def|for|from|if|import|in|is|not|or|return|True|False|None|with)\b|\b(?:DataFrame|Path|append|active|itertuples|load_workbook|save)\b|\b\d+(?:\.\d+)?\b)/g;

function highlightPython(line) {
  const matches = [...line.matchAll(pythonTokenPattern)];
  if (!matches.length) return line || ' ';

  const parts = [];
  let lastIndex = 0;
  matches.forEach((match, index) => {
    const token = match[0];
    const start = match.index;
    if (start > lastIndex) parts.push(line.slice(lastIndex, start));
    const type = token.startsWith('#')
      ? 'comment'
      : token.startsWith(('"')) || token.startsWith("'")
        ? 'string'
        : /^\d/.test(token)
          ? 'number'
          : /^(?:DataFrame|Path|append|active|itertuples|load_workbook|save)$/.test(token)
            ? 'builtin'
            : 'keyword';
    parts.push(<span className={`syntax-${type}`} key={`${token}-${start}-${index}`}>{token}</span>);
    lastIndex = start + token.length;
  });
  if (lastIndex < line.length) parts.push(line.slice(lastIndex));
  return parts;
}

function App() {
  const [tab, setTab] = useState('rules');
  const [fileDetails, setFileDetails] = useState(null);
  const [currentProcess, setCurrentProcess] = useState(-1);
  const [copied, setCopied] = useState(false);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const inputRef = useRef(null);

  const chooseFile = (file) => {
    if (!file) return;
    setFileDetails({
      name: file.name,
      size: formatFileSize(file.size),
      sheets: 'Pending analysis',
      modules: 'Pending analysis',
      uploaded: new Date().toLocaleString()
    });
    setCurrentProcess(-1);
  };

  const run = () => {
    setCurrentProcess(0);
    steps.forEach((_, index) => {
      setTimeout(() => setCurrentProcess(index), index * 200);
    });
    setTimeout(() => setCurrentProcess(7), steps.length * 200);
  };

  const getStepState = (index) => {
    if (currentProcess === 7 || index < currentProcess) return 'completed';
    if (index === currentProcess) return 'running';
    return 'waiting';
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-row">
          <div className="migration-mark"><span className="excel-logo">X</span><ArrowRight /><span className="python-logo">Py</span></div>
          <div><h1>EUC Modernization Framework</h1><p>From Excel Macros to Python <i /> Understand <b>•</b> Modernize <b>•</b> Validate</p></div>
        </div>
        <div className="user-area">
          <div><strong>Demo User</strong><p>Same Business Logic. Modern Technology. Measurable Results.</p></div>
          <div className="user-menu">
            <button
              className="user-avatar"
              type="button"
              aria-label="Show user details"
              aria-expanded={showUserDetails}
              onClick={() => setShowUserDetails(value => !value)}
            >
              DU
            </button>
            {showUserDetails && (
              <div className="user-popup" role="dialog" aria-label="User details">
                <div className="user-popup-heading">
                  <span className="user-popup-avatar">DU</span>
                  <div><strong>Demo User</strong><small>Migration Analyst</small></div>
                </div>
                <dl>
                  <div><dt>Email</dt><dd>demo.user@hsbc.com</dd></div>
                  <div><dt>Workspace</dt><dd>EUC Modernization</dd></div>
                </dl>
                <button className="logout-btn" type="button" onClick={() => setShowUserDetails(false)}>
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <section className="card process-card">
        <div className="process-top">
          <div className="upload-panel">
            <h3>1. Upload EUC File</h3>
            <div className="upload-content">
              <button className="drop-zone" onClick={() => inputRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); chooseFile(e.dataTransfer.files[0]); }}>
                <UploadCloud size={34} /><span>Drag and drop your Excel file here<br /><small>(.xlsm or .xlsb)</small></span><b>Browse Files</b>
              </button>
              <input ref={inputRef} type="file" accept=".xlsm,.xlsb,.xlsx" hidden onChange={e => chooseFile(e.target.files[0])} />
              <div className="file-summary"><FileSpreadsheet size={50} /><div><strong>{fileDetails?.name || 'No file selected'}</strong><p>File size: {fileDetails?.size || '-'}<br />Sheets: {fileDetails?.sheets || '-'}<br />VBA Modules: {fileDetails?.modules || '-'}<br />Uploaded: {fileDetails?.uploaded || '-'}</p></div></div>
            </div>
          </div>
          <div className="run-panel">
            <h3>2. Run Migration</h3>
            <button className="primary-btn" onClick={run} disabled={currentProcess >= 0 && currentProcess < 7}><Play size={18} fill="currentColor" />{currentProcess >= 0 && currentProcess < 7 ? 'Migration Running...' : 'Run Migration'}</button>
            <p>This will execute all 7 steps using AI and validation</p>
          </div>
          <div className="status-panel">
            <h3>3. Status</h3>
            <div className="status-body"><span className={`success-ring ${currentProcess >= 0 && currentProcess < 7 ? 'running' : currentProcess === -1 ? 'ready' : 'complete'}`}><Check /></span><div><strong>{currentProcess >= 0 && currentProcess < 7 ? 'Migration in Progress' : currentProcess === -1 ? 'Ready to Migrate' : 'Completed Successfully'}</strong><p>Total time: 3 min 28 sec<br />Completed on: 07 Sep 2026, 16:55</p></div><button className="outline-btn"><FileText size={16} />View Logs</button></div>
          </div>
        </div>
        <div className="stepper">
          {steps.map(({ name, duration }, i) => {
            const stepState = getStepState(i);
            return <div className={`step ${stepState}`} key={name}><div className="step-track"><span>{i + 1}</span></div><strong>{name}</strong><small>{stepState === 'completed' ? <><Check size={13} />{duration}</> : stepState}</small></div>;
          })}
        </div>
      </section>

      <section className="workspace card">
        <nav className="main-tabs" aria-label="Conversion output sections">
          <button className={tab === 'rules' ? 'active purple' : ''} onClick={() => setTab('rules')}><IconBox color="purple"><Settings2 /></IconBox><span><strong>Business Rules</strong><small>AI extracted business rules from your EUC</small></span></button>
          <button className={tab === 'code' ? 'active blue' : ''} onClick={() => setTab('code')}><IconBox><Code2 /></IconBox><span><strong>Generated Python Code</strong><small>AI generated Python code for the selected procedure</small></span></button>
          <button className={tab === 'reports' ? 'active green' : ''} onClick={() => setTab('reports')}><IconBox color="green"><FileText /></IconBox><span><strong>Reports & Outputs</strong><small>Generated output files and validation reports</small></span></button>
        </nav>

        <div className="tab-stage">
          {tab === 'rules' && <BusinessRules />}
          {tab === 'code' && <CodePanel copied={copied} onCopy={() => { navigator.clipboard?.writeText(codeText); setCopied(true); setTimeout(() => setCopied(false), 1200); }} />}
          {tab === 'reports' && <Reports />}
        </div>
      </section>

      <section className="metrics-grid">
        <div className="card metric-card wide"><h3><IconBox><Clock3 /></IconBox>Processing Time (Stepwise)</h3><div className="time-grid">{steps.map(({ name, duration }, i) => <div key={name}><strong>{i + 1}</strong><span>{name}</span><small>{duration}</small></div>)}</div></div>
        <div className="card metric-card"><h3><IconBox><BarChart3 /></IconBox>LLM Token Usage</h3><table><thead><tr><th>Step</th><th>Prompt</th><th>Completion</th><th>Total</th></tr></thead><tbody><tr><td>3. Analyse</td><td>6,421</td><td>6,421</td><td>12,842</td></tr><tr><td>4. Business Rules</td><td>7,983</td><td>7,923</td><td>15,906</td></tr><tr><td>5. Generate Python</td><td>9,112</td><td>9,299</td><td>18,411</td></tr><tr className="total"><td>Total</td><td>22,516</td><td>22,643</td><td>45,159</td></tr></tbody></table></div>
        <div className="card summary-card"><h3><IconBox><Layers3 /></IconBox>Total Summary</h3><p><Clock3 /><span>Total Processing Time<strong>3 min 28 sec</strong></span></p><p><Layers3 /><span>Total LLM Tokens<strong>45,159</strong></span></p></div>
      </section>
    </main>
  );
}

function BusinessRules() {
  return (
    <div className="content-panel rules-panel">
      <div className="panel-tools">
        <label>
          Procedure <button>PM <ChevronDown /></button>
        </label>
        <div className="search">
          <Search />
          <input placeholder="Search business rules..." />
        </div>
        <button
          className="outline-btn"
          onClick={() =>
            downloadText(
              'business_rules.json',
              JSON.stringify(
                {
                  procedure: 'PM',
                  purpose: 'Import previous month data into the PM worksheet'
                },
                null,
                2
              ),
              'application/json'
            )
          }
        >
          <Download />
          Download (.JSON)
        </button>
      </div>

      <div className="rule-sheet">
        <div className="sheet-title">
          <h2>Business Rule: PM</h2>
          <span>BR-001</span>
        </div>

        <Rule icon={<Zap />} color="purple" title="Purpose">
          Import previous month data from selected workbook into the PM worksheet.
        </Rule>

        <Rule icon={<ArrowRight />} color="green" title="Inputs">
          <ul>
            <li>User selected Excel file (previous month)</li>
            <li>Source sheet: Active sheet</li>
            <li>Target sheet: PM</li>
          </ul>
        </Rule>

        <Rule icon={<Settings2 />} color="blue" title="Processing Logic">
          <ul>
            <li>Open the selected workbook</li>
            <li>Copy used range from active sheet</li>
            <li>Paste values into PM sheet</li>
            <li>Apply data formatting</li>
          </ul>
        </Rule>

        <Rule icon={<File />} color="blue" title="Outputs">
          <ul>
            <li>Updated PM worksheet with imported data</li>
          </ul>
        </Rule>

        <div className="pager">
          <ChevronLeft />
          <span>1 / 5</span>
          <ChevronRight />
        </div>
      </div>
    </div>
  );
}
function Rule({ icon, color, title, children }) {
  return (
    <div className="rule-row">
      <IconBox color={color}>{icon}</IconBox>
      <div>
        <h4>{title}</h4>
        <div>{children}</div>
      </div>
    </div>
  );
}

function CodePanel({ copied, onCopy }) {
  return (
    <div className="content-panel code-panel">
      <div className="subtabs">
        <button className="active">Code</button>
        <button>Explanation</button>
        <button
          className="outline-btn"
          onClick={() => downloadText('pm.py', codeText, 'text/x-python')}
        >
          <Download />
          Download (.py)
        </button>
      </div>
      <div className="code-window">
        <div className="code-head">
          <span>
            <Code2 />
            pm.py
          </span>
          <button onClick={onCopy}>
            <Copy />
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <pre>
          {codeText.split('\n').map((line, i) => (
            <div key={i}>
              <span className="line-number">{i + 1}</span>
              <code>{highlightPython(line)}</code>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}
function Reports() {
  return (
    <div className="content-panel reports-panel">
      <div className="subtabs">
        <button className="active">Output Files</button>
        <button>Validation Report</button>
        <button>Execution Log</button>
        <button
          className="outline-btn"
          onClick={() =>
            downloadText(
              'migration_summary.txt',
              'Migration completed successfully.',
            )
          }
        >
          <Download />
          Download All
        </button>
      </div>

      <div className="files-list">
        {files.map((f) => (
          <div className="file-row" key={f.name}>
            <IconBox
              color={
                f.kind === 'excel' || f.kind === 'csv' ? 'green' : 'purple'
              }
            >
              {f.kind === 'excel' ? (
                <FileSpreadsheet />
              ) : f.kind === 'json' ? (
                <FileJson />
              ) : (
                <FileText />
              )}
            </IconBox>
            <div>
              <strong>{f.name}</strong>
              <small>{f.desc}</small>
            </div>
            <span>{f.size}</span>
            <button>
              <Eye />
            </button>
            <button
              onClick={() => downloadText(f.name, `Demo output for ${f.name}`)}
            >
              <Download />
            </button>
          </div>
        ))}
      </div>

      <h3 className="preview-title">Preview: Maturity_Variance_Report.xlsx</h3>
      <div className="preview-tabs">
        <button className="active">Data Preview</button>
        <button>Charts</button>
        <button>Sheet View</button>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Maturity Date</th>
            <th>Variance</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r[0]}>
              {r.map((v, i) => (
                <td key={v}>
                  {i === 3 ? (
                    <span className={`badge ${v.toLowerCase()}`}>{v}</span>
                  ) : (
                    v
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);
