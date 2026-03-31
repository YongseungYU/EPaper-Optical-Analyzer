"""피드백 페이지 - 앱 내에서 직접 피드백을 제출하면 GitHub Issue로 자동 등록됩니다."""

import sys
from pathlib import Path

import streamlit as st
import requests

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.ui_common import render_mode_header

st.set_page_config(page_title="피드백", page_icon="💬", layout="wide")

# ---------------------------------------------------------------------------
# 고급 모드 체크
# ---------------------------------------------------------------------------

if st.session_state.get('app_mode') is None:
    st.warning("먼저 홈에서 모드를 선택해 주세요.")
    st.stop()

if st.session_state.get('app_mode') != 'advanced':
    st.warning("이 페이지는 고급 모드에서만 사용할 수 있습니다.")
    st.stop()

render_mode_header()

# ---------------------------------------------------------------------------
# 비밀번호 보호
# ---------------------------------------------------------------------------

if 'feedback_authenticated' not in st.session_state:
    st.session_state['feedback_authenticated'] = False

if not st.session_state['feedback_authenticated']:
    st.title("💬 피드백")
    st.markdown("피드백 페이지에 접근하려면 비밀번호를 입력하세요.")
    password = st.text_input("비밀번호", type="password", key="feedback_pw")
    if st.button("확인"):
        if password == "tjsgod123!":
            st.session_state['feedback_authenticated'] = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

# ---------------------------------------------------------------------------
# 피드백 폼
# ---------------------------------------------------------------------------

st.title("💬 피드백")
st.markdown("앱 사용 중 개선사항이나 오류를 알려주세요. 개발팀에 자동 전달됩니다.")

st.divider()

# 카테고리 선택
category = st.selectbox(
    "피드백 유형",
    options=["기능 개선 요청", "오류/버그 신고", "UI/화면 수정", "기타"],
)

# 페이지 선택
page = st.selectbox(
    "관련 페이지",
    options=["전체/홈", "Data Upload", "Color Analysis", "Delta E", "Graphs", "기타"],
)

# 제목
title = st.text_input(
    "제목",
    placeholder="예: Delta E 판정 기준 수정 요청",
)

# 내용
body = st.text_area(
    "상세 내용",
    height=200,
    placeholder="구체적으로 어떤 변경이 필요한지 작성해 주세요...",
)

# 긴급도
priority = st.radio(
    "긴급도",
    options=["보통", "긴급"],
    horizontal=True,
)

st.divider()

if st.button("📨 피드백 제출", type="primary", use_container_width=True):
    if not title.strip():
        st.error("제목을 입력해 주세요.")
    elif not body.strip():
        st.error("내용을 입력해 주세요.")
    else:
        try:
            token = st.secrets["github"]["token"]
            repo = st.secrets["github"]["repo"]
        except Exception:
            st.error("GitHub 연동 설정이 되어 있지 않습니다. 관리자에게 문의하세요.")
            st.stop()

        labels = []
        if category == "기능 개선 요청":
            labels.append("enhancement")
        elif category == "오류/버그 신고":
            labels.append("bug")
        if priority == "긴급":
            labels.append("urgent")

        issue_title = f"[{category}] {title}"
        issue_body = (
            f"## 피드백\n\n"
            f"**유형:** {category}\n"
            f"**관련 페이지:** {page}\n"
            f"**긴급도:** {priority}\n\n"
            f"---\n\n"
            f"{body}\n\n"
            f"---\n"
            f"*앱 내 피드백 폼에서 자동 생성됨*"
        )

        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        data = {
            "title": issue_title,
            "body": issue_body,
            "labels": labels,
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 201:
            st.success("피드백이 성공적으로 전달되었습니다! 감사합니다. 😊")
            st.balloons()
        else:
            st.error(f"전송 실패 (코드: {response.status_code}). 관리자에게 문의하세요.")
