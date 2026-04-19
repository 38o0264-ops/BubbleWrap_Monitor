# 📦 에어캡 시장 단가 통합 모니터링 시스템

에어캡(버블랩) 시장의 업체별 단가를 **20×30 규격으로 환산**하여 통합 비교·분석하는 Streamlit 웹 대시보드입니다.

## 🎯 주요 기능

- **단가 데이터 입력**: 3개 업체 × 주력 상품별 가격 정보 관리
- **20×30 환산 최종단가**: 배송비 포함 Landed Cost를 20×30 면적 기준으로 표준화
- **비교 분석표**: 최저가 하이라이트 + 업체별 비교 테이블
- **가격 추이 차트**: Plotly 인터랙티브 선 그래프 (일별 추이)
- **크롤링 자동화**: Selenium/BeautifulSoup 확장을 위한 placeholder 구조

## 📐 핵심 수식

```
개당 실질원가 = 단가 + (박스당 배송비 ÷ 박스당 입수량)
20×30 환산 최종단가 = (개당 실질원가 ÷ (가로 × 세로)) × 600
```

> 600 = 20cm × 30cm = 600㎠ (기준 면적)

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속됩니다.

## 📁 파일 구조

```
BubbleWrap_Monitor/
├── app.py                 # Streamlit 메인 대시보드
├── crawler.py             # 크롤링 자동화 (placeholder)
├── price_history.csv      # 로컬 데이터 저장소 (자동 생성)
├── requirements.txt       # Python 의존성 목록
└── README.md              # 이 파일
```

## 📝 사용 방법

### 데이터 입력
1. 왼쪽 **사이드바**에서 회사명, 상품명, 규격, 단가 등을 입력
2. `박스당 가격`과 `20×30 환산 최종단가`가 **실시간 자동 계산**
3. **"💾 데이터 저장"** 버튼 클릭 → CSV에 저장
4. 같은 날짜/회사/상품 데이터는 자동으로 **덮어쓰기(upsert)**

### 분석 보기
- **메트릭 카드**: 최저가, 최고가, 평균, 격차 한눈에 확인
- **비교표**: 최저가 행이 초록색으로 하이라이트
- **추이 차트**: 2일 이상 데이터 입력 시 자동 표시

## 🤖 크롤링 확장 가이드

`crawler.py` 파일에 각 업체별 크롤링 로직을 구현하세요:

```python
def crawl_boxmall() -> list[dict]:
    # 1. 박스몰 사이트 접속
    # 2. 상품 정보 파싱
    # 3. dict 형태로 반환
    return [
        {
            "product": "에어캡 20x30",
            "width": 20,
            "height": 30,
            "unit_price": 15.0,
            "qty_per_box": 2000,
            "shipping_per_box": 5000,
        }
    ]
```

## 🖥️ 호스팅 (선택)

### Streamlit Cloud
1. GitHub에 코드 push
2. [share.streamlit.io](https://share.streamlit.io)에서 배포
3. `requirements.txt`가 자동으로 의존성 설치

### 로컬 서버
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## ⚙️ 기술 스택

| 구분 | 기술 |
|------|------|
| 프레임워크 | Streamlit |
| 데이터 처리 | Pandas |
| 시각화 | Plotly |
| 크롤링 (예정) | Selenium, BeautifulSoup |
| 데이터 저장 | CSV (로컬) |
