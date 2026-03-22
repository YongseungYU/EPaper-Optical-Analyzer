"""
그래프 및 시각화 페이지.

측정 데이터를 다양한 Plotly 차트로 시각화합니다.
- a*b* 색도 다이어그램
- L* 비교 차트
- Color Gamut 분석
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from core.color_utils import lab_to_hex, calculate_gamut_area, calculate_gamut_volume

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="그래프 및 시각화 - E-paper Optical Analyzer",
    page_icon="📈",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 고급 모드 체크
# ---------------------------------------------------------------------------

if st.session_state.get('app_mode') != 'advanced':
    st.warning("이 페이지는 고급 모드에서만 사용할 수 있습니다. 홈에서 고급 모드를 선택해 주세요.")
    st.stop()

# ---------------------------------------------------------------------------
# 공통 스타일
# ---------------------------------------------------------------------------

_PLOT_FONT = dict(family="Malgun Gothic, NanumGothic, sans-serif", size=13)
_PLOT_TEMPLATE = "plotly_white"


def _common_layout(**kwargs) -> dict:
    """모든 차트에 적용할 공통 레이아웃 설정을 반환합니다."""
    base = dict(
        font=_PLOT_FONT,
        template=_PLOT_TEMPLATE,
        margin=dict(l=60, r=30, t=50, b=50),
    )
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# 데이터 확인
# ---------------------------------------------------------------------------

st.title("그래프 및 시각화")
st.markdown("측정 데이터를 인터랙티브 차트로 시각화합니다.")
st.divider()

# ---------------------------------------------------------------------------
# 데이터 소스 선택 (현재 데이터 vs 누적 데이터)
# ---------------------------------------------------------------------------

data_source = st.selectbox(
    "데이터 소스 선택",
    ["현재 데이터", "누적 데이터"],
    index=0,
)

if data_source == "누적 데이터":
    cumulative = st.session_state.get("cumulative_data")
    if cumulative is None or (isinstance(cumulative, pd.DataFrame) and cumulative.empty):
        st.warning("누적 데이터가 없습니다. 현재 데이터를 사용합니다.")
        data_source = "현재 데이터"
    elif isinstance(cumulative, list) and len(cumulative) == 0:
        st.warning("누적 데이터가 없습니다. 현재 데이터를 사용합니다.")
        data_source = "현재 데이터"

if data_source == "현재 데이터":
    if "measurement_data" not in st.session_state or st.session_state["measurement_data"] is None:
        st.warning("측정 데이터가 없습니다. 먼저 데이터를 업로드해 주세요.")
        st.stop()
    df: pd.DataFrame = st.session_state["measurement_data"]
    # 현재 데이터는 단일 소스이므로 data_frames 리스트로 통일
    data_frames: list[tuple[str, pd.DataFrame]] = [("현재 데이터", df)]
else:
    cumulative = st.session_state.get("cumulative_data")
    if isinstance(cumulative, pd.DataFrame):
        df = cumulative
        data_frames = [("누적 데이터", df)]
    elif isinstance(cumulative, list):
        df = pd.concat(cumulative, ignore_index=True)
        data_frames = [(f"데이터 {i + 1}", sub_df) for i, sub_df in enumerate(cumulative)]
    else:
        st.error("누적 데이터 형식을 인식할 수 없습니다.")
        st.stop()

# L*a*b* 컬럼 존재 확인
_REQUIRED_COLS = ["LAB_L", "LAB_A", "LAB_B"]
if not all(c in df.columns for c in _REQUIRED_COLS):
    st.error("데이터에 L*a*b* 컬럼(LAB_L, LAB_A, LAB_B)이 없습니다.")
    st.stop()

# 샘플 이름 결정
if "SAMPLE_NAME" in df.columns:
    sample_names = df["SAMPLE_NAME"].astype(str).tolist()
else:
    sample_names = [f"샘플 {i + 1}" for i in range(len(df))]

# 각 포인트의 hex 색상 계산
hex_colors = [
    lab_to_hex(row["LAB_L"], row["LAB_A"], row["LAB_B"])
    for _, row in df.iterrows()
]

# =========================================================================
# 1. a*b* 색도 다이어그램
# =========================================================================

st.header("1. a*b* 색도 다이어그램")
st.caption("a*-b* 평면 위에 측정 색상을 표시합니다. 기준 색상은 다이아몬드(◆)로 표시됩니다.")

fig_ab = go.Figure()

# 기준선 (a*=0, b*=0)
a_range = [df["LAB_A"].min() - 10, df["LAB_A"].max() + 10]
b_range = [df["LAB_B"].min() - 10, df["LAB_B"].max() + 10]

fig_ab.add_hline(y=0, line_dash="dash", line_color="gray", line_width=0.8)
fig_ab.add_vline(x=0, line_dash="dash", line_color="gray", line_width=0.8)

# 측정 데이터 포인트 - 누적 데이터일 때 데이터 소스별로 분리
if data_source == "누적 데이터" and len(data_frames) > 1:
    _MARKER_SYMBOLS = ["circle", "square", "diamond", "cross", "triangle-up",
                       "triangle-down", "star", "hexagon", "pentagon", "x"]
    for src_idx, (src_name, sub_df) in enumerate(data_frames):
        if not all(c in sub_df.columns for c in _REQUIRED_COLS):
            continue
        sub_hex = [
            lab_to_hex(row["LAB_L"], row["LAB_A"], row["LAB_B"])
            for _, row in sub_df.iterrows()
        ]
        if "SAMPLE_NAME" in sub_df.columns:
            sub_names = sub_df["SAMPLE_NAME"].astype(str).tolist()
        else:
            sub_names = [f"샘플 {i + 1}" for i in range(len(sub_df))]

        symbol = _MARKER_SYMBOLS[src_idx % len(_MARKER_SYMBOLS)]
        fig_ab.add_trace(
            go.Scatter(
                x=sub_df["LAB_A"],
                y=sub_df["LAB_B"],
                mode="markers+text",
                marker=dict(
                    size=14,
                    color=sub_hex,
                    line=dict(width=1.5, color="black"),
                    symbol=symbol,
                ),
                text=sub_names,
                textposition="top right",
                textfont=dict(size=10),
                name=src_name,
                hovertemplate=(
                    "<b>%{text}</b> (" + src_name + ")<br>"
                    "a* = %{x:.2f}<br>"
                    "b* = %{y:.2f}<extra></extra>"
                ),
            )
        )
else:
    fig_ab.add_trace(
        go.Scatter(
            x=df["LAB_A"],
            y=df["LAB_B"],
            mode="markers+text",
            marker=dict(
                size=14,
                color=hex_colors,
                line=dict(width=1.5, color="black"),
                symbol="circle",
            ),
            text=sample_names,
            textposition="top right",
            textfont=dict(size=10),
            name="측정값",
            hovertemplate=(
                "<b>%{text}</b><br>"
                "a* = %{x:.2f}<br>"
                "b* = %{y:.2f}<extra></extra>"
            ),
        )
    )

# 기준 색상 표시 (session_state에 reference_colors가 있는 경우)
ref_colors = st.session_state.get("reference_colors")
if ref_colors and isinstance(ref_colors, dict):
    ref_a_vals = []
    ref_b_vals = []
    ref_names = []
    ref_hex = []
    for name, vals in ref_colors.items():
        if isinstance(vals, (list, tuple)) and len(vals) == 3:
            rL, ra, rb = vals
            ref_a_vals.append(ra)
            ref_b_vals.append(rb)
            ref_names.append(name)
            ref_hex.append(lab_to_hex(rL, ra, rb))
        elif isinstance(vals, dict) and "a" in vals and "b" in vals and "L" in vals:
            ref_a_vals.append(vals["a"])
            ref_b_vals.append(vals["b"])
            ref_names.append(name)
            ref_hex.append(lab_to_hex(vals["L"], vals["a"], vals["b"]))

    if ref_a_vals:
        fig_ab.add_trace(
            go.Scatter(
                x=ref_a_vals,
                y=ref_b_vals,
                mode="markers+text",
                marker=dict(
                    size=12,
                    color=ref_hex,
                    line=dict(width=2, color="black"),
                    symbol="diamond",
                ),
                text=ref_names,
                textposition="bottom right",
                textfont=dict(size=9, color="gray"),
                name="기준 색상",
                hovertemplate=(
                    "<b>%{text} (기준)</b><br>"
                    "a* = %{x:.2f}<br>"
                    "b* = %{y:.2f}<extra></extra>"
                ),
            )
        )

# 축 라벨
fig_ab.add_annotation(
    x=a_range[1] - 2, y=2, text="+a* (적색)", showarrow=False,
    font=dict(size=10, color="red"),
)
fig_ab.add_annotation(
    x=a_range[0] + 2, y=2, text="-a* (녹색)", showarrow=False,
    font=dict(size=10, color="green"),
)
fig_ab.add_annotation(
    x=2, y=b_range[1] - 2, text="+b* (황색)", showarrow=False,
    font=dict(size=10, color="goldenrod"),
)
fig_ab.add_annotation(
    x=2, y=b_range[0] + 2, text="-b* (청색)", showarrow=False,
    font=dict(size=10, color="blue"),
)

fig_ab.update_layout(
    **_common_layout(
        title="a*b* 색도 다이어그램",
        xaxis_title="a*",
        yaxis_title="b*",
        xaxis=dict(zeroline=False, range=a_range),
        yaxis=dict(zeroline=False, range=b_range, scaleanchor="x"),
        height=600,
        showlegend=True,
        legend=dict(x=0.01, y=0.99),
    )
)

st.plotly_chart(fig_ab, use_container_width=True)
st.divider()

# =========================================================================
# 2. L* 비교 차트
# =========================================================================

st.header("2. L* 비교 차트")
st.caption("각 샘플의 명도(L*) 값을 비교합니다.")

fig_lstar = go.Figure()

# 누적 데이터일 때 데이터 소스별로 그룹화된 바 차트
if data_source == "누적 데이터" and len(data_frames) > 1:
    _BAR_COLORS = [
        "rgba(31, 119, 180, 0.8)", "rgba(255, 127, 14, 0.8)",
        "rgba(44, 160, 44, 0.8)", "rgba(214, 39, 40, 0.8)",
        "rgba(148, 103, 189, 0.8)", "rgba(140, 86, 75, 0.8)",
        "rgba(227, 119, 194, 0.8)", "rgba(127, 127, 127, 0.8)",
    ]
    for src_idx, (src_name, sub_df) in enumerate(data_frames):
        if not all(c in sub_df.columns for c in _REQUIRED_COLS):
            continue
        if "SAMPLE_NAME" in sub_df.columns:
            sub_names = sub_df["SAMPLE_NAME"].astype(str).tolist()
        else:
            sub_names = [f"샘플 {i + 1}" for i in range(len(sub_df))]

        bar_color = _BAR_COLORS[src_idx % len(_BAR_COLORS)]
        fig_lstar.add_trace(
            go.Bar(
                x=sub_names,
                y=sub_df["LAB_L"],
                marker_color=bar_color,
                marker_line=dict(width=1.5, color="black"),
                text=[f"{v:.1f}" for v in sub_df["LAB_L"]],
                textposition="outside",
                name=src_name,
                hovertemplate=(
                    "<b>%{x}</b> (" + src_name + ")<br>"
                    "L* = %{y:.2f}<extra></extra>"
                ),
            )
        )
    fig_lstar.update_layout(barmode="group")
else:
    bar_hex = [
        lab_to_hex(row["LAB_L"], row["LAB_A"], row["LAB_B"])
        for _, row in df.iterrows()
    ]

    fig_lstar.add_trace(
        go.Bar(
            x=sample_names,
            y=df["LAB_L"],
            marker_color=bar_hex,
            marker_line=dict(width=1.5, color="black"),
            text=[f"{v:.1f}" for v in df["LAB_L"]],
            textposition="outside",
            name="측정 L*",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "L* = %{y:.2f}<extra></extra>"
            ),
        )
    )

fig_lstar.update_layout(
    **_common_layout(
        title="L* 명도 비교",
        xaxis_title="샘플",
        yaxis_title="L*",
        yaxis=dict(range=[0, 105]),
        height=500,
        showlegend=data_source == "누적 데이터" and len(data_frames) > 1,
    )
)

st.plotly_chart(fig_lstar, use_container_width=True)
st.divider()

# =========================================================================
# 3. Color Gamut 분석
# =========================================================================

st.header("3. Color Gamut 분석")
st.caption("색역(Gamut)을 2D 면적(a*b*) 및 3D 체적(L*a*b*)으로 분석합니다.")

# Chromatic color 판별: White/Black (a*~0, b*~0, L* 극단) 제외
import math

_ACHROMATIC_THRESHOLD = 10.0  # chroma < threshold → achromatic


def _is_chromatic(L: float, a: float, b: float) -> bool:
    """Return True if the color is chromatic (not near the neutral axis)."""
    chroma = math.sqrt(a ** 2 + b ** 2)
    return chroma >= _ACHROMATIC_THRESHOLD


chromatic_indices = [
    i for i in range(len(df))
    if _is_chromatic(df.iloc[i]["LAB_L"], df.iloc[i]["LAB_A"], df.iloc[i]["LAB_B"])
]
chromatic_names = [sample_names[i] for i in chromatic_indices]

# 사용자가 gamut에 사용할 색상 선택
if chromatic_names:
    selected_gamut_colors = st.multiselect(
        "Gamut 계산에 사용할 색상 선택",
        options=chromatic_names,
        default=chromatic_names,
        help="White, Black 등 무채색은 자동 제외됩니다. 최소 3개 이상 선택해야 합니다.",
    )
else:
    # fallback: let user pick from all
    selected_gamut_colors = st.multiselect(
        "Gamut 계산에 사용할 색상 선택",
        options=sample_names,
        default=sample_names,
        help="최소 3개 이상 선택해야 합니다.",
    )

# 선택된 색상의 좌표 추출
gamut_ab_points: list[tuple[float, float]] = []
gamut_lab_points: list[tuple[float, float, float]] = []
gamut_labels: list[str] = []
gamut_hex: list[str] = []

for i, name in enumerate(sample_names):
    if name in selected_gamut_colors:
        L_val = float(df.iloc[i]["LAB_L"])
        a_val = float(df.iloc[i]["LAB_A"])
        b_val = float(df.iloc[i]["LAB_B"])
        gamut_ab_points.append((a_val, b_val))
        gamut_lab_points.append((L_val, a_val, b_val))
        gamut_labels.append(name)
        gamut_hex.append(hex_colors[i])

if len(gamut_ab_points) >= 3:
    # Calculate 2D gamut area
    gamut_area = calculate_gamut_area(gamut_ab_points)

    # Calculate 3D gamut volume
    gamut_volume = calculate_gamut_volume(gamut_lab_points)

    # Display metrics
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("2D Gamut 면적 (a*b* 단위²)", f"{gamut_area:,.1f}")
    with col_m2:
        st.metric("3D Gamut 체적 (L*a*b* 단위³)", f"{gamut_volume:,.1f}")

    # --- Tab layout for 2D and 3D views ---
    tab_2d, tab_3d = st.tabs(["2D Gamut (a*b* 면적)", "3D Gamut (L*a*b* 체적)"])

    # --- 2D a*b* Gamut polygon view ---
    with tab_2d:
        # Sort points by hue angle for polygon drawing
        sorted_indices = sorted(
            range(len(gamut_ab_points)),
            key=lambda idx: math.atan2(gamut_ab_points[idx][1], gamut_ab_points[idx][0]),
        )
        sorted_ab = [gamut_ab_points[idx] for idx in sorted_indices]
        sorted_labels = [gamut_labels[idx] for idx in sorted_indices]
        sorted_hex = [gamut_hex[idx] for idx in sorted_indices]

        # Close the polygon
        poly_a = [p[0] for p in sorted_ab] + [sorted_ab[0][0]]
        poly_b = [p[1] for p in sorted_ab] + [sorted_ab[0][1]]

        fig_gamut = go.Figure()

        # 기준선
        fig_gamut.add_hline(y=0, line_dash="dash", line_color="gray", line_width=0.8)
        fig_gamut.add_vline(x=0, line_dash="dash", line_color="gray", line_width=0.8)

        # Filled gamut polygon
        fig_gamut.add_trace(
            go.Scatter(
                x=poly_a,
                y=poly_b,
                mode="lines",
                fill="toself",
                fillcolor="rgba(100, 149, 237, 0.2)",
                line=dict(color="rgba(65, 105, 225, 0.7)", width=2),
                name="Gamut 영역",
                hoverinfo="skip",
            )
        )

        # Color points on the gamut
        fig_gamut.add_trace(
            go.Scatter(
                x=[p[0] for p in sorted_ab],
                y=[p[1] for p in sorted_ab],
                mode="markers+text",
                marker=dict(
                    size=14,
                    color=sorted_hex,
                    line=dict(width=1.5, color="black"),
                    symbol="circle",
                ),
                text=sorted_labels,
                textposition="top right",
                textfont=dict(size=10),
                name="색상 포인트",
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "a* = %{x:.2f}<br>"
                    "b* = %{y:.2f}<extra></extra>"
                ),
            )
        )

        # Axis range
        all_a = [p[0] for p in gamut_ab_points]
        all_b = [p[1] for p in gamut_ab_points]
        ga_range = [min(all_a) - 15, max(all_a) + 15]
        gb_range = [min(all_b) - 15, max(all_b) + 15]

        fig_gamut.update_layout(
            **_common_layout(
                title=f"2D Gamut (a*b* 면적: {gamut_area:,.1f})",
                xaxis_title="a*",
                yaxis_title="b*",
                xaxis=dict(zeroline=False, range=ga_range),
                yaxis=dict(zeroline=False, range=gb_range, scaleanchor="x"),
                height=600,
                showlegend=True,
                legend=dict(x=0.01, y=0.99),
            )
        )

        st.plotly_chart(fig_gamut, use_container_width=True)

    # --- 3D L*a*b* Gamut view ---
    with tab_3d:
        fig_3d = go.Figure()

        L_vals = [p[0] for p in gamut_lab_points]
        a_vals = [p[1] for p in gamut_lab_points]
        b_vals = [p[2] for p in gamut_lab_points]

        # Scatter3d for gamut points
        fig_3d.add_trace(
            go.Scatter3d(
                x=a_vals,
                y=b_vals,
                z=L_vals,
                mode="markers+text",
                marker=dict(
                    size=8,
                    color=gamut_hex,
                    line=dict(width=1.5, color="black"),
                ),
                text=gamut_labels,
                textposition="top right",
                textfont=dict(size=9),
                name="색상 포인트",
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "a* = %{x:.2f}<br>"
                    "b* = %{y:.2f}<br>"
                    "L* = %{z:.2f}<extra></extra>"
                ),
            )
        )

        # Convex Hull mesh surface if enough points
        if len(gamut_lab_points) >= 4:
            try:
                from scipy.spatial import ConvexHull
                pts = np.array(gamut_lab_points)
                hull = ConvexHull(pts)
                # hull.simplices gives triangle faces
                i_faces = [s[0] for s in hull.simplices]
                j_faces = [s[1] for s in hull.simplices]
                k_faces = [s[2] for s in hull.simplices]

                fig_3d.add_trace(
                    go.Mesh3d(
                        x=pts[:, 1],  # a*
                        y=pts[:, 2],  # b*
                        z=pts[:, 0],  # L*
                        i=i_faces,
                        j=j_faces,
                        k=k_faces,
                        opacity=0.25,
                        color="cornflowerblue",
                        name="Gamut 체적",
                        hoverinfo="skip",
                    )
                )
            except Exception:
                pass

        fig_3d.update_layout(
            **_common_layout(
                title=f"3D Gamut (L*a*b* 체적: {gamut_volume:,.1f})",
                height=700,
                showlegend=True,
            ),
            scene=dict(
                xaxis_title="a*",
                yaxis_title="b*",
                zaxis_title="L*",
            ),
        )

        st.plotly_chart(fig_3d, use_container_width=True)
else:
    st.warning("Gamut 계산에는 최소 3개 이상의 색상이 필요합니다. 색상을 더 선택해 주세요.")
