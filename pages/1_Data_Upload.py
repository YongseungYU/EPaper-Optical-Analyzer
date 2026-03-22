"""데이터 업로드 페이지

I1Pro3 CGATS 형식 txt 파일을 업로드하고 파싱 결과를 확인합니다.
"""

import streamlit as st
import pandas as pd
import sys
import os
import re

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.parser import parse_cgats_file, parse_cgats_string
from core.color_utils import lab_to_hex
from core.export import export_to_excel

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="데이터 업로드 - E-paper Optical Analyzer",
    page_icon="📄",
    layout="wide",
)

st.title("📄 데이터 업로드")
st.markdown("I1Pro3 측정 데이터(CGATS txt)를 업로드하거나 붙여넣어 L\\*a\\*b\\* 값을 추출합니다.")

# ---------------------------------------------------------------------------
# 세션 상태 초기화
# ---------------------------------------------------------------------------
if 'measurement_data' not in st.session_state:
    st.session_state['measurement_data'] = None
if 'file_metadata' not in st.session_state:
    st.session_state['file_metadata'] = {}
if 'uploaded_file_names' not in st.session_state:
    st.session_state['uploaded_file_names'] = []
if 'cumulative_data' not in st.session_state:
    st.session_state['cumulative_data'] = None


# ---------------------------------------------------------------------------
# 샘플 데이터 생성 함수
# ---------------------------------------------------------------------------
def generate_sample_data() -> tuple[pd.DataFrame, dict]:
    """E-paper 측정 샘플 데이터를 생성합니다 (32RS1Q 6색 스펙)."""
    sample_cgats = """CGATS.17
ORIGINATOR "i1Profiler"
DESCRIPTOR "32RS1Q E-paper Sample Measurement"
NUMBER_OF_FIELDS 5
BEGIN_DATA_FORMAT
SAMPLE_ID SAMPLE_NAME LAB_L LAB_A LAB_B
END_DATA_FORMAT
NUMBER_OF_SETS 6
BEGIN_DATA
1   "White"    65.82   -3.75    0.42
2   "Black"    12.34    6.85  -10.67
3   "Red"      27.15   40.23   29.54
4   "Yellow"   61.47  -10.82   64.31
5   "Blue"     26.78    6.32  -34.52
6   "Green"    31.56  -21.45    5.28
END_DATA"""
    return parse_cgats_string(sample_cgats)


# ---------------------------------------------------------------------------
# 복수 CGATS 블록 분리 함수
# ---------------------------------------------------------------------------
def split_cgats_blocks(text: str) -> list[str]:
    """붙여넣기 텍스트에서 복수의 CGATS 블록을 분리합니다.

    여러 CGATS 파일이 빈 줄, '---' 구분자, 또는 연속된 CGATS 헤더로
    이어진 경우를 감지하여 개별 블록으로 나눕니다.
    """
    # CGATS 헤더 위치를 찾아서 분리
    # 'CGATS' 로 시작하는 줄의 위치를 모두 찾음
    lines = text.split('\n')
    header_indices = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper().startswith('CGATS'):
            header_indices.append(i)

    if len(header_indices) <= 1:
        # 단일 블록
        return [text.strip()]

    # 여러 블록으로 분리
    blocks = []
    for idx, start in enumerate(header_indices):
        if idx + 1 < len(header_indices):
            end = header_indices[idx + 1]
            block_text = '\n'.join(lines[start:end]).strip()
        else:
            block_text = '\n'.join(lines[start:]).strip()
        if block_text:
            blocks.append(block_text)

    return blocks


# ---------------------------------------------------------------------------
# 색상 미리보기가 포함된 테이블 생성
# ---------------------------------------------------------------------------
def build_display_html(df: pd.DataFrame) -> str:
    """L*a*b* 데이터에 색상 패치를 추가한 HTML 테이블을 생성합니다."""
    # L*, a*, b* 컬럼 이름 탐색
    lab_l_col = next((c for c in df.columns if c.upper() in ('LAB_L', 'L*', 'L')), None)
    lab_a_col = next((c for c in df.columns if c.upper() in ('LAB_A', 'A*', 'A')), None)
    lab_b_col = next((c for c in df.columns if c.upper() in ('LAB_B', 'B*', 'B')), None)

    if not all([lab_l_col, lab_a_col, lab_b_col]):
        return None

    # HTML 테이블 구성
    html = """
    <style>
    .color-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
        font-family: 'Segoe UI', sans-serif;
    }
    .color-table th {
        background-color: #1f2937;
        color: white;
        padding: 10px 14px;
        text-align: left;
        border-bottom: 2px solid #374151;
    }
    .color-table th.lab-col {
        background-color: #1e40af;
    }
    .color-table td {
        padding: 8px 14px;
        border-bottom: 1px solid #e5e7eb;
    }
    .color-table tr:hover {
        background-color: #f3f4f6;
    }
    .color-patch {
        display: inline-block;
        width: 28px;
        height: 28px;
        border-radius: 4px;
        border: 1px solid #d1d5db;
        vertical-align: middle;
    }
    </style>
    <table class="color-table">
    <thead><tr>
        <th>색상 미리보기</th>
    """
    for col in df.columns:
        cls = ' class="lab-col"' if col in (lab_l_col, lab_a_col, lab_b_col) else ''
        html += f"<th{cls}>{col}</th>"
    html += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        try:
            L = float(row[lab_l_col])
            a = float(row[lab_a_col])
            b = float(row[lab_b_col])
            hex_color = lab_to_hex(L, a, b)
        except (ValueError, TypeError):
            hex_color = '#cccccc'

        html += f'<tr><td><span class="color-patch" style="background-color:{hex_color};" title="{hex_color}"></span></td>'
        for col in df.columns:
            val = row[col]
            if col in (lab_l_col, lab_a_col, lab_b_col):
                try:
                    html += f'<td style="font-weight:600;color:#1e40af;">{float(val):.2f}</td>'
                except (ValueError, TypeError):
                    html += f'<td>{val}</td>'
            else:
                html += f'<td>{val}</td>'
        html += '</tr>'

    html += "</tbody></table>"
    return html


# ---------------------------------------------------------------------------
# 메인 레이아웃
# ---------------------------------------------------------------------------

# --- 안내 ---
with st.expander("📖 사용 안내", expanded=False):
    st.markdown("""
    **지원 파일 형식**: I1Pro3 CGATS 형식 (.txt)

    **데이터 입력 방법 (택 1)**:
    1. **텍스트 붙여넣기 (권장)**: txt 파일을 메모장으로 열어 전체 복사(Ctrl+A → Ctrl+C) 후 텍스트 입력란에 붙여넣기.
       여러 파일의 데이터를 한 번에 붙여넣을 수도 있습니다.
    2. **파일 업로드**: 사내 보안으로 차단될 수 있습니다.
    3. **샘플 데이터**: 테스트용 32RS1Q 6색 데모 데이터 로드

    **누적 기능**: 붙여넣기 할 때마다 데이터가 누적됩니다. 초기화 버튼으로 리셋할 수 있습니다.
    """)

# --- 데이터 입력 방식 선택 (탭) ---
tab_paste, tab_upload, tab_sample = st.tabs([
    "📋 텍스트 붙여넣기 (권장)",
    "📁 파일 업로드 (보안 차단 시 사용 불가)",
    "🔬 샘플 데이터",
])

# --- 탭 1: 텍스트 붙여넣기 ---
with tab_paste:
    st.subheader("텍스트 붙여넣기")
    st.markdown(
        "CGATS txt 파일을 **메모장**으로 열어 "
        "**전체 선택(Ctrl+A) → 복사(Ctrl+C)** 후 아래에 붙여넣기하세요.\n\n"
        "여러 파일의 데이터를 한 번에 붙여넣을 수 있습니다 (CGATS 헤더가 여러 개이면 자동 분리)."
    )

    pasted_text = st.text_area(
        "CGATS 데이터 붙여넣기",
        height=300,
        placeholder="여기에 CGATS 데이터를 붙여넣으세요...\n\nCGATS.17\nORIGINATOR \"i1Profiler\"\n...\n\n여러 CGATS 블록을 한 번에 붙여넣을 수 있습니다.",
        key="cgats_paste_input",
    )

    if st.button("📋 붙여넣기 데이터 파싱", type="primary", use_container_width=True):
        if pasted_text and pasted_text.strip():
            try:
                blocks = split_cgats_blocks(pasted_text)
                all_paste_dfs = []
                all_paste_meta = {}

                for idx, block in enumerate(blocks):
                    source_name = f"paste_{idx + 1}"
                    block_df, block_meta = parse_cgats_string(block)
                    block_df['SOURCE_FILE'] = source_name
                    all_paste_dfs.append(block_df)
                    all_paste_meta[source_name] = block_meta

                if all_paste_dfs:
                    current_df = pd.concat(all_paste_dfs, ignore_index=True)
                    total_samples = len(current_df)

                    # 현재 데이터를 세션에 저장
                    st.session_state['measurement_data'] = current_df
                    st.session_state['file_metadata'] = all_paste_meta
                    st.session_state['uploaded_file_names'] = list(all_paste_meta.keys())

                    # 누적 데이터에 추가
                    if st.session_state['cumulative_data'] is not None:
                        st.session_state['cumulative_data'] = pd.concat(
                            [st.session_state['cumulative_data'], current_df],
                            ignore_index=True,
                        )
                    else:
                        st.session_state['cumulative_data'] = current_df.copy()

                    cumulative_count = len(st.session_state['cumulative_data'])
                    st.success(
                        f"파싱 성공! {len(blocks)}개 블록, {total_samples}개 샘플 "
                        f"(누적 총 {cumulative_count}개)"
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"파싱 실패: {e}")
                st.info("CGATS 형식이 올바른지 확인해 주세요. BEGIN_DATA_FORMAT, BEGIN_DATA 등이 포함되어야 합니다.")
        else:
            st.warning("데이터를 입력해 주세요.")

# --- 탭 2: 파일 업로드 ---
with tab_upload:
    st.subheader("파일 업로드")
    st.caption("사내 보안 정책으로 파일 업로드가 차단될 수 있습니다. 그 경우 '텍스트 붙여넣기' 탭을 이용하세요.")
    uploaded_files = st.file_uploader(
        "CGATS txt 파일을 선택하거나 여기에 드래그하세요",
        type=["txt"],
        accept_multiple_files=True,
        help="I1Pro3에서 내보낸 CGATS 형식 txt 파일을 업로드합니다.",
    )

# --- 탭 3: 샘플 데이터 ---
with tab_sample:
    st.subheader("샘플 데이터")
    st.markdown("테스트용 32RS1Q E-paper 측정 샘플 데이터(6색)를 불러옵니다.")
    if st.button("🔬 샘플 데이터 로드", use_container_width=True):
        try:
            sample_df, sample_meta = generate_sample_data()
            st.session_state['measurement_data'] = sample_df
            st.session_state['file_metadata'] = {
                'sample_data': sample_meta
            }
            st.session_state['uploaded_file_names'] = ['sample_data.txt']
            st.success("샘플 데이터가 로드되었습니다! (6개 샘플, 32RS1Q 스펙)")
            st.rerun()
        except Exception as e:
            st.error(f"샘플 데이터 로드 실패: {e}")

st.divider()

# ---------------------------------------------------------------------------
# 누적 데이터 관리 영역
# ---------------------------------------------------------------------------
cumul_col1, cumul_col2 = st.columns([1, 1])
with cumul_col1:
    cumul_count = len(st.session_state['cumulative_data']) if st.session_state['cumulative_data'] is not None else 0
    st.metric("📊 누적 데이터 수", f"{cumul_count}개")
with cumul_col2:
    if st.button("🗑️ 누적 데이터 초기화", use_container_width=True):
        st.session_state['cumulative_data'] = None
        st.session_state['measurement_data'] = None
        st.session_state['file_metadata'] = {}
        st.session_state['uploaded_file_names'] = []
        st.success("누적 데이터가 초기화되었습니다.")
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 파일 파싱 처리
# ---------------------------------------------------------------------------
if uploaded_files:
    st.subheader("파싱 결과")

    all_dfs = []
    all_metadata = {}
    file_names = []
    parse_errors = []

    progress_bar = st.progress(0, text="파일 파싱 중...")

    for i, uploaded_file in enumerate(uploaded_files):
        progress_bar.progress(
            (i + 1) / len(uploaded_files),
            text=f"파싱 중: {uploaded_file.name} ({i + 1}/{len(uploaded_files)})"
        )
        try:
            df, meta = parse_cgats_file(uploaded_file)
            # 파일명 컬럼 추가 (여러 파일 구분용)
            df['SOURCE_FILE'] = uploaded_file.name
            all_dfs.append(df)
            all_metadata[uploaded_file.name] = meta
            file_names.append(uploaded_file.name)
        except Exception as e:
            parse_errors.append((uploaded_file.name, str(e)))

    progress_bar.empty()

    # 파싱 상태 표시
    col_success, col_error = st.columns(2)
    with col_success:
        if all_dfs:
            st.success(f"{len(all_dfs)}개 파일 파싱 성공")
    with col_error:
        if parse_errors:
            st.error(f"{len(parse_errors)}개 파일 파싱 실패")
            for fname, err in parse_errors:
                st.warning(f"**{fname}**: {err}")

    # 데이터 병합 및 저장
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        st.session_state['measurement_data'] = combined_df
        st.session_state['file_metadata'] = all_metadata
        st.session_state['uploaded_file_names'] = file_names

# ---------------------------------------------------------------------------
# 데이터 미리보기 표시 (현재 데이터)
# ---------------------------------------------------------------------------
if st.session_state['measurement_data'] is not None:
    df = st.session_state['measurement_data']
    metadata = st.session_state['file_metadata']

    st.subheader("현재 데이터 미리보기")

    # --- 파일 정보 요약 ---
    info_col1, info_col2, info_col3 = st.columns(3)
    with info_col1:
        st.metric("현재 샘플 수", f"{len(df)}개")
    with info_col2:
        st.metric("소스 수", f"{len(st.session_state['uploaded_file_names'])}개")
    with info_col3:
        cumul_total = len(st.session_state['cumulative_data']) if st.session_state['cumulative_data'] is not None else 0
        st.metric("누적 데이터 수", f"{cumul_total}개")

    # 파일별 메타데이터 표시
    if metadata:
        with st.expander("파일 메타데이터 상세", expanded=False):
            for fname, meta in metadata.items():
                st.markdown(f"**{fname}**")
                meta_items = {k: v for k, v in meta.items() if k != 'COLUMNS'}
                st.json(meta_items)

    # --- 색상 패치가 포함된 HTML 테이블 ---
    st.markdown("#### 측정 데이터 (색상 미리보기 포함)")
    html_table = build_display_html(df)
    if html_table:
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("L*a*b* 컬럼을 찾을 수 없어 색상 미리보기를 표시할 수 없습니다.")

    st.divider()

    # --- Excel 다운로드 (현재 데이터) ---
    st.subheader("데이터 내보내기")

    dl_col1, dl_col2 = st.columns([1, 3])
    with dl_col1:
        try:
            excel_bytes = export_to_excel(df)
            st.download_button(
                label="📥 현재 데이터 Excel 다운로드",
                data=excel_bytes,
                file_name="epaper_measurement_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Excel 파일 생성 실패: {e}")
            st.info("openpyxl 패키지가 설치되어 있는지 확인하세요: `pip install openpyxl`")

    with dl_col2:
        st.caption("현재 파싱된 측정 데이터를 Excel 파일로 다운로드합니다.")

    # --- 누적 데이터 내보내기 ---
    st.subheader("누적 데이터 내보내기")

    if st.session_state['cumulative_data'] is not None and len(st.session_state['cumulative_data']) > 0:
        cumul_df = st.session_state['cumulative_data']
        st.info(f"누적 데이터: 총 {len(cumul_df)}개 샘플")

        dl_cumul_col1, dl_cumul_col2 = st.columns([1, 3])
        with dl_cumul_col1:
            try:
                cumul_excel_bytes = export_to_excel(cumul_df)
                st.download_button(
                    label="📥 누적 데이터 Excel 다운로드",
                    data=cumul_excel_bytes,
                    file_name="epaper_cumulative_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"누적 Excel 파일 생성 실패: {e}")
        with dl_cumul_col2:
            st.caption("지금까지 누적된 모든 측정 데이터를 하나의 Excel 파일로 다운로드합니다.")
    else:
        st.caption("아직 누적된 데이터가 없습니다. 텍스트 붙여넣기로 데이터를 추가하세요.")

else:
    # 데이터가 없을 때 안내 메시지
    st.info("위에서 파일을 업로드하거나 샘플 데이터를 로드하세요.")

    st.markdown("""
    ---
    **CGATS 파일 형식 예시:**
    ```
    CGATS.17
    ORIGINATOR "i1Profiler"
    DESCRIPTOR "i1Pro3 measurement data"
    NUMBER_OF_FIELDS 5
    BEGIN_DATA_FORMAT
    SAMPLE_ID SAMPLE_NAME LAB_L LAB_A LAB_B
    END_DATA_FORMAT
    NUMBER_OF_SETS 3
    BEGIN_DATA
    1   "White"    95.2   -0.8    2.1
    2   "Black"     5.3    0.2   -0.5
    3   "Red"      45.1   67.2   35.8
    END_DATA
    ```
    """)
