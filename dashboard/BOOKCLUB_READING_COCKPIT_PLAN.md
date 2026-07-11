# Bookclub Reading Cockpit Redesign Plan

> **For Hermes:** 이 문서는 `dashboard/`의 독서모임 탭을 “창작 글감 전초기지”가 아니라 “해석·질문·강의 조종석”으로 재설계하기 위한 구현 계획이다. 구현 시 `tools/generate_data.py`, `tools/test_generate_data.py`, `dashboard/app.js`, `dashboard/style.css`, `dashboard/index.html`를 TDD로 수정한다.

**Goal:** 독서모임 탭이 책을 “몇 개의 글감을 낳았는가”로만 보여주지 않고, 각 책이 축적한 해석 자산, 질문망, close-reading, 비교 강의, 다음 모임 발화 가능성을 독립적으로 보여주게 한다.

**Architecture:** 기존 `bookclub` 데이터는 유지하되 `bookclubReading` 또는 `readingCockpit` 필드를 추가한다. 데이터 생성기는 `wiki/bookclub/books/*/00_책카드.md`, 책 폴더의 close-reading note, `wiki/bookclub/lectures/*.md`, `wiki/shared/questions/*.md`, `wiki/writing/notes/*.md`의 링크를 읽어 책별 `readingScore`와 질문/강의/해석 축을 계산한다. UI는 독서모임 탭 상단에 `현재 독서 좌표` 패널을 추가하고, 기존 “가장 많은 글감을 낳은 책들”을 “오래 남은 책들” / “해석이 많이 열린 책들”로 바꾼다.

**Tech Stack:** 정적 HTML/CSS/JS, Python 데이터 생성기, Obsidian URI 링크, markdown frontmatter/lightweight regex parsing.

---

## 0. 문제 정의

현재 독서모임 탭은 다음 지표를 중심으로 보인다.

```text
책 수
rawTotal
원본 장치 지도 수
derivedNotes
stars
lineages
```

이 구조는 창작 파이프라인에는 유용하지만, 독서모임 탭을 이렇게 좁힌다.

> “책은 글감 생산량으로 평가된다.”

하지만 vault 안의 독서모임 자산은 더 넓다.

- 책카드의 중심 해석
- close-reading note
- 비교 강의 script
- shared question 연결
- 다음 모임에서 바로 말할 수 있는 10분 해설 축
- 책들 사이의 대조/응답 관계
- 창작과 무관하게 남는 독서의 기억

따라서 독서모임 탭의 중심 질문을 바꾼다.

```text
기존: 이 책은 몇 개의 글감을 낳았나?
변경: 이 책은 어떤 질문과 해석 좌표를 만들었나?
```

---

## 1. 목표 화면

독서모임 탭 구조를 다음 순서로 바꾼다.

```text
[현재 독서 좌표]
  살아 있는 책: 편의점 인간
  중심 질문: 보통이라는 말은 누구를 사람 밖으로 밀어내는가
  현재 쓸 수 있는 것:
    - close-reading 10개
    - 질문 연결 10개
    - 비교 강의 10개
    - 창작 파생 36개
  다음 독서모임 행동:
    정상성/견본 축을 10분 해설로 압축

[질문망]
  사람은 어떻게 사람 아닌 것이 되는가
  좋은 말은 어떻게 폭력의 재료가 되는가
  진짜와 가짜는 누가 판정하는가
  ...

[책 서가]
  편의점 인간
    해석 중심: 정상성 / 견본 / 기능 자리
    읽기 10 · 질문 10 · 비교 10 · 창작 36

[비교 강의 선반]
  편의점 인간 × 코뿔소
  편의점 인간 × 사람, 장소, 환대
  ...

[오래 남은 책들]
  단순 글감 수가 아니라 readingScore 기준 bar chart
```

---

## 2. 데이터 모델

`data.js`에 새 필드 추가:

```js
bookclubReading: {
  focus: {
    title: "편의점인간",
    cardPath: "wiki/bookclub/books/편의점인간/00_책카드",
    axis: "정상성 / 견본 / 기능 자리",
    centerQuestion: "보통이라는 말은 누구를 사람 밖으로 밀어내는가",
    nextAction: "정상성/견본 축을 10분 해설로 압축",
    metrics: {
      closeReadings: 10,
      questionLinks: 10,
      lectureLinks: 10,
      writingLinks: 36,
      derivedNotes: 26
    },
    links: {
      questions: [...],
      lectures: [...],
      closeReadings: [...]
    }
  },
  questions: [
    {
      title: "사람은 어떻게 사람 아닌 것이 되는가",
      link: "wiki/shared/questions/사람은 어떻게 사람 아닌 것이 되는가",
      books: ["편의점인간", "사람장소환대", ...],
      playsOrWriting: 12,
      strength: "strong"
    }
  ],
  books: [
    {
      title: "편의점인간",
      cardPath: "wiki/bookclub/books/편의점인간/00_책카드",
      axis: "정상성 / 견본 / 기능 자리",
      closeReadings: 10,
      questionLinks: 10,
      lectureLinks: 10,
      writingLinks: 36,
      derivedNotes: 26,
      readingScore: 86,
      topQuestions: [...],
      topLectures: [...]
    }
  ],
  lectures: [
    {
      title: "편의점인간과 코뿔소 — 보통인간과 동조의언어",
      link: "wiki/bookclub/lectures/편의점인간과_코뿔소_보통인간과_동조의언어",
      books: ["편의점인간", "코뿔소"],
      axis: "정상성이 감염/훈련/견본으로 작동하는 방식"
    }
  ]
}
```

---

## 3. 핵심 지표 정의

### 3.1 `closeReadings`

책 폴더 안의 markdown 중 다음 제외:

- `00_책카드.md`
- `00_작성브리프.md`
- 기타 `00_` 시작 파일

나머지를 close-reading/보강 note로 간주한다.

```python
close_readings = [p for p in book_dir.glob('*.md') if p.name != '00_책카드.md' and not p.name.startswith('00_')]
```

### 3.2 `questionLinks`

책카드 본문에서 `[[wiki/shared/questions/...]]` 링크 수를 센다. 중복 제거한다.

```python
question_links = extract_wikilinks(card_text, prefix='wiki/shared/questions/')
```

### 3.3 `lectureLinks`

두 방식으로 센다.

1. 책카드 본문에 직접 연결된 `wiki/bookclub/lectures/` 링크
2. `wiki/bookclub/lectures/*.md` 본문 또는 파일명에서 책 폴더명/제목이 등장하는 경우

최초 구현은 보수적으로:

- lecture 파일명에 책 폴더명 또는 책 표시명이 포함되면 연결
- lecture 본문 `sources`/`related_to`에 책카드 경로가 있으면 연결

### 3.4 `writingLinks`

책카드 본문에서 `[[wiki/writing/...]]` 링크 수. 창작 파생은 보조 지표로 표시하되, 정렬 기준의 전부가 되지 않게 한다.

### 3.5 `readingScore`

창작 파생이 너무 압도하지 않도록 가중치를 둔다.

```python
readingScore = (
  closeReadings * 4 +
  questionLinks * 3 +
  lectureLinks * 5 +
  min(writingLinks, 12) * 1 +
  min(derivedNotes, 12) * 1
)
```

의도:

- close-reading과 강의는 독서모임 고유 자산으로 크게 반영.
- question links는 해석망 자산.
- writing links/derivedNotes는 보조 반영하되 12에서 cap.

---

## 4. `axis` 추출 규칙

책카드에서 독서모임용 중심축을 추출한다.

우선순위:

1. `## 한 줄 핵심` 아래 blockquote 또는 첫 문장
2. `## 중심 질문`, `## 핵심 질문`, `## 내 해석`의 첫 문장
3. 없으면 question link 상위 2~3개 제목에서 키워드 조합
4. 그래도 없으면 `lineages` 상위 항목을 보조 축으로 사용

최초 구현은 간단히:

```python
extract_axis(card_text):
    heading candidates = ['한 줄 핵심', '핵심', '내 해석', '중심 질문']
    return first non-empty quote/list/plain line under that section, max 48 chars
```

없으면:

```text
해석 축 정리 필요
```

단 이 문구는 UI 상태 문구이지 verifier placeholder가 아니다. 원하면 `축 미정`으로 짧게 쓴다.

---

## 5. 현재 독서 좌표 선택 규칙

독서 조종석 focus는 창작 조종석과 다르게 고른다.

### 자동 선택

1. `dashboard/reading_cockpit.json` override가 있으면 그 책.
2. 없으면 `readingScore` 최상위 책.
3. 동점이면 최근 `log.md`에 언급된 책 우선.
4. 그래도 동점이면 `lectureLinks + closeReadings` 높은 책.

### override 파일

Create:

```text
dashboard/reading_cockpit.json
```

예시:

```json
{
  "focusBook": "편의점인간",
  "question": "정상성/견본 축을 독서모임에서 어떻게 말할까?",
  "nextAction": "편의점 인간 × 코뿔소 × 사람, 장소, 환대 10분 해설 압축",
  "updated": "2026-07-09"
}
```

이 파일은 독서모임 조종석 초점만 지정한다. 책카드나 질문망의 공식 진실원이 아니다.

---

## 6. UI 설계

### 6.1 `dashboard/index.html`

독서모임 탭 안에서 `bc-summary` 앞에 추가:

```html
<div id="reading-cockpit"></div>
```

현재:

```html
<section id="tab-bookclub" role="tabpanel" hidden>
  <div id="bc-summary"></div>
```

변경:

```html
<section id="tab-bookclub" role="tabpanel" hidden>
  <div id="reading-cockpit"></div>
  <div id="bc-summary"></div>
```

### 6.2 `dashboard/app.js`

새 함수:

```js
function renderReadingCockpit(r) { ... }
```

표시 요소:

- `현재 독서 좌표`
- focus book title + link
- axis
- center question
- nextAction
- metrics chips: 읽기 / 질문 / 비교 / 창작
- top question links
- top lecture links

기존 독서모임 요약 문장도 수정:

현재:

```js
"함께 읽은 N권 가운데 M권이 글감이 되었습니다..."
```

변경:

```js
"함께 읽은 N권 가운데 M권이 글감으로도 이어졌고, Q개의 질문과 L개의 비교 강의가 독서의 좌표를 만들고 있습니다."
```

### 6.3 제목 변경

현재 HTML:

```html
<h2>가장 많은 글감을 낳은 책들</h2>
<div id="bc-flow"></div>
```

변경:

```html
<h2>오래 남은 책들</h2>
<div id="bc-flow"></div>
```

`bc-flow` bar는 `derivedNotes`가 아니라 `readingScore` 기준으로 그린다.

### 6.4 책 카드 표시 변경

현재:

```text
글감 26 · 신설 정상성/견본, 공동체/명단...
```

변경:

```text
정상성 / 견본 / 기능 자리
읽기 10 · 질문 10 · 비교 10 · 창작 36
글감 파생 26
```

창작 파생은 마지막 줄로 낮춘다.

---

## 7. 구현 태스크

### Task 1: 테스트 — bookclub reading metrics

**Objective:** 책카드/폴더/강의/질문 링크로 독서모임 지표를 계산하는 테스트를 먼저 추가한다.

**Files:**
- Modify: `tools/test_generate_data.py`

**Test fixture:**

- `wiki/bookclub/books/편의점인간/00_책카드.md`
- `wiki/bookclub/books/편의점인간/01_죽은_새.md`
- `wiki/bookclub/books/편의점인간/02_몸이_약해서.md`
- `wiki/bookclub/lectures/편의점인간과_코뿔소_보통인간과_동조의언어.md`
- question links in card
- writing links in card

**Expected:**

```python
book = metrics['books'][0]
assert book['title'] == '편의점인간'
assert book['closeReadings'] == 2
assert book['questionLinks'] == 2
assert book['lectureLinks'] == 1
assert book['writingLinks'] == 1
assert book['readingScore'] > book['derivedNotes']
```

Run:

```bash
python tools/test_generate_data.py
```

Expected RED: `AttributeError: module 'generate_data' has no attribute 'scan_bookclub_reading'`.

### Task 2: Implement `extract_wikilinks()` and `scan_bookclub_reading()`

**Files:**
- Modify: `tools/generate_data.py`

Add helpers:

```python
def extract_wikilinks(text, prefix=None): ...
def path_to_note_link(path, vault_root): ...
def extract_axis(text): ...
def scan_bookclub_reading(vault_root, bookclub): ...
```

Use existing `bookclub` data so `derivedNotes` remains available.

Run:

```bash
python tools/test_generate_data.py
```

Expected GREEN.

### Task 3: lecture association test and implementation

**Objective:** lecture filename/body association works even when bookcard does not link lecture directly.

**Test:** lecture file named `편의점인간과_코뿔소_...md` should count for `편의점인간` and `코뿔소` if both book folders exist.

Potential simple implementation:

```python
if book_dir.name in lecture.stem:
    linked.append(lecture)
```

Also inspect body links:

```python
if book.cardPath in extract_wikilinks(lecture_text): ...
```

### Task 4: reading cockpit override

**Files:**
- Create: `dashboard/reading_cockpit.json`
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

Override example:

```json
{
  "focusBook": "편의점인간",
  "question": "정상성/견본 축을 독서모임에서 어떻게 말할까?",
  "nextAction": "편의점 인간 × 코뿔소 × 사람, 장소, 환대 10분 해설 압축",
  "updated": "2026-07-09"
}
```

Expected generated focus:

```python
assert data['bookclubReading']['focus']['title'] == '편의점인간'
```

### Task 5: add `bookclubReading` to `build_data()`

**Files:**
- Modify: `tools/generate_data.py`

Inside `build_data()` after `bookclub = scan_books(...)`:

```python
bookclub_reading = scan_bookclub_reading(vault_root, bookclub)
```

Then:

```python
"bookclubReading": bookclub_reading,
```

Run:

```bash
python tools/generate_data.py
node -c dashboard/data.js
```

Expected:

```text
생성 완료 ... unparsed 0
```

### Task 6: HTML slot and title changes

**Files:**
- Modify: `dashboard/index.html`

Changes:

```html
<div id="reading-cockpit"></div>
```

and:

```html
<h2>오래 남은 책들</h2>
```

### Task 7: renderReadingCockpit UI

**Files:**
- Modify: `dashboard/app.js`

Add after bookclub tab setup:

```js
renderReadingCockpit(d.bookclubReading);
```

Render:

- focus book title/link
- axis
- question
- next action
- metric chips
- top questions
- top lectures

Also modify book card rendering to use reading metrics:

```js
var rb = readingByTitle[b.title]
card.appendChild(el('div', 'book-axis', rb.axis))
card.appendChild(el('div', 'tags', '읽기 X · 질문 Y · 비교 Z · 창작 W'))
card.appendChild(el('div', 'tags dim', '글감 파생 N'))
```

### Task 8: CSS for reading cockpit

**Files:**
- Modify: `dashboard/style.css`

Add classes parallel to cockpit but less “flight” and more “reading desk / atlas”.

Suggested classes:

```css
#reading-cockpit { margin-top: 32px; }
.reading-panel { ... border: 1px solid rgba(79,157,105,.45); }
.reading-kicker { color: var(--ok); }
.reading-axis { font-size: 18px; }
.reading-metrics { display: flex; flex-wrap: wrap; gap: 8px; }
.reading-chip { ... }
.reading-links { ... }
.book-axis { color: var(--text); font-size: 13px; margin-top: 4px; }
.tags.dim { color: var(--dim); }
```

### Task 9: change `bc-flow` to readingScore

**Files:**
- Modify: `dashboard/app.js`

Current:

```js
var top = bc.books.slice(0, 10).filter(function (b) { return b.derivedNotes > 0; });
var maxD = Math.max(... derivedNotes ...)
bar.style.width = (b.derivedNotes / maxD) * 60 + "%";
```

Change to:

```js
var rb = d.bookclubReading.books.slice(0, 10);
var maxD = Math.max(... readingScore ...)
bar.style.width = (b.readingScore / maxD) * 60 + "%";
label = b.title
value = b.readingScore + "점"
```

### Task 10: full verification

Run:

```bash
python tools/test_generate_data.py
python tools/generate_data.py
node -c dashboard/app.js
node -c dashboard/data.js
python - <<'PY'
from pathlib import Path
import json
s=Path('dashboard/data.js').read_text(encoding='utf-8')
js=s[len('window.VAULT_DATA = '):]
if js.endswith(';\n'): js=js[:-2]
data=json.loads(js)
r=data['bookclubReading']
print('READING_FOCUS', r['focus']['title'])
print('READING_AXIS', r['focus']['axis'])
print('READING_METRICS', r['focus']['metrics'])
print('READING_TOP', [(b['title'], b['readingScore']) for b in r['books'][:5]])
print('UNPARSED', len(data['unparsed']))
PY
```

Expected:

```text
Ran 38+ tests
OK
생성 완료 ... unparsed 0
READING_FOCUS 편의점인간
UNPARSED 0
```

---

## 8. 현재 vault 기준 예상값

이미 quick scan한 결과, 현재 상위 독서 자산은 대략 다음과 같다.

```text
편의점인간: close-reading 10 / question links 10 / lecture links 10 / writing links 36
궤도: question 11 / lecture 6 / writing 70
남아있는나날: close-reading 1 / question 13 / lecture 3 / writing 9
서사의위기: close-reading 3 / question 4 / lecture 10 / writing 57
마션: close-reading 5 / question 9 / lecture 2 / writing 78
```

따라서 override 없이도 편의점인간이 상단에 올 가능성이 높지만, 이번 작업 맥락을 반영해 `reading_cockpit.json`으로 focus를 고정한다.

---

## 9. 하지 않을 것

- 독서모임 탭에서 창작 파생을 숨기지는 않는다. 다만 마지막/보조 지표로 낮춘다.
- 책의 가치를 `derivedNotes` 하나로 정렬하지 않는다.
- question note를 새로 만들지 않는다. 이 작업은 dashboard 표시/데이터 생성만 다룬다.
- 책카드 내용을 대량 수정하지 않는다.
- 독서모임 탭을 별도의 복잡한 BI 대시보드로 만들지 않는다. “다음 모임에서 무엇을 말할 수 있나”가 중심이다.

---

## 10. 완료 기준

1. 독서모임 탭 상단에 `현재 독서 좌표`가 보인다.
2. focus book이 글감 수가 아니라 해석 축/질문/강의/close-reading 지표로 표시된다.
3. 책 서가 카드가 `읽기 / 질문 / 비교 / 창작`을 분리해 보여준다.
4. `가장 많은 글감을 낳은 책들`이 `오래 남은 책들`로 바뀌고 `readingScore` 기준으로 정렬된다.
5. `편의점인간`은 정상성/견본 축의 독서모임 자산으로 보인다.
6. 기존 창작 cockpit은 그대로 작동한다.
7. `python tools/test_generate_data.py`, `python tools/generate_data.py`, `node -c dashboard/app.js`, `node -c dashboard/data.js`가 통과한다.
