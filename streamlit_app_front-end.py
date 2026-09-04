"""
streamlit_app.py
================
Multi-page enterprise UI for the EUC VBA -> Python Migration Platform.

Pages:
    Dashboard
    Upload & Run
    Business Rules
    Generated Code
    Validation
    Execution Results
    Reports
    LLM Usage
    Logs & Status

Run:
    streamlit run streamlit_app.py

The UI talks to FastAPI. It does NOT implement migration logic.
"""

from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any

import requests
import streamlit as st


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="EUC Modernisation Platform",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = st.session_state.get(
    "api_base",
    "http://127.0.0.1:8000",
).rstrip("/")


# ---------------------------------------------------------------------
# Enterprise styling
# ---------------------------------------------------------------------

st.markdown(
    """
<style>
:root {
    --navy: #06244f;
    --navy-2: #0b2f63;
    --blue: #1264e8;
    --blue-soft: #eaf2ff;
    --green: #16a765;
    --green-soft: #eaf8f1;
    --amber: #f4a000;
    --purple: #8d63d8;
    --cyan: #12b8cf;
    --ink: #10233f;
    --muted: #71829a;
    --border: #e1e8f1;
    --surface: #ffffff;
    --page: #f4f7fb;
}

.stApp {
    background: var(--page);
    color: var(--ink);
}

.block-container {
    max-width: 1510px;
    padding: 1rem 1.25rem 2.5rem;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071f43 0%, #061a37 100%);
    border-right: 1px solid #17345b;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

section[data-testid="stSidebar"] * {
    color: #eaf1fb;
}

.sidebar-brand {
    padding: 4px 4px 18px;
    border-bottom: 1px solid rgba(255,255,255,.12);
}

.sidebar-logo {
    width: 42px;
    height: 42px;
    border-radius: 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#16a6ff,#1264e8);
    font-size: 23px;
    margin-right: 9px;
    vertical-align: middle;
}

.sidebar-title {
    display: inline-block;
    vertical-align: middle;
    font-size: 17px;
    line-height: 1.1;
    font-weight: 800;
}

.sidebar-subtitle {
    color: #9fb2cc !important;
    font-size: 10px;
    margin-top: 8px;
}

.sidebar-heading {
    color: #a9bad0 !important;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin: 18px 0 8px;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    min-height: 42px !important;
    height: 42px !important;
    padding: 0 13px !important;
    margin: 2px 0 !important;
    text-align: left !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    background: transparent !important;
    color: #dce8f7 !important;
    font-size: 13px !important;
    font-weight: 650 !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #123b6c !important;
    border-color: #20558f !important;
    color: #fff !important;
}

section[data-testid="stSidebar"] .stButton > button:focus {
    box-shadow: 0 0 0 2px rgba(18,100,232,.3) !important;
}

section[data-testid="stSidebar"] [data-testid="stAlert"] {
    border-radius: 8px;
}

.sidebar-health {
    margin-top: 22px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,.12);
}

.health-dot {
    display:inline-block;
    width:9px;
    height:9px;
    border-radius:50%;
    background:#21c56e;
    margin-right:7px;
    box-shadow:0 0 0 3px rgba(33,197,110,.12);
}

/* ---------- Hero ---------- */
.hero {
    position: relative;
    overflow: hidden;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 31px 34px 30px;
    margin-bottom: 17px;
    min-height: 190px;
    box-shadow: 0 5px 20px rgba(13,42,76,.055);
}

.hero::after {
    content: "";
    position: absolute;
    right: -30px;
    top: -40px;
    width: 300px;
    height: 220px;
    background: radial-gradient(circle, rgba(37,117,236,.10), rgba(37,117,236,0) 68%);
}

.hero-art {
    position:absolute;
    right:48px;
    top:31px;
    width:230px;
    height:130px;
    opacity:.9;
}

.hero-doc {
    position:absolute;
    width:65px;
    height:82px;
    border:3px solid #cfe0fb;
    border-radius:9px;
    background:#fff;
    box-shadow:0 5px 14px rgba(20,70,130,.08);
}

.hero-doc.left { left:25px; top:15px; }
.hero-doc.right { right:25px; top:15px; }

.hero-doc::before {
    content:"";
    position:absolute;
    left:12px;
    right:12px;
    top:42px;
    height:3px;
    background:#dbe8fa;
    box-shadow:0 10px 0 #dbe8fa, 0 20px 0 #dbe8fa;
}

.hero-arrow {
    position:absolute;
    left:91px;
    top:44px;
    color:#1680e8;
    font-size:35px;
    font-weight:800;
}

.hero-badge {
    position:absolute;
    left:17px;
    top:17px;
    font-size:14px;
    font-weight:900;
}

.hero-badge.vba { color:#1d9651; }
.hero-badge.py { color:#2468c8; }

.eyebrow {
    position:relative;
    z-index:2;
    font-size:11px;
    letter-spacing:1.7px;
    font-weight:850;
    text-transform:uppercase;
    color:#1466df;
}

.hero h1 {
    position:relative;
    z-index:2;
    margin:7px 0 8px;
    color:#10233f;
    font-size:32px;
    line-height:1.15;
    font-weight:850;
}

.hero p {
    position:relative;
    z-index:2;
    max-width:900px;
    color:#5b6e87;
    font-size:14px;
    line-height:1.6;
    margin:0;
}

/* ---------- Workflow ---------- */
.workflow-grid {
    display:grid;
    grid-template-columns:repeat(7,1fr);
    gap:9px;
    margin-bottom:8px;
}

.stage {
    position:relative;
    min-height:105px;
    background:#fff;
    border:1px solid var(--border);
    border-radius:12px;
    padding:14px 10px 12px;
    box-shadow:0 3px 12px rgba(13,42,76,.035);
}

.stage-icon {
    width:31px;
    height:31px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    margin:0 auto 7px;
    font-size:16px;
    font-weight:800;
    background:var(--blue-soft);
    color:var(--blue);
}

.stage:nth-child(3) .stage-icon { background:#f0eaff; color:var(--purple); }
.stage:nth-child(4) .stage-icon { background:#fff4dd; color:var(--amber); }
.stage:nth-child(5) .stage-icon { background:#e7f9fb; color:#0796aa; }
.stage:nth-child(7) .stage-icon { background:#fff4dd; color:var(--amber); }

.stage-number {
    color:#6c7e96;
    font-size:9px;
    font-weight:850;
    text-align:center;
    letter-spacing:.5px;
}

.stage-name {
    color:#142844;
    font-size:12px;
    font-weight:800;
    text-align:center;
    margin-top:3px;
}

.stage-detail {
    color:#7c8ca2;
    font-size:9px;
    text-align:center;
    margin-top:2px;
}

/* ---------- Run badge ---------- */
.runbar {
    display:flex;
    justify-content:flex-end;
    align-items:center;
    gap:7px;
    margin:3px 0 14px;
}

.run-label {
    color:#71829a;
    font-size:11px;
}

.run-id {
    background:#eef5ff;
    color:#1c4d82;
    border:1px solid #d1e2f8;
    border-radius:7px;
    padding:6px 10px;
    font-size:11px;
    font-weight:800;
}

.run-status {
    border-radius:7px;
    padding:6px 10px;
    font-size:11px;
    font-weight:850;
}

.run-status.success {
    background:#edf9f1;
    color:#21834c;
    border:1px solid #d0ecd9;
}

.run-status.failed {
    background:#fff1f0;
    color:#d74a44;
    border:1px solid #f4d0cd;
}

.run-status.running {
    background:#eef5ff;
    color:#1762bb;
    border:1px solid #d3e4fa;
}

/* ---------- Cards / KPIs ---------- */
.section-title {
    font-size:20px;
    font-weight:850;
    color:#10233f;
    margin:18px 0 11px;
}

.section-caption {
    font-size:12px;
    color:#7a8ba0;
    margin-bottom:8px;
}

.card {
    background:#fff;
    border:1px solid var(--border);
    border-radius:12px;
    padding:15px 16px;
    box-shadow:0 3px 13px rgba(13,42,76,.045);
}

.kpi-card {
    min-height:126px;
    text-align:center;
}

.kpi-icon {
    width:39px;
    height:39px;
    margin:0 auto 7px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:18px;
    font-weight:850;
    background:#eaf2ff;
    color:#1264e8;
}

.kpi-label {
    color:#74859a;
    font-size:9px;
    font-weight:850;
    text-transform:uppercase;
    letter-spacing:.8px;
}

.kpi-value {
    color:#10233f;
    font-size:21px;
    line-height:1.15;
    font-weight:850;
    margin-top:5px;
    overflow-wrap:anywhere;
    word-break:normal;
}

.kpi-sub {
    color:#8796a9;
    font-size:9px;
    margin-top:5px;
}

.kpi-failed .kpi-icon {
    background:#eaf8f1;
    color:#13a561;
}

.kpi-failed .kpi-value {
    color:#df4c48;
}

/* ---------- Panels ---------- */
.panel {
    background:#fff;
    border:1px solid var(--border);
    border-radius:12px;
    padding:15px;
    box-shadow:0 3px 13px rgba(13,42,76,.045);
}

.panel-title {
    color:#0d356a;
    font-size:14px;
    font-weight:850;
    margin-bottom:11px;
}

.rule {
    background:#fff;
    border:1px solid #e6ecf3;
    border-left:4px solid #2b76df;
    border-radius:8px;
    padding:10px 12px;
    margin:6px 0;
}

.rule-title {
    color:#172d4c;
    font-size:12px;
    font-weight:800;
}

.rule-body {
    color:#61738b;
    font-size:10px;
    line-height:1.45;
    margin-top:3px;
}

.rule-source {
    color:#2b6fba;
    font-size:9px;
    margin-top:5px;
}

.output-row {
    background:#fff;
    border:1px solid #e4eaf1;
    border-radius:8px;
    padding:8px 10px;
    margin:5px 0;
}


.pipeline-progress-card {
    background:#fff;
    border:1px solid #e2e9f1;
    border-radius:10px;
    padding:13px 16px 11px;
    margin:8px 0 16px;
    box-shadow:0 2px 10px rgba(13,42,76,.035);
}
.pipeline-progress-title {
    color:#0d356a;
    font-size:13px;
    font-weight:850;
    margin-bottom:12px;
}
.pipeline-track {
    position:relative;
    display:grid;
    grid-template-columns:repeat(7,1fr);
    align-items:start;
    min-height:55px;
}
.pipeline-track-line {
    position:absolute;
    left:6.7%;
    right:6.7%;
    top:11px;
    height:2px;
    background:#d8dee7;
    z-index:0;
}
.pipeline-track-line-fill {
    position:absolute;
    left:6.7%;
    top:11px;
    height:2px;
    background:#12a56a;
    z-index:1;
    transition:width .35s ease;
}
.pipeline-step {
    position:relative;
    z-index:2;
    text-align:center;
    min-width:0;
}
.pipeline-dot {
    width:20px;
    height:20px;
    margin:0 auto 6px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:9px;
    font-weight:850;
    border:2px solid #d6dde6;
    background:#eef1f5;
    color:#7c8796;
    box-sizing:border-box;
}
.pipeline-step.completed .pipeline-dot,
.pipeline-step.current .pipeline-dot {
    border-color:#12a56a;
    background:#12a56a;
    color:#fff;
}
.pipeline-step.failed .pipeline-dot {
    border-color:#df4c48;
    background:#df4c48;
    color:#fff;
}
.pipeline-label {
    color:#53657c;
    font-size:9px;
    line-height:1.15;
    font-weight:650;
    white-space:nowrap;
}
.pipeline-step.completed .pipeline-label,
.pipeline-step.current .pipeline-label {
    color:#17314f;
}
.pipeline-step.failed .pipeline-label {
    color:#c73f3b;
}
.pipeline-progress-meta {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-top:4px;
    color:#71839a;
    font-size:9px;
}
.pipeline-progress-meta strong {
    color:#17314f;
}
@media (max-width: 850px) {
    .pipeline-label { font-size:8px; white-space:normal; }
    .pipeline-progress-card { overflow-x:auto; }
    .pipeline-track { min-width:650px; }
}

.footer {
    border-top:1px solid #dfe6ee;
    margin-top:28px;
    padding-top:11px;
    color:#8291a4;
    font-size:10px;
}

/* ---------- Controls ---------- */
.stButton > button {
    border-radius:7px !important;
    min-height:36px !important;
    height:36px !important;
    padding:0 15px !important;
    font-size:12px !important;
    font-weight:750 !important;
    border:1px solid #ccd9e7 !important;
    background:#fff !important;
    color:#16324f !important;
    box-shadow:none !important;
}

.stButton > button:hover {
    border-color:#1264e8 !important;
    color:#1264e8 !important;
    background:#f5f9ff !important;
}

.stButton > button[kind="primary"],
button[kind="primary"] {
    background:#1264e8 !important;
    color:#fff !important;
    border-color:#1264e8 !important;
}

.stButton > button[kind="primary"]:hover,
button[kind="primary"]:hover {
    background:#0d55c9 !important;
    border-color:#0d55c9 !important;
    color:#fff !important;
}

[data-testid="stDownloadButton"] button {
    min-height:33px !important;
    height:33px !important;
    padding:0 12px !important;
    font-size:11px !important;
}

[data-testid="stFileUploader"] {
    margin-bottom:6px;
}

.element-container {
    margin-bottom:.3rem;
}

[data-testid="stProgress"] > div > div > div {
    border-radius:8px !important;
}

@media (max-width: 1050px) {
    .hero-art { display:none; }
    .workflow-grid { grid-template-columns:repeat(4,1fr); }
}

</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------

def api_get(path: str) -> Any:
    response = requests.get(
        f"{API_BASE}{path}",
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def upload_pipeline(file_bytes: bytes, filename: str) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE}/pipeline/run",
        files={
            "file": (
                filename,
                file_bytes,
                "application/octet-stream",
            )
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def download_artifact(
    run_id: str,
    artifact_name: str,
) -> tuple[bytes, str]:

    response = requests.get(
        f"{API_BASE}/files/{run_id}/{artifact_name}",
        timeout=60,
    )

    if response.status_code == 404:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            pass
        raise RuntimeError(
            f"Artifact '{artifact_name}' is not available for run "
            f"{run_id}. {detail}".strip()
        )

    response.raise_for_status()

    return (
        response.content,
        response.headers.get(
            "content-type",
            "application/octet-stream",
        ),
    )


def get_status(run_id: str) -> dict[str, Any]:
    return api_get(
        f"/pipeline/status/{run_id}"
    )


def render_run_badge(run_id: str | None, status: dict[str, Any] | None) -> None:
    if not run_id:
        return

    state = str((status or {}).get("status", "RUNNING")).upper()
    label = {
        "COMPLETED": "COMPLETED",
        "FAILED": "FAILED",
        "RUNNING": "RUNNING",
        "QUEUED": "QUEUED",
    }.get(state, state)

    state_class = (
        "success" if state == "COMPLETED"
        else "failed" if state == "FAILED"
        else "running"
    )

    st.markdown(
        f"""
        <div class="runbar">
            <span class="run-label">Run ID</span>
            <span class="run-id">{run_id}</span>
            <span class="run-status {state_class}">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )




def render_pipeline_progress(status: dict[str, Any] | None) -> None:
    """Render the seven-stage migration progress tracker from live API status."""
    steps = [
        ("1", "Extract VBA", ("extract", "raw extraction", "vba")),
        ("2", "Parse Procedures", ("parse", "procedure parser", "procedure parsing")),
        ("3", "Analyse (LLM)", ("procedure agent", "procedure analysis", "analyse")),
        ("4", "Business Rules (LLM)", ("business rule", "business rules", "formalise")),
        ("5", "Generate Python (LLM)", ("python code", "code generation", "generate")),
        ("6", "Validate Code", ("validation", "static validation", "validate")),
        ("7", "Execute Reports", ("execution", "execute", "reports")),
    ]

    status = status or {}
    state = str(status.get("status", "RUNNING")).upper()
    current = str(status.get("current_step", "")).lower()
    raw_progress = status.get("progress", 0)
    try:
        progress = max(0, min(100, int(raw_progress)))
    except (TypeError, ValueError):
        progress = 0

    # Prefer the backend's current_step over a guessed stage from percentage.
    current_idx = None
    for i, (_, _, keywords) in enumerate(steps):
        if any(keyword in current for keyword in keywords):
            current_idx = i
            break

    if state == "COMPLETED":
        completed_count = 7
        current_idx = 6
        progress = 100
    elif current_idx is not None:
        completed_count = current_idx
        # If the backend reports a step as completed, advance the visual tracker.
        if any(word in current for word in ("completed", "complete", "done")):
            completed_count = current_idx + 1
    else:
        completed_count = min(6, max(0, int(round(progress * 7 / 100))))

    if state == "FAILED" and current_idx is not None:
        completed_count = current_idx

    fill_percent = 0 if completed_count <= 1 else min(100, ((completed_count - 1) / 6) * 100)
    if state == "COMPLETED":
        fill_percent = 100

    stage_html = [
        '<div class="pipeline-progress-card">',
        '<div class="pipeline-progress-title">▣ &nbsp;Pipeline Progress</div>',
        '<div class="pipeline-track">',
        '<div class="pipeline-track-line"></div>',
        f'<div class="pipeline-track-line-fill" style="width:{fill_percent * 0.866:.2f}%"></div>',
    ]

    for i, (number, label, _) in enumerate(steps):
        if state == "FAILED" and i == current_idx:
            cls = "failed"
        elif i < completed_count or (state == "COMPLETED" and i == 6):
            cls = "completed"
        elif i == current_idx:
            cls = "current"
        else:
            cls = "pending"

        dot = "✓" if cls == "completed" else "!" if cls == "failed" else number
        stage_html.append(
            f'<div class="pipeline-step {cls}">'
            f'<div class="pipeline-dot">{dot}</div>'
            f'<div class="pipeline-label">{label}</div>'
            '</div>'
        )

    stage_html.append('</div>')
    current_text = status.get("current_step", "Migration completed." if state == "COMPLETED" else "Waiting for migration...")
    stage_html.append(
        f'<div class="pipeline-progress-meta"><span><strong>{current_text}</strong></span>'
        f'<span>{progress}%</span></div>'
    )
    stage_html.append('</div>')
    st.markdown("".join(stage_html), unsafe_allow_html=True)

def wait_for_completion(
    run_id: str,
    placeholder,
    timeout_seconds: int = 7200,
) -> dict[str, Any]:

    started = time.monotonic()

    while True:

        status = get_status(run_id)

        # The placeholder is an st.empty() container holding the custom 7-step tracker.
        with placeholder.container():
            render_pipeline_progress(status)

        state = str(
            status.get("status", "UNKNOWN")
        ).upper()

        if state in {
            "COMPLETED",
            "FAILED",
        }:
            return status

        if time.monotonic() - started >= timeout_seconds:
            raise TimeoutError(
                f"Migration run {run_id} did not finish within "
                f"{timeout_seconds // 60} minutes."
            )

        time.sleep(1)


# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "run_id" not in st.session_state:
    st.session_state.run_id = None

if "run_status" not in st.session_state:
    st.session_state.run_status = None


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

with st.sidebar:

    st.markdown(
        """
<div class="sidebar-brand">
    <span class="sidebar-logo">▣</span>
    <span class="sidebar-title">EUC Migration<br>Platform</span>
    <div class="sidebar-subtitle">VBA to Python Migration</div>
</div>
""",
        unsafe_allow_html=True,
    )

    pages = [
        ("Dashboard", "⌂"),
        ("Upload & Run", "⇧"),
        ("Business Rules", "▦"),
        ("Generated Code", "⌘"),
        ("Validation", "✓"),
        ("Execution Results", "⚙"),
        ("Reports", "▤"),
        ("LLM Usage", "◉"),
        ("Logs & Status", "☷"),
    ]

    st.markdown('<div class="sidebar-heading">Navigation</div>', unsafe_allow_html=True)

    for page, icon in pages:

        if st.button(
            f"{icon}  {page}",
            key=f"nav_{page}",
        ):
            st.session_state.page = page
            st.rerun()

    st.markdown('<div class="sidebar-health">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-heading" style="margin-top:0;">System Status</div>', unsafe_allow_html=True)
    health_ok = False

    try:
        health = api_get("/health")
        health_ok = health.get("status") == "healthy"
    except Exception:
        pass

    if health_ok:
        st.markdown(
            '<div><span class="health-dot"></span><b style="color:#4bd584;">System Healthy</b></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#e45a5a;margin-right:7px;"></span><b style="color:#ff9a9a;">API Unavailable</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="color:#8198b5;font-size:10px;margin-top:14px;">Version 1.0.0</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.markdown(
    """
<div class="hero">
    <div class="eyebrow">Enterprise User Computing Modernisation</div>
    <h1>VBA → Python Migration Platform</h1>
    <p>
        Convert Excel-based VBA EUCs into traceable Python workflows,
        preserve business rules, validate generated code, and produce
        equivalent reporting outputs.
    </p>
    <div class="hero-art" aria-hidden="true">
        <div class="hero-doc left"><div class="hero-badge vba">VBA</div></div>
        <div class="hero-arrow">→</div>
        <div class="hero-doc right"><div class="hero-badge py">Py</div></div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Workflow strip
# ---------------------------------------------------------------------

workflow = [
    ("01", "Extract", "Raw VBA"),
    ("02", "Analyse", "Procedures"),
    ("03", "Understand", "LLM"),
    ("04", "Formalise", "Rules"),
    ("05", "Generate", "Python"),
    ("06", "Validate", "Static"),
    ("07", "Execute", "Reports"),
]

stage_icons = ["▤", "⌕", "✦", "☷", "</>", "✓", "▥"]

stage_html = ['<div class="workflow-grid">']
for (num, name, detail), icon in zip(workflow, stage_icons):
    stage_html.append(
        f"""
<div class="stage">
    <div class="stage-icon">{icon}</div>
    <div class="stage-number">STEP {num}</div>
    <div class="stage-name">{name}</div>
    <div class="stage-detail">{detail}</div>
</div>
"""
    )
stage_html.append("</div>")
st.markdown("".join(stage_html), unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Common current-run data
# ---------------------------------------------------------------------

run_id = st.session_state.run_id
run_status = None

if run_id:

    try:
        run_status = get_status(run_id)
        st.session_state.run_status = run_status
    except Exception as exc:
        st.warning(
            f"Unable to refresh run status: {exc}"
        )

render_run_badge(run_id, run_status)


# ---------------------------------------------------------------------
# Page: Dashboard
# ---------------------------------------------------------------------

if st.session_state.page == "Dashboard":

    st.markdown(
        '<div class="section-title">Migration Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">End-to-end migration of VBA Macro to Python</div>',
        unsafe_allow_html=True,
    )

    render_pipeline_progress(run_status)

    if not run_status:

        st.info(
            "No migration run selected. Use Upload & Run to start."
        )

    else:

        summary = run_status.get(
            "summary",
            {},
        )

        artifacts = run_status.get(
            "artifacts",
            {},
        )

        outputs = artifacts.get(
            "generated_outputs",
            [],
        )

        metrics = [
            (
                "WORKBOOK",
                run_status.get("workbook", "-"),
                "Source macro workbook",
            ),
            (
                "STATUS",
                run_status.get("status", "-"),
                "Pipeline status",
            ),
            (
                "PROCEDURES",
                summary.get("procedure_count", "-"),
                "Dynamically discovered",
            ),
            (
                "BUSINESS RULES",
                summary.get("business_rule_count", "-"),
                "Extracted",
            ),
            (
                "REPORTS",
                len(outputs),
                "Generated outputs",
            ),
            (
                "LLM TOKENS",
                summary.get("total_llm_tokens", "-"),
                "Steps 3–5",
            ),
        ]

        kpi_icons = ["▣", "✓", "♟", "☷", "▤", "▥"]

        cols = st.columns(6)

        for col, (label, value, sub), icon in zip(
            cols,
            metrics,
            kpi_icons,
        ):

            with col:

                failed_class = (
                    " kpi-failed"
                    if label == "STATUS"
                    and str(value).upper() == "FAILED"
                    else ""
                )

                st.markdown(
                    f"""
<div class="card kpi-card{failed_class}">
    <div class="kpi-icon">{icon}</div>
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value}</div>
    <div class="kpi-sub">{sub}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="section-title">Pipeline Status</div>',
            unsafe_allow_html=True,
        )

        if run_status.get("status") == "COMPLETED":
            st.success(
                "Migration completed successfully."
            )
        elif run_status.get("status") == "FAILED":
            st.error(
                run_status.get(
                    "error",
                    "Migration failed.",
                )
            )
        else:
            st.info(
                run_status.get(
                    "current_step",
                    "Migration is running.",
                )
            )


# ---------------------------------------------------------------------
# Page: Upload & Run
# ---------------------------------------------------------------------

elif st.session_state.page == "Upload & Run":

    st.markdown(
        '<div class="section-title">1. Upload & Run</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Upload any XLSB/XLSM EUC. Procedure and report names are discovered dynamically."
    )

    uploaded = st.file_uploader(
        "Upload Workbook",
        type=["xlsb", "xlsm"],
        help="Excel workbook containing VBA macros.",
    )

    if uploaded:

        c1, c2 = st.columns(
            [3, 1]
        )

        with c1:
            st.markdown(
                f"""
<div class="card">
    <div class="kpi-label">SELECTED FILE</div>
    <div class="kpi-value">{uploaded.name}</div>
    <div class="kpi-sub">{uploaded.size / 1024 / 1024:.2f} MB</div>
</div>
""",
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """
<div class="card">
    <div class="kpi-label">FORMAT</div>
    <div class="kpi-value">Macro</div>
    <div class="kpi-sub">XLSB / XLSM</div>
</div>
""",
                unsafe_allow_html=True,
            )

        if st.button(
            "▶  Start Migration Pipeline",
            type="primary",
            key="start_migration",
        ):

            try:

                submission = upload_pipeline(
                    uploaded.getvalue(),
                    uploaded.name,
                )

                st.session_state.run_id = submission[
                    "run_id"
                ]

                progress = st.empty()
                with progress.container():
                    render_pipeline_progress({
                        "status": "RUNNING",
                        "progress": 0,
                        "current_step": "Migration submitted...",
                    })

                final_status = wait_for_completion(
                    st.session_state.run_id,
                    progress,
                )

                st.session_state.run_status = final_status

                if final_status.get("status") == "COMPLETED":

                    st.success(
                        "Migration completed successfully."
                    )

                    st.session_state.page = "Dashboard"
                    st.rerun()

                else:

                    st.error(
                        final_status.get(
                            "error",
                            "Migration failed.",
                        )
                    )

            except Exception as exc:

                st.error(
                    f"Unable to start migration: {exc}"
                )


# ---------------------------------------------------------------------
# Page: Business Rules
# ---------------------------------------------------------------------

elif st.session_state.page == "Business Rules":

    st.markdown(
        '<div class="section-title">4. Business Rules</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Business-oriented understanding of what the EUC performs."
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        try:

            data = api_get(
                f"/pipeline/rules/{run_id}"
            )

            rules = data.get(
                "rules",
                [],
            )

            st.caption(
                f"{len(rules)} business rule(s) detected."
            )

            if not rules:
                st.warning(
                    "No business rules were returned by the Business Rule Agent."
                )

            for rule in rules:

                name = html.escape(
                    str(rule.get("name", "Business Rule"))
                )
                description = html.escape(
                    str(rule.get("description", ""))
                )
                source_procedure = html.escape(
                    str(rule.get("source_procedure", ""))
                )

                st.markdown(
                    f"""
<div class="rule">
    <div class="rule-title">
        {name}
    </div>
    <div class="rule-body">
        {description}
    </div>
    <div class="rule-source">
        Source procedure: {source_procedure}
    </div>
</div>
""",
                    unsafe_allow_html=True,
                )

        except Exception as exc:
            st.error(str(exc))

        st.markdown(
            '<div class="section-title">Business Rule Artifacts</div>',
            unsafe_allow_html=True,
        )

        for key, label in (
            (
                "business_rules",
                "Download business_rules.json",
            ),
            (
                "technical_business_rules",
                "Download technical business rules JSON",
            ),
            (
                "business_rules_docx",
                "Download business rules / BRD",
            ),
        ):

            try:
                data_bytes, mime = download_artifact(
                    run_id,
                    key,
                )

                st.download_button(
                    label,
                    data=data_bytes,
                    file_name=(
                        "business_rules.json"
                        if key == "business_rules"
                        else
                        "business_rules_technical.json"
                        if key == "technical_business_rules"
                        else
                        "business_rules.docx"
                    ),
                    mime=mime,
                    key=f"download_{key}",
                    use_container_width=True,
                )

            except Exception:
                pass


# ---------------------------------------------------------------------
# Page: Generated Code
# ---------------------------------------------------------------------

elif st.session_state.page == "Generated Code":

    st.markdown(
        '<div class="section-title">5. Generated Code</div>',
        unsafe_allow_html=True,
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        try:

            data_bytes, _ = download_artifact(
                run_id,
                "generated_python",
            )

            code = data_bytes.decode(
                "utf-8",
                errors="replace",
            )

            st.code(
                code,
                language="python",
            )

            st.download_button(
                "Download generated_euc.py",
                data=data_bytes,
                file_name="generated_euc.py",
                mime="text/x-python",
                use_container_width=True,
            )

        except Exception as exc:
            st.error(
                f"Generated Python unavailable: {exc}"
            )


# ---------------------------------------------------------------------
# Page: Validation
# ---------------------------------------------------------------------

elif st.session_state.page == "Validation":

    st.markdown(
        '<div class="section-title">6. Validation</div>',
        unsafe_allow_html=True,
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        status = run_status or {}

        # FastAPI stores pipeline results under status["summary"].
        summary = status.get(
            "summary",
            {},
        )

        validation = summary.get(
            "validation",
            {},
        )

        validation_status = validation.get(
            "status",
            "UNKNOWN",
        )

        if validation_status == "PASS":
            st.success(
                "✓ VALIDATION PASSED"
            )
        elif validation_status == "FAIL":
            st.error(
                "VALIDATION FAILED"
            )
        else:
            st.warning(
                f"Validation status: {validation_status}"
            )

        try:

            data_bytes, _ = download_artifact(
                run_id,
                "python_validation",
            )

            st.download_button(
                "Download Validation Report (JSON)",
                data=data_bytes,
                file_name="generated_python_validation.json",
                mime="application/json",
                use_container_width=True,
            )

            with st.expander(
                "View validation JSON"
            ):
                st.json(
                    json.loads(
                        data_bytes.decode(
                            "utf-8"
                        )
                    )
                )

        except Exception as exc:
            st.warning(
                f"Validation report unavailable: {exc}"
            )


# ---------------------------------------------------------------------
# Page: Execution Results
# ---------------------------------------------------------------------

elif st.session_state.page == "Execution Results":

    st.markdown(
        '<div class="section-title">7. Execution Results</div>',
        unsafe_allow_html=True,
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        try:

            data_bytes, _ = download_artifact(
                run_id,
                "python_execution",
            )

            execution = json.loads(
                data_bytes.decode(
                    "utf-8"
                )
            )

            results = execution.get(
                "results",
                [],
            )

            total = len(results)
            succeeded = sum(
                1
                for item in results
                if str(
                    item.get("status", "")
                ).upper()
                in {
                    "SUCCESS",
                    "PASS",
                    "COMPLETED",
                }
            )

            a, b, c = st.columns(3)

            for col, label, value in (
                (a, "TOTAL PROCEDURES", total),
                (b, "SUCCEEDED", succeeded),
                (c, "FAILED", total - succeeded),
            ):

                with col:
                    st.markdown(
                        f"""
<div class="card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )

            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True,
            )

        except Exception as exc:
            st.error(
                f"Execution results unavailable: {exc}"
            )


# ---------------------------------------------------------------------
# Page: Reports
# ---------------------------------------------------------------------

elif st.session_state.page == "Reports":

    st.markdown(
        '<div class="section-title">6. Reports</div>',
        unsafe_allow_html=True,
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        try:

            status = get_status(
                run_id
            )

            outputs = status.get(
                "artifacts",
                {},
            ).get(
                "generated_outputs",
                [],
            )

            if not outputs:
                st.info(
                    "No generated Excel reports found."
                )

            for index, relative_path in enumerate(
                outputs
            ):

                filename = Path(
                    relative_path
                ).name

                st.markdown(
                    f"""
<div class="output-row">
    <strong>▣ {filename}</strong>
</div>
""",
                    unsafe_allow_html=True,
                )

                try:

                    data_bytes, mime = download_artifact(
                        run_id,
                        filename,
                    )

                    st.download_button(
                        "Download",
                        data=data_bytes,
                        file_name=filename,
                        mime=mime,
                        key=f"report_{index}",
                    )

                except Exception as exc:
                    st.caption(
                        f"Unavailable: {exc}"
                    )

        except Exception as exc:
            st.error(str(exc))


# ---------------------------------------------------------------------
# Page: LLM Usage
# ---------------------------------------------------------------------

elif st.session_state.page == "LLM Usage":

    st.markdown(
        '<div class="section-title">7. LLM Usage</div>',
        unsafe_allow_html=True,
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        try:

            usage = api_get(
                f"/pipeline/tokens/{run_id}"
            )

            if isinstance(
                usage,
                dict,
            ) and "steps" in usage:

                raw_steps = usage["steps"]

                if isinstance(raw_steps, dict):
                    rows = []
                    for step_name, item in raw_steps.items():
                        if not isinstance(item, dict):
                            continue
                        rows.append(
                            {
                                "step": step_name,
                                "calls": item.get("calls", 0),
                                "input_tokens": item.get("input_tokens", 0),
                                "output_tokens": item.get("output_tokens", 0),
                                "total_tokens": item.get("total_tokens", 0),
                            }
                        )
                elif isinstance(raw_steps, list):
                    rows = raw_steps
                else:
                    rows = []

                if rows:
                    st.dataframe(
                        rows,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No LLM token usage recorded for this run.")

                st.caption(
                    "LLM token consumption is recorded for Steps 3, 4 and 5 only."
                )

            else:

                st.json(
                    usage
                )

        except Exception as exc:
            st.error(str(exc))


# ---------------------------------------------------------------------
# Page: Logs & Status
# ---------------------------------------------------------------------

elif st.session_state.page == "Logs & Status":

    st.markdown(
        '<div class="section-title">8. Logs & Status</div>',
        unsafe_allow_html=True,
    )

    if not run_id:
        st.info("Run a migration first.")
    else:

        try:

            status = get_status(
                run_id
            )

            st.markdown(
                f"""
<div class="card">
    <div class="kpi-label">PIPELINE STATUS</div>
    <div class="kpi-value">{status.get("status", "UNKNOWN")}</div>
    <div class="kpi-sub">
        {status.get("current_step", "")}
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="section-title">Execution Log</div>',
                unsafe_allow_html=True,
            )

            try:
                log_data = api_get(
                    f"/pipeline/logs/{run_id}"
                )

                st.code(
                    log_data.get(
                        "content",
                        "No log available.",
                    ),
                    language="text",
                )

                st.caption(
                    f"Run-specific log: {log_data.get('log_file', '')}"
                )

            except Exception as exc:
                st.warning(
                    f"Unable to load pipeline log: {exc}"
                )

        except Exception as exc:
            st.error(str(exc))


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

st.markdown(
    """
<div class="footer">
    EUC Modernisation Platform · VBA reverse engineering ·
    Business-rule preservation · Python generation ·
    Static validation · Deterministic execution
</div>
""",
    unsafe_allow_html=True,
)
