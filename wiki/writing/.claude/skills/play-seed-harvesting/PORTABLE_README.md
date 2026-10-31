# Play Seed Harvesting — 배포용 사본

**버전: 1.8.0-portable.1 · 기반 스킬: 1.8.0**

공개 출처에서 희곡 글감을 채집하고, 원문 근거·연극적 잔여·취급 위험을 분리하여 검토하는 에이전트용 스킬입니다. 글감 선택 전에는 형식·분량·집필을 강제하지 않으며, A0 채집과 A1 판정은 별도 승인 단계입니다.

## 무엇이 들어 있나

- `SKILL.md`: 채집·검증·선택·접근 조건 고정 규칙.
- `references/`: 한국·일본 공개커뮤니티, 뉴스/RSS, 재개, A1 판정·평가, 서비스 검증의 세부 지침.
- `scripts/`: 문서/A1 구조 검증기, Scrapy 기반 파서 구성요소와 합성 회귀 테스트.
- `templates/`: 받는 사람의 채집 계약·극작 맥락 입력 양식.
- `MANIFEST.json`: 배포 파일별 SHA-256. 자기 자신은 해시 목록에서 제외합니다.
- `VERIFICATION.md`: 이 배포본에 실제 실행한 검증 결과와 미검증 범위.

원 저자의 Vault, 원문 채집 데이터, 개인 작업물·심사 기록, 쿠키·인증정보, 브라우저 프로파일, 배치 전용 수집기, Python 환경은 들어 있지 않습니다. 테스트 안의 URL은 합성 파서 입력이며 실제 수집 대상이나 성공 영수증이 아닙니다.

## 중요한 기능 한계

**이 ZIP은 클릭 한 번으로 모든 사이트를 수집하는 완제품이 아닙니다.**

`public-community-spider.py`는 목록/본문 파서와 인자 검사를 갖추었지만 `start()`가 요청을 생성하지 않습니다. 요청 스케줄링·회계/영수증 저장·기간 필터·재개를 구현한 완성 크롤러로 사용하면 안 됩니다. `runspider`의 종료 코드 0은 채집 성공을 뜻하지 않습니다. 일본 사이트의 배치 수집 코드도 포함하지 않습니다. 현재 지침은 에이전트가 사용할 수 있는 웹 도구로 실행할 수 있지만, 각 도구의 실제 기능과 승인된 사이트·본문 경계를 지켜야 합니다.

오프라인 테스트 통과는 파서/스키마 회귀 확인입니다. 현재 사이트 접근, 실제 글감 수율, A1 의미 판정 정확도, 전체 자동화의 작동을 증명하지 않습니다.

## 설치: Hermes

1. ZIP을 임의 폴더에 풉니다. 안쪽의 **`play-seed-harvesting/` 전체**가 설치 단위입니다. `SKILL.md`만 복사하지 마세요.
2. 사용할 Hermes 프로파일의 실제 홈을 확인합니다. 환경변수 `HERMES_HOME`이 있으면 그 경로의 `skills/`를 사용합니다. 기본 경로나 다른 프로파일이라고 추정하지 마세요.
3. 대상 `skills/` 아래에 `play-seed-harvesting/`를 놓습니다. 같은 이름의 스킬이 이미 있으면 덮어쓰지 말고 백업·비교 병합 또는 별도 시험 프로파일을 사용합니다.
4. 새 세션에서 `play-seed-harvesting 스킬을 읽고 버전과 사용 가능한 기능을 알려줘`라고 요청합니다. 도구가 읽은 실제 버전이 `1.8.0-portable.1`인지 확인합니다.
5. `templates/collection-contract.md`와 `templates/writing-context.md`를 자신의 작업 폴더로 복사해 채웁니다. 템플릿 자체는 승인 기록이 아닙니다.

Hermes 설치·모델·도구 사용료와 API 키는 수신자가 별도로 준비합니다. 이 스킬은 키를 포함하거나 설정하지 않습니다. 다른 에이전트에서는 같은 문서를 사용할 수 있지만 Hermes 도구 호출을 해당 환경에 맞춰야 합니다.

공식 문서: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

## 첫 사용 요청 예시

> play-seed-harvesting를 읽어줘. 첨부한 채집 계약과 극작 맥락을 기준으로 먼저 필수 누락 사항만 확인해줘. 확인 후 승인된 공개 출처만 A0로 채집하고, 근거와 연극적 잔여 및 취급 위험을 나눠 보여줘. A1·집필·외부 게시·Git 변경은 아직 하지 마.

이미 승인된 계약이 있으면 재확인을 이유로 더 엄격한 중단 조건·작은 예산·추가 필터를 만들지 않습니다. 실제 접근 제한 변화만 정확한 URL/UA/규칙/상태/시각과 함께 처리합니다. 다른 봇 이름의 제한을 수집기에 확대 적용하지 않습니다.

## 실행 환경과 오프라인 테스트

Python 3.10+가 필요합니다. 이 배포본의 실제 검증 환경은 `VERIFICATION.md`에 기록합니다. 구조 검증기는 Python 표준 라이브러리만 사용합니다. 아래 명령은 압축을 푼 `play-seed-harvesting` 폴더에서 실행합니다. 시스템에 따라 `python`을 Python 3 실행명으로 바꾸세요.

```bash
python -B scripts/test-verify-public-community-a1.py
python -B scripts/test-verify-public-community-note.py
python -B scripts/verify-community-harvest-structure.py --help
```

Scrapy 파서 테스트만 추가 의존성이 필요합니다. `uv`가 있다면 격리 환경에서 실행할 수 있습니다(패키지 다운로드는 네트워크를 사용하지만 테스트 자체는 커뮤니티에 접속하지 않습니다).

```bash
uv run --no-project --with 'Scrapy==2.17.0' python -B scripts/test-public-community-spider.py
```

`uv`가 없으면 자신이 만든 가상환경에 `python -m pip install -r requirements-crawler.txt`를 실행한 뒤 같은 Python으로 `python -B scripts/test-public-community-spider.py`를 실행합니다. 전역 Python에 설치할 필요는 없습니다.

실제 산출물 구조 확인:

```bash
python scripts/verify-public-community-note.py "채집문서.md"
python scripts/verify-public-community-a1.py "승인된_비공개_작업경로/a1-package.json"
```

첫 검증기는 한국 커뮤니티 **카드 문서** 형식에 맞습니다. A0 종합표·일본 집계 문서·A1 사용자 열람 문서는 다른 계약이므로 같은 형식으로 위장해 통과시키지 마세요. A1 검증기 역시 실제 원문·의미적 지지·독립 심사를 대신하지 않습니다.

## 보존된 원칙과 배포 경계

- 승인된 접근 조건 고정, 에이전트의 임의 제한 추가 금지.
- `오늘`은 별도 지정이 없으면 실행 기준 최근 24시간. 정확한 시작/종료/시간대를 기록.
- 민감 주제 자체로 A0를 버리지 않고 연극적 잔여와 취급 위험을 분리.
- A1은 증거 고정 후 비식별 구조 심사와 출처 공개 계보 심사를 분리.
- 사용자용 A1 문서는 pass 외 상태도 전건 표시. 원문 재현 방식과 제한을 명시하며, source-hidden은 독립 심사용 경계일 뿐 사용자를 위한 원문 가림 규칙이 아님.
- 개인 작업실의 원문 열람과 외부 재배포는 다름. 이 스킬의 라이선스는 커뮤니티 원문이나 제3자 저작물에 대한 이용 허락이 아님.
- 이 ZIP 생성은 사이트 접속·사용자 원문 공유·GitHub 업로드·서비스 공개·결제·commit/push를 승인하거나 수행하지 않음.

세부 적응 내역은 `DISTRIBUTION.md`, 초기 설정과 선택적 연동은 `references/portable-setup.md`, 권리 표시는 `LICENSE`와 `THIRD_PARTY_NOTICES.md`를 읽으세요.
