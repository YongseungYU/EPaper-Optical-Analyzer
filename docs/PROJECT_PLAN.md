# E-paper 광학 분석 Tool 기획안

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | E-paper Optical Analyzer |
| 목적 | I1Pro3 측정 데이터(txt)를 자동 파싱하여 L\*a\*b\* 색상 분석 및 Delta E 계산 |
| 사용자 | 광학 검토 담당자 (다수) |
| 기술 스택 | Python + Streamlit (웹 기반 대시보드) |
| 배포 방식 | 사내 네트워크 Streamlit 서버 or Streamlit Cloud |

## 2. 기술 스택 선정 이유: Streamlit

| 비교 항목 | Streamlit | Flask | Gradio |
|-----------|-----------|-------|--------|
| 개발 속도 | 매우 빠름 | 느림 (HTML/CSS 필요) | 빠름 |
| 데이터 분석 UI | 최적화 | 직접 구현 | ML 중심 |
| 그래프/차트 | 내장 지원 | 별도 구현 | 제한적 |
| 다중 사용자 접근 | URL 공유만으로 가능 | 가능 | 가능 |
| 파일 업로드 | 내장 위젯 | 직접 구현 | 내장 위젯 |
| 배포 난이도 | 매우 쉬움 | 보통 | 쉬움 |

**결론**: 데이터 분석 대시보드에 최적화된 **Streamlit** 채택

## 3. 핵심 기능

### 3.1 데이터 입력
- I1Pro3 CGATS 형식 txt 파일 업로드 (단일/복수)
- 드래그 앤 드롭 지원
- 샘플 데이터 제공 (데모용)

### 3.2 데이터 파싱 및 처리
- CGATS txt 파일 자동 파싱
- L\*a\*b\* 값 추출
- XYZ, 스펙트럼 데이터 추출 (있을 경우)
- 파싱 결과 테이블 표시 및 Excel 다운로드

### 3.3 색상 분석
- L\*a\*b\* 값 기반 색상 시각화 (색상 패치 미리보기)
- 색상 이름 자동 매핑 (Red, Green, Blue, Black, White 등)
- a\*b\* 색도 다이어그램 플롯

### 3.4 Delta E 계산
- 기준값(Reference) 설정 기능
  - 직접 입력 (L\*, a\*, b\*)
  - 파일에서 기준값 로드
  - 사전 정의된 표준값 선택 (sRGB white, D65 등)
- Delta E 계산 공식 지원:
  - ΔE*ab (CIE76)
  - ΔE*94 (CIE94)
  - ΔE*00 (CIEDE2000) - 기본값
- Pass/Fail 판정 (임계값 설정 가능)

### 3.5 그래프 및 시각화
- L\*a\*b\* 3D 산점도
- a\*b\* 2D 색도 다이어그램
- Delta E 바 차트 (기준값 대비)
- 스펙트럼 반사율 그래프 (데이터 있을 경우)
- 측정 이력 트렌드 그래프
- 모든 그래프 이미지 다운로드 지원

### 3.6 리포트
- 분석 결과 Excel 다운로드
- PDF 리포트 생성 (선택)

## 4. 페이지 구조

```
📊 E-paper Optical Analyzer
├── 📄 Data Upload        - 파일 업로드 및 파싱 결과 확인
├── 🎨 Color Analysis     - 색상 시각화 및 L*a*b* 분석
├── 📐 Delta E Calculator - 기준값 대비 Delta E 계산
├── 📈 Graphs             - 각종 그래프 및 차트
└── ⚙️ Settings           - 기준값 관리, 임계값 설정
```

## 5. 프로젝트 구조

```
E-paper_Project/
├── app.py                    # Streamlit 메인 앱 (멀티페이지)
├── requirements.txt          # 의존성
├── pages/
│   ├── 1_Data_Upload.py      # 데이터 업로드 페이지
│   ├── 2_Color_Analysis.py   # 색상 분석 페이지
│   ├── 3_Delta_E.py          # Delta E 계산 페이지
│   └── 4_Graphs.py           # 그래프 페이지
├── core/
│   ├── __init__.py
│   ├── parser.py             # CGATS 파일 파서
│   ├── color_utils.py        # 색상 변환 유틸리티
│   ├── delta_e.py            # Delta E 계산 엔진
│   └── export.py             # Excel/리포트 내보내기
├── config/
│   ├── reference_colors.json # 기준 색상값 설정
│   └── settings.py           # 앱 설정
├── sample_data/              # 샘플 CGATS 데이터
├── tests/                    # 테스트 코드
│   ├── test_parser.py
│   ├── test_delta_e.py
│   └── test_color_utils.py
└── docs/
    └── PROJECT_PLAN.md       # 이 기획안
```

## 6. 핵심 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| streamlit | 웹 앱 프레임워크 |
| pandas | 데이터 처리 |
| numpy | 수치 계산 |
| plotly | 인터랙티브 그래프 (3D 포함) |
| colormath | L\*a\*b\* 변환 및 Delta E 계산 검증 |
| openpyxl | Excel 내보내기 |
| colour-science | 색 과학 계산 (보조) |
| pytest | 테스트 |

## 7. I1Pro3 CGATS 데이터 형식 (예상)

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

> 실제 파일 형식은 사용자 데이터 확인 후 조정 필요

## 8. 배포 방법

### Option A: 사내 서버 배포 (추천)
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```
- 같은 네트워크의 모든 사용자가 `http://서버IP:8501` 로 접근 가능

### Option B: Streamlit Cloud (무료)
- GitHub 연동 후 자동 배포
- 외부 접근 가능 (보안 검토 필요)

### Option C: Docker 컨테이너
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 9. 구현 우선순위

| 순서 | 항목 | 중요도 |
|------|------|--------|
| 1 | CGATS 파서 | 필수 |
| 2 | L\*a\*b\* 추출 및 테이블 표시 | 필수 |
| 3 | Delta E 계산 (CIE76, CIEDE2000) | 필수 |
| 4 | Excel 내보내기 | 필수 |
| 5 | 색상 시각화 (패치, 색도도) | 높음 |
| 6 | 그래프 (바차트, 3D, 스펙트럼) | 높음 |
| 7 | 기준값 관리 (Settings) | 보통 |
| 8 | PDF 리포트 | 낮음 |
