"""
CAG vs RAG Showdown — Streamlit Dashboard
==========================================
Run: streamlit run dashboard/app.py
"""

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", str(Path(__file__).parent.parent / "results")))

st.set_page_config(
    page_title="CAG vs RAG Showdown",
    page_icon="⚔️",
    layout="wide",
)

st.title("⚔️ CAG vs RAG Benchmark Dashboard")

# ---------------------------------------------------------------------------
# Sidebar — file selection
# ---------------------------------------------------------------------------

result_files = sorted(RESULTS_DIR.glob("benchmark_*.json"), reverse=True)

if not result_files:
    st.warning("No benchmark results found yet.")
    st.info("Run a benchmark first:  `python main.py benchmark`")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Benchmark Run",
    result_files,
    format_func=lambda p: p.stem,
)

with open(selected_file, encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]
results = data["results"]

st.sidebar.caption(f"Run timestamp: {data.get('timestamp', 'unknown')}")
st.sidebar.caption(f"Questions: {summary['num_questions']}")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

st.subheader("Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### CAG")
    st.metric("Avg Judge Score", f"{summary['cag']['avg_judge_score']:.2f} / 5")
    st.metric("Avg Latency", f"{summary['cag']['avg_latency_seconds']:.2f}s")
    st.metric("Wins", summary["cag"]["wins"])

with col2:
    st.markdown("### RAG")
    st.metric("Avg Judge Score", f"{summary['rag']['avg_judge_score']:.2f} / 5")
    st.metric("Avg Latency", f"{summary['rag']['avg_latency_seconds']:.2f}s")
    st.metric("Wins", summary["rag"]["wins"])

with col3:
    st.markdown("### Head-to-head")
    st.metric("Ties", summary["ties"])
    total = summary["num_questions"]
    cag_pct = round(summary["cag"]["wins"] / total * 100) if total else 0
    rag_pct = round(summary["rag"]["wins"] / total * 100) if total else 0
    st.write(f"CAG win rate: **{cag_pct}%**")
    st.write(f"RAG win rate: **{rag_pct}%**")

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

chart_col1, chart_col2 = st.columns(2)

ids = [r["id"] for r in results]
cag_scores = [r["cag"]["judge_scores"].get("total", 0) for r in results]
rag_scores = [r["rag"]["judge_scores"].get("total", 0) for r in results]
cag_latencies = [r["cag"]["latency_seconds"] for r in results]
rag_latencies = [r["rag"]["latency_seconds"] for r in results]

with chart_col1:
    st.subheader("Judge Score by Question")
    score_df = pd.DataFrame({"CAG": cag_scores, "RAG": rag_scores}, index=ids)
    st.bar_chart(score_df, y_label="Score (0–5)")

with chart_col2:
    st.subheader("Latency by Question (s)")
    latency_df = pd.DataFrame({"CAG": cag_latencies, "RAG": rag_latencies}, index=ids)
    st.bar_chart(latency_df, y_label="Seconds")

st.divider()

# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------

st.subheader("Per-Question Results")
rows = []
for r in results:
    cag_s = r["cag"]["judge_scores"].get("total", 0)
    rag_s = r["rag"]["judge_scores"].get("total", 0)
    rows.append(
        {
            "ID": r["id"],
            "Category": r["category"],
            "Question": r["question"][:70] + ("..." if len(r["question"]) > 70 else ""),
            "CAG Score": cag_s,
            "RAG Score": rag_s,
            "CAG Latency (s)": r["cag"]["latency_seconds"],
            "RAG Latency (s)": r["rag"]["latency_seconds"],
            "Winner": "CAG" if cag_s > rag_s else ("RAG" if rag_s > cag_s else "TIE"),
        }
    )

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Per-question detail
# ---------------------------------------------------------------------------

st.subheader("Question Detail")
selected_id = st.selectbox("Select question", ids)
q_data = next(r for r in results if r["id"] == selected_id)

st.markdown(f"**Category:** {q_data['category']}")
st.markdown(f"**Question:** {q_data['question']}")
st.markdown(f"**Expected concepts:** {', '.join(q_data.get('expected_concepts', []))}")

detail_col1, detail_col2 = st.columns(2)

with detail_col1:
    st.markdown("#### CAG Answer")
    st.write(q_data["cag"]["answer"])
    scores = q_data["cag"]["judge_scores"]
    if scores:
        st.markdown("**Judge Scores**")
        st.json({k: v for k, v in scores.items() if k != "total"})
        st.metric("Total", f"{scores.get('total', 'N/A')} / 5")

with detail_col2:
    st.markdown("#### RAG Answer")
    st.write(q_data["rag"]["answer"])
    retrieved = q_data["rag"].get("retrieved_chunks") or []
    if retrieved:
        st.markdown(f"**Retrieved chunks:** {[c['title'] for c in retrieved]}")
    scores = q_data["rag"]["judge_scores"]
    if scores:
        st.markdown("**Judge Scores**")
        st.json({k: v for k, v in scores.items() if k != "total"})
        st.metric("Total", f"{scores.get('total', 'N/A')} / 5")
