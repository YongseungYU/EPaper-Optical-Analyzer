# E-paper Optical Analyzer

I1Pro3 측정 데이터(CGATS 형식)로부터 E-paper 디스플레이의 광학 특성을 분석하는 Streamlit 기반 웹 애플리케이션입니다.

**앱 바로가기**: <https://lge-adv-dev.streamlit.app>

> LGE ID선행개발 E-paper 연구팀

---

## 개요

i1Pro3 분광 측색계로 측정한 CGATS txt 데이터를 업로드하면 다음 항목을 자동으로 계산해 보여줍니다.

- L\*a\*b\* 값에서 색상 자동 식별
- 기준값 대비 색차(Delta E, CIEDE2000)
- 색상별 합격/불합격 판정
- 색재현 영역(Color Gamut) 시각화
- 반사율(R) 및 명암비(CR) 분석
- 결과 Excel 다운로드

## 사용 모드

| 모드 | 용도 | 주요 기능 |
|------|------|----------|
| 기본 모드 | 빠른 Delta E 확인 | 데이터 입력, Delta E 계산, Excel 내보내기 |
| 고급 모드 | 전체 분석 | 데이터 누적, 색상 분석, 그래프, Gamut, R/CR, 피드백 |

## 사용 방법

1. 앱에 접속해 홈 화면에서 **기본 모드 / 고급 모드** 중 하나를 선택합니다.
2. **데이터 업로드** 페이지에서 CGATS `.txt` 파일을 업로드하거나 텍스트로 붙여넣습니다.
3. **Delta E 계산기**에서 자동 식별된 색상별 기준값 표를 확인하고, 필요하면 표 안에서 기준 L\*a\*b\* 값을 직접 수정한 뒤 계산합니다.
4. 고급 모드에서는 **색상 분석**, **그래프**, **R/CR** 결과까지 시각화로 확인할 수 있습니다.

## 기술 스택

- Python 3.10+ / Streamlit
- pandas, numpy, scipy
- plotly (인터랙티브 차트)
- openpyxl (Excel 내보내기)
- colour-science

## 로컬 실행

```bash
git clone https://github.com/YongseungYU/EPaper-Optical-Analyzer.git
cd EPaper-Optical-Analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

## 배포

- `main` 브랜치에 push 하면 Streamlit Community Cloud가 자동으로 재배포합니다.
- 운영 URL: <https://lge-adv-dev.streamlit.app>

## 프로젝트 구조

```
.
├── app.py                 # 홈 (모드 선택)
├── pages/                 # Streamlit 멀티페이지
│   ├── 1_Data_Upload.py
│   ├── 2_Color_Analysis.py
│   ├── 3_Delta_E.py
│   ├── 4_Graphs.py
│   └── 5_Feedback.py
├── core/                  # 비즈니스 로직 (순수 Python)
│   ├── parser.py          # CGATS 파서
│   ├── delta_e.py         # ΔE 공식 (CIE76 / CIE94 / CIEDE2000)
│   ├── color_utils.py     # Lab/XYZ/sRGB 변환, 색상 식별, Gamut
│   ├── export.py          # Excel 내보내기
│   └── ui_common.py       # 공용 UI 컴포넌트
├── config/                # 기본 기준 색상, 광학 스펙
├── docs/                  # 기획안, 보안 검토, 피드백 보고
├── sample_data/           # 데모용 샘플 CGATS
└── requirements.txt
```

## 피드백 / 문의

- 앱 내 **피드백** 페이지(고급 모드)에서 직접 작성하면 본 저장소의 Issue로 자동 등록됩니다.
- 또는 [Issues](https://github.com/YongseungYU/EPaper-Optical-Analyzer/issues)에 직접 등록해 주세요.

---

ⓒ 2026 LGE ID선행개발 E-paper 연구팀
