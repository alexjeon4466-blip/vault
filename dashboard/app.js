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

  // ── 오늘의 한 걸음: 이 화면이 존재하는 이유. 첫 번째 제안 하나만 크게. ──
  var acts = d.nextActions;
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
    acts.slice(1).forEach(function (a) {
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

  // ── 독서모임: 숫자 타일이 아니라 문장으로 ──
  var bc = d.bookclub;
  var mined = bc.books.filter(function (b) { return b.derivedNotes > 0; }).length;
  $("bc-summary").textContent =
    "함께 읽은 " + bc.books.length + "권 가운데 " + mined + "권이 글감이 되었습니다. " +
    "모임의 기록 " + bc.rawTotal + "편, 원본에서 캐낸 장치 지도 " + bc.deviceMapTotal + "권.";

  bc.books.forEach(function (b) {
    var card = el("div", "book-card" + (b.derivedNotes ? "" : " unmined"));
    var title = el("div", "book-title");
    title.appendChild(noteEl(b.title, b.cardPath));
    if (b.stars) title.appendChild(el("span", "star-quiet", " ★" + b.stars));
    card.appendChild(title);
    card.appendChild(el("div", "tags",
      b.derivedNotes
        ? "글감 " + b.derivedNotes + (b.lineages.length ? " · " + b.lineages.join(", ") : "")
        : "아직 채굴 전"));
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
