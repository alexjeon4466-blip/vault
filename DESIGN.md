---
name: Vault 대시보드
description: 극작가의 무대 뒤 작업실 — 독서와 창작의 진행을 비추는 조용한 화면
colors:
  stage-dark: "#14161a"
  backstage-panel: "#1d2026"
  backstage-panel-high: "#23272e"
  chalk-line: "#2c3038"
  chalk-line-high: "#454b55"
  script-ink: "#e6e6e3"
  stage-whisper: "#9aa0a8"
  dust: "#6b7280"
  pinspot-amber: "#d4a73f"
  exit-green: "#4f9d69"
  cue-yellow: "#e0b64a"
  fire-curtain-red: "#c05b4d"
typography:
  headline:
    fontFamily: "Pretendard Variable, Pretendard, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.4
  title:
    fontFamily: "Pretendard Variable, Pretendard, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.45
  body:
    fontFamily: "Pretendard Variable, Pretendard, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Pretendard Variable, Pretendard, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  none: "0px"
  sm: "4px"
  md: "6px"
  pill: "20px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "12px"
  lg: "20px"
  xl: "28px"
components:
  tab-button:
    backgroundColor: "{colors.backstage-panel}"
    textColor: "{colors.stage-whisper}"
    rounded: "{rounded.none}"
    padding: "6px 18px"
  tab-button-active:
    backgroundColor: "{colors.backstage-panel}"
    textColor: "{colors.script-ink}"
  next-hero:
    textColor: "{colors.script-ink}"
    typography: "{typography.headline}"
    padding: "0"
  step-chip:
    backgroundColor: "{colors.stage-dark}"
    textColor: "{colors.stage-whisper}"
    rounded: "{rounded.pill}"
    padding: "6px 14px"
  kanban-card:
    backgroundColor: "{colors.stage-dark}"
    textColor: "{colors.script-ink}"
    rounded: "{rounded.sm}"
    padding: "6px 8px"
  merger-chip:
    backgroundColor: "{colors.stage-dark}"
    textColor: "{colors.stage-whisper}"
    rounded: "14px"
    padding: "3px 10px"
  book-card:
    backgroundColor: "{colors.backstage-panel}"
    textColor: "{colors.script-ink}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
---

# Design System: Vault 대시보드

## 1. Overview

**Creative North Star: "무대 뒤 작업실"**

공연 전, 객석의 불이 꺼진 극장의 무대 뒤. 대본 더미와 소품 상자, 벽에 붙은 큐시트, 그리고 작업등 하나. 이 대시보드는 극작가가 자기 작업의 무대 뒤를 둘러보는 화면이다 — 관객에게 보여주는 무대(완성된 희곡)가 아니라, 그것을 준비하는 어두운 뒷공간. 그래서 배경은 "다크 모드"가 아니라 **객석 소등**이고, 강조색은 "액센트 컬러"가 아니라 **핀스포트 불빛**이다. 빛은 귀하고, 귀해서 의미가 있다.

이 시스템이 명시적으로 거부하는 것: SaaS 관리자 패널(카드 그리드 + KPI 숫자 + 그라데이션), 생산성 앱의 할 일 압박(체크박스·진행률 게이지·"오늘의 목표"), 차가운 개발자 툴(터미널 미학·모노스페이스 도배·네온). 이 화면의 데이터는 지표가 아니라 **원고 더미**이며, 숫자는 성과가 아니라 서가의 두께다.

**Key Characteristics:**
- 객석 소등 위의 정갈한 원고 카드 — 완전 평면, 잉크와 괘선의 세계
- 핀스포트 하나: 앰버는 유망★와 '다음 할 일'에만 닿는다
- 한국어 활자 존중: `word-break: keep-all`, 숫자는 `tabular-nums`
- 재촉하지 않는 화면: 경고색은 파서가 실제로 깨졌을 때만 등장

## 2. Colors

객석이 꺼진 어둠 속, 무대 조명의 언어로 명명된 절제(Restrained) 팔레트 — 앰버 한 줄기가 화면의 10% 이하를 비춘다.

### Primary
- **핀스포트 앰버** (#d4a73f): 무대 위 단 한 사람을 비추는 빛. 한 화면에서 정확히 세 곳에만 닿는다 — ① '오늘의 한 걸음' 라벨, ② 무대 근처(조립·개작) 원고의 ★, ③ 키보드 포커스 링(일시적). 그 외 모든 ★는 무대 속삭임 톤이다. 채도를 낮춘 앰버라 다크 배경에서 쏘지 않는다.

### Secondary
- **비상구 초록** (#4f9d69): 극장 어둠 속에서도 항상 켜져 있는 표지. 완료된 단계, 채점된 분량, 파생 흐름 막대 — "여기까지는 안전하게 왔다"의 색.

### Tertiary
- **큐 옐로** (#e0b64a): 큐시트의 형광펜. 운반체 미정 등 "결정이 필요함" 표시 전용.
- **방화막 레드** (#c05b4d): 무대 화재 커튼. 파서 파손(unparsed ≥ 10) 배너 단 하나의 용도. 이 색이 보이면 진짜 사고다.

### Neutral
- **객석 소등** (#14161a): 몸통 배경. 불 꺼진 객석의 어둠 — 검정이 아니라 어둠.
- **무대 뒤 패널** (#1d2026): 원고 카드·패널의 면. 배경보다 반 단계 밝은, 작업등이 스치는 벽.
- **분필 괘선** (#2c3038): 1px 경계선 전용. 무대 바닥의 블로킹 분필 선.
- **원고 잉크** (#e6e6e3): 본문 텍스트. 어둠 위의 잉크 — 순백이 아니라 종이에 스민 흰색.
- **무대 속삭임** (#9aa0a8): 보조 텍스트(라벨·생성 시각·계열 태그). 어둠 속 낮춘 목소리.
- **먼지** (#6b7280): 비활성·미채굴의 회색. 짧은 표식 전용 — 문장 단위 텍스트에는 금지(대비 부족).

### Named Rules
**핀스포트 규칙.** 앰버는 한 화면에서 시선이 처음 가야 할 곳에만 닿는다 — 유망★와 '다음 할 일'. 화면의 10%를 넘는 순간 스포트라이트가 아니라 조명 사고다.
**방화막 규칙.** 방화막 레드는 시스템 고장(파서 파손) 단 하나의 신호다. 데이터가 많다/적다/늦었다 같은 상태에 빨강을 쓰는 것은 금지 — 이 화면은 재촉하지 않는다.

## 3. Typography

**Display Font:** 없음 — 도구 화면이므로 디스플레이 급은 쓰지 않는다
**Body Font:** Pretendard Variable (폴백: Pretendard → Malgun Gothic → Apple SD Gothic Neo → sans-serif)
**Label/Mono Font:** 별도 없음 — 모노스페이스는 이 시스템에서 금지 자산

**Character:** 단일 가족, 무게와 크기의 대비로만 위계를 만든다. 한국어 원고의 화면이므로 활자는 조용하고 정확해야 한다 — 꾸밈은 없고, 끊김도 없다.

### Hierarchy
- **Headline** (700, 20px, 1.4): 페이지 제목 "Vault 대시보드" 단 한 곳.
- **Title** (600, 16px, 1.45, 무대 속삭임 색): 섹션 제목(사이클 진행도·집필 파이프라인·계열별 현황). 밝기가 아니라 위치와 여백으로 구획한다.
- **Body** (400, 15px, 1.55): 본문·카드 제목·표 셀. 최대 행길이는 컨테이너(max-width 1200px) 안의 컬럼이 관리한다.
- **Label** (400, 13px, 무대 속삭임 색): 계열 태그, 생성 시각, 배치 라벨, 집계 수치.

### Named Rules
**원고 존중 규칙.** 모든 한국어 텍스트는 `word-break: keep-all` — 어절 중간에서 꺾인 제목은 원고에 대한 무례다. 수치 열은 `font-variant-numeric: tabular-nums`로 자릿수를 정렬한다.

## 4. Elevation

**그림자는 전면 금지.** 이 시스템의 깊이는 종이의 깊이다: 객석 소등(#14161a) 위에 무대 뒤 패널(#1d2026)이 반 단계 떠 있고, 그 경계를 분필 괘선(#2c3038) 1px이 긋는다. 인쇄물이 그림자 없이 위계를 만들듯, 면의 명도차와 괘선만으로 층을 표현한다. 호버·포커스에서도 글로우나 그림자를 켜지 않는다 — 상태 변화는 괘선 색이나 잉크 명도의 변화로 말한다.

### Named Rules
**잉크와 괘선 규칙.** `box-shadow`는 이 코드베이스에 존재하지 않는다. 깊이가 필요하면 면 색차(객석 소등 → 무대 뒤 패널)를 쓰고, 구분이 필요하면 1px 분필 괘선을 긋는다. 예외 없음.

## 5. Components

모든 컴포넌트의 성격: **정갈한 원고 카드** — 모서리는 거의 없고(0~6px), 괘선은 명확하고, 여백은 넉넉하다. 정리된 원고 더미의 질서.

### Buttons
- **Shape:** 직각 (0px) — 탭 버튼은 원고 파일의 견출지처럼 각져 있다
- **Primary (탭):** 무대 뒤 패널 배경 + 무대 속삭임 텍스트, 6px 18px 패딩, 1px 분필 괘선
- **Active:** 텍스트가 원고 잉크로 밝아지고 괘선이 무대 속삭임(#9aa0a8)으로 — 앰버는 탭에 쓰지 않는다(핀스포트는 세 곳뿐)
- **Hover:** 괘선이 밝은 분필(#454b55)로. 글로우 금지(잉크와 괘선 규칙)
- **Focus:** `:focus-visible`에서 1px 핀스포트 앰버 아웃라인, offset 2px — 계약의 유일한 일시적 앰버

### Chips
- **스텝 칩 (사이클 단계):** 알약형(20px), 투명 배경 + 분필 괘선, 무대 속삭임 텍스트. 완료 시 괘선이 비상구 초록, 텍스트가 원고 잉크로.
- **병합 칩 (A~L):** 14px 알약, 분필 괘선, 13px 무대 속삭임 텍스트, `title` 툴팁으로 다음 행동 노출.

### Cards / Containers
- **Corner Style:** 6px (패널·서가 카드) / 4px (칸반 카드 — 더 작은 단위는 더 각지게)
- **Background:** 무대 뒤 패널; 칸반 카드는 열 안에서 역전되어 객석 소등 배경(패널 위의 어둠)
- **Shadow Strategy:** 없음 — Elevation 참조
- **Border:** 1px 분필 괘선, 전 방향 균일 (한쪽 측면 스트라이프 금지)
- **Internal Padding:** 10px 12px (카드) / 8px (칸반 열)
- **미채굴 상태:** 서가에서 파생 글감 0인 책은 제목을 무대 속삭임 톤으로 + "아직 채굴 전" 한 줄 — opacity 감산은 대비 미달을 낳으므로 금지

### Inputs / Fields
현재 입력 요소 없음 (읽기 전용 대시보드). 추가 시 이 시스템의 규칙을 따를 것: 직각~4px, 분필 괘선, 포커스는 괘선의 앰버 전환.

### Navigation
- 상단 헤더 한 줄: 제목(Headline) + 생성 시각(Label) + 탭 버튼 2개. 탭 전환이 유일한 내비게이션.
- 접이식 `<details>`가 보조 동선: "미채점 N편 보기", "잠자는 계열 N개 더 보기" — 서랍은 열기 전까지 조용하다.

### 문장 서가 (Signature Component)
이 시스템 고유의 데이터 표현: **차트가 아니라 문장이 지표를 말한다.**
- **오늘의 한 걸음:** 앰버 라벨 한 줄 + 22px 문장형 히어로. 화면이 존재하는 이유가 첫 시선에 온다.
- **서가 문장:** "지금까지 N편을 읽었고, 서가에는 새 원고 M편이 쌓여 있습니다." — 미채점은 결손(빈 도넛)이 아니라 쌓여가는 원고 더미(자산)로 말한다. 상세는 `<details>` 서랍.
- **흐름 막대:** `width: N%` 단일 div, 비상구 초록. 책→창작 파생량 — 유일하게 허용된 그림 지표.
- **금지된 문법:** 커버리지 도넛, 배치별 스택 바 등 처리량 회고 차트는 이 화면에서 제거되었다(2026-07-04 크리틱). 사용자가 물을 수 없는 숫자(배치 번호)는 그리지 않는다.

## 6. Do's and Don'ts

### Do:
- **Do** 앰버를 아껴라 — 핀스포트 규칙 실행 명세: 한 화면에 정확히 세 곳(오늘의 한 걸음 라벨 / 조립·개작 ★ / 포커스 링). 나머지 ★는 전부 무대 속삭임 톤 (#9aa0a8).
- **Do** 모든 한국어에 `word-break: keep-all`, 모든 수치 열에 `tabular-nums`.
- **Do** 깊이는 면 색차(#14161a → #1d2026)와 1px 괘선(#2c3038)으로만.
- **Do** 본문 대비 4.5:1 이상 유지 — 먼지(#6b7280)는 짧은 표식 전용, 문장에는 원고 잉크나 무대 속삭임.
- **Do** 빈 상태에도 문장을 — "비어 있음", "전부 채점 완료 ✓", "데이터 없음 — 갱신.bat을 실행하세요". 침묵하되 무뚝뚝하지 않게.
- **Do** `prefers-reduced-motion: reduce`에서 모든 전환을 즉시 전환으로.

### Don't:
- **Don't** "SaaS 관리자 패널"이 되지 마라 (PRODUCT.md 안티레퍼런스): 큰 숫자 KPI 히어로, 그라데이션 액센트, 동일 카드 무한 그리드 금지.
- **Don't** "생산성 앱 느낌"을 들이지 마라: 체크박스, 진행률 게이지, 스트릭·배지·"오늘의 목표" 금지. 이 화면은 재촉하지 않는다.
- **Don't** "차가운 개발자 툴"로 기울지 마라: 모노스페이스 도배, 터미널 초록, 네온 하이라이트 금지.
- **Don't** `box-shadow`, 글래스모피즘, 그라데이션 텍스트 — 잉크와 괘선 규칙 위반.
- **Don't** 1px 초과의 한쪽 측면 컬러 스트라이프(`border-left` 액센트) — 괘선은 전 방향이다.
- **Don't** 방화막 레드를 상태 표시에 쓰지 마라 — 파서 파손 배너 단 하나의 용도.
- **Don't** 데이터를 이기는 그래픽 — 차트는 CSS로 그린 조명이지, 화면의 주인공이 아니다 (PRODUCT.md: "기록은 이미 아름답다").
