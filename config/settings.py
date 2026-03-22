"""
E-paper Optical Analyzer 설정 모듈.
분석에 사용되는 기본값과 상수를 정의합니다.
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Delta E 설정
# ---------------------------------------------------------------------------

# 지원하는 Delta E 공식 목록
DELTA_E_FORMULAS = ["CIE76", "CIE94", "CIEDE2000"]

# 기본 Delta E 공식
DEFAULT_DELTA_E_FORMULA = "CIEDE2000"

# 기본 Delta E 임계값 (이 값 이하이면 Pass)
DEFAULT_DELTA_E_THRESHOLD = 3.0

# ---------------------------------------------------------------------------
# 색 허용 오차 (Color Tolerance) 설정
# ---------------------------------------------------------------------------

COLOR_TOLERANCE = {
    # Delta E 기준 등급 (CIEDE2000 기준)
    "excellent": 1.0,   # 거의 감지 불가
    "good": 2.0,        # 근접 관찰 시 감지 가능
    "acceptable": 3.5,  # 일반 관찰 시 감지 가능
    "marginal": 5.0,    # 명확히 인지 가능
    "poor": 10.0,       # 큰 색차
}

# ---------------------------------------------------------------------------
# 기본 기준 색상 (CIE L*a*b*)
# ---------------------------------------------------------------------------

DEFAULT_REFERENCE_COLORS = {
    "White":  {"L": 95.0, "a": -0.5, "b": 2.0},
    "Black":  {"L": 5.0,  "a": 0.0,  "b": 0.0},
    "Red":    {"L": 45.0, "a": 65.0, "b": 35.0},
    "Green":  {"L": 50.0, "a": -50.0, "b": 30.0},
    "Blue":   {"L": 30.0, "a": 20.0, "b": -50.0},
    "Yellow": {"L": 85.0, "a": -5.0, "b": 80.0},
    "Orange": {"L": 60.0, "a": 45.0, "b": 60.0},
}

# ---------------------------------------------------------------------------
# 파일 경로
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).resolve().parent
REFERENCE_COLORS_PATH = _CONFIG_DIR / "reference_colors.json"

# ---------------------------------------------------------------------------
# 유틸리티 함수
# ---------------------------------------------------------------------------


def load_reference_colors(path: Path | None = None) -> dict:
    """JSON 파일에서 기준 색상 데이터를 로드합니다.

    Parameters
    ----------
    path : Path | None
        JSON 파일 경로. None이면 기본 경로를 사용합니다.

    Returns
    -------
    dict
        기준 색상 딕셔너리. 파일이 없으면 기본값을 반환합니다.
    """
    target = path or REFERENCE_COLORS_PATH
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"E-paper Standard": DEFAULT_REFERENCE_COLORS}
