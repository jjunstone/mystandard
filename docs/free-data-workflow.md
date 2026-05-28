# 무료 데이터 연결 워크플로

이 대시보드는 유료 실시간 피드 없이도 장마감 일별 데이터로 돌아가도록 만들었다.

## 매일 할 일: 통합 방식

가장 편한 방식은 아래 1개 명령이다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/update_dashboard.ps1
```

이 명령은 다음을 한 번에 처리한다.

1. `db/free_inputs/*.csv`를 읽는다.
2. `db/eod_snapshot.json`을 새로 만든다.
3. 대시보드 서버가 꺼져 있으면 `http://127.0.0.1:8000/`으로 띄운다.

대시보드가 이미 켜져 있으면 화면 위쪽의 `IMPORT CSV` 버튼을 누르면 된다. 이 버튼은 서버 안에서 `scripts/import_free_data.py`를 실행한 것과 같은 효과다.

## 매일 할 일: 수동 방식

1. KRX 정보데이터시스템에서 필요한 표를 엑셀/CSV로 내려받는다.
2. 숫자를 `db/free_inputs/*.csv` 형식에 맞춰 붙여넣는다.
3. 아래 명령으로 `db/eod_snapshot.json`을 만든다.

```powershell
python scripts/import_free_data.py
```

Python 명령이 잡히지 않으면 이 환경에서는 아래처럼 실행할 수 있다.

```powershell
C:\Users\happy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts/import_free_data.py
```

4. 대시보드를 새로고침한다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_dashboard.ps1
```

## KRX에서 구체적으로 받을 메뉴

KRX Data Marketplace: <https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd>

### A. indices.csv

`db/free_inputs/indices.csv`에 넣는다.

| 필요한 값 | KRX 메뉴 | 넣을 컬럼 |
| --- | --- | --- |
| KOSPI, KOSPI200 | 통계 > 기본 통계 > 지수 > 주가지수 > 전체지수 시세 | `kospi`, `kospi_change`, `kospi_change_pct`, `kospi200`, `kospi200_change`, `kospi200_change_pct` |
| VKOSPI | 통계 > 기본 통계 > 지수 > 파생 및 기타지수 > 전체지수 시세 | `vkospi`, `vkospi_change` |
| basis | 통계 > 기본 통계 > 파생상품 > 세부안내 > 베이시스 추이(선물) | `basis` |

USD/KRW는 KRX 필수값이 아니다. 무료로 쓰려면 네이버/증권사/한국은행 화면 값을 수동 입력하거나 0으로 둬도 된다.

### B. investors.csv

`db/free_inputs/investors.csv`에 넣는다.

| 필요한 값 | KRX 메뉴 | 넣을 컬럼 |
| --- | --- | --- |
| 외국인/기관/개인 현물 순매수 | 통계 > 기본 통계 > 주식 > 거래실적 > 투자자별 거래실적 | `spot_net_eok` |
| 외국인/기관/개인 KOSPI200 선물 순매수 | 통계 > 기본 통계 > 파생상품 > 거래실적 > 투자자별 거래실적 | `futures_net_contracts` |
| 선물 5일 누적 | 위 화면에서 최근 5영업일 값을 더함 | `futures_cum_5d` |
| 옵션 투자자 수급 | 통계 > 기본 통계 > 파생상품 > 거래실적 > 투자자별 거래실적 | `call_net_contracts`, `put_net_contracts`, `option_premium_eok` |

KRX 화면에서 콜/풋이 분리되지 않으면 옵션 수급은 0으로 둬도 된다. 이 경우 대시보드는 옵션 투자자 수급 대신 행사가별 OI/PCR 비중을 더 크게 본다.

금액 단위 주의:

- `spot_net_eok`, `option_premium_eok`은 억원 단위다.
- KRX 화면이 백만원 단위라면 `백만원 / 100 = 억원`으로 바꿔서 넣는다.
- KRX 화면이 원 단위라면 `원 / 100,000,000 = 억원`으로 바꿔서 넣는다.

### C. options.csv

`db/free_inputs/options.csv`에 넣는다.

| 필요한 값 | KRX 메뉴 | 넣을 컬럼 |
| --- | --- | --- |
| 행사가별 콜/풋 OI, 거래량 | 통계 > 기본 통계 > 파생상품 > 세부안내 > 행사가격/만기별 가격표(옵션) | `strike`, `call_oi`, `put_oi`, `call_volume`, `put_volume` |
| OI 증감 | 같은 화면에 증감 컬럼이 있으면 사용. 없으면 전일 OI와 비교 계산 | `call_delta`, `put_delta` |

대체 메뉴:

- 통계 > 기본 통계 > 파생상품 > 종목시세 > 전종목 시세
- 여기서 KOSPI200 옵션 최근월물을 내려받고, 종목명을 기준으로 콜/풋과 행사가를 나눠도 된다.

### D. leaders.csv

선택 사항이다. 없어도 대시보드는 돌아간다.

| 필요한 값 | KRX 메뉴 | 넣을 컬럼 |
| --- | --- | --- |
| 주도주/주도섹터 | 통계 > 기본 통계 > 주식 > 종목시세 > 전종목 등락률 | `name`, `sector`, `change_pct` |

## 필요한 무료 데이터

### 1. 지수 기준값

파일: `db/free_inputs/indices.csv`

- KOSPI
- KOSPI200
- VKOSPI, 없으면 0 가능
- basis, 없으면 0 가능
- USD/KRW, 없으면 0 가능

### 2. 투자자별 수급

파일: `db/free_inputs/investors.csv`

- 외국인/기관/개인 현물 순매수
- 외국인/기관/개인 KOSPI200 선물 순매수
- 5일 누적 선물 순매수
- 옵션 콜/풋 순매수, 없으면 0 가능

현물 금액은 `spot_net_eok`에 억원 단위로 넣는다.

### 3. 옵션 미결제약정

파일: `db/free_inputs/options.csv`

- 행사가
- 콜 미결제약정
- 풋 미결제약정
- 콜/풋 미결제약정 증감
- 콜/풋 거래량

이 데이터가 콜벽, 풋벽, Max Pain, OI P/C 계산의 핵심이다.

## 무료 소스

- KRX Data Marketplace / 정보데이터시스템: 투자자별 매매동향, KOSPI200 옵션, 선물/옵션 일별 정보
- 증권사 HTS/MTS 무료 화면: 투자자별 선물/옵션 매매동향과 미결제약정 확인용

무료 데이터는 실시간/자동 API보다 메뉴명과 컬럼명이 자주 바뀐다. 그래서 이 프로젝트는 먼저 CSV 템플릿을 안정적인 입력 포맷으로 두고, 그 뒤 자동 수집기를 붙일 수 있게 해두었다.

## 크롤링 자동화는 어디까지 가능한가

가능하다. 다만 무료 사이트 자동화는 3단계로 나누는 편이 안전하다.

### 1단계: 다운로드만 자동화

브라우저 자동화로 KRX 페이지를 열고, 날짜/상품을 선택하고, 다운로드 버튼을 누르게 만든다.

장점:

- 사람이 하던 클릭을 줄일 수 있다.
- 사이트 내부 API 구조를 몰라도 된다.

단점:

- KRX 화면 구조나 버튼명이 바뀌면 자동화가 깨질 수 있다.
- 다운로드 파일의 컬럼명이 바뀌면 변환기를 조금 고쳐야 한다.

### 2단계: 다운로드 폴더 감시 + 자동 변환

KRX에서 받은 파일을 `downloads/krx/` 같은 폴더에 저장하면, 스크립트가 파일명을 보고 `db/free_inputs/*.csv`로 변환한다.

예:

```text
downloads/krx/index.csv       -> db/free_inputs/indices.csv
downloads/krx/investor.csv    -> db/free_inputs/investors.csv
downloads/krx/options.csv     -> db/free_inputs/options.csv
```

### 3단계: KRX 내부 JSON 요청 직접 호출

가장 자동화 수준이 높지만, KRX 내부 요청 파라미터와 OTP 흐름이 바뀌면 자주 깨질 수 있다. 개인 로컬 분석용으로만 쓰고, 과도한 반복 요청은 피해야 한다.

## 추천 자동화 순서

1. 지금처럼 CSV 템플릿을 먼저 안정화한다.
2. `IMPORT CSV` 버튼으로 대시보드 안에서 변환까지 끝낸다.
3. 그 다음 KRX 다운로드 자동화를 붙인다.
4. 마지막으로 필요할 때만 내부 JSON 요청 자동화를 검토한다.

자동화 소스 정의 초안은 `config/free_sources.example.json`에 있다.
