# Reference implementations · 레퍼런스 구현

> **EN** — Runnable, **fully anonymized** reference implementations of the patterns described in
> `../archive-blueprint/`. All data is **fictional sample data** — no real organization content.
>
> **KO** — `../archive-blueprint/`의 패턴을 **실행 가능한 익명 동작본**으로 구현한 것입니다. 데이터는
> 전부 **가짜 샘플**이며 실제 조직 콘텐츠는 없습니다.

## Contents · 구성

| Folder · 폴더 | What · 내용 |
|------|------|
| **`archive/`** | ⭐ **(primary · 주)** The "third brain" knowledge-archive engine — BM25 search server + Claude CLI, intake checker, terminal UI, and a sample `archive.html`. · 제3의뇌 아카이브 엔진(검색서버·인테이크·TUI + 샘플 HTML). |
| **`dashboard/`** | AI collaboration dashboard — concurrency-safe (append-only + id-merge) task & inquiry board. · AI 협업 대시보드(동시기록 안전 칸반·문의보드). |

## ⭐ Primary content · 주 콘텐츠
**EN** — In this repository the **knowledge archive + AI collaboration** is the primary content
(`archive/`). The dashboard is included here as a mirror reference, but it **also has its own
dedicated standalone repository**:

**KO** — 이 저장소의 **주 콘텐츠는 지식 아카이브 + AI 협업**(`archive/`)입니다. 대시보드는 여기 미러
레퍼런스로 포함하지만, **별도 전용 단독 레포로도 존재**합니다:

> 🔗 **AI Collaboration Dashboard (standalone) · 단독 레포:** https://github.com/11pyo/ai-collab-dashboard

So: for the dashboard's own home, issues, and history, use that dedicated repo. The copy here is a
convenience mirror that demonstrates the operational layer alongside the archive.
대시보드의 본거지·이슈·이력은 그 전용 레포를 사용하세요. 여기 사본은 아카이브와 함께 운영 레이어를
보여주기 위한 편의 미러입니다.

## Run · 실행
- **Archive** — `cd archive && python archive-server.py` → http://localhost:5174 (see `archive/README.md`).
- **Dashboard** — open `dashboard/task-board.html` in a browser (see `dashboard/README.md`).
