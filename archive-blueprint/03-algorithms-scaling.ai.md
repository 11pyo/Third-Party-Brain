---
doc_type: ai_reference
topic: search_intake_algorithms_and_scaling_thresholds
version: 1.0
last_updated: 2026-05-29
critical: "이 문서는 규모(N=아티클 수)에 따라 알고리즘을 언제 바꿔야 하는지 정의한다. 재구축/확장 시 필수 참조."
---

# ALGORITHMS & SCALING THRESHOLDS

## A. 검색 알고리즘 (현재, archive-server.py::search_relevant)
```
1. 질의어 추출: re.findall([A-Za-z가-힣][...]+)  (1자 이상)
2. 동의어 확장: SEARCH_SYNONYMS dict (월간↔월말↔마감↔결산 등)
3. 본문 점수: 각 키워드 정규식 finditer → 소속 아티클 +1
4. 제목/태그 점수: 키워드가 title|tags에 있으면 +3 (가중)
5. 단어경계 매칭: len≤3 ASCII 토큰(RE/CR/DR)은 (?<![A-Za-z])kw(?![A-Za-z]) → substring 노이즈 제거
6. 정렬 top_n=3, score>0만 컨텍스트화 (각 1800자)
```

## B. 인테이크 알고리즘 (archive-intake.py)
```
1. expand_keywords(ALIASES)
2. search_archive → 아티클별 히트 집계
3. detect_conflict(CONFLICT_PAIRS): 절차 순서 역전 정규식쌍 매칭
4. 중복도: 신규텍스트 단어집합 ∩ 기존 / |신규| > 0.7 → 중복경고
5. suggest_category(CATEGORY_SIGNALS): 시그널 키워드 카운트
6. 판정: NEW(0히트) / UPDATE(1아티클) / REVIEW(2+) / CONFLICT
```

## C. 스케일링 임계점 — **언제 무엇을 바꾸나** (핵심)
| 규모 N | 검색 방식 | 인테이크 | 인덱스 | 변경 트리거 / 신호 |
|--------|----------|---------|--------|------------------|
| **≤200** (현재 51) | 정규식 전문검색 + 동의어맵 + 제목 ×3 | 단어집합 중복도 + 충돌패턴 | 단일 `structure.md` | 현 구조 유지. 동의어맵 수기 관리 가능. |
| **200–500** | 동일 + 동의어맵 자동확장 검토 | 카테고리별 분리 검사 | structure.md를 카테고리별 분할 | 동의어맵 항목 >50개 / 검색 오탐↑ / structure.md 1파일 가독성 저하 |
| **500–1000** | **SQLite FTS5로 이전** (BM25 랭킹) | FTS 기반 유사도 | DB 인덱스 | 단일 HTML 로딩 >1s / 정규식 풀스캔 체감 지연 / 메모리 부담 |
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
