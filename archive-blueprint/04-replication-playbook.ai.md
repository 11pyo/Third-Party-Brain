---
doc_type: ai_reference
topic: replication_playbook_new_archive
version: 1.0
last_updated: 2026-05-29
trigger_phrases: ["새 아카이브", "이런 거 또 만들어", "다른 부서 아카이브", "위키 만들어"]
---

# REPLICATION PLAYBOOK — 새 아카이브 생성 (에이전트 실행 절차)

## STEP 0 — 도메인 파라미터 수집 (사용자에게 물을 것)
- DOMAIN: 주제 (예: "MM 모듈 운영", "인사팀 사내 절차")
- CATEGORIES: 카테고리 집합 (기본 5종 재사용 or 도메인 맞춤). 각 카테고리에 시그널 키워드 정의.
- ID_SCHEME: 아티클 id 규칙 (예: `cat-topic` 케밥케이스, 영구불변).
- SENSITIVE: 저장 금지 항목 목록 (비밀번호·IP·계정 등 — 도메인별 확정).
- TCODE_STYLE: 코드 표기 규칙 (SAP면 `코드 — 화면명`).
- SYNONYMS: 도메인 동의어 시드 (질의어↔내부용어).

## STEP 1 — 골격 HTML 생성
- 원본 `archive.html`의 `<head>` 인라인 CSS 전체 복사(컴포넌트 재사용).
- `<nav id="sidebar">` 카테고리 헤더 + 빈 링크목록 + `<span class="cnt">0</span>`.
- 빈 `<article>` 컨테이너 영역. 제목줄에 DOMAIN·작성자·날짜.
- AI 패널은 서버가 주입하므로 HTML엔 불필요.

## STEP 2 — 아티클 작성 규격 (불변)
```html
<article id="{stable-id}" data-tags="키워드 공백구분 동의어포함">
  <div class="ah"><div class="at">제목</div>
    <span class="badge b-{cat}">카테고리</span><span class="db">YYYY-MM-DD</span></div>
  <div class="tags"><span class="tag">#키워드</span>...</div>
  <div class="sec"><div class="st">섹션제목</div> ...내용... </div>
</article>
```
- data-tags에 **검색 동의어를 풍부하게** 넣을수록 검색 적중↑.

## STEP 3 — 인덱스 파일 생성 (`{name}-structure.md`)
- 카테고리별 표: # / id / 제목 / 대략 line / 핵심 키워드.
- 전체 카운트 표. CSS 클래스 레퍼런스. 삽입 체크리스트(3곳 동기화).

## STEP 4 — 파이썬 도구 3종 복제 + 파라미터화
- `archive-intake.py`, `archive-menu.py`, `archive-server.py` 복사.
- 수정 포인트: `BASE`/파일명 경로, `ALIASES`/`SEARCH_SYNONYMS`(도메인 동의어), `CATEGORY_SIGNALS`(카테고리 시그널), `CONFLICT_PAIRS`(도메인 충돌 패턴), `PORT`(충돌 회피).
- 인코딩 처리부·claude 경로탐지부·LAN공유부는 **그대로 재사용**(도메인 무관).

## STEP 5 — 검증 (필수, ≥3 케이스)
- 검색: 도메인 대표 질의 3종 → 관련 아티클 top3 정확성 확인.
- 인테이크: 기존중복/신규/충돌 각 1케이스 → 판정 정확성.
- 서버: GET 200 + /query 실응답(claude) + 한글 비깨짐.
- LAN: `--share` 후 `http://{lan_ip}:{port}` 200.

## STEP 6 — 운영 규율 인계
- 편집 후 3곳 동기화 규칙. 인테이크 선검사. 민감정보 금지. T-Code 표기법.
- 규모 증가 시 `03-algorithms-scaling` 임계점 따라 백엔드 전환.

## REUSE CHECKLIST (그대로 vs 교체)
| 컴포넌트 | 그대로 | 도메인별 교체 |
|---------|--------|--------------|
| 인라인 CSS | ✅ | 색상 테마만 선택적 |
| 인코딩/claude경로/LAN/서버골격 | ✅ | — |
| search_relevant 로직 | ✅ | SEARCH_SYNONYMS |
| intake 로직 | ✅ | ALIASES, CATEGORY_SIGNALS, CONFLICT_PAIRS |
| 아티클 데이터 | — | ✅ 전부 신규 |
| 카테고리/시그널 | — | ✅ |
