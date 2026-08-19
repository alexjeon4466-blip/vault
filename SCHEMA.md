# LLM Wiki v2 Schema — 북클럽 × 희곡 창작 순환 장치

> 이 vault는 읽은 책을 정리하는 곳이 아니라, 매달 세 권씩 쌓이는 강독의 에너지와 단막극을 계속 고치고 투고하는 창작의 에너지를 서로 순환시키는 장치다.

## 1. 목적

이 위키의 목적은 네 가지다.

1. **휘발성 방지** — 강독 준비 과정에서 생긴 깊은 이해를 오래 붙잡는다.
2. **책 사이 연결 발견** — 전혀 관련 없어 보이는 책들이 공유하는 질문·정서·사유의 선을 드러낸다.
3. **창작으로 순환** — 반복 질문이 희곡의 주제, 장면 이미지, 사건 설계, 퇴고 감각으로 돌아오게 한다.
4. **콘텐츠화 기반** — 강의형 유튜브/팟캐스트/발제문으로 재가공 가능한 재료를 남긴다.

## 2. 핵심 원칙

- 기본 언어는 한국어다.
- 문체는 사용자가 실제 강독에서 말할 법한 구어체에 가깝게 쓴다.
- 논문식 정리보다 "책을 읽은 사람에게 다시 설명하는 강의형 문장"을 우선한다.
- 줄거리 요약보다 **핵심 질문, 내 해석, 오래 남는 장면, 책 사이 연결**을 우선한다.
- AI는 적극적으로 연결과 가설을 제안해도 된다. 단, `내 해석`과 `AI 가설`을 반드시 구분한다.
- 원본 자료(`bookclub/`, `script/`)는 읽기 전용이다. 이동/삭제/덮어쓰기 금지.
- 기존 v1 위키는 `_archive/wiki_v1/`에 보존한다.

## 3. 주요 폴더

```text
wiki/
  _inbox/            # 빠른 캡처와 Web Clipper 자료의 임시 승격 대기실.
    quick-captures/  # 갑자기 떠오른 문장, 장면감, Hermes에게 던지는 짧은 조각.
    web-clips/       # 기사/트윗/인터뷰/웹 문장. URL과 핵심 문장 우선.
    raw-ideas/       # 아직 질문형 노트나 창작 노트로 승격하기 애매한 글감 원석.
    to-triage/       # 분류는 되었지만 승격/폐기 판정이 남은 항목.
  bookclub/
    books/           # 책별 카드. 한 권을 다시 붙잡는 기억 장치.
    exhibitions/     # 전시별 노트. 관람 기억과 설치·해설·제도 질문을 한 장으로 붙잡는다.
    authors/         # 작가론이 반복적으로 중요할 때.
    themes/          # 책모임 안에서만 유효한 주제.
    reading-flow/    # 장기 독서 흐름, 월별/연도별 지도.
    decisions/       # 책모임/강독/비교 강의 관련 결정 노트.
  writing/
    plays/           # 희곡별 작품카드.
    revisions/       # 버전 비교와 퇴고 기록.
    aesthetics/      # 내 희곡의 반복 미학/장면 감각.
    contest/         # 신춘문예 투고, 당선작 분석, 심사 기준.
    references/      # 기성 희곡, 연극론, 작법 자료.
    seeds/           # 글감 채집의 역할별 장기 정본.
      harvests/      # 회차 범위·접근·수율 정본과 A1 전건 원문 열람 정본.
      notes/         # A1 pass 뒤 비식별화한 사용자 미선택 개별 글감.
    decisions/       # 희곡/집필/퇴고/투고 관련 결정 노트.
  shared/
    questions/       # 핵심. 책과 책, 책과 희곡을 잇는 질문형 노트.
    themes/          # 질문보다 주제명이 더 적합할 때만.
    emotions/        # 정서별 연결.
    maps/            # 연결 지도.
    decisions/       # 공통 결정 노트.
    reviews/         # 작업 묶음 리뷰.
      weekly/        # 주간 리뷰. 다음 작업의 압축 출발점.

  lecture-scripts/   # 강독 대본 재정리.
  youtube-scripts/   # 유튜브 대본.
  podcast-scripts/   # 팟캐스트 대본.
  reports/           # 점검/분석 리포트.
_templates/          # Obsidian 템플릿.
```

## 4. 문서 타입

## 4.0 타입 레지스트리 (2026-08-20 신설)

> **왜 신설했나.** `type`이 닫힌 enum으로 선언돼 있었으나 실사용은 **47종이 미선언 상태**였고 그중 둘(`writing-note` 1,067건 · `writing-note-evaluation` 896건)이 vault 최대 문서군이었다. 선언과 실사용이 어긋난 채로는 폴더보다 `type`을 우선 해석하는 구조가 성립하지 않는다. **닫힌 목록을 지키는 척하는 대신 실사용을 등재하고 확장 규칙을 명시한다.**

**규칙: 새 `type` 값을 쓰기 전에 이 절에 등재한다.** 등재 없이 새 값을 만들지 않는다.

### 독서·전시 (bookclub / shared)

`book-card` · `exhibition-note` · `question-note` · `close-reading-note` · `lecture-script` · `short-story-card` · `anthology-index` · `theme-note` · `shared-theme-note`

### 집필 — 산출물 (writing)

`play-card` · `play-draft` · `draft-scene` · `draft-candidate` · `revision-note` · `draft-revision-note` · `revision-log` · `writing-note`

### 집필 — 평가·진단

`writing-note-evaluation` · `writing-evaluation` · `dramaturgy-diagnostic` · `structure-test` · `stage-test` · `doctrine-behavior-test`

### 집필 — 교리·도구 (진실원 층)

`writing-doctrine` · `writing-tool` · `writing-router` · `writing-checklist`

### 지도·기록

`map` · `map-note` · `writing-map` · `draft-map` · `draft-candidate-map` · `writing-device-map` · `checkpoint-map` · `work-ledger` · `gate-record` · `writing-log` · `weekly-review`

### 씨앗·수집

`seed-harvest` · `seed-note` · `inbox-capture` · `exploration` · `research-development`

### 운영

`decision-note` · `reference` · `contest-note` · `index`

### 통합 대기 (1~3건짜리 변종 — 새로 쓰지 않는다)

`draft` · `draft-structure` · `draft-material-note` · `decision` · `play` · `question` · `playwriting-development` · `playwriting-probe` · `playwriting-note` · `project-checkpoint` · `work-brief` · `revision-cue-sheet` · `revision-directive` · `reading-kit` · `review-note`

위 값들은 이미 등재된 정식 타입과 의미가 겹친다(예: `draft` ↔ `draft-scene`, `decision` ↔ `decision-note`, `play` ↔ `play-card`). **기존 문서는 소급 수정하지 않되 새 문서에 쓰지 않는다.** 통합은 별도 작업으로 다룬다.

### 타입 외 관계 필드

- `connected_questions` — 질문형 노트 링크. **wikilink 형식**(`"[[wiki/shared/questions/...]]"`)이 표준이다. (2026-08-20에 강의 73편의 `linked_questions`를 이 필드로 이관했다.)
- `linked_books` — `lecture-script` 전용. 그 강의가 다루는 책카드를 가리킨다. `related_to`와 달리 "이 강의의 대상"이라는 특정 관계이므로 별도 필드로 유지한다.
- `related_to` / `belongs_to` / `has` — 관계가 명확할 때만 추가한다(AGENTS.md §8).
- `authority_scope` — 교리 문서가 관할하는 범위. `writing-doctrine`에서만 쓴다.


### book-card
책 한 권을 다시 떠올리기 위한 장기 기억 장치. 줄거리보다 강독의 흐름과 핵심 질문을 우선한다.

필수 섹션:
- 이 책을 다시 떠올리는 한 문장
- 왜 이 작가는 이 책을 썼을까
- 이 책의 핵심 질문
- 내 해석
- 강독의 흐름
- 오래 남겨야 할 장면/문장
- 이 책이 남긴 정서
- 다른 책과 연결되는 지점
- 아직 찜찜한 점
- 콘텐츠로 바꿀 수 있는 각도
- 근거 자료

### exhibition-note
예술 전시 한 회차를 다시 붙잡기 위한 장기 기억 장치. 전시 전체를 작품 목록으로 요약하기보다, 실제 관람에서 남은 감각·판단·망각을 설치·해설·제도와 대조하고 기존 질문망으로 확장한다.

필수 섹션:
- 이 전시를 다시 떠올리는 한 문장
- 왜 지금 이 전시인가
- 전시 기본 정보와 관람 조건
- 실제로 남은 장면·문장·감각
- 작가/작품별 핵심과 강한 반례
- 내 해석과 AI 가설의 구분
- 기존 책·질문과 연결되는 지점
- 아직 찜찜한 점과 근거 자료

### question-note
v2의 중심 문서. 추상 주제어보다 질문형 제목을 우선한다.

좋은 제목 예:
- `제도는 인간을 어떻게 지우는가`
- `개인은 언제 세계를 부조리하다고 느끼는가`
- `언어는 왜 관계를 구하지 못하는가`

필수 섹션:
- 질문의 핵심
- 왜 이 질문이 내 위키에서 중요한가
- 연결된 책
- 연결된 희곡/창작 문제
- 반복되는 정서
- 아직 모르는 것
- 다음에 붙일 후보

### play-card
희곡 소개가 아니라 퇴고 감각을 보존하는 문서.

필수 섹션:
- 이 작품의 핵심 질문
- 한 문장 로그라인
- 현재 버전 상태
- 이 작품의 미학
- 사건의 힘
- 관객 이해의 문제
- 설명을 덜어내는 방식
- 퇴고가 해치면 안 되는 것
- 다음 퇴고에서 실험할 것
- 연결 질문
- 투고 이력
- 근거 원고

### revision-note
버전 비교 문서. 좋아졌다/나빠졌다보다 무엇이 살아났고 무엇이 사라졌는지 본다.

필수 섹션:
- 비교 대상
- 가장 큰 변화 한 문장
- 구조 변화
- 인물/관계 변화
- 대사/침묵 변화
- 사건의 힘 변화
- 사라진 강점
- 새로 생긴 강점
- 미학을 해칠 위험
- 다음 버전에서 실험할 것

### seed-harvest
한 회차의 글감 채집 범위·접근 경계·실제 수율·선별 과정을 보존하는 배치 정본. A1 고정 표본이 있으면 pass 여부와 관계없이 전건의 공개 원문과 사용자용 판정 이유를 보존하는 companion harvest를 둘 수 있다. 개별 글감의 개발 승인 문서가 아니다.

필수 내용:
- 고정 cutoff와 채집 범위
- 사이트·레인별 후보 우주와 실제 원글 열기 수
- 공개 본문과 댓글·응답 경계
- provisional과 부모 재독의 차이
- 최종 수율과 제외·보류 이유
- 사용자 선택·개발 권한의 미개방 상태
- 원시 자료와 전건 심사 package의 Vault 밖 보존 경계

A1 전건 원문 열람 companion의 필수 내용:
- 제목·사이트·게시 시각·canonical URL
- 접을 수 있는 공개 원글 전체
- A1까지 온 이유와 원문에서 확실히 남는 연극적 요소
- AI 확장·참고 아이디어와 상태별 판정 이유
- 작가가 다음에 볼 것
- 직접 식별자·키/서명 블록 마스킹과 사용자 선택 미개방 상태

Source-hidden은 심사자 입력에만 적용하며 사용자용 harvest에는 적용하지 않는다. 원시 HTML·A0 전건 body·댓글/답변본문·hash/evidence/review receipt는 계속 Vault 밖에 둔다. 세부 운영은 [[wiki/writing/decisions/A1_전건_원문열람_정본_운영_2026-08-17|A1 전건 원문 열람 정본 운영]]을 따른다.

### seed-note
A1 pass 뒤 장기 보존하는 sanitized 개별 글감. 원문 사연의 반입이나 draft candidate 승격이 아니라, 비발명 구조 메모의 최소 projection이다.

필수 내용:
- 다시 붙잡는 한 문장과 sanitized A0 anchor
- 보호 핵심과 source distance
- 공연 운반체와 긴장 topology
- 시간 규칙·temporal operation·terminal condition
- audience route
- 윤리 거리와 기존 글감과의 차이
- 다음 사용자 선택 질문
- opaque A1/residue lineage
- `a1-pass-unselected`와 `derived_permissions: []`

## 5. Frontmatter 규칙

모든 wiki 문서는 YAML frontmatter를 가진다. 이 vault는 Tolaria식 `filesystem-first / convention over configuration` 원칙을 일부 흡수한다. 즉, 마크다운 파일이 단일 진실 공급원이고, frontmatter는 AI와 사람이 같은 방식으로 문서를 찾고 연결하기 위한 최소 규칙이다.

```yaml
---
type: <아래 §4.0 타입 레지스트리의 값 하나>
status: draft | stable | needs-review
created: YYYY-MM-DD
updated: YYYY-MM-DD
visibility: private
sources: []
connected_questions: []
related_to: []
belongs_to: []
has: []
---
```

공통 convention:

- `type`은 문서의 역할을 나타낸다. 폴더 위치와 충돌하면 폴더보다 frontmatter를 우선해 해석한다.
- `status`는 문서의 완성도다. `stable`은 더 이상 수정하지 않는다는 뜻이 아니라, 현재 강독/창작 판단에서 기준 문서로 쓸 수 있다는 뜻이다.
- `connected_questions`는 질문형 노트 링크를 모으는 필드다. 본문에도 자연스러운 wikilink를 둔다.
- `related_to`, `belongs_to`, `has`는 필요한 경우만 쓴다. 모두 Obsidian wikilink 배열을 기본 형태로 한다.
- `_`로 시작하는 필드는 시스템/워크플로 메타데이터다. 일반 해석 내용처럼 읽지 않는다. 예: `_workflow_version`, `_source_kind`, `_generated_by`, `_verification`.
- API 키, 로컬 경로, 임시 캐시, 도구 설정처럼 특정 PC에만 속하는 정보는 vault 문서에 쓰지 않는다. 그런 정보는 Hermes 설정/환경변수/로컬 작업 폴더에 둔다.

책카드 추가 필드:

```yaml
book: 책 제목
author: 작가
club_date: YYYY-MM-DD 또는 unknown
source_folder: bookclub/...
```

전시노트 추가 필드:

```yaml
exhibition: 전시명
venue: 전시장
exhibition_period: "YYYY-MM-DD–YYYY-MM-DD"
visit_date: YYYY-MM-DD 또는 unknown
source_folder: bookclub/전시감상/...
```

희곡카드 추가 필드:

```yaml
play: 작품명
form: 단막극
latest_version: 파일명
source_folder: script
submission_target: 신춘문예
```

글감 노트 추가 필드:

```yaml
type: seed-note
status: stable
seed_state: a1-pass-unselected
a1_state: pass
novelty_state: distinct | drift_warning
source_handling: clear | transform_only
derived_permissions: []
_a1_record_id: opaque-id
_residue_id: opaque-id
sources: []
connected_questions: []
related_to: []
```

- `seed-harvest`는 출처 감사를 위해 안전한 최소 canonical을 둘 수 있지만 원시 cache와 전건 심사 자료는 넣지 않는다.
- `seed-note`의 `sources`는 기본적으로 비운다. URL·사이트·작성자·게시물 제목·exact evidence·재식별 단서는 외부 private archive에만 둔다.
- A1 pass는 카드·사용자 선택·장면·형식·길이·B2를 허가하지 않는다. 사용자 선택 전에는 `derived_permissions: []`를 유지한다.

## 6. 링크 규칙

- 의미 연결은 태그보다 질문형 노트 wikilink로 만든다. 예: `[[wiki/shared/questions/자각은 왜 사건이 되지 못하는가|자각은 왜 사건이 되지 못하는가]]`
- 태그는 문서 타입 보조나 검토/처리 대기 같은 상태 표시용으로만 최소 사용한다. 의미 연결은 태그가 아니라 wikilink와 frontmatter 배열로 만든다.
- 책카드는 최소 2개 이상의 질문형 노트에 연결하는 것을 목표로 한다. 억지 연결은 금지.
- 질문형 노트는 연결된 책/희곡이 늘어날수록 갱신한다.
- Obsidian alias는 대괄호 두 겹 안에서 `대상경로|표시명` 형식으로 쓰고, `\|`처럼 escape하지 않는다.
- Inbox 캡처와 Web Clipper 자료는 바로 장기 지식으로 취급하지 않고, 출처·핵심 문장·승격 방향을 정한 뒤 질문형 노트/창작 노트/지도/책카드/결정 노트로 이동한다.
- `log.md`의 결정이 나중에 반복 논쟁이 될 가능성이 있으면 decision-note로 승격한다. 공통 결정은 `wiki/shared/decisions/`, 희곡/집필 결정은 `wiki/writing/decisions/`, 책모임/강독 결정은 `wiki/bookclub/decisions/`를 쓴다.
- 주간 또는 큰 작업 묶음 뒤에는 필요할 때 `wiki/shared/reviews/weekly/`에 weekly-review를 남겨 남은 질문·새 연결·다음 초점을 압축한다.
- 승격 규칙: 한 번만 등장한 생각은 Inbox나 log에 둘 수 있고, 두 번 이상 반복되면 question/note 후보, 작업 방향을 바꾸는 판단이면 decision-note, 여러 책/희곡/글감을 잇기 시작하면 map으로 승격한다.

## 7. Ingest 원칙

1. 원본 위치와 파일명을 확인한다.
2. `파트2`, `통합`, `최종`, 발표용 스크립트에 가까운 파일을 우선 읽는다.
3. 필요한 경우 작가론/사전리서치/시대배경 파일을 보조로 읽는다.
4. 책카드는 원본에서 새로 작성한다.
5. 작성 후 `_archive/wiki_v1/`의 기존 문서와 비교해 빠진 통찰만 선별 반영한다.
6. `index.md`와 `log.md`를 갱신한다.

## 8. 퇴고 원칙

희곡을 다룰 때 가장 중요한 질문은 다음이다.

- 이 작품은 무슨 질문을 가진 이야기였나?
- 사건은 충분히 움직이는가?
- 설명을 덜어내면서도 관객이 따라올 수 있는가?
- 퇴고가 작품의 고유한 미학을 해치고 있지는 않은가?
- 책에서 온 질문이 장면/사건/인물의 행동으로 바뀌었는가?

## 9. Lint 기준

정기 점검 시 확인한다.

- 질문형 노트 없이 고립된 책카드
- 너무 추상적인 주제 노트
- `내 해석`과 `AI 가설`이 섞인 문서
- 원본 근거가 없는 주장
- 책과 희곡 사이 연결이 억지인 문서
- 설명은 많은데 장면/질문이 약한 희곡카드
- v1에서 가져온 문장이 새 목적에 맞지 않는 경우
