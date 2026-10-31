---
name: play-seed-harvesting
description: 공개 커뮤니티·뉴스·블로그·관찰 자료에서 희곡 글감을 채집하고 A0→A1 판정까지 진행할 때 사용한다. "오늘 글감 채집", "커뮤니티 채집", "글감 채집 배치", A0/A1 판정, evidence-lock, seed-harvest 정본 작성, 채집 정본 검증 요청에 반응한다. 판정 교리의 정본은 vault 결정문서이고 이 스킬은 실행 어댑터다. 선택 뒤의 형식·길이·B2·장면 집필은 이 스킬의 권한이 아니다.
---

# 글감 채집 — A0→A1 실행 어댑터

## 권위 순서

**최신 사용자 지시 > 명시된 스코프·소스 계약 > 직접 확인한 라이브 소스와 현행 vault 결정문서 > 쓰기 우선·윤리 불변식 > 이 스킬 > 과거 예시.**

이 스킬은 판정 교리를 소유하지 않는다. 교리 정본은 vault 결정문서이고, 이 스킬은 그 문서를 실행 가능한 순서로 바꾼 얇은 어댑터다. 이 스킬과 결정문서가 어긋나면 **결정문서가 이긴다.** 그 경우 어긋난 지점을 사용자에게 보고하고 이 파일을 고친다.

이 디렉토리는 vault 어댑터 위에 Hermes 배포본 `1.8.0-portable.1`의 참조·템플릿·검증기·파서를 병합한 사본이다(2026-10-31). 배포본 원래의 `SKILL.md`는 들이지 않았고, 설치·한계·권리 표시는 `PORTABLE_README.md`·`DISTRIBUTION.md`·`VERIFICATION.md`·`LICENSE`·`THIRD_PARTY_NOTICES.md`, 파일별 해시는 `MANIFEST.json`에 있다(`SKILL.md`·`README.md` 해시는 배포본 기준이라 여기서는 일치하지 않는다). 영어 참조 문서는 운영 보조 자료이며, vault 결정문서와 어긋나면 결정문서가 이긴다.

## 이 스킬이 열지 않는 것

A0 yes도, A1 pass도 다음을 **승인하지 않는다.**

- 최종 카드 승인 · 사용자 선택
- 장면 집필(2~5쪽) · 독백 · 반복 스코어 · 음향 실험
- 형식·길이·결말 결정 · B2 · 물성 시험
- 다음 개발 단계 자동 개방

A1 pass의 직접 권한은 **구조 메모가 존재한다는 기록** 하나뿐이다. 모든 미선택 항목은 `derived_permissions: []`를 유지한다. 선택 이후의 형식·집필·퇴고·승격은 희곡 교리 쪽으로 넘긴다.

## 정본 교리 — 먼저 읽을 것

작업 전에 스코프에 해당하는 행만 읽는다. 요약본을 신뢰하지 말고 현행 파일을 직접 연다.

**아래 표의 경로는 vault 루트(git 저장소 루트) 기준이다.** 이 스킬은 `wiki/writing/.claude/skills/`에 있으므로 작업 디렉토리가 `wiki/writing`일 때는 앞의 `wiki/writing/`을 떼고 열거나 저장소 루트에서 상대경로로 연다. 경로가 안 맞으면 `git rev-parse --show-toplevel`로 루트를 확인한다. 절대경로를 이 파일에 적지 않는다(AGENTS.md §8).

| 무엇을 정하나 | 정본 문서 |
|---|---|
| A0/A1 판정 전체 설계, 6개 직교 상태, workflow_state 파생 우선순위, 메모 8필드, 줄별 line_type, 두 독립 리뷰 | `wiki/writing/decisions/공개커뮤니티_A0-A1_판정설계_2026-08-15.md` |
| A1 전건 원문 열람 정본의 항목 순서·마스킹·저장 경계 | `wiki/writing/decisions/A1_전건_원문열람_정본_운영_2026-08-17.md` |
| 한국 공개 커뮤니티 채집풀 운영 규칙 | `wiki/writing/decisions/공개커뮤니티_채집풀_운영규칙_2026-07-18.md` |
| 일본 공개 커뮤니티 표본 레인·상한·A0→A1 계약 v3 | `wiki/writing/decisions/일본_공개커뮤니티_표본선정_2026-08-09.md` |
| 조건 레인(뉴스·사고 기록·제도 문서): 층 표시, 사실 출처 등급, C0/C1, 이해 충돌, 원천과 주기 | `wiki/writing/decisions/조건레인_운영규칙_2026-10-31.md` |
| Hermes 수집 → Claude 판정 분업, 핸드오프 폴더·`HANDOFF.json`·재독 요청, 막힌 사이트 원문의 Claude 판정 허용과 직접 요청 금지 | `wiki/writing/decisions/Hermes_Claude_글감채집_협업체계_2026-10-31.md` |
| 폴더 역할, 상태 흐름, `seed-harvest`/`seed-note` 문서 계약, 저장 경계, 현재 체크포인트 | `wiki/writing/seeds/README.md` |
| frontmatter `type` 레지스트리와 관계 필드 | `SCHEMA.md` §4.0 |

`seeds/README.md`의 **현재 체크포인트** 절이 배치 번호와 누적 상태의 정본이다. 과거 계획의 숫자를 기억으로 되돌려 가정하지 않는다.

## 스코프 잠금

작업을 시작하기 전에 다음을 기록한다. 하나라도 비면 사용자에게 묻는다.

- 소스 클래스·사이트·제외 목록
- 시간 창과 절단 시각
- 사이트별·전체 상한
- 출력 모드: chat-only / read-only / 지정 파일만 / hold / stop
- 쓰기·commit·push 허용 여부

**시간 기본값:** 사용자가 `오늘`이라고 하면 **절단 시각 직전 rolling 24시간**을 뜻한다. 달력 날짜가 아니다. 절단 시각(타임존 포함)과 파생 시작 시각을 둘 다 기록한다. 명시적 달력 날짜·`당일`·더 좁은 범위는 이 기본값을 덮는다.

**미달은 유효하고 대체는 무효다.** 승인된 풀에서 통과한 글이 적으면 부족분을 채우지 않는다. 뉴스나 미승인 사이트로 커뮤니티 슬롯을 메우지 않는다.

## robots·접근 게이트 — 수집 전 필수

**실행할 때마다 각 사이트 robots.txt를 다시 읽는다.** 캐시된 판단이나 지난 배치의 결과를 재사용하지 않는다. 같은 run-dir을 이어 실행할 때도 호출마다 새로 읽고, 직전 영수증은 `robots_history.jsonl`로 넘긴다. 판정은 대표 경로 하나가 아니라 **실제로 요청하는 목록·본문 URL(경로+query) 각각**에 대해 요청 직전에 한다. robots.txt가 429/430이면 RFC 9309의 4xx 허용이 아니라 요청 제한으로 보고 그 사이트를 멈춘다.

**접근 기준선 고정:** 새 한국·일본 계약은 `access_policy_version: 2026-10-30-verified-baseline-v1`을 쓴다(정본: 채집풀 운영규칙 2026-10-30 절). 실제 요청 주체와 그에 해당하는 robots 그룹·wildcard 경로 규칙만 적용한다. `ChatGPT-User`·`OAI-SearchBot`·`GPTBot` 등 **다른 이름의 봇 제한을 확대 적용하지 않고**, 모든 봇 이름이 허용해야 한다는 AND 조건을 만들지 않는다. **명시적 예외 하나:** 실행 주체가 Claude일 때는 Anthropic 계열 토큰 다섯 개를 모두 자기 이름으로 보고, 그중 하나라도 금지하면 따른다(아래 1번, 2026-10-31 사용자 결정 — 결정문서 2026-10-30 절에 근거 기록). 이 예외는 다른 회사 봇이나 Hermes로 확대하지 않는다. "더 안전하게"를 이유로 중단 조건·진입 경로·요청 예산·채택 조건을 임의로 좁히지 않는다 — 재량적 변경은 사용자 명시 승인이 필요하다. 실제 현재 제한(해당 robots 거부·로그인 벽·403/challenge·429)은 해당 요청/사이트에만 적용하고 URL·주체·규칙/상태·시각을 남긴다. 이전 배치를 재사용할 때 그 배치의 `extra_conservative_rule`·`provider_policy_conservative_stop`·전 봇 AND 게이트를 새 계약에 복제하지 않는다.

판정 순서:

1. **실행 주체별로 판정한다(2026-10-31 사용자 결정, 접근 기준선의 명시적 예외).**
   - **Hermes**(`HermesAgent-PublicResearch/1.0`): 자기 제품 토큰에 해당하는 그룹, 없으면 `*` 그룹만 적용한다. 다른 이름의 봇 제한은 확대 적용하지 않는다(접근 기준선).
   - **Claude**(Claude Code 등 Anthropic 모델이 직접 요청): `Claude-User`·`ClaudeBot`·`Claude-Web`·`anthropic-ai`·`Claude-SearchBot` 가운데 **하나라도** 해당 경로를 금지하면 그 사이트는 Claude 수집에서 제외한다. 학습용 토큰만 지목된 경우도 Anthropic 계열 전체에 대한 반대 의사로 존중한다. **단, robots에 `Claude-User`를 이름으로 지목한 그룹이 있으면 사용자 지시 수집은 그 그룹만 따른다**(2026-10-31 사용자 승인 개정. 예: GeekNews. 예약 작업의 자율 수집에는 적용하지 않는다). 수집기 `judge_actor`가 이 규칙을 구현한다.
   - 제외된 사이트는 `robots_denied`로 기록하고 그 몫은 미달로 남긴다. 같은 사이트를 다른 주체가 정당하게 수집할 수는 있지만, Claude가 Hermes UA를 빌리는 것은 2번의 우회다.
2. **UA를 바꿔 우회하지 않는다.** 사이트가 이 에이전트 계열을 지목해 거부했는데 브라우저 UA로 갈아타 200을 받는 것은 접근 성공이 아니라 거부 우회다. `curl -A`, playwright, TLS 지문 위장 모두 같다. 열린다는 사실이 열어도 된다는 뜻은 아니다.
3. **사람이 직접 읽은 것은 다른 경로다.** 사용자가 공개 페이지를 자기 브라우저로 읽고 본문을 가져오는 것은 에이전트 크롤링이 아니다. 이 경로로 들어온 원문은 출처와 열람 주체를 `_access_route`에 남긴다.
4. **`*` 그룹만 보고 판단하지 않는다.** `Disallow: /`와 더 구체적인 `Allow`가 함께 있으면 raw 그룹을 열어 longest-match 우선순위를 직접 확인한다. `*` 그룹이 아예 없는 robots도 있다 — 그때도 이름이 지목되었는지가 기준이다.
5. **Content-Signal도 읽는다.** `ai-train=no`, `use=reference` 같은 신호는 권리 유보 선언이다. 수집 여부와 별개로 문서에 기록한다.

사이트별 실측 경로·차단 형태·selector 벽은 `references/사이트별_접근경로.md`를 읽는다.

로그인·가입·API·쿠키 벽은 우회하지 않는다. 스니펫으로 본문 주장을 지지하지 않는다. HTTP 200과 비어 있지 않은 길이는 본문 근거가 아니다.

## 현행 한국 풀

`community_pool_version: "2026-10-31"` — **핵심 2 + 보조 2**(Hermes 레인) + **Claude 레인 1**(에펨코리아 `/best`, 사용자 지시 때만). 사이트당 최대 `5`, 전체 최대 `20`. 미달 허용.

| 사이트 | 경로 | 비고 |
|---|---|---|
| Instiz `일상` (핵심) | `/name` 목록 · `/name/<id>` 본문 | 회원 전용 안내 페이지를 공개 본문으로 오인하지 않는다 |
| Clien 모두의공원 (핵심) | `/service/board/park` 목록 · `/service/board/park/<id>` 본문 | 2026-10-31 진입점 교정. robots가 Anthropic 계열을 지목하므로 Hermes 레인 전용 |
| 82cook 자유게시판 (보조 B) | `bn=15` 한정 · **본문만** | 댓글은 수집·판정 대상이 아니다 |
| Ruliweb `고민상담 300147` (보조 B) | query 없는 board 경로 · `/community/board/300147/read/<id>` | 댓글·답글·JSON-LD 댓글 본문 제외. 목록 2페이지부터는 `?page=N`만 붙인다(2026-10-31 개정). `cate=` 등 다른 query는 금지 |
| FMKorea `포텐 터짐 /best` (Claude 레인) | `/best` · `/best?page=N` 목록 · `/best/<id>` 본문 | 2026-10-31 편입. 사용자 지시 때만 `--actor claude`로 수집한다. Hermes UA는 430. 댓글 제외. 2026-08-29 품질 `C`라 첫 배치 A0 회계가 재평가 자료다 |

TodayHumor는 2026-08-29부터 비활성(공개 본문 재현 불가), MLBPARK는 은퇴했다. FMKorea는 Hermes 레인에서는 비활성이고, `/best`만 2026-10-31 Claude 레인으로 편입됐다(Hermes UA는 430, Claude-User는 200). 수집기 프로필은 `fmkorea`다. 목록 2쪽부터 `/best?page=N`을 쓴다. `2026-08-29`(클리앙 게시판 무관)·`2026-08-15` 풀이나 풀 버전 없는 과거 노트는 당시 계약의 역사 자료로 보존하고 소급 무효화하지 않는다. 기본 풀 제외: 보배드림(예비 B, 2026-10-31 재평가 텍스트 독립 6/11)·인벤 오픈이슈(`C`)·뽐뿌·더쿠·루리웹 `300147` 외 게시판. 뉴스는 주장 교차 확인에만 쓰고 커뮤니티 슬롯을 메우지 않는다.

이 네 곳은 학교·직장·가족·나이·건강·돈·위치 단서가 섞인 사적 노출을 자주 담는다. 자동 수락하지 말고 지속 사용 전에 해당 단서를 제거하거나 강하게 변형한다.

## 채집 루프

1. **스코프 잠금** — 위 절대로 기록한다. 카드마다 합법 레인 하나가 필요하다.
2. **라이브 상태 점검** — 현행 결정문서, 기존 노트·중복, `seeds/README.md` 체크포인트, git status를 읽는다. 활성·보류·완료·자기복제 가지를 파악한다.
3. **robots 게이트** — 위 절을 실행한다. 제외된 사이트는 미달로 남긴다.
4. **재현 가능하게 수집** — `scripts/community-collector.py`로 사이트별 스냅샷·큐·영수증·카운터를 분리한다. 한 사이트 실패가 뒤 사이트를 지우지 못하게 격리한다. 차단은 이름을 붙여 기록하고 대체하지 않는다. **글 하나의 벽·삭제는 레인 중단 사유가 아니다.**
5. **수락 전 검증** — 직접 페이지를 열어 현행 제목·날짜·본문·접근 상태와 지지 문구를 확인한다. `listed / title-filtered / opened / current-range / non-empty / accepted`를 각각 따로 센다.
6. **A0 — 넓은 잔여 회수** — 원 사건을 버린 뒤 명명 가능한 잔여가 남는지만 본다. **주제·민감성은 탈락 사유가 아니다.** `residue: yes/no`와 `source_handling`을 분리한다. A0 yes마다 **서로 다른 exact span 2개**를 잠근다. 하나는 게시물 제목이어도 되지만(`evidence_kind: title`, 2026-10-31 개정), 다른 하나는 반드시 현행 본문이다. 판정 단위는 `(source_id, source_version_id, residue_id)`다.
7. **Evidence-lock 게이트** — 메모 작성 **전에**, 계보 레인이 두 span이 현행 본문(제목 근거는 현행 열람 제목)에 글자 그대로 있고 상속된 잔여를 의미적으로 지지하는지 확인한다. span이나 잔여가 흔들리면 A0 결정을 버전하고 `a0_recheck`로 멈춘다. **메모 작성자가 대체 근거를 조용히 고르게 하지 않는다.**
8. **A1 — 비발명 구조 증명** — evidence-lock을 통과한 runnable 레코드만 상속한다. 원문에 없던 동기·사건·결과를 더하지 않고 5~10줄 공연 규칙을 기술할 수 있는지만 묻는다. 줄마다 `supported_abstraction / entailed / speculative`를 붙인다. **`speculative`가 한 줄이라도 있으면 pass할 수 없다.** 잔여는 지지되는데 메모가 발명했으면 `resting`, A0 근거·잔여 오판이면 `a0_recheck`다. 상태 정의와 파생 우선순위는 판정설계 v0.2 §7을 따른다.
9. **두 독립 리뷰** — masked 구조 리뷰(앵커·URL·사이트·handling·기존 카드 여부를 가림)와 source-open 계보 리뷰를 둘 다 통과해야 `structure_state=proven`이다. 불일치는 부모 재심으로 보낸다.
10. **자기복제 검사는 구조 추출 뒤에** — 사전 탈락은 순환 논리다. 메모가 만들어진 뒤 무대 문법을 비교한다. 일부만 비슷하면 `drift_warning`을 남기고 pass할 수 있다.
11. **모든 레인 정합화** — 모든 소스·판정 작업을 기다린 뒤 제한된 풀을 다시 열고 1:1로 교체하고 자기복제·선별을 다시 돌린다. **타임아웃은 표가 아니다.** 하위 에이전트 후보 목록이 잘렸으면 저장된 전체 요약을 열어 확인한다. 잘린 줄에서 누락 항목을 추론하지 않는다.
12. **요청된 산출물만 생성** — chat/read-only는 아무것도 쓰지 않는다.
13. **사용자 게이트** — 압축 후보를 제시한다. 선택 뒤에는 지목된 probe만 실행하고 형식·집필·승격은 넘긴다. 영(0) 승격도 유효하다.

## 산출물 계약

한 배치는 문서 **두 개**를 남긴다. 둘은 같은 타임스탬프 접미(`HHMMSS`)를 공유하고 서로를 `related_to`로 링크한다.

```text
seeds/harvests/글감_채집_<YYYY-MM-DD>_<풀이름>_A0-A1_<HHMMSS>.md
seeds/harvests/글감_채집_<YYYY-MM-DD>_<풀이름>_A1전건_원문열람_<HHMMSS>.md
```

절 골격과 frontmatter 필드는 `references/문서_템플릿.md`를 읽는다.

핵심 계약 두 개만 여기 남긴다.

- **A0→A1 정본** — 고정 창·접근 경계, 수집·A0 회계, A1 고정 표본, evidence-lock·메모·리뷰, 최종 정합화, 권한 경계, 검증·저장 경계.
- **A1 전건 원문 열람 정본** — A1 고정 표본을 **pass 여부와 무관하게 전건** 보여 준다. `pass / resting / a0_recheck / blocked / not_run`은 가시성 필터가 아니라 같은 문서에서 읽는 판정 라벨이다. Source-hidden은 독립 심사 입력에만 적용하고 사용자 문서에는 적용하지 않는다. 운영 코드·hash·source ID·validator 전문은 사용자 본문에 넣지 않고 짧은 부록으로 내린다.

마스킹은 직접 식별자(전화·이메일·계좌·주소·실명과 고유 이력의 결합·핸들·공개키/서명 블록·자격 증명)만 필요한 부분을 `[식별정보 마스킹]`으로 대체한다. **민감 주제·정치·질병·돈·가족 갈등·성별 차별은 자동 마스킹 사유가 아니다.** 잔여를 성립시키는 내용 축은 지우지 않는다.

## 저장 경계

**Vault 안:** 배치의 범위·cutoff·접근 실패·실제 수율 / 상태별 집계 / A1 고정 표본 전건의 공개 원문·제목·사이트·게시 시각·canonical URL / 원문 지지분·AI 확장·판정 이유 / 사용자 선택 여부와 열리지 않은 권한.

**Vault 밖(재현·감사용 private archive):** 원시 HTML·이미지 cache / 크롤러 queue·opened 전건·request receipt / A0 전체 모집단 body와 전건 URL / **댓글·답변·レス·트랙백 본문** / source hash·exact evidence 전건 ledger·review receipt·validator fixture / A1 전건 package / 쿠키·로그인 상태·로컬 API 값·자격 증명.

제거한 개인정보의 실제 값은 별도 목록으로 남기지 않는다. Temp는 작업 위치일 뿐 장기 보존소가 아니다. AGENTS.md §8에 따라 PC 고유 절대경로·API 키를 vault 문서에 쓰지 않는다.

## 검증

**검증기와 문서 종류를 반드시 맞춘다.** 잘못 걸면 허위 오류가 난다.

| 검증기 | 대상 | 대상이 아닌 것 |
|---|---|---|
| `scripts/verify-public-community-note.py <note.md>` | `### [후보 N]` 카드를 가진 **카드노트**. sources/cards 집합 일치, 번호 연속성, 사이트별 상한, 풀 버전, 은퇴·제외 호스트 | 배치 A0→A1 정본. `## 1~7` 절 번호를 카드 번호로 오독해 `card numbering is not sequential` 허위 오류를 낸다 |
| `scripts/verify-public-community-a1.py <package.json>` | **Vault 밖** A1 package. A0/A1 residue 집합 일치, workflow_state 파생 우선순위, card⊆pass, 메모 계약 | vault 안 `.md` 문서 |
| `scripts/verify-community-harvest-structure.py <note> --expected-count N [--site-count SITE=N]` | 기대 수량·사이트별 수량을 외부에서 주입해 확인할 때 | |

위 표의 `scripts/`는 **이 스킬 디렉토리 기준**이다. 작업 디렉토리가 `wiki/writing`이면 `.claude/skills/play-seed-harvesting/scripts/...`로 부른다.

검증기 자체 테스트는 스킬 디렉토리에서 `python -B scripts/test-verify-public-community-note.py`, `python -B scripts/test-verify-public-community-a1.py`로 돌린다(각 8개·13개 통과가 정상). 파서 테스트는 Scrapy가 필요하다: `uv run --no-project --with 'Scrapy==2.17.0' python -B scripts/test-public-community-spider.py`(22개).

`scripts/public-community-spider.py`는 **완성 크롤러가 아니다.** 목록/본문 파서와 인자 검사만 있고 `start()`가 요청을 만들지 않는다. 종료 코드 0을 채집 성공으로 보고하지 않는다. 설계 계약은 `references/scrapy-local-community-crawler.md`(미구현 표시). 실제 수집은 아래 `community-collector.py`를 쓴다.

## 수집기 — `scripts/community-collector.py`

표준 라이브러리만 쓰는 재개형 수집기다(Python 3.10+). 배치마다 수집기를 새로 짜지 않는다. 사이트 DOM이 바뀌면 `PROFILES`의 selector만 고치고 테스트를 추가한다.

```bash
python -B scripts/community-collector.py profiles
python -B scripts/community-collector.py all --run-dir <Vault·Git 밖 절대경로> --actor hermes|claude \
  --window-hours 168 --page-budget 24 --per-day-cap 4 --max-posts 40 --site ruliweb --site 82cook ...
python -B scripts/community-collector.py status --run-dir <같은 경로> --site ruliweb
python -B scripts/test-community-collector.py   # 오프라인 회귀 57개
python -B scripts/verify-handoff.py "$SEED_HARVEST_RUNS/<batch>"   # Hermes 핸드오프 기계 검증(판정 전)
python -B scripts/test-verify-handoff.py        # 오프라인 회귀 12개
```

- **단계:** `robots → discover → freeze → fetch → status`. 각 단계는 `<run-dir>/<site>/`에 영수증을 남긴다. 같은 명령을 다시 실행하면 이어서 진행한다. 처음 실행할 때 `contract.json`에 실행 주체·UA·창을 고정하며, 주체를 바꾸려면 새 run-dir을 쓴다.
- **discover:** 목록 날짜를 읽어 창의 날짜마다 도달하도록 페이지를 이분·보간 탐색한다. 7일 창을 전부 덮는다는 보장은 없다 — 페이지 예산 소진, 프로필 페이지 상한, 목록 날짜 해석 실패로 빈 날짜가 남을 수 있고, 그 결과는 `in_window_days`의 0으로 드러난다. 0인 날은 미달로 보고하고 다른 날로 채우지 않는다. 날짜 칸은 프로필에 적힌 우선순위대로 시도해 처음 해석되는 값을 쓴다. 날짜를 못 읽은 행은 같은 날의 이웃 ID 사이에 있을 때만 그 날로 보간하고, 나머지는 `date_unresolved`로 센다. 버리지 않는다.
- **freeze:** 날짜별 상한 안에서 ID를 균등 간격으로 고른다. 제목은 쓰지 않고, 보충하지 않는다. 목록 칸에 시각이 있으면 분 단위로 창 밖이 확실한 행을 먼저 뺀다(`excluded_by_list_time`). 날짜만 있는 행과 경계 분의 행은 남기고 글 자체 시각으로 판정한다.
- **fetch는 글 단위 판정이 원칙이다.** selector를 못 찾은 글(`selector_missing`)은 텍스트 없이 `page_title`·`dom_outline`(태그·id·class 구조)만 남겨, Claude가 열 수 없는 사이트도 영수증으로 selector를 고칠 수 있게 한다. 회원 전용·삭제(404)·빈 본문·창 밖·리다이렉트·robots 개별 금지(`robots_denied`)·본문이 닫히기 전 응답 종료(`truncated_body`)·문자셋 오판으로 깨진 본문(`encoding_error`)·canonical이 다른 글을 가리킴(`canonical_mismatch`, scheme·끝 `/` 차이는 같은 글로 본다) 글은 **그 글만** 상태를 기록하고 넘어간다. 이들은 `eligible_bodies`에 들어가지 않는다. 사이트를 멈추는 것은 다음 경우뿐이다.
  - robots가 목록 페이지를 금지·도달 불가, robots.txt 429/430, robots.txt 자리의 봇 확인 HTML(`challenge`). 확인 화면이 아닌 HTML(소프트 404)은 규칙 없음으로 읽고 `robots.json`에 `robots_html: true`로 남긴다
  - 403/429/430/451, 봇 챌린지
  - 목록의 다른 호스트 리다이렉트
  - 연속 3회 selector 미검출 또는 댓글 경계 걸림(`parser_drift`)
  - 백오프 재시도 뒤 연속 3회 네트워크 실패(`network_unreachable`). 재시도 단위는 연결부터 본문을 다 읽을 때까지다. 응답 전 연결 끊김·RST·잘못된 상태줄·읽는 도중 끊김·Content-Length보다 짧은 본문 모두 같은 요청을 다시 한다.
  - 그 밖의 예기치 못한 오류는 `collector_error`로 그 사이트만 멈추고 다음 사이트를 계속한다.
- **멈춘 사이트는 조용히 재개하지 않는다.** `stop.json`을 사람이 확인한 뒤 새 run-dir로 다시 시작한다. 시작 영수증만 있고 완료 영수증이 없는 글은 `unresolved_attempts`로 남기고 자동으로 재요청하지 않는다.
- **본문만 받는다.** 본문 요소가 닫히면 연결을 끊는다. 모든 프로필은 댓글 컨테이너 selector(`comment_guard`)를 선언하고, 본문이 닫히기 전에 그것이 나오면 그 태그에서 파싱을 멈추고 `boundary_error`로 그 글을 제외한다. 그래서 영수증의 `comments_parsed=false`는 고정값이 아니라 검사 결과다(가드가 없으면 `null`). 가드는 댓글을 담을 수 있는 블록 요소(div·ul·table 등)에만 걸리고 `script`·`link`·인라인 배지는 무시한다. 82cook 가드는 Scrapy spider의 "class·id에 comment 포함" 규칙을 옮긴 것이라 실측 전이다 — 첫 실행에서 `boundary_error`가 몰리면(연속 3회면 `parser_drift`로 멈춘다) 영수증의 태그를 보고 가드를 좁힌다.
- **알려진 한계:** 표준 라이브러리 HTML 파서는 본문 안의 닫히지 않은 내부 태그나 짝 없는 닫는 태그를 바로잡지 못한다. 그러면 본문이 주변 광고·사이드바를 삼키거나 앞부분만 남은 채 `eligible`이 될 수 있다. `eligible`은 수집 영수증일 뿐이고, 수락 전 직접 열람 검증(채집 루프 5번)이 이 경우를 잡는다.
- **`accepted`는 항상 0이다.** `eligible`은 창 안의 공개 본문이라는 뜻이다. A0 판정·윤리·두 문구 근거 게이트는 수집 뒤의 별도 단계다.
- **아직 부족한 것:** 일본 사이트 프로필은 아직 없다(기존 Hermes 배치 수집기를 쓴다). 인스티즈·클리앙·82cook 목록 날짜 selector는 Claude가 실측하지 못했다. Hermes 첫 실행에서 `discover` 영수증의 `date_unresolved`를 확인하고, 0이 아니면 selector를 고친다.

## 참조 색인

현재 요청에 맞는 행만 읽는다. vault 전용 문서가 먼저이고, 영어 참조는 배포본에서 들인 운영 보조다. 파일명의 날짜는 근거 시점일 뿐 현행 계약을 덮지 않는다.

| 트리거 | 참조 |
|---|---|
| 사이트별 실측 경로·차단 형태 | `references/사이트별_접근경로.md` |
| 배치 정본 절 골격·frontmatter | `references/문서_템플릿.md` |
| 새 계약·극작 맥락 빈 양식 | `templates/collection-contract.md`, `templates/writing-context.md` |
| 커뮤니티 전용 풀·스코프·프라이버시 | `references/public-community-first-harvest.md` |
| A0→A1 레코드, masked/source-open 리뷰, 판정자 오류 분석·held-out 평가 | `references/public-community-a1-adjudication.md` |
| 직접 크롤·두 문구 근거 게이트 | `references/public-community-direct-crawl-and-evidence-gate-2026-07-23.md` |
| 재개 가능한 다중 사이트 크롤 | `references/resumable-community-crawl-checkpointing.md` |
| 부분 접근·독립 재독 정합화 | `references/public-community-partial-access-and-review-reconciliation-2026-07-25.md` |
| 늦은 레인·사라진 페이지 | `references/late-sweep-reconciliation.md` |
| 일본 공개커뮤니티 v2 압력·신선도 | `references/japanese-public-community-v2-pressure-and-evidence.md` |
| 한국 뉴스/RSS 발견 | `references/google-news-rss-korean-seed-harvest.md` |
| RSS 래퍼 복원·canonical·중단 재개 | `references/google-news-rss-canonical-url-and-resume.md` |
| 정확 제목 출판사 대체 경로 | `references/publisher-site-search-canonical-fallback.md` |
| 공개 블로그·커뮤니티 검색 자료 | `references/korean-blog-community-seed-harvest.md` |
| 보류 뒤 주제 전환 | `references/themed-harvest-and-hold-transition.md` |
| 혼합 소스 20카드 풀·2차 패스 | `references/multi-source-20-to-dramatic-expansion.md` |
| 시험 편의 편향·쓰기 우선 재선별 | `references/writing-first-reselection-regression-2026-07-12.md` |
| 책 기반 글감 다중 선택 | `references/multi-select-book-seed-writing-probes.md` |
| 조사 확장·승격 가능성 | `references/research-expansion-to-draft-candidate-map.md` |
| 채집을 서비스/제품으로 검토할 때만 | `references/harvest-service-idea-validation.md` |
| 배포본 설치·선택 연동·Python 기능 한계 | `references/portable-setup.md` |

참조에 나오는 `playwriting-dramaturgy`·`internet-research-routing`·`obsidian`·`bookclub-wiki-v2`는 Hermes 쪽 스킬 이름이다. 이 환경에서는 선택 뒤 형식·설계를 `play-design-theatricality` 스킬과 vault 희곡 교리로 넘기고, 없는 스킬의 규칙을 지어내지 않는다.

어떤 스크립트도 **라이브 근거 확인과 두 독립 리뷰를 대체하지 않는다.** selector·HTTP 코드·first-match는 본문 근거가 아니다.

완료 전에 확인한다.

1. 스코프 재독 — 수량·소스 순도·상한·제외·미달·출력 모드
2. 수락 URL과 카드·frontmatter 일치, 현행 제목·날짜·본문 근거. 만료·접근불가·교체·삭제 카드를 이름 붙여 보고
3. `확인 사실`과 `희곡적 확장` 분리, 윤리·보호 압력·작가 질문·자기복제, 선택 전 형식/B2/시험 팽창 없음
4. 위임·발견·판정 레인 전부 회계. 최종 교체 뒤 다시 실행
5. frontmatter·링크·번호·개행, 그래프 동기화, 범위 한정 `git diff --check`. 형제 편집 보존, 전역 부채는 따로 분류
6. A1 package는 전용 검증기 + A0/A1 residue 집합 일치 + card⊆pass
7. 경로·수량·접근 경계·영 수율·보류 가지·근거·공개 상태 보고

## Git

vault 인증 변경·commit·push는 **명시 요청이 있을 때만** 한다. 원문을 포함한 A1 전건 문서는 자동 commit·push하지 않는다. 무관한 작업을 일괄 stage·stash·reset·checkout·폐기·덮어쓰기하지 않는다. **올바른 채집은 vault를 dirty하게 남길 수 있다.**

## 함정

1. 출처에 근거한 압력·행동·관계·시간 대신 브리핑이나 논지 라벨을 만든다.
2. 주제를 논지로 다루거나, 무관한 출처들에 제도적 장치(민원실·키오스크·서식)를 발명해 넣는다.
3. 무대화가 쉬운 소품·시험 기준으로 순위를 매긴다.
4. 커뮤니티 미달을 뉴스나 미승인 사이트로 메운다.
5. 목록 행·스니펫·로그인 벽 본문·낡은 200 페이지·일반 댓글을 검증된 카드로 센다.
6. robots `*` 그룹만 보고 판단하거나, 이름이 지목된 차단을 UA 교체로 우회한다.
7. 소스·윤리·판정 레인이 남았는데 완료 선언한다. 독립 재독을 불필요하다고 부른다.
8. 늦게 온 후보를 상한 밖에 덧붙인다(1:1 교체가 맞다).
9. 원시 식별자·cache를 vault에 저장하거나 출처 사실과 희곡적 확장을 섞는다.
10. 선택·조사 깊이·무대화 가능성·한 번의 성공한 시험을 B2·형식·승격 승인으로 취급한다.
11. A0 yes를 A1 pass로 취급한다. masked 구조 레인에 앵커·출처를 보여 준다. `speculative` 메모 줄을 남긴 채 pass한다. `archive_only`·`blocked`·`merge`를 하나의 일반 거절 상태로 뭉갠다.
12. 카드노트 검증기를 배치 정본에 걸고 그 출력을 실제 오류로 보고한다.
13. 회원 전용 글 1건이나 selector 미검출 1건으로 사이트 레인 전체를 멈춘다. 글 단위 상태로 기록하고 계속한다(2026-10-31 인스티즈 22건 중단 사례).
14. 목록 날짜를 연도 하드코딩·단일 형식으로 읽어 행을 조용히 버린다(2026-10-31 인스티즈 107건 유실). `parse_list_day`로 읽고 `date_unresolved`를 보고한다.
15. 승인 진입점이 robots로 막혔는데 원인을 사이트 차단으로 적고 끝낸다. 같은 사이트의 허용 경로(예: 클리앙 `/service/board/park`)가 있으면 풀 개정 후보로 사용자에게 올린다. 사용자 승인 전 조용히 바꾸지 않는다.
16. TCP 타임아웃을 정책 차단으로 기록한다. 네트워크 계층(`tcp_connect`·`tls`·`dns`·`read_timeout`)을 남기고 백오프 뒤 재시도한다.
