# Korean blog/community seed-harvest pattern

Use this reference when extending a news-based 희곡 글감 harvest into public Korean blogs, Naver View, cafés, or community search results.

## Source lanes

- Start with public search queries that combine the existing card's procedure/object words with lived-experience words: `후기`, `안됨`, `대기`, `번호표`, `지문`, `챗봇`, `상담원 연결`, `이의신청`, `주민센터`, `무인민원발급기`, `정부24`.
- Naver mobile blog URLs (`https://m.blog.naver.com/<blogId>/<logNo>`) are often more extractable than desktop `blog.naver.com` URLs. If a desktop Naver blog extraction returns empty, retry the mobile URL before giving up.
- Bing/Google RSS may be noisy for blog/community searches. Treat it as discovery only; verify any final source by reading the accessible public page.
- Naver café/community results often expose only titles/snippets unless logged in. Do not reproduce private or login-walled content. Record only source-lane potential and extract structures, not personal stories.

## What to harvest from blogs vs news

News often gives official phrases and institutional state: `일부 서비스 가능`, `기한 연장`, `출범 첫날`, `대상자 아님`.

Blogs/community posts are better for embodied procedural material:

- hands failing fingerprint recognition;
- unexpected places where a public procedure appears, e.g. bank, mart, subway station, apartment office;
- small conditions like `24시간 연중무휴` beside `주말·공휴일 발급 중단`;
- payment quirks: cash only, thousand-won bills, free vs paid documents;
- USB/PDF/print/fax loops;
- `전송완료` vs actual arrival confirmation;
- fallback human windows such as `10·11번 창구`;
- delayed recognition with unchanged deadline, e.g. `사용 기한은 동일합니다`.

## Ethical boundary

- Public institutional blogs and official 안내 posts can be cited as sources for procedures and phrases.
- Personal blog details should be transformed into structure/object/action, not copied as a character biography.
- Login/가입-walled café posts: do not cite or paraphrase unseen bodies. Use them only to note that a source lane may be worth manually checking later.
- Avoid turning community complaints into gossip. Extract stageable mechanisms: 접수번호, 기준일, 본인확인, 상담원 연결 실패, 지연 문자, 재등록, 수신 확인.

## Output shape

For each accessible source, preserve title/source/date/URL and then write:

1. `채집 데이터` — factual procedural details only.
2. `희곡적으로 건질 것` — one compact mechanism, not a summary.
3. `구체소재` — objects/sounds/status values.
4. `대사 조각` — official or quasi-official sentences that can recur.

For inaccessible community lanes, write a short `커뮤니티/카페 레인 관찰` table with columns: lane, visible space, possible dramatic pressure, access boundary.

## Promotion pattern

When blog/community harvest extends an already promoted candidate map:

- Add the blog/community note as a source in the candidate map.
- Add only the strongest new materials to `쓸 리서치 부품` and `구체소재 표`; do not bloat the plot with every source detail.
- Prefer materials that deepen the existing engine. Example: for an administrative lobby play, `USB 출력`, `팩스 전송완료`, `수신 확인 전화`, and `10·11번 창구` extend the chain from 발급 failure to 처리/도착 ambiguity.
- If a new material has its own engine, leave it as a separate card rather than forcing it into the promoted play. Examples: `오직 지문입니다`, `사용 기한은 동일합니다`.
