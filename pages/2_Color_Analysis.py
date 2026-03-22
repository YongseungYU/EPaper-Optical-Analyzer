"""색상 분석 페이지 - E-paper Optical Analyzer."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ensure project root is on sys.path for imports
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.color_utils import lab_to_hex, get_color_name

# ── 페이지 설정 ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="색상 분석", page_icon="🎨", layout="wide")

# ── 고급 모드 체크 ──────────────────────────────────────────────────────────

if st.session_state.get('app_mode') != 'advanced':
    st.warning("이 페이지는 고급 모드에서만 사용할 수 있습니다. 홈에서 고급 모드를 선택해 주세요.")
    st.stop()

st.title("🎨 색상 분석")
st.markdown("측정된 L\\*a\\*b\\* 데이터를 기반으로 색상을 시각화하고 분석합니다.")

# ── 데이터 소스 선택 (현재 / 누적) ──────────────────────────────────────────

data_source = "현재 데이터"
has_cumulative = st.session_state.get("cumulative_data") is not None

if has_cumulative:
    data_source = st.selectbox(
        "분석 데이터 선택",
        options=["현재 데이터", "누적 데이터"],
        index=0,
        help="누적 데이터를 선택하면 이전에 업로드한 데이터를 합산하여 분석합니다.",
    )

# ── 데이터 확인 ─────────────────────────────────────────────────────────────

is_cumulative = data_source == "누적 데이터"

if is_cumulative:
    df: pd.DataFrame = st.session_state["cumulative_data"]
    st.info("📂 누적 데이터를 사용하여 분석합니다.")
else:
    if "measurement_data" not in st.session_state or st.session_state["measurement_data"] is None:
        st.warning("⚠️ 측정 데이터가 없습니다. 먼저 **Data Upload** 페이지에서 데이터를 업로드해 주세요.")
        st.stop()
    df = st.session_state["measurement_data"]

# Validate required columns
required_cols = ["LAB_L", "LAB_A", "LAB_B"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"필수 컬럼이 누락되었습니다: {missing}")
    st.stop()

# Determine name column
name_col = "SAMPLE_NAME" if "SAMPLE_NAME" in df.columns else (
    "SAMPLE_ID" if "SAMPLE_ID" in df.columns else None
)

has_source_col = "SOURCE_FILE" in df.columns

# ── 색상 데이터 준비 ────────────────────────────────────────────────────────

color_data = []
# Build a mapping from SOURCE_FILE to display label (데이터 1, 데이터 2, ...)
source_label_map = {}
if is_cumulative and has_source_col:
    unique_sources = df["SOURCE_FILE"].unique().tolist()
    for si, src in enumerate(unique_sources):
        source_label_map[src] = f"데이터 {si + 1}"

for idx, row in df.iterrows():
    L, a, b = float(row["LAB_L"]), float(row["LAB_A"]), float(row["LAB_B"])
    sample_name = str(row[name_col]) if name_col else f"Sample {idx + 1}"
    hex_color = lab_to_hex(L, a, b)
    nearest_color = get_color_name(L, a, b)
    source_file = str(row["SOURCE_FILE"]) if has_source_col else None
    source_label = source_label_map.get(source_file, source_file) if source_file else None
    color_data.append({
        "name": sample_name,
        "L": L, "a": a, "b": b,
        "hex": hex_color,
        "nearest": nearest_color,
        "source_file": source_file,
        "source_label": source_label,
    })

# ── 섹션 1: 색상 패치 및 상세 정보 ──────────────────────────────────────────

st.header("📋 측정 색상 목록")

if is_cumulative and has_source_col:
    # Group color patches by data source
    from collections import OrderedDict
    source_groups: dict[str, list] = OrderedDict()
    for cd in color_data:
        label = cd["source_label"] or "기타"
        source_groups.setdefault(label, []).append(cd)

    for source_label, group_items in source_groups.items():
        st.subheader(f"📁 {source_label}")
        cols_per_row = 3
        for i in range(0, len(group_items), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(group_items):
                    cd = group_items[i + j]
                    with col:
                        text_color = "#FFFFFF" if cd["L"] < 50 else "#000000"
                        st.markdown(
                            f"""
                            <div style="
                                background-color: {cd['hex']};
                                border: 2px solid #ccc;
                                border-radius: 10px;
                                padding: 20px;
                                text-align: center;
                                margin-bottom: 10px;
                                min-height: 100px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            ">
                                <span style="color: {text_color}; font-size: 18px; font-weight: bold;">
                                    {cd['name']}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**식별 색상:** {cd['nearest']}")
                        st.markdown(
                            f"- **L\\*** = {cd['L']:.2f}  \n"
                            f"- **a\\*** = {cd['a']:.2f}  \n"
                            f"- **b\\*** = {cd['b']:.2f}"
                        )
                        st.markdown(f"HEX: `{cd['hex']}`")
                        st.divider()
else:
    # Non-cumulative: original layout
    cols_per_row = 3
    for i in range(0, len(color_data), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(color_data):
                cd = color_data[i + j]
                with col:
                    text_color = "#FFFFFF" if cd["L"] < 50 else "#000000"
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {cd['hex']};
                            border: 2px solid #ccc;
                            border-radius: 10px;
                            padding: 20px;
                            text-align: center;
                            margin-bottom: 10px;
                            min-height: 100px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <span style="color: {text_color}; font-size: 18px; font-weight: bold;">
                                {cd['name']}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**식별 색상:** {cd['nearest']}")
                    st.markdown(
                        f"- **L\\*** = {cd['L']:.2f}  \n"
                        f"- **a\\*** = {cd['a']:.2f}  \n"
                        f"- **b\\*** = {cd['b']:.2f}"
                    )
                    st.markdown(f"HEX: `{cd['hex']}`")
                    st.divider()

# ── 섹션 2: a*b* 색도 다이어그램 ─────────────────────────────────────────────

st.header("🔵 a*b* 색도 다이어그램")

fig_ab = go.Figure()

# Plot measured points
for cd in color_data:
    legend_name = cd["name"]
    if is_cumulative and cd.get("source_label"):
        legend_name = f"{cd['source_label']} - {cd['name']}"
    fig_ab.add_trace(go.Scatter(
        x=[cd["a"]],
        y=[cd["b"]],
        mode="markers+text",
        marker=dict(
            size=16,
            color=cd["hex"],
            line=dict(width=2, color="#333333"),
        ),
        text=[legend_name],
        textposition="top center",
        textfont=dict(size=11),
        name=legend_name,
        hovertemplate=(
            f"<b>{legend_name}</b><br>"
            f"a* = {cd['a']:.2f}<br>"
            f"b* = {cd['b']:.2f}<br>"
            f"L* = {cd['L']:.2f}"
            "<extra></extra>"
        ),
    ))

# Plot reference color markers (if reference data exists in session)
if "reference_colors" in st.session_state and st.session_state["reference_colors"]:
    ref_data = st.session_state["reference_colors"]
    for ref_name, ref_lab in ref_data.items():
        rL, ra, rb = ref_lab
        ref_hex = lab_to_hex(rL, ra, rb)
        fig_ab.add_trace(go.Scatter(
            x=[ra],
            y=[rb],
            mode="markers",
            marker=dict(
                size=12,
                color=ref_hex,
                symbol="diamond",
                line=dict(width=2, color="#999999"),
            ),
            name=f"기준: {ref_name}",
            hovertemplate=(
                f"<b>기준: {ref_name}</b><br>"
                f"a* = {ra:.2f}<br>"
                f"b* = {rb:.2f}<br>"
                f"L* = {rL:.2f}"
                "<extra></extra>"
            ),
        ))

# Add axis lines
fig_ab.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig_ab.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

fig_ab.update_layout(
    title="a*b* 색도 다이어그램",
    xaxis_title="a* (녹색 ← → 빨강)",
    yaxis_title="b* (파랑 ← → 노랑)",
    xaxis=dict(zeroline=True, range=[-128, 128]),
    yaxis=dict(zeroline=True, range=[-128, 128], scaleanchor="x", scaleratio=1),
    height=650,
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=-0.2),
)

st.plotly_chart(fig_ab, use_container_width=True)

# ── 섹션 3: L* 명도 바 차트 ─────────────────────────────────────────────────

st.header("📊 L* 명도 분포")

fig_L = go.Figure()

if is_cumulative and has_source_col:
    # Grouped bar chart: X = color names, groups = data source
    import plotly.express as px

    # Build DataFrame for grouped chart
    chart_rows = []
    for cd in color_data:
        chart_rows.append({
            "색상명": cd["name"],
            "L*": cd["L"],
            "데이터": cd["source_label"] or "기타",
            "hex": cd["hex"],
        })
    chart_df = pd.DataFrame(chart_rows)

    # Get unique source labels for color assignment
    unique_sources = chart_df["데이터"].unique().tolist()
    # Use a qualitative color palette
    source_colors = px.colors.qualitative.Set2[:len(unique_sources)]
    color_map = dict(zip(unique_sources, source_colors))

    for src_label in unique_sources:
        src_data = chart_df[chart_df["데이터"] == src_label]
        fig_L.add_trace(go.Bar(
            x=src_data["색상명"],
            y=src_data["L*"],
            name=src_label,
            marker=dict(
                color=color_map[src_label],
                line=dict(width=1, color="#333333"),
            ),
            text=[f"{v:.1f}" for v in src_data["L*"]],
            textposition="inside",
            textfont=dict(size=12),
            hovertemplate="<b>%{x}</b><br>L* = %{y:.2f}<br>" + src_label + "<extra></extra>",
        ))

    fig_L.update_layout(barmode="group")
else:
    names = [cd["name"] for cd in color_data]
    L_values = [cd["L"] for cd in color_data]
    bar_colors = [cd["hex"] for cd in color_data]
    text_colors = ["#FFFFFF" if cd["L"] < 50 else "#000000" for cd in color_data]

    fig_L.add_trace(go.Bar(
        x=names,
        y=L_values,
        marker=dict(
            color=bar_colors,
            line=dict(width=1, color="#333333"),
        ),
        text=[f"{v:.1f}" for v in L_values],
        textposition="inside",
        textfont=dict(color=text_colors, size=14),
        hovertemplate="<b>%{x}</b><br>L* = %{y:.2f}<extra></extra>",
    ))

fig_L.update_layout(
    title="샘플별 L* (명도) 값",
    xaxis_title="샘플",
    yaxis_title="L* (0=검정, 100=흰색)",
    yaxis=dict(range=[0, 105]),
    height=450,
    showlegend=is_cumulative and has_source_col,
)

st.plotly_chart(fig_L, use_container_width=True)

# ── 섹션 4: 요약 테이블 ─────────────────────────────────────────────────────

st.header("📝 색상 분석 요약")

if is_cumulative and has_source_col:
    summary_df = pd.DataFrame([
        {
            "데이터": cd["source_label"] or "기타",
            "샘플명": cd["name"],
            "L*": round(cd["L"], 2),
            "a*": round(cd["a"], 2),
            "b*": round(cd["b"], 2),
            "식별 색상": cd["nearest"],
            "HEX": cd["hex"],
        }
        for cd in color_data
    ])
else:
    summary_df = pd.DataFrame([
        {
            "샘플명": cd["name"],
            "L*": round(cd["L"], 2),
            "a*": round(cd["a"], 2),
            "b*": round(cd["b"], 2),
            "식별 색상": cd["nearest"],
            "HEX": cd["hex"],
        }
        for cd in color_data
    ])

st.dataframe(summary_df, use_container_width=True, hide_index=True)
