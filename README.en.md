# Third-Party-Brain

**🌐 Language: [한국어](./README.md) · English (this page)** · 🤖 [AGENTS.md](./AGENTS.md) · 💬 [Discussions](https://github.com/11pyo/Third-Party-Brain/discussions)

> **A blueprint (methodology) — plus runnable reference implementations — for building, running,
> and replicating an AI-indexable operational knowledge archive, from scratch.**

> 🌍 **Domain-agnostic — not SAP-specific.** The worked example happens to be SAP SD operations, so
> you'll see some SAP terms (T-Codes, etc.) in the samples — but **the pattern works for any team,
> module, company, or topic**: IT runbooks, HR procedures, a support FAQ, research notes, a team wiki.
> *Just fill it with your own domain's terms.*

A lightweight, portable pattern for an internal knowledge archive that runs on **a few files** — no
heavy database, no server install. It's one HTML file (data + UI + search), a few Python tools, and
local-AI natural-language search. The origin case is an SAP SD operations archive (an example
domain); the pattern applies just as well to other ERP modules, teams, companies, or a general
internal wiki.

The **primary content here is the knowledge archive + AI collaboration**.

---

## 🤖 Build / run with an AI
Clone, then hand the folder to your AI assistant and say: **"Read `AGENTS.md` and set this up / run it."**
A fresh AI session auto-onboards via `AGENTS.md` (+ `CLAUDE.md`) and does the intended thing:
- **Run the reference implementations** — `reference-implementation/dashboard/` opens in a browser
  (**no build**); `reference-implementation/archive/` is `pip install -r requirements.txt` then
  `python archive-server.py`.
- **Replicate a new archive** for your own domain — follow `archive-blueprint/04-replication-playbook`.
  - The AI first **asks you for (STEP 0)**: the domain · categories · a **do-not-store (sensitive) list** · code notation · synonyms — and **the real content to fill it** (it won't invent your knowledge). Plus statuses/classification/task data if you use the dashboard.

**Prereqs:** Python 3.8+ (archive search server). The archive's *natural-language AI answer* feature
also needs a local `claude` CLI — search/intake/dashboard work without it.

---

## 💡 Where this shines (use cases)

### 🚨 When someone leaves suddenly — closing the handover gap
If operational knowledge lives only in **one person's head, scattered chats, and email**, work stalls
the moment they leave (*bus factor 1*). This archive pattern removes that risk structurally.

- **Before they leave:** the departing expert piles up T-Codes, procedures, troubleshooting, and
  contact maps as articles → it becomes **one searchable HTML file**.
- **After they leave:** the successor just **asks in natural language** ("what do I do at the start
  of the month?") and a local AI answers from the archive and points to the exact source — no need
  to read a thick manual front to back.
- **Validation:** right before leaving, share **a single link** (same network) so the predecessor can
  quickly review the successor's archive.

> This blueprint was, in fact, born during an **SAP SD operations handover** — to structure a
> predecessor's knowledge fast and get it reviewed.

### Other uses
- **New-hire onboarding** — the archive answers "how do I handle this?" instead of a senior person.
- **De-risking single-person work** — turn tacit knowledge into a searchable asset.
- **Unifying scattered knowledge** — chat/email/personal notes → one place.
- **Audit / compliance** — preserve procedures and rationale with dates and history.
- **Scale to other teams/modules** — replicate the pattern to MM, FI, HR, etc.

---

## What's in this repository

This repo is a **methodology (blueprint)** plus **runnable, fully anonymized reference
implementations**. You can either re-create the tools yourself by following the design/algorithms/
playbook, or just run the reference implementations directly. All data is fictional sample data.

```
Third-Party-Brain/
├─ README.md / README.en.md   ← entry point (KO / EN)
├─ AGENTS.md / CLAUDE.md       ← ⭐ AI auto-onboarding (functions, rules, direction)
├─ archive-blueprint/
│  ├─ 00-INDEX.*            entry point · artifact map · invariants (INV) · ⛔ sync rules
│  ├─ 01-overview-architecture.*   overview · architecture · tech stack
│  ├─ 02-buildup-process.*         build-up history · common pitfalls
│  ├─ 03-algorithms-scaling.*  ⭐  search/intake algorithms + scaling thresholds
│  ├─ 04-replication-playbook.*    step-by-step: build a new archive
│  ├─ 05-operational-layer.*       ops layer — server-less dashboard · conflict-free log · org map
│  ├─ 06-automation-and-ops-model.*  automation · read-only ops safety model · disclosure tiers
│  ├─ 07-dashboard-operating-guide.*  dashboard rules & usage (inquiry-log CLI · append-only id-merge)
│  └─ CHANGELOG.*                  program/structure change history
└─ reference-implementation/    ⭐ runnable anonymized builds (fictional samples)
   ├─ archive/                ⭐ the third-brain archive engine — BM25 search server · intake · TUI + sample archive.html
   └─ dashboard/              AI collaboration dashboard (ch. 07) — standalone repo: 11pyo/ai-collab-dashboard
```

> 🔗 **Sister repo:** the AI Collaboration Dashboard also has its own dedicated standalone
> repository — **https://github.com/11pyo/ai-collab-dashboard** . The copy under
> `reference-implementation/dashboard/` is a convenience mirror.

### Docs come in pairs (AI + human)
- **`*.ai.md`** — for **AI agents** in other sessions. Compact, directive, structured (with metadata).
- **`*.human.md`** — for **people**. Narrative, with background and rationale.

> Same content, two forms. To have an AI do the work after cloning, point it at the `.ai.md`; to
> understand it yourself, read the `.human.md`.

---

## Quick start — clone and build the same thing

```bash
git clone <this repo URL>
cd Third-Party-Brain
```

1. **Onboard** — read [`AGENTS.md`](./AGENTS.md) (auto-loaded by Claude Code via `CLAUDE.md`).
2. **Read** — `archive-blueprint/00-INDEX.*` in numeric order.
3. **Understand** — `01` (architecture) → `03` (search/intake algorithms).
4. **Replicate** — follow the 6 steps in `04-replication-playbook.*`:
   - Step 0: collect domain parameters (categories · synonyms · sensitive-info list · code notation)
   - Step 1: empty skeleton HTML (inline CSS components + sidebar)
   - Step 2: article spec `<article id data-tags>`
   - Step 3: a lightweight index (`*-structure.md`)
   - Step 4: the three Python tools (search server · intake · menu) + domain parameterization
   - Step 5: validation (search · intake · server · LAN, ≥3 cases)
   - Step 6: hand over the operating discipline
5. **Run it now** — `reference-implementation/archive/` (search engine) and
   `reference-implementation/dashboard/` (board). Each has its own README.

---

## Core design principles

1. **Portable** — data is a single HTML file. No external DB. Copy it and it opens anywhere (offline OK).
2. **Simple** — Python standard library only. One line to run (`python x.py`); non-developer friendly.
3. **Search-friendly** — every article carries search keywords (`data-tags`). Easy for people and AI.
4. **Safe** — **never store** secrets: passwords, IPs, accounts, certificates, real data.
5. **Local AI** — natural-language search via a local LLM CLI. No API key/cost, no data leaving your box.

Invariants (INV1–INV9) and scaling thresholds (N ≤ 200 / 500 / 1000) are in `00-INDEX` and
`03-algorithms-scaling`.

---

## Rules for contributors / AI agents

See [`AGENTS.md`](./AGENTS.md) for the full list. The essentials:
- **Public repo → fictional sample data only** (no real names/customers/T-Codes/secrets — see `SECURITY.md`).
- **Bilingual docs** (Korean + English).
- **Blueprint sync** on any program/structure change (update `*.ai.md`+`*.human.md` + `CHANGELOG.*`).
- **Dashboard log is append-only** — use `log-inquiry.py`, never hand-edit `inquiry-log.js`.

---

## License / use

**MIT License** ([`LICENSE`](./LICENSE)) — copy, modify, distribute, and adapt freely; keep the
copyright notice; no warranty. Fill in your own categories, synonyms, and articles for your domain.
When publishing, always keep the **no-sensitive-data** principle (accounts, passwords, internal IPs,
contacts, real data must not be included).
