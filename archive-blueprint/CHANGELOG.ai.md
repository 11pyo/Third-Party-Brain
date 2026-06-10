---
doc_type: ai_reference
topic: change_log
purpose: "아카이브의 프로그램·알고리즘·구조 변경 이력. 콘텐츠(아티클) 변경은 여기 기록하지 않음 — archive-structure.md 소관."
scope: "program | algorithm | structure | encoding | deployment 변경만"
last_updated: 2026-06-10
rule: "신규 항목은 맨 위. 형식 고정: 날짜 / 분류 / 변경 / 영향파일 / 이유. (B)분류 변경 시 MANDATORY SYNC에 따라 이 파일 + 해당 .ai/.human 문서 동시 갱신."
---

# CHANGELOG (프로그램·알고리즘·구조)

> 분류 태그: `[STRUCTURE]` 파일/구성 · `[ALGO]` 검색/인테이크 로직 · `[ENCODING]` 인코딩 · `[DEPLOY]` 실행/배포/공유 · `[DOC]` 블루프린트 문서.

## 2026-06-10
- `[ALGO]` **🚨 핸들 키 충돌 사고 + 수정 — 아카이브 저장이 대시보드 파일을 덮어씀.** 인시던트: 같은 폴더의 archive.html과 task-board.html 편집기가 IndexedDB(`tbfs/h`) **공용 키 `'f'`** 를 썼고, `file://` 페이지는 Chrome에서 **한 오리진으로 저장소를 공유** → 대시보드가 먼저 기억시킨 핸들을 아카이브 saveFile이 집어 **task-board.html에 아카이브 HTML을 기록**(2026-06-10 14:58·15:19 2회, "롤백" 증상의 진짜 원인). 복구: ① VSS 섀도카피(C: 06-10 00:00 스냅샷)에서 task-board.html(06-09 17:01 상태) 추출 → 그 후 적용분(💾저장 기능)을 하드닝 포함 재이식 → 렌더 12태스크·9문의 검증 ② 덮어쓴 사본에서 사용자의 아카이브 편집(1건)을 diff로 회수 적용 ③ 사고 사본은 `_clobbered_archive_copy_20260610.html`로 격리 보관. 수정(5파일 공통): **앱별 고유 핸들 키** `_FS_KEY`(`sap-archive`/`sap-board`/`tpb-archive`/`tpb-board`/`acd-board`) + **핸들 파일명 검증**(`h.name!==기대명 → 폐기·재선택`) + picker 직후 파일명 불일치 토스트. 기존 오염 핸들(구 키 `'f'`)은 새 키 미스로 자동 무효화.
  - 영향: 정본 archive.html·정본 task-board.html(섀도 복원+재이식), 공개 3종(`reference-implementation/archive/archive.html`·`reference-implementation/dashboard/task-board.html`·`(acd)/task-board.html` — 미러/단독 보드엔 스탬프·무침묵·라운드트립 하드닝도 이번에 함께 이식, localStorage 키 `tpb-board-saved-stamp`/`acd-board-saved-stamp`).
  - 검증: 내부 보드(12태스크·9문의·savef 게이팅·TASKS regex), 내부 아카이브(69아티클·회수 편집 반영), 공개 2보드(8/6카드·키·함수) — 전부 console 0 error.
  - 교훈(INV 후보): **여러 앱이 한 폴더에서 file://로 열리는 설계면 오리진 공유를 전제**하라 — IndexedDB/localStorage 키는 반드시 앱 네임스페이스, 파일 핸들은 사용 전 이름 검증.
- `[ALGO]` **💾저장 신뢰성 하드닝 — "저장했는데 새로고침하면 롤백" 차단.** 실사용 보고: 편집→💾저장→새로고침 시 편집분 소실. 조사 결과 원본 파일에 브라우저 기록 흔적 없음(쓰기가 원본에 도달 안 함 — 취소 무알림/타 위치 저장/비보안 주소 다운로드 폴백 등 어느 분기든 종전 코드는 침묵). 변경(아카이브 2종 공통): ① **저장 스탬프** — 저장본 `<html data-saved="sv-…">` + localStorage 쌍 기록, 로드 시 대조 → 불일치면 상단 경고 배너("마지막 저장이 이 파일에 반영 안 됨") + **[저장 위치 재선택]**(`_fsForget()`=IndexedDB 핸들 삭제→다음 저장 때 재선택) ② **무침묵 원칙** — AbortError(취소)도 ⚠토스트, 기타 실패는 에러명 토스트 후 다운로드 폴백 ③ **라운드트립 검증** — write 후 `getFile().size`를 기대 바이트와 대조 ④ 성공 토스트에 파일명 표시 ⑤ picker `id`+`startIn:'documents'`(위치 기억 개선) ⑥ 비보안 컨텍스트(`http://IP`)는 로드 시 💾버튼을 "💾 다운로드"로 재라벨(직접기록 API 부재 명시).
  - 영향: 정본(비공개) `archive.html` + `reference-implementation/archive/archive.html`(localStorage 키 `archive-saved-stamp`/`tpb-archive-saved-stamp`). 대시보드들은 추후 동일 패턴 이식 가능(미적용).
  - 검증: 헤드리스 — 스탬프 직렬화(`<html … data-saved>`), 불일치 배너 표시+버튼 2종 동작(재선택=핸들 삭제·닫기=스탬프 클리어), 스탬프 없음=배너 없음, `_fsForget` 정상, console 0 error (두 파일 모두).
  - 이유: 저장 실패가 조용히 지나가면 사용자는 "롤백"으로 인지 — 실패·불일치를 반드시 표면화.
- `[ALGO]` **편집 모드 perf 수정 — 일괄 contenteditable 토글 → 클릭 위임(delegation).** 종전 `toggleEdit`가 편집대상 전 요소(`_EDIT_SEL` 매칭, 정본 기준 4,787개)에 `contenteditable`을 일괄 set/remove → 토글당 헤드리스 250~360ms(실브라우저는 점선 outline 수천 개 페인트까지 추가) 렉. 변경: `toggleEdit`=body 클래스만 토글(off 시 잔여 속성 정리), **클릭한 요소만 그 순간** `contenteditable` 부여(document 클릭 위임 + `closest(_EDIT_SEL)`), `focusout`에서 회수, `caretRangeFromPoint`로 클릭 지점에 캐럿, 편집 중 본문 `<a>`는 `preventDefault`(이동 대신 편집). CSS는 `body.editing <대상>:hover` 점선 어포던스 추가(`[contenteditable="true"]` 규칙 유지). 아카이브 크기와 무관하게 O(1) — 페이지 분할 불필요 근거.
  - 영향: 정본(비공개) `archive.html` + `reference-implementation/archive/archive.html`(공개 샘플, 동일 패턴 — 복사해 큰 아카이브 만들면 같은 함정이라 함께 수정). `addArticle` 말미의 재토글 호출 제거(위임이라 불필요). 대시보드들은 편집 노드 수가 작아 미적용.
  - 검증: 헤드리스 preview(정본) — 토글 250~360ms→27~42ms(×3 반복), 클릭→해당 1개만 editable, blur 회수, off 후 잔여 0, add 정상, console 0 error. 공개 샘플 동일 통과.
  - 이유: 실사용 보고("편집모드 켜고 끌 때마다 렉이 장난이 아니다"). 단일 HTML 정본 원칙(INV1) 유지 — 렉 원인은 파일 크기가 아니라 토글 알고리즘.
- `[DOC]` **보조 노트 신설 — 범용 LLM‑위키 비교 + 2단 결합 모델.** `archive-blueprint/COMPARISON-llm-wiki.md`: 이 단일‑HTML 정본 아카이브 패턴 vs 범용 LLM‑위키(Karpathy LLM Wiki / 에이전트 `wiki` 스킬) — 공통 DNA·divergence·선택 기준 + **2단(scratch→canonical) 결합**(위키=값싼 스크래치, `archive-intake.py`=승격 게이트[NEW/UPDATE/CONFLICT/REVIEW], `archive.html`=정본, 승격 후 위키 카드 회수) + 카테고리 브리지. 번호 챕터 아님(.ai/.human 페어 없는 포지셔닝 보조).
  - 영향: `COMPARISON-llm-wiki.md`(신규), `00-INDEX.ai.md`(agent routing 7번 + version 1.7→1.8·last_updated)·`00-INDEX.human.md`(📎 포인터), `CHANGELOG.*`. 핵심 도구 로직 불변(신규 코드 0).
  - 이유: 사용자 질문 기록 + 범용 위키와 결합 방법 명문화.
- `[STRUCTURE]` **서버 없는 인-브라우저 편집(✏️) 추가** — `reference-implementation/archive/archive.html` + (별도 레포)대시보드 `task-board.html`. 편집모드(`contenteditable` 토글 + 새 글/태스크 추가 + 🗑삭제), **저장=File System Access API로 원본 파일 write-back**(`showSaveFilePicker`, 핸들 캐시), 미지원 시 `download` 폴백. 저장 직렬화는 `[data-noexport]`(편집 UI)·`#ai-toggle/#ai-panel`(서버주입분) 제거 + `contenteditable` 속성 제거 + `.hidden` 해제, 편집 스크립트/CSS는 **보존**(저장본도 재편집 가능). 대시보드는 `outerHTML` 직렬화 후 정규식 `/const TASKS = \[[\s\S]*?\n\];/`를 모델 JSON으로 1회 교체.
  - 영향: `reference-implementation/archive/archive.html`·`(ai-collab-dashboard)/task-board.html`(편집 CSS/UI/JS) + `reference-implementation/dashboard/task-board.html`(이 레포 미러 — 기존 `openEdit`/`overrides` 편집기에 **💾 파일에 저장** 버튼+`saveToFile()` 추가: `mergedTasks()` 베이크 후 `const TASKS=[…]` 리터럴 write-back / FS Access·download), `README.md`/`README.en.md`·`reference-implementation/archive/README.md`·`reference-implementation/dashboard/README.md`·`AGENTS.md`(✏️ 안내), `CHANGELOG.*`. 핵심 도구(`archive-server.py` 등) 로직은 불변. ※ 실무용(비공개) 대시보드에도 동일 `saveToFile()` 적용(미푸시).
  - 검증: preview 헤드리스 — 편집토글·add(아티클: 사이드바·카운트 갱신 / 태스크: TASKS 모델 갱신)·저장직렬화(`elementsWithContenteditableAttr=0`, TASKS 리터럴 1개로 교체, 편집본 반영, 편집 스크립트 보존) 통과, console 0 error.
  - 이유: 실사용 피드백(간단 수정을 클로드 없이) 수용. 서버리스·무의존 원칙(INV1) 유지 — `file://` 에서 동작.
  - 후속(같은 날): **파일 핸들 IndexedDB 영속**(`_fsOpen/_fsLoad/_fsStore` + `_pickFileHandle`) — 첫 선택 후 폴더 재탐색·재선택 없이 같은 파일에 저장(세션·재방문 모두). 4개 파일(아카이브·② 단독·③ 미러·① 실무용) 동일 적용. 실사용 피드백("덮어쓰기 거부감"·"파일위치 자동 네비") 수용: README에 **「덮어쓰기 안심 가이드」**(한/영) + 인앱 힌트 안심 문구 추가. **#savef 버튼은 변경 0건이면 `disabled`(수정 있을 때만 활성)** — `exp`/`rst`와 동일 게이팅(`renderBar`).
  - 후속(같은 날): **정본(비공개) `archive.html`에도 편집(✏️) 이식**(미푸시·로컬). 샘플 대비 차이 = **배지텍스트 ≠ cat-header텍스트**(예: badge `운영 매뉴얼` / header `운영 참조 매뉴얼`)라 `addArticle`이 헤더 매칭 불가 → **`_CATS` 매핑표**(`{cls,badge,hdr}` ×5: 기초/프로세스/기술/트러블/매뉴얼) 도입: 모달 select·badge span은 `badge`, 섹션·네비 삽입 매칭은 `hdr`(`.cat-header`/`.nav-cat-title`의 `textContent.includes(hdr)`). 저장 직렬화는 동일(서버주입 `#ai-toggle/#ai-panel` 제거 포함). 검증: 헤드리스 preview — 편집토글(`contenteditable` on/off 4787), add(매뉴얼 배지→"운영 참조 매뉴얼" 섹션 정확 삽입·cnt 11→12·네비 생성), 저장직렬화(`[contenteditable]`속성=0·`[data-noexport]` 제거·추가글·편집스크립트 보존), console 0 error.

## 2026-06-09
- `[STRUCTURE]` **아카이브 익명 동작본(참조 구현) 추가 + 루트 AI 온보딩 신설 + 문서 한/영 병기.** `reference-implementation/archive/`(`archive-server.py` BM25검색서버·`archive-intake.py`·`archive-menu.py` TUI·sample `archive.html` 9art/5cat·`archive-structure.md`·`requirements.txt`·`run-*.bat/sh`·`README.md`). 루트 `AGENTS.md`+`CLAUDE.md` 신설(새 세션 자동 온보딩=기능·룰·방향; Claude Code는 `CLAUDE.md` auto-load→`AGENTS.md` 유도). AI 협업 대시보드=**별도 전용 레포 `11pyo/ai-collab-dashboard`** 명시(이 repo 주콘텐츠=아카이브+AI협업). 신규 문서 KO+EN(`README.en.md` 추가).
  - 영향: `reference-implementation/archive/*`(신규), `reference-implementation/README.md`(신규), `AGENTS.md`·`CLAUDE.md`·`README.en.md`(신규), `README.md`("도구소스 미포함" 단서→"블루프린트+실행 구현 둘 다"로 정정·트리·대시보드 별도레포 명시), `00-INDEX.*`(ARTIFACT MAP에 archive 동작본·루트 온보딩 추가·version bump), `CHANGELOG.*`
  - 검증: 샘플 `archive.html` 9아티클 파싱·BM25 1순위 적중(매출취소→`proc-sales-cancel`/여신→`ts-credit-check`/결산→`month-end-closing`). 기계식 데니리스트 0건(허구 ZTSD0xx 샘플만 잔존, SAP 표준 명명규칙).
  - 이유: 사용자 지시 — 제3의뇌(아카이브)는 **기존 repo에 통합**(새 repo 금지), 새 AI 세션 자동 온보딩, 대시보드는 별도 레포 유지하되 표기, 문서 한/영.

- `[STRUCTURE]` **대시보드 익명 동작본(참조 구현) 추가** — `reference-implementation/dashboard/`(`task-board.html`·`inquiry-log.js`·`log-inquiry.py`·`tasks.md`·`README.md`). 블루프린트 최초의 실행 가능 산출물(기존=문서만). 프로그램 골격(CSS+렌더JS)은 사내 `task-board.html`에서 verbatim 추출, 데이터는 가상 샘플로 교체(빌드 스크립트 조립, 조립물 금지어 assert 가드).
  - 영향: `reference-implementation/dashboard/*`(신규), `README.md`(트리·"도구 소스 미포함" 단서에 대시보드 예외 명시), `00-INDEX.*`(agent routing·version 1.5→1.6), `07-*`(상단 동작본 포인터), `CHANGELOG.*`
  - 검증: 헤드리스 렌더(preview)로 3보드·4상태·3주기·id-병합 정상·console 0 error. 다관점 적대 감사(critical/warning 0)+데니리스트 0.
  - 이유: 챕터 07 설명을 '더블클릭 실행 예제'로 보강. 회사정보 0 원칙 유지(데이터=가상 샘플).

## 2026-06-08
- `[DOC]` **대시보드 운영 가이드 챕터 신설** — `07-dashboard-operating-guide.*`. 05-operational-layer(개념/INV-OL)의 실무 매뉴얼: ARTIFACTS 4(정본 `tasks.md`/화면 `task-board.html`/문의로그 `inquiry-log.js`/헬퍼 `log-inquiry.py`), BOARDS 3(일회성·정기·문의), HELPER CLI 계약(`--new`/`--id`/`--status`/`--done` + 필드스키마 + id-merge + OS락 동시성), RENDER 시맨틱(localStorage override + 변경분 export 역동기화), OPERATING RULES R1~R8, SANITIZATION/DENYLIST.
  - 영향: `07-*`(신규), `00-INDEX.*`(read_order·agent routing·ARTIFACT MAP에 운영레이어 산출물 4종·version 1.4→1.5), `README.md`(구조 트리)
  - 이유: 05는 운영레이어 *개념*만 → 일상 운용(대시보드 규칙·문의 CLI 사용법) 실무 문서 부재.
  - 공개 sanitize: 데이터파일(`tasks.md`/`inquiry-log.js`) 비공개(고객명·문서·금액·실명 포함), 구조·규칙·익명예시만. DENYLIST=회사/고객/사람명·커스텀코드·문서/금액/사번·연락처.

## 2026-06-05
- `[ALGO]` **검색 랭킹을 term-count → BM25(char-2gram)로 교체.** `search_relevant`의 스코어링(본문 +1 / 제목·태그 ×3)을 BM25Okapi 랭킹으로 교체. 서버 기동 시 `build_index()`가 각 아티클(제목+태그+본문)을 char-2gram 토큰화해 BM25 인덱스 1회 구축, 질의마다 `get_scores`로 top_n. 순수 랭킹 진입점 `rank_article_ids()` 신설(평가 스크립트가 직접 호출 → 배포본=평가본 동일 경로). **동의어 확장(expand_query)은 BM25 랭킹엔 미적용**(실측상 R@1 하락 — 흔한 코드 동의어가 무관 아티클을 끌어올림) → 패시지 추출·legacy fallback에서만 유지. extract_passage 발췌 로직·컨텍스트 포맷 불변. rank_bm25 미가용 시 기존 term-count 스코어링으로 graceful fallback(`_rank_legacy_scored`).
  - 영향: `archive-server.py`(build_index/_tok_char2/_doc_text/_rank_scored/rank_article_ids 신규, search_relevant 랭킹부 교체, rank_bm25 의존 추가), `03-algorithms-scaling.*`(A절·C표), `00-INDEX.*`(SCALING TRIGGERS·ARTIFACT MAP)
  - 이유: 구 스코어링은 IDF(흔한 코드 노이즈)·문서길이 정규화(긴 글 편향)가 없어 부정확. BM25가 정확히 이 둘을 보정.
  - 검증: 오프라인 검색평가(실아카이브 65문서·49질의 라벨셋) — 구 R@1 42.9%/R@3 63.3% → 신 R@1 81.6%/R@3 85.7%(MRR 0.857, ~1.3ms/q). dense(MiniLM-multi)는 이 코퍼스 부적합(R@1 12%). 컴파일·fallback(_bm25=None)·패시지추출 스모크 통과.
  - 계약 유지: `search_relevant(query)->[ctx]` 시그니처·컨텍스트 포맷(`[아티클: #id — title (cat)]\n{body}`)·아티클 id 불변 → 서버/프롬프트/자동스크롤·CORE INVARIANTS 무관.
- `[DOC]` **운영 레이어·자동화 챕터 2개 신설** — `05-operational-layer.*`(무서버 대시보드·충돌없는 append-only id-merge 로그·AI유지 조직맵, INV-OL1~4), `06-automation-and-ops-model.*`(자가갱신 잠긴 스프레드시트 생성기·read-structure/guide-prod 모델·cross-repo 업적적재·공개수준 계층).
  - 영향: `05-*`, `06-*`(신규), `00-INDEX.*`(read_order·agent instructions·아티클수 de-stale), `README.md`(구조 트리)
  - 이유: 블루프린트가 코어(HTML+도구3)만 커버 → 실제로 더 크게 자란 운영/자동화 레이어 누락. 공개 sanitize 후 일반 패턴 추가.
- `[DOC]` 커스텀 코드 식별자 일반화(공개 sanitize) + 아티클 수 하드코딩 de-stale(03·00-INDEX). 06-02 알고리즘 개선 push.

## 2026-06-02
- `[ALGO]` **검색 컨텍스트 발췌를 '글 맨 앞 1800자'→'키워드 매칭 위치 주변 발췌'로 변경.** `search_relevant`가 본문을 `[:1800]`(항상 글 머리)로 잘라 넘기던 것을 신설 `extract_passage()`로 교체 — 키워드 첫 매칭 위치(−400/+1600) 발췌 + 글 머리(제목/도입 300자) 동봉, 상한 ~2200자. 매칭이 머리(≤300자)면 앞에서부터(기존 동일). `make_pattern()`을 search_relevant 내부 중첩 → 모듈 레벨로 승격(extract_passage와 공유).
  - 영향: `archive-server.py`(extract_passage 신규, make_pattern 모듈화, search_relevant 본문 추출부)
  - 이유: 아티클이 길어지며(특히 ops-cts-procedure에 SR처리유형분기·테스트결과서양식·②변경필요 입력가이드 등 누적) **뒤쪽 최근 추가 내용이 검색에 걸려도 컨텍스트에서 잘려** Claude가 못 보던 문제. 스모크테스트: "테스트 결과서 양식"/"SR 변경 불필요"/"반제" 질의에서 깊은 내용 포함 확인.
  - 계약 유지: `search_relevant(query)->[ctx]` 시그니처·컨텍스트 포맷(`[아티클: #id — title (cat)]\n{body}`) 불변 → 서버/프롬프트/자동스크롤 영향 없음(00-INDEX 불변식 무관).
- `[ALGO]` **검색 동의어맵 확장** — `SEARCH_SYNONYMS`에 최근 핵심어 14개 키 추가(반제/차변/대변/전표흐름/배차/테스트결과서/적용승인/적용관리/판매단가/NETPR/수금계획/계산서/SR/CTS). data-tags ×3 가중치만 의존하던 신규 주제어 질의 보강.
  - 영향: `archive-server.py::SEARCH_SYNONYMS`
  - 이유: 최근 추가 아티클(회계기초·반품취소②·CTS절차 확장)의 핵심어가 동의어맵에 없어 표현 차이로 누락 위험.
- `[ALGO]` **인테이크 정의-불일치 휴리스틱 추가** (archive-intake.py). 기존 `detect_conflict`(순서역전 4쌍)는 정의 충돌(한 코드가 글마다 'CR/DR이력'↔'반품이력'으로 어긋난 류)을 못 잡았음 → `detect_definition_divergence()` 신설: **사전 아티클(DICT_ARTICLES 9종)끼리** 같은 코드 뒤 '설명'을 글자 bigram Jaccard<0.18로 비교 → `[?] 정의 불일치 의심`. `_looks_definitional()`로 산문·링크 조각 제외, `_def_snippet()`은 CR/DR·I/O의 '/'를 보존. CONFLICT_PAIRS에 VF11→VL09·회계먼저/재고먼저 2쌍 추가.
  - 영향: `archive-intake.py`(CODE_RE, DICT_ARTICLES, _def_snippet, _char_bigrams, _looks_definitional, detect_definition_divergence, run STEP 3b, CONFLICT_PAIRS)
  - 이유: 정의 충돌(같은 코드 다른 설명)이 인테이크에서 안 잡혀 사람이 일일이 비교해야 했음. 사전끼리로 스코프를 좁혀 오탐 최소화.
  - 검증: 단위테스트(사전끼리 충돌 검출 / 사전vs산문 무시 / 일관케이스 무플래그) + 실데이터(예시 코드 다수 오탐 0). 한계: 표현차·교차언급에 잔여 advisory 1~2건 가능(정밀도 한계, '오탐 가능' 라벨).
- `[DOC]` 03-algorithms-scaling.*(검색 A절 발췌방식·인테이크 B절 3b·현재 N=58) 갱신.
  - 영향: `03-algorithms-scaling.ai.md`, `03-algorithms-scaling.human.md`
  - 참고: 본 변경들은 알고리즘 내부 개선으로 ARTIFACT MAP·CORE INVARIANTS 불변 → 00-INDEX 갱신 불요.

## 2026-05-29
- `[STRUCTURE]` **블루프린트 폴더 이동** — `C:\Users\<user>\Documents\Third-Party-Brain` → `C:\My-Projects\Third-Party-Brain`. 동기화 체인 참조 경로(`SAP SD AI Indexable Archive\.claude\CLAUDE.md`의 블루프린트 경로) 1곳 갱신. 동기화 끊김 없음 검증 완료.
  - 영향: 폴더 전체 위치, `…\.claude\CLAUDE.md`(블루프린트 경로)
  - 이유: 사용자 프로젝트를 `C:\My-Projects` 컨테이너로 통합.
  - 참고: 블루프린트 `canonical_example`(원본 아카이브 경로)는 아카이브 미이동이라 불변.
- `[STRUCTURE][DEPLOY]` **대화 로그 기능 추가** — `/query` 처리 시 질문/답변/시각/접속IP/참조아티클을 `conversations.jsonl`(BASE 디렉토리, 1줄=1대화 JSONL)에 append. `log_conversation()` 추가, do_POST에서 호출. 실패해도 검색 서비스에 영향 없음(try/except pass). 공유 검증 시 전임자 등 접속자의 모든 질의응답을 호스트 PC에서 사후 검토 가능.
  - 영향: `archive-server.py`(log_conversation, do_POST, CONV_LOG 상수, datetime import), 신규 산출물 `conversations.jsonl`
  - 이유: 공유 검증 중 접속자 대화가 어디에도 안 남아(일회성 claude -p, 브라우저 메모리만) 피드백 검토 불가했음.
  - 주의: 로그에 입력 내용 그대로 저장됨 → 민감정보 입력 금지 원칙 유지. 로그는 호스트 PC 로컬 파일.
- `[ALGO]` **동의어맵에 월 단위 정기업무 보강** — `월초/월별/정기/매달/이번달` 추가, 모두 `월별 오더생성(커스텀 T-Code)` + `월말결산(결산 T-Code)`을 함께 끌어오도록 매핑. 기존엔 "월초에 할 일" 질의가 `#sm-order-flow`만 반환하고 `#month-end-closing` 누락 → 답변에서 월말결산 빠짐. 수정 후 월초/월간/정기/이번달 질의 모두 top3에 `#month-end-closing` 포함.
  - 영향: `archive-server.py::SEARCH_SYNONYMS`
  - 이유: "월초/월간 할 일" 류 정기업무 질의가 결산을 못 끌어와 답변 누락 발생.
- `[DEPLOY]` 공유 모드(`--share`) 기동 시 **브라우저 자동 열기 주소를 localhost → LAN IP**로 변경. `browse_host = ip if cli.share else "localhost"`. 호스트 본인 브라우저에도 동료에게 줄 공유 링크(`http://{lan_ip}:5174`)가 바로 떠서 링크 복사 혼선 제거.
  - 영향: `archive-server.py`(open_browser)
  - 이유: 공유 모드인데 브라우저가 localhost로 열려, 그 주소를 동료에게 줘도 접속 안 되는 혼선 발생.
- `[DOC][STRUCTURE]` 블루프린트에 **MANDATORY SYNC 지침** + 이 CHANGELOG 신설. INV7(인코딩)·INV8(동기화)·INV9(상대경로 fetch) 추가. ARTIFACT MAP에 배치파일 5종 반영.
  - 영향: `00-INDEX.ai.md`, `00-INDEX.human.md`, `CHANGELOG.*`
  - 이유: 프로그램/구조 변경이 블루프린트에 자동 반영되지 않아 실제 구현과 문서가 어긋날 위험. 모든 AI 대상 강제 규칙화.
- `[DEPLOY][STRUCTURE]` **실행/종료 배치파일 5종 추가** — 1_개인모드, 2_공유모드, 3_개인종료, 4_공유종료, 5_전체종료. 개인=127.0.0.1 / 공유=0.0.0.0 바인딩 주소로 모드별 선택 종료(netstat `tokens=5`→taskkill, PID 0 제외).
  - 영향: `1~5_*.bat`(신규)
  - 이유: 비개발자도 더블클릭으로 서버 운용. 모드별 독립 종료 요구.
- `[ENCODING]` 배치파일 **CP949 인코딩 + 리다이렉션 제거** 확정. 한국어 cmd 기본 CP949에서 UTF-8 배치는 한글 줄이 명령으로 오인되어 깨짐. 또한 린터가 `>nul`→`>/dev/null`(Unix)로 변형 → cmd에서 실패. 해결: 배치는 CP949로 저장 + `>nul` 미사용(출력 약간 verbose 허용). 기동 배치는 python 직전 `chcp 65001`, 종료 후 `chcp 949`.
  - 영향: `1~5_*.bat`, 블루프린트 INV7
  - 이유: 한국어 Windows 호환 + 린터 변형 회피.
- `[DEPLOY]` `archive-server.py` **`--share` 플래그(LAN 공유)** 추가 — `0.0.0.0` 바인딩, 기동 시 LAN IP 링크·방화벽(netsh) 안내 출력. `allow_reuse_address=True`.
  - 영향: `archive-server.py`
  - 이유: 같은 네트워크 선임자 검증·협업.
- `[ALGO]` 프론트 fetch URL을 `http://localhost:5174/query` → **`window.location.origin + '/query'`** 상대경로화.
  - 영향: `archive-server.py`(AI 패널 JS)
  - 이유: LAN 공유 시 타 PC 브라우저에서 localhost가 자기자신을 가리켜 실패. INV9.
- `[ALGO]` 검색 품질 개선 — **동의어맵 확장**(`SEARCH_SYNONYMS`: 월간↔월말↔마감↔결산 등) + **제목/태그 히트 ×3 가중** + **짧은 ASCII코드(RE/CR/DR) 단어경계 매칭**(영어단어 substring 노이즈 제거). 빈 결과(질의어≠아카이브용어) 문제 해소.
  - 영향: `archive-server.py::search_relevant`, `load()`(tags 추출 추가)
  - 이유: "월간 작업" 질의가 "월말 결산" 아티클을 못 찾던 누락.
- `[STRUCTURE]` 페이지 내 자동 네비게이션 — 답변 후 첫 출처 아티클로 **자동 스크롤 + 하이라이트 플래시**, 출처 버튼, "페이지에서 이 내용 보기" 버튼. 시스템 프롬프트에 "이동 불가라고 말하지 말 것" 명시.
  - 영향: `archive-server.py`(AI 패널 JS/CSS, build_prompt)
  - 이유: 챗봇이 사이트 임베드 JS이므로 실제 페이지 제어 가능 — UX 개선.

## (이전) 블루프린트 v1.0 최초 작성 — 2026-05-29
- 5개 주제 × (ai/human) 10개 문서 + README 작성. 당시 구현 스냅샷 기준. 상세 빌드업은 `02-buildup-process.ai.md` P1~P10 참조.
