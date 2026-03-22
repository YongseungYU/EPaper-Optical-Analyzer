"""
그래프 및 시각화 페이지.

측정 데이터를 다양한 Plotly 차트로 시각화합니다.
- L*a*b* 3D 산점도
- a*b* 색도 다이어그램
- Delta E 막대 차트
- 분광 반사율 그래프
- L* 비교 차트
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from core.color_utils import lab_to_hex

# Delta E 모듈이 아직 없을 수 있으므로 안전하게 임포트
try:
    from core.delta_e import batch_delta_e
except ImportError:
    batch_delta_e = None

from core.parser import get_spectral, spectral_wavelengths

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="그래프 및 시각화 - E-paper Optical Analyzer",
    page_icon="📈",
    layout="wide",
)

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

if "measurement_data" not in st.session_state or st.session_state["measurement_data"] is None:
    st.warning("측정 데이터가 없습니다. 먼저 데이터를 업로드해 주세요.")
    st.stop()

df: pd.DataFrame = st.session_state["measurement_data"]

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
# 1. L*a*b* 3D 산점도
# =========================================================================

st.header("1. L*a*b* 3D 산점도")
st.caption("a*를 X축, b*를 Y축, L*를 Z축으로 배치한 3D 색 공간 시각화입니다.")

fig_3d = go.Figure(
    data=[
        go.Scatter3d(
            x=df["LAB_A"],
            y=df["LAB_B"],
            z=df["LAB_L"],
            mode="markers+text",
            marker=dict(
                size=10,
                color=hex_colors,
                line=dict(width=1, color="gray"),
                opacity=0.95,
            ),
            text=sample_names,
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "a* = %{x:.2f}<br>"
                "b* = %{y:.2f}<br>"
                "L* = %{z:.2f}<extra></extra>"
            ),
        )
    ]
)

fig_3d.update_layout(
    **_common_layout(
        title="L*a*b* 3D 색 공간",
        scene=dict(
            xaxis_title="a* (녹-적)",
            yaxis_title="b* (청-황)",
            zaxis_title="L* (명도)",
            xaxis=dict(backgroundcolor="rgb(240,240,240)"),
            yaxis=dict(backgroundcolor="rgb(240,240,240)"),
            zaxis=dict(backgroundcolor="rgb(245,245,245)"),
        ),
        height=650,
    )
)

st.plotly_chart(fig_3d, use_container_width=True)
st.divider()

# =========================================================================
# 2. a*b* 색도 다이어그램
# =========================================================================

st.header("2. a*b* 색도 다이어그램")
st.caption("a*-b* 평면 위에 측정 색상을 표시합니다. 기준 색상은 다이아몬드(◆)로 표시됩니다.")

fig_ab = go.Figure()

# 기준선 (a*=0, b*=0)
a_range = [df["LAB_A"].min() - 10, df["LAB_A"].max() + 10]
b_range = [df["LAB_B"].min() - 10, df["LAB_B"].max() + 10]

fig_ab.add_hline(y=0, line_dash="dash", line_color="gray", line_width=0.8)
fig_ab.add_vline(x=0, line_dash="dash", line_color="gray", line_width=0.8)

# 측정 데이터 포인트
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
# 3. Delta E 막대 차트
# =========================================================================

st.header("3. Delta E 막대 차트")

delta_e_results = st.session_state.get("delta_e_results")

if delta_e_results is not None and isinstance(delta_e_results, (list, pd.DataFrame)):
    # DataFrame으로 변환
    if isinstance(delta_e_results, list):
        de_df = pd.DataFrame(delta_e_results)
    else:
        de_df = delta_e_results.copy()

    # 필요한 컬럼 확인
    de_col = None
    for candidate in ["Delta E", "delta_e", "Delta_E", "DELTA_E", "dE"]:
        if candidate in de_df.columns:
            de_col = candidate
            break

    name_col = None
    for candidate in ["샘플명", "SAMPLE_NAME", "sample_name", "name", "Name"]:
        if candidate in de_df.columns:
            name_col = candidate
            break

    if de_col is not None:
        threshold = st.session_state.get("delta_e_threshold", 3.0)
        de_values = de_df[de_col].astype(float)
        de_names = (
            de_df[name_col].astype(str).tolist()
            if name_col
            else [f"샘플 {i + 1}" for i in range(len(de_df))]
        )

        bar_colors = [
            "rgb(46, 160, 67)" if v <= threshold else "rgb(218, 54, 51)"
            for v in de_values
        ]

        fig_de = go.Figure(
            data=[
                go.Bar(
                    y=de_names,
                    x=de_values,
                    orientation="h",
                    marker_color=bar_colors,
                    text=[f"{v:.2f}" for v in de_values],
                    textposition="outside",
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Delta E = %{x:.2f}<extra></extra>"
                    ),
                )
            ]
        )

        # 임계값 선
        fig_de.add_vline(
            x=threshold,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text=f"임계값 ({threshold})",
            annotation_position="top right",
            annotation_font=dict(size=11, color="orange"),
        )

        fig_de.update_layout(
            **_common_layout(
                title="Delta E 분석 결과",
                xaxis_title="Delta E",
                yaxis_title="샘플",
                height=max(350, len(de_names) * 45 + 100),
                yaxis=dict(autorange="reversed"),
            )
        )

        # 범례 설명
        st.markdown(
            f"🟢 **Pass** (Delta E ≤ {threshold})  &nbsp;&nbsp; "
            f"🔴 **Fail** (Delta E > {threshold})"
        )
        st.plotly_chart(fig_de, use_container_width=True)
    else:
        st.info("Delta E 결과 데이터에 Delta E 값 컬럼을 찾을 수 없습니다.")
else:
    st.info("Delta E 분석 결과가 없습니다. 분석 페이지에서 먼저 Delta E를 계산해 주세요.")

st.divider()

# =========================================================================
# 4. 분광 반사율 그래프
# =========================================================================

st.header("4. 분광 반사율 그래프")

spec_df = get_spectral(df)
wavelengths = spectral_wavelengths(df)

if spec_df is not None and wavelengths:
    fig_spec = go.Figure()

    spec_cols = sorted(
        [c for c in spec_df.columns if c.upper().startswith(("SPECTRAL_", "SPEC_", "NM"))],
        key=lambda c: int(''.join(filter(str.isdigit, c)) or '0'),
    )

    for idx in range(len(spec_df)):
        row = spec_df.iloc[idx]
        reflectance = [float(row[c]) for c in spec_cols]
        name = sample_names[idx] if idx < len(sample_names) else f"샘플 {idx + 1}"

        fig_spec.add_trace(
            go.Scatter(
                x=wavelengths,
                y=reflectance,
                mode="lines",
                name=name,
                line=dict(width=2),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "파장 = %{x} nm<br>"
                    "반사율 = %{y:.4f}<extra></extra>"
                ),
            )
        )

    fig_spec.update_layout(
        **_common_layout(
            title="분광 반사율 곡선",
            xaxis_title="파장 (nm)",
            yaxis_title="반사율",
            xaxis=dict(range=[380, 730], dtick=50),
            height=500,
            showlegend=True,
            legend=dict(x=1.02, y=1, xanchor="left"),
        )
    )

    st.plotly_chart(fig_spec, use_container_width=True)
else:
    st.info("분광 반사율 데이터가 포함되어 있지 않습니다. 스펙트럼 데이터가 있는 파일을 업로드하면 이 그래프가 표시됩니다.")

st.divider()

# =========================================================================
# 5. L* 비교 차트
# =========================================================================

st.header("5. L* 비교 차트")
st.caption("각 샘플의 명도(L*) 값을 비교합니다. 기준 L* 값이 있으면 수평선으로 표시됩니다.")

fig_lstar = go.Figure()

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

# 기준 색상의 L* 값을 수평선으로 표시
if ref_colors and isinstance(ref_colors, dict):
    # 고유한 색상 사용
    _line_colors = [
        "red", "blue", "green", "purple", "orange", "brown", "teal",
        "magenta", "olive", "navy",
    ]
    for i, (name, vals) in enumerate(ref_colors.items()):
        ref_L = None
        if isinstance(vals, (list, tuple)) and len(vals) == 3:
            ref_L = vals[0]
        elif isinstance(vals, dict) and "L" in vals:
            ref_L = vals["L"]
        if ref_L is not None:
            line_col = _line_colors[i % len(_line_colors)]
            fig_lstar.add_hline(
                y=ref_L,
                line_dash="dot",
                line_color=line_col,
                line_width=1.5,
                annotation_text=f"기준 {name} (L*={ref_L:.1f})",
                annotation_position="top right",
                annotation_font=dict(size=9, color=line_col),
            )

fig_lstar.update_layout(
    **_common_layout(
        title="L* 명도 비교",
        xaxis_title="샘플",
        yaxis_title="L*",
        yaxis=dict(range=[0, 105]),
        height=500,
        showlegend=False,
    )
)

st.plotly_chart(fig_lstar, use_container_width=True)
