---
type: project-checkpoint
status: draft
created: "2026-07-01"
updated: "2026-07-02"
visibility: private
project: "Bookcut Zero"
sources:
  - "C:/Users/LOQ/bookclub-media/docs/bookcut-detailed-design-v0.2.md"
  - "C:/Users/LOQ/bookclub-media/tools/bookcut-zero/"
---

# Bookcut Zero 체크포인트 — 2026-07-01

## 한 줄 상태

Bookcut은 오늘 **Audacity 실사용 → 전사 기반 컷 편집기 아이디어 → 상세 설계 v0.2.1 → Bookcut Zero UX spike 구현 확인**까지 진행했다. 현재는 Tauri 풀앱 착수 전, **대안 B: 전사 보며 컷 찍는 로컬 웹 프로토타입**이 실제로 동작하는지 검증하는 단계다.

---

## 현재 핵심 경로

- 설계서
  - `C:/Users/LOQ/bookclub-media/docs/bookcut-detailed-design-v0.2.md`
- 테스트버전 / UX spike
  - `C:/Users/LOQ/bookclub-media/tools/bookcut-zero/`
- Obsidian 체크포인트
  - `wiki/projects/bookcut/2026-07-01_Bookcut_Zero_체크포인트.md`

---

## 오늘 확정한 제품 방향

### Bookcut의 목적

Bookcut은 Audacity 전체 대체가 아니다. 목적은 더 좁다.

> 긴 북클럽/대화 녹음에서 **전사 텍스트를 보며 구간을 선택하고, Audacity의 C 기능처럼 컷 미리듣기한 뒤, 괜찮으면 CUT 라벨을 붙이고, 최종적으로 CUT 삭제본을 export**하는 도구.

### 핵심 UX

1. 전사 단어/문장 또는 타임라인에서 구간 선택
2. `C`로 cut preview
   - 선택 시작 전 여유 구간 재생
   - 선택 구간 스킵
   - 선택 끝 뒤 여유 구간 재생
3. 자연스러우면 `X` 또는 Enter로 `CUT` 라벨 확정
4. Edited playback에서는 `CUT` 구간 자동 스킵
5. Export에서는 `CUT` 구간 실제 삭제 + loudness normalization

---

## 설계 상태

`bookcut-detailed-design-v0.2.md`는 현재 **v0.2.1 보정판** 상태다.

### v0.2.1에서 반영된 주요 보정

- R1 WAV proxy 용량 정정
  - 1h mono s16 WAV: 약 `320–350MB`
  - 2h mono s16 WAV: 약 `640–700MB`
  - stereo는 ×2
  - Drive sync 부담을 명시
- R2 proxy/import 성능 목표 정합화
  - 60분 proxy 생성 `<60s` 목표
  - hard budget `<3분`
  - import 전체 예산 별도
- R3 truePeak 분리
  - `targetTruePeak: -1.5`
  - `acceptanceTruePeak: -1.0`
  - 안전 마진으로 설명
- R4 CUT gap 현실화
  - hard fail은 `CUT leak ≤30ms`
  - gap은 MVP median `<100ms`, v1 목표 `20–50ms`
- R5 실행 3계층 도입
  - Prototype Gate
  - Tauri MVP
  - Full v1
- R6 export crossfade 비용 리스크 보정
  - pairwise ffmpeg acrossfade의 O(N²) 위험
  - MVP 권장 경로를 Rust streaming PCM stitcher로 상향
- R7 review preset 추상화
  - `review_audio`: m4a 기본, mp3 optional
- R8 peaks escape hatch
  - MVP는 단일 mip 먼저
  - 성능 미달 시 `.bkpk` 멀티밉 확장
- R9 ClovaNote 샘플 6종 확보를 Phase 0 gate로 명시

### 아직 설계서에 남은 정리 포인트

다음에 문서 수정 시 우선순위:

1. §11.2 pseudocode를 pairwise ffmpeg acrossfade 중심에서 **streaming PCM stitcher 중심**으로 완전히 정리
2. §15.0의 “2-pass 정밀화 제외”와 §11.4의 “2-pass MVP 기본” 문구 모순 정리
   - 추천: Tauri MVP에 2-pass loudnorm 포함
   - Full v1은 measured caching / album normalization / resume 최적화까지
3. 서장 대안 B의 “1~2h 브라우저 decode 가능” 표현 완화
   - 대안 B는 UX 검증용이지, 대용량 브라우저-only 기술 검증이 아님
4. §2.1의 “멀티해상도 peaks”를 “MVP 단일 mip, 필요 시 멀티”로 수정
5. 선택 사항
   - `breathingGapMs=120` 기본값을 0 또는 옵션으로 낮추기
   - seek/mapping 측정을 파일 레벨과 WebView 재생 레벨로 분리

---

## Bookcut Zero 구현 확인

테스트버전 위치:

```text
C:/Users/LOQ/bookclub-media/tools/bookcut-zero/
```

### 확인된 파일

- `package.json`
- `vite.config.js`
- `src/App.jsx`
- `src/Timeline.jsx`
- `src/parseTranscript.js`
- `src/styles.css`
- `public/data/meta.json`
- `public/data/aligned.json`
- `public/data/audio.mp3`
- `dist/index.html`

### 현재 성격

Bookcut Zero는 아직 Bookcut 앱 전체가 아니라:

> **대안 B 검증 프로토타입 — 전사 보며 컷 찍어 EDL 생성**

이다.

### 실제 검증 결과

실행한 빌드:

```bash
npm run build
```

결과:

```text
vite v6.4.3 building for production...
✓ 29 modules transformed.
✓ built in 618ms
```

브라우저 확인:

```text
http://127.0.0.1:5173
```

로드 확인:

- 제목: `Bookcut Zero — 전사 보며 컷`
- 오디오 길이: 약 `01:04:50`
- 전사 rows: `225개`
- 단어 span: `6668개`
- `aligned.json` 기반 단어 정렬 모드 표시
- transcript panel / sidebar / timeline 표시
- console error 없음

간단 smoke:

- timeline 드래그 선택 가능
- `X` 키로 `CUT` mark 추가 가능
- CUT 합계 / 예상 결과 길이 업데이트됨
- EDL 내보내기 버튼 활성화됨

---

## Bookcut Zero 현재 기능

### 구현됨

- React/Vite 웹앱
- audio 재생
- `aligned.json` 단어 정렬 전사 표시
- 단어 단위 선택
- shift 선택
- 현재 active word 표시
- CUT에 포함된 단어 취소선 표시
- 타임라인 표시
  - 발화 block
  - 빈틈
  - marks
  - selection
  - playhead
- `C` cut preview
- `X` CUT
- `K` KEEP
- `L` CLIP
- Edited playback에서 CUT skip
- EDL markdown export

### 아직 없음

- localStorage / project 저장
- JSON export/import
- 실제 audio export
- waveform/peaks
- Tauri/Rust/ffmpeg
- loudnorm
- microfade / WebAudio GainNode
- minKeepMs 병합 규칙
- 정식 ClovaNote adapter

---

## 다음 작업 우선순위

### 1순위 — Bookcut Zero v0.0.2

Tauri로 바로 가지 말고, 현재 UX spike를 실사용 가능한 정도로만 보강한다.

1. localStorage autosave
   - marks
   - notes
   - edited mode
   - pad/rate
2. project JSON export/import
   - `bookcut-zero-project.json`
   - EDL과 별도로 다시 불러올 수 있는 기계 판독 저장본
3. `CHECK` 라벨 추가
   - 현재 `KEEP`보다 실사용성이 높을 가능성
   - 추천 라벨: `CUT`, `CHECK`, `CLIP`
4. mark row별 `C preview` 버튼 추가
   - 목록에서 특정 mark를 바로 미리듣기
5. 실제 북클럽 10~20분을 Bookcut Zero로 컷해 보고 Audacity 대비 체감 비교

### 2순위 — 설계서 v0.2.2 보정

- §11.2 streaming PCM stitcher 중심 정리
- 2-pass loudnorm MVP 범위 문구 정합화
- 대안 B 브라우저 decode 표현 완화
- peaks 단일 mip 표현 정합화

### 3순위 — Tauri 여부 판단

Bookcut Zero로 실제 파일 10~20분 컷을 해본 뒤 판단한다.

판단 질문:

- 전사를 보며 컷 찍는 게 Audacity보다 빠른가?
- `C` preview → `CUT` 라벨 workflow가 덜 피곤한가?
- Edited playback이 컷 검수에 충분히 도움 되는가?
- EDL 기반으로 Audacity 편집을 보조하는 것만으로도 충분한가?
- 그래도 로컬 앱/Tauri가 필요하다고 느끼는가?

---

## 현재 결론

Bookcut Zero는 **성공적인 UX spike 초안**이다. 빌드와 브라우저 로드는 확인됐다. 다만 아직 완성 앱이 아니라, 다음 질문을 검증하기 위한 도구다.

> 실제 1시간 북클럽 파일에서 전사 보며 CUT 찍는 것이 Audacity보다 빠르고 덜 피곤한가?

다음 세션은 `C:/Users/LOQ/bookclub-media/tools/bookcut-zero/`에서 시작하면 된다.
