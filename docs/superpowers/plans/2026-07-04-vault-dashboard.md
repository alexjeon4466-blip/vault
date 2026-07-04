# Vault 대시보드 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Obsidian vault를 스캔해 `dashboard/data.js`를 생성하는 Python 스크립트와, 그 데이터를 렌더링하는 정적 대시보드(탭 2개: 창작/독서모임)를 만든다.

**Architecture:** `tools/generate_data.py`(표준 라이브러리만)가 vault의 마크다운을 파싱해 `window.VAULT_DATA = {...}` 형태의 `dashboard/data.js` 하나만 쓴다. `dashboard/index.html + app.js + style.css`는 정적이며 `file://`과 http 양쪽에서 동작한다. 차트는 순수 CSS(conic-gradient 도넛, flex 스택 바, width% 막대).

**Tech Stack:** Python 3 (stdlib only: `re`, `json`, `pathlib`, `datetime`, `sys`, `unittest`), 순수 HTML/CSS/JS (의존성 0).

**Spec:** `docs/superpowers/specs/2026-07-04-vault-dashboard-design.md` (v2) — 모든 파싱 규칙·화면 규칙의 원전. 이 계획과 스펙이 충돌하면 스펙이 이긴다.

## Global Constraints

- Python 표준 라이브러리만. 외부 패키지·pip 금지.
- **모든 `open()`/`read_text()`/`write_text()`에 `encoding="utf-8"` 명시** (Windows 기본 cp949). 읽기는 `errors="replace"`.
- 쓰기 대상은 `dashboard/data.js` **단 하나**. `wiki/`, `bookclub/`, `script/`는 읽기 전용.
- 경로는 전부 `__file__` 기준: `VAULT_ROOT = Path(__file__).resolve().parent.parent`. cwd 의존 금지.
- `.bat` 파일 내용은 100% ASCII (파일명 한글은 허용).
- 프론트엔드: 외부 CDN·웹폰트·JS 라이브러리 금지. `dashboard/` 폴더째 복사만으로 동작.
- obsidian:// 링크는 `location.protocol === "file:"`일 때만 생성.
- 직렬화: `json.dumps(..., ensure_ascii=False, indent=2)`.
- 파싱 실패는 예외로 죽지 않고 `unparsed`에 `{file, reason}`으로 수집.
- 커밋 메시지 끝에 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` 붙일 것.
- 테스트 실행 명령: `py -3 -m unittest tools.test_generate_data -v` (vault 루트 `C:\obsidian\vault\vault`에서). `py`가 없으면 `python`으로 대체.

## 파일 구조 (전체)

| 파일 | 책임 |
|---|---|
| `tools/generate_data.py` | vault 스캔 → data.js 생성. 파서 함수 전부 이 파일 (단일 스크립트, ~500줄) |
| `tools/test_generate_data.py` | 파서 단위 테스트 (unittest, 임시 디렉터리 픽스처) |
| `tools/대시보드_갱신.bat` | 생성 + 브라우저 오픈 (ASCII) |
| `dashboard/index.html` | 정적 셸: 헤더, 탭 2개, 폴백 화면 |
| `dashboard/style.css` | 다크 테마, CSS 차트, 반응형 |
| `dashboard/app.js` | `window.VAULT_DATA` → DOM 렌더링 |
| `dashboard/data.js` | 생성물 (Task 8부터 실데이터) |

---

### Task 1: 스캐폴드 + frontmatter 파서 + source 정규화

**Files:**
- Create: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Produces: `parse_frontmatter(text: str) -> dict` (키: 문자열 값 또는 리스트), `normalize_source(s: str) -> str`, `read_text(path: Path) -> str`, 상수 `VAULT_ROOT: Path`, `OUTPUT: Path`

- [ ] **Step 1: 실패하는 테스트 작성**

`tools/test_generate_data.py` 생성:

```python
# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_data as g


class TestFrontmatter(unittest.TestCase):
    def test_scalar_and_list(self):
        text = (
            '---\n'
            'type: writing-note-evaluation\n'
            'title: "출처 확인 중인 위로 — 평가 완료"\n'
            'sources:\n'
            '  - "wiki/writing/notes/출처_확인_중인_위로.md"\n'
            '---\n\n# 본문\n'
        )
        fm = g.parse_frontmatter(text)
        self.assertEqual(fm["type"], "writing-note-evaluation")
        self.assertEqual(fm["sources"], ["wiki/writing/notes/출처_확인_중인_위로.md"])

    def test_no_frontmatter(self):
        self.assertEqual(g.parse_frontmatter("# 그냥 본문"), {})


class TestNormalizeSource(unittest.TestCase):
    def test_four_variants(self):
        key = "wiki/bookclub/books/궤도/00_책카드"
        self.assertEqual(g.normalize_source('"wiki/bookclub/books/궤도/00_책카드.md"'), key)
        self.assertEqual(g.normalize_source("wiki/bookclub/books/궤도/00_책카드.md"), key)
        self.assertEqual(g.normalize_source('"[[wiki/bookclub/books/궤도/00_책카드]]"'), key)
        self.assertEqual(g.normalize_source("[[wiki/bookclub/books/궤도/00_책카드|궤도]]"), key)

    def test_raw_path_with_space(self):
        self.assertEqual(
            g.normalize_source('"bookclub/석촌호수책모임/_혼모노_ 성해나.md"'),
            "bookclub/석촌호수책모임/_혼모노_ 성해나")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `cd C:\obsidian\vault\vault && py -3 -m unittest tools.test_generate_data -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_data'` (파일 없음)

- [ ] **Step 3: 최소 구현**

`tools/generate_data.py` 생성:

```python
# -*- coding: utf-8 -*-
"""vault 스캔 → dashboard/data.js 생성. 쓰기 대상은 OUTPUT 하나뿐."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = VAULT_ROOT / "dashboard" / "data.js"

KNOWN_TOTALS = {"scored": 228, "stars": 33, "twins": 113}  # 정합성 경고용 (실패 아님)


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text):
    """--- 블록에서 스칼라와 1단계 리스트만 추출. 그 이상은 필요 없음."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data, key = {}, None
    for line in text[3:end].splitlines():
        if not line.strip():
            continue
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            data[key] = val.strip('"') if val else []
        elif line.lstrip().startswith("- ") and isinstance(data.get(key), list):
            data[key].append(line.lstrip()[2:].strip().strip('"'))
    return data


def normalize_source(s):
    """sources 4변형(따옴표/plain/wikilink/별칭)을 비교 키로 정규화."""
    s = s.strip().strip('"').strip()
    if s.startswith("[[") and s.endswith("]]"):
        s = s[2:-2]
    s = s.split("|")[0].strip()
    if s.endswith(".md"):
        s = s[:-3]
    return s
```

- [ ] **Step 4: 통과 확인**

Run: `py -3 -m unittest tools.test_generate_data -v`
Expected: PASS (테스트 4개)

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): scaffold generator with frontmatter and source parsers"
```

---

### Task 2: 판정·계열 추출기 + 표 행 분할기

**Files:**
- Modify: `tools/generate_data.py` (함수 추가)
- Test: `tools/test_generate_data.py` (클래스 추가)

**Interfaces:**
- Produces: `extract_verdict(text) -> tuple[str|None, str|None]` (판정, 괄호한정어), `parse_verdict_cell(cell) -> tuple[str|None, str|None]`, `extract_lineage(text) -> str|None`, `split_row(line) -> list[str]`, `extract_tables(text) -> list[list[list[str]]]`, `stem_from_cell(cell) -> str`

- [ ] **Step 1: 실패하는 테스트 작성** — `tools/test_generate_data.py`에 추가:

```python
class TestVerdict(unittest.TestCase):
    def test_twin_variants(self):
        # 실측 변형 5종 (스펙 파싱 규칙 1)
        self.assertEqual(g.extract_verdict("- 판정: **유망★** / 채점: ..."), ("유망★", None))
        self.assertEqual(g.extract_verdict("- 판정: 유망★ (8축 만점) / 운반체 후보"), ("유망★", "8축 만점"))
        self.assertEqual(g.extract_verdict("- 판정: **유망★ — 집필 대기 큐 4순위**"), ("유망★", None))
        self.assertEqual(g.extract_verdict("- 판정: **유망** (소품 규격) / 채점"), ("유망", "소품 규격"))
        self.assertEqual(g.extract_verdict("- 판정: **병합** / 채점: A1○"), ("병합", None))
        self.assertIsNone(g.extract_verdict("판정 없음 본문")[0])

    def test_map_cell_variants(self):
        self.assertEqual(g.parse_verdict_cell("**유망★(흡수)**"), ("유망★", "흡수"))
        self.assertEqual(g.parse_verdict_cell("**병합(모체)**"), ("병합", "모체"))
        self.assertEqual(g.parse_verdict_cell("유망(소품)"), ("유망", "소품"))
        self.assertEqual(g.parse_verdict_cell("**진행 중**"), ("진행 중", None))
        self.assertEqual(g.parse_verdict_cell("**유망★**"), ("유망★", None))


class TestLineage(unittest.TestCase):
    def test_cut_at_punctuation(self):
        self.assertEqual(g.extract_lineage("- 계열: 결함/생존 (신규 — 노인과바다×고래 유입)."), "결함/생존")
        self.assertEqual(g.extract_lineage("- 계열: 진짜/출처 운반체 후보. **집필 후보 검토 대상.**"),
                         "진짜/출처 운반체 후보")
        self.assertEqual(g.extract_lineage("- 계열: 말/작별 · 노동 교차."), "말/작별 · 노동 교차")
        self.assertIsNone(g.extract_lineage("계열 언급 없음"))


class TestTable(unittest.TestCase):
    def test_split_row_with_wikilink_pipe(self):
        # 위키링크 내부 |는 셀 구분자가 아니다 (배치 1~6 실측 형식)
        cells = g.split_row("| [[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]] | △ △ △ | **병합** |")
        self.assertEqual(len(cells), 3)
        self.assertEqual(cells[0], "[[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]]")

    def test_stem_from_cell(self):
        self.assertEqual(g.stem_from_cell("[[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]]"), "3_8초_지연")
        self.assertEqual(g.stem_from_cell("[[wiki/writing/notes/그늘은_예약할_수_없습니다|그늘]]"), "그늘은_예약할_수_없습니다")
        self.assertEqual(g.stem_from_cell("**출처_확인_중인_위로**"), "출처_확인_중인_위로")

    def test_extract_tables(self):
        text = ("앞 문장\n\n| 글감 | 판정 |\n|---|---|\n| 왜요 | 유망 |\n| 흼_설명회 | 병합 |\n\n뒤 문장\n")
        tables = g.extract_tables(text)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0][0], ["글감", "판정"])   # 헤더 행
        self.assertEqual(len(tables[0]), 3)                  # 구분선 제외 헤더+데이터 2
```

- [ ] **Step 2: 실패 확인**

Run: `py -3 -m unittest tools.test_generate_data -v`
Expected: FAIL — `AttributeError: module 'generate_data' has no attribute 'extract_verdict'`

- [ ] **Step 3: 구현** — `tools/generate_data.py`에 추가:

```python
_VERDICT_WORDS = r'(유망★?|병합|보류|제외|진행 중|맵)'
_TWIN_VERDICT_RE = re.compile(r'판정[::]\s*\**\s*' + _VERDICT_WORDS)
_QUALIFIER_RE = re.compile(r'[\((]([^)\)]*)[\))]')
_LINEAGE_RE = re.compile(r'^\s*-?\s*계열:\s*(.+)$', re.M)


def _qualifier_after(text, start):
    """판정어 직후의 괄호 한정어만 취한다 (뒤쪽 아무 괄호나 잡지 않게 30자 제한)."""
    m = _QUALIFIER_RE.match(text[start:start + 30].lstrip("*").strip())
    return m.group(1).strip() if m else None


def extract_verdict(text):
    m = _TWIN_VERDICT_RE.search(text)
    if not m:
        return (None, None)
    return (m.group(1), _qualifier_after(text, m.end()))


def parse_verdict_cell(cell):
    flat = cell.replace("*", "").strip()
    m = re.match(_VERDICT_WORDS, flat)
    if not m:
        return (None, None)
    q = _QUALIFIER_RE.search(flat[m.end():m.end() + 30])
    return (m.group(1), q.group(1).strip() if q else None)


def extract_lineage(text):
    m = _LINEAGE_RE.search(text)
    if not m:
        return None
    val = re.split(r'[.(（—]', m.group(1))[0].strip()
    return val or None


def split_row(line):
    """마크다운 표 행 → 셀 리스트. [[...]] 내부와 \\| 이스케이프의 |는 구분자가 아님."""
    cells, buf, depth, i = [], "", 0, 0
    while i < len(line):
        two = line[i:i + 2]
        if two == "[[":
            depth += 1; buf += two; i += 2; continue
        if two == "]]":
            depth = max(0, depth - 1); buf += two; i += 2; continue
        if two == "\\|":
            buf += "|"; i += 2; continue
        ch = line[i]
        if ch == "|" and depth == 0:
            cells.append(buf.strip()); buf = ""
        else:
            buf += ch
        i += 1
    cells.append(buf.strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def extract_tables(text):
    """연속된 | 행 묶음들을 표로. 구분선(|---|) 행은 버림."""
    tables, current = [], []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            if re.match(r'^\s*\|[\s:\-|]+\|?\s*$', line):
                continue
            current.append(split_row(line))
        else:
            if current:
                tables.append(current); current = []
    if current:
        tables.append(current)
    return tables


def stem_from_cell(cell):
    """글감 셀 → 파일 스템. 위키링크면 타깃 경로의 마지막 조각, _scored 접미사 제거."""
    m = re.search(r'\[\[([^\]|]+)', cell)
    name = (m.group(1).split("/")[-1] if m else cell.replace("*", "").strip())
    if name.endswith("_scored"):
        name = name[:-len("_scored")]
    return name.strip()
```

- [ ] **Step 4: 통과 확인**

Run: `py -3 -m unittest tools.test_generate_data -v`
Expected: PASS (누적 테스트 전부)

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): verdict/lineage extractors and pipe-safe table parser"
```

---

### Task 3: 평가 쌍둥이 스캐너

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Consumes: `parse_frontmatter`, `extract_verdict`, `extract_lineage`, `read_text`
- Produces: `scan_twins(vault_root: Path, unparsed: list) -> dict[str, dict]` — 키는 원본 스템, 값은 `{"verdict", "qualifier", "lineage", "path"}` (path는 vault 상대 POSIX, `.md` 없음)

- [ ] **Step 1: 실패하는 테스트 작성** — 추가:

```python
import tempfile


def make_vault(files):
    """dict{상대경로: 내용} → 임시 vault 루트 Path. 호출자가 TemporaryDirectory 관리."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return tmp, root


TWIN = ('---\ntype: writing-note-evaluation\nsources:\n  - "wiki/writing/notes/왜요.md"\n---\n'
        '# 왜요 — 평가 완료\n- 판정: **유망** (소품 규격) / 채점: A1○\n- 계열: 말/작별 · 노동 교차.\n')
FAKE_TWIN = ('---\ntype: writing-note\n---\n# 1차 개명 원본\n- 판정: **유망** 처방이 본문에 있음\n')


class TestScanTwins(unittest.TestCase):
    def test_type_gate_and_extraction(self):
        tmp, root = make_vault({
            "wiki/writing/notes/왜요_scored.md": TWIN,
            "wiki/writing/notes/관심_지도_scored.md": FAKE_TWIN,   # type이 달라 무시돼야 함
        })
        with tmp:
            unparsed = []
            twins = g.scan_twins(root, unparsed)
            self.assertIn("왜요", twins)
            self.assertNotIn("관심_지도", twins)      # 이중 계상 방지 (스펙 파싱 규칙 1)
            self.assertEqual(twins["왜요"]["verdict"], "유망")
            self.assertEqual(twins["왜요"]["lineage"], "말/작별 · 노동 교차")
            self.assertEqual(twins["왜요"]["path"], "wiki/writing/notes/왜요")
            self.assertEqual(unparsed, [])

    def test_missing_verdict_goes_unparsed(self):
        broken = '---\ntype: writing-note-evaluation\n---\n# 깨진 쌍둥이\n판정 줄이 없다\n'
        tmp, root = make_vault({"wiki/writing/notes/깨짐_scored.md": broken})
        with tmp:
            unparsed = []
            twins = g.scan_twins(root, unparsed)
            self.assertNotIn("깨짐", twins)
            self.assertEqual(len(unparsed), 1)
            self.assertIn("판정", unparsed[0]["reason"])
```

- [ ] **Step 2: 실패 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: FAIL (`scan_twins` 없음)

- [ ] **Step 3: 구현** — 추가:

```python
def scan_twins(vault_root, unparsed):
    """type: writing-note-evaluation 파일만 쌍둥이로 인정 (파일명 글롭만으로는 이중 계상)."""
    twins = {}
    notes = vault_root / "wiki" / "writing" / "notes"
    if not notes.is_dir():
        return twins
    for p in sorted(notes.glob("*_scored.md")):
        text = read_text(p)
        if parse_frontmatter(text).get("type") != "writing-note-evaluation":
            continue
        stem = p.stem[:-len("_scored")]
        verdict, qualifier = extract_verdict(text)
        if verdict is None:
            unparsed.append({"file": p.name, "reason": "쌍둥이에서 판정 추출 실패"})
            continue
        twins[stem] = {
            "verdict": verdict,
            "qualifier": qualifier,
            "lineage": extract_lineage(text),   # 부재 시 None — 지도 폴백은 build_data에서
            "path": "wiki/writing/notes/" + stem,
        }
    return twins
```

- [ ] **Step 4: 통과 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): twin scanner with frontmatter type gate"
```

---

### Task 4: 트리아지 지도 파서

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Consumes: `extract_tables`, `parse_verdict_cell`, `stem_from_cell`
- Produces: `parse_triage_map(text: str, unparsed: list) -> dict` — `{"entries": dict[stem, {"verdict","qualifier","lineage","batch"}], "excluded": set[str]}`. 배치 집계는 여기서 하지 않는다(Task 7의 `build_data`가 쌍둥이 우선 병합 후 집계).

- [ ] **Step 1: 실패하는 테스트 작성** — 추가:

```python
TRIAGE_FIXTURE = """# 글감 트리아지 지도

## 배치 1 — notes 1~20 (2026-07-04)

| 글감 | A1 A2 A3 | B1 B2 B3 B4 B5 | 판정 | 가장 약한 축 / 한 줄 사유 | 계열(가) |
|---|---|---|---|---|---|
| [[wiki/writing/notes/3_8초_지연_scored|3.8초 지연]] | △ △ △ | ✕ ✕ ✕ ✕ ○ | **병합** | 독백 | 통신/지연 |
| [[wiki/writing/notes/거울을_옮기는_사람|거울을 옮기는 사람]] | — | — | **진행 중** | 활성 | 돌봄/반복 |

### 배치 1 대상 아님 (메타/작업 파일 — 개명·채점 제외)

- [[wiki/writing/notes/수많은_일인칭]] — 메타
- 설명란_부족 — 진행 중 원고

### 배치 1에서 보이기 시작한 계열

| 계열 | 글감 수 | 비고 |
|---|---|---|
| 통신/지연 | 1 | 초기 |

## 배치 12 — 신규 노트 101~106 (2026-07-04, 최종 잔여분)

| 글감 | 판정 | 한 줄 사유 | 계열 |
|---|---|---|---|
| 왜요 | 유망(소품) | 한 단어 | 말/작별·노동 |
| 주정으로_처리하지_마세요 | **유망★** | 자기강화 루프 | 기록-발언 운반체 후보 |

## 전체 트리아지 완료 (2026-07-04)

| 구분 | notes | draft-candidates | 합계 |
|---|---|---|---|
| 유망★ | 13 | 8 | **21** |
"""


class TestTriageMap(unittest.TestCase):
    def test_parse(self):
        unparsed = []
        r = g.parse_triage_map(TRIAGE_FIXTURE, unparsed)
        e = r["entries"]
        # 배치 1 (6열 위키링크 형식)
        self.assertEqual(e["3_8초_지연"]["verdict"], "병합")
        self.assertEqual(e["3_8초_지연"]["lineage"], "통신/지연")
        self.assertEqual(e["3_8초_지연"]["batch"], 1)
        self.assertEqual(e["거울을_옮기는_사람"]["verdict"], "진행 중")
        # 배치 12 (4열 플레인 형식)
        self.assertEqual(e["왜요"]["verdict"], "유망")
        self.assertEqual(e["왜요"]["qualifier"], "소품")
        self.assertEqual(e["주정으로_처리하지_마세요"]["verdict"], "유망★")
        self.assertEqual(e["주정으로_처리하지_마세요"]["batch"], 12)
        # 오탐 배제: 집계표(판정 열 없음)와 계열 보조표의 행이 글감으로 오인되지 않음
        self.assertNotIn("유망★", e)
        self.assertNotIn("통신/지연", e)
        # 대상 아님 수집 (위키링크·플레인 양쪽)
        self.assertIn("수많은_일인칭", r["excluded"])
        self.assertIn("설명란_부족", r["excluded"])
```

- [ ] **Step 2: 실패 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: FAIL (`parse_triage_map` 없음)

- [ ] **Step 3: 구현** — 추가:

```python
def _find_col(header, name):
    for i, cell in enumerate(header):
        if name in cell:
            return i
    return None


def parse_triage_map(text, unparsed):
    """배치 섹션(## 배치 N)만 파싱. 섹션 내 표 중 헤더에 '판정' 열이 있는 표만 글감 표."""
    entries, excluded = {}, set()
    for sec in re.split(r'(?m)^## ', text):
        header_line = sec.split("\n", 1)[0]
        m = re.match(r'배치\s*(\d+)', header_line)
        if not m:
            continue
        batch_no = int(m.group(1))
        # 「대상 아님」 하위 섹션에서 제외 목록 수집
        for sub in re.split(r'(?m)^### ', sec)[1:]:
            if "대상 아님" not in sub.split("\n", 1)[0]:
                continue
            for link in re.finditer(r'\[\[([^\]|]+)', sub):
                excluded.add(link.group(1).split("/")[-1].strip())
            for bullet in re.finditer(r'(?m)^-\s+([^\[\s—-][^—\n]*?)(?:\s+—|$)', sub):
                excluded.add(bullet.group(1).strip())
        for table in extract_tables(sec):
            header = table[0]
            v_idx = _find_col(header, "판정")
            if v_idx is None:
                continue                       # 집계표·계열 보조표 자동 배제
            l_idx = _find_col(header, "계열")
            for row in table[1:]:
                if len(row) <= v_idx:
                    unparsed.append({"file": "글감_트리아지_지도.md",
                                     "reason": "배치 %d 행 열 부족: %s" % (batch_no, row[:1])})
                    continue
                stem = stem_from_cell(row[0])
                verdict, qualifier = parse_verdict_cell(row[v_idx])
                if verdict is None:
                    unparsed.append({"file": "글감_트리아지_지도.md",
                                     "reason": "배치 %d 판정 해석 실패: %s" % (batch_no, stem)})
                    continue
                lineage = None
                if l_idx is not None and len(row) > l_idx:
                    lineage = re.split(r'[.(（]', row[l_idx].replace("*", ""))[0].strip() or None
                entries[stem] = {"verdict": verdict, "qualifier": qualifier,
                                 "lineage": lineage, "batch": batch_no}
    return {"entries": entries, "excluded": excluded}
```

- [ ] **Step 4: 통과 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): triage map parser (header-based table detection)"
```

---

### Task 5: 계열·병합 지도 파서

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Consumes: `extract_tables`, `stem_from_cell`
- Produces: `parse_lineage_map(text: str, unparsed: list) -> dict` — `{"lineages": [{"name","carrier","stars","members","parts","state"}], "mergers": [{"id","title","nextAction"}], "cards": [{"title","lineage","star","state","link"}]}`
- 칸반 카드 규칙(스펙): 상태 ∈ {개작, 조립, 대기} 행은 전부 카드. 상태 `설계`는 ★ 보유 행만.

- [ ] **Step 1: 실패하는 테스트 작성** — 추가:

```python
LINEAGE_FIXTURE = """# 글감 계열·병합 지도

## 계열 지도

### 1. 기록 — 유류품/애도

| 역할 | 글감 | 상태 |
|---|---|---|
| 운반체 | [[wiki/writing/draft-candidates/폐기_전_확인_초고후보_scored|폐기 전 확인]] ★ | 조립 |
| 독립 가능 | [[wiki/writing/notes/라벨_없음_scored|라벨 없음]] ★ | 설계 |
| 비트 | 고작이라는_말 | 부품 |

### 3. 기록 — 보정 체인

기록이 좋아질수록 사람이 사라지는 극. **운반체 없음 → 신규 극 후보.**

| 역할 | 글감 | 상태 |
|---|---|---|
| 체인 순서 | 잡음이_제거되었습니다 | 부품 |

## 병합 후보 요약

| # | 병합 극 | 재료 | 다음 행동 |
|---|---|---|---|
| A | 유류품 인계극 | 한_장짜리_보고서 + 그건_관련이 | 차별화 확인 후 2단계 처방 |
| H | 공동 수리 극 | 상호_번역_작업대 ★ × 공동_수리_허가 | 재해석 후 2부 구조 설계 |
"""


class TestLineageMap(unittest.TestCase):
    def test_lineages(self):
        unparsed = []
        r = g.parse_lineage_map(LINEAGE_FIXTURE, unparsed)
        by_name = {x["name"]: x for x in r["lineages"]}
        rec = by_name["기록 — 유류품/애도"]
        self.assertEqual(rec["carrier"], "폐기 전 확인")
        self.assertEqual(rec["stars"], 2)
        self.assertEqual(rec["members"], 2)     # 부품 제외
        self.assertEqual(rec["parts"], 1)
        self.assertEqual(rec["state"], "조립")   # 운반체의 상태
        self.assertIsNone(by_name["기록 — 보정 체인"]["carrier"])  # 운반체 없음 선언

    def test_mergers_only_from_summary_table(self):
        unparsed = []
        r = g.parse_lineage_map(LINEAGE_FIXTURE, unparsed)
        ids = [m["id"] for m in r["mergers"]]
        self.assertEqual(ids, ["A", "H"])
        self.assertEqual(r["mergers"][1]["nextAction"], "재해석 후 2부 구조 설계")

    def test_kanban_cards(self):
        unparsed = []
        r = g.parse_lineage_map(LINEAGE_FIXTURE, unparsed)
        titles = {(c["title"], c["state"]) for c in r["cards"]}
        self.assertIn(("폐기 전 확인", "조립"), titles)
        self.assertIn(("라벨 없음", "설계"), titles)          # ★라서 설계 카드 포함
        self.assertNotIn(("고작이라는_말", "부품"), titles)   # 부품은 카드 아님
```

- [ ] **Step 2: 실패 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: FAIL

- [ ] **Step 3: 구현** — 추가:

```python
_CARD_STATES = {"개작", "조립", "대기"}


def _clean_title(cell):
    """셀에서 표시용 제목: 위키링크 별칭 우선, 없으면 타깃 스템, 플레인은 그대로."""
    m = re.search(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', cell)
    if m:
        return (m.group(2) or m.group(1).split("/")[-1]).strip()
    return cell.replace("*", "").replace("★", "").strip()


def _link_from_cell(cell):
    m = re.search(r'\[\[([^\]|]+)', cell)
    if m:
        path = m.group(1).strip()
        return path[:-len("_scored")] if path.endswith("_scored") else path
    return None


def parse_lineage_map(text, unparsed):
    lineages, cards = [], []
    for sec in re.split(r'(?m)^### ', text)[1:]:
        header = sec.split("\n", 1)[0].strip()
        m = re.match(r'(?:\d+\.\s*)?(.+)$', header)
        name = m.group(1).strip() if m else header
        carrier, stars, members, parts, state = None, sec.count("★"), 0, 0, "설계"
        no_carrier = "운반체 없음" in sec
        try:
            for table in extract_tables(sec):
                head = table[0]
                if _find_col(head, "역할") is None:
                    continue
                for row in table[1:]:
                    if len(row) < 3:
                        continue
                    role, item, st = row[0], row[1], row[2].replace("*", "").strip()
                    if "부품" in role or st == "부품":
                        parts += 1
                        continue
                    members += 1
                    star = "★" in item
                    if "운반체" in role and not no_carrier:
                        carrier = _clean_title(item)
                        state = st or "설계"
                    if st in _CARD_STATES or (st == "설계" and star):
                        cards.append({"title": _clean_title(item),
                                      "lineage": name, "star": star,
                                      "state": st or "설계",
                                      "link": _link_from_cell(item)})
        except Exception as exc:  # 관대한 파싱: 섹션 단위로만 실패
            unparsed.append({"file": "글감_계열_병합_지도.md",
                             "reason": "계열 섹션 파싱 실패(%s): %s" % (name, exc)})
            continue
        lineages.append({"name": name, "carrier": carrier, "stars": stars,
                         "members": members, "parts": parts, "state": state})
    mergers = []
    summary = text.split("## 병합 후보 요약", 1)
    if len(summary) == 2:
        for table in extract_tables(summary[1]):
            head = table[0]
            if _find_col(head, "다음 행동") is None:
                continue
            for row in table[1:]:
                if len(row) >= 4:
                    mergers.append({"id": row[0].strip(), "title": _clean_title(row[1]),
                                    "nextAction": row[3].replace("*", "").strip()})
            break
    else:
        unparsed.append({"file": "글감_계열_병합_지도.md", "reason": "병합 후보 요약 표 없음"})
    return {"lineages": lineages, "mergers": mergers, "cards": cards}
```

- [ ] **Step 4: 통과 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): lineage map parser with kanban cards and merger summary"
```

---

### Task 6: 책 서가 + 책↔창작 역추적

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Consumes: `parse_frontmatter`, `normalize_source`, `read_text`
- Produces:
  - `scan_note_sources(vault_root: Path) -> dict[str, list[str]]` — 원본 노트(스템)별 정규화된 sources (type: writing-note인 `notes/*.md`만, `_scored` 파일 제외)
  - `scan_books(vault_root: Path, note_sources: dict, verdict_of) -> dict` — `{"rawTotal", "deviceMapTotal", "books": [...]}`. `verdict_of`는 `stem -> {"verdict","lineage"} | None` callable

- [ ] **Step 1: 실패하는 테스트 작성** — 추가:

```python
NOTE_WITH_BOOK = ('---\ntype: writing-note\nsources:\n'
                  '  - "wiki/bookclub/books/혼모노/00_책카드.md"\n'
                  '  - "bookclub/석촌호수책모임/_혼모노_ 성해나.md"\n---\n# 노트\n')
DEVICE_MAP = ('---\ntype: writing-map\nsources:\n'
              '  - "bookclub/석촌호수책모임/_혼모노_ 성해나.md"\n'
              '  - "wiki/bookclub/books/혼모노/00_책카드.md"\n---\n# 지도\n')


class TestBooks(unittest.TestCase):
    def _root(self):
        return make_vault({
            "wiki/bookclub/books/혼모노/00_책카드.md": "---\ntype: book-card\n---\n# 혼모노\n",
            "wiki/bookclub/books/궤도/00_책카드.md": "---\ntype: book-card\n---\n# 궤도\n",
            "wiki/writing/notes/바나나맛_진짜.md": NOTE_WITH_BOOK,
            "wiki/writing/notes/바나나맛_진짜_scored.md": TWIN,  # sources 스캔에서 제외돼야 함
            "wiki/writing/maps/혼모노_원본_창작장치_지도.md": DEVICE_MAP,
            "bookclub/석촌호수책모임/_혼모노_ 성해나.md": "로우 데이터",
            "bookclub/석촌호수책모임/모임기록.md": "로우 데이터 2",
            "bookclub/석촌호수책모임/표지.webp": "binary-ish",   # md 아님 → rawTotal 제외
        })

    def test_book_linkage(self):
        tmp, root = self._root()
        with tmp:
            sources = g.scan_note_sources(root)
            self.assertIn("바나나맛_진짜", sources)
            self.assertNotIn("바나나맛_진짜_scored", sources)
            verdicts = {"바나나맛_진짜": {"verdict": "유망★", "lineage": "진짜/출처"}}
            r = g.scan_books(root, sources, lambda s: verdicts.get(s))
            self.assertEqual(r["rawTotal"], 2)          # .md만
            self.assertEqual(r["deviceMapTotal"], 1)
            by_title = {b["title"]: b for b in r["books"]}
            self.assertEqual(by_title["혼모노"]["derivedNotes"], 1)
            self.assertEqual(by_title["혼모노"]["stars"], 1)
            self.assertEqual(by_title["혼모노"]["rawNotes"], 1)   # 장치 지도 교량
            self.assertEqual(by_title["혼모노"]["lineages"], ["진짜/출처"])
            self.assertEqual(by_title["궤도"]["derivedNotes"], 0)  # 미채굴
```

- [ ] **Step 2: 실패 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: FAIL

- [ ] **Step 3: 구현** — 추가:

```python
def scan_note_sources(vault_root):
    """원본 글감 노트(type: writing-note, _scored 아님)의 정규화 sources."""
    out = {}
    notes = vault_root / "wiki" / "writing" / "notes"
    if not notes.is_dir():
        return out
    for p in sorted(notes.glob("*.md")):
        if p.stem.endswith("_scored"):
            continue
        fm = parse_frontmatter(read_text(p))
        if fm.get("type") != "writing-note":
            continue
        srcs = fm.get("sources")
        if isinstance(srcs, list) and srcs:
            out[p.stem] = [normalize_source(s) for s in srcs]
    return out


def scan_books(vault_root, note_sources, verdict_of):
    books_dir = vault_root / "wiki" / "bookclub" / "books"
    raw_dir = vault_root / "bookclub" / "석촌호수책모임"
    maps_dir = vault_root / "wiki" / "writing" / "maps"
    raw_total = len(list(raw_dir.rglob("*.md"))) if raw_dir.is_dir() else 0
    device_maps = sorted(maps_dir.glob("*_원본_창작장치_지도.md")) if maps_dir.is_dir() else []

    # 장치 지도 = 로우↔책카드 교량: 책 키 → 로우 소스 수
    raw_bridge = {}
    for p in device_maps:
        fm = parse_frontmatter(read_text(p))
        srcs = [normalize_source(s) for s in fm.get("sources", []) if isinstance(fm.get("sources"), list)]
        card_keys = [s for s in srcs if s.startswith("wiki/bookclub/books/")]
        raws = [s for s in srcs if s.startswith("bookclub/")]
        for key in card_keys:
            raw_bridge[key] = raw_bridge.get(key, 0) + len(raws)

    books = []
    if books_dir.is_dir():
        for d in sorted(books_dir.iterdir()):
            card = d / "00_책카드.md"
            if not d.is_dir() or not card.is_file():
                continue
            key = "wiki/bookclub/books/%s/00_책카드" % d.name
            derived, stars, lineage_count = 0, 0, {}
            for stem, srcs in note_sources.items():
                if key not in srcs:
                    continue
                derived += 1
                info = verdict_of(stem)
                if info:
                    if info.get("verdict") == "유망★":
                        stars += 1
                    lin = info.get("lineage")
                    if lin:
                        lineage_count[lin] = lineage_count.get(lin, 0) + 1
            top = sorted(lineage_count.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
            books.append({"title": d.name,
                          "cardPath": key,
                          "rawNotes": raw_bridge.get(key, 0),
                          "derivedNotes": derived, "stars": stars,
                          "lineages": [k for k, _ in top]})
    books.sort(key=lambda b: (-b["derivedNotes"], b["title"]))
    return {"rawTotal": raw_total, "deviceMapTotal": len(device_maps), "books": books}
```

- [ ] **Step 4: 통과 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): book shelf scan and book-to-note back-linking"
```

---

### Task 7: 미채점 실측 + 다음 할 일 + build_data 조립

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Consumes: Task 3~6의 모든 함수
- Produces:
  - `compute_unscored(vault_root, twins, entries, excluded) -> list[{"title","link"}]`
  - `compute_next_actions(unscored, lineages, cards) -> list[{"text","link"}]` (최대 3건, 스펙 규칙 4개)
  - `build_data(vault_root: Path) -> dict` — 스펙 스키마 그대로의 최상위 dict

- [ ] **Step 1: 실패하는 테스트 작성** — 추가:

```python
class TestUnscoredAndActions(unittest.TestCase):
    def test_unscored(self):
        tmp, root = make_vault({
            "wiki/writing/notes/새_글감.md": "---\ntype: writing-note\n---\n# 새 글감\n",
            "wiki/writing/notes/왜요.md": "---\ntype: writing-note\n---\n# 왜요\n",
            "wiki/writing/notes/왜요_scored.md": TWIN,
            "wiki/writing/notes/수많은_일인칭.md": "---\ntype: writing-note\n---\n# 메타\n",
            "wiki/writing/notes/글감_트리아지_지도.md": "---\ntype: writing-note\n---\n# 지도\n",
        })
        with tmp:
            r = g.compute_unscored(root, twins={"왜요": {}}, entries={},
                                   excluded={"수많은_일인칭"})
            titles = [x["title"] for x in r]
            self.assertEqual(titles, ["새_글감"])   # 쌍둥이·제외·지도 자신 전부 빠짐

    def test_next_actions_rules(self):
        unscored = [{"title": "n%d" % i, "link": None} for i in range(12)]
        lineages = [{"name": "기록 — 보정 체인", "carrier": None, "stars": 1,
                     "members": 3, "parts": 5, "state": "설계"}]
        cards = [{"title": "라벨 없음", "lineage": "기록", "star": True,
                  "state": "설계", "link": None}]
        acts = g.compute_next_actions(unscored, lineages, cards)
        self.assertEqual(len(acts), 3)
        self.assertIn("12편 대기", acts[0]["text"])
        self.assertIn("보정 체인", acts[1]["text"])
        self.assertIn("라벨 없음", acts[2]["text"])

    def test_next_actions_empty(self):
        acts = g.compute_next_actions([], [], [])
        self.assertEqual(len(acts), 1)
        self.assertIn("계속 쓰세요", acts[0]["text"])
```

- [ ] **Step 2: 실패 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: FAIL

- [ ] **Step 3: 구현** — 추가:

```python
MAP_SELF = "글감_트리아지_지도"


def compute_unscored(vault_root, twins, entries, excluded):
    out = []
    notes = vault_root / "wiki" / "writing" / "notes"
    if not notes.is_dir():
        return out
    for p in sorted(notes.glob("*.md")):
        stem = p.stem
        if stem.endswith("_scored") or stem == MAP_SELF:
            continue
        if stem in twins or stem in entries or stem in excluded:
            continue
        if parse_frontmatter(read_text(p)).get("type") != "writing-note":
            continue
        out.append({"title": stem, "link": "wiki/writing/notes/" + stem})
    return out


def compute_next_actions(unscored, lineages, cards):
    acts = []
    if len(unscored) >= 10:
        acts.append({"text": "다음 트리아지 사이클 돌릴 때 (%d편 대기)" % len(unscored), "link": None})
    for lin in lineages:
        if len(acts) >= 3:
            break
        if lin["carrier"] is None and lin["stars"] > 0:
            acts.append({"text": "『%s』 운반체 지정 필요" % lin["name"], "link": None})
    for c in cards:
        if len(acts) >= 3:
            break
        if c["state"] == "설계" and c["star"]:
            acts.append({"text": "『%s』 처방 대기" % c["title"], "link": c["link"]})
    if not acts:
        acts.append({"text": "당장 할 일 없음 — 계속 쓰세요.", "link": None})
    return acts[:3]


_COUNTED = {"유망★", "유망", "병합", "보류", "제외"}


def build_data(vault_root):
    unparsed = []
    twins = scan_twins(vault_root, unparsed)

    triage_path = vault_root / "wiki" / "writing" / "notes" / "글감_트리아지_지도.md"
    triage = ({"entries": {}, "excluded": set()} if not triage_path.is_file()
              else parse_triage_map(read_text(triage_path), unparsed))
    if not triage_path.is_file():
        unparsed.append({"file": "글감_트리아지_지도.md", "reason": "파일 없음"})

    lmap_path = vault_root / "wiki" / "shared" / "maps" / "글감_계열_병합_지도.md"
    lmap = ({"lineages": [], "mergers": [], "cards": []} if not lmap_path.is_file()
            else parse_lineage_map(read_text(lmap_path), unparsed))
    if not lmap_path.is_file():
        unparsed.append({"file": "글감_계열_병합_지도.md", "reason": "파일 없음"})

    # 판정 병합: 쌍둥이 우선 (배치 5 복원 17편에서 실제 발동)
    def verdict_of(stem):
        if stem in twins:
            t = twins[stem]
            lin = t["lineage"] or (triage["entries"].get(stem) or {}).get("lineage")
            return {"verdict": t["verdict"], "lineage": lin}
        e = triage["entries"].get(stem)
        return {"verdict": e["verdict"], "lineage": e["lineage"]} if e else None

    # 배치 집계 (지도 배치 소속 + 쌍둥이 우선 판정)
    batch_tally = {}
    for stem, e in triage["entries"].items():
        v = verdict_of(stem)["verdict"]
        if v not in _COUNTED:
            continue
        t = batch_tally.setdefault(e["batch"], {"star": 0, "promising": 0, "merge": 0})
        if v == "유망★":
            t["star"] += 1
        elif v == "유망":
            t["promising"] += 1
        else:
            t["merge"] += 1
    batches = [{"no": no, "phase": ("1차" if no <= 6 else "2·3차"),
                "scored": t["star"] + t["promising"] + t["merge"], **t}
               for no, t in sorted(batch_tally.items())]

    all_scored = {s for s in (set(twins) | set(triage["entries"]))
                  if (verdict_of(s) or {}).get("verdict") in _COUNTED}
    unscored = compute_unscored(vault_root, twins, triage["entries"], triage["excluded"])

    note_sources = scan_note_sources(vault_root)
    bookclub = scan_books(vault_root, note_sources, verdict_of)

    columns = {"설계": [], "대기": [], "조립": [], "개작": []}
    for c in lmap["cards"]:
        columns.get(c["state"], columns["설계"]).append(
            {"title": c["title"], "lineage": c["lineage"], "star": c["star"], "link": c["link"]})

    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "vaultName": vault_root.name,
        "nextActions": compute_next_actions(unscored, lmap["lineages"], lmap["cards"]),
        "bookclub": bookclub,
        "cycle": {
            "stages": {"triage": "done" if not unscored else "pending",
                       "lineage": "done", "prescription": "done", "label": "사이클 1회차"},
            "batches": batches,
            "coverage": {"scored": len(all_scored), "unscoredFiles": unscored},
        },
        "pipeline": {"columns": columns, "mergers": lmap["mergers"]},
        "lineages": sorted(lmap["lineages"], key=lambda x: (-x["stars"], x["name"])),
        "unparsed": unparsed,
    }
    total_stars = sum(1 for s in all_scored if verdict_of(s)["verdict"] == "유망★")
    for label, got, want in (("채점 총계", len(all_scored), KNOWN_TOTALS["scored"]),
                             ("유망★ 총계", total_stars, KNOWN_TOTALS["stars"]),
                             ("쌍둥이 수", len(twins), KNOWN_TOTALS["twins"])):
        if got != want:
            print("경고: %s %d ≠ 기준치 %d (vault 성장이면 정상)" % (label, got, want))
    return data
```

- [ ] **Step 4: 통과 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py
git commit -m "feat(dashboard): unscored detection, next actions, build_data assembly"
```

---

### Task 8: data.js 라이터 + main + 실 vault 스모크

**Files:**
- Modify: `tools/generate_data.py`
- Test: `tools/test_generate_data.py`

**Interfaces:**
- Produces: `write_data_js(data: dict, out: Path) -> None`, `main() -> int` (성공 0). data.js 형식: `window.VAULT_DATA = {...};\n`

- [ ] **Step 1: 실패하는 테스트 작성** — 추가:

```python
class TestWriter(unittest.TestCase):
    def test_write_utf8_and_shape(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            out = Path(tmp.name) / "data.js"
            g.write_data_js({"generated": "지금", "한글": ["값"]}, out)
            raw = out.read_bytes()
            text = raw.decode("utf-8")                    # cp949였다면 여기서 깨짐/예외
            self.assertTrue(text.startswith("window.VAULT_DATA = {"))
            self.assertTrue(text.rstrip().endswith(";"))
            self.assertIn('"한글"', text)                  # ensure_ascii=False
```

- [ ] **Step 2: 실패 확인** — Run: `py -3 -m unittest tools.test_generate_data -v` / Expected: FAIL

- [ ] **Step 3: 구현** — 추가:

```python
def write_data_js(data, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = "window.VAULT_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    out.write_text(payload, encoding="utf-8")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    data = build_data(VAULT_ROOT)
    write_data_js(data, OUTPUT)
    print("생성 완료: %s (채점 %d, 미채점 %d, unparsed %d)"
          % (OUTPUT, data["cycle"]["coverage"]["scored"],
             len(data["cycle"]["coverage"]["unscoredFiles"]), len(data["unparsed"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과 확인 + 실 vault 스모크**

Run: `py -3 -m unittest tools.test_generate_data -v` → Expected: PASS
Run: `py -3 tools/generate_data.py` (vault 루트에서)
Expected: `생성 완료: ...dashboard\data.js (채점 228, 미채점 N, unparsed M)` — 채점 228·유망★ 33·쌍둥이 113에서 크게 어긋나면 경고 줄 출력됨. **unparsed가 10건을 넘으면 여기서 멈추고 원인(어느 파서인지)을 조사할 것** — reason 필드에 파서별 사유가 있다.
Run (임의 cwd 검증): `cd C:\ && py -3 C:\obsidian\vault\vault\tools\generate_data.py` → 동일 출력.

- [ ] **Step 5: 커밋**

```bash
git add tools/generate_data.py tools/test_generate_data.py dashboard/data.js
git commit -m "feat(dashboard): data.js writer, main entrypoint, real-vault smoke"
```

---

### Task 9: 대시보드_갱신.bat

**Files:**
- Create: `tools/대시보드_갱신.bat`

**Interfaces:**
- Consumes: `tools/generate_data.py` (Task 8의 main)
- Produces: 더블클릭 실행 파일. 내용 100% ASCII.

- [ ] **Step 1: 파일 작성** — 스펙 골격 그대로 (한글 금지, 경로는 `%~dp0` 기준):

```bat
@echo off
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>nul && (set "PYCMD=py -3") || (set "PYCMD=python")
%PYCMD% "%~dp0generate_data.py"
if errorlevel 1 (echo FAILED - see message above & pause & exit /b 1)
start "" "%~dp0..\dashboard\index.html"
```

파일 저장 인코딩: ASCII 범위만 있으므로 무엇으로 저장해도 동일 — 확인 차 `git diff`에서 비ASCII 바이트가 없는지 본다.

- [ ] **Step 2: 검증**

Run (Git Bash): `cd "C:/obsidian/vault/vault" && cmd //c "tools\\대시보드_갱신.bat"`
Expected: 생성 완료 메시지 출력 후 기본 브라우저가 열림 (index.html은 Task 10 전이면 404여도 무방 — 생성 성공과 exit 0만 확인). `echo $?` → 0.

- [ ] **Step 3: 커밋**

```bash
git add "tools/대시보드_갱신.bat"
git commit -m "feat(dashboard): one-click refresh batch file (ASCII body, py launcher)"
```

---

### Task 10: index.html + style.css (정적 셸, 폴백, CSS 차트 부품)

**Files:**
- Create: `dashboard/index.html`
- Create: `dashboard/style.css`

**Interfaces:**
- Produces: DOM 앵커 — `#no-data`(기본 표시), `#app`(기본 hidden), `#generated`, 탭 버튼 `.tab-btn[data-tab]`, 섹션 `#tab-creation`/`#tab-bookclub`, 각 블록 컨테이너 `#next-actions #stepper #coverage #batches #kanban #mergers #lineages #footnote #bc-summary #bc-shelf #bc-flow #warn-banner`. app.js(Task 11)는 이 id들만 사용.

- [ ] **Step 1: index.html 작성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vault 대시보드</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div id="no-data">
  <h1>데이터 없음</h1>
  <p><code>tools\대시보드_갱신.bat</code>을 실행하세요.</p>
</div>
<div id="app" hidden>
  <header>
    <h1>Vault 대시보드</h1>
    <span id="generated"></span>
    <nav>
      <button class="tab-btn active" data-tab="creation">창작</button>
      <button class="tab-btn" data-tab="bookclub">독서모임</button>
    </nav>
  </header>
  <div id="warn-banner" hidden></div>
  <main>
    <section id="tab-creation">
      <div id="next-actions"></div>
      <h2>사이클 진행도</h2>
      <div id="stepper"></div>
      <div id="coverage"></div>
      <div id="batches"></div>
      <h2>집필 파이프라인</h2>
      <div id="kanban"></div>
      <div id="mergers"></div>
      <h2>계열별 현황</h2>
      <div id="lineages"></div>
      <div id="footnote"></div>
    </section>
    <section id="tab-bookclub" hidden>
      <div id="bc-summary"></div>
      <h2>책 서가</h2>
      <div id="bc-shelf"></div>
      <h2>책 → 창작 흐름 (상위 10권)</h2>
      <div id="bc-flow"></div>
    </section>
  </main>
</div>
<script src="data.js"></script>
<script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: style.css 작성**

```css
:root {
  --bg: #14161a; --panel: #1d2026; --line: #2c3038;
  --text: #e6e6e3; --muted: #9aa0a8; --dim: #6b7280;
  --star: #d4a73f; --ok: #4f9d69; --warn: #e0b64a; --alert: #c05b4d;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: "Pretendard Variable", Pretendard, "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
  font-size: 15px; line-height: 1.55; word-break: keep-all;
}
main, header { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
header { display: flex; align-items: baseline; gap: 16px; padding-top: 24px; flex-wrap: wrap; }
header h1 { font-size: 20px; margin: 0; }
#generated { color: var(--muted); font-size: 13px; }
nav { margin-left: auto; }
.tab-btn { background: var(--panel); color: var(--muted); border: 1px solid var(--line);
  padding: 6px 18px; cursor: pointer; font: inherit; }
.tab-btn.active { color: var(--text); border-color: var(--star); }
h2 { font-size: 16px; margin: 28px 0 10px; color: var(--muted); }
#no-data { max-width: 520px; margin: 18vh auto; text-align: center; color: var(--text);
  font-family: "Malgun Gothic", sans-serif; }
#warn-banner { background: var(--alert); color: #fff; padding: 8px 20px; margin: 12px auto;
  max-width: 1200px; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
th, td { border-bottom: 1px solid var(--line); padding: 6px 10px; text-align: left; }
a { color: var(--text); }
.star { color: var(--star); }
.card, .strip-item { background: var(--panel); border: 1px solid var(--line);
  border-radius: 6px; padding: 10px 12px; }
/* 다음 할 일 스트립 */
#next-actions { display: flex; gap: 10px; margin-top: 18px; flex-wrap: wrap; }
#next-actions .strip-item { border-left: 3px solid var(--star); }
/* 스텝퍼 */
#stepper { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
.step { padding: 6px 14px; border: 1px solid var(--line); border-radius: 20px; color: var(--muted); }
.step.done { border-color: var(--ok); color: var(--text); }
/* 도넛 (conic-gradient) */
.donut-wrap { display: flex; align-items: center; gap: 18px; margin: 12px 0; }
.donut { width: 120px; height: 120px; border-radius: 50%; position: relative; flex: none; }
.donut::after { content: ""; position: absolute; inset: 18px; border-radius: 50%; background: var(--bg); }
/* 배치 스택 바 */
.batch-row { display: flex; align-items: center; gap: 8px; margin: 3px 0; }
.batch-label { width: 70px; color: var(--muted); font-size: 13px; flex: none; }
.batch-bar { display: flex; height: 16px; flex: 1; background: var(--panel); }
.batch-bar .seg-star { background: var(--star); }
.batch-bar .seg-prom { background: var(--ok); }
.batch-bar .seg-merge { background: var(--dim); }
.batch-divider { border-top: 1px dashed var(--muted); margin: 8px 0 4px; color: var(--muted);
  font-size: 12px; padding-top: 2px; }
/* 칸반 */
#kanban { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.kanban-col { background: var(--panel); border: 1px solid var(--line); padding: 8px; min-height: 60px; }
.kanban-col h3 { margin: 0 0 8px; font-size: 13px; color: var(--muted); }
.kanban-card { border: 1px solid var(--line); border-radius: 4px; padding: 6px 8px;
  margin-bottom: 6px; font-size: 13px; background: var(--bg); }
.kanban-empty { color: var(--dim); font-size: 12px; }
#mergers { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
.merger-chip { border: 1px solid var(--line); border-radius: 14px; padding: 3px 10px;
  font-size: 12px; color: var(--muted); cursor: help; }
/* 계열표 노란 표시 */
td.no-carrier { color: var(--warn); }
/* 독서모임 */
#bc-summary { display: flex; gap: 10px; margin-top: 18px; flex-wrap: wrap; }
#bc-shelf { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 10px; }
.book-card.unmined { opacity: .55; }
.book-card .tags { color: var(--muted); font-size: 12px; }
.flow-row { display: flex; align-items: center; gap: 8px; margin: 3px 0; }
.flow-label { width: 180px; flex: none; font-size: 13px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; }
.flow-bar { height: 14px; background: var(--ok); }
details { margin-top: 8px; color: var(--muted); }
@media (max-width: 760px) { #kanban { grid-template-columns: repeat(2, 1fr); } }
```

- [ ] **Step 3: 폴백 검증**

Run (Git Bash): `start dashboard/index.html` — 이 시점에 app.js가 없으므로 브라우저에 **"데이터 없음" 폴백 화면**이 보이면 정상 (`#no-data`가 기본 표시).

- [ ] **Step 4: 커밋**

```bash
git add dashboard/index.html dashboard/style.css
git commit -m "feat(dashboard): static shell with fallback state and CSS chart parts"
```

---

### Task 11: app.js 렌더링

**Files:**
- Create: `dashboard/app.js`

**Interfaces:**
- Consumes: Task 10의 DOM id들, Task 8의 `window.VAULT_DATA` 스키마 (필드명은 스펙 데이터 모델 절과 동일)

- [ ] **Step 1: app.js 작성**

```javascript
(function () {
  "use strict";
  var d = window.VAULT_DATA;
  var $ = function (id) { return document.getElementById(id); };
  if (!d) { return; }                      // data.js 부재 → #no-data가 그대로 보임
  $("no-data").remove();
  $("app").hidden = false;
  $("generated").textContent = "생성: " + d.generated;

  var isFile = location.protocol === "file:";
  function noteEl(title, path) {
    if (isFile && path) {
      var a = document.createElement("a");
      a.href = "obsidian://open?vault=" + encodeURIComponent(d.vaultName) +
               "&file=" + encodeURIComponent(path);
      a.textContent = title;
      return a;
    }
    var s = document.createElement("span");
    s.textContent = title;
    return s;
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  // 탭
  var btns = document.querySelectorAll(".tab-btn");
  btns.forEach(function (b) {
    b.addEventListener("click", function () {
      btns.forEach(function (x) { x.classList.remove("active"); });
      b.classList.add("active");
      $("tab-creation").hidden = b.dataset.tab !== "creation";
      $("tab-bookclub").hidden = b.dataset.tab !== "bookclub";
    });
  });

  // 경고 배너 (unparsed >= 10 승격)
  if (d.unparsed.length >= 10) {
    $("warn-banner").hidden = false;
    $("warn-banner").textContent =
      "파서 경고: 분류 안 됨 " + d.unparsed.length + "건 — 파서 점검 필요";
  }

  // 0. 다음 할 일
  d.nextActions.forEach(function (a) {
    var item = el("div", "strip-item");
    item.appendChild(a.link ? noteEl(a.text, a.link) : el("span", null, a.text));
    $("next-actions").appendChild(item);
  });

  // 1a. 스텝퍼
  var stageNames = [["triage", "1단계 트리아지"], ["lineage", "3단계 계열 지도"],
                    ["prescription", "2단계 처방"]];
  $("stepper").appendChild(el("span", "step done", d.cycle.stages.label || "사이클"));
  stageNames.forEach(function (s) {
    var cls = "step" + (d.cycle.stages[s[0]] === "done" ? " done" : "");
    $("stepper").appendChild(el("span", cls, s[1]));
  });

  // 1b. 커버리지 도넛 + 미채점 목록
  var cov = d.cycle.coverage, un = cov.unscoredFiles.length, total = cov.scored + un;
  var wrap = el("div", "donut-wrap");
  if (un === 0) {
    wrap.appendChild(el("span", null, "전부 채점 완료 ✓ (" + cov.scored + "편)"));
  } else {
    var pct = total ? (cov.scored / total) * 100 : 0;
    var donut = el("div", "donut");
    donut.style.background =
      "conic-gradient(var(--ok) 0 " + pct + "%, var(--dim) " + pct + "% 100%)";
    wrap.appendChild(donut);
    var lab = el("div");
    lab.appendChild(el("div", null, "채점 " + cov.scored + " / 미채점 " + un));
    var det = el("details");
    det.appendChild(el("summary", null, "미채점 " + un + "편 보기"));
    cov.unscoredFiles.forEach(function (f) {
      var line = el("div");
      line.appendChild(noteEl(f.title, f.link));
      det.appendChild(line);
    });
    lab.appendChild(det);
    wrap.appendChild(lab);
  }
  $("coverage").appendChild(wrap);

  // 1c. 배치 스택 바 (배치 6/7 사이 구분선 — 두 구간은 연속 추세 아님)
  var maxScored = Math.max.apply(null, d.cycle.batches.map(function (b) { return b.scored; }).concat([1]));
  d.cycle.batches.forEach(function (b, i) {
    if (i > 0 && d.cycle.batches[i - 1].phase !== b.phase) {
      $("batches").appendChild(el("div", "batch-divider", "▲ 1차분 | ▼ 2·3차분"));
    }
    var row = el("div", "batch-row");
    row.appendChild(el("span", "batch-label", "배치 " + b.no));
    var bar = el("div", "batch-bar");
    bar.style.maxWidth = (b.scored / maxScored) * 100 + "%";
    [["seg-star", b.star], ["seg-prom", b.promising], ["seg-merge", b.merge]].forEach(function (seg) {
      if (!seg[1]) return;
      var s = el("span", seg[0]);
      s.style.width = (seg[1] / b.scored) * 100 + "%";
      s.title = seg[1] + "편";
      bar.appendChild(s);
    });
    row.appendChild(bar);
    row.appendChild(el("span", "batch-label",
      "★" + b.star + " 유망" + b.promising + " 병합" + b.merge));
    $("batches").appendChild(row);
  });

  // 2. 칸반 (4열 고정 — 빈 열도 유지)
  ["설계", "대기", "조립", "개작"].forEach(function (colName) {
    var col = el("div", "kanban-col");
    col.appendChild(el("h3", null, colName));
    var cards = d.pipeline.columns[colName] || [];
    if (!cards.length) {
      col.appendChild(el("div", "kanban-empty", "비어 있음"));
    }
    cards.forEach(function (c) {
      var card = el("div", "kanban-card");
      if (c.star) card.appendChild(el("span", "star", "★ "));
      card.appendChild(noteEl(c.title, c.link));
      card.appendChild(el("div", "tags", c.lineage || ""));
      col.appendChild(card);
    });
    $("kanban").appendChild(col);
  });
  d.pipeline.mergers.forEach(function (m) {
    var chip = el("span", "merger-chip", m.id + " " + m.title);
    chip.title = m.nextAction;
    $("mergers").appendChild(chip);
  });

  // 3. 계열표 — 활성(★>0 또는 개작/조립)만 기본, 나머지 접이식
  function lineageTable(rows) {
    var t = el("table"), head = el("tr");
    ["계열", "운반체", "★", "구성원", "부품", "상태"].forEach(function (h) {
      head.appendChild(el("th", null, h));
    });
    t.appendChild(head);
    rows.forEach(function (l) {
      var tr = el("tr");
      tr.appendChild(el("td", null, l.name));
      var carrier = el("td", l.carrier ? null : "no-carrier",
                       l.carrier || "운반체 결정 필요");
      tr.appendChild(carrier);
      tr.appendChild(el("td", "star", String(l.stars)));
      tr.appendChild(el("td", null, String(l.members)));
      tr.appendChild(el("td", null, String(l.parts)));
      tr.appendChild(el("td", null, l.state));
      t.appendChild(tr);
    });
    return t;
  }
  var active = d.lineages.filter(function (l) {
    return l.stars > 0 || l.state === "개작" || l.state === "조립";
  });
  var dormant = d.lineages.filter(function (l) { return active.indexOf(l) === -1; });
  $("lineages").appendChild(lineageTable(active));
  if (dormant.length) {
    var det2 = el("details");
    det2.appendChild(el("summary", null, "잠자는 계열 " + dormant.length + "개 더 보기"));
    det2.appendChild(lineageTable(dormant));
    $("lineages").appendChild(det2);
  }

  // 4. 풋노트 (0건이면 미렌더, >=10은 위 배너가 담당하되 목록은 여기)
  if (d.unparsed.length > 0) {
    var det3 = el("details");
    det3.appendChild(el("summary", null, "분류 안 됨 " + d.unparsed.length + "건"));
    d.unparsed.forEach(function (u) {
      det3.appendChild(el("div", null, u.file + " — " + u.reason));
    });
    $("footnote").appendChild(det3);
  }

  // 독서모임 탭
  var bc = d.bookclub;
  var mined = bc.books.filter(function (b) { return b.derivedNotes > 0; }).length;
  var rate = bc.books.length ? Math.round((mined / bc.books.length) * 100) : 0;
  [["책", bc.books.length], ["로우 데이터", bc.rawTotal],
   ["원본장치 지도", bc.deviceMapTotal], ["창작 전환율", rate + "%"]].forEach(function (s) {
    var item = el("div", "strip-item");
    item.appendChild(el("div", "tags", s[0]));
    item.appendChild(el("div", null, String(s[1])));
    $("bc-summary").appendChild(item);
  });
  bc.books.forEach(function (b) {
    var card = el("div", "card book-card" + (b.derivedNotes ? "" : " unmined"));
    var title = el("div");
    title.appendChild(noteEl(b.title, b.cardPath));
    if (b.stars) title.appendChild(el("span", "star", " ★" + b.stars));
    card.appendChild(title);
    card.appendChild(el("div", "tags",
      "글감 " + b.derivedNotes + (b.lineages.length ? " · " + b.lineages.join(", ") : "")));
    $("bc-shelf").appendChild(card);
  });
  var top = bc.books.slice(0, 10).filter(function (b) { return b.derivedNotes > 0; });
  var maxD = Math.max.apply(null, top.map(function (b) { return b.derivedNotes; }).concat([1]));
  top.forEach(function (b) {
    var row = el("div", "flow-row");
    row.appendChild(el("span", "flow-label", b.title));
    var bar = el("div", "flow-bar");
    bar.style.width = (b.derivedNotes / maxD) * 60 + "%";
    row.appendChild(bar);
    row.appendChild(el("span", "tags", b.derivedNotes + "편"));
    $("bc-flow").appendChild(row);
  });
})();
```

- [ ] **Step 2: 수동 검증 (스펙 테스트 절 4번)**

1. `py -3 tools/generate_data.py` 재실행 후 `start dashboard/index.html`
2. 확인 목록: 창작 탭이 기본 / 다음 할 일 스트립 표시 / 도넛+미채점 접이식 / 배치 바에 1차·2·3차 구분선 / 칸반 4열(빈 열에 "비어 있음") / 병합 칩 툴팁 / 계열표 활성+접이식 / 독서모임 탭 서가·상위10 막대
3. 링크: 글감 제목 클릭 → Obsidian이 해당 노트를 엶 (file://이므로)
4. 폴백: `dashboard/data.js`를 임시로 `data.js.bak`으로 개명 → 새로고침 → "데이터 없음" 화면 → 원복
5. http 모드: `cd dashboard && py -3 -m http.server 8765` → `http://localhost:8765` → 링크가 일반 텍스트인지 확인 → 서버 종료

- [ ] **Step 3: 커밋**

```bash
git add dashboard/app.js dashboard/data.js
git commit -m "feat(dashboard): full rendering (creation + bookclub tabs, CSS charts)"
```

---

### Task 12: 마무리 — 루브릭 사이클 연동 + 로그

**Files:**
- Modify: `wiki/writing/aesthetics/글감_판정_루브릭.md` (보칙 2 사이클 종료 조건에 한 줄)
- Modify: `log.md` (vault 루트), `index.md` (vault 루트)

- [ ] **Step 1: 루브릭 보칙 2 갱신** — "사이클 종료 조건" 문단 끝에 다음 한 줄 추가 (Edit 도구, 기존 문구 보존):

```
4. **대시보드 갱신**: 사이클 완료 선언 전에 `tools/대시보드_갱신.bat`(또는 `py -3 tools/generate_data.py`)을 실행해 `dashboard/data.js`를 최신화한다.
```

- [ ] **Step 2: index.md 등록** — 적절한 섹션에 한 줄:

```
- [[dashboard/index.html|Vault 대시보드]] — 트리아지 사이클 진행도·집필 파이프라인·계열 현황·독서모임 연결을 보여주는 정적 대시보드. 갱신: `tools/대시보드_갱신.bat`.
```

- [ ] **Step 3: log.md 항목 추가** (append-only 규칙):

```
## [날짜] create | Vault 대시보드 v1

- 생성 문서: `tools/generate_data.py`, `tools/test_generate_data.py`, `tools/대시보드_갱신.bat`, `dashboard/` (index.html, app.js, style.css, data.js)
- 핵심 변경: 트리아지 사이클 대시보드 — 창작 탭(다음 할 일·사이클 진행도·칸반·계열표) + 독서모임 탭(서가·책→창작 흐름). 루브릭 보칙 2에 대시보드 갱신 단계 추가.
- 다음 작업: 사용하면서 파서 unparsed 항목 관찰, 필요 시 Pages 마스킹 모드(--public).
- 백업: 개인 GitHub push는 하지 않고 로컬 커밋만 유지한다.
```

- [ ] **Step 4: 전체 테스트 최종 실행**

Run: `py -3 -m unittest tools.test_generate_data -v` → Expected: 전부 PASS
Run: `py -3 tools/generate_data.py` → Expected: 생성 완료, 경고 없음(또는 vault 성장분만큼의 경고)

- [ ] **Step 5: 커밋**

```bash
git add wiki/writing/aesthetics/글감_판정_루브릭.md index.md log.md dashboard/data.js
git commit -m "docs(dashboard): wire dashboard refresh into triage cycle, register in index/log"
```

---

## 계획 자체 점검 결과 (self-review)

- **스펙 커버리지**: 파싱 규칙 1~5 → Task 3/4/5/6/7. 화면 블록(다음 할 일·스텝퍼·도넛·배치 바·칸반·병합 칩·계열표·풋노트·배너·독서모임 3블록) → Task 10/11. 빈 상태 표 6종 → Task 10(#no-data)/11(빈 열·완료 문구·풋노트 조건·배너). bat 골격 → Task 9. UTF-8·cwd 독립 → Task 1/8. 사이클 연동 → Task 12. **Pages 마스킹 모드(--public)는 스펙에서 "조건부 미래"로 배포 전 구현 조건 — 이번 계획 범위 밖(비목표)**.
- **타입 일관성**: `verdict_of(stem) -> {"verdict","lineage"}|None` (Task 6 소비 = Task 7 정의), 카드 `{title,lineage,star,state,link}` (Task 5 생산 = Task 7/11 소비), data.js 필드명 = 스펙 스키마와 일치 확인.
- **주의**: Task 4~5 픽스처는 실파일 축약본 — 실파일에서 파싱이 어긋나면 Task 8 스모크의 unparsed로 드러난다(그 시점에 파서 보정).
