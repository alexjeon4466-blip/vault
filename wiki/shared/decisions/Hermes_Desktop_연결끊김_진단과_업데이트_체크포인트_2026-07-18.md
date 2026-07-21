---
type: decision-note
status: stable
created: 2026-07-18
updated: 2026-07-18
visibility: private
title: "Hermes Desktop 연결 끊김 — 이벤트 루프 정지 진단·업데이트 체크포인트"
sources:
  - "https://hermes-agent.nousresearch.com/docs/getting-started/updating"
  - "https://github.com/NousResearch/hermes-agent/commit/e73adb50437a591979e6d63eb1d63b79dbfd267c"
  - "https://github.com/NousResearch/hermes-agent/commit/ebb81f10cb70c4c37a2d00ef58a8aea37e7971f2"
connected_questions: []
related_to:
  - "[[wiki/shared/decisions/README|Decision note 운영]]"
  - "[[SCHEMA]]"
belongs_to:
  - "[[wiki/shared/decisions/README|Decision note 운영]]"
has: []
decision_status: decided
review_date:
---

# Hermes Desktop 연결 끊김 — 이벤트 루프 정지 진단·업데이트 체크포인트

## 현재 결정

2026-07-18에 반복된 Hermes Desktop 연결 끊김은 인터넷·OpenAI 인증 장애가 아니라, **Desktop과 로컬 Hermes 백엔드를 잇는 WebSocket이 대형·동시 작업 중 이벤트 루프 정지로 끊어진 문제**로 판정한다.

Hermes를 `v0.18.2`로 업데이트하고 설정을 v33으로 마이그레이션했다. 이번 문제와 직접 관련된 두 수정 커밋이 현재 설치본에 포함됐고 `hermes doctor`가 전체 통과했으므로, 현재 상태는 **업데이트 완료·정상 사용 관찰 단계**로 닫는다.

```yaml
current_state: updated-and-observing
root_cause: local-websocket-event-loop-stall-under-heavy-concurrent-work
provider_auth_status: openai-codex-ok
config_status: v33-current
diagnostic_status: doctor-all-checks-passed
relevant_fixes: included
next_action: normal-use-observation
```

## 재현 당시의 증거

2026-07-18 실측 로그에서 다음 순서가 확인됐다.

1. Desktop 연결 상대는 외부 서버가 아니라 `127.0.0.1`의 로컬 백엔드였다.
2. `ws write slow (loop stalled >10.0s)`가 여러 차례 반복됐다.
3. 이어 `WebSocketDisconnect`, `send_failed_after_response`, 재접속 직후 `ready_send_failed`가 발생했다.
4. 같은 시간 OpenAI Codex 모델 요청은 정상 완료됐다.
5. 연결 종료 시 세 개의 작업 세션이 분리되어 있었다.

따라서 외부 인터넷이나 모델 제공자 연결이 먼저 끊어진 것이 아니라, 백엔드 작업이 이벤트 루프를 오래 점유하면서 Desktop 표시 연결이 응답하지 못한 것으로 본다.

## 부하를 키운 조건

재현 시점에는 다음이 겹쳤다.

- 여러 장기 세션의 동시 실행
- 세션별 약 10만–20만 토큰 규모의 컨텍스트
- 여러 세션의 자동 압축
- 대용량 로그·파일 결과 처리
- 동시 세션 상한이 설정되지 않은 상태
- 설치본이 당시 최신 `main`보다 크게 뒤처진 상태

이 조건은 원인과 트리거를 구분해 읽는다. 핵심 결함은 로컬 WebSocket이 이벤트 루프 정지를 견디지 못한 것이고, 대형·동시 세션은 그 결함을 드러낸 부하 조건이다.

## 실행한 조치

### 1. Hermes 업데이트

공식 업데이트 절차에 따라 설치본을 `v0.17.0`에서 `v0.18.2`로 갱신했다.

현재 설치본에는 다음 수정이 포함되어 있다.

- 로컬 loopback 연결에서 WebSocket keepalive ping이 이벤트 루프 정지 때문에 정상 연결을 끊지 않도록 하는 수정
- GIL 압력 아래 WebSocket 스트리밍 프레임을 병합하고 연결 안정성을 높이는 수정

### 2. 설정 마이그레이션

- 설정 버전: `31 → 33`
- 폐기된 `delegation.max_async_children` 제거
- `delegation.max_concurrent_children`가 백그라운드 위임까지 제한하는 현행 구조로 전환

### 3. 사후 검증

다음을 실제 실행해 확인했다.

```text
hermes version
hermes update --check
hermes config check
hermes doctor
hermes status --all
```

검증 결과:

- Hermes `v0.18.2`
- 설정 v33 최신
- OpenAI Codex 인증 정상
- Gateway 실행 정상
- `hermes doctor`: `All checks passed`
- 연결 끊김 관련 두 수정 커밋 포함

업데이트 직후 `main`이 계속 이동해 소수 커밋 뒤로 표시된 것은 업데이트 실패가 아니다. 위 두 수정의 포함 여부를 별도로 검증했다.

## Teams·Google Chat 경고 해석

마이그레이션 중 다음 경고가 나왔다.

```text
platform 'teams' references unknown toolset 'hermes-teams'
platform 'google_chat' references unknown toolset 'hermes-google_chat'
```

현재 두 플랫폼은 구성되어 있지 않고 해당 플러그인도 활성화하지 않았다. 과거 플랫폼별 toolset 참조가 설정에 남아 경고가 발생한 것으로, 현재 사용하는 Desktop·OpenAI Codex·Telegram에는 영향을 주지 않는다.

두 플랫폼을 실제로 도입할 때만 `hermes gateway setup`과 플러그인 상태를 함께 재검토한다. 경고를 없애기 위해 사용하지 않는 플랫폼 플러그인을 임의로 활성화하지 않는다.

## 운영 안전선

업데이트 이후에도 다음 원칙을 권장한다.

1. 장기 대화가 15만–18만 토큰 이상으로 커지거나 압축이 반복되면 산출물을 저장하고 `/new`로 넘긴다.
2. 대형 리서치·다중 파일 처리·여러 위임을 수행하는 장기 세션을 세 개 이상 동시에 돌리지 않는다.
3. 안정성을 우선할 때만 동시 세션 상한을 2로 둔다.

```text
hermes config set max_concurrent_sessions 2
```

현재 체크포인트에서는 상한을 강제로 설정하지 않았다. WebSocket 수정이 포함된 새 버전을 먼저 정상 사용하면서 관찰한다.

## 재발 시 판별 절차

업데이트 후 다시 끊기면 발생 시각을 먼저 기록하고 다음 순서로 확인한다.

1. `hermes status --all`로 Gateway와 활성 세션 수를 확인한다.
2. 같은 시각에 `ws write slow`, `event loop stalled`, `WebSocketDisconnect`, `ready_send_failed`가 있는지 본다.
3. 같은 시간 모델 API 요청이 성공했는지, 401·403·429·5xx·timeout이 있었는지 분리한다.
4. 한 개의 새 세션에서도 재현되면 동시 세션 부하가 아닌 업데이트 후 회귀 가능성으로 취급한다.
5. 재현 로그와 `hermes doctor` 결과를 묶어 `/debug` 또는 공식 이슈 보고 대상으로 올린다.

## 재검토 조건

다음 중 하나가 발생하면 이 체크포인트를 다시 연다.

- 업데이트 후 한 개의 새 세션에서도 동일한 로컬 WebSocket 종료가 재현된다.
- `hermes doctor`가 연결·설정·버전 오류를 새로 보고한다.
- Teams 또는 Google Chat을 실제로 구성해 잔여 toolset 경고가 기능에 영향을 준다.
- 장기 동시 작업이 다시 잦아져 `max_concurrent_sessions: 2`를 운영 기본값으로 채택할 필요가 생긴다.

그 전까지는 추가 설정 변경이나 재설치를 자동 실행하지 않는다.

## 관련 노트

- [[wiki/shared/decisions/README|Decision note 운영]]
- [[SCHEMA|LLM Wiki v2 Schema]]

## log.md에 남길 한 줄

- 결정: Hermes Desktop 반복 단절은 대형·동시 작업 중 로컬 WebSocket 이벤트 루프 정지로 판정했고, v0.18.2 업데이트·설정 v33 마이그레이션·관련 수정 포함·Doctor 전체 통과를 확인한 뒤 정상 사용 관찰 단계로 닫았다.
