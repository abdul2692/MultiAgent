"""
Streamlit Web Dashboard for Multi-Agent Research Assistant.
Modern, sleek, portfolio-grade UI with advanced styling, live agent stepper,
topic presets, interactive citations, and telemetry dashboards.
"""
import os
import sys
import time
import tempfile
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from graph.workflow import create_research_graph
from graph.state import ResearchState
from tools.report_generator import export_to_markdown, export_to_pdf
from utils.metrics import tracker
from utils.llm_factory import is_cloud_mode
from utils.ollama_manager import ensure_ollama_running

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ResearchMatrix AI | Multi-Agent Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Modern CSS Design System
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hero Header Banner */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 32px 36px;
        margin-bottom: 24px;
        color: #F8FAFC;
        box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.4);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        background: linear-gradient(90deg, #FFFFFF, #94A3B8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-top: 8px;
        max-width: 800px;
        line-height: 1.5;
    }

    /* Agent Status Card Grid */
    .agent-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
    }
    .agent-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .agent-icon {
        font-size: 1.6rem;
    }
    .agent-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 2px;
    }
    .agent-desc {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.4;
    }
    .badge-status {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .status-idle { background: #F1F5F9; color: #64748B; }
    .status-running { background: #E0F2FE; color: #0284C7; border: 1px solid #BAE6FD; }
    .status-success { background: #DCFCE7; color: #16A34A; border: 1px solid #BBF7D0; }

    /* Telemetry Metric Cards */
    .telemetry-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .telemetry-val {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
    }
    .telemetry-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Executive Callout */
    .exec-callout {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border-left: 4px solid #16A34A;
        padding: 18px 22px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: #14532D;
    }

    /* Source Citation Card */
    .source-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .source-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1E3A8A;
        text-decoration: none;
    }
    .source-url {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #64748B;
        word-break: break-all;
    }
    .source-snippet {
        font-size: 0.85rem;
        color: #334155;
        margin-top: 6px;
        line-height: 1.45;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Configuration & Telemetry
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <span style="font-size:1.8rem;">🔬</span>
        <div>
            <div style="font-size:1.15rem; font-weight:800; color:#0F172A; line-height:1.1;">ResearchMatrix</div>
            <div style="font-size:0.75rem; font-weight:600; color:#64748B;">Multi-Agent Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Check and display LLM status — cloud or local
    if is_cloud_mode():
        is_ollama_ready = True   # Groq cloud API — always available
        st.success("🟢 Cloud LLM: Groq API Connected (`llama-3.1-8b-instant`)")
    else:
        is_ollama_ready = ensure_ollama_running()
        if is_ollama_ready:
            st.success("🟢 Local Ollama: Connected (`llama3.2:1b`)")
        else:
            st.error("🔴 Local Ollama: Offline")

    st.markdown("---")
    st.markdown("### 📊 Operational Telemetry")
    metrics_data = tracker.load_metrics()
    summary = metrics_data.get("summary", {})

    c_t1, c_t2 = st.columns(2)
    with c_t1:
        st.markdown(f"""
        <div class="telemetry-card">
            <div class="telemetry-val">{summary.get('total_tasks', 0)}</div>
            <div class="telemetry-label">Completed</div>
        </div>
        """, unsafe_allow_html=True)
    with c_t2:
        st.markdown(f"""
        <div class="telemetry-card">
            <div class="telemetry-val">₹0.00</div>
            <div class="telemetry-label">Total Cost</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    c_t3, c_t4 = st.columns(2)
    with c_t3:
        avg_t = summary.get('avg_execution_time_seconds', 0.0)
        st.markdown(f"""
        <div class="telemetry-card">
            <div class="telemetry-val">{avg_t:.0f}s</div>
            <div class="telemetry-label">Avg Runtime</div>
        </div>
        """, unsafe_allow_html=True)
    with c_t4:
        sources_cnt = summary.get('total_sources_collected', 0)
        st.markdown(f"""
        <div class="telemetry-card">
            <div class="telemetry-val">{sources_cnt}</div>
            <div class="telemetry-label">Sources Mined</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ Engine Parameters")
    search_depth = st.radio("Web Search Breadth:", ["Standard (4 sources)", "Deep (8 sources)"], index=0)
    max_search_res = 8 if "Deep" in search_depth else 4
    
    st.caption("Running purely local open-source inference. Zero external API calls, zero tracking, zero credit cards.")

# ---------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">✨ Multi-Agent System • Zero Budget Architecture</div>
    <div class="hero-title">ResearchMatrix AI</div>
    <div class="hero-subtitle">
        Four specialized AI agents collaborate autonomously through LangGraph to mine live web indexes,
        ingest local documents, detect contradictions, and synthesize formal intelligence briefings.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Multi-Agent Pipeline Visualization (Static/Live)
# ---------------------------------------------------------
st.markdown("##### 👥 Active Multi-Agent Topology")

col_a1, col_a2, col_a3, col_a4 = st.columns(4)

with col_a1:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">🔍</span>
            <span class="badge-status status-idle" id="badge-a1">Agent 1</span>
        </div>
        <div class="agent-title">Researcher</div>
        <div class="agent-desc">Decomposes inquiries and queries live web indexes for primary sources.</div>
    </div>
    """, unsafe_allow_html=True)

with col_a2:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">📑</span>
            <span class="badge-status status-idle" id="badge-a2">Agent 2</span>
        </div>
        <div class="agent-title">Reader</div>
        <div class="agent-desc">Extracts text passages from local PDFs with page citations.</div>
    </div>
    """, unsafe_allow_html=True)

with col_a3:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">🧠</span>
            <span class="badge-status status-idle" id="badge-a3">Agent 3</span>
        </div>
        <div class="agent-title">Analyst</div>
        <div class="agent-desc">Cross-references evidence, flags discrepancies, and detects data gaps.</div>
    </div>
    """, unsafe_allow_html=True)

with col_a4:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">✍️</span>
            <span class="badge-status status-idle" id="badge-a4">Agent 4</span>
        </div>
        <div class="agent-title">Writer</div>
        <div class="agent-desc">Synthesizes findings into formal briefings with numbered bibliographies.</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------
# Interactive Quick Presets
# ---------------------------------------------------------
st.markdown("##### ⚡ Quick Research Topics")
preset_cols = st.columns(4)

presets = [
    ("🚀 Solid-State Aviation Batteries", "Commercial Feasibility of Solid-State Batteries in Commercial Aviation"),
    ("⚛️ Quantum Drug Discovery", "Quantum Computing Applications in Molecular Drug Discovery"),
    ("🧬 CRISPR Agri-Genomics", "CRISPR-Cas9 Crop Resistance and Food Security Trends"),
    ("🔋 Sodium-Ion Grid Storage", "Sodium-Ion vs Lithium-Ion for Grid Scale Energy Storage 2025")
]

selected_preset = ""
for idx, (label, topic_text) in enumerate(presets):
    if preset_cols[idx].button(label, use_container_width=True):
        st.session_state["topic_input"] = topic_text

# ---------------------------------------------------------
# Input Section
# ---------------------------------------------------------
col_input, col_upload = st.columns([2, 1])

with col_input:
    current_topic = st.session_state.get("topic_input", "")
    user_topic = st.text_input(
        "Enter Research Topic or Strategic Query:",
        value=current_topic,
        placeholder="e.g. Next-Generation Perovskite Solar Cell Commercialization",
        help="Type any technical, scientific, or market research question."
    )

with col_upload:
    uploaded_files = st.file_uploader(
        "Upload PDF Research Papers (Optional):",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload local PDFs. The Reader Agent will parse pages and cite page numbers."
    )

start_clicked = st.button("🚀 Start Autonomous Research", type="primary", use_container_width=True)

# ---------------------------------------------------------
# Pipeline Execution
# ---------------------------------------------------------
if start_clicked:
    if not user_topic.strip():
        st.warning("⚠️ Please provide a research topic before launching the agents.")
    elif not is_ollama_ready and not is_cloud_mode():
        st.error("⚠️ Ollama local server is offline. Please start Ollama before proceeding.")
    else:
        # Ingest PDF files
        pdf_paths = []
        if uploaded_files:
            temp_dir = tempfile.mkdtemp()
            for uf in uploaded_files:
                temp_path = os.path.join(temp_dir, uf.name)
                with open(temp_path, "wb") as f:
                    f.write(uf.get_buffer().read())
                pdf_paths.append(temp_path)

        st.markdown("---")
        progress_banner = st.empty()
        progress_bar = st.progress(0.0)
        
        status_col1, status_col2, status_col3, status_col4 = st.columns(4)
        box_r = status_col1.empty()
        box_d = status_col2.empty()
        box_a = status_col3.empty()
        box_w = status_col4.empty()

        box_r.info("🔍 Researcher: Queued")
        box_d.info("📑 Reader: Queued")
        box_a.info("🧠 Analyst: Queued")
        box_w.info("✍️ Writer: Queued")

        start_time = time.time()
        
        # Build StateGraph
        app = create_research_graph()
        initial_state: ResearchState = {
            "topic": user_topic.strip(),
            "pdf_paths": pdf_paths,
            "researcher_output": None,
            "reader_output": None,
            "analyst_output": None,
            "final_report": None,
            "iteration_count": 0,
            "status_message": "Pipeline initialized.",
            "error_message": None
        }

        # Step 1: Researcher Active
        progress_banner.info("🔄 [Stage 1/4] **Researcher Agent** formulating queries and querying live web...")
        box_r.warning("🔍 Researcher: In Progress...")
        progress_bar.progress(0.20)

        # Run pipeline
        final_state = app.invoke(initial_state)

        # Step 2: Completed Stepper Updates
        box_r.success("🔍 Researcher: Completed")
        box_d.success(f"📑 Reader: Completed ({len(final_state['reader_output'].chunks)} chunks)")
        box_a.success(f"🧠 Analyst: Completed")
        box_w.success("✍️ Writer: Completed")
        progress_bar.progress(1.0)

        duration = time.time() - start_time
        progress_banner.success(f"🎉 **Autonomous Research Completed in {duration:.1f}s** | Zero-Budget Local Execution")

        # Save to session
        st.session_state["result_state"] = final_state
        st.session_state["duration"] = duration

        # Record Telemetry
        res_sources = len(final_state["researcher_output"].sources) if final_state.get("researcher_output") else 0
        doc_chunks = len(final_state["reader_output"].chunks) if final_state.get("reader_output") else 0
        total_sources = res_sources + doc_chunks

        tracker.record_run(
            topic=user_topic,
            duration_seconds=duration,
            success=True,
            sources_count=total_sources,
            agent_statuses={"all_agents": "completed"}
        )

# ---------------------------------------------------------
# Results Presentation
# ---------------------------------------------------------
if "result_state" in st.session_state and st.session_state["result_state"].get("final_report"):
    state = st.session_state["result_state"]
    report = state["final_report"]
    researcher_out = state["researcher_output"]
    reader_out = state["reader_output"]
    analyst_out = state["analyst_output"]

    st.markdown("---")

    # Export Documents
    md_path = export_to_markdown(report)
    pdf_path = export_to_pdf(report)

    # Action Toolbar
    col_dl_md, col_dl_pdf, col_meta = st.columns([1.2, 1.2, 2.6])

    with col_dl_md:
        with open(md_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Export Markdown",
                data=f.read(),
                file_name=os.path.basename(md_path),
                mime="text/markdown",
                use_container_width=True
            )

    with col_dl_pdf:
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📑 Export Executive PDF",
                data=f.read(),
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True
            )

    with col_meta:
        quality_pct = int(analyst_out.source_quality_score * 100)
        st.markdown(f"""
        <div style="background:#F1F5F9; border-radius:10px; padding:8px 16px; display:flex; justify-content:space-between; align-items:center;">
            <span>🛡️ Confidence Score: <b>{quality_pct}%</b></span>
            <span>📚 Sources Consulted: <b>{len(report.references)}</b></span>
            <span>⚡ Cost: <b>₹0.00</b></span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Tabbed Interface
    tab_report, tab_analyst, tab_sources, tab_workflow = st.tabs([
        "📄 Executive Briefing Report",
        "🧠 Analysis & Contradiction Matrix",
        "🌐 Source Evidence Corpus",
        "⚙️ LangGraph Architecture & State"
    ])

    with tab_report:
        st.markdown(f"## {report.title}")
        
        # Executive Summary Callout
        st.markdown(f"""
        <div class="exec-callout">
            <div style="font-weight:700; font-size:1.05rem; margin-bottom:6px;">📌 Executive Summary</div>
            <div style="line-height:1.6;">{report.executive_summary}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔬 Research Methodology")
        st.info(report.methodology)

        st.markdown("### 📊 Synthesized Findings")
        st.markdown(report.findings)

        st.markdown("### ⚖️ Critical Analysis & Feasibility")
        st.markdown(report.analysis)

        st.markdown("### 🎯 Strategic Conclusion & Roadmap")
        st.success(report.conclusion)

    with tab_analyst:
        st.markdown("### 🧠 Strategic Synthesis & Gap Detection")
        
        c_ins, c_gaps = st.columns([1, 1])

        with c_ins:
            st.markdown("#### 💡 Core Overarching Insights")
            for ins in analyst_out.core_insights:
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:12px; margin-bottom:8px; border-left:4px solid #3B82F6;">
                    {ins}
                </div>
                """, unsafe_allow_html=True)

        with c_gaps:
            st.markdown("#### ⚡ Contradictions & Discrepancies")
            if analyst_out.contradictions:
                for con in analyst_out.contradictions:
                    st.markdown(f"""
                    <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:12px; margin-bottom:8px; border-left:4px solid #F59E0B; color:#92400E;">
                        {con}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No empirical contradictions detected across the consulted evidence.")

            st.markdown("#### ❓ Identified Knowledge Gaps")
            for gap in analyst_out.identified_gaps:
                st.markdown(f"""
                <div style="background:#F0F9FF; border:1px solid #BAE6FD; border-radius:10px; padding:12px; margin-bottom:8px; border-left:4px solid #0EA5E9; color:#0369A1;">
                    {gap}
                </div>
                """, unsafe_allow_html=True)

    with tab_sources:
        st.markdown("### 🌐 Evidence Corpus & Indexed Citations")
        
        st.markdown("#### Live Web Sources (Researcher Agent)")
        if researcher_out and researcher_out.sources:
            for s in researcher_out.sources:
                st.markdown(f"""
                <div class="source-box">
                    <div><a class="source-title" href="{s.url}" target="_blank">🔗 {s.title}</a></div>
                    <div class="source-url">{s.url}</div>
                    <div class="source-snippet">{s.snippet}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No live web sources were indexed.")

        st.markdown("#### Document Passages (Reader Agent)")
        if reader_out and reader_out.chunks:
            for c in reader_out.chunks:
                with st.expander(f"📄 {c.file_name} — Page {c.page_number}"):
                    st.write(c.text)
        else:
            st.caption("No local PDF documents were uploaded for this session.")

    with tab_workflow:
        st.markdown("### ⚙️ Multi-Agent Architecture & State Machine")
        
        # Display Mermaid Diagram
        st.markdown("""
        ```mermaid
        flowchart LR
            Start([START]) --> Researcher[Node 1: Researcher]
            Researcher --> Gate{Quality Gate}
            Gate -- "Sources < 1" --> Researcher
            Gate -- "Verified" --> Reader[Node 2: Reader]
            Reader --> Analyst[Node 3: Analyst]
            Analyst --> Writer[Node 4: Writer]
            Writer --> EndNode([END])
        ```
        """)

        st.markdown("#### Current State Payload")
        st.json({
            "topic": state.get("topic"),
            "iteration_count": state.get("iteration_count"),
            "sources_count": len(researcher_out.sources) if researcher_out else 0,
            "documents_count": len(reader_out.documents_read) if reader_out else 0,
            "status_message": state.get("status_message")
        })
