# Korean Google News RSS seed-harvest route

Use this as a lightweight public-source lane when the user asks for open-ended Korean play seed harvesting and no specific source is given.

## Query pattern

Use Google News RSS search URLs with Korean UI parameters:

```text
https://news.google.com/rss/search?q=<urlencoded query>&hl=ko&gl=KR&ceid=KR:ko
```

Run several stageability-oriented queries rather than one broad topical query. Good query clusters:

- `2026 민원 시스템 오류 접수 지연`
- `2026 무인민원발급기 오류`
- `2026 주민센터 신청 첫날 혼란`
- `2026 자격 확인 서류 누락 반려`
- `2026 콜센터 AI 상담 자동응답 민원`
- `2026 공항 출입국 키오스크 오류 대기`
- `2026 요양원 면회 예약 오류`
- `2026 번호표 대기 민원실 혼란`

Bias toward procedure/state words: `신청`, `접수`, `반려`, `대기`, `확인`, `예약`, `오류`, `무인`, `키오스크`, `번호표`, `대상`, `이의신청`, `업무지연`, `일부 서비스 가능`.

## Filtering lesson from 2026-07-10 run

A good first pass is: collect 10-60 RSS items, dedupe by title stem, then score only for stageability. Do not rank by national importance.

Strong candidate shapes found:

- partial public-system recovery: `납부 가능 / 확인 불가 / 일부 서비스만 가능`
- administrative-name change + kiosk failure: celebration signage beside `발급 불가`
- subsidy application first day: `대상 아님`, `이의신청`, second queue
- AI call-center summary: machine-generated record arrives before human listening
- automated border gates: repeated body correction, `얼굴을 다시 올려 주세요`

## Provenance caveat

Google News RSS item links may be Google redirect/article URLs rather than canonical article URLs. For quick inbox cards this is acceptable if labeled as `Google News RSS`; for higher-confidence expansion, resolve/read the original article before making detailed factual claims.

## Obsidian save pattern

For an optional Vault layout, a possible relative output path is:

```text
wiki/writing/notes/글감_채집_YYYY-MM-DD.md
```

Recommended note structure:

1. YAML: `type: seed-harvest`, `status: inbox`, date, source RSS URLs, related writing/aesthetic notes.
2. `수집 메모`: timestamp, source route, stageability criteria, provenance caveat.
3. `1차 후보 풀`: table with final/hold, title, source, date, why kept.
4. 3-7 seed cards in the skill's standard format.
5. `오늘의 판정`: strongest candidates, holds, next expansion options.

Update `index.md` and append `log.md` only when the user expects the vault to be maintained end-to-end.