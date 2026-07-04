# Vault 대시보드 — 설계 문서

날짜: 2026-07-04
상태: 승인됨 → 3각 리뷰(파싱 견고성 / UX·정보설계 / 유지보수·배포) 반영 개정판 v2

## 목적

Obsidian vault(희곡 글감 위키 + 독서모임 아카이브)의 구조와 트리아지 사이클 진행도를 보여주는 로컬 시각화 앱. 사용자는 글을 쓰다가 가끔 열어 **"지금 어디까지 왔나 / 다음에 뭘 할까"**를 확인한다.

핵심 맥락: 사용자는 **독서모임**(매주, 로우 데이터가 `bookclub/석촌호수책모임/`에 축적)과 **창작**(글감 → 트리아지 → 집필, `wiki/writing/`)을 함께 운영한다. 두 활동은 분리 관리하되, 글감 노트의 frontmatter `sources`가 책카드를 가리키므로 "책 → 파생 글감 → 유망★" 연결을 자동 계산할 수 있다.

## 결정 사항 요약

| 항목 | 결정 |
|---|---|
| 주 용도 | 사이클 대시보드 (1순위) |
| 형태 | 정적 사이트 — 데이터/화면 분리 (B안) |
| 데이터 전달 | `data.js` (`window.VAULT_DATA = {...}`) — `file://`과 GitHub Pages 양쪽 동작. JSON fetch는 file://에서 차단되므로 배제 |
| 차트 | ~~Chart.js vendor~~ → **순수 CSS/HTML** (리뷰 반영: 도넛=conic-gradient, 스택 바=flex, 막대=width%). 외부 의존성 0 |
| 화면 구성 | 탭 2개: **① 창작(기본 활성)** ② 독서모임 — 주 용도가 사이클 대시보드이므로 창작을 첫 화면으로 |
| 창작 탭 블록 | 다음 할 일 스트립 + 사이클 진행도 + 집필 파이프라인 칸반 + 계열별 현황표 |
| 배포 | 로컬 우선. Pages는 **마스킹 모드(`--public`) 구현 전까지 배포 금지** (하단 배포 절 참조) |
| **비목표** | 정렬·필터·검색 UI, 기간별 추이 차트, localStorage 상태 저장, 칸반 편집은 하지 않음. 상호작용은 탭 전환 / `<details>` 접이식 / obsidian:// 링크 3종뿐 |

## 아키텍처 & 파일 배치

```
vault/
├─ tools/
│  ├─ generate_data.py      # vault 스캔 → dashboard/data.js 생성 (Python 표준 라이브러리만)
│  ├─ test_generate_data.py # 파서 단위 테스트 (unittest)
│  └─ 대시보드_갱신.bat       # 더블클릭: 생성 + 브라우저 오픈 (내용은 100% ASCII)
└─ dashboard/                # 이 폴더째 복사만으로 동작하도록 상대 경로만 사용
   ├─ index.html
   ├─ app.js                 # 렌더링 로직 (data.js 읽어 DOM 생성)
   ├─ style.css
   └─ data.js                # 생성물 — 유일하게 재생성되는 파일
```

원칙:
- 스크립트의 쓰기 대상은 `dashboard/data.js` **단 하나**. `wiki/`, `bookclub/`, `script/`는 읽기 전용.
- **cwd에 절대 의존하지 않는다.** 모든 경로는 `__file__` 기준:
  ```python
  VAULT_ROOT = Path(__file__).resolve().parent.parent   # tools/의 부모
  OUTPUT = VAULT_ROOT / "dashboard" / "data.js"
  ```
- **모든 파일 I/O에 `encoding="utf-8"` 명시** (Windows 기본이 cp949라 미지정 시 읽기는 UnicodeDecodeError, 쓰기는 깨진 data.js가 됨). 읽기는 `errors="replace"` + 실패분 unparsed 수집. 스크립트 시작부에 `sys.stdout.reconfigure(encoding="utf-8")`.
- `index.html`/`app.js`/`style.css`는 한 번 만들면 데이터와 무관하게 안정.

### 대시보드_갱신.bat 표준 골격 (내용 ASCII 원칙)

```bat
@echo off
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>nul && (set "PYCMD=py -3") || (set "PYCMD=python")
%PYCMD% "%~dp0generate_data.py"
if errorlevel 1 (echo FAILED - see message above & pause & exit /b 1)
start "" "%~dp0..\dashboard\index.html"
```

- echo 메시지 포함 **내용은 전부 영문** (한글 내용은 cp949/UTF-8 어느 쪽으로 저장해도 콘솔에서 깨짐). 파일명의 한글은 무해.
- `py -3` 우선 (이 머신의 `python`은 임의 venv를 가리킴 — 실측 확인), 에러 시 `pause`로 창 유지.

## 데이터 모델 (`data.js` 스키마)

```js
window.VAULT_DATA = {
  generated: "2026-07-04 21:30",
  vaultName: "vault",          // VAULT_ROOT.name 실측 — obsidian:// 링크용, 하드코딩 금지

  nextActions: [                // "다음 할 일" 규칙 계산 결과, 최대 3건
    { text: "다음 트리아지 사이클 돌릴 때 (12편 대기)", link: null }
  ],

  bookclub: {
    rawTotal: 0,               // bookclub/석촌호수책모임/ 재귀 .md 파일 수 (정의 고정)
    deviceMapTotal: 0,         // wiki/writing/maps/*_원본_창작장치_지도.md 수
    books: [{
      title: "혼모노",
      cardPath: "wiki/bookclub/books/혼모노/00_책카드.md",
      rawNotes: 2,             // 장치 지도 sources를 교량으로 매칭, 실패 시 0
      derivedNotes: 14,        // sources가 이 책카드를 가리키는 글감 수
      stars: 2,
      lineages: ["진짜/출처", "말/작별"]   // 상위 3개
    }]
  },

  cycle: {
    stages: { triage: "done", lineage: "done", prescription: "done" },  // 회차 라벨 포함
    batches: [{ no: 9, phase: "2·3차", scored: 20, star: 1, promising: 10, merge: 9 }],
    coverage: { scored: 228, unscoredFiles: [{ title: "...", link: "..." }] }
    // unscored 수 = unscoredFiles.length 파생
  },

  pipeline: {
    columns: { "설계": [...], "대기": [...], "조립": [...], "개작": [...] },
    // 카드: { title, lineage, star: bool, link }
    mergers: [{ id: "H", title: "공동 수리 극", nextAction: "재해석 후 2부 구조 설계" }]
    // state가 아니라 nextAction — 지도의 「병합 후보 요약」 표에 상태 열이 없음 (실측)
  },

  lineages: [{
    name: "진짜/출처", carrier: "출처_확인_중인_위로",
    stars: 1, members: 9, parts: 1, state: "설계"   // carrier 없으면 null → 화면 노란 표시
  }],

  unparsed: [{ file: "...", reason: "판정 추출 실패" }]
}
```

직렬화: `json.dumps(..., ensure_ascii=False, indent=2)` + 키/리스트 순서 고정 (diff 노이즈 최소화). data.js는 커밋 대상 (단일 작성자라 충돌 없음, 클론 직후 바로 열림).

### 다음 할 일 규칙 (우선순위순, 최대 3건)

1. 미채점 ≥ 10편 → "다음 트리아지 사이클 돌릴 때 (N편 대기)"
2. 운반체 미정 계열 중 ★ 보유 → "『계열명』 운반체 지정 필요"
3. 칸반 '설계' 열에 ★ 카드 존재 → "『제목』 처방 대기"
4. 해당 없음 → "당장 할 일 없음 — 계속 쓰세요."

## 파싱 규칙

리뷰에서 실파일 전수 확인된 규칙. **파싱 실패는 예외로 죽지 않고 `unparsed` 수집** (조용한 누락 금지).

### 1. 평가 쌍둥이 (판정·계열의 1차 소스)

- **frontmatter `type: writing-note-evaluation`인 파일만** 쌍둥이로 인정 (실측 113편).
  ⚠️ `notes/*_scored.md` 204편 중 91편은 `type: writing-note`(1차 개명 원본)이고 **그중 다수가 본문에 `- 판정:` 줄을 가짐** — 파일명 글롭만으로 판별하면 이중 계상. type 판독이 필수.
- 판정 정규식 (볼드 선택, 후행 텍스트 무시): `판정[::]\s*\**\s*(유망★?|병합|보류|제외)`
  실측 변형: `**유망★**`, `유망★ (8축 만점)`, `**유망★ — 집필 대기 큐 4순위**`, `**유망** (소품 규격)`, `**유망** (재해석 조건부)` 등. 괄호 한정어는 별도 캡처(칸반 분류에 활용).
- 계열: `- 계열:` 줄에서 첫 구두점(`.` `(` `—`) 전까지. **113편 중 83편만 보유** — 부재 시 지도 배치 표로 폴백, 그래도 없으면 `lineage: null` (unparsed 아님 — 판정은 유효).

### 2. 트리아지 지도 배치 표 (1차분 + 폴백)

- ~~열 개수로 구분~~ → **성립하지 않음** (집계표 4열, 계열 보조표 3열, 배치 5는 표 4개, 배치 6은 헤더가 `후보`). 대신:
  1. `^## 배치 (\d+)` 헤더로 섹션 분할
  2. 섹션 내 표 중 **헤더 행에 `판정` 열이 있는 표만** 글감 표로 인정
  3. `판정`/`계열` 열 인덱스는 헤더 행에서 동적 탐색
  4. 배치 형식 구분은 `A1 A2 A3` 열 존재 여부
- 글감 셀: 배치 1~6은 위키링크 `[[...X_scored|제목]]`(일부 `_scored` 없음), 7~12는 플레인 스템 — 양쪽 정규화.
- 판정 셀 변형 전체: `**유망★**`, `**유망**`, `**병합**`, `**유망★(흡수)**`, `**병합(흡수)**`, `**병합(모체)**`, `**병합(원리)**`, `**유망(개작 단계)**`, `**유망★(개작/조립 단계)**`, `**진행 중**`, `**맵(생성기)**`, 무볼드 `유망`/`병합`/`유망(소품)`.
- 중복 처리: 같은 글감이 쌍둥이와 표 양쪽에 있으면 **쌍둥이 우선** (배치 5 복원 17편에서 실제 발동 확인).

### 3. 계열·병합 지도

- 형식이 최소 5종(3열 역할표 / 2열 key-value / 헤더 기형 표 / 불릿 / 본문 단락) — `### N. 이름` 헤더로 섹션 분할 후 **관대한 파싱**: 3열 표 우선, 2열은 key-value, 실패 시 해당 섹션만 unparsed.
- **병합 A~L은 말미 「병합 후보 요약」 표(4열 균일)에서만 파싱** — 본문 단락의 H/I/J 선언은 무시.
- 계열 이름 매칭: 정확 일치 금지 — 정규화(공백·`—`·`·`·`/` 통일) 후 부분 일치 (지도 `기록 — 유류품/애도` vs 표 `기록/유류품/애도` vs 쌍둥이 `진짜/출처 · 노동-분류 교차` 불일치 실측).
- 상태값: 3열 표 상태 열(`설계`/`대기`/`조립`/`개작`/`부품`/`재료`, 볼드 허용), 2열 표는 괄호에서 추출.

### 4. 책 ↔ 창작 연결

- 책카드: `wiki/bookclub/books/*/00_책카드.md` (44권 실측 — 최상위 `bookclub/`에는 books 없음, 석촌호수책모임만 있음).
- `sources` 정규화 4변형 대응: 따옴표 제거 → `[[`/`]]` 제거 → `|별칭` 절단 → `.md` 제거 후 비교. 역추적 키: `wiki/bookclub/books/<책>/00_책카드`.
- rawTotal: `bookclub/석촌호수책모임/` 재귀 `.md`만 카운트 (정의 고정 — pdf/webp 제외).
- 책별 rawNotes: 로우 파일명(`_혼모노_ 성해나.md`)과 책 폴더명(`혼모노`)이 달라 직접 매칭 불가 — `*_원본_창작장치_지도.md`의 sources(로우 경로 + 책카드 동시 보유)를 교량으로 매칭, 실패 시 0 (unparsed 아님).

### 5. 미채점 실측

`notes/*.md` 중 (쌍둥이 아님) ∧ (대응 쌍둥이 없음) ∧ (제외 목록에 없음) → unscoredFiles.
제외 목록: 지도의 「대상 아님」 섹션들(배치 1·2·3·5·6)에서 **수집** + `글감_트리아지_지도.md` 자신 상수 제외. (하드코딩 목록 금지 — 지도가 진실원)

## 화면 설계

공통:
- 상단 헤더: 제목·생성 시각·탭 버튼 2개. **창작 탭이 기본 활성.**
- 다크 톤, max-width 1200px, 반응형.
- 폰트: 웹폰트 금지(오프라인 원칙). `font-family: "Pretendard Variable", Pretendard, "Malgun Gothic", "Apple SD Gothic Neo", sans-serif`. 한글 줄바꿈 `word-break: keep-all`, 숫자 열 `font-variant-numeric: tabular-nums`. 텍스트 대비 4.5:1↑, 회색(미채굴) 3:1↑, ★는 채도 낮춘 앰버.
- obsidian:// 링크: **`location.protocol === "file:"`일 때만** 생성 (http면 일반 텍스트 — Pages에서 프로토콜 팝업 방지). `obsidian://open?vault=${data.vaultName}&file=${encodeURIComponent(path)}`.

### 탭 ① 창작 (기본)

0. **다음 할 일 스트립**: `nextActions` 최대 3건을 한 줄 카드로.
1. **사이클 진행도**: 단계 스텝퍼(1→3→2, 회차 라벨) + 커버리지 도넛(CSS conic-gradient) — 도넛 아래 "미채점 N편" 접이식 목록(클릭→obsidian://). 배치 1~12 스택 바(★앰버/유망 초록/병합 회색, flex div)는 **그 아래 보조 기록**으로 — 배치 6/7 사이 구분선 + "1차분 | 2·3차분" 캡션 (두 구간은 연속 추세가 아님).
2. **집필 파이프라인 칸반**: 4열(설계→대기→조립→개작) 고정 — 카드 0장이어도 열 유지("비어 있음" 플레이스홀더). 카드: 제목·계열·★. 하단에 병합 후보 A~L 칩(nextAction 툴팁).
3. **계열별 현황표**: ★ 1개 이상 **또는** 상태 개작·조립인 계열만 기본 표시(★순). 나머지는 `<details>` "잠자는 계열 N개 더 보기". 운반체 미정(null)은 노란 표시.
4. **풋노트**: unparsed 0건이면 렌더 안 함. 1~9건은 접이식. **≥10건은 페이지 상단 경고 배너로 승격** (파서 파손 신호).

### 탭 ② 독서모임

1. **요약 스트립** 4칸: 책 수 / 로우 데이터 수 / 원본장치 지도 수 / 창작 전환율(파생 글감 있는 책 비율)
2. **책 서가 그리드**: 책 카드 — 제목, 파생 글감 수, ★배지, 계열 태그(≤3). 파생 0은 회색(미채굴).
3. **책→창작 흐름**: 파생 수 **상위 10권** 가로 막대(CSS width%)만. 표는 없음 (서가가 전 권 담당).

### 빈 상태·에러 표시

| 상태 | 표시 |
|---|---|
| `window.VAULT_DATA` 미정의 (data.js 부재/로드 실패) | 전체 화면 안내: "데이터 없음 — `tools/대시보드_갱신.bat`을 실행하세요" (`<noscript>`/기본 DOM으로 구현 — 첫 실행 경험 좌우) |
| 칸반 열 카드 0장 | 열 유지 + "비어 있음" 플레이스홀더 |
| 미채점 0편 | 도넛 대신 "전부 채점 완료 ✓" 한 줄 |
| unparsed 0건 | 풋노트 미렌더 |
| unparsed ≥ 10건 | 상단 경고 배너 승격 |
| 필수 파일(지도 2종) 부재 | 해당 블록만 "데이터 없음", 나머지 정상 렌더 |

## 갱신·배포 플로우

- 일상: `tools/대시보드_갱신.bat` 더블클릭 또는 Claude에게 "대시보드 갱신해줘".
- 사이클 연동: 루브릭 보칙 2의 사이클 종료 단계에 "대시보드 갱신" 추가.
- Git: `tools/`+`dashboard/`(data.js 포함) 커밋. push는 요청 시.
- **Pages (조건부 미래)**: `data.js`에는 글감 제목 전부·계열 체계·병합 기획·내부 경로가 들어감 — 공개 시 **창작 기획의 목차 전체가 노출**되며 git 히스토리에 영구 잔존. 따라서 **마스킹 모드(`generate_data.py --public`: 제목→ID 마스킹, 경로 제거, 수치·구조만 유지) 구현 전까지 공개 배포 금지.** 배포 시에도 별도 공개 레포에 `dashboard/`만 push (vault 본 레포 비공개 유지).

## 테스트

1. 파서 단위 테스트 (`unittest`, 실제 vault 발췌 픽스처):
   - 배치 1~6 표 / 배치 7~12 표 / 집계·보조 표 **오탐 배제** / 쌍둥이 판정 변형 5종 / **writing-note 타입 `_scored` 파일의 판정 줄 무시** / sources 4변형 정규화 / 계열 줄 부재 폴백
2. 정합성 자체 점검: 생성 직후 합계를 기준치(총 228, ★ 33 = 1차 21 + 2·3차 12)와 대조 — 불일치 시 경고 출력 (실패 아님, 수치는 vault 성장에 따라 변함). ⚠️ 쌍둥이 수 검증은 113 기준 (106 아님 — 배치 5 복원분 17편 포함).
3. **임의 cwd 실행 테스트**: vault 밖 디렉터리에서 실행해도 동일 결과 (`__file__` 기준 검증).
4. 수동 확인: 두 탭 렌더, data.js 삭제 후 폴백 화면, obsidian:// 링크 (file://에서만), http 서빙 시 링크 비활성.

## 리뷰 반영 이력 (v2)

- 파싱: 열 개수 구분 폐기→헤더 기반, 판정 정규식 완화, type 필수 판별(이중 계상 방지), 책카드 경로 정정, mergers.state→nextAction, sources 4변형, 제외 목록 지도 수집
- UX: 창작 탭 기본, 다음 할 일 스트립, 미채점 목록화, 빈 상태 표, 계열표 접이식, 배치 차트 강등+구분선, 책 차트 상위 10권, 타이포 규칙, 비목표 명문화
- 배포: UTF-8 강제(cp949 함정), bat ASCII 골격+py -3+pause, __file__ 경로, Pages 마스킹 전제, Chart.js 제거(CSS 차트), vaultName 실측, file:// 조건부 링크, 직렬화 안정화
