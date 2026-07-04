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
