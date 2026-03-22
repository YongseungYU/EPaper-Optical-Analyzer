"""
E-paper Optical Analyzer - PyInstaller Launcher
================================================
Streamlit 앱을 실행하기 위한 런처.
일반 Python 스크립트 및 PyInstaller exe 환경 모두 지원.
"""

import os
import sys
import signal
import subprocess
import threading
import time
import webbrowser

# ---------------------------------------------------------------------------
# 1. Base path: PyInstaller frozen 모드와 일반 스크립트 모드 모두 처리
# ---------------------------------------------------------------------------

def get_base_path() -> str:
    """PyInstaller 번들 또는 일반 스크립트의 기준 경로를 반환."""
    if getattr(sys, "frozen", False):
        # PyInstaller --onefile 실행 시 임시 폴더(_MEIPASS)가 base
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = get_base_path()

# ---------------------------------------------------------------------------
# 2. Streamlit 환경 변수 설정
# ---------------------------------------------------------------------------

PORT = "8501"

def setup_env() -> dict:
    """Streamlit 실행에 필요한 환경 변수를 설정하고 반환."""
    env = os.environ.copy()

    # Streamlit headless 모드 (브라우저 자동 열기 비활성화 — 런처가 직접 연다)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = PORT
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

    # PyInstaller 환경에서 pages 디렉토리를 명시적으로 지정
    pages_dir = os.path.join(BASE_PATH, "pages")
    if os.path.isdir(pages_dir):
        env["STREAMLIT_SERVER_PAGES_DIR"] = pages_dir

    return env


# ---------------------------------------------------------------------------
# 3. 브라우저 자동 열기
# ---------------------------------------------------------------------------

def open_browser(port: str, delay: float = 2.0) -> None:
    """지정 시간 후 기본 브라우저로 앱 URL을 연다."""
    def _open():
        time.sleep(delay)
        url = f"http://localhost:{port}"
        print(f"[launcher] 브라우저를 엽니다: {url}")
        webbrowser.open(url)
    t = threading.Thread(target=_open, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# 4. Streamlit 서버 실행
# ---------------------------------------------------------------------------

def run_streamlit() -> None:
    """Streamlit 앱을 서브프로세스로 실행."""
    app_path = os.path.join(BASE_PATH, "app.py")

    if not os.path.isfile(app_path):
        print(f"[launcher] 오류: app.py를 찾을 수 없습니다 ({app_path})")
        sys.exit(1)

    env = setup_env()

    # sys.executable 을 사용해 현재(또는 번들된) Python 인터프리터로 실행
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        app_path,
        "--server.port", PORT,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]

    print(f"[launcher] E-paper Optical Analyzer 시작 (port {PORT})")
    print(f"[launcher] Base path: {BASE_PATH}")
    print(f"[launcher] Command: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        env=env,
        cwd=BASE_PATH,
    )

    return process


# ---------------------------------------------------------------------------
# 5. Graceful Shutdown
# ---------------------------------------------------------------------------

def main() -> None:
    """런처 메인: 서버 시작 → 브라우저 열기 → 종료 대기."""
    process = run_streamlit()
    open_browser(PORT)

    def _shutdown(signum, frame):
        print("\n[launcher] 종료 신호 수신, 서버를 중지합니다...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        process.wait()
    except KeyboardInterrupt:
        _shutdown(None, None)

    ret = process.returncode
    if ret != 0:
        print(f"[launcher] Streamlit이 종료 코드 {ret}(으)로 종료되었습니다.")
    sys.exit(ret or 0)


if __name__ == "__main__":
    main()
