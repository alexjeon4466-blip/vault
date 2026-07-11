# Vault Dashboard Cockpit Redesign Plan

> **For Hermes:** 이 문서는 `dashboard/`를 “전체 지도”에서 “현재 비행 조종석”으로 확장하기 위한 수정 설계다. 구현 시 `tools/generate_data.py`, `dashboard/app.js`, `dashboard/style.css`, `tools/test_generate_data.py`를 작은 단위로 수정한다.

**Goal:** 대시보드가 vault 전체의 글감 지도뿐 아니라, 지금 사용자가 어느 창작 사이클(A/B/C) 어디를 지나고 있고 다음 조작이 무엇인지 즉시 보여주게 한다.

**Architecture:** 상태의 단일 진실원은 계속 `wiki/shared/maps/글감_계열_병합_지도.md`의 역할표 `상태` 열이다. 새 상태값은 만들지 않고, 4번째 열 `비고`와 산출물 존재 여부를 보조 신호로 읽어 cockpit 데이터를 생성한다. UI는 기존 창작 탭 상단에 `현재 비행` 패널을 추가하고, 기존 `오늘의 한 걸음`은 cockpit의 추천 행동과 합친다.

**Tech Stack:** 정적 HTML/CSS/JS, Python 데이터 생성기, Obsidian URI 링크.

---

## 0. 설계 원칙

1. **새 대시보드가 아니라 상단 조종석을 얹는다.** 기존 `창작 / 독서모임 / 무대까지의 거리 / 계열 서랍` 구조는 유지한다.
2. **상태값은 늘리지 않는다.** 공식 상태는 `설계 / 대기 / 조립 / 개작 / 무대` 다섯 개만 유지한다. `B2 통과`, `C1 톤 확인`, `B4 검증 필요` 같은 미세 상태는 `phaseLabel` 또는 `cockpitNote`로 표시한다.
3. **사용자 질문에 바로 답해야 한다.** 화면을 열면 “지금 C인가?”에 대해 `아직 B→C 경계`, `C1 조립 중`, `C3 개작 중`처럼 읽혀야 한다.
4. **현재작업과 전체지도는 분리한다.** 전체지도는 긴 서랍이고, cockpit은 지금 조작해야 하는 계기판이다.
5. **파일 생성 여부를 과신하지 않는다.** 산출물 파일이 있어도 계열 지도의 상태 전이가 없으면 “비공식/톤 확인/미승격”으로 표시한다.

---

## 1. 목표 화면 구조

창작 탭 상단 순서:

```text
[현재 비행]
  주력 후보: 환대는 기능 자리가 아닙니다
  현재 위치: 사이클 B4 통과 → C1 진입 대기
  다음 조작: 계열 지도 상태를 대기 반영 후 첫 장면 조립
  경고/주의: AI 제한 공모 목표 시 C1 전에 사용자 단독 집필 모드 확인

[나란히 비행 중]
  보통 인간 연수에 참석했습니다
  현재 위치: C1 톤 확인 장면 있음 / 정식 B2 구조맵 없음
  다음 조작: B2 구조맵을 만들지, 톤 스파이크로 보존할지 결정

[오늘의 한 걸음]
  환대는 기능 자리가 아닙니다 — C1 첫 장면 조립

[두 세계의 다리]
[서가/사이클 A 칩]
[무대까지의 거리]
[계열 서랍]
```

시각 은유:

- cockpit panel: 어두운 패널 + 얇은 amber border.
- `현재 위치`: 항공 고도계처럼 큰 문장.
- `다음 조작`: 가장 눈에 띄는 CTA.
- `계기 경고`: 작고 낮은 목소리. 빨간 경고는 진짜 파서/상태 불일치에만 쓴다.

---

## 2. 데이터 모델 추가

`data.js`에 새 최상위 필드 추가:

```js
window.VAULT_DATA = {
  ...,
  cockpit: {
    generatedFrom: "wiki/shared/maps/글감_계열_병합_지도.md",
    activeCycle: "B→C",
    activeQuestion: "지금 C인가?",
    primary: {
      title: "환대는 기능 자리가 아닙니다",
      link: "wiki/writing/draft-candidates/환대는_기능_자리가_아닙니다_단막후보_맵",
      lineage: "자리/환대",
      officialState: "설계",
      phaseLabel: "B2 구조맵 작성 · B4 검증 통과 · C1 진입 대기",
      phaseKind: "ready-for-c1",
      nextAction: "계열 지도 상태를 대기 반영 후 C1 첫 장면 조립",
      reason: "장소·문제·정보차·구체소재·B4 재채점이 구조맵에 존재함",
      blockers: ["상태 전이 미반영", "AI 제한 공모 목표 여부 미확인"],
      artifacts: [
        { label: "단막 후보 맵", link: "wiki/writing/draft-candidates/환대는_기능_자리가_아닙니다_단막후보_맵", kind: "B2" }
      ]
    },
    secondary: [
      {
        title: "보통 인간 연수에 참석했습니다",
        link: "wiki/writing/drafts/보통_인간_연수에_참석했습니다_첫장면",
        officialState: "설계",
        phaseLabel: "C1 톤 확인 장면 있음 · 정식 B2 구조맵 필요",
        phaseKind: "tone-spike",
        nextAction: "톤을 살릴지 결정한 뒤 B2 구조맵 작성",
        artifacts: [
          { label: "첫 장면", link: "wiki/writing/drafts/보통_인간_연수에_참석했습니다_첫장면", kind: "C1-tone" }
        ]
      }
    ],
    instruments: [
      { label: "A 사이클", value: "채점 970 / 미채점 3 / unparsed 0", status: "ok" },
      { label: "B 사이클", value: "환대 후보 B4 통과", status: "attention" },
      { label: "C 사이클", value: "정식 조립 전", status: "standby" }
    ]
  }
}
```

### `phaseKind` 값

공식 상태값이 아니라 UI용 파생 상태:

| phaseKind | 의미 | UI |
|---|---|---|
| `triage-backlog` | A 사이클 미채점/처방 대기 | 낮은 회색 |
| `designing` | 설계 상태, B2 구조화 전 | 회색 |
| `b2-map` | 구조맵 존재, B4 미확인 | 파란/중립 |
| `ready-for-c1` | B4 통과, C1 진입 가능 | amber |
| `tone-spike` | 정식 B 없이 장면/톤 확인 있음 | 보라/점선 |
| `assembling` | 공식 상태 조립 | amber + 별 |
| `revising` | 공식 상태 개작 | amber + 강한 강조 |
| `stage` | 무대 승격, cockpit에서 제외하고 작품카드 쪽으로 | hidden 또는 archive |
| `blocked` | 링크 없음/상태 불일치/필수 산출물 없음 | red 경고 |

---

## 3. 데이터 추출 규칙

### 3.1 공식 상태는 기존 그대로

- `parse_lineage_map()`은 역할표에서 `역할 / 글감 / 상태 / 비고`를 읽는다.
- 상태 열은 `설계 / 대기 / 조립 / 개작 / 무대`만 공식 상태로 인정한다.
- `비고` 열이 있으면 `note` 필드로 보존한다.

현재 코드 수정 지점:

```python
# tools/generate_data.py
# parse_lineage_map() row 처리부
role, item, st = row[0], row[1], row[2].replace("*", "").strip()
note = row[3].replace("*", "").strip() if len(row) > 3 else None
```

`cards.append()`에 추가:

```python
"role": role,
"note": note,
"stem": stem_from_cell(item),
```

### 3.2 링크 폴백 추가

계열 지도 항목이 plain text라 `link: null`인 문제가 있다. `generate_data.py`에서 다음 순서로 링크를 찾는다.

1. 셀 안 위키링크가 있으면 그대로 사용.
2. `wiki/writing/draft-candidates/<stem>_단막후보_맵.md` 존재하면 그 링크 사용.
3. `wiki/writing/draft-candidates/<stem>_구조맵.md` 존재하면 사용.
4. `wiki/writing/drafts/<stem>_첫장면.md` 존재하면 사용.
5. `wiki/writing/notes/<stem>.md` 존재하면 사용.
6. 없으면 `null`.

이 규칙만 넣어도 현재:

- `환대는 기능 자리가 아닙니다` → 단막 후보 맵 링크 가능
- `보통 인간 연수에 참석했습니다` → 첫장면 링크 가능

### 3.3 산출물 감지

새 함수:

```python
def detect_artifacts(vault_root, stem):
    candidates = [
        ("B2", "단막 후보 맵", f"wiki/writing/draft-candidates/{stem}_단막후보_맵.md"),
        ("B2", "구조맵", f"wiki/writing/draft-candidates/{stem}_구조맵.md"),
        ("C1-tone", "첫 장면", f"wiki/writing/drafts/{stem}_첫장면.md"),
        ("C1", "장면 초안", f"wiki/writing/draft-candidates/{stem}_첫장면_초안.md"),
        ("C2", "연결본", f"wiki/writing/drafts/{stem}_1-N장_연결본.md"),
        ("C2", "1막초고", f"wiki/writing/drafts/{stem}_1막초고.md"),
    ]
```

주의: 실제 파일명 관용이 다양하므로 최초 구현은 위 6개만. 나중에 glob 확장.

### 3.4 B4 통과 감지

구조맵 파일 본문에서 다음 중 하나를 찾는다.

- `B4 맵 검증형 재채점`
- `판정: **B2 통과`
- `C1 진입 가능`
- 표 안에서 A1~B5가 모두 `○`

최초 구현은 보수적으로:

```python
has_b4_pass = "B4 맵 검증형 재채점" in text and "판정: **B2 통과" in text
```

### 3.5 cockpit primary 선택 규칙

현재작업을 자동 선정하되, 과하게 똑똑하게 만들지 않는다.

1. `개작` 상태 카드 중 star 있는 것: primary.
2. 없으면 `조립` 상태 카드 중 star 있는 것.
3. 없으면 `ready-for-c1` 카드.
4. 없으면 `tone-spike` 카드.
5. 없으면 `설계` star 카드 중 첫 번째.

단, 사용자가 특정 세션에서 진행한 최신 작업을 반영하려면 `dashboard/cockpit.json` 수동 override를 허용한다.

---

## 4. 수동 override 파일

자동 추론만으로는 “오늘 네가 이걸 보고 있다”를 알기 어렵다. 그래서 작은 파일을 둔다.

Create:

```text
dashboard/cockpit.json
```

예시:

```json
{
  "primary": "환대는_기능_자리가_아닙니다",
  "secondary": ["보통_인간_연수에_참석했습니다"],
  "question": "지금 사이클 C인가?",
  "updated": "2026-07-09"
}
```

`generate_data.py`는 이 파일이 있으면:

- primary를 우선 적용
- secondary 순서를 우선 적용
- 없으면 자동 선택 규칙 사용

이 파일은 dashboard 전용 상태 표시 파일이지, 공식 파이프라인 진실원이 아니다. 공식 상태는 계속 계열 지도다.

---

## 5. UI 설계

### 5.1 HTML 변경

`dashboard/index.html` 창작 탭 안에서 `next-hero` 앞에 추가:

```html
<div id="cockpit"></div>
```

### 5.2 JS 렌더링

`dashboard/app.js`에 `renderCockpit(d.cockpit)` 추가.

렌더링 구조:

```html
<section class="cockpit-panel">
  <div class="cockpit-kicker">현재 비행</div>
  <div class="cockpit-main">
    <div>
      <div class="cockpit-label">주력 후보</div>
      <h2><a>환대는 기능 자리가 아닙니다</a></h2>
      <p class="cockpit-phase">B2 구조맵 작성 · B4 검증 통과 · C1 진입 대기</p>
    </div>
    <div class="cockpit-action">
      <span>다음 조작</span>
      <strong>계열 지도 상태를 대기 반영 후 C1 첫 장면 조립</strong>
    </div>
  </div>
  <div class="cockpit-instruments">...</div>
  <details class="cockpit-secondary">...</details>
</section>
```

### 5.3 CSS 방향

- `.cockpit-panel`: `background: linear-gradient(...)`, border amber, padding 18–22px.
- `.cockpit-phase`: 큰 문장, `font-size: 18px`.
- `.cockpit-action strong`: 다음 행동 강조.
- `.instrument.ok`: green, `.attention`: amber, `.standby`: muted, `.blocked`: red.
- 모바일에서는 세로 배치.

---

## 6. 현재 편의점 인간 계열에 적용되는 표시

현 데이터 기준 cockpit은 이렇게 보여야 한다.

### Primary

```text
주력 후보
환대는 기능 자리가 아닙니다

현재 위치
B2 구조맵 작성 · B4 검증 통과 · C1 진입 대기

다음 조작
계열 지도 상태를 대기 반영 후 C1 첫 장면 조립
```

정확한 해석:

- 공식 상태가 아직 `설계`라면: “C 아님 / C 진입 대기”.
- 계열 지도 상태를 `대기`로 바꾸면: “C 입력 준비 완료”.
- 첫 장면 초안을 만들고 상태를 `조립`으로 바꾸면: “C1 조립 중”.

### Secondary

```text
나란히 비행 중
보통 인간 연수에 참석했습니다

현재 위치
C1 톤 확인 장면 있음 · 정식 B2 구조맵 없음

다음 조작
B2 구조맵 작성 후 정식 C 편입 여부 결정
```

---

## 7. 구현 태스크

### Task 1: `cockpit.json` override 읽기

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Objective:** 수동 primary/secondary 지정 파일을 읽는다.

Steps:
1. `read_cockpit_override(vault_root)` 추가.
2. 파일 없음 → `{}` 반환.
3. JSON 파싱 실패 → `unparsed`에 경고 추가하고 `{}` 반환.
4. unit test 추가.

Verification:

```bash
python tools/test_generate_data.py
```

Expected: `OK`.

### Task 2: 계열 카드에 `role`, `note`, `stem` 보존

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Objective:** 4번째 비고 열을 cockpit이 쓸 수 있게 한다.

Steps:
1. `parse_lineage_map()`에서 `note` 추출.
2. `cards.append()`에 `role`, `note`, `stem` 추가.
3. 기존 테스트 fixture에 4열 행 추가.
4. note가 보존되는지 assert.

Verification:

```bash
python tools/test_generate_data.py
```

### Task 3: 링크 폴백 구현

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Objective:** plain text 카드도 실제 노트/맵/초안으로 연결되게 한다.

Steps:
1. `resolve_work_link(vault_root, cell, stem)` 추가.
2. `_link_from_cell()` 결과가 있으면 우선.
3. 파일 존재 순서대로 fallback.
4. `환대는_기능_자리가_아닙니다_단막후보_맵.md` fixture test 추가.

Verification:

```bash
python tools/test_generate_data.py
python tools/generate_data.py
node -c dashboard/data.js
```

### Task 4: 산출물 감지와 phaseKind 파생

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Objective:** `ready-for-c1`, `tone-spike` 같은 cockpit 상태를 계산한다.

Rules:

```text
officialState == 개작 → revising
officialState == 조립 → assembling
B2 artifact + B4 pass → ready-for-c1
C1-tone artifact + no B2 artifact → tone-spike
B2 artifact only → b2-map
else officialState == 설계 → designing
```

Verification:

```bash
python tools/test_generate_data.py
```

### Task 5: `build_cockpit()` 추가

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Objective:** data에 `cockpit` 필드를 넣는다.

Steps:
1. enriched cards 목록 생성.
2. override 적용.
3. primary/secondary 선택.
4. instruments 생성.
5. nextAction 문구 생성.

Verification:

```bash
python tools/generate_data.py
python - <<'PY'
from pathlib import Path
import json
s=Path('dashboard/data.js').read_text(encoding='utf-8')
data=json.loads(s[len('window.VAULT_DATA = '):-2])
print(data['cockpit']['primary']['title'])
PY
```

Expected current target if override exists:

```text
환대는 기능 자리가 아닙니다
```

### Task 6: cockpit UI DOM 추가

**Files:**
- Modify: `dashboard/index.html`
- Modify: `dashboard/app.js`

**Objective:** 창작 탭 상단에 cockpit 패널을 렌더링한다.

Steps:
1. `index.html`에서 `next-hero` 앞에 `<div id="cockpit"></div>` 추가.
2. `app.js`에 `renderCockpit(c)` 함수 추가.
3. 데이터 없으면 아무것도 렌더하지 않음.
4. primary, instruments, secondary details 렌더.

Verification:

```bash
node -c dashboard/app.js
```

### Task 7: cockpit CSS 추가

**Files:**
- Modify: `dashboard/style.css`

**Objective:** 조종석 느낌의 시각 계층을 만든다.

Add classes:

```css
#cockpit { margin-top: 34px; }
.cockpit-panel { ... }
.cockpit-kicker { ... }
.cockpit-main { ... }
.cockpit-phase { ... }
.cockpit-action { ... }
.cockpit-instruments { ... }
.instrument.ok / .attention / .standby / .blocked { ... }
```

Verification:

```bash
node -c dashboard/app.js
```

Then open:

```text
file:///C:/obsidian/vault/vault/dashboard/index.html
```

### Task 8: current 편의점 override 작성

**Files:**
- Create: `dashboard/cockpit.json`

Content:

```json
{
  "primary": "환대는_기능_자리가_아닙니다",
  "secondary": ["보통_인간_연수에_참석했습니다"],
  "question": "지금 사이클 C인가?",
  "updated": "2026-07-09"
}
```

Verification:

```bash
python tools/generate_data.py
```

Expected cockpit primary: `환대는 기능 자리가 아닙니다`.

### Task 9: full verification

Commands:

```bash
python tools/test_generate_data.py
python tools/generate_data.py
node -c dashboard/data.js
node -c dashboard/app.js
```

Expected:

```text
Ran 34+ tests
OK
생성 완료: ... unparsed 0
```

Also verify data shape:

```bash
python - <<'PY'
from pathlib import Path
import json
s=Path('dashboard/data.js').read_text(encoding='utf-8')
data=json.loads(s[len('window.VAULT_DATA = '):-2])
print(data['cockpit']['activeCycle'])
print(data['cockpit']['primary']['phaseLabel'])
PY
```

Expected:

```text
B→C
B2 구조맵 작성 · B4 검증 통과 · C1 진입 대기
```

---

## 8. 하지 않을 것

- 공식 상태값에 `톤확인`, `B4통과`, `C진입대기`를 추가하지 않는다.
- `script/`에는 쓰지 않는다.
- 완성작 `무대` 카드를 다시 선반에 올리지 않는다.
- 대시보드를 생산성 앱처럼 복잡한 칸반으로 만들지 않는다.
- “현재작업”을 자동 추론만으로 결정하려고 과도한 로직을 넣지 않는다. 필요하면 `cockpit.json`이 이긴다.

---

## 9. 완료 기준

1. 대시보드 상단에서 현재 주력 후보와 위치가 보인다.
2. `환대는 기능 자리가 아닙니다`가 링크와 함께 표시된다.
3. `보통 인간 연수에 참석했습니다`가 톤 확인/비공식 C1 상태로 표시된다.
4. “지금 C인가?”에 대한 답이 화면에 보인다.
5. 기존 테스트가 통과한다.
6. `python tools/generate_data.py` 결과가 `unparsed 0`이다.
