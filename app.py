import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Lifecycle Upgrade Dashboard", page_icon="📊", layout="wide")

STARBUCKS_GREEN = "#006241"
STARBUCKS_DARK_GREEN = "#1E3932"
STARBUCKS_GOLD = "#CBA258"
STARBUCKS_CREAM = "#F7F4ED"
STARBUCKS_TEXT = "#1F2933"
STARBUCKS_LOGO_URL = "https://upload.wikimedia.org/wikipedia/en/d/d3/Starbucks_Corporation_Logo_2011.svg"

DEFAULT_FILE_CANDIDATES = [
    Path("data") / "Lifecycle_upgrade.xlsx",
    Path(r"C:\Users\PSP1001461\Downloads\Lifecycle_upgrade.xlsx"),
]
EXPECTED_COLUMNS = [
    "Track",
    "Applications",
    "Assigned Resources",
    "Total # of Test Scenarios",
    "Completed # of Scenarios",
    "Completion %",
    "Blocked Scenarios",
    "Comments",
]


def build_pdf_report(
    filtered: pd.DataFrame,
    app_progress: pd.DataFrame,
    comments_df: pd.DataFrame,
    total_apps: int,
    total_scenarios: int,
    completed: int,
    blocked: int,
    overall_completion: float,
) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    pdf.setFillColorRGB(0.0, 0.384, 0.255)
    pdf.rect(0, y - 25, width, 40, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(36, y - 10, "Starbucks | Lifecycle Upgrade Executive Report")
    y -= 50

    pdf.setFillColorRGB(0.12, 0.22, 0.20)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(36, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 20

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, y, "KPI Summary")
    y -= 16
    pdf.setFont("Helvetica", 10)
    kpi_lines = [
        f"Applications: {total_apps}",
        f"Total Scenarios: {total_scenarios:,}",
        f"Completed: {completed:,}",
        f"Blocked: {blocked:,}",
        f"Overall Completion: {overall_completion:.1%}",
    ]
    for line in kpi_lines:
        pdf.drawString(46, y, line)
        y -= 14

    y -= 6
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, y, "Top Application Progress")
    y -= 16
    pdf.setFont("Helvetica", 9)
    top_apps = app_progress.sort_values("Completion %", ascending=False).head(10)
    for _, row in top_apps.iterrows():
        line = (
            f"{row['Track']} | {row['Applications']} | "
            f"Done {int(row['Completed # of Scenarios'])}/{int(row['Total # of Test Scenarios'])} "
            f"({row['Completion %']:.0%})"
        )
        pdf.drawString(46, y, line[:105])
        y -= 12
        if y < 90:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 9)

    y -= 8
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(36, y, "Open Risks / Comments")
    y -= 16
    pdf.setFont("Helvetica", 9)
    if comments_df.empty:
        pdf.drawString(46, y, "No open comments for selected filters.")
    else:
        for _, row in comments_df.head(8).iterrows():
            detail = f"{row['Track']} | {row['Applications']} | Blocked: {int(row['Blocked Scenarios'])} | {row['Comments']}"
            pdf.drawString(46, y, detail[:105])
            y -= 12
            if y < 70:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 9)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


@st.cache_data
def load_data(file_bytes: bytes | None, default_file: Path | None) -> pd.DataFrame:
    if file_bytes is not None:
        source = io.BytesIO(file_bytes)
    else:
        if default_file is None:
            raise FileNotFoundError(
                "Default file not found. Upload an Excel file from the sidebar."
            )
        source = default_file

    df = pd.read_excel(source, sheet_name=0)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    cleaned = df[EXPECTED_COLUMNS].copy()
    cleaned["Track"] = cleaned["Track"].ffill()
    cleaned["Assigned Resources"] = cleaned["Assigned Resources"].ffill()

    for col in [
        "Total # of Test Scenarios",
        "Completed # of Scenarios",
        "Completion %",
        "Blocked Scenarios",
    ]:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    cleaned["Completion %"] = cleaned["Completion %"].where(cleaned["Completion %"] <= 1, cleaned["Completion %"] / 100)
    cleaned["Total # of Test Scenarios"] = cleaned["Total # of Test Scenarios"].fillna(0)
    cleaned["Completed # of Scenarios"] = cleaned["Completed # of Scenarios"].fillna(0)
    cleaned["Blocked Scenarios"] = cleaned["Blocked Scenarios"].fillna(0)
    cleaned["Comments"] = cleaned["Comments"].fillna("")
    cleaned["Applications"] = cleaned["Applications"].fillna("Unknown")

    cleaned["Remaining Scenarios"] = (
        cleaned["Total # of Test Scenarios"] - cleaned["Completed # of Scenarios"]
    ).clip(lower=0)
    return cleaned


st.markdown(
    f"""
    <style>
      .stApp {{
        background-color: {STARBUCKS_CREAM};
        color: {STARBUCKS_TEXT};
      }}
      .main h1, .main h2, .main h3 {{
        letter-spacing: 0.2px;
        color: {STARBUCKS_DARK_GREEN};
      }}
      [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {STARBUCKS_DARK_GREEN} 0%, {STARBUCKS_GREEN} 100%);
      }}
      [data-testid="stSidebar"] * {{
        color: white;
      }}
      [data-testid="stFileUploaderDropzone"] {{
        border: 1px solid rgba(255, 255, 255, 0.75);
        background-color: rgba(255, 255, 255, 0.08);
      }}
      [data-testid="stFileUploaderDropzone"] span {{
        color: white;
      }}
      [data-testid="stFileUploaderDropzone"] button {{
        background-color: {STARBUCKS_GOLD} !important;
        color: {STARBUCKS_DARK_GREEN} !important;
        border: 1px solid {STARBUCKS_GOLD} !important;
        font-weight: 600 !important;
      }}
      .default-path {{
        background: rgba(255, 255, 255, 0.94);
        color: {STARBUCKS_DARK_GREEN};
        border-left: 4px solid {STARBUCKS_GOLD};
        border-radius: 0.45rem;
        padding: 0.55rem 0.65rem;
        margin-top: 0.35rem;
      }}
      .default-path code {{
        color: {STARBUCKS_DARK_GREEN};
      }}
      [data-testid="stMetricValue"] {{
        color: {STARBUCKS_GREEN};
      }}
      .dashboard-banner {{
        border-left: 6px solid {STARBUCKS_GREEN};
        background: white;
        padding: 0.8rem 1rem;
        border-radius: 0.6rem;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
        margin-bottom: 0.8rem;
      }}
      .dashboard-banner h4 {{
        margin: 0;
        color: {STARBUCKS_DARK_GREEN};
      }}
      .dashboard-banner p {{
        margin: 0.3rem 0 0 0;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Lifecycle Upgrade Program Dashboard")
st.caption("Interactive reporting dashboard for testing progress, blockers, and execution health.")
logo_col, title_col = st.columns([1, 7])
with logo_col:
    st.image(STARBUCKS_LOGO_URL, width=90)
with title_col:
    st.markdown("### Starbucks Program Reporting")
st.markdown(
    """
    <div class="dashboard-banner">
      <h4>Starbucks Leadership View</h4>
      <p>Program execution metrics aligned for executive reporting and publishing.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Starbucks Reporting Controls")
    uploaded = st.file_uploader("Upload Lifecycle Excel file", type=["xlsx", "xls"])
    default_file = next((p for p in DEFAULT_FILE_CANDIDATES if p.exists()), None)
    if default_file is not None:
        st.markdown(
            f'<div class="default-path"><strong>Default file path</strong><br><code>{default_file}</code></div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Default file not found. Please upload your file.")

try:
    file_bytes = uploaded.getvalue() if uploaded else None
    df = load_data(file_bytes, default_file)
except Exception as exc:
    st.error(str(exc))
    st.stop()

tracks = sorted(df["Track"].dropna().unique())
resources = sorted(df["Assigned Resources"].dropna().unique())
selected_tracks = st.sidebar.multiselect("Filter by Track", tracks, default=tracks)
selected_resources = st.sidebar.multiselect(
    "Filter by Resource", resources, default=resources
)

filtered = df[df["Track"].isin(selected_tracks) & df["Assigned Resources"].isin(selected_resources)].copy()

total_apps = filtered["Applications"].nunique()
total_scenarios = int(filtered["Total # of Test Scenarios"].sum())
completed = int(filtered["Completed # of Scenarios"].sum())
blocked = int(filtered["Blocked Scenarios"].sum())
overall_completion = (completed / total_scenarios) if total_scenarios else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Applications", f"{total_apps}")
c2.metric("Total Scenarios", f"{total_scenarios:,}")
c3.metric("Completed", f"{completed:,}")
c4.metric("Blocked", f"{blocked:,}")
c5.metric("Overall Completion", f"{overall_completion:.1%}")

app_progress = (
    filtered.groupby(["Track", "Applications"], as_index=False)[
        ["Total # of Test Scenarios", "Completed # of Scenarios", "Blocked Scenarios"]
    ]
    .sum()
)
app_progress["Completion %"] = app_progress["Completed # of Scenarios"] / app_progress["Total # of Test Scenarios"].replace(0, pd.NA)
app_progress["Completion %"] = app_progress["Completion %"].fillna(0)

track_progress = (
    filtered.groupby("Track", as_index=False)[
        ["Total # of Test Scenarios", "Completed # of Scenarios", "Remaining Scenarios"]
    ]
    .sum()
)
track_progress_melt = track_progress.melt(
    id_vars="Track",
    value_vars=["Completed # of Scenarios", "Remaining Scenarios"],
    var_name="Status",
    value_name="Scenarios",
)

resource_workload = (
    filtered.groupby("Assigned Resources", as_index=False)[
        ["Total # of Test Scenarios", "Completed # of Scenarios"]
    ]
    .sum()
)
resource_workload["Completion %"] = (
    resource_workload["Completed # of Scenarios"]
    / resource_workload["Total # of Test Scenarios"].replace(0, pd.NA)
).fillna(0)

left, right = st.columns([1.2, 1])
with left:
    fig_app = px.bar(
        app_progress.sort_values("Completion %", ascending=False),
        x="Applications",
        y="Completion %",
        color="Track",
        text=app_progress.sort_values("Completion %", ascending=False)["Completion %"].map(lambda x: f"{x:.0%}"),
        title="Application Completion Rate",
        color_discrete_sequence=[STARBUCKS_GREEN, STARBUCKS_DARK_GREEN, STARBUCKS_GOLD],
    )
    fig_app.update_layout(
        yaxis_tickformat=".0%",
        xaxis_title="",
        yaxis_title="Completion %",
        legend_title="Track",
        paper_bgcolor="white",
        plot_bgcolor="white",
        title_font_color=STARBUCKS_DARK_GREEN,
    )
    st.plotly_chart(fig_app, use_container_width=True)

with right:
    fig_track = px.bar(
        track_progress_melt,
        x="Track",
        y="Scenarios",
        color="Status",
        barmode="stack",
        title="Completed vs Remaining by Track",
        color_discrete_map={
            "Completed # of Scenarios": STARBUCKS_GREEN,
            "Remaining Scenarios": STARBUCKS_GOLD,
        },
    )
    fig_track.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        title_font_color=STARBUCKS_DARK_GREEN,
    )
    st.plotly_chart(fig_track, use_container_width=True)

fig_resource = px.scatter(
    resource_workload,
    x="Total # of Test Scenarios",
    y="Completion %",
    size="Completed # of Scenarios",
    color="Assigned Resources",
    title="Resource Workload & Delivery Performance",
    labels={"Completion %": "Completion %"},
    color_discrete_sequence=[STARBUCKS_GREEN, STARBUCKS_DARK_GREEN, STARBUCKS_GOLD],
)
fig_resource.update_layout(
    yaxis_tickformat=".0%",
    paper_bgcolor="white",
    plot_bgcolor="white",
    title_font_color=STARBUCKS_DARK_GREEN,
)
st.plotly_chart(fig_resource, use_container_width=True)

st.subheader("Detailed Report")
display_df = app_progress.copy()
display_df["Completion %"] = display_df["Completion %"].map(lambda x: round(float(x) * 100, 2))
st.dataframe(
    display_df,
    use_container_width=True,
    column_config={
        "Completion %": st.column_config.ProgressColumn(
            "Completion %",
            format="%.1f%%",
            min_value=0.0,
            max_value=100.0,
        )
    },
)

st.subheader("Open Risks / Comments")
comments_df = filtered[filtered["Comments"].str.len() > 0][
    ["Track", "Applications", "Blocked Scenarios", "Comments"]
]

pdf_bytes = build_pdf_report(
    filtered=filtered,
    app_progress=app_progress,
    comments_df=comments_df,
    total_apps=total_apps,
    total_scenarios=total_scenarios,
    completed=completed,
    blocked=blocked,
    overall_completion=overall_completion,
)
st.sidebar.download_button(
    label="One-Click PDF Export",
    data=pdf_bytes,
    file_name=f"starbucks_lifecycle_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf",
    use_container_width=True,
)

if comments_df.empty:
    st.success("No open comments for the selected filters.")
else:
    st.dataframe(comments_df, use_container_width=True)
