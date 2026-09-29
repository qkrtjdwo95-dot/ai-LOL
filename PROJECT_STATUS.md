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
- `TFT-MATCH-V1`로 같은 Riot ID의 TFT 경기, 배치, 기물, 특성, 증강 정보를 조회합니다. TFT도 기존 `ACCOUNT-V1` 계정 조회와 `.env` API 키를 재사용합니다.
- TFT 기물/아이템/특성/증강 이름과 아이콘은 한국어 Data Dragon 데이터를 사용하며, 로딩이 안 될 때는 원래 ID를 표시합니다.
- 지역 코드(KR, JP, NA, EUW 등)와 Riot의 지역 라우팅을 분리했습니다.
- 경기 목록에서 한 경기를 누르면 해당 소환사의 K/D/A와 구매 아이템이 아래에 펼쳐집니다.
- 챔피언과 아이템의 한국어 이름 및 아이콘은 Data Dragon의 `ko_KR` 데이터를 사용합니다. Data Dragon 데이터를 불러오지 못하면 이름은 Riot 경기 응답의 영문으로 대체되고 아이콘은 생략될 수 있습니다.
- Riot API 403, 404, 429 오류를 사용자에게 설명하는 응답으로 변환합니다.
- `.env`에서 Riot API 키를 읽습니다. 키를 코드나 프론트 파일에 넣지 않습니다.
- 증강 API는 `backend/app/data/augments.json` 파일을 읽으며 한국어/영어 이름·설명 검색과 등급 필터를 지원합니다.

## 의도적으로 아직 하지 않은 것

- PostgreSQL 접속, 경기 캐시, 검색 기록 저장은 보류했습니다. 현재 앱은 DB 없이 시작해야 합니다. `DATABASE_URL`이 기존 `.env`에 남아 있어도 현재 설정에서 사용하지 않습니다.
- `frontend/`의 React/Vite 코드는 만들어 둔 초기 스캐폴드입니다. 지금 기본 화면은 React가 아니라 `backend/app/static/index.html`에서 FastAPI가 직접 제공합니다.
- 아수라장 증강 도감은 `backend/app/data/augments.json`에서 관리합니다. 2026-09-29 기준 공개된 Patch 26.19 활성 목록 195개(실버 56, 골드 72, 프리즘 67)를 채웠습니다. Riot의 LoL API에는 전체 도감 API가 없으며, TFT 증강과 분리된 자료입니다.
- 각 항목에는 한국어/영어 이름, 등급, 출처 패치 및 링크를 기록하고 Patch 26.19 통계 상위 챔피언 6개를 추천으로 연결합니다. 효과 설명 192개는 Patch 26.17 한국어 공개 자료에서 가져왔고, Patch 26.18의 Spin To Win 변경을 반영했습니다. 설명이 확인되지 않은 3개는 미확인 상태로 표시합니다. 일부 설명에는 게임 내 수치 자리표시자가 남아 있어 최신 패치에서 다시 대조해야 합니다.
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
| `GET /api/tft/{region}/{riot_id}/matches?count=10` | Riot ID의 최근 TFT 경기와 사용 조합 조회 |

경기 응답에는 영문 챔피언 ID 이름, 한국어 표시명, 챔피언 아이콘, 7개 아이템 슬롯 ID 및 비어 있지 않은 아이템의 한국어 이름·설명·아이콘이 들어갑니다.

## 주요 파일

- `backend/app/main.py` — 화면 라우트, 상태/증강/LoL/TFT 전적 API
- `backend/app/riot.py` — Riot API 키 처리, LoL/TFT 엔드포인트 및 지역 라우팅
- `backend/app/data_dragon.py` — Data Dragon에서 한국어 LoL/TFT 이름 및 아이콘 로드
- `backend/app/static/index.html` — LoL/TFT 검색 전환, 상세 경기 정보, 증강 도감 화면
- `backend/app/data/augments.json` — 아수라장 증강 도감 195개(목록 26.19, 설명 출처 패치 별도 기록)
- `backend/scripts/sync_mayhem_augments.py` — 공개 증강 목록/설명 HTML로 도감 JSON을 갱신하는 스크립트
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

- Patch 26.19 라이브 목록과 최신 효과 설명을 대조해 데이터 차이를 보완합니다. 현재 3개 항목은 설명을 확인하지 못했고, 일부 수치가 `?`로 생략된 설명도 있습니다.
- 패치마다 라이브 목록, 등급, 효과 설명을 대조하고 출처/패치 메타데이터를 갱신합니다.

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
