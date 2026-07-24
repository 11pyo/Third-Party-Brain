---
doc_type: ai_reference
topic: search_intake_algorithms_and_scaling_thresholds
version: 1.4
last_updated: 2026-07-24
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

### A-1. 하이브리드 임베딩 검색 — 시도 후 폐기 (2026-07-24, N=96 아티클)
```
가설: BM25(char-2gram)에 범용 다국어 임베딩(sentence-transformers,
paraphrase-multilingual-MiniLM-L12-v2)을 결합하면 동의어 사전에 없는 표현도 잡을 것.

실측(라벨 20질의, _tmp/_eval_retrieval.py):
  - BM25 단독(기준선):                              R@1 70.0% / R@3 75.0%
  - BM25+임베딩 대등 RRF(순위기반) 융합:            R@1 50.0% / R@3 55.0%  ← 악화
  - BM25 우선, "BM25가 못 찾을 때만" 임베딩 보강
    (rescue-only, BM25 top_n 중 양수점수 <top_n일 때만 발동): R@1 70.0%/R@3 75.0%(회귀 0)
    이지만 → 이 코퍼스의 BM25Okapi는 완전 무관한 질의(외계어·숫자나열)에도
    96개 중 90개+ 문서에 양수 점수를 줘서 "BM25가 못 찾은 경우"가 사실상 발생 안 함
    → rescue 분기가 도달 불가능한 죽은 코드였음.

결론: 이 규모·전문용어 밀도의 코퍼스에서는 범용 임베딩이 이미 튜닝된 BM25보다
부정확하고, 안전하게 결합하려던 방법(rescue-only)도 실제로는 발동하지 않는다.
→ 임베딩 레이어는 도입하지 않고 순수 BM25 유지.
재도전 조건: ① 이 코퍼스에 파인튜닝된 임베딩 확보, 또는 ② BM25 양수점수 분포 자체가
지금과 달라지는 구조 변화(코퍼스 성격 변화·문서당 길이 급증 등) — 재도전 전 반드시
`_tmp/_eval_retrieval.py`(사내 정본 폴더, 20질의 라벨셋)로 회귀 확인할 것.
```
> 아래 §C "N>1000 또는 의미검색 요구 → 임베딩 전환" 권고는 **"일반론"**이며 위 실측으로
> 무효화되지 않는다(그 권고는 코퍼스가 훨씬 커지고 성격이 달라진 뒤의 얘기) — 다만 그
> 시점에도 "임베딩=항상 이득"이라 가정하지 말고 매번 회귀 테스트할 것이 이번 실측의 교훈.

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

## B2. 링크·backlink 렌더 알고리즘 (archive.html 인라인 JS, data-related) — 2026-06-24
```
0. 메타: 각 article에 data-related="id id ..."(# 없는 공백구분 아티클 id). 본문 무손상·속성만 추가.
   동반 메타 data-cat/data-topics/data-updated(현 렌더 미소비, 향후 필터용). 통제어휘=META_TAG_SCHEMA(원본폴더).
1. DOMContentLoaded: article.article 수집 → byId 맵 + back(역참조) 인덱스 1회 구축
   (data-related를 역방향 뒤집어 backlink 무료 생성 — 한쪽만 적어도 양방향).
2. 각 아티클 하단 .rel-panel(data-noexport) 동적 append: 「🔗 관련」=fwd(자기 data-related),
   「↩ 여기를 참조」=bk(나를 가리키는 글, fwd와 중복 제외). 둘 다 없으면 패널 생략.
3. 클릭 위임(document): .rel-chip→대상 scrollIntoView+collapsed 해제 / .tags .tag→search-input에
   태그텍스트 주입 후 doSearch()+scrollTop. body.editing이면 무시(제목 편집 우선).
4. 단일출처: 연결 정본=data-related 속성뿐. 패널은 render-only → saveFile의 [data-noexport] strip이
   자동 제거(저장오염 0). id=불변키(제목 변경에도 링크 불파손).
```
**설계의도**: 검색(BM25=쿼리→문서, 섹션 A)과 **직교하는 탐색축**(문서→인접문서) 보강. Obsidian 양방향링크 패턴의 앱-프리 흡수. **커버리지**: 큐레이션 핵심 클러스터에만 부여(전수금지=AI 검색 노이즈 가드레일). 현 정본 15아티클(여신/세금/반품/취소 허브), 공개샘플 데모 4아티클(라벨 EN). 코어 검색·인테이크 불변. 포지셔닝 상세=`COMPARISON-llm-wiki`(PKM/Obsidian).

## C. 스케일링 임계점 — **언제 무엇을 바꾸나** (핵심)
| 규모 N | 검색 방식 | 인테이크 | 인덱스 | 변경 트리거 / 신호 |
|--------|----------|---------|--------|------------------|
| **≤200** (예시 도메인 현재 수십 개) | **BM25(char-2gram) 랭킹** + 매칭위치 발췌(extract_passage); 동의어맵은 패시지추출/fallback | 단어집합 중복도 + 충돌패턴 | 인메모리 BM25 + 단일 `structure.md` | 현 구조 유지. rank_bm25 의존(미설치 시 term-count fallback). |
| **200–500** | 동일 + 동의어맵 자동확장 검토 | 카테고리별 분리 검사 | structure.md를 카테고리별 분할 | 동의어맵 항목 >50개 / 검색 오탐↑ / structure.md 1파일 가독성 저하 |
| **500–1000** | **SQLite FTS5로 이전** (랭킹은 BM25 유지 — 인메모리→DB 인덱스) | FTS 기반 유사도 | DB 인덱스 | 단일 HTML 로딩 >1s / 인메모리 BM25 재구축·메모리 부담 |
| **>1000 또는 의미검색 요구** | **임베딩 시맨틱 검색** (벡터인덱스: sqlite-vec/faiss + 로컬 임베딩) ⚠️도입 전 §A-1 참조(N=96 실측: 범용 임베딩이 BM25 대비 R@1 70%→50%로 악화한 사례 — 매번 회귀테스트 필수) | 임베딩 유사도 + LLM 중복판정 | 벡터 + 메타 인덱스 | 키워드 불일치 누락 빈발 / "비슷한 의미" 질의 요구 / 동의어맵 한계 |

## D. 변경 시 보존해야 할 인터페이스 (마이그레이션 계약)
- `search_relevant(query) -> [context_str]` 시그니처 유지 → 서버/프롬프트 불변.
- 컨텍스트 포맷 `[아티클: #{id} — {title} ({cat})]\n{body}` 유지 → source 파싱·자동스크롤 불변.
- 아티클 `id`는 영구 불변 (검색백엔드 바뀌어도 앵커·소스링크 유지).
- Claude 호출부(`call_claude` 오케스트레이션 — API 우선/CLI 폴백, 01문서 참조)는 검색 백엔드 교체와 독립.

## E. 백엔드 전환 레시피 (요약)
- **→ SQLite FTS5**: `articles(id, title, tags, body, cat)` + FTS5 가상테이블. HTML은 표시용으로 유지, 빌드 시 HTML→DB 추출 스크립트 1개 추가. `search_relevant`만 교체.
- **→ 임베딩**: 빌드 시 아티클별 임베딩 생성→벡터스토어. 질의 임베딩→top-k 코사인. 동의어맵 제거 가능. 로컬 임베딩 모델 권장(외부유출 0 원칙 유지). ⚠️§A-1 실측 참조 — 도입 전 반드시 자체 라벨셋으로 BM25 대비 회귀 테스트(범용 임베딩이 항상 이득이라는 보장 없음, 이 코퍼스 규모·성격에서는 오히려 악화 확인됨).

## F. 인코딩 불변식 (규모 무관 항상)
- 파일 UTF-8. 콘솔 stdout UTF-8 wrap. cmd 경유 `chcp 65001` + 폴백 디코드.
- 한글을 CLI argv로 직접 전달 금지 → 임시파일/stdin.
