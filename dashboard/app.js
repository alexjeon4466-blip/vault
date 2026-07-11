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

  // 탭 (role=tab / aria-selected)
  var btns = document.querySelectorAll(".tab-btn");
  btns.forEach(function (b) {
    b.addEventListener("click", function () {
      btns.forEach(function (x) {
        x.classList.remove("active");
        x.setAttribute("aria-selected", "false");
      });
      b.classList.add("active");
      b.setAttribute("aria-selected", "true");
      $("tab-creation").hidden = b.dataset.tab !== "creation";
      $("tab-bookclub").hidden = b.dataset.tab !== "bookclub";
    });
  });

  // 경고 배너 (unparsed >= 10 = 파서 파손 신호 — 방화막의 유일한 용도)
  if (d.unparsed.length >= 10) {
    $("warn-banner").hidden = false;
    $("warn-banner").textContent =
      "파서 경고: 분류 안 됨 " + d.unparsed.length + "건 — 파서 점검 필요";
  }

  // ── 현재 비행 조종석: 지금의 B/C 위치를 비추는 상태 패널.
  //    행동 제안은 여기 두지 않는다 — '오늘의 한 걸음' 하나가 그 자리다. ──
  function renderCockpit(c) {
    if (!c || !c.primary) return;
    var root = $("cockpit");
    if (!root) return;
    var panel = el("section", "cockpit-panel cockpit-" + c.primary.phaseKind);
    panel.setAttribute("aria-label", "현재 비행");
    var top = el("div", "cockpit-top");
    top.appendChild(el("div", "cockpit-kicker", "현재 비행 · " + (c.activeCycle || "")));
    if (c.activeQuestion) top.appendChild(el("div", "cockpit-question", c.activeQuestion));
    panel.appendChild(top);

    var left = el("div", "cockpit-primary");
    left.appendChild(el("div", "cockpit-label", "주력 후보"));
    var title = el("h2", "cockpit-title");
    title.appendChild(c.primary.link ? noteEl(c.primary.title, c.primary.link) : el("span", null, c.primary.title));
    left.appendChild(title);
    left.appendChild(el("p", "cockpit-phase", c.primary.phaseLabel));
    if (c.primary.blockers && c.primary.blockers.length) {
      left.appendChild(el("p", "cockpit-blockers", "주의: " + c.primary.blockers.join(" · ")));
    }
    if (c.primary.artifacts && c.primary.artifacts.length) {
      var arts = el("div", "cockpit-artifacts");
      arts.appendChild(el("span", null, "산출물"));
      c.primary.artifacts.forEach(function (a) {
        arts.appendChild(a.link ? noteEl(a.label, a.link) : el("span", null, a.label));
      });
      left.appendChild(arts);
    }
    panel.appendChild(left);

    if (c.instruments && c.instruments.length) {
      var inst = el("div", "cockpit-instruments");
      c.instruments.forEach(function (i) {
        var box = el("div", "instrument " + (i.status || "standby"));
        box.appendChild(el("span", "instrument-label", i.label));
        box.appendChild(el("strong", null, i.value));
        inst.appendChild(box);
      });
      panel.appendChild(inst);
    }

    if (c.secondary && c.secondary.length) {
      var det = el("details", "cockpit-secondary");
      det.appendChild(el("summary", null, "나란히 비행 중 " + c.secondary.length + "편"));
      c.secondary.forEach(function (s) {
        var row = el("div", "secondary-flight " + s.phaseKind);
        var name = el("b");
        name.appendChild(s.link ? noteEl(s.title, s.link) : el("span", null, s.title));
        row.appendChild(name);
        row.appendChild(el("span", null, s.phaseLabel + " — " + s.nextAction));
        det.appendChild(row);
      });
      panel.appendChild(det);
    }
    root.appendChild(panel);
  }
  renderCockpit(d.cockpit);

  // ── 오늘의 한 걸음: 이 화면이 존재하는 이유. 앰버가 닿는 유일한 행동 제안.
  //    조종석의 '다음 조작'이 첫 걸음이 되고, 전역 제안은 '그다음엔'으로 줄 선다. ──
  var acts = d.nextActions.slice();
  var flight = d.cockpit && d.cockpit.primary;
  if (flight && flight.nextAction) {
    acts = [{ text: "『" + flight.title + "』 — " + flight.nextAction, link: flight.link }]
      .concat(acts.filter(function (a) { return a.text.indexOf(flight.title) === -1; }));
  }
  $("next-hero").appendChild(el("div", "hero-label", "오늘의 한 걸음"));
  var hero = el("div", "hero-sentence");
  if (acts.length) {
    hero.appendChild(acts[0].link ? noteEl(acts[0].text, acts[0].link)
                                  : el("span", null, acts[0].text));
  } else {
    hero.textContent = "당장 할 일 없음 — 계속 쓰세요.";
  }
  $("next-hero").appendChild(hero);
  if (acts.length > 1) {
    var rest = el("div", "hero-rest");
    acts.slice(1, 4).forEach(function (a) {
      var line = el("div");
      line.appendChild(el("span", null, "그다음엔 — "));
      line.appendChild(a.link ? noteEl(a.text, a.link) : el("span", null, a.text));
      rest.appendChild(line);
    });
    $("next-hero").appendChild(rest);
  }

  // ── 두 세계의 다리: 어떤 책이 어떤 원고가 되어 무대로 가는지 한 문장. ──
  if (d.bridge) {
    var br = el("div", "bridge-line");
    br.appendChild(el("span", null, "『" + d.bridge.book + "』에서 자란 "));
    br.appendChild(noteEl("『" + d.bridge.work + "』", d.bridge.link));
    br.appendChild(el("span", null, "가 " + d.bridge.phrase + "."));
    $("bridge").appendChild(br);
  }

  // ── 서가: 미채점은 결손이 아니라 아직 읽지 않은 원고 더미다. ──
  var cov = d.cycle.coverage, un = cov.unscoredFiles.length;
  var shelfLine = el("div");
  if (un === 0) {
    shelfLine.textContent = "서가의 원고 " + cov.scored + "편을 전부 읽었습니다.";
    $("shelf").appendChild(shelfLine);
  } else {
    shelfLine.textContent =
      "지금까지 " + cov.scored + "편을 읽었고, 서가에는 새 원고 " + un + "편이 쌓여 있습니다.";
    $("shelf").appendChild(shelfLine);
    var det = el("details");
    det.appendChild(el("summary", null, "기다리는 원고 " + un + "편 펼치기"));
    var list = el("div", "waiting-list");
    cov.unscoredFiles.forEach(function (f) {
      var line = el("div");
      line.appendChild(noteEl(f.title, f.link));
      list.appendChild(line);
    });
    det.appendChild(list);
    $("shelf").appendChild(det);
  }

  // 사이클 칩 (번호 없이 — 순서는 워크플로가 안다)
  var stageNames = [["triage", "채점"], ["lineage", "계열 지도"], ["prescription", "처방"]];
  $("stepper").appendChild(el("span", "step", d.cycle.stages.label || "사이클"));
  stageNames.forEach(function (s) {
    var cls = "step" + (d.cycle.stages[s[0]] === "done" ? " done" : "");
    $("stepper").appendChild(el("span", cls, s[1]));
  });

  // ── 무대까지의 거리: 칸반(생산성 앱 문법)이 아니라 무대에 가까운 순으로
  //    쌓인 선반. 무대 코앞(개작·조립)만 핀스포트 앰버 ★를 받는다. ──
  var SHELVES = [
    { key: "개작", label: "개작 중", note: "무대 코앞", near: true },
    { key: "조립", label: "조립 중", note: null, near: true },
    { key: "대기", label: "차례 대기", note: null, near: false },
    { key: "설계", label: "설계 단계", note: null, near: false }
  ];
  function workEl(c, near) {
    var w = el("span", "work" + (near ? " work-near" : ""));
    if (c.star && near) w.appendChild(el("span", "star", "★ "));
    w.appendChild(noteEl(c.title, c.link));
    if (near && c.lineage) w.appendChild(el("small", "work-lin", c.lineage));
    return w;
  }
  SHELVES.forEach(function (sh) {
    var cards = d.pipeline.columns[sh.key] || [];
    var shelf = el("div", "shelf" + (sh.near ? " shelf-near" : ""));
    var lab = el("div", "shelf-label");
    lab.appendChild(el("span", null, sh.label));
    var count = cards.length;
    lab.appendChild(el("small", "shelf-note", sh.note || (count + "편")));
    shelf.appendChild(lab);
    var works = el("div", "shelf-works");
    if (!count) {
      works.appendChild(el("span", "shelf-empty", "아직 없음"));
    }
    var LIMIT = sh.near ? count : 6;   // 무대 근처는 전부, 먼 선반은 6편 + 서랍
    cards.slice(0, LIMIT).forEach(function (c) { works.appendChild(workEl(c, sh.near)); });
    if (count > LIMIT) {
      var more = el("details", "shelf-more");
      more.appendChild(el("summary", null, "…그리고 " + (count - LIMIT) + "편 더"));
      cards.slice(LIMIT).forEach(function (c) { more.appendChild(workEl(c, false)); });
      works.appendChild(more);
    }
    shelf.appendChild(works);
    $("stage-shelves").appendChild(shelf);
  });

  // 병합 후보: 호버 뒤에 숨기지 않고 펼치면 문장으로
  if (d.pipeline.mergers.length) {
    var mdet = el("details");
    mdet.appendChild(el("summary", null, "병합 후보 " + d.pipeline.mergers.length + "건 — 다음 행동 보기"));
    var ul = el("ul");
    d.pipeline.mergers.forEach(function (m) {
      var li = el("li");
      var name = el("b", null, m.id + " " + m.title);
      li.appendChild(name);
      li.appendChild(el("span", null, " — " + m.nextAction));
      ul.appendChild(li);
    });
    mdet.appendChild(ul);
    $("mergers").appendChild(mdet);
  }

  // ── 계열 서랍: 움직이는 계열만 기본 표시, 주석은 낮은 목소리로 ──
  function lineageTable(rows) {
    var t = el("table"), head = el("tr");
    ["계열", "운반체", "★", "구성원", "부품", "상태"].forEach(function (h) {
      head.appendChild(el("th", null, h));
    });
    t.appendChild(head);
    rows.forEach(function (l) {
      var tr = el("tr");
      var nameCell = el("td", null, l.name);
      if (l.annotation) nameCell.appendChild(el("small", "lineage-note", l.annotation));
      tr.appendChild(nameCell);
      tr.appendChild(el("td", l.carrier ? null : "no-carrier",
                       l.carrier || "운반체 결정 필요"));
      tr.appendChild(el("td", "star-quiet", String(l.stars)));
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

  // 풋노트 (0건이면 미렌더)
  if (d.unparsed.length > 0) {
    var det3 = el("details");
    det3.appendChild(el("summary", null, "분류 안 됨 " + d.unparsed.length + "건"));
    d.unparsed.forEach(function (u) {
      det3.appendChild(el("div", null, u.file + " — " + u.reason));
    });
    $("footnote").appendChild(det3);
  }

  // ── 독서모임: 창작 전초기지가 아니라 해석·질문·강의 조종석 ──
  var bc = d.bookclub;
  var br = d.bookclubReading || { books: [], questions: [], lectures: [] };
  var readingByTitle = {};
  br.books.forEach(function (b) { readingByTitle[b.title] = b; });

  function metricText(m) {
    return "읽기 " + m.closeReadings + " · 질문 " + m.questionLinks +
           " · 비교 " + m.lectureLinks + " · 창작 " + m.writingLinks;
  }

  // 책카드에서 딸려온 목록 번호(1. )와 백틱은 화면에 내보내지 않는다
  function cleanAxis(s) {
    return (s || "").replace(/^\s*\d+\.\s*/, "").replace(/`/g, "").trim();
  }

  // 독서 조종석도 상태 패널이다 — 행동 제안은 아래 '다음 모임의 한 걸음' 하나.
  function renderReadingCockpit(r) {
    if (!r || !r.focus) return;
    var root = $("reading-cockpit");
    if (!root) return;
    var f = r.focus;
    var panel = el("section", "reading-panel");
    panel.setAttribute("aria-label", "현재 독서 좌표");
    var top = el("div", "reading-top");
    top.appendChild(el("div", "reading-kicker", "현재 독서 좌표"));
    top.appendChild(el("div", "reading-question", f.centerQuestion || "다음 독서 질문"));
    panel.appendChild(top);

    var left = el("div");
    left.appendChild(el("div", "cockpit-label", "살아 있는 책"));
    var title = el("h2", "reading-title");
    title.appendChild(noteEl(f.title, f.cardPath));
    left.appendChild(title);
    left.appendChild(el("p", "reading-axis", cleanAxis(f.axis)));
    panel.appendChild(left);

    var chips = el("div", "reading-metrics");
    [["읽기", f.metrics.closeReadings], ["질문", f.metrics.questionLinks], ["비교", f.metrics.lectureLinks], ["창작", f.metrics.writingLinks], ["글감 파생", f.metrics.derivedNotes]].forEach(function (m) {
      var chip = el("span", "reading-chip");
      chip.appendChild(el("b", null, m[0]));
      chip.appendChild(el("span", null, String(m[1])));
      chips.appendChild(chip);
    });
    panel.appendChild(chips);

    var links = el("div", "reading-links");
    if (f.topQuestions && f.topQuestions.length) {
      var q = el("div"); q.appendChild(el("span", "reading-link-label", "질문"));
      f.topQuestions.slice(0, 3).forEach(function (x) { q.appendChild(noteEl(x.title, x.link)); });
      links.appendChild(q);
    }
    if (f.topLectures && f.topLectures.length) {
      var l = el("div"); l.appendChild(el("span", "reading-link-label", "비교"));
      f.topLectures.slice(0, 3).forEach(function (x) { l.appendChild(noteEl(x.title, x.link)); });
      links.appendChild(l);
    }
    panel.appendChild(links);
    root.appendChild(panel);
  }
  renderReadingCockpit(br);

  // ── 다음 모임의 한 걸음: 독서모임 탭의 유일한 행동 제안 (창작 탭 히어로와 대칭) ──
  if (br.focus && br.focus.nextAction) {
    $("reading-hero").appendChild(el("div", "hero-label", "다음 모임의 한 걸음"));
    var rHero = el("div", "hero-sentence");
    rHero.appendChild(noteEl(br.focus.nextAction, br.focus.cardPath));
    $("reading-hero").appendChild(rHero);
  }

  // ── 돌아오는 다리: 창작 탭의 다리와 대칭 — 이 책의 질문이 창작으로 흐른 만큼 ──
  if (br.focus) {
    var focusBook = bc.books.filter(function (b) { return b.title === br.focus.title; })[0];
    if (focusBook && focusBook.derivedNotes > 0) {
      var rb2 = el("div", "bridge-line");
      rb2.appendChild(el("span", null, "『" + focusBook.title + "』의 질문에서 글감 "));
      rb2.appendChild(el("b", null, focusBook.derivedNotes + "편"));
      rb2.appendChild(el("span", null, focusBook.stars
        ? "이 자랐고, 그중 " + focusBook.stars + "편이 유망★로 무대를 바라봅니다."
        : "이 자라고 있습니다."));
      $("reading-bridge").appendChild(rb2);
    }
  }

  var mined = bc.books.filter(function (b) { return b.derivedNotes > 0; }).length;
  $("bc-summary").textContent =
    "함께 읽은 " + bc.books.length + "권 가운데 " + mined + "권이 글감으로도 이어졌고, " +
    (br.questions ? br.questions.length : 0) + "개의 질문과 " + (br.lectures ? br.lectures.length : 0) +
    "개의 비교 강의가 독서의 좌표를 만들고 있습니다. 모임 기록 " + bc.rawTotal + "편, 원본 장치 지도 " + bc.deviceMapTotal + "권.";

  // ── 질문망: 추상 명사가 아니라 질문형 노트가 책들을 잇는다 ──
  var QN_LIMIT = 7;
  function questionRow(q) {
    var row = el("div", "question-row");
    var sent = el("span", "question-sentence");
    sent.appendChild(noteEl(q.title, q.link));
    row.appendChild(sent);
    row.appendChild(el("span", "question-meta", "책 " + q.books.length + "권"));
    return row;
  }
  (br.questions || []).slice(0, QN_LIMIT).forEach(function (q) {
    $("question-net").appendChild(questionRow(q));
  });
  if ((br.questions || []).length > QN_LIMIT) {
    var qDet = el("details");
    qDet.appendChild(el("summary", null, "질문 " + (br.questions.length - QN_LIMIT) + "개 더 보기"));
    br.questions.slice(QN_LIMIT).forEach(function (q) { qDet.appendChild(questionRow(q)); });
    $("question-net").appendChild(qDet);
  }

  // ── 책 서가: 해석이 두터운 순으로 앞줄만 카드, 나머지는 서가 안쪽 ──
  var SHELF_LIMIT = 12;
  var byScore = bc.books.slice().sort(function (a, b) {
    var ra = readingByTitle[a.title], rb = readingByTitle[b.title];
    return ((rb && rb.readingScore) || 0) - ((ra && ra.readingScore) || 0);
  });
  byScore.slice(0, SHELF_LIMIT).forEach(function (b) {
    var rb = readingByTitle[b.title];
    var card = el("div", "book-card" + ((rb && rb.readingScore) ? "" : " unmined"));
    var title = el("div", "book-title");
    title.appendChild(noteEl(b.title, b.cardPath));
    if (b.stars) title.appendChild(el("span", "star-quiet", " ★" + b.stars));
    card.appendChild(title);
    if (rb) {
      card.appendChild(el("div", "book-axis", cleanAxis(rb.axis)));
      card.appendChild(el("div", "tags", metricText(rb)));
      card.appendChild(el("div", "tags dim", "글감 파생 " + rb.derivedNotes));
    } else {
      card.appendChild(el("div", "tags", "아직 해석 지표 없음"));
    }
    $("bc-shelf").appendChild(card);
  });
  if (byScore.length > SHELF_LIMIT) {
    var sDet = el("details");
    sDet.appendChild(el("summary", null, "서가 안쪽 " + (byScore.length - SHELF_LIMIT) + "권 더 보기"));
    var inner = el("div", "shelf-inner");
    byScore.slice(SHELF_LIMIT).forEach(function (b) {
      var rb = readingByTitle[b.title];
      var line = el("div", "shelf-inner-line");
      line.appendChild(noteEl(b.title, b.cardPath));
      line.appendChild(el("span", "tags", rb ? " — " + metricText(rb) : " — 아직 해석 지표 없음"));
      inner.appendChild(line);
    });
    sDet.appendChild(inner);
    $("bc-shelf-rest").appendChild(sDet);
  }

  // ── 비교 강의 선반: 책과 책이 마주 앉은 자리 ──
  var LEC_LIMIT = 8;
  function lectureRow(l) {
    var row = el("div", "lecture-row");
    var name = el("span", "lecture-title");
    name.appendChild(noteEl(l.title, l.link));
    row.appendChild(name);
    if (l.books && l.books.length) {
      row.appendChild(el("span", "lecture-books", l.books.map(function (t) { return "『" + t + "』"; }).join(" × ")));
    }
    return row;
  }
  (br.lectures || []).slice(0, LEC_LIMIT).forEach(function (l) {
    $("lecture-shelf").appendChild(lectureRow(l));
  });
  if ((br.lectures || []).length > LEC_LIMIT) {
    var lDet = el("details");
    lDet.appendChild(el("summary", null, "강의 " + (br.lectures.length - LEC_LIMIT) + "편 더 보기"));
    br.lectures.slice(LEC_LIMIT).forEach(function (l) { lDet.appendChild(lectureRow(l)); });
    $("lecture-shelf").appendChild(lDet);
  }

  var top = (br.books || []).slice(0, 10).filter(function (b) { return b.readingScore > 0; });
  var maxD = Math.max.apply(null, top.map(function (b) { return b.readingScore; }).concat([1]));
  top.forEach(function (b) {
    var row = el("div", "flow-row");
    row.appendChild(el("span", "flow-label", b.title));
    var bar = el("div", "flow-bar reading-bar");
    bar.style.width = (b.readingScore / maxD) * 60 + "%";
    row.appendChild(bar);
    row.appendChild(el("span", "tags", b.readingScore + "점"));
    $("bc-flow").appendChild(row);
  });
})();
