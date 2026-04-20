"""
Scraper Insight — Analytics Dashboard
Run with:  cd scraper_insight && streamlit run dashboard/app.py
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dashboard.pdf_export import generate_pdf
from scrapers import ALL_SCRAPERS
from storage.results import load_all_runs, load_latest_run, list_runs

# ── Static vendor metadata (pricing + capabilities) ─────────────────────────

VENDOR_META: dict[str, dict] = {}
for _cls in ALL_SCRAPERS:
    VENDOR_META[_cls.vendor_name] = {
        "free_tier_limit": _cls.free_tier_limit,
        "paid_entry_usd": _cls.paid_entry_price_usd,
        "paid_entry_credits": _cls.paid_entry_credits,
        "usd_per_credit": round(_cls.usd_per_credit(), 6),
        "supports_js": _cls.supports_js,
        "supports_proxy": _cls.supports_proxy,
        "returns_structured": _cls.returns_structured,
    }

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Scraper Insight",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.title("🕷️ Scraper Insight")
st.sidebar.markdown("Comparing free-tier web scraping APIs")

run_files = list_runs()
data_source = st.sidebar.radio("Data source", ["Latest run", "All runs (historical)"])

if st.sidebar.button("↺ Refresh"):
    st.rerun()

# ── Load benchmark data ───────────────────────────────────────────────────────

if data_source == "Latest run":
    raw = load_latest_run()
else:
    raw = load_all_runs()

st.title("🕷️ Scraper Insight — Vendor Analytics")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Pricing & Free Tier Overview (static, no benchmark needed)
# ══════════════════════════════════════════════════════════════════════════════

st.header("Pricing & Free Tier Comparison")
st.caption("Static vendor metadata — no benchmark run required")

pricing_rows = []
for vendor, m in VENDOR_META.items():
    pricing_rows.append({
        "Vendor": vendor,
        "Free Tier (req/mo)": f"{m['free_tier_limit']:,}",
        "Paid Entry ($/mo)": f"${m['paid_entry_usd']:.2f}" if m["paid_entry_usd"] > 0 else "—",
        "Paid Credits": f"{m['paid_entry_credits']:,}" if m["paid_entry_credits"] > 0 else "—",
        "Cost/Credit (paid)": f"${m['usd_per_credit']:.6f}" if m["usd_per_credit"] > 0 else "—",
        "JS Render": "✓" if m["supports_js"] else "✗",
        "Proxy": "✓" if m["supports_proxy"] else "✗",
        "Structured Output": "✓" if m["returns_structured"] else "✗",
    })

pricing_df = pd.DataFrame(pricing_rows)
st.dataframe(pricing_df, use_container_width=True, hide_index=True)

# Highlight callouts
col_a, col_b, col_c = st.columns(3)
with col_a:
    cheapest = min(VENDOR_META.items(), key=lambda x: x[1]["usd_per_credit"] if x[1]["usd_per_credit"] > 0 else 9999)
    st.info(f"**Most credit-efficient (paid):** {cheapest[0]}  \n${cheapest[1]['usd_per_credit']:.6f}/credit")
with col_b:
    most_free = max(VENDOR_META.items(), key=lambda x: x[1]["free_tier_limit"])
    st.success(f"**Most generous free tier:** {most_free[0]}  \n{most_free[0]} gives {most_free[1]['free_tier_limit']:,} req/month free")
with col_c:
    structured = [v for v, m in VENDOR_META.items() if m["returns_structured"]]
    if structured:
        st.warning(f"**Returns structured data (not HTML):** {', '.join(structured)}  \nCompare separately — apples vs oranges")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Benchmark Results
# ══════════════════════════════════════════════════════════════════════════════

if not raw:
    st.warning(
        "No benchmark results yet. Run the benchmark first:\n\n"
        "```bash\ncd scraper_insight\npython -m benchmark.runner\n```"
    )
    st.stop()

df = pd.DataFrame(raw)

# Back-compat: fill columns added after the initial schema
for _col, _default in [
    ("estimated_cost_usd", 0.0),
    ("parsed_text_length", None),
    ("parsed_fields", None),
    ("returns_structured", False),
    ("label", ""),
]:
    if _col not in df.columns:
        df[_col] = _default

df["response_time_s"] = df["response_time_ms"] / 1000
df["success_int"] = df["success"].astype(int)
df["content_kb"] = df["content_length"] / 1024

all_vendors = sorted(df["vendor"].unique().tolist())
all_urls = sorted(df["url"].unique().tolist())

st.sidebar.markdown("---")
selected_vendors = st.sidebar.multiselect("Vendors", all_vendors, default=all_vendors)
selected_urls = st.sidebar.multiselect("Target URLs", all_urls, default=all_urls)
df_f = df[df["vendor"].isin(selected_vendors) & df["url"].isin(selected_urls)]

st.header("Benchmark Results")
st.caption(
    f"Loaded **{len(df_f)}** results from **{len(run_files)}** run(s) · Source: *{data_source}*"
)

# ── Per-vendor summary ────────────────────────────────────────────────────────

summary = (
    df_f.groupby("vendor")
    .agg(
        success_rate=("success_int", "mean"),
        avg_response_ms=("response_time_ms", "mean"),
        p95_response_ms=("response_time_ms", lambda x: x.quantile(0.95)),
        total_credits=("credits_used", "sum"),
        total_cost_usd=("estimated_cost_usd", "sum"),
        total_requests=("url", "count"),
        avg_content_kb=("content_kb", "mean"),
    )
    .reset_index()
)
summary["success_rate_pct"] = (summary["success_rate"] * 100).round(1)
summary["avg_response_ms"] = summary["avg_response_ms"].round(0).astype(int)
summary["p95_response_ms"] = summary["p95_response_ms"].round(0).astype(int)
summary["avg_content_kb"] = summary["avg_content_kb"].round(1)
summary["cost_per_success"] = (
    summary["total_cost_usd"] / (summary["success_rate"] * summary["total_requests"])
).round(6)

# KPI cards
kpi_cols = st.columns(len(summary))
for col, (_, row) in zip(kpi_cols, summary.iterrows()):
    with col:
        st.metric(
            label=row["vendor"],
            value=f"{row['success_rate_pct']}%",
            delta=f"{row['avg_response_ms']} ms avg",
        )

# ── Smart Insights ────────────────────────────────────────────────────────────

st.subheader("Smart Insights")

insights = []
if len(summary) > 1:
    best_success = summary.loc[summary["success_rate_pct"].idxmax()]
    worst_success = summary.loc[summary["success_rate_pct"].idxmin()]
    fastest = summary.loc[summary["avg_response_ms"].idxmin()]
    slowest = summary.loc[summary["avg_response_ms"].idxmax()]
    lowest_p95 = summary.loc[summary["p95_response_ms"].idxmin()]
    most_content = summary.loc[summary["avg_content_kb"].idxmax()]

    non_structured = summary[~summary["vendor"].isin(
        [v for v, m in VENDOR_META.items() if m["returns_structured"]]
    )]

    if best_success["success_rate_pct"] > worst_success["success_rate_pct"]:
        insights.append(("success", "Most reliable",
            f"**{best_success['vendor']}** has the highest success rate at "
            f"**{best_success['success_rate_pct']}%** — "
            f"{best_success['success_rate_pct'] - worst_success['success_rate_pct']:.1f}pp ahead of "
            f"{worst_success['vendor']} ({worst_success['success_rate_pct']}%)"))

    insights.append(("speed", "Fastest",
        f"**{fastest['vendor']}** is the fastest at **{fastest['avg_response_ms']} ms** avg "
        f"({fastest['p95_response_ms']} ms p95) — "
        f"{slowest['avg_response_ms'] - fastest['avg_response_ms']} ms faster than "
        f"{slowest['vendor']} ({slowest['avg_response_ms']} ms)"))

    insights.append(("consistency", "Most consistent (low p95)",
        f"**{lowest_p95['vendor']}** has the lowest p95 latency at **{lowest_p95['p95_response_ms']} ms**, "
        f"meaning fewer slow outliers — good for time-sensitive pipelines"))

    if not non_structured.empty:
        most_content_ns = non_structured.loc[non_structured["avg_content_kb"].idxmax()]
        insights.append(("content", "Most content returned (HTML scrapers only)",
            f"**{most_content_ns['vendor']}** returns the most content at "
            f"**{most_content_ns['avg_content_kb']:.1f} KB** avg — "
            f"likely fewer truncated responses"))

    # Cost efficiency: cost per successful request on paid tier
    valid_cost = summary[summary["cost_per_success"] > 0]
    if not valid_cost.empty:
        cheapest_success = valid_cost.loc[valid_cost["cost_per_success"].idxmin()]
        insights.append(("cost", "Most cost-efficient (paid tier)",
            f"**{cheapest_success['vendor']}** costs **${cheapest_success['cost_per_success']:.6f}** "
            f"per successful request on the paid tier — lowest effective cost"))

    # Warn about low success rate
    bad = summary[summary["success_rate_pct"] < 50]
    for _, row in bad.iterrows():
        insights.append(("warn", f"{row['vendor']} — Low success rate",
            f"**{row['vendor']}** only succeeded on **{row['success_rate_pct']}%** of requests in this run. "
            f"Consider enabling proxy/JS options, or this vendor may struggle with these targets."))

    # Diffbot note
    diffbot_row = summary[summary["vendor"] == "Diffbot"]
    if not diffbot_row.empty:
        df_dt = df_f[df_f["vendor"] == "Diffbot"]
        avg_text = df_dt["parsed_text_length"].dropna().mean()
        avg_fields = df_dt["parsed_fields"].dropna().mean()
        if avg_text > 0:
            insights.append(("diffbot", "Diffbot — Structured extraction quality",
                f"Diffbot extracted **{avg_text:.0f} chars** of clean body text and "
                f"**{avg_fields:.0f} structured fields** per page on average. "
                f"Unlike HTML scrapers, it returns ready-to-use data with no parsing needed."))

ins_cols = st.columns(2)
for i, (tag, title, body) in enumerate(insights):
    col = ins_cols[i % 2]
    with col:
        if tag == "warn":
            st.error(f"**{title}**  \n{body}")
        elif tag in ("success", "diffbot"):
            st.success(f"**{title}**  \n{body}")
        elif tag == "cost":
            st.info(f"**{title}**  \n{body}")
        else:
            st.info(f"**{title}**  \n{body}")

st.divider()

# ── Charts — Performance ──────────────────────────────────────────────────────

st.subheader("Performance")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Success Rate (%)**")
    fig = px.bar(
        summary, x="vendor", y="success_rate_pct", color="vendor",
        text="success_rate_pct", range_y=[0, 110],
        labels={"success_rate_pct": "Success Rate (%)", "vendor": "Vendor"},
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Avg Response Time + p95 (ms)**")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg", x=summary["vendor"], y=summary["avg_response_ms"],
        text=summary["avg_response_ms"], textposition="outside",
        marker_color="#4C78A8",
    ))
    fig.add_trace(go.Bar(
        name="p95", x=summary["vendor"], y=summary["p95_response_ms"],
        text=summary["p95_response_ms"], textposition="outside",
        marker_color="#F58518", opacity=0.7,
    ))
    fig.update_layout(
        barmode="group", showlegend=True,
        legend=dict(orientation="h", y=1.1),
        yaxis_title="ms", margin=dict(t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Charts — Content Quality ──────────────────────────────────────────────────

st.subheader("Content Quality")
st.caption(
    "HTML scrapers: measured by bytes returned. "
    "Diffbot: measured by clean extracted text length (chars). "
    "Higher = more usable content."
)

col3, col4 = st.columns(2)

with col3:
    st.markdown("**Avg Raw Response Size (KB) — HTML scrapers**")
    html_vendors = summary[~summary["vendor"].isin(
        [v for v, m in VENDOR_META.items() if m["returns_structured"]]
    )]
    if not html_vendors.empty:
        fig = px.bar(
            html_vendors, x="vendor", y="avg_content_kb", color="vendor",
            text="avg_content_kb",
            labels={"avg_content_kb": "Avg Response (KB)", "vendor": "Vendor"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_traces(texttemplate="%{text:.1f} KB", textposition="outside")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No HTML scrapers in current selection.")

with col4:
    st.markdown("**Diffbot: Extracted Text Length (chars)**")
    diffbot_df = df_f[df_f["vendor"] == "Diffbot"].dropna(subset=["parsed_text_length"])
    if not diffbot_df.empty:
        diffbot_by_url = (
            diffbot_df.groupby("url")["parsed_text_length"].mean().reset_index()
        )
        diffbot_by_url["url_short"] = diffbot_by_url["url"].apply(
            lambda u: u.split("/")[-1][:30] or u.split("/")[-2][:30]
        )
        fig = px.bar(
            diffbot_by_url, x="url_short", y="parsed_text_length",
            text="parsed_text_length",
            labels={"parsed_text_length": "Extracted Text (chars)", "url_short": "Target"},
            color_discrete_sequence=["#72B7B2"],
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(margin=dict(t=10, b=40))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Diffbot results in current selection.")

st.divider()

# ── Charts — Cost Analysis ────────────────────────────────────────────────────

st.subheader("Cost Analysis (Paid Tier Projection)")
st.caption("Estimated cost based on paid entry plan rates. Free tier runs cost $0.")

col5, col6 = st.columns(2)

with col5:
    st.markdown("**Credits Consumed (total)**")
    fig = px.pie(
        summary, names="vendor", values="total_credits", hole=0.45,
    )
    fig.update_traces(textinfo="label+percent")
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.markdown("**Estimated Spend if on Paid Tier ($)**")
    cost_summary = summary[summary["total_cost_usd"] > 0]
    if not cost_summary.empty:
        fig = px.bar(
            cost_summary, x="vendor", y="total_cost_usd", color="vendor",
            text="total_cost_usd",
            labels={"total_cost_usd": "Estimated Cost (USD)", "vendor": "Vendor"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_traces(texttemplate="$%{text:.5f}", textposition="outside")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Cost estimation requires paid tier pricing data in vendor metadata.")

st.divider()

# ── Response time distribution ────────────────────────────────────────────────

st.subheader("Response Time Distribution")
fig = px.box(
    df_f, x="vendor", y="response_time_ms", color="vendor", points="all",
    labels={"response_time_ms": "Response Time (ms)", "vendor": "Vendor"},
    color_discrete_sequence=px.colors.qualitative.Safe,
)
fig.update_layout(showlegend=False, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Per-URL success heatmap ───────────────────────────────────────────────────

st.subheader("Success Rate by Vendor × Target URL")
pivot = (
    df_f.groupby(["vendor", "url"])["success_int"]
    .mean()
    .mul(100)
    .round(1)
    .reset_index()
    .pivot(index="url", columns="vendor", values="success_int")
    .fillna(0)
)
if not pivot.empty:
    # Shorten URL labels for readability
    pivot.index = pivot.index.map(
        lambda u: u.replace("https://", "").replace("http://", "")[:55]
    )
    fig = px.imshow(
        pivot, text_auto=True, color_continuous_scale="RdYlGn",
        zmin=0, zmax=100, labels=dict(color="Success %"), aspect="auto",
    )
    fig.update_layout(margin=dict(t=10, b=60), xaxis_tickangle=-20)
    st.plotly_chart(fig, use_container_width=True)

# ── Historical trend ──────────────────────────────────────────────────────────

if data_source == "All runs (historical)" and "timestamp" in df_f.columns:
    st.divider()
    st.subheader("Historical: Avg Response Time per Run")
    df_f["run_date"] = pd.to_datetime(df_f["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
    trend = df_f.groupby(["run_date", "vendor"])["response_time_ms"].mean().reset_index()
    fig = px.line(
        trend, x="run_date", y="response_time_ms", color="vendor", markers=True,
        labels={"response_time_ms": "Avg Response (ms)", "run_date": "Run"},
    )
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

# ── Summary table ─────────────────────────────────────────────────────────────

st.divider()
st.subheader("Summary Table")
st.dataframe(
    summary.rename(columns={
        "vendor": "Vendor",
        "success_rate_pct": "Success %",
        "avg_response_ms": "Avg Resp (ms)",
        "p95_response_ms": "p95 Resp (ms)",
        "total_credits": "Credits Used",
        "total_cost_usd": "Est. Cost (USD)",
        "cost_per_success": "Cost/Success (USD)",
        "total_requests": "Requests",
        "avg_content_kb": "Avg Content (KB)",
    })[[
        "Vendor", "Success %", "Avg Resp (ms)", "p95 Resp (ms)",
        "Requests", "Credits Used", "Est. Cost (USD)", "Cost/Success (USD)", "Avg Content (KB)",
    ]],
    use_container_width=True,
    hide_index=True,
)

with st.expander("Raw results"):
    st.dataframe(df_f, use_container_width=True)

# ── PDF Export ────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Export")

if st.button("Generate PDF report"):
    with st.spinner("Building PDF…"):
        try:
            pdf_bytes = generate_pdf(df_f, summary, VENDOR_META, insights)
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"scraper_insight_{ts}.pdf",
                mime="application/pdf",
            )
        except Exception as exc:
            st.error(f"PDF generation failed: {exc}")
