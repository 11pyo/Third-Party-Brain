# archive.html 구조 인덱스
> **목적**: 매 세션마다 archive.html 전체를 읽지 않도록 구조를 미리 파악하기 위한 경량 인덱스.  
> **업데이트 규칙**: archive.html에 아티클 추가·삭제·이동 시 이 파일도 반드시 동기화할 것.  
> **최종 업데이트**: 2026-10-16

---

## 파일 위치
```
archive.html
```

---

## 전체 아티클 수
| 카테고리 | 아티클 수 | HTML 변수 (cnt) |
|----------|-----------|----------------|
| 📘 기초용어 | 3 | `<span class="cnt">3</span>` |
| 🔄 프로세스 | 2 | `<span class="cnt">2</span>` |
| ⚙️ 기술설정 | 1 | `<span class="cnt">1</span>` |
| 🔧 트러블슈팅 | 2 | `<span class="cnt">2</span>` |
| 📋 운영참조매뉴얼 | 1 | `<span class="cnt">1</span>` |
| **합계** | **9** | |

> **🔗 메타·링크 레이어 (2026-06-24, Obsidian 패턴 융합)**: 일부 핵심 아티클에 `data-related`(관련글 id 공백구분)·`data-cat` 속성이 추가됨(본문 무손상·검색 영향 0·아티클 수 불변). 페이지 하단 인라인 JS가 이를 읽어 글 하단에 「🔗 관련 / ↩ 여기를 참조」 backlink 칩 + `#태그` 클릭검색을 자동 렌더(`data-noexport`=💾저장 제외, 정본=`data-related` 속성뿐). 통제 태그어휘·메타 규칙=`META_TAG_SCHEMA.md`. 현재 부여 15아티클(여신/세금/반품/취소 허브). 알고리즘 상세=블루프린트 `03-algorithms-scaling`.

---

## 📘 기초용어 (3개)

| # | id | 제목 | 핵심 키워드 |
|---|----|----|------------|
| 1 | `order-type-io` | 오더 / 내부오더(IO) 유형 | 오더 내부오더 IO 유형 단품 서비스 비용집계 진행매출 sample 기초용어 |
| 2 | `tcode-master` | 커스텀 T-Code 마스터 | 커스텀 T-Code 마스터 ZSD ZMM ZCO 판매오더 세금계산서 매출취소 결산 sample 기초용어 |
| 3 | `ztsd-tables` | ZTSD 테이블 참조 | ZTSD 테이블 커스텀 데이터사전 단가 여신 sample 기초용어 ZTSD010 ZTSD071 ZTSD075 |

---

## 🔄 프로세스 (2개)

| # | id | 제목 | 핵심 키워드 |
|---|----|----|------------|
| 1 | `base-order-flow` | 표준 판매오더 처리 흐름 | 판매오더 처리 흐름 출고 빌링 세금계산서 프로세스 sample ZSD025 ZSD010 |
| 2 | `proc-sales-cancel` | 매출 취소 프로세스 | 매출 취소 프로세스 빌링취소 세금계산서 ZSD030 VF11 VL09 순서 프로세스 sample |

---

## ⚙️ 기술설정 (1개)

| # | id | 제목 | 핵심 키워드 |
|---|----|----|------------|
| 1 | `month-end-closing` | 월말 결산 프로세스 | 월말 결산 프로세스 마감 정기 ZSD143 기술설정 sample 월초 월별 |

---

## 🔧 트러블슈팅 (2개)

| # | id | 제목 | 핵심 키워드 |
|---|----|----|------------|
| 1 | `ts-credit-check` | 여신 점검 / 매출환산가치 | 여신 점검 매출환산가치 한도 노출액 Credit BLOCK FD32 VKM4 ZTSD071 트러블슈팅 sample |
| 2 | `ts-tax-invoice` | 세금계산서 수정·재발행 | 세금계산서 수정 재발행 오류 마이너스 정정 ZSD010 트러블슈팅 sample |

---

## 📋 운영참조매뉴얼 (1개)

| # | id | 제목 | 핵심 키워드 |
|---|----|----|------------|
| 1 | `ops-system-env` | 시스템 환경 & 연계 개요 | 시스템 환경 연계 개요 아키텍처 인터페이스 매뉴얼 참조 가이드 sample |

---

## When you add / remove / move an article — 3 places to update

1. **Sidebar nav link** inside `<nav id="sidebar">` (under the right category).
2. **Category count** `<span class="cnt">N</span>` → N±1.
3. **This file** (the table above + the line-number notes if you keep them).

Run `python archive-intake.py "<keywords>"` first — it tells you whether the
content is a duplicate, conflicts with an existing article, or needs a new one.

---

## CSS class reference (for authoring article bodies)

| Class | Use |
|-------|-----|
| `.sec` / `.st` | section wrapper / section title |
| `.tbl` | data table (header row dark) |
| `.tc` / `.tc-z` | inline code — standard SAP T-Code / custom Z T-Code |
| `.dt` | prose block (`<p>` paragraphs) |
| `.flow-bar` + `.fb`/`.fb-cur`/`.fb-next` | process flow strip |
| `.hl-box` | blue highlight callout |
| `.warn-box` | orange warning callout |
| `.tags` + `.tag` | keyword chips under the title |

---

## IO type quick reference

(Mirrors the `order-type-io` article — the TUI reads this section.)

| IO type | name | use |
|---------|------|-----|
| IO10 | 단품 판매 | simple goods sale cost roll-up |
| IO20 | 서비스/유지보수 | service-contract revenue & cost |
| IO30 | 진행매출(프로젝트) | long-project percentage-of-completion |
| IO90 | 건설중자산(AUC) | capitalizable cost collection |

*(All codes are fictional sample data.)*
