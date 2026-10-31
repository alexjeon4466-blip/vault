---
type: decision-note
status: approved
created: 2026-10-31
updated: 2026-10-31
access_policy_version: "2026-10-30-verified-baseline-v1"
visibility: private
title: "Hermes·Claude 글감 채집 협업 체계"
decision_status: decided
scope: community-play-seed-harvest-collaboration
sources: []
connected_questions: []
related_to:
  - "[[wiki/writing/decisions/공개커뮤니티_채집풀_운영규칙_2026-07-18]]"
  - "[[wiki/writing/decisions/일본_공개커뮤니티_표본선정_2026-08-09]]"
  - "[[wiki/writing/decisions/공개커뮤니티_A0-A1_판정설계_2026-08-15]]"
  - "[[wiki/shared/decisions/검증가능한_작업계약_도입_2026-07-18]]"
---

# Hermes·Claude 글감 채집 협업 체계

## 결정

공개 커뮤니티 글감 채집은 **수집은 Hermes, 판정·기록은 Claude**로 나눈다. 두 에이전트는 상대의 산출물을 검증하고, 같은 글을 서로 독립적으로 재독한다. 도입은 3단계로 하며, 현재 승인된 범위는 **1단계**다. 2·3단계는 진입 조건을 충족하고 사용자가 승인하면 시작한다.

Claude 전용 수집 레인은 두지 않는다. 2026-10-31 조사에서 Claude가 robots상 들어갈 수 있으면서 본문만으로 글감이 서는 곳이 한국·일본 모두 거의 없었다(아래 근거 절).

## 근거 — Claude 레인 조사 (2026-10-31)

Anthropic 계열 토큰 다섯 개(`claude-user`·`claudebot`·`claude-web`·`anthropic-ai`·`claude-searchbot`) 중 하나라도 금지하면 제외하는 기준으로 판정했다. 사이트별 상세는 스킬 참조 `.claude/skills/play-seed-harvesting/references/사이트별_접근경로.md`의 "2026-10-31 Claude 레인 후보 조사" 절에 있다.

- **한국 현행 풀:** 인스티즈·클리앙은 Anthropic 계열을 지목해 막는다. 루리웹 `300147`만 확실하고, 82cook은 그날 연결될 때만 가능하다.
- **한국 새 후보 23곳:** 대부분 Anthropic 계열을 지목해 막거나, 모든 봇을 막거나, 접속이 안 되거나, 봇 확인 화면을 띄운다. 통과한 곳의 게시판(루리웹 괴담·사건사고, 보배드림 이야기)은 표본에서 정보글·기사·운영진 글이라 탈락했다. 인벤 오픈이슈는 이미 C다.
- **일본 기존 풀:** 知恵袋·はてな匿名·発言小町 모두 Claude를 막는다.
- **일본 새 후보:** ママスタ·ガールズちゃんねる·5ch는 열리지만 주글이 짧은 화두이고 내용은 댓글·レス에 있다. 본문만 쓰는 규칙에서는 맞지 않는다(ママスタ 24건 중 단독 생활 서사 약 10%). ママリ는 웹에 편집 기사만 보였다.

## 역할

| 일 | Hermes | Claude |
|---|---|---|
| 수집 | 한국·일본 현행 풀 전체를 `HermesAgent-PublicResearch/1.0`으로 수집 | 하지 않는다 |
| 현행 원문 재독 | 담당 | Claude가 robots상 허용되는 사이트만 직접 확인할 수 있다 |
| 1차 A0 → evidence-lock → A1 | — | 담당 |
| 독립 재독 | 2단계부터 블라인드 2차 판정 | 정합화 |
| vault 기록(노트·로그·결정) | 하지 않는다 | 담당 |
| 수집기 | 실사이트 실측 | 코드·프로필·테스트 수정 |

## 정책 결정 — Hermes가 받은 원문의 Claude 판정 (사용자 결정 2026-10-31)

- Claude는 Hermes가 정당하게 수집해 로컬에 넘긴 원문을 판정·인용·기록할 수 있다. Claude가 직접 막힌 사이트(인스티즈·클리앙·일본 기존 풀 등)의 원문도 포함한다. robots는 크롤링 규칙이고, 사용자가 넘긴 로컬 자료의 판정은 크롤링이 아니라는 해석이다.
- **선:** Claude는 자신에게 막힌 사이트의 URL을 직접 요청하지 않는다. 본문·목록·robots·이미지 모두 마찬가지다. 현행 확인이 필요하면 재독 요청으로 Hermes에 넘긴다. Hermes UA를 빌리거나 Hermes 세션을 통해 Claude 요청을 대리 실행하는 것도 금지한다.
- 이 결정은 robots 판정 규칙을 바꾸지 않는다. Claude가 직접 수집할 때의 Anthropic 계열 전체 규칙과 Hermes의 자기 토큰·`*` 규칙은 그대로다. 단, 같은 날 뒤에 승인된 개정으로 `Claude-User`를 이름으로 지목한 robots 그룹이 있으면 사용자 지시 Claude 수집은 그 그룹을 따른다([[wiki/writing/decisions/공개커뮤니티_채집풀_운영규칙_2026-07-18|운영 규칙]] 2026-10-30 절).
- 원문 본문은 vault·Git에 넣지 않는다. vault에는 기존 노트 규칙대로 exact span·URL·시각·해시만 남긴다.

## 공유 폴더

- 같은 PC의 vault·Git 밖 폴더를 쓴다. 위치는 환경변수 `SEED_HARVEST_RUNS`로만 가리키고, vault 문서에는 절대경로를 쓰지 않는다. 수집기는 Git 작업 트리 안의 run-dir을 거부한다.
- 배치 폴더는 `$SEED_HARVEST_RUNS/<YYYY-MM-DD>_<kr|jp>[_<n>]/`이다. 한 배치는 한 주체(Hermes)만 쓴다.

```text
<batch>/
  contract.json          수집기가 첫 실행에 고정 (주체·UA·창)
  <site>/                수집기 사이트별 영수증·posts.jsonl(body, body_sha256)
  HANDOFF.json           Hermes가 수집을 끝낸 뒤 마지막에 쓴다 (완료 표지)
  requests/              Claude → Hermes 재독·추가 요청
  responses/             Hermes → Claude 응답
  claude/                Claude 검증·판정 작업 파일
```

## 1단계 — 수동 핸드오프 (현행)

### Hermes

1. vault의 `wiki/writing/.claude/skills/play-seed-harvesting/scripts/community-collector.py`를 그대로 쓴다. 사본을 만들거나 고치지 않는다. 결함은 영수증을 남기고 Claude 쪽 수정을 요청한다.
2. 한국 배치는 다음과 같이 실행한다. 창·예산은 [[wiki/writing/decisions/공개커뮤니티_채집풀_운영규칙_2026-07-18|채집풀 운영 규칙]]을 따른다.
   ```bash
   python -B <collector> all --run-dir "$SEED_HARVEST_RUNS/<batch>" --actor hermes \
     --window-hours 24 --site instiz --site clien --site 82cook --site ruliweb
   python -B <collector> status --run-dir "$SEED_HARVEST_RUNS/<batch>"
   ```
3. 일본 배치는 Hermes의 기존 일본 수집 절차와 [[wiki/writing/decisions/일본_공개커뮤니티_표본선정_2026-08-09|일본 계약 v3]]을 따른다. 결과는 `<batch>/<site>/posts.jsonl`에 글마다 한 줄로 쓴다. 필수 필드는 `url`·`title`·`posted_at`·`fetched_at`·`state`·`lane`·`lane_signal`(답변 수·북마크 수 등)·`body`·`body_sha256`(UTF-8 본문의 SHA-256)이다. 댓글·답변·レス·트랙백 본문은 넣지 않는다.
4. 사이트가 멈추면(`stop.json`) 우회하거나 다른 사이트로 채우지 않는다. 그대로 두고 `HANDOFF.json`에 적는다.
5. 마지막으로 `HANDOFF.json`을 쓴다. 이 파일이 생기기 전 배치는 Claude가 읽지 않는다.
   ```json
   {"batch": "2026-11-01_kr", "actor": "hermes", "finished_at": "<ISO KST>",
    "sites": {"instiz": "done", "clien": "done", "82cook": "stopped:network_unreachable", "ruliweb": "done"},
    "collector_sha256": "<수집기 파일 해시, 일본은 사용한 수집 코드 설명>",
    "notes": "사람이 알아야 할 이상 징후"}
   ```

### Claude

1. 사용자가 "핸드오프 판정 `<batch>`"를 요청하면 `HANDOFF.json`부터 읽는다.
2. `scripts/verify-handoff.py "$SEED_HARVEST_RUNS/<batch>"`로 기계 검증을 하고 결과를 `claude/verify.json`에 쓴다. 종료 코드 0이 아니면 판정하지 않는다.
   - `contract.json` 주체가 `hermes`인지 확인한다.
   - 수집기 해시가 vault 현행본과 같은지 확인한다.
   - `eligible` 본문마다 `body_sha256`을 다시 계산한다.
   - 카운터와 정지 사유를 대조한다.

   하나라도 어긋나면 판정하지 않고 그 사실을 보고한다.
3. A0 → evidence-lock → A1은 기존 결정문서와 스킬 절차를 따른다. 근거 span은 저장된 본문과 그 해시에 고정한다.
4. 현행 본문 확인이 필요한 글은 `requests/reread_<n>.json`에 쓴다(`url`·`reason`·`expected_sha256`). Claude가 robots상 허용되는 사이트는 Claude UA로 직접 확인할 수 있다.
5. 노트·로그는 vault 규칙대로 Claude가 쓴다. 노트에는 배치 이름과 수집 주체 `hermes`를 적는다. 커밋은 사용자 요청이 있을 때만 한다.

### 1단계 산출 조건

- 한국 배치 3회 이상이 `verify.json` 무결 통과
- 인스티즈·클리앙·82cook의 `date_unresolved`와 82cook 댓글 가드 실측 결과가 수집기에 반영됨
- 재독 요청 왕복이 1회 이상 실제로 이루어짐

## 2단계 — 양방향 큐와 블라인드 교차 판정 (예정)

- 배치마다 `ledger.jsonl`을 둔다. 상태는 `collected → verified → a0 → reread → a1 → noted`다. 두 에이전트는 줄을 추가만 하고 고치지 않는다. 줄마다 `actor`·`at`·`state`·`items`·`evidence`(파일 경로와 해시)를 적는다.
- **블라인드 교차 판정:** Hermes는 Claude의 판정을 보지 않고 같은 글에 A0 판정을 낸다. 서로 다른 모델이 내는 독립 재독이다. 판정이 갈린 글만 Claude가 정합화하고, 풀리지 않는 쟁점은 사용자에게 올린다.
- **selector 수리 루프:** `parser_drift`·`date_unresolved`가 나오면 Claude가 프로필과 테스트를 고친다. Hermes가 실사이트에서 확인하고 원장에 기록한다.
- 진입 조건: 1단계 산출 조건 충족과 사용자 승인

## 3단계 — 정기 운영 (예정)

- Hermes는 자체 스케줄로 매일 정해진 창을 수집하고 `HANDOFF.json`을 쓴다.
- Claude는 예약 작업으로 새 핸드오프를 찾아 판정 초안까지 만든다. 사용자가 승인하기 전에는 노트를 확정하거나 커밋하지 않는다.
- 주간 점검 지표는 레인별 수율, 정지율, 판정 불일치율, selector 드리프트다. 풀 승격·강등 판단을 이 지표로 한다. 대시보드 연결은 별도 작업이다.
- 진입 조건: 2단계 3회 이상에서 원장이 끊김 없이 이어지고, 판정 불일치율이 측정됨. 그리고 사용자 승인

## 하지 않는 것

- Claude 전용 수집 레인 신설
- 막힌 사이트를 Claude가 직접 열거나 Hermes를 통해 대리 요청하는 일
- 수집기 이원화(Hermes용 사본)
- 미달 배치를 다른 사이트·다른 날로 자동 보충하는 일
- 원문 본문을 vault·Git에 반입하는 일

## 남은 작업

- 사용자가 `SEED_HARVEST_RUNS`를 Hermes·Claude 양쪽 환경에 설정
- 첫 Hermes 한국 배치와 첫 핸드오프 판정

2026-10-31 구현 완료:
- 수집기가 robots.txt 자리의 봇 확인 HTML을 `challenge`로 멈춘다(PGR21 사례). 확인 화면이 아닌 HTML은 규칙 없음으로 읽고 `robots_html`로 남긴다.
- 1단계 기계 검증 스크립트 `scripts/verify-handoff.py`와 오프라인 회귀 12개를 추가했다. 일본 배치는 `contract.json`이 없으면 외부 수집 형식으로 보고 필수 필드와 해시를 검사한다.
