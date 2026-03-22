"""Delta E 계산기 페이지 - E-paper Optical Analyzer."""

import json
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure project root is on sys.path for imports
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.delta_e import delta_e_cie76, delta_e_cie94, delta_e_ciede2000, batch_delta_e
from core.color_utils import lab_to_hex, get_color_name, calculate_chroma, calculate_hue
from core.export import export_to_excel

# ── 페이지 설정 ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Delta E 계산기", page_icon="📐", layout="wide")
st.title("📐 Delta E 계산기")
st.markdown("측정값과 기준값 사이의 색차(Delta E)를 계산합니다.")

# ── 데이터 확인 ─────────────────────────────────────────────────────────────

if "measurement_data" not in st.session_state or st.session_state["measurement_data"] is None:
    st.warning("⚠️ 측정 데이터가 없습니다. 먼저 **Data Upload** 페이지에서 데이터를 업로드해 주세요.")
    st.stop()

df: pd.DataFrame = st.session_state["measurement_data"]

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

# Delta E formula selection
formula = st.sidebar.radio(
    "Delta E 공식 선택",
    options=["CIEDE2000", "CIE94", "CIE76"],
    index=0,
    help="CIEDE2000이 가장 정확한 인간 시각 모델입니다.",
)

# Threshold
threshold = st.sidebar.number_input(
    "합격 기준값 (임계값)",
    min_value=0.1,
    max_value=50.0,
    value=3.0,
    step=0.5,
    help="Delta E가 이 값 이하이면 합격(Pass)으로 판정합니다.",
)

# ── 기준값 설정 ─────────────────────────────────────────────────────────────

st.header("📌 기준값(Reference) 설정")

ref_method = st.radio(
    "기준값 입력 방식",
    options=["사전 정의 기준값 불러오기", "직접 입력", "기준값 파일 업로드"],
    horizontal=True,
)

reference: dict[str, tuple[float, float, float]] = {}

if ref_method == "사전 정의 기준값 불러오기":
    # Load from config/reference_colors.json
    config_path = Path(_PROJECT_ROOT) / "config" / "reference_colors.json"
    if config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            ref_sets = json.load(f)

        set_names = list(ref_sets.keys())
        selected_set = st.selectbox("기준값 세트 선택", options=set_names)

        if selected_set:
            selected_ref = ref_sets[selected_set]
            st.info(f"📄 {selected_ref.get('description', '')}")

            colors = selected_ref.get("colors", {})
            ref_display = []
            for cname, vals in colors.items():
                rL, ra, rb = vals["L"], vals["a"], vals["b"]
                reference[cname] = (rL, ra, rb)
                hex_c = lab_to_hex(rL, ra, rb)
                ref_display.append({
                    "색상명": cname,
                    "L*": rL,
                    "a*": ra,
                    "b*": rb,
                    "미리보기": hex_c,
                })

            ref_df = pd.DataFrame(ref_display)
            st.dataframe(ref_df, use_container_width=True, hide_index=True)
    else:
        st.error("기준값 파일을 찾을 수 없습니다: config/reference_colors.json")

elif ref_method == "직접 입력":
    st.markdown("각 샘플에 대한 기준 L\\*a\\*b\\* 값을 입력하세요.")

    # Get sample names from measurement data
    if name_col:
        sample_names = df[name_col].unique().tolist()
    else:
        sample_names = [f"Sample {i + 1}" for i in range(len(df))]

    for sname in sample_names:
        st.markdown(f"**{sname}**")
        c1, c2, c3 = st.columns(3)
        with c1:
            ref_L = st.number_input(
                f"L* ({sname})",
                min_value=0.0, max_value=100.0, value=50.0,
                step=0.1, key=f"ref_L_{sname}",
            )
        with c2:
            ref_a = st.number_input(
                f"a* ({sname})",
                min_value=-128.0, max_value=128.0, value=0.0,
                step=0.1, key=f"ref_a_{sname}",
            )
        with c3:
            ref_b = st.number_input(
                f"b* ({sname})",
                min_value=-128.0, max_value=128.0, value=0.0,
                step=0.1, key=f"ref_b_{sname}",
            )
        reference[str(sname)] = (ref_L, ref_a, ref_b)

elif ref_method == "기준값 파일 업로드":
    st.markdown(
        "기준값 파일을 업로드하세요. "
        "지원 형식: **JSON** (reference_colors.json과 동일 형식) 또는 "
        "**Excel/CSV** (색상명, L\\*, a\\*, b\\* 컬럼 포함)"
    )
    uploaded_ref = st.file_uploader(
        "기준값 파일 선택",
        type=["json", "csv", "xlsx"],
        key="ref_file_upload",
    )

    if uploaded_ref is not None:
        try:
            if uploaded_ref.name.endswith(".json"):
                ref_json = json.load(uploaded_ref)
                # Support both flat and nested format
                if any("colors" in v for v in ref_json.values() if isinstance(v, dict)):
                    # Nested format: pick first set or let user choose
                    set_keys = list(ref_json.keys())
                    chosen = st.selectbox("세트 선택", set_keys, key="upload_set")
                    colors = ref_json[chosen].get("colors", ref_json[chosen])
                    for cname, vals in colors.items():
                        reference[cname] = (vals["L"], vals["a"], vals["b"])
                else:
                    # Flat format: {"ColorName": {"L": ..., "a": ..., "b": ...}}
                    for cname, vals in ref_json.items():
                        reference[cname] = (vals["L"], vals["a"], vals["b"])

            elif uploaded_ref.name.endswith(".csv"):
                ref_csv = pd.read_csv(uploaded_ref)
                for _, row in ref_csv.iterrows():
                    cname = str(row.iloc[0])
                    reference[cname] = (float(row["L"]), float(row["a"]), float(row["b"]))

            elif uploaded_ref.name.endswith(".xlsx"):
                ref_xlsx = pd.read_excel(uploaded_ref)
                for _, row in ref_xlsx.iterrows():
                    cname = str(row.iloc[0])
                    reference[cname] = (float(row["L"]), float(row["a"]), float(row["b"]))

            st.success(f"✅ {len(reference)}개 기준값을 불러왔습니다.")
        except Exception as e:
            st.error(f"파일 처리 오류: {e}")

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
    # Select the formula function
    func_map = {
        "CIE76": delta_e_cie76,
        "CIE94": delta_e_cie94,
        "CIEDE2000": delta_e_ciede2000,
    }
    calc_fn = func_map[formula]

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
        pass_fail = "합격" if de_value <= threshold else "불합격"

        results.append({
            "샘플명": sample_name,
            "측정 L*": round(mL, 2),
            "측정 a*": round(ma, 2),
            "측정 b*": round(mb, 2),
            "기준 L*": round(rL, 2),
            "기준 a*": round(ra, 2),
            "기준 b*": round(rb, 2),
            "Delta E": round(de_value, 4),
            "판정": pass_fail,
        })

    if not results:
        st.warning("일치하는 기준값이 없어 계산할 수 없습니다. 샘플명과 기준값 색상명이 일치하는지 확인해 주세요.")
    else:
        results_df = pd.DataFrame(results)

        # Store in session state
        st.session_state["delta_e_results"] = results_df

        # Display styled table with pass/fail colors
        def highlight_pass_fail(row):
            if row["판정"] == "합격":
                return [""] * (len(row) - 1) + ["background-color: #d4edda; color: #155724; font-weight: bold"]
            else:
                return [""] * (len(row) - 1) + ["background-color: #f8d7da; color: #721c24; font-weight: bold"]

        styled_df = results_df.style.apply(highlight_pass_fail, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

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

        st.markdown(f"**사용 공식:** {formula} | **임계값:** {threshold}")

        # ── Excel 다운로드 ───────────────────────────────────────────────

        st.divider()
        st.subheader("💾 결과 다운로드")

        # Prepare export DataFrame with additional info
        export_df = results_df.copy()
        export_df["공식"] = formula
        export_df["임계값"] = threshold

        excel_bytes = export_to_excel(export_df, sheet_name="Delta E 결과")

        st.download_button(
            label="📥 Excel 파일 다운로드",
            data=excel_bytes,
            file_name="delta_e_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
