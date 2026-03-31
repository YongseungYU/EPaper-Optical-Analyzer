"""Delta E 계산기 페이지 - E-paper Optical Analyzer."""

import math
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure project root is on sys.path for imports
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.delta_e import delta_e_ciede2000
from core.color_utils import lab_to_hex, get_color_name
from core.export import export_to_excel
from core.ui_common import render_mode_header

# ── 페이지 설정 ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Delta E 계산기", page_icon="📐", layout="wide")

# ── 모드 체크 ───────────────────────────────────────────────────────────────

app_mode = st.session_state.get('app_mode')
if app_mode is None:
    st.warning("이 페이지는 모드 선택 후 사용할 수 있습니다. 홈에서 모드를 선택해 주세요.")
    st.stop()

is_basic = app_mode == 'basic'
is_advanced = app_mode == 'advanced'

render_mode_header()
st.title("📐 Delta E 계산기")
st.markdown("측정값과 기준값 사이의 색차(Delta E)를 계산합니다.")

# ── 데이터 소스 선택 (현재 / 누적) ──────────────────────────────────────────

data_source = "현재 데이터"

if is_advanced:
    has_cumulative = st.session_state.get("cumulative_data") is not None
    if has_cumulative:
        data_source = st.selectbox(
            "분석 데이터 선택",
            options=["현재 데이터", "누적 데이터"],
            index=0,
            help="누적 데이터를 선택하면 이전에 업로드한 데이터를 합산하여 분석합니다.",
        )

# ── 데이터 확인 ─────────────────────────────────────────────────────────────

if data_source == "누적 데이터":
    df: pd.DataFrame = st.session_state["cumulative_data"]
    st.info("📂 누적 데이터를 사용하여 분석합니다.")
else:
    if "measurement_data" not in st.session_state or st.session_state["measurement_data"] is None:
        st.warning("⚠️ 측정 데이터가 없습니다. 먼저 **Data Upload** 페이지에서 데이터를 업로드해 주세요.")
        st.stop()
    df = st.session_state["measurement_data"]

required_cols = ["LAB_L", "LAB_A", "LAB_B"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"필수 컬럼이 누락되었습니다: {missing}")
    st.stop()

name_col = "SAMPLE_NAME" if "SAMPLE_NAME" in df.columns else (
    "SAMPLE_ID" if "SAMPLE_ID" in df.columns else None
)

# ── 사이드바: 설정 ──────────────────────────────────────────────────────────

st.sidebar.header("⚙️ 계산 설정")

# CIEDE2000 only — no formula selection
formula = "CIEDE2000"
st.sidebar.markdown(f"**사용 공식:** {formula}")

# Per-color Delta E limits
st.sidebar.subheader("🎯 색상별 합격 기준값")
st.sidebar.markdown("색상별로 ΔE 허용 한계를 설정합니다.")

DEFAULT_LIMITS = {
    "White": 6.0,
    "Black": 6.0,
    "Red": 6.0,
    "Yellow": 6.0,
    "Blue": 6.0,
    "Green": 8.0,
}

color_limits = {}
for color_name, default_val in DEFAULT_LIMITS.items():
    color_limits[color_name] = st.sidebar.number_input(
        f"{color_name} ΔE 한계",
        min_value=0.1,
        max_value=50.0,
        value=default_val,
        step=0.5,
        key=f"limit_{color_name}",
    )

# Default limit for unmatched colors
default_limit = st.sidebar.number_input(
    "기타 색상 ΔE 한계",
    min_value=0.1,
    max_value=50.0,
    value=6.0,
    step=0.5,
    key="limit_default",
)

# ── 기준값 설정 ─────────────────────────────────────────────────────────────

st.header("📌 기준값(Reference) 설정")

reference: dict[str, tuple[float, float, float]] = {}

# 세션에 저장된 파싱 결과 불러오기
if "parsed_reference" not in st.session_state:
    st.session_state["parsed_reference"] = {}


def _parse_ref_text(text: str) -> tuple[dict, list]:
    """기준값 텍스트를 파싱하여 (reference dict, errors list)를 반환합니다."""
    parsed = {}
    errors = []
    for line_num, line in enumerate(text.strip().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 4:
            errors.append(f"Line {line_num}: 형식 오류 (최소 4개 필드 필요) - '{line}'")
            continue
        try:
            name = " ".join(parts[:-3])
            rL = float(parts[-3])
            ra = float(parts[-2])
            rb = float(parts[-1])
            parsed[name] = (rL, ra, rb)
        except ValueError:
            errors.append(f"Line {line_num}: 숫자 변환 오류 - '{line}'")
    return parsed, errors


def _show_ref_table(ref: dict):
    """파싱된 기준값을 테이블로 표시합니다."""
    ref_display = []
    for cname, (rL, ra, rb) in ref.items():
        hex_c = lab_to_hex(rL, ra, rb)
        ref_display.append({"색상명": cname, "L*": rL, "a*": ra, "b*": rb, "미리보기": hex_c})
    st.dataframe(pd.DataFrame(ref_display), use_container_width=True, hide_index=True)


if is_basic:
    # Basic mode: text paste only
    st.markdown("기준 L\\*a\\*b\\* 값을 아래 형식으로 붙여넣으세요 (공백 또는 탭 구분):")
    st.code("White 66.5 -4 0\nBlack 12 7 -11\nRed 26.5 41 30\nYellow 62 -11 65\nBlue 27 6 -35\nGreen 32 -22 5", language="text")

    ref_text = st.text_area(
        "기준값 텍스트 입력",
        height=200,
        placeholder="White 66.5 -4 0\nBlack 12 7 -11\n...",
        key="ref_text_input",
    )

    if st.button("📋 기준값 파싱", type="primary", use_container_width=True, key="btn_parse_ref_basic"):
        if ref_text.strip():
            parsed, errors = _parse_ref_text(ref_text)
            for err in errors:
                st.warning(err)
            if parsed:
                st.session_state["parsed_reference"] = parsed
                st.success(f"✅ {len(parsed)}개 기준값을 파싱했습니다.")
            else:
                st.warning("파싱된 기준값이 없습니다. 형식을 확인해 주세요.")
        else:
            st.warning("기준값 텍스트를 입력해 주세요.")

    # 파싱 결과 표시
    if st.session_state["parsed_reference"]:
        reference = st.session_state["parsed_reference"]
        _show_ref_table(reference)

elif is_advanced:
    # Advanced mode: text paste + 직접 입력
    ref_method = st.radio(
        "기준값 입력 방식",
        options=["텍스트 붙여넣기 (기준값)", "직접 입력"],
        horizontal=True,
    )

    if ref_method == "텍스트 붙여넣기 (기준값)":
        st.markdown("기준 L\\*a\\*b\\* 값을 아래 형식으로 붙여넣으세요 (공백 또는 탭 구분):")
        st.code("White 66.5 -4 0\nBlack 12 7 -11\nRed 26.5 41 30\nYellow 62 -11 65\nBlue 27 6 -35\nGreen 32 -22 5", language="text")

        ref_text = st.text_area(
            "기준값 텍스트 입력",
            height=200,
            placeholder="White 66.5 -4 0\nBlack 12 7 -11\n...",
            key="ref_text_input",
        )

        if st.button("📋 기준값 파싱", type="primary", use_container_width=True, key="btn_parse_ref_adv"):
            if ref_text.strip():
                parsed, errors = _parse_ref_text(ref_text)
                for err in errors:
                    st.warning(err)
                if parsed:
                    st.session_state["parsed_reference"] = parsed
                    st.success(f"✅ {len(parsed)}개 기준값을 파싱했습니다.")
                else:
                    st.warning("파싱된 기준값이 없습니다. 형식을 확인해 주세요.")
            else:
                st.warning("기준값 텍스트를 입력해 주세요.")

        # 파싱 결과 표시
        if st.session_state["parsed_reference"]:
            reference = st.session_state["parsed_reference"]
            _show_ref_table(reference)

    elif ref_method == "직접 입력":
        st.markdown("각 샘플에 대한 기준 L\\*a\\*b\\* 값을 입력하세요.")

        # Get sample names from measurement data
        if name_col:
            sample_names = df[name_col].unique().tolist()
        else:
            sample_names = [f"Sample {i + 1}" for i in range(len(df))]

        # Build color groups: map each sample to its detected color name
        sample_color_map = {}
        for idx, row in df.iterrows():
            sname = str(row[name_col]) if name_col else f"Sample {idx + 1}"
            L, a, b = float(row["LAB_L"]), float(row["LAB_A"]), float(row["LAB_B"])
            detected = get_color_name(L, a, b)
            sample_color_map[sname] = detected

        # Get unique color groups
        unique_colors = sorted(set(sample_color_map.values()))

        # ── 전체 적용 / 분할 적용 ───────────────────────────────────────────
        st.subheader("일괄 입력 도구")

        apply_col1, apply_col2 = st.columns(2)

        with apply_col1:
            st.markdown("**전체 적용** — 모든 샘플에 동일한 기준값 적용")
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                bulk_L = st.number_input("L*", min_value=0.0, max_value=100.0, value=50.0, step=0.1, key="bulk_L")
            with ac2:
                bulk_a = st.number_input("a*", min_value=-128.0, max_value=128.0, value=0.0, step=0.1, key="bulk_a")
            with ac3:
                bulk_b = st.number_input("b*", min_value=-128.0, max_value=128.0, value=0.0, step=0.1, key="bulk_b")
            if st.button("전체 적용", key="apply_all"):
                for sn in sample_names:
                    st.session_state[f"ref_L_{sn}"] = bulk_L
                    st.session_state[f"ref_a_{sn}"] = bulk_a
                    st.session_state[f"ref_b_{sn}"] = bulk_b
                st.rerun()

        with apply_col2:
            st.markdown("**분할 적용** — 선택한 색상 그룹에 기준값 적용")
            group_colors = st.multiselect(
                "대상 색상 선택",
                unique_colors,
                key="group_color_select",
                help="선택한 색상으로 식별된 모든 샘플에 동일한 기준값을 적용합니다.",
            )
            gc1, gc2, gc3 = st.columns(3)
            with gc1:
                group_L = st.number_input("L*", min_value=0.0, max_value=100.0, value=50.0, step=0.1, key="group_L")
            with gc2:
                group_a = st.number_input("a*", min_value=-128.0, max_value=128.0, value=0.0, step=0.1, key="group_a")
            with gc3:
                group_b = st.number_input("b*", min_value=-128.0, max_value=128.0, value=0.0, step=0.1, key="group_b")
            if st.button("분할 적용", key="apply_group"):
                # Apply to all samples whose detected color is in the selected group
                for sn in sample_names:
                    detected = sample_color_map.get(sn)
                    if detected in group_colors:
                        st.session_state[f"ref_L_{sn}"] = group_L
                        st.session_state[f"ref_a_{sn}"] = group_a
                        st.session_state[f"ref_b_{sn}"] = group_b
                st.rerun()

        # ── 테이블 형태 입력 ────────────────────────────────────────────────
        st.subheader("개별 샘플 기준값")

        # Header row
        hc1, hc2, hc3, hc4, hc5 = st.columns([2, 1, 1, 1, 1])
        with hc1:
            st.markdown("**샘플명**")
        with hc2:
            st.markdown("**식별 색상**")
        with hc3:
            st.markdown("**L\\***")
        with hc4:
            st.markdown("**a\\***")
        with hc5:
            st.markdown("**b\\***")

        for sname in sample_names:
            detected = sample_color_map.get(sname, "")
            c0, c_color, c1, c2, c3 = st.columns([2, 1, 1, 1, 1])
            with c0:
                st.markdown(f"`{sname}`")
            with c_color:
                st.markdown(f"{detected}")
            with c1:
                ref_L = st.number_input(
                    "L*", min_value=0.0, max_value=100.0, value=50.0,
                    step=0.1, key=f"ref_L_{sname}", label_visibility="collapsed",
                )
            with c2:
                ref_a = st.number_input(
                    "a*", min_value=-128.0, max_value=128.0, value=0.0,
                    step=0.1, key=f"ref_a_{sname}", label_visibility="collapsed",
                )
            with c3:
                ref_b = st.number_input(
                    "b*", min_value=-128.0, max_value=128.0, value=0.0,
                    step=0.1, key=f"ref_b_{sname}", label_visibility="collapsed",
                )
            reference[str(sname)] = (ref_L, ref_a, ref_b)

# Store reference in session state for use by Color Analysis page
if reference:
    st.session_state["reference_colors"] = reference

# ── Delta E 계산 ────────────────────────────────────────────────────────────

st.divider()
st.header("📊 Delta E 계산 결과")

if not reference:
    st.info("기준값을 설정한 후 아래 버튼을 눌러 계산하세요.")

calc_button = st.button("🔬 Delta E 계산", type="primary", disabled=len(reference) == 0)

if calc_button and reference:
    calc_fn = delta_e_ciede2000

    results = []
    for idx, row in df.iterrows():
        sample_name = str(row[name_col]) if name_col else f"Sample {idx + 1}"
        mL = float(row["LAB_L"])
        ma = float(row["LAB_A"])
        mb = float(row["LAB_B"])

        # Find matching reference
        ref_lab = reference.get(sample_name)
        if ref_lab is None:
            # Try partial match
            for ref_name in reference:
                if ref_name.lower() in sample_name.lower() or sample_name.lower() in ref_name.lower():
                    ref_lab = reference[ref_name]
                    break

        if ref_lab is None:
            continue

        rL, ra, rb = ref_lab
        de_value = calc_fn(mL, ma, mb, rL, ra, rb)

        # Determine color for per-color limit
        detected_color = get_color_name(mL, ma, mb)
        limit = color_limits.get(detected_color, default_limit)
        pass_fail = "합격" if de_value <= limit else "불합격"

        results.append({
            "샘플명": sample_name,
            "식별 색상": detected_color,
            "측정 L*": round(mL, 2),
            "측정 a*": round(ma, 2),
            "측정 b*": round(mb, 2),
            "기준 L*": round(rL, 2),
            "기준 a*": round(ra, 2),
            "기준 b*": round(rb, 2),
            "Delta E": round(de_value, 4),
            "ΔE 한계": limit,
            "판정": pass_fail,
        })

    if not results:
        st.warning("일치하는 기준값이 없어 계산할 수 없습니다. 샘플명과 기준값 색상명이 일치하는지 확인해 주세요.")
    else:
        results_df = pd.DataFrame(results)

        # Store in session state
        st.session_state["delta_e_results"] = results_df

        # ── 색상별 그룹화된 결과 표시 ─────────────────────────────────
        # 색상명 → HEX 매핑 (식별 색상 컬러 패치용)
        _COLOR_HEX_MAP = {
            "White": "#F5F5F5", "Black": "#222222", "Red": "#D32F2F",
            "Green": "#388E3C", "Blue": "#1976D2", "Yellow": "#FBC02D",
            "Orange": "#F57C00", "Gray": "#9E9E9E",
        }

        unique_colors = results_df["식별 색상"].unique().tolist()

        for color_name in unique_colors:
            color_group = results_df[results_df["식별 색상"] == color_name]
            color_hex = _COLOR_HEX_MAP.get(color_name, "#9E9E9E")
            text_color = "#FFFFFF" if color_name in ("Black", "Blue", "Red", "Green") else "#000000"

            # 색상 그룹 헤더 (컬러 패치 + 색상명 + 판정 요약)
            group_pass = (color_group["판정"] == "합격").sum()
            group_total = len(color_group)
            group_status = "합격" if group_pass == group_total else f"{group_pass}/{group_total} 합격"

            st.markdown(
                f"""<div style="
                    display: flex; align-items: center; gap: 12px;
                    margin-top: 16px; margin-bottom: 8px;
                ">
                    <span style="
                        display: inline-block; width: 32px; height: 32px;
                        background-color: {color_hex}; border-radius: 6px;
                        border: 2px solid #ccc;
                    "></span>
                    <span style="font-size: 18px; font-weight: bold;">{color_name}</span>
                    <span style="
                        font-size: 14px; padding: 2px 10px; border-radius: 12px;
                        background-color: {'#d4edda' if group_pass == group_total else '#f8d7da'};
                        color: {'#155724' if group_pass == group_total else '#721c24'};
                        font-weight: 600;
                    ">{group_status}</span>
                </div>""",
                unsafe_allow_html=True,
            )

            # 해당 색상의 결과 테이블
            display_cols = [c for c in color_group.columns if c != "식별 색상"]
            group_display = color_group[display_cols].copy()

            def highlight_pass_fail(row):
                n_cols = len(row)
                styles = [""] * n_cols
                judgment_idx = row.index.get_loc("판정")
                if row["판정"] == "합격":
                    styles[judgment_idx] = "background-color: #d4edda; color: #155724; font-weight: bold"
                else:
                    styles[judgment_idx] = "background-color: #f8d7da; color: #721c24; font-weight: bold"
                return styles

            styled_group = group_display.style.apply(highlight_pass_fail, axis=1)
            st.dataframe(styled_group, use_container_width=True, hide_index=True)

        # ── 요약 통계 ────────────────────────────────────────────────────

        st.subheader("📈 요약 통계")

        de_values = results_df["Delta E"]
        pass_count = (results_df["판정"] == "합격").sum()
        fail_count = (results_df["판정"] == "불합격").sum()
        total = len(results_df)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("평균 Delta E", f"{de_values.mean():.4f}")
        with col2:
            st.metric("최대 Delta E", f"{de_values.max():.4f}")
        with col3:
            st.metric("최소 Delta E", f"{de_values.min():.4f}")
        with col4:
            st.metric("합격", f"{pass_count}/{total}", delta=None)
        with col5:
            st.metric("불합격", f"{fail_count}/{total}", delta=None)

        # Pass rate
        if total > 0:
            pass_rate = pass_count / total * 100
            st.progress(pass_rate / 100.0, text=f"합격률: {pass_rate:.1f}%")

        st.markdown(f"**사용 공식:** {formula}")

        # ── R / CR 분석 (Advanced only) ──────────────────────────────────

        if is_advanced:
            st.divider()
            st.header("📊 R / CR 분석")
            st.markdown("E-paper의 반사율(R)과 명암비(CR)를 분석합니다.")

            # Find White and Black samples from results
            white_rows = results_df[results_df["식별 색상"] == "White"]
            black_rows = results_df[results_df["식별 색상"] == "Black"]

            if white_rows.empty:
                st.warning("White 색상 샘플이 감지되지 않았습니다. R/CR 분석을 수행할 수 없습니다.")
            else:
                # Use the first White / Black sample found
                white_L = white_rows.iloc[0]["측정 L*"]

                # Approximate reflectance: R ≈ (L*/100)^2 * 100
                R_white = (white_L / 100.0) ** 2 * 100.0

                # Specs
                R_MIN = 30.0
                R_TYP = 34.0

                r_pass = "Pass" if R_white >= R_MIN else "Fail"

                r_data = {
                    "항목": ["R (White 반사율 %)"],
                    "Min Spec": [f"{R_MIN:.1f}%"],
                    "Typ Spec": [f"{R_TYP:.1f}%"],
                    "측정값": [f"{R_white:.2f}%"],
                    "White L*": [f"{white_L:.2f}"],
                    "판정": [r_pass],
                }

                if not black_rows.empty:
                    black_L = black_rows.iloc[0]["측정 L*"]
                    R_black = (black_L / 100.0) ** 2 * 100.0

                    # Contrast Ratio
                    if R_black > 0:
                        CR = R_white / R_black
                    else:
                        CR = float("inf")

                    CR_MIN = 15.0
                    CR_TYP = 22.0
                    cr_pass = "Pass" if CR >= CR_MIN else "Fail"

                    r_data["항목"].append("CR (명암비)")
                    r_data["Min Spec"].append(f"{CR_MIN:.0f}")
                    r_data["Typ Spec"].append(f"{CR_TYP:.0f}")
                    r_data["측정값"].append(f"{CR:.2f}")
                    r_data["White L*"].append(f"Black L*: {black_L:.2f}")
                    r_data["판정"].append(cr_pass)
                else:
                    st.info("Black 색상 샘플이 감지되지 않아 CR(명암비) 계산을 건너뜁니다.")

                rcr_df = pd.DataFrame(r_data)

                def highlight_rcr(row):
                    n_cols = len(row)
                    styles = [""] * n_cols
                    judgment_idx = row.index.get_loc("판정")
                    if row["판정"] == "Pass":
                        styles[judgment_idx] = "background-color: #d4edda; color: #155724; font-weight: bold"
                    else:
                        styles[judgment_idx] = "background-color: #f8d7da; color: #721c24; font-weight: bold"
                    return styles

                styled_rcr = rcr_df.style.apply(highlight_rcr, axis=1)
                st.dataframe(styled_rcr, use_container_width=True, hide_index=True)

                st.caption("R (%) ≈ (L*/100)² × 100 으로 근사 계산. CR = R_white / R_black.")

        # ── Excel 다운로드 ───────────────────────────────────────────────

        st.divider()
        st.subheader("💾 결과 다운로드")

        # Prepare export DataFrame with additional info
        export_df = results_df.copy()
        export_df["공식"] = formula

        excel_bytes = export_to_excel(export_df, sheet_name="Delta E 결과")

        st.download_button(
            label="📥 Excel 파일 다운로드",
            data=excel_bytes,
            file_name="delta_e_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
