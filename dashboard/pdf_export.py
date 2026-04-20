"""
PDF report generator for Scraper Insight benchmark results.
Called from the Streamlit dashboard via the "Export PDF" button.
"""

import io
from datetime import datetime, timezone

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

matplotlib.use("Agg")  # non-interactive backend — safe for server use

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm

# ── Colour palette (matches dashboard) ───────────────────────────────────────
COLORS = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2"]
HEADER_BG = colors.HexColor("#1f3a5f")
ROW_ALT = colors.HexColor("#f5f7fa")
GREEN = colors.HexColor("#2ecc71")
RED = colors.HexColor("#e74c3c")
AMBER = colors.HexColor("#f39c12")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _fig_to_image(fig, width_cm: float = 17, max_height_cm: float = 12) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    # Scale to desired width, then clamp height so it never overflows a page frame
    aspect = img.imageHeight / img.imageWidth if img.imageWidth else 1
    draw_w = width_cm * cm
    draw_h = draw_w * aspect
    if draw_h > max_height_cm * cm:
        draw_h = max_height_cm * cm
        draw_w = draw_h / aspect
    img.drawWidth = draw_w
    img.drawHeight = draw_h
    img.hAlign = "CENTER"
    return img


def _bar_chart(labels, values, title: str, ylabel: str, color="#4C78A8") -> Image:
    fig, ax = plt.subplots(figsize=(9, 3.5))
    bars = ax.bar(labels, values, color=COLORS[: len(labels)], edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel("")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    return _fig_to_image(fig)


def _grouped_bar_chart(summary: pd.DataFrame) -> Image:
    vendors = summary["vendor"].tolist()
    x = range(len(vendors))
    fig, ax = plt.subplots(figsize=(9, 3.5))
    w = 0.35
    bars1 = ax.bar([i - w / 2 for i in x], summary["avg_response_ms"], w,
                   label="Avg", color="#4C78A8")
    bars2 = ax.bar([i + w / 2 for i in x], summary["p95_response_ms"], w,
                   label="p95", color="#F58518", alpha=0.8)
    ax.bar_label(bars1, fmt="%.0f", padding=2, fontsize=7)
    ax.bar_label(bars2, fmt="%.0f", padding=2, fontsize=7)
    ax.set_title("Avg vs p95 Response Time (ms)", fontsize=11, fontweight="bold", pad=8)
    ax.set_ylabel("ms", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(vendors, fontsize=8)
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_image(fig)


def _heatmap_chart(df: pd.DataFrame) -> Image | None:
    pivot = (
        df.groupby(["vendor", "url"])["success_int"]
        .mean()
        .mul(100)
        .round(1)
        .reset_index()
        .pivot(index="url", columns="vendor", values="success_int")
        .fillna(0)
    )
    if pivot.empty:
        return None
    pivot.index = pivot.index.map(
        lambda u: u.replace("https://", "").replace("http://", "")[:50]
    )
    fig, ax = plt.subplots(figsize=(10, min(10, max(3, len(pivot) * 0.55))))
    im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=7)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.values[i, j]:.0f}%", ha="center", va="center", fontsize=7,
                    color="black" if 20 < pivot.values[i, j] < 80 else "white")
    plt.colorbar(im, ax=ax, label="Success %", shrink=0.8)
    ax.set_title("Success Rate by Vendor × Target URL", fontsize=11, fontweight="bold", pad=8)
    fig.tight_layout()
    return _fig_to_image(fig)


# ── Table helpers ─────────────────────────────────────────────────────────────

def _styled_table(data: list[list], col_widths=None) -> Table:
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t


# ── Main export function ──────────────────────────────────────────────────────

def generate_pdf(
    df: pd.DataFrame,
    summary: pd.DataFrame,
    vendor_meta: dict,
    insights: list[tuple],
) -> bytes:
    """
    Build a PDF report and return it as bytes.

    Args:
        df:          Full filtered results dataframe.
        summary:     Per-vendor aggregated summary dataframe.
        vendor_meta: VENDOR_META dict from app.py.
        insights:    List of (tag, title, body) tuples from app.py.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=20, spaceAfter=4,
                         textColor=colors.HexColor("#1f3a5f"), alignment=TA_CENTER)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=14,
                         spaceAfter=6, textColor=colors.HexColor("#1f3a5f"))
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=8.5, leading=13,
                           spaceAfter=4)
    caption = ParagraphStyle("caption", parent=styles["Normal"], fontSize=7.5,
                              textColor=colors.HexColor("#666666"), spaceAfter=8,
                              alignment=TA_CENTER)
    insight_good = ParagraphStyle("insight_good", parent=styles["Normal"], fontSize=8.5,
                                   leading=13, spaceAfter=6, leftIndent=10,
                                   textColor=colors.HexColor("#1a6e2e"))
    insight_warn = ParagraphStyle("insight_warn", parent=styles["Normal"], fontSize=8.5,
                                   leading=13, spaceAfter=6, leftIndent=10,
                                   textColor=colors.HexColor("#7a3c00"))
    insight_info = ParagraphStyle("insight_info", parent=styles["Normal"], fontSize=8.5,
                                   leading=13, spaceAfter=6, leftIndent=10,
                                   textColor=colors.HexColor("#1a3a6e"))

    story = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("🕷️ Scraper Insight", h1))
    story.append(Paragraph("Web Scraping API Benchmark Report", h1))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"Generated: {now}", caption))
    story.append(Paragraph(
        f"Vendors: {', '.join(sorted(df['vendor'].unique()))} &nbsp;|&nbsp; "
        f"Targets: {df['url'].nunique()} &nbsp;|&nbsp; "
        f"Total requests: {len(df)}",
        caption,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1f3a5f")))
    story.append(Spacer(1, 0.6 * cm))

    # ── Section 1: Pricing ───────────────────────────────────────────────────
    story.append(Paragraph("1. Pricing & Free Tier Comparison", h2))

    pricing_header = [
        "Vendor", "Free Tier\n(req/mo)", "Paid Entry\n($/mo)",
        "Paid Credits", "Cost/Credit\n(paid)", "JS", "Proxy", "Structured",
    ]
    pricing_rows = [pricing_header]
    for vendor, m in vendor_meta.items():
        pricing_rows.append([
            vendor,
            f"{m['free_tier_limit']:,}",
            f"${m['paid_entry_usd']:.2f}" if m["paid_entry_usd"] > 0 else "—",
            f"{m['paid_entry_credits']:,}" if m["paid_entry_credits"] > 0 else "—",
            f"${m['usd_per_credit']:.6f}" if m["usd_per_credit"] > 0 else "—",
            "✓" if m["supports_js"] else "✗",
            "✓" if m["supports_proxy"] else "✗",
            "✓" if m["returns_structured"] else "✗",
        ])

    col_w = [3.2*cm, 2*cm, 2.2*cm, 2.4*cm, 2.4*cm, 1.2*cm, 1.2*cm, 2*cm]
    story.append(_styled_table(pricing_rows, col_widths=col_w))
    story.append(Spacer(1, 0.4 * cm))

    # ── Section 2: Smart Insights ────────────────────────────────────────────
    story.append(Paragraph("2. Smart Insights", h2))
    for tag, title, body_text in insights:
        clean = body_text.replace("**", "").replace("  \n", " ")
        style = insight_warn if tag == "warn" else (
            insight_good if tag in ("success", "diffbot") else insight_info
        )
        prefix = "⚠" if tag == "warn" else ("✓" if tag in ("success", "diffbot") else "→")
        story.append(Paragraph(f"{prefix}  <b>{title}:</b>  {clean}", style))

    story.append(Spacer(1, 0.3 * cm))

    # ── Section 3: Performance Summary Table ─────────────────────────────────
    story.append(Paragraph("3. Performance Summary", h2))

    perf_header = [
        "Vendor", "Success %", "Avg Resp\n(ms)", "p95 Resp\n(ms)",
        "Requests", "Credits\nUsed", "Est. Cost\n(USD)", "Avg Content\n(KB)",
    ]
    perf_rows = [perf_header]
    for _, row in summary.iterrows():
        perf_rows.append([
            row["vendor"],
            f"{row['success_rate_pct']}%",
            f"{row['avg_response_ms']}",
            f"{row['p95_response_ms']}",
            f"{row['total_requests']}",
            f"{row['total_credits']:.1f}",
            f"${row['total_cost_usd']:.5f}",
            f"{row['avg_content_kb']:.1f}",
        ])

    col_w2 = [3.2*cm, 1.8*cm, 2*cm, 2*cm, 1.8*cm, 2*cm, 2.4*cm, 2.4*cm]
    story.append(_styled_table(perf_rows, col_widths=col_w2))
    story.append(Spacer(1, 0.4 * cm))

    # ── Section 4: Charts ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Performance Charts", h2))

    story.append(_bar_chart(
        summary["vendor"].tolist(),
        summary["success_rate_pct"].tolist(),
        "Success Rate by Vendor (%)", "%",
    ))
    story.append(Paragraph("Higher is better. Tier-3 targets with proxy/JS are harder to pass.", caption))
    story.append(Spacer(1, 0.4 * cm))

    story.append(_grouped_bar_chart(summary))
    story.append(Paragraph("Lower is better. p95 shows worst-case latency — important for pipelines.", caption))
    story.append(Spacer(1, 0.4 * cm))

    story.append(_bar_chart(
        summary["vendor"].tolist(),
        summary["avg_content_kb"].tolist(),
        "Avg Content Returned per Request (KB)", "KB",
    ))
    story.append(Paragraph(
        "HTML scrapers only. Higher KB = more complete page content returned. "
        "Diffbot returns structured JSON so byte count is not directly comparable.",
        caption,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # ── Section 5: Per-URL Heatmap ────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5. Success Rate by Vendor × Target URL", h2))
    heatmap = _heatmap_chart(df)
    if heatmap:
        story.append(heatmap)
        story.append(Paragraph(
            "Green = 100% success, Red = 0%. Reveals which vendors struggle on specific targets.", caption
        ))

    # ── Diffbot quality section (if present) ─────────────────────────────────
    diffbot_df = df[df["vendor"] == "Diffbot"].dropna(subset=["parsed_text_length"])
    if not diffbot_df.empty:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("6. Diffbot — Structured Extraction Quality", h2))
        story.append(Paragraph(
            "Diffbot is the only AI-extraction vendor in this benchmark. "
            "It returns structured JSON (title, body text, author, images) instead of raw HTML.",
            body,
        ))

        dt_by_url = (
            diffbot_df.groupby("url")
            .agg(avg_text=("parsed_text_length", "mean"), avg_fields=("parsed_fields", "mean"))
            .reset_index()
        )
        dt_header = ["Target URL", "Avg Extracted Text (chars)", "Avg Structured Fields"]
        dt_rows = [dt_header] + [
            [
                r["url"].replace("https://", "")[:55],
                f"{r['avg_text']:.0f}",
                f"{r['avg_fields']:.0f}",
            ]
            for _, r in dt_by_url.iterrows()
        ]
        story.append(_styled_table(dt_rows, col_widths=[9*cm, 4.5*cm, 4.5*cm]))

    doc.build(story)
    buf.seek(0)
    return buf.read()
