# CLAUDE.md

> Auto-loaded by Claude Code. **Read [`AGENTS.md`](./AGENTS.md) first** — it is the full
> onboarding (functions, structure, rules, direction). This file is the short version.
>
> Claude Code가 자동 로드합니다. **먼저 [`AGENTS.md`](./AGENTS.md)** 를 읽으세요 — 기능·구조·규칙·방향
> 전체 온보딩이 거기 있습니다. 이 파일은 요약본입니다.

## What · 무엇
Third-Party-Brain = blueprint + runnable reference implementations for an **AI-searchable
operational knowledge archive ("third brain")**. Primary content = **archive + AI collaboration**.
The **AI Collaboration Dashboard** also has its own standalone repo: **`11pyo/ai-collab-dashboard`**.

Third-Party-Brain = **AI 검색 가능 운영 지식 아카이브("제3의 뇌")**의 블루프린트 + 실행 레퍼런스 구현.
주 콘텐츠 = **아카이브 + AI 협업**. **AI 협업 대시보드는 별도 전용 레포 `11pyo/ai-collab-dashboard`** 로도 존재.

## Top rules · 핵심 규칙 (full list in AGENTS.md §4)
1. **Public repo → fictional sample data only.** No real names/customers/T-Codes/secrets. · 공개 레포 → 가짜 샘플만.
2. **Bilingual docs (KO + EN).** · 문서 한/영 병기.
3. **Blueprint sync** on program/structure changes (update `*.ai.md`+`*.human.md` + `CHANGELOG.*`). · 구조 변경 시 블루프린트·체인지로그 동기화.
4. **Dashboard log is append-only** — use `log-inquiry.py`, never hand-edit `inquiry-log.js`. · 대시보드 로그 추가전용.
5. **`*.local.md` = private, git-ignored** — never copy into committed files. · 로컬 비공개 메모.

## Start here · 시작점
- `AGENTS.md` → `archive-blueprint/00-INDEX.ai.md` → `01` → `03` (algorithms) → `04` (replication).
- Working code: `reference-implementation/archive/` and `reference-implementation/dashboard/`.
