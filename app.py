"""
E-paper Optical Analyzer - 메인 Streamlit 앱
E-paper 디스플레이의 광학 특성을 분석하는 도구입니다.
"""

import streamlit as st


def init_session_state():
    """세션 상태 초기화."""
    defaults = {
        "uploaded_data": None,
        "analysis_results": None,
        "reference_colors": None,
        "delta_e_formula": "CIEDE2000",
        "delta_e_threshold": 3.0,
        "app_mode": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar():
    """사이드바 네비게이션 렌더링."""
    with st.sidebar:
        st.title("📊 E-paper Optical Analyzer")
        st.divider()
        st.markdown(
            """
            **E-paper 광학 분석 도구**

            이 앱은 E-paper 디스플레이의
            광학 특성을 측정하고 분석하는 데 사용됩니다.

            ---
            **주요 기능**
            - 색차(Delta E) 분석
            - 색 재현성 평가
            - 기준 색상 비교
            - 분석 리포트 생성
            """
        )
        st.divider()
        st.caption("© 2026 LGE ID선행개발 E-paper 연구팀")


def render_home():
    """홈 페이지 렌더링."""
    st.title("E-paper Optical Analyzer")
    st.markdown("##### LGE ID선행개발 E-paper 연구팀")

    st.divider()

    current_mode = st.session_state.get("app_mode")

    # --- Mode already selected: show current mode and change button ---
    if current_mode is not None:
        mode_label = "기본 모드" if current_mode == "basic" else "고급 모드"
        st.success(f"현재 **{mode_label}**가 선택되어 있습니다. 사이드바에서 원하는 페이지로 이동하세요.")

        if current_mode == "basic":
            st.info("기본 모드: 데이터 붙여넣기 → Delta E 계산 (CIEDE2000)")
        else:
            st.info("고급 모드: 데이터 관리 + 색상 분석 + Delta E + 그래프/Gamut + 피드백")

        st.divider()
        if st.button("🔄 모드 변경", use_container_width=True):
            st.session_state["app_mode"] = None
            st.rerun()
        return

    # --- Mode selection ---
    st.header("분석 모드를 선택하세요")
    st.markdown("사용 목적에 맞는 모드를 선택하면 해당 기능 페이지로 안내됩니다.")

    st.markdown("")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div style="
                border: 2px solid #4CAF50;
                border-radius: 16px;
                padding: 30px 24px;
                text-align: center;
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                min-height: 320px;
            ">
                <h2 style="color: #2E7D32; margin-bottom: 12px;">📋 기본 모드</h2>
                <p style="font-size: 18px; color: #333; font-weight: 600;">
                    간단한 데이터 입력과 Delta E 분석
                </p>
                <hr style="border-color: #a5d6a7;">
                <p style="font-size: 15px; color: #555; text-align: left; line-height: 1.8;">
                    ✅ 데이터 붙여넣기<br>
                    ✅ Delta E 계산 (CIEDE2000)<br>
                    ✅ Pass / Fail 판정<br>
                    ✅ 빠른 결과 확인
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("기본 모드 선택", key="btn_basic", use_container_width=True, type="primary"):
            st.session_state["app_mode"] = "basic"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div style="
                border: 2px solid #1565C0;
                border-radius: 16px;
                padding: 30px 24px;
                text-align: center;
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                min-height: 320px;
            ">
                <h2 style="color: #0D47A1; margin-bottom: 12px;">🔬 고급 모드</h2>
                <p style="font-size: 18px; color: #333; font-weight: 600;">
                    전체 기능 (색상 분석, 그래프, Gamut 등)
                </p>
                <hr style="border-color: #90caf9;">
                <p style="font-size: 15px; color: #555; text-align: left; line-height: 1.8;">
                    ✅ 데이터 관리 (업로드/입력)<br>
                    ✅ 색상 분석 및 식별<br>
                    ✅ Delta E 분석<br>
                    ✅ 그래프 / Gamut 시각화<br>
                    ✅ 피드백 및 리포트
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("고급 모드 선택", key="btn_advanced", use_container_width=True, type="primary"):
            st.session_state["app_mode"] = "advanced"
            st.rerun()


def main():
    """앱 메인 함수."""
    st.set_page_config(
        page_title="E-paper Optical Analyzer",
        page_icon="📊",
        layout="wide",
    )

    init_session_state()
    render_sidebar()
    render_home()


if __name__ == "__main__":
    main()
