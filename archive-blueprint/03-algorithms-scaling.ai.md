---
doc_type: ai_reference
topic: search_intake_algorithms_and_scaling_thresholds
version: 1.2
last_updated: 2026-06-05
critical: "이 문서는 규모(N=아티클 수)에 따라 알고리즘을 언제 바꿔야 하는지 정의한다. 재구축/확장 시 필수 참조."
---

# ALGORITHMS & SCALING THRESHOLDS

## A. 검색 알고리즘 (현재, archive-server.py::search_relevant / rank_article_ids)
```
0. 인덱스: 서버 기동 시(load 끝 build_index()) 각 아티클 텍스트(제목+태그+본문)를 char-2gram
   토큰화 → BM25Okapi 인덱스 1회 구축(_bm25, _bm25_ids). 의존성: rank_bm25.
1. 질의어 추출: re.findall([A-Za-z가-힣][...]+) → 동의어 확장(expand_query). (※ 확장본은 6번 발췌용)
2. 랭킹(rank_article_ids): 원질의를 char-2gram 토큰화 → bm25.get_scores → 상위 top_n(=3).
   IDF(흔한 코드 노이즈 하향)·문서길이 정규화(긴 글 편향 보정)는 BM25가 처리.
3. 동의어 확장은 **랭킹엔 미적용**: 실측상 BM25 랭킹에 동의어를 넣으면 R@1 하락(흔한 Z코드 동의어가
   무관 아티클을 끌어올려 노이즈) → 패시지 추출·legacy fallback에서만 유지.
4. 컨텍스트화: 양수 점수 후보가 있으면 비양수(무관) 아티클 제외 후 top_n만.
5. 단어경계 매칭 make_pattern(len≤3 ASCII RE/CR/DR): char-2gram 랭킹엔 불필요(자연 완화)하나
   extract_passage·legacy fallback에서 그대로 사용(영어 단어 속 substring 오탐 차단).
6. 컨텍스트 발췌 = extract_passage() (불변): 키워드(동의어 확장본) 첫 매칭 위치 주변(−400/+1600)
   발췌 + 글 머리(제목/도입 300자) 동봉, 상한 ~2200자. 매칭이 머리(≤300자)면 앞에서부터.
7. graceful fallback: rank_bm25 임포트 실패/_bm25=None → 기존 term-count(본문 +1, 제목/태그 ×3,
   동의어 확장) 스코어링(_rank_legacy_scored)으로 자동 폴백.
```
**측정**(오프라인 검색평가, 실아카이브 65문서·49질의 라벨셋): 구 term-count(제목×3+동의어) **R@1 42.9% / R@3 63.3%** → 신 BM25(char-2gram) **R@1 81.6% / R@3 85.7%** (MRR 0.857, ~1.3ms/q). 범용 dense(MiniLM-multilingual)는 이 소규모·전문용어 코퍼스엔 부적합(R@1 12%). 핵심 원인: 구 스코어링은 IDF·길이정규화가 없어 흔한 코드 노이즈·긴 글 편향에 취약 → BM25가 정확히 이 둘을 보정.

## B. 인테이크 알고리즘 (archive-intake.py)
```
1. expand_keywords(ALIASES)
2. search_archive → 아티클별 히트 집계
3. detect_conflict(CONFLICT_PAIRS): 절차 순서 역전 정규식쌍 매칭 (하드 [!!])
3b. detect_definition_divergence: **사전 아티클(DICT_ARTICLES)끼리만** 같은 코드의 뒤따르는 '설명'을 글자 bigram Jaccard<0.18로 비교 → '[?] 정의 불일치 의심'(휴리스틱·오탐 가능). 비-사전 산문 인용·링크 조각은 _looks_definitional로 제외. 목적: 한 코드가 사전 글마다 다른 정의(예: 'CR/DR 이력'↔'반품 이력')로 어긋난 '정의 충돌' 포착. 한계: 표현차/교차언급에 잔여 오탐 1~2건 가능(정밀도 한계, advisory).
4. 중복도: 신규텍스트 단어집합 ∩ 기존 / |신규| > 0.7 → 중복경고
5. suggest_category(CATEGORY_SIGNALS): 시그널 키워드 카운트
6. 판정: NEW(0히트) / UPDATE(1아티클) / REVIEW(2+) / CONFLICT
```

## C. 스케일링 임계점 — **언제 무엇을 바꾸나** (핵심)
| 규모 N | 검색 방식 | 인테이크 | 인덱스 | 변경 트리거 / 신호 |
|--------|----------|---------|--------|------------------|
| **≤200** (예시 도메인 현재 수십 개) | **BM25(char-2gram) 랭킹** + 매칭위치 발췌(extract_passage); 동의어맵은 패시지추출/fallback | 단어집합 중복도 + 충돌패턴 | 인메모리 BM25 + 단일 `structure.md` | 현 구조 유지. rank_bm25 의존(미설치 시 term-count fallback). |
| **200–500** | 동일 + 동의어맵 자동확장 검토 | 카테고리별 분리 검사 | structure.md를 카테고리별 분할 | 동의어맵 항목 >50개 / 검색 오탐↑ / structure.md 1파일 가독성 저하 |
| **500–1000** | **SQLite FTS5로 이전** (랭킹은 BM25 유지 — 인메모리→DB 인덱스) | FTS 기반 유사도 | DB 인덱스 | 단일 HTML 로딩 >1s / 인메모리 BM25 재구축·메모리 부담 |
| **>1000 또는 의미검색 요구** | **임베딩 시맨틱 검색** (벡터인덱스: sqlite-vec/faiss + 로컬 임베딩) | 임베딩 유사도 + LLM 중복판정 | 벡터 + 메타 인덱스 | 키워드 불일치 누락 빈발 / "비슷한 의미" 질의 요구 / 동의어맵 한계 |

## D. 변경 시 보존해야 할 인터페이스 (마이그레이션 계약)
- `search_relevant(query) -> [context_str]` 시그니처 유지 → 서버/프롬프트 불변.
- 컨텍스트 포맷 `[아티클: #{id} — {title} ({cat})]\n{body}` 유지 → source 파싱·자동스크롤 불변.
- 아티클 `id`는 영구 불변 (검색백엔드 바뀌어도 앵커·소스링크 유지).
- `claude -p` 호출부는 백엔드 교체와 독립.

## E. 백엔드 전환 레시피 (요약)
- **→ SQLite FTS5**: `articles(id, title, tags, body, cat)` + FTS5 가상테이블. HTML은 표시용으로 유지, 빌드 시 HTML→DB 추출 스크립트 1개 추가. `search_relevant`만 교체.
- **→ 임베딩**: 빌드 시 아티클별 임베딩 생성→벡터스토어. 질의 임베딩→top-k 코사인. 동의어맵 제거 가능. 로컬 임베딩 모델 권장(외부유출 0 원칙 유지).

## F. 인코딩 불변식 (규모 무관 항상)
- 파일 UTF-8. 콘솔 stdout UTF-8 wrap. cmd 경유 `chcp 65001` + 폴백 디코드.
- 한글을 CLI argv로 직접 전달 금지 → 임시파일/stdin.
