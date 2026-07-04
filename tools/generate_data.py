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
