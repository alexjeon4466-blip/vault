# -*- coding: utf-8 -*-
"""vault 스캔 → dashboard/data.js 생성. 쓰기 대상은 OUTPUT 하나뿐."""
import collections
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = VAULT_ROOT / "dashboard" / "data.js"

KNOWN_TOTALS = {"scored": 970, "stars": 94, "twins": 853}  # 사이클 4 종료 시점 재보정


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
    if m:
        name = m.group(1).split("/")[-1]
    else:
        name = cell.replace("*", "").strip()
        name = name.split("★", 1)[0]
        name = re.split(r'\(|（|\s+—\s+', name)[0]
    if name.endswith("_scored"):
        name = name[:-len("_scored")]
    return name.strip().replace(" ", "_")


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


def display_title(stem):
    """파일 스템 → 사람용 제목. 언더스코어는 기계의 흔적이라 화면에 내보내지 않는다."""
    return stem.replace("_", " ").strip()


def split_lineage_name(raw):
    """계열 헤더에서 이름과 괄호 주석을 분리. 이름 속 '—'는 보존한다."""
    m = re.match(r'^(.*?)\s*[（(](.*)$', raw)
    if not m:
        return raw.strip(), None
    name = m.group(1).strip()
    ann = re.sub(r'\s+', ' ', m.group(2).replace(")", " ").replace("）", " ")).strip(" —-·")
    return name, (ann or None)


def _clean_title(cell):
    """셀에서 표시용 제목: 위키링크 별칭 우선, 없으면 타깃 스템, 플레인은 그대로."""
    m = re.search(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', cell)
    if m:
        return display_title((m.group(2) or m.group(1).split("/")[-1]).strip())
    plain = cell.replace("*", "").replace("★", "").strip()
    plain = re.split(r'\(|（|\s+—\s+', plain)[0].strip()
    return display_title(plain)


def _link_from_cell(cell):
    m = re.search(r'\[\[([^\]|]+)', cell)
    if m:
        path = m.group(1).strip()
        return path[:-len("_scored")] if path.endswith("_scored") else path
    return None


def read_cockpit_override(vault_root, unparsed):
    """dashboard/cockpit.json은 공식 상태가 아니라 현재 조종석 초점 override다."""
    p = vault_root / "dashboard" / "cockpit.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(read_text(p))
    except Exception as exc:
        unparsed.append({"file": "dashboard/cockpit.json",
                         "reason": "cockpit override JSON 파싱 실패: %s" % exc})
        return {}
    return data if isinstance(data, dict) else {}


def _strip_md(rel):
    return rel[:-3] if rel.endswith(".md") else rel


def resolve_work_link(vault_root, cell, stem):
    """위키링크가 없는 계열 지도 plain text 항목도 실제 산출물로 연결한다."""
    direct = _link_from_cell(cell)
    if direct:
        return direct
    candidates = [
        "wiki/writing/draft-candidates/%s_단막후보_맵.md" % stem,
        "wiki/writing/draft-candidates/%s_구조맵.md" % stem,
        "wiki/writing/drafts/%s_첫장면.md" % stem,
        "wiki/writing/draft-candidates/%s_첫장면_초안.md" % stem,
        "wiki/writing/notes/%s.md" % stem,
    ]
    for rel in candidates:
        if (vault_root / rel).is_file():
            return _strip_md(rel)
    return None


def detect_artifacts(vault_root, stem):
    candidates = [
        ("B2", "단막 후보 맵", "wiki/writing/draft-candidates/%s_단막후보_맵.md" % stem),
        ("B2", "구조맵", "wiki/writing/draft-candidates/%s_구조맵.md" % stem),
        ("C1-tone", "첫 장면", "wiki/writing/drafts/%s_첫장면.md" % stem),
        ("C1", "장면 초안", "wiki/writing/draft-candidates/%s_첫장면_초안.md" % stem),
        ("C2", "연결본", "wiki/writing/drafts/%s_1-N장_연결본.md" % stem),
        ("C2", "1막초고", "wiki/writing/drafts/%s_1막초고.md" % stem),
    ]
    out = []
    for kind, label, rel in candidates:
        p = vault_root / rel
        if p.is_file():
            out.append({"kind": kind, "label": label, "link": _strip_md(rel)})
    return out


def _has_b4_pass(vault_root, artifacts):
    for a in artifacts:
        if a["kind"] != "B2":
            continue
        p = vault_root / (a["link"] + ".md")
        text = read_text(p) if p.is_file() else ""
        if "B4 맵 검증형 재채점" in text and ("B2 통과" in text or "C1 진입" in text):
            return True
    return False


def derive_phase(vault_root, card):
    artifacts = detect_artifacts(vault_root, card.get("stem") or card["title"].replace(" ", "_"))
    kinds = {a["kind"] for a in artifacts}
    state = card.get("state") or card.get("officialState") or "설계"
    if state == "개작":
        kind, label, action = "revising", "C3 개작 중", "현재판 평가·기능감사·체크리스트 순서로 개작 루프 진행"
    elif state == "조립":
        kind, label, action = "assembling", "C1 장면 조립 중", "장면 초안 1개 또는 연결부 퇴고표 작성"
    elif state == "대기":
        kind, label, action = "ready-for-c1", "C1 진입 준비 완료", "첫 장면 조립"
    elif "B2" in kinds and _has_b4_pass(vault_root, artifacts):
        kind, label, action = "ready-for-c1", "B2 구조맵 작성 · B4 검증 통과 · C1 진입 대기", "계열 지도 상태를 대기 반영 후 C1 첫 장면 조립"
    elif "C1-tone" in kinds and "B2" not in kinds:
        kind, label, action = "tone-spike", "C1 톤 확인 장면 있음 · 정식 B2 구조맵 필요", "톤을 살릴지 결정한 뒤 B2 구조맵 작성"
    elif "B2" in kinds:
        kind, label, action = "b2-map", "B2 구조맵 있음 · B4 검증 필요", "B4 맵 검증형 재채점"
    else:
        kind, label, action = "designing", "설계 단계", "B1 소집 또는 B2 구조맵 작성"
    return {"phaseKind": kind, "phaseLabel": label, "nextAction": action, "artifacts": artifacts}


def _card_identity(card):
    return (card.get("stem") or card.get("title", "")).replace(" ", "_")


def _enrich_cockpit_card(vault_root, card):
    phase = derive_phase(vault_root, card)
    link = card.get("link")
    if not link and phase["artifacts"]:
        link = phase["artifacts"][0]["link"]
    return {
        "title": card["title"],
        "link": link,
        "lineage": card.get("lineage"),
        "officialState": card.get("state", "설계"),
        "role": card.get("role"),
        "note": card.get("note"),
        "phaseKind": phase["phaseKind"],
        "phaseLabel": phase["phaseLabel"],
        "nextAction": phase["nextAction"],
        "reason": card.get("note") or ("산출물과 계열 지도 상태를 함께 판정"),
        "blockers": (["상태 전이 미반영"] if phase["phaseKind"] == "ready-for-c1" and card.get("state") == "설계" else []),
        "artifacts": phase["artifacts"],
    }


def build_cockpit(vault_root, cards, coverage, unparsed):
    override = read_cockpit_override(vault_root, unparsed)
    by_id = {_card_identity(c): c for c in cards}
    enriched = [_enrich_cockpit_card(vault_root, c) for c in cards]
    enriched_by_id = {_card_identity(c): _enrich_cockpit_card(vault_root, c) for c in cards}

    def pick_auto():
        order = {"revising": 0, "assembling": 1, "ready-for-c1": 2, "tone-spike": 3, "b2-map": 4, "designing": 5}
        return sorted(enriched, key=lambda c: (order.get(c["phaseKind"], 9), c["title"]))[0] if enriched else None

    primary = enriched_by_id.get(override.get("primary")) if override.get("primary") else None
    primary = primary or pick_auto()
    secondary = []
    for ident in override.get("secondary", []) if isinstance(override.get("secondary", []), list) else []:
        if ident in enriched_by_id and (not primary or enriched_by_id[ident]["title"] != primary["title"]):
            secondary.append(enriched_by_id[ident])
    if not secondary:
        secondary = [c for c in enriched if primary and c["title"] != primary["title"]][:2]

    active_cycle = "B→C" if primary and primary["phaseKind"] in {"ready-for-c1", "tone-spike", "b2-map"} else "C" if primary and primary["phaseKind"] in {"assembling", "revising"} else "A/B"
    # 계기판 = A/B/C 세 사이클의 고도계. 패널 본문(현재 위치·다음 조작)과 중복 금지.
    in_b = primary is not None and primary["phaseKind"] in {"designing", "b2-map", "tone-spike", "ready-for-c1"}
    in_c = primary is not None and primary["phaseKind"] in {"assembling", "revising"}
    state_count = {}
    for c in cards:
        st = c.get("state", "설계")
        state_count[st] = state_count.get(st, 0) + 1
    instruments = [
        {"label": "A 사이클 — 채점", "value": "채점 %d · 미채점 %d" % (coverage.get("scored", 0), len(coverage.get("unscoredFiles", []))), "status": "ok"},
        {"label": "B 사이클 — 구조", "value": "설계 %d · 대기 %d" % (state_count.get("설계", 0), state_count.get("대기", 0)), "status": "attention" if in_b else "standby"},
        {"label": "C 사이클 — 원고", "value": "조립 %d · 개작 %d" % (state_count.get("조립", 0), state_count.get("개작", 0)), "status": "attention" if in_c else "standby"},
    ]
    return {"generatedFrom": "wiki/shared/maps/글감_계열_병합_지도.md",
            "activeCycle": active_cycle,
            "activeQuestion": override.get("question") or "지금 어디를 날고 있나?",
            "primary": primary,
            "secondary": secondary,
            "instruments": instruments}


def parse_lineage_map(text, unparsed):
    lineages, cards = [], []
    for sec in re.split(r'(?m)^### ', text)[1:]:
        header = sec.split("\n", 1)[0].strip()
        m = re.match(r'(?:\d+\.\s*)?(.+)$', header)
        name, annotation = split_lineage_name(m.group(1).strip() if m else header)
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
                    note = row[3].replace("*", "").strip() if len(row) > 3 else None
                    stem = stem_from_cell(item)
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
                                      "link": _link_from_cell(item),
                                      "stem": stem,
                                      "role": role,
                                      "note": note})
        except Exception as exc:  # 관대한 파싱: 섹션 단위로만 실패
            unparsed.append({"file": "글감_계열_병합_지도.md",
                             "reason": "계열 섹션 파싱 실패(%s): %s" % (name, exc)})
            continue
        lineages.append({"name": name, "annotation": annotation, "carrier": carrier,
                         "stars": stars, "members": members, "parts": parts, "state": state})
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


def extract_wikilinks(text, prefix=None):
    links = []
    for m in re.finditer(r'\[\[([^\]|#]+)', text):
        link = m.group(1).strip()
        if prefix is None or link.startswith(prefix):
            links.append(link)
    return sorted(set(links))


def note_link_from_path(path, vault_root):
    rel = path.relative_to(vault_root).as_posix()
    return rel[:-3] if rel.endswith(".md") else rel


def extract_axis(text):
    headings = ("한 줄 핵심", "핵심", "내 해석", "중심 질문")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("##") or not any(h in line for h in headings):
            continue
        for nxt in lines[i + 1:i + 8]:
            val = nxt.strip().lstrip(">- ").strip()
            if not val or val.startswith("#") or val.startswith("|"):
                continue                                  # 표 행은 축 문장이 아니다
            val = re.sub(r'^\d+[.)]\s*', '', val)          # 목록 번호는 화면에 내보내지 않는다
            val = val.replace("**", "").replace("`", "").strip()
            if val:
                return val[:80]
    return "축 미정"


def read_reading_override(vault_root, unparsed):
    p = vault_root / "dashboard" / "reading_cockpit.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(read_text(p))
    except Exception as exc:
        unparsed.append({"file": "dashboard/reading_cockpit.json",
                         "reason": "reading cockpit override JSON 파싱 실패: %s" % exc})
        return {}
    return data if isinstance(data, dict) else {}


def scan_bookclub_reading(vault_root, bookclub, unparsed):
    lectures_dir = vault_root / "wiki" / "bookclub" / "lectures"
    lecture_files = sorted(lectures_dir.glob("*.md")) if lectures_dir.is_dir() else []
    known_titles = {b["title"] for b in bookclub.get("books", [])}
    books = []
    for b in bookclub.get("books", []):
        title = b["title"]
        card_path = vault_root / (b["cardPath"] + ".md")
        card_text = read_text(card_path) if card_path.is_file() else ""
        close = []
        if card_path.parent.is_dir():
            close = [p for p in sorted(card_path.parent.glob("*.md"))
                     if p.name != "00_책카드.md" and not p.name.startswith("00_")]
        qlinks = extract_wikilinks(card_text, "wiki/shared/questions/")
        wlinks = extract_wikilinks(card_text, "wiki/writing/")
        linked_lectures = set(extract_wikilinks(card_text, "wiki/bookclub/lectures/"))
        for lp in lecture_files:
            ltext = read_text(lp)
            if title in lp.stem or b["cardPath"] in extract_wikilinks(ltext):
                linked_lectures.add(note_link_from_path(lp, vault_root))
        derived = b.get("derivedNotes", 0)
        score = len(close) * 4 + len(qlinks) * 3 + len(linked_lectures) * 5 + min(len(wlinks), 12) + min(derived, 12)
        books.append({
            "title": title, "cardPath": b["cardPath"], "axis": extract_axis(card_text),
            "closeReadings": len(close), "questionLinks": len(qlinks),
            "lectureLinks": len(linked_lectures), "writingLinks": len(wlinks),
            "derivedNotes": derived, "readingScore": score,
            "topQuestions": [{"title": q.split("/")[-1], "link": q} for q in qlinks[:5]],
            "topLectures": [{"title": l.split("/")[-1].replace("_", " "), "link": l} for l in sorted(linked_lectures)[:5]],
            "closeReadingLinks": [{"title": p.stem.replace("_", " "), "link": note_link_from_path(p, vault_root)} for p in close[:5]],
        })
    books.sort(key=lambda b: (-b["readingScore"], b["title"]))
    q_counter = collections.Counter()
    q_books = collections.defaultdict(list)
    for b in books:
        for q in b["topQuestions"]:
            q_counter[q["link"]] += 1
            q_books[q["link"]].append(b["title"])
    questions = [{"title": q.split("/")[-1], "link": q, "books": q_books[q],
                  "strength": "strong" if count >= 2 else "medium"}
                 for q, count in q_counter.most_common(12)]
    lectures = []
    for lp in lecture_files:
        ltext = read_text(lp)
        body_links = extract_wikilinks(ltext)
        touched = [t for t in known_titles if t in lp.stem or ("wiki/bookclub/books/%s/00_책카드" % t) in body_links]
        if touched:
            lectures.append({"title": lp.stem.replace("_", " "), "link": note_link_from_path(lp, vault_root),
                             "books": sorted(touched), "axis": extract_axis(ltext)})
    override = read_reading_override(vault_root, unparsed)
    focus = next((b for b in books if b["title"] == override.get("focusBook")), None) if override.get("focusBook") else None
    focus = focus or (books[0] if books else None)
    if focus:
        focus = dict(focus)
        focus["centerQuestion"] = override.get("question") or (focus["topQuestions"][0]["title"] if focus["topQuestions"] else focus["axis"])
        focus["nextAction"] = override.get("nextAction") or "이 책의 해석 축을 10분 독서모임 발화로 압축"
        focus["metrics"] = {"closeReadings": focus["closeReadings"], "questionLinks": focus["questionLinks"],
                             "lectureLinks": focus["lectureLinks"], "writingLinks": focus["writingLinks"],
                             "derivedNotes": focus["derivedNotes"]}
    return {"focus": focus, "questions": questions, "books": books, "lectures": lectures[:20]}


MAP_SELF = "글감_트리아지_지도"

# 진단·도구 문서 파일명 접미 — 특정 원고의 퇴고 도구지 트리아지할 글감이 아니다.
# 접미 뒤에 _YYYY-MM-DD 날짜가 붙는 경우(작업체크리스트·현재판_평가)도 잡는다.
_TOOL_SUFFIXES = ("기능감사", "작업체크리스트", "현재판_평가", "반복어",
                  "퇴고표", "맵", "어휘표", "물성표")
# 진단·도구 문서 type. writing-note 이외는 이미 게이트에서 빠지지만 명시적으로 둔다.
_TOOL_TYPES = {"writing-evaluation", "writing-checklist"}
_DATE_SUFFIX_RE = re.compile(r'_\d{4}-\d{2}-\d{2}$')


def is_tool_note(stem, note_type=None):
    """진단/도구 문서면 True — 미채점 글감 카운트에서 제외한다.
    type이 도구류거나, (날짜 접미 제거 후) 파일명이 도구 접미로 끝나면 도구로 본다."""
    if note_type in _TOOL_TYPES:
        return True
    base = _DATE_SUFFIX_RE.sub("", stem)
    return any(base == s or base.endswith("_" + s) for s in _TOOL_SUFFIXES)


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
        note_type = parse_frontmatter(read_text(p)).get("type")
        if note_type != "writing-note":
            continue
        if is_tool_note(stem, note_type):     # writing-note로 위장한 진단/도구 문서 제외
            continue
        out.append({"title": display_title(stem), "link": "wiki/writing/notes/" + stem})
    return out


_STAGE_ORDER = {"개작": 0, "조립": 1, "설계": 2, "대기": 3}


def compute_next_actions(unscored, lineages, cards):
    """히어로는 원자적이고 실행 가능한 한 걸음이어야 한다. 무대에 가까운 원고 먼저,
    백로그 숫자는 마지막 수단(서가 문장이 이미 그것을 말한다)."""
    acts = []
    # 1. 무대에 가장 가까운 원고 — 이어서 할 일, 링크를 가진다
    for state, verb in (("개작", "개작을 이어서"), ("조립", "조립을 마저")):
        for c in cards:
            if len(acts) >= 3:
                break
            if c["state"] == state:
                acts.append({"text": "『%s』 %s" % (c["title"], verb), "link": c.get("link")})
                break
    # 2. 설계 단계의 유망★ — 처방부터
    for c in cards:
        if len(acts) >= 3:
            break
        if c["state"] == "설계" and c["star"]:
            acts.append({"text": "『%s』 처방부터" % c["title"], "link": c.get("link")})
            break
    # 3. 운반체 미정 계열
    for lin in lineages:
        if len(acts) >= 3:
            break
        if lin["carrier"] is None and lin["stars"] > 0:
            acts.append({"text": "『%s』 계열 운반체 지정" % lin["name"], "link": None})
    # 4. 백로그 — 다른 할 일이 하나도 없을 때만
    if not acts and len(unscored) >= 10:
        acts.append({"text": "새 원고 %d편 트리아지" % len(unscored), "link": None})
    if not acts:
        acts.append({"text": "당장 할 일 없음 — 계속 쓰세요.", "link": None})
    return acts[:3]


_BRIDGE_PHRASE = {"개작": "무대에 오르고 있습니다", "조립": "무대로 향합니다",
                  "설계": "이제 막 설계에 들어갔습니다", "대기": "차례를 기다립니다"}


def compute_bridge(cards, work_book):
    """두 세계의 다리: 무대에 가장 가까운 원고가 어느 책에서 자랐는지 한 문장으로.
    책을 역추적할 수 있는 첫 원고를 고른다(개작→조립→설계 순)."""
    for c in sorted(cards, key=lambda c: _STAGE_ORDER.get(c["state"], 9)):
        link = c.get("link")
        if not link:
            continue
        book = work_book.get(link.split("/")[-1])
        if book:
            return {"book": book, "work": c["title"], "link": link,
                    "phrase": _BRIDGE_PHRASE.get(c["state"], "무대로 향합니다")}
    return None


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

    all_scored = {s for s in (set(twins) | set(triage["entries"]))
                  if (verdict_of(s) or {}).get("verdict") in _COUNTED}
    unscored = compute_unscored(vault_root, twins, triage["entries"], triage["excluded"])

    note_sources = scan_note_sources(vault_root)
    bookclub = scan_books(vault_root, note_sources, verdict_of)
    bookclub_reading = scan_bookclub_reading(vault_root, bookclub, unparsed)

    for c in lmap["cards"]:
        if not c.get("link"):
            c["link"] = resolve_work_link(vault_root, c["title"], c.get("stem") or c["title"].replace(" ", "_"))

    columns = {"설계": [], "대기": [], "조립": [], "개작": []}
    for c in lmap["cards"]:
        columns.get(c["state"], columns["설계"]).append(
            {"title": c["title"], "lineage": c["lineage"], "star": c["star"],
             "link": c["link"], "role": c.get("role"), "note": c.get("note")})

    # 원고 → 책 역인덱스 (다리 문장용): 노트 sources가 가리키는 책카드 경로로 매핑
    book_title_by_key = {b["cardPath"]: b["title"] for b in bookclub["books"]}
    work_book = {}
    for stem, srcs in note_sources.items():
        for s in srcs:
            if s in book_title_by_key:
                work_book.setdefault(stem, book_title_by_key[s])
                break

    coverage = {"scored": len(all_scored), "unscoredFiles": unscored}
    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "vaultName": vault_root.name,
        "nextActions": compute_next_actions(unscored, lmap["lineages"], lmap["cards"]),
        "bridge": compute_bridge(lmap["cards"], work_book),
        "bookclub": bookclub,
        "bookclubReading": bookclub_reading,
        "cockpit": build_cockpit(vault_root, lmap["cards"], coverage, unparsed),
        "cycle": {
            "stages": {"triage": "done" if not unscored else "pending",
                       "lineage": "done", "prescription": "done", "label": "사이클 1회차"},
            "coverage": coverage,
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


def write_data_js(data, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = "window.VAULT_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    out.write_text(payload, encoding="utf-8", newline="")


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
