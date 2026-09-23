# LOL Archive — 작업 재개 안내

이 문서는 다른 작업 환경이나 새 대화에서 프로젝트를 빠르게 이어가기 위한 현재 상태와 다음 작업 정리입니다.

기준일: 2026-09-23  
프로젝트 위치: `D:\SourceBank\ai-LOL`

## 프로젝트 목표

Riot ID로 리그 오브 레전드 전적을 조회하고, 경기별 아이템 빌드와 아수라장(ARAM: Mayhem) 증강 정보를 볼 수 있는 서비스입니다.

현재 개발 순서는 **FastAPI 백엔드 우선**입니다. 기본 사용 화면은 FastAPI가 직접 제공하고, React 화면은 나중에 다시 결정합니다. PostgreSQL 연결도 지금은 보류했습니다.

## 지금까지 구현한 내용

- FastAPI 앱과 기본 한국어 화면을 만들었습니다. `/`에서 전적 검색과 증강 도감 탭을 제공합니다.
- `/docs`에는 Swagger 대화형 API 문서가 있습니다.
- Riot ID의 `게임이름#태그`를 받는 `ACCOUNT-V1` 계정 조회를 연결했습니다.
- `MATCH-V5`로 최근 경기 ID와 경기 상세 데이터를 가져옵니다.
- 지역 코드(KR, JP, NA, EUW 등)와 Riot의 지역 라우팅을 분리했습니다.
- 경기 목록에서 한 경기를 누르면 해당 소환사의 K/D/A와 구매 아이템이 아래에 펼쳐집니다.
- 챔피언과 아이템의 한국어 이름 및 아이콘은 Data Dragon의 `ko_KR` 데이터를 사용합니다. Data Dragon 데이터를 불러오지 못하면 이름은 Riot 경기 응답의 영문으로 대체되고 아이콘은 생략될 수 있습니다.
- Riot API 403, 404, 429 오류를 사용자에게 설명하는 응답으로 변환합니다.
- `.env`에서 Riot API 키를 읽습니다. 키를 코드나 프론트 파일에 넣지 않습니다.
- 증강 API는 `backend/app/data/augments.json` 파일을 읽으며 검색어와 등급 필터를 지원합니다.

## 의도적으로 아직 하지 않은 것

- PostgreSQL 접속, 경기 캐시, 검색 기록 저장은 보류했습니다. 현재 앱은 DB 없이 시작해야 합니다. `DATABASE_URL`이 기존 `.env`에 남아 있어도 현재 설정에서 사용하지 않습니다.
- `frontend/`의 React/Vite 코드는 만들어 둔 초기 스캐폴드입니다. 지금 기본 화면은 React가 아니라 `backend/app/static/index.html`에서 FastAPI가 직접 제공합니다.
- 아수라장 증강 목록은 비어 있습니다. Riot의 LoL API에서 이 모드의 전체 증강 도감을 받는 경로를 사용하지 않습니다. TFT 증강 데이터를 LoL 아수라장 증강처럼 재사용하지 않습니다.
- 경기별 참가자 정보는 응답에 있지만, 상세 화면에는 현재 검색한 소환사의 구매 아이템만 표시합니다.
- 아수라장 경기만 걸러내는 큐 분류와 필터는 아직 추가하지 않았습니다.

## 실행 방법

요구 사항: Python 3.11 이상, Riot Developer Portal의 유효한 개발 API 키. 개발 키는 24시간마다 만료됩니다.

프로젝트 루트 `D:\SourceBank\ai-LOL\.env`에 최소한 다음 값을 설정합니다. API 키 원문은 문서나 코드에 기록하지 마세요.

```env
RIOT_API_KEY=RGAPI-발급받은_키
```

PowerShell에서 실행:

```powershell
cd D:\SourceBank\ai-LOL\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

- 기본 화면: <http://localhost:8000/>
- Swagger API 문서: <http://localhost:8000/docs>
- 상태 확인: <http://localhost:8000/api/health>

현재 Windows 개발 환경에서는 `--reload`를 빼고 실행합니다. 코드 변경 후에는 서버 터미널에서 `Ctrl+C`로 종료하고 다시 시작해야 합니다. 이미 실행 중인 서버가 8000 포트를 점유하면 이전 서버를 먼저 종료하세요.

## API 요약

| 경로 | 용도 |
| --- | --- |
| `GET /api/health` | FastAPI 상태와 Riot 키 설정 여부 |
| `GET /api/regions` | 지원 지역 코드 목록 |
| `GET /api/augments?q=&tier=` | 로컬 증강 JSON 검색 |
| `GET /api/summoners/{region}/{riot_id}/matches?count=10` | Riot ID의 최근 경기 조회. Riot ID는 `이름#태그` 형식 |

경기 응답에는 영문 챔피언 ID 이름, 한국어 표시명, 챔피언 아이콘, 7개 아이템 슬롯 ID 및 비어 있지 않은 아이템의 한국어 이름·설명·아이콘이 들어갑니다.

## 주요 파일

- `backend/app/main.py` — 화면 라우트, 상태/증강/전적 API
- `backend/app/riot.py` — Riot API 키 처리, 엔드포인트 및 지역 라우팅
- `backend/app/data_dragon.py` — Data Dragon에서 최신 버전의 한국어 챔피언/아이템 데이터 로드
- `backend/app/static/index.html` — 기본 화면과 경기별 확장 아이템 목록
- `backend/app/data/augments.json` — 수동 관리하는 증강 도감 데이터(현재 빈 배열)
- `backend/app/config.py` — 설정. `.env`는 저장소 최상위에서 읽습니다.
- `backend/requirements.txt` — 현재 DB 없이 실행하는 Python 의존성
- `frontend/` — 추후 UI를 다시 결정할 때 참고할 React/Vite 초기 파일

## 다음 작업 제안

### 우선 순위 1 — 전적 상세와 게임 구분

- 실제 Riot ID로 전적 검색을 다시 해 보고 확장 행에 아이템 아이콘/한국어 이름이 표시되는지 확인합니다.
- 아이템 설명이 빈 경우 설명 표현을 보완하고, 아이템 없는 경기 및 Data Dragon 로딩 실패 화면을 다듬습니다.
- 큐 ID와 모드 정보를 조사해 아수라장 경기를 정확히 판별하고, 전적 검색에 모드 필터를 추가합니다.
- 참가자 전체 빌드가 필요한지 결정하고, 필요하면 상세 영역을 팀별로 확장합니다.

### 우선 순위 2 — 아수라장 증강 도감

- 공식 인게임에서 검증한 증강 정보를 `augments.json` 형식으로 추가합니다.
- 증강 데이터 필드(이름, 설명, 등급, 효과 유형, 패치/출처)를 확정하고, 패치별 변경 관리 방식을 정합니다.
- 확인되지 않은 효과 수치나 등급을 임의로 작성하지 않습니다.

### 우선 순위 3 — 지속성 및 정식 프론트엔드

- 저장/캐시가 필요해질 때 PostgreSQL 스키마, 마이그레이션, 만료 정책을 추가합니다. DB 접속 전까지 현재 앱을 DB 필수로 만들지 않습니다.
- 기본 화면으로 충분하지 않을 때 React/Vite를 FastAPI API에 연결하거나, 더 적합한 프론트 구조를 선택합니다.
- 공개 배포를 계획하면 Riot 제품 등록, API 키 유형, 정책/한도를 확인합니다.

## 작업 재개 시 지킬 결정 사항

1. 먼저 FastAPI와 Swagger에서 API 흐름을 확인하고, 사용자가 요청하기 전에는 디자인에 많은 시간을 쓰지 않습니다.
2. 지금 단계에서 PostgreSQL이나 Docker는 요구하지 않습니다.
3. Riot API 키와 DB 비밀번호를 출력하거나 Markdown에 복사하지 않습니다.
4. 챔피언/아이템 한국어 이름과 아이콘은 가능한 한 Data Dragon을 사용합니다.
5. 아수라장 증강은 TFT 데이터와 혼동하지 말고, 검증된 별도 카탈로그로 관리합니다.
