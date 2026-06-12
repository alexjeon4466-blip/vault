# 적용 방법

아래 파일들을 Obsidian vault의 최상위 폴더에 넣으세요.

- `AGENTS.md`: Codex와 공통 에이전트 규칙
- `CLAUDE.md`: Claude Code용 진입 파일. 내부에서 `AGENTS.md`를 import함
- `LLM_WIKI_PLAYBOOK.md`: 상세 작업 템플릿과 프롬프트
- `index.md`: 위키 지도. 이미 있으면 덮어쓰지 말고 내용을 병합
- `log.md`: 작업 일지. 이미 있으면 덮어쓰지 말고 내용을 병합

처음에는 기존 파일을 옮기지 말고, AI에게 다음 요청만 하세요.

```text
AGENTS.md와 CLAUDE.md의 규칙을 읽고, 이 vault의 구조만 스캔해 주세요.
아직 파일 생성/수정/삭제/이름 변경은 하지 마세요.
```
