---
type: index
status: stable
created: 2026-08-15
updated: 2026-08-17
visibility: private
title: "글감 채집 라이브러리"
sources: []
connected_questions:
  - "[[wiki/shared/questions/의미를 서두르지 않는다는 것은 무엇인가]]"
related_to:
  - "[[wiki/writing/decisions/글감_채집_폴더_운영_2026-08-15]]"
  - "[[wiki/writing/decisions/공개커뮤니티_A0-A1_판정설계_2026-08-15]]"
  - "[[wiki/writing/decisions/A1_전건_원문열람_정본_운영_2026-08-17]]"
---

# 글감 채집 라이브러리

이 폴더는 공개 자료·책 원본·관찰에서 채집한 재료를 **배치 정본**과 **장기 개별 글감**으로 나눠 보존한다. 폴더는 상태가 아니라 역할을 나타낸다.

## 역할별 경로

| 경로 | 역할 | 들어오는 것 | 들어오지 않는 것 |
|---|---|---|---|
| `harvests/` | `seed-harvest` | 회차 범위·접근·수율 정본, A1 전건 원문 열람 문서, 상태별 연극적 이유 | 원시 HTML·크롤러 cache, A0 전체 body, 댓글·답변본문, review receipt, 임시 경로 |
| `notes/` | `seed-note` | A1 pass 뒤 비식별화한 구조 메모, 보호 핵심, 공연 운반체, 시간 규칙 | URL·사이트·작성자·게시물 제목·exact evidence·식별 단서 |
| `draft-candidates/` | 기존 개발 후보 영역 | 사용자가 명시적으로 선택한 뒤 별도 이관된 후보 | A1 pass만 받은 글감의 자동 승격 |

`pass/selected/resting` 같은 상태별 하위 폴더는 만들지 않는다. 상태는 frontmatter로 관리한다.

## 상태 흐름

```text
외부 private archive
  원시 HTML/A0 body · exact evidence · 전건 A1 package · review receipts
                       │ audit lineage
                       ▼
seeds/harvests/        배치 단위 채집 정본 + A1 전건 원문 열람
                       │ A1 pass
                       ▼
seeds/notes/           a1-pass-unselected 개별 글감
                       │ 사용자 명시 선택
                       ▼
writing/draft-candidates/
```

- A0 yes는 넓은 잔여 회수다.
- A1 pass는 비발명 구조 메모가 성립했다는 뜻뿐이다.
- `seed-note`가 생겨도 카드 승인·사용자 선택·장면 집필·형식·길이·B2 권한은 열리지 않는다.
- 모든 미선택 글감은 `derived_permissions: []`를 유지한다.
- `resting`, `a0_recheck`, `blocked`를 포함한 A1 전건은 사용자 열람용 harvest 문서에 원문과 판정 이유를 남긴다. 외부 package는 hash·evidence·review receipt의 감사 정본이다.
- 상태는 가시성 필터가 아니다. `pass / resting / a0_recheck / blocked / not_run`을 같은 전건 문서에서 비교한다.

## 저장 경계

### Vault에 둘 수 있는 것

- 배치의 범위·cutoff·접근 실패·실제 수율
- 선별된 글감의 보호 제목과 비식별화된 구조
- 출처를 공개해도 안전하고 감사에 필요한 최소 canonical
- A1 pass의 sanitized projection과 opaque lineage ID
- A1 고정 표본 전건의 공개 원글 본문·제목·사이트·게시 시각·canonical URL
- pass/resting/a0_recheck/blocked별 원문 지지분·AI 확장·판정 이유
- 사용자 선택 여부와 아직 열리지 않은 권한

### Vault 밖에 둘 것

- 원시 HTML·이미지 cache·크롤러 queue/opened JSON
- A0 전체 모집단의 본문·전건 URL
- 댓글·답변·レス·트랙백 본문
- exact evidence 전건 ledger·게시물 ID·작성자 프로필
- 구조·계보 리뷰 전문과 review receipt
- A1 전건 package
- 로컬 API 값·임시 cache 경로·자격 증명

외부 package는 **감사·재현용 private archive**다. 사용자 열람의 정본은 `harvests/` 아래 A1 전건 원문 문서다. Temp는 작업 위치일 뿐 장기 보존소로 간주하지 않는다.

## 문서 계약

### `seed-harvest`

반드시 남긴다.

1. 채집 범위와 고정 cutoff
2. 사이트·레인별 후보 우주와 실제 원글 열기 수
3. 공개 본문·댓글/응답 경계와 접근 실패
4. provisional과 부모 재독의 차이
5. 최종 수율과 제외·보류 이유
6. 사용자 선택·개발 권한의 미개방 상태
7. 원시 자료의 Vault 밖 보존 경계

### `seed-note`

반드시 남긴다.

1. 다시 붙잡는 한 문장
2. A1 상태와 아직 열리지 않은 것
3. sanitized A0 anchor
4. 보호 핵심과 source distance
5. 공연 운반체와 긴장 topology
6. 시간 규칙·temporal operation·terminal condition
7. audience route
8. 윤리 거리와 기존 글감과의 차이
9. 다음 사용자 선택 질문
10. opaque A1/residue lineage

### A1 전건 원문 열람 `seed-harvest`

배치의 A1 고정 표본을 pass 여부와 무관하게 모두 보여 주는 사용자 정본이다.

1. 제목·사이트·게시 시각·canonical URL
2. 접을 수 있는 공개 원글 전체
3. A1까지 온 이유
4. 원문에서 확실히 남는 연극적 요소
5. AI가 더한 구조와 참고 아이디어
6. `pass / resting / a0_recheck / blocked / not_run` 판정 이유
7. 작가가 다음에 볼 것
8. 사용자 선택·개발 권한의 미개방 상태

Source-hidden은 독립 심사 입력에만 적용한다. 사용자 문서에는 적용하지 않는다. 직접 식별자·키/서명 블록·자격 증명만 필요한 부분을 마스킹하고, 민감 주제나 성별 차별 같은 내용 축은 자동으로 지우지 않는다. 세부 계약은 [[wiki/writing/decisions/A1_전건_원문열람_정본_운영_2026-08-17|A1 전건 원문 열람 정본 운영]]을 따른다.

## 현재 체크포인트 — 2026-08-17

- 새 구조를 적용한 `seed-harvest`: **7개** — [[wiki/writing/seeds/harvests/글감_채집_2026-08-15_해외커뮤니티_일본v2_222940|일본 공개 커뮤니티 v2 배치 70]] · [[wiki/writing/seeds/harvests/글감_채집_2026-08-16_해외커뮤니티_일본v3_A0-A1_223632|일본 공개 커뮤니티 v3 A0→A1 배치 71]] · [[wiki/writing/seeds/harvests/글감_채집_2026-08-16_해외커뮤니티_일본v3_A1전건_원문열람_223632|일본 배치 71 A1 전건 원문 열람]] · [[wiki/writing/seeds/harvests/글감_채집_2026-08-16_한국공개커뮤니티_A0-A1_234657|한국 공개 커뮤니티 A0→A1 배치 72]] · [[wiki/writing/seeds/harvests/글감_채집_2026-08-16_한국공개커뮤니티_A1전건_원문열람_234657|한국 배치 72 A1 전건 원문 열람]] · [[wiki/writing/seeds/harvests/글감_채집_2026-08-17_해외커뮤니티_일본v3_A0-A1_180446|일본 공개 커뮤니티 v3 A0→A1 배치 73]] · [[wiki/writing/seeds/harvests/글감_채집_2026-08-17_한국공개커뮤니티_A0-A1_204210|한국 공개 커뮤니티 A0→A1 배치 74]].
- 기존 `wiki/writing/notes/글감_채집_*.md`: **35개**, 아직 이동하지 않음.
- 옛 경로 참조: **51개 파일 / 189회**, 이동 전 manifest 재생성이 필요함.
- 외부 A1 58건: `pass 8 / resting 21 / a0_recheck 19 / blocked 10`.
- 일본 v3 배치 71 외부 A1 파일럿 12건: `resting 5 / a0_recheck 5 / blocked 2 / pass 0`.
- 일본 배치 71 A1 12건 전부를 [[wiki/writing/seeds/harvests/글감_채집_2026-08-16_해외커뮤니티_일본v3_A1전건_원문열람_223632|원문 열람 정본]]에 저장했다. 비차단 10건은 일본어 원문 전체, blocked 2건은 식별자·키/서명 블록만 마스킹했다. 기존 [[wiki/shared/reviews/배치71_출처비귀속_변형아이디어_레인_테스트_2026-08-17|source-detached review]]는 초기 시험 이력으로 축소했다.
- 한국 배치 72 외부 A1 고정 24건: `resting 12 / a0_recheck 11 / pass 1`. 최종 카드는 배치 정본 안에 1건만 두었고 `drift_warning`을 유지함.
- 한국 배치 72 A1 24건 전부를 [[wiki/writing/seeds/harvests/글감_채집_2026-08-16_한국공개커뮤니티_A1전건_원문열람_234657|원문 열람 정본]]에 저장했다. 원문·URL·연극적 이유·AI 확장·판정 이유를 함께 보여 준다. 기존 [[wiki/shared/reviews/배치72_출처비귀속_변형아이디어_레인_테스트_2026-08-17|source-detached review]]는 초기 시험 이력으로 축소했다.
- 일본 v3 배치 73 외부 A1 파일럿 12건: `pass 2 / resting 2 / a0_recheck 6 / blocked 2`. pass 2건은 정본 안의 비식별 구조 메모일 뿐 final card·사용자 선택·개발 권한은 0이다.
- 배치 73 `resting` 2건은 [[wiki/shared/reviews/배치73_출처비귀속_변형아이디어_레인_테스트_2026-08-17|출처 비귀속 변형 아이디어 레인 테스트]]로 별도 projection했다. `merge-route 1 / structure-insufficient 1`이며 source-backed claim과 개발 권한을 포함하지 않는다.
- 한국 배치 74 외부 A1 고정 20건: `a0_recheck 19 / resting 1 / pass 0`. memo 전 evidence-lock은 pass 2 · fail 18이었고, 작성 메모 2건은 구조 pass 2 뒤 계보 fail 2로 종료했다. final card·사용자 선택·개발 권한은 0이다.
- 배치 74 `resting` 1건은 [[wiki/shared/reviews/배치74_출처비귀속_변형아이디어_레인_테스트_2026-08-17|출처 비귀속 변형 아이디어 레인 테스트]]로 별도 projection했다. `transformative-hypothesis 1`이며 source-backed claim과 개발 권한을 포함하지 않는다.
- `seeds/notes/`: **0개**. 기존 pass 8건과 배치 72 pass 1건·배치 73 pass 2건의 개별 sanitized 글감 노트는 아직 만들지 않음.
- 기존 35개 이동·redirect 생성·live backlink 전환·pass 8건 생성·private archive 영구 이전: **미실행**.
- Git commit/push: **미실행**.

재개할 때는 [[wiki/writing/decisions/글감_채집_폴더_운영_2026-08-15|글감 채집 폴더 운영 결정]]의 manifest 잠금 단계부터 시작한다. 현재 숫자를 과거 계획의 35/8/184로 되돌려 가정하지 않는다.

## 연결

- [[wiki/writing/decisions/글감_채집_폴더_운영_2026-08-15|글감 채집 폴더 운영 및 체크포인트]]
- [[wiki/writing/decisions/공개커뮤니티_A0-A1_판정설계_2026-08-15|공개 커뮤니티 A0→A1 판정 설계 v0.2]]
- [[wiki/writing/decisions/A1_전건_원문열람_정본_운영_2026-08-17|A1 전건 원문 열람 정본 운영]]
- [[wiki/writing/decisions/일본_공개커뮤니티_표본선정_2026-08-09|일본 공개 커뮤니티 표본·A0→A1 판정 계약 v3]]
- [[wiki/writing/notes/글감_트리아지_지도|글감 트리아지 지도]]
