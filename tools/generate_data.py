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
                # Split on commas, strip backticks and whitespace from each piece
                text_part = bullet.group(1).strip()
                for piece in text_part.split(','):
                    piece = piece.strip().strip('`').strip()
                    if piece and '[[' not in piece:
                        excluded.add(piece)
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


_CARD_STATES = {"개작", "조립", "대기"}


_ROLE_KEYWORDS = ("운반체", "독립", "병합 짝", "부품", "비트", "체인", "교차", "재해석", "소품")


def _clean_title(cell):
    """셀에서 표시용 제목: 위키링크 별칭 우선, 없으면 타깃 스템, 플레인은 그대로."""
    m = re.search(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', cell)
    if m:
        return (m.group(2) or m.group(1).split("/")[-1]).strip()
    plain = cell.replace("*", "").replace("★", "").strip()
    plain = re.split(r'\(|（|\s+—\s+', plain)[0].strip()
    return plain


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
        carrier, stars, members, parts, state = None, 0, 0, 0, "설계"
        no_carrier = "운반체 없음" in sec
        try:
            for table in extract_tables(sec):
                head = table[0]
                if _find_col(head, "역할") is None:
                    if head and any(kw in head[0] for kw in _ROLE_KEYWORDS):
                        data_rows = table
                    else:
                        continue
                else:
                    data_rows = table[1:]
                for row in data_rows:
                    if len(row) < 3:
                        continue
                    role, item, st = row[0], row[1], row[2].replace("*", "").strip()
                    stars += item.count("★")
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
