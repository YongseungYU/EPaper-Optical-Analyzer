"""
E-paper Optical Analyzer - 메인 Streamlit 앱
전자종이 디스플레이의 광학 특성을 분석하는 도구입니다.
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
            **전자종이 광학 분석 도구**

            이 앱은 전자종이(E-paper) 디스플레이의
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
        st.caption("© 2026 ETRI - E-paper 연구팀")


def render_home():
    """홈 페이지 렌더링."""
    st.title("전자종이 광학 분석기")
    st.markdown("##### E-paper Optical Analyzer")

    st.divider()

    # 프로젝트 개요
    st.header("프로젝트 개요")
    st.markdown(
        """
        **E-paper Optical Analyzer**는 전자종이 디스플레이의 광학 성능을
        정량적으로 분석하기 위한 도구입니다.

        측정된 색상 데이터를 기준 색상과 비교하여 **색차(Delta E)**를 계산하고,
        디스플레이의 색 재현 품질을 평가합니다.
        """
    )

    st.divider()

    # 주요 기능 카드
    st.header("주요 기능")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("색차 분석")
        st.markdown(
            """
            - CIEDE2000 기반 색차 계산
            - CIE76 / CIE94 지원
            - 허용 임계값 설정
            - Pass/Fail 판정
            """
        )

    with col2:
        st.subheader("데이터 시각화")
        st.markdown(
            """
            - CIE L\\*a\\*b\\* 색공간 시각화
            - Delta E 분포 차트
            - 색상별 비교 그래프
            - 인터랙티브 플롯
            """
        )

    with col3:
        st.subheader("리포트 생성")
        st.markdown(
            """
            - 분석 결과 요약
            - Excel / CSV 내보내기
            - 통계 지표 제공
            - 이력 관리
            """
        )

    st.divider()

    # 빠른 시작 가이드
    st.header("빠른 시작 가이드")

    st.markdown(
        """
        1. **데이터 준비**: 측정된 색상 데이터를 Excel 또는 CSV 파일로 준비합니다.
           파일에는 L\\*, a\\*, b\\* 값이 포함되어야 합니다.

        2. **데이터 업로드**: 사이드바의 데이터 업로드 페이지에서 파일을 업로드합니다.

        3. **기준 색상 설정**: 비교할 기준 색상을 선택하거나 직접 입력합니다.
           기본 E-paper 표준 색상이 제공됩니다.

        4. **분석 실행**: Delta E 공식과 임계값을 설정한 후 분석을 실행합니다.

        5. **결과 확인**: 시각화된 결과를 확인하고 리포트를 다운로드합니다.
        """
    )

    # 현재 설정 상태 표시
    st.divider()
    st.header("현재 설정")

    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.metric(
            label="Delta E 공식",
            value=st.session_state.get("delta_e_formula", "CIEDE2000"),
        )

    with settings_col2:
        st.metric(
            label="Delta E 임계값",
            value=st.session_state.get("delta_e_threshold", 3.0),
        )

    if st.session_state.get("uploaded_data") is not None:
        st.success("데이터가 업로드되어 있습니다. 분석을 시작할 수 있습니다.")
    else:
        st.info("아직 데이터가 업로드되지 않았습니다. 데이터를 업로드해 주세요.")


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
