# Vault 대시보드 — 설계 문서

날짜: 2026-07-04
상태: 승인됨 (사용자 확인)

## 목적

Obsidian vault(희곡 글감 위키 + 독서모임 아카이브)의 구조와 트리아지 사이클 진행도를 보여주는 로컬 시각화 앱. 사용자는 글을 쓰다가 가끔 열어 "지금 어디까지 왔나 / 다음에 뭘 할까"를 확인한다.

핵심 맥락: 사용자는 **독서모임**(매주, 로우 데이터가 `bookclub/`에 축적)과 **창작**(글감 → 트리아지 → 집필, `wiki/writing/`)을 함께 운영한다. 두 활동은 분리 관리하되, 글감 노트의 frontmatter `sources`가 책카드를 가리키므로 "책 → 파생 글감 → 유망★" 연결을 자동 계산할 수 있다.

## 결정 사항 요약

| 항목 | 결정 |
|---|---|
| 주 용도 | 사이클 대시보드 (1순위) |
| 형태 | 정적 사이트 — 데이터/화면 분리 (B안) |
| 데이터 전달 | `data.js` (`window.VAULT_DATA = {...}`) — `file://`과 GitHub Pages 양쪽 동작. JSON fetch는 file://에서 차단되므로 배제 |
| 차트 | Chart.js 로컬 사본 (vendor) — 오프라인·Pages 양쪽 동작 |
| 화면 구성 | 탭 2개: ① 독서모임 ② 창작 |
| 창작 탭 블록 | 사이클 진행도 + 집필 파이프라인 칸반 + 계열별 현황표 (선택됨). 결정 대기 목록은 제외 |
| 배포 | 로컬 우선. Pages는 나중에 별도 공개 레포로 `dashboard/`만 분리 push (vault 레포는 비공개 유지 — 글감 노출 방지) |

## 아키텍처 & 파일 배치

```
vault/
├─ tools/
│  ├─ generate_data.py      # vault 스캔 → dashboard/data.js 생성 (Python 표준 라이브러리만)
│  ├─ test_generate_data.py # 파서 단위 테스트 (unittest)
│  └─ 대시보드_갱신.bat       # 더블클릭: 생성 + 브라우저 오픈
└─ dashboard/                # 이 폴더째 Pages 루트로 쓸 수 있게 상대 경로만 사용
   ├─ index.html
   ├─ app.js                 # 렌더링 로직 (data.js 읽어 DOM/차트 생성)
   ├─ style.css
   ├─ vendor/chart.umd.js    # Chart.js 로컬 사본
   └─ data.js                # 생성물 — 유일하게 재생성되는 파일
```

원칙:
- 스크립트의 쓰기 대상은 `dashboard/data.js` **단 하나** (경로 하드코딩). `wiki/`, `bookclub/`, `script/`는 읽기 전용.
- `index.html`/`app.js`/`style.css`는 한 번 만들면 데이터와 무관하게 안정.

## 데이터 모델 (`data.js` 스키마)

```js
window.VAULT_DATA = {
  generated: "2026-07-04 21:30",

  bookclub: {
    rawTotal: 0,              // bookclub/석촌호수책모임/ 등 로우 파일 수
    deviceMapTotal: 0,        // wiki/writing/maps/*_원본_창작장치_지도.md 수
    books: [{
      title: "혼모노",
      cardPath: "wiki/bookclub/books/혼모노/00_책카드.md",
      rawNotes: 2,            // 이 책 관련 로우 자료 수
      derivedNotes: 14,       // sources가 이 책카드를 가리키는 글감 수
      stars: 2,               // 그중 유망★
      lineages: ["진짜/출처", "말/작별"]   // 상위 3개
    }]
  },

  cycle: {
    stages: { triage: "done", lineage: "done", prescription: "done" },  // 사이클 회차 라벨 포함
    batches: [{ no: 9, scored: 20, star: 1, promising: 10, merge: 9 }], // 1~12
    coverage: { scored: 228, unscored: 3 }   // unscored는 실행 시점 실측
  },

  pipeline: {
    columns: { "설계": [...], "대기": [...], "조립": [...], "개작": [...] },
    // 카드: { title, lineage, star: bool, link }
    mergers: [{ id: "H", title: "공동 수리 극", state: "처방" }]  // A~L
  },

  lineages: [{
    name: "진짜/출처", carrier: "출처_확인_중인_위로",
    stars: 1, members: 9, parts: 1, state: "설계"
  }],

  unparsed: [{ file: "...", reason: "판정 추출 실패" }]
}
```

## 파싱 규칙

| 소스 | 추출 대상 | 방법 |
|---|---|---|
| `notes/*_scored.md` (type: writing-note-evaluation) | 판정·계열 (2·3차 106편) | 본문 정규식: `판정: \*\*(유망★?|병합|보류|제외)`, `계열: (.+)` |
| 트리아지 지도 배치 표 | 1차분 122편 판정·계열 | 표 행 파싱 — 배치 1~6(6열)과 7~12(4열)는 열 개수로 구분 |
| 계열·병합 지도 | 계열/운반체/부품, 상태값(개작·조립·대기·설계), 대기 큐, 병합 A~L | 섹션 헤더 + 표/리스트 파싱 |
| notes frontmatter `sources` | 책 → 글감 역추적 | YAML frontmatter의 책카드 경로 매칭 |
| `bookclub/books/*/00_책카드.md` | 책 서가 목록 | 디렉터리 스캔 |
| `bookclub/` 로우 파일, `wiki/writing/maps/*지도*` | 자료 축적 카운트 | 디렉터리 스캔 |

중복 처리: 같은 글감이 쌍둥이와 지도 표에 모두 있으면 **쌍둥이 우선**.
미채점 실측: `notes/*.md` 중 (쌍둥이 아님) ∧ (쌍둥이 없음) ∧ (메타/기법 노트 제외 목록에 없음) → unscored.

## 화면 설계

공통: 상단 헤더(제목·생성 시각·탭 버튼 2개), 다크 톤, max-width 1200px, 반응형. 노트·책 제목 클릭 → `obsidian://open?vault=vault&file=...` (Pages에서는 무동작·무해).

### 탭 ① 독서모임
1. 요약 스트립 4칸: 책 수 / 로우 데이터 수 / 원본장치 지도 수 / 창작 전환율(파생 글감 있는 책 비율)
2. 책 서가 그리드: 책 카드 — 제목, 파생 글감 수, ★배지, 계열 태그(≤3). 파생 0인 책은 회색(미채굴).
3. 책→창작 흐름: 파생 수 상위 정렬 표(책|로우|글감|★|대표 계열) + 가로 막대 차트

### 탭 ② 창작
1. 사이클 진행도: 단계 스텝퍼(1→3→2, 회차 라벨) + 배치 1~12 스택 바(★금/유망 초록/병합 회색) + 커버리지 도넛(채점/미채점 — 미채점 증가가 "다음 사이클" 신호)
2. 집필 파이프라인 칸반: 4열(설계→대기→조립→개작) + 병합 후보 A~L 칩 행. 카드: 제목·계열·★
3. 계열별 현황표: 계열 × (운반체|★|구성원|부품|상태), ★순 정렬, 운반체 미정은 노란 표시
4. 풋노트: `분류 안 됨 N건` 접이식 목록

## 갱신·배포 플로우

- 일상: `tools/대시보드_갱신.bat` 더블클릭 (생성+브라우저 오픈) 또는 Claude에게 "대시보드 갱신해줘"
- 사이클 연동: 루브릭 보칙 2의 사이클 종료 단계에 "대시보드 갱신" 추가
- Git: `tools/`+`dashboard/`(data.js 포함) 커밋. push는 요청 시.
- Pages (미래): 별도 공개 레포에 `dashboard/`만 push → Pages 활성화. vault 본 레포는 비공개 유지. 상대 경로만 사용해 폴더 복사만으로 동작 보장.

## 에러 처리

- **조용한 누락 금지**: 파싱 실패는 `unparsed`로 수집해 화면에 표시. 예외로 죽지 않음.
- 필수 파일 부재 시 해당 블록만 "데이터 없음", 나머지 정상 렌더.
- 인코딩 UTF-8 고정, 한글 파일명·공백 경로 대응.
- vault 파일 무수정 보장 (쓰기 경로 1개 하드코딩).

## 테스트

1. 파서 단위 테스트 (`unittest`): 배치 1~6 표 / 배치 7~12 표 / 쌍둥이 추출 / sources 역추적 — 실제 vault 파일 발췌 픽스처
2. 정합성 자체 점검: 생성 직후 합계를 알려진 수치(총 228, ★ 33)와 대조, 불일치 시 경고 출력(실패는 아님 — 수치는 vault 성장에 따라 변함)
3. 수동 확인: 두 탭 렌더, obsidian:// 링크, 상대 경로 검사
