"""공통 UI 유틸리티 - 모드 표시, 페이지 숨기기 등."""

import streamlit as st


def render_mode_header():
    """현재 모드 표시 + '모드 설정으로 돌아가기' 버튼을 페이지 상단에 렌더링합니다.

    기본 모드일 때 고급 전용 페이지를 사이드바에서 숨깁니다.
    """
    app_mode = st.session_state.get("app_mode")
    if app_mode is None:
        return

    mode_label = "기본 모드" if app_mode == "basic" else "고급 모드"
    mode_color = "#2E7D32" if app_mode == "basic" else "#1565C0"
    mode_bg = "#e8f5e9" if app_mode == "basic" else "#e3f2fd"

    col_mode, col_btn = st.columns([4, 1])
    with col_mode:
        st.markdown(
            f'<span style="background:{mode_bg}; color:{mode_color}; '
            f'padding:4px 14px; border-radius:12px; font-weight:600; font-size:14px;">'
            f'{mode_label}</span>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("모드 변경", key="_mode_switch_btn", use_container_width=True):
            st.session_state["app_mode"] = None
            # 세션 데이터 초기화
            for key in ["parsed_reference"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("app.py")

    # 기본 모드에서 고급 전용 페이지 숨기기 (CSS)
    if app_mode == "basic":
        st.markdown(
            """
            <style>
            /* 기본 모드: Color Analysis, Graphs, Feedback 페이지 숨기기 */
            [data-testid="stSidebarNav"] li:has(a[href*="Color_Analysis"]),
            [data-testid="stSidebarNav"] li:has(a[href*="Graphs"]),
            [data-testid="stSidebarNav"] li:has(a[href*="Feedback"]) {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
