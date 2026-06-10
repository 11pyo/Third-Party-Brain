# AGENTS.md — onboarding for AI agents · AI 에이전트 온보딩

> **새 대화 세션이면 이 파일을 먼저 읽으세요.** 이 한 장으로 이 저장소의 **기능·규칙·방향**을 즉시 파악할 수 있게 만들었습니다.
> **If you are a fresh AI session, read this first.** This single page gets you onboarded to the project's **functions, rules, and direction** immediately.

---

## 1. What this project is · 이게 뭔가

**EN** — *Third-Party-Brain* is a **blueprint (methodology) + runnable reference implementations** for building a portable, **AI-searchable operational knowledge archive** ("a third brain"). The primary content is the **knowledge archive + AI collaboration** workflow. It runs on a few files — no database, no server install — with a local LLM for natural-language search.

**KO** — *Third-Party-Brain*은 이식성 좋은 **AI 검색 가능 운영 지식 아카이브("제3의 뇌")**를 만드는 **방법론(블루프린트) + 실행 가능한 레퍼런스 구현**입니다. 주 콘텐츠는 **지식 아카이브 + AI 협업**입니다. 무거운 DB·서버 없이 파일 몇 개와 로컬 LLM 검색으로 굴러갑니다.

> 🔗 **Sister repo · 자매 레포:** the **AI Collaboration Dashboard** also lives as its own standalone repository — **https://github.com/11pyo/ai-collab-dashboard** . A mirror reference copy is included here under `reference-implementation/dashboard/`, but that dedicated repo is the standalone home for the dashboard.
> AI 협업 대시보드는 **별도 전용 레포(`11pyo/ai-collab-dashboard`)로도 존재**합니다. 여기 `reference-implementation/dashboard/`에 미러 사본을 두지만, 대시보드 단독 본거지는 그 전용 레포입니다.

---

## 2. Repository map · 저장소 지도

```
Third-Party-Brain/
├─ README.md / README.en.md        시작점 (KO / EN) · entry point
├─ AGENTS.md (이 파일) / CLAUDE.md   AI 자동 온보딩 · agent auto-onboarding
├─ LICENSE · CONTRIBUTING.md · SECURITY.md
├─ archive-blueprint/               ⭐ 방법론 문서 · the methodology
│   ├─ 00-INDEX.*        진입점 · 아티팩트 맵 · 불변식(INV) · 동기화 지침
│   ├─ 01..07-*.*        아키텍처/빌드업/알고리즘/복제/운영/자동화/대시보드 (각 .ai.md+.human.md)
│   └─ CHANGELOG.*       프로그램·구조 변경 이력
└─ reference-implementation/        ⭐ 실행 가능한 동작본 (가짜 샘플 데이터)
    ├─ archive/          제3의뇌 아카이브 엔진 (BM25 검색서버·인테이크·TUI + 샘플 archive.html)
    └─ dashboard/        AI 협업 대시보드 (append-only id-병합 로거 + 칸반·문의보드)
```

**Docs come in pairs · 문서는 2벌씩:** `*.ai.md` (compact, for AI agents) and `*.human.md` (narrative, for people). Same content, different form.

---

## 3. Reading order for a new agent · 새 에이전트 권장 독서 순서

1. **This file (AGENTS.md)** — orientation, rules.
2. `archive-blueprint/00-INDEX.ai.md` — entry point, artifact map, invariants (INV1–INV9), sync rules.
3. `archive-blueprint/01-overview-architecture.ai.md` → `03-algorithms-scaling.ai.md` — architecture + the search/intake algorithms (code-level).
4. `archive-blueprint/04-replication-playbook.ai.md` — step-by-step to build a new archive.
5. `05` (operational layer) · `06` (automation/ops safety) · `07` (dashboard guide).
6. To see working code, open `reference-implementation/archive/` and `reference-implementation/dashboard/` (each has its own README).

---

## 4. Rules — do NOT break these · 절대 규칙

1. **Public repo → fictional sample data ONLY.** Never commit real company names, customers, people, internal/custom T-Codes, table names, document numbers, amounts, hostnames, IPs, or credentials. Invent examples.
   **공개 레포 → 가짜 샘플만.** 실제 회사명·고객·인명·내부 Z T-Code·테이블명·문서번호·금액·호스트·IP·자격증명 절대 금지. 예시는 지어내세요. (See `SECURITY.md`.)
2. **Bilingual docs.** New git-tracked docs are written in **both Korean and English**.
   **문서 한/영 병기.** 새로 추가하는 git 문서는 **한글·영문 둘 다** 작성.
3. **Blueprint sync discipline.** If you change program logic / algorithms / file structure, you MUST update the matching `archive-blueprint/*.ai.md` + `*.human.md`, add a `CHANGELOG.*` entry (newest on top: date/type/change/files/why), and update `00-INDEX` artifact map if affected.
   **블루프린트 동기화.** 프로그램·알고리즘·구조 변경 시 해당 `*.ai.md`+`*.human.md` 갱신 + `CHANGELOG.*` 항목 추가 + 영향 시 `00-INDEX` 아티팩트 맵 갱신.
4. **Archive HTML contract.** Articles must keep the `<article id … data-tags>` + `class="at"/"badge"/"db"` shape — the Python tools parse it by regex. See `reference-implementation/archive/archive-structure.md`.
   **아카이브 HTML 계약.** 파서가 정규식으로 읽으므로 아티클 형식을 유지하세요.
5. **Dashboard log is append-only.** Never hand-edit `inquiry-log.js`; append via `log-inquiry.py` (append-only + id-merge + file-lock keeps concurrent writers safe).
   **대시보드 로그는 추가전용.** `inquiry-log.js` 직접 편집 금지, `log-inquiry.py`로만.
6. **`*.local.md` / `*.local` are git-ignored private notes** — read for intent, never copy into committed files.
   **`*.local.md`/`*.local`은 비공개 메모(gitignore)** — 의도 파악용으로만 읽고 커밋 파일에 옮기지 마세요.

---

## 5. Direction / vision · 방향과 비전

**EN** — Kill *bus-factor-1*: turn one person's tacit operational knowledge into a searchable, AI-queryable asset, and make day-to-day work visible + collaboration-safe. Memory (archive) + workflow (dashboard), designed so a person and their AI assistant operate as one. Full vision: `README.md` / `README.en.md` and `archive-blueprint/00–07`.

**KO** — *버스 팩터 1*을 없앤다: 한 사람 머릿속의 속지식을 검색·AI질의 가능한 자산으로 바꾸고, 일상 업무를 가시화하고 협업에 안전하게. 메모리(아카이브) + 워크플로우(대시보드)로, 사람과 AI 비서가 하나처럼 일하게. 전체 비전은 `README` 와 블루프린트 `00–07`.

---

## 6. When asked to "set this up" · "셋업해줘" 하면 — offer a choice, don't just run something
**Don't assume — offer two paths:**
- **Ⓐ See the demo** → run the shipped sample (no setup, all fictional data): `reference-implementation/archive/` (`pip install -r requirements.txt` → `python archive-server.py`, http://localhost:5174) or `reference-implementation/dashboard/task-board.html`.
- **Ⓑ Build their own** → run the **STEP 0 interview** first (domain · categories · sensitive/do-not-store list · code notation · synonyms · the **real content** to fill it), then follow `archive-blueprint/04-replication-playbook`. Never fabricate domain knowledge.

**먼저 선택지 제시** (지레짐작 금지): **Ⓐ 데모 보기** → 포함된 샘플 바로 실행(아카이브 `python archive-server.py` 또는 `dashboard/task-board.html`, 전부 가짜 데이터) · **Ⓑ 내 아카이브 만들기** → STEP 0 인터뷰(도메인·카테고리·민감정보 금지목록·코드표기·동의어·**실제 콘텐츠**)부터, 절차는 `04-replication-playbook`. 도메인 지식 임의 생성 금지.

## 7. Common tasks · 자주 하는 작업

- **Run the archive search server** — `cd reference-implementation/archive && python archive-server.py` (→ http://localhost:5174). `--share` for LAN.
- **Check before adding a knowledge article** — `python archive-intake.py "<keywords>"` (duplicate/conflict/placement).
- **Open the dashboard** — open `reference-implementation/dashboard/task-board.html` in a browser.
- **Log an inquiry** — `python reference-implementation/dashboard/log-inquiry.py --new --type simple --q "..." --by you`.
- **Build a brand-new archive for another domain** — follow `archive-blueprint/04-replication-playbook.ai.md`.
  **Run its STEP 0 interview first** — ask the user for: domain · categories(+signals) · id scheme ·
  **sensitive / do-not-store list** · code notation · synonyms · and the **real content** to fill it.
  Never fabricate domain knowledge. · 새 아카이브는 **STEP 0 인터뷰부터**: 도메인·카테고리·민감정보
  금지목록·코드표기·동의어·**실제 콘텐츠**를 사용자에게 묻고 시작(도메인 지식 임의 생성 금지).
