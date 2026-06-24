# 🧠 Third-Party-Brain

> **A project to build a "brain + hands" you can hand almost all your thinking and doing to.**
> Today, its first piece — **an AI-searchable knowledge archive ("a third brain") you run from a single file**, plus the blueprint to replicate your own.

🌐 [한국어](./README.md) · 🤖 [AGENTS.md](./AGENTS.md) · 🗂️ [AI Collaboration Dashboard](https://github.com/11pyo/ai-collab-dashboard) · 💬 [Discussions](https://github.com/11pyo/Third-Party-Brain/discussions) · 🆕 [v2.0 release](https://github.com/11pyo/Third-Party-Brain/releases/tag/v2.0)

---

## ⚡ Try it in 30 seconds — zero code, zero install

> **No dev skills needed.** Three steps:

1. **Download** — the green **`Code` ▸ `Download ZIP`** above → unzip
2. **Open** — double-click `reference-implementation/archive/archive.html` (it just opens in your browser)
3. **Write** — bottom-right **✏️ Edit** → **➕ New article** to add knowledge → **💾 Save**

No terminal, no Python, nothing. **One HTML file *is* a searchable knowledge base** — that's 90% of the value.

> Want to also **ask it in natural language** ("what do I do at the start of the month?") and get an AI answer? → [Level ②](#-three-paths-by-difficulty) below.

---

## 🚨 Why — remove the "everything stops when they leave" risk

When operational knowledge lives only in **one person's head, scattered chats, and email**, work stalls the moment they leave (*bus factor 1*).
This tool turns that knowledge into **one searchable HTML file** → the successor just **asks in natural language**, gets an answer, and is pointed to the exact source. No reading a thick manual front to back.

> This blueprint was, in fact, born during an **SAP SD operations handover** — to structure a predecessor's knowledge fast and get it reviewed.

**Other uses** — new-hire onboarding · de-risking single-person work · unifying scattered know-how · audit/compliance (procedure + rationale + history) · replicate to other teams/modules.

---

## 🎚️ Three paths by difficulty

Do only as much as you want. **① alone is genuinely useful.**

| Level | What | Needs | Who |
|-------|------|-------|-----|
| **① Just use it** | pile up knowledge in `archive.html`, keyword search | **a browser only** | **anyone (zero code)** |
| **② Turn on AI search** | "natural-language question → AI answer + auto-scroll to source" | Python + (optional) Claude CLI | one-time install |
| **③ Build your own system** | recreate an archive for your domain from scratch | the blueprint + (optional) an AI agent | yourself or AI-assisted |

<details>
<summary><b>② How to turn on AI search</b> — expand</summary>

```bash
cd reference-implementation/archive
pip install -r requirements.txt     # enables BM25 search (auto-fallback if skipped)
python archive-server.py            # → open http://localhost:5174
```
- **Windows**: double-click `run-server.bat` (it runs the two lines for you) — but install Python first from [python.org](https://www.python.org/downloads/).
- Add `--share` to share a link on your office LAN (`python archive-server.py --share`).
- The **Claude CLI is only needed for "natural-language AI answers."** Keyword search, intake, and the terminal UI all work without it.

</details>

<details>
<summary><b>③ Build your own (domain) archive</b> — expand</summary>

**Easiest — let an AI do it:** hand the folder to an AI agent (e.g. Claude Code) and say
> *"Read this `AGENTS.md` and `archive-blueprint`, then set up an archive for my ○○ work."*

The AI will **first ask you (STEP 0)** — domain · categories · a **do-not-store (sensitive) list** · code notation · synonyms, plus **the real content to fill it** (it won't invent your knowledge). Then it follows the 6 steps in [`04-replication-playbook`](./archive-blueprint/04-replication-playbook.human.md).

**Do it yourself:**
```bash
git clone https://github.com/11pyo/Third-Party-Brain.git
cd Third-Party-Brain
```
1. **Read** — [`archive-blueprint/00-INDEX.human.md`](./archive-blueprint/00-INDEX.human.md) in numeric order
2. **Understand** — `01` (architecture) → `03` (search/intake algorithms)
3. **Replicate** — the 6 steps in `04-replication-playbook` (domain params → skeleton HTML → article spec → lightweight index → 3 Python tools → validation → operating handover)

</details>

---

## 🔬 How it works & specs (the essence)

> Simple at the front, solid underneath. Here's the "why" and the core logic — expand each.

<details>
<summary><b>Why search is accurate — BM25 (Recall@1 42.9% → 81.6%)</b></summary>

- On startup, every article (title + tags + body) is tokenized into **char-2grams** and a **BM25** index is built once. A query picks the top-3 by BM25 score as evidence for the AI.
- BM25 corrects for "how distinctive a term is (IDF)" and "document length" → robust against common-code noise and long-article bias.
- **Synonym expansion is *not* used for ranking** (measurably hurt accuracy) — only to find *which passage to extract* inside the chosen articles.
- On an in-house eval (65 docs, 49 queries), top-1 hit rate went **42.9% → 81.6%** (≈2×). Auto-falls back to the old scoring if the library is missing.
- Details: [`03-algorithms-scaling`](./archive-blueprint/03-algorithms-scaling.human.md)
</details>

<details>
<summary><b>Intake that catches duplicates & contradictions before they land</b></summary>

Before adding content, automatic checks: **duplicate** (70%+ overlap) · **conflict** (reversed procedure order) · **definition divergence** (dictionary articles describing the same code very differently) · **placement** (recommends one of 5 categories). So knowledge stays consistent as it grows.
</details>

<details>
<summary><b>Obsidian-style bidirectional links · backlinks · tag filter (v2.0)</b></summary>

Adopts Obsidian's **linking patterns without the app**. Add a `data-related` attribute to an article and a **"🔗 Related" / "↩ Referenced by"** chip panel renders at the bottom automatically (one side suffices — it's bidirectional). Click a tag to search by it. Body untouched, search efficiency intact. → see the *logic/algorithm comparison table* in the [v2.0 release notes](https://github.com/11pyo/Third-Party-Brain/releases/tag/v2.0).
</details>

<details>
<summary><b>Core design principles & scaling thresholds</b></summary>

1. **Portable** — data is a single HTML file. No external DB. Copy it, opens anywhere (offline OK).
2. **Simple** — Python standard library only. One line to run (`python x.py`); non-developer friendly.
3. **Search-friendly** — every article carries search keywords (`data-tags`).
4. **Safe** — **never store** secrets: passwords, IPs, accounts, certificates, real data.
5. **Local AI** — natural-language search via a local LLM CLI. No API key/cost, no data leaving your box.

Invariants (INV1–INV9) and scaling thresholds (N ≤ 200 / 500 / 1000): [`00-INDEX`](./archive-blueprint/00-INDEX.human.md) · [`03-algorithms-scaling`](./archive-blueprint/03-algorithms-scaling.human.md).
</details>

---

## 📦 What's in this repository

A **methodology (blueprint)** + **runnable, fully anonymized reference implementations**. All data is **fictional sample data**.

```
Third-Party-Brain/
├─ README.md / README.en.md   ← entry point (KO / EN)
├─ AGENTS.md / CLAUDE.md       ← ⭐ AI auto-onboarding (functions, rules, direction)
├─ archive-blueprint/          📘 methodology (paired .human.md + .ai.md)
│  ├─ 00-INDEX               entry point · artifact map · invariants (INV) · ⛔ sync rules
│  ├─ 01-overview-architecture     overview · architecture · tech stack
│  ├─ 02-buildup-process           build-up history · common pitfalls
│  ├─ 03-algorithms-scaling   ⭐   search/intake algorithms + scaling thresholds
│  ├─ 04-replication-playbook      step-by-step: build a new archive
│  ├─ 05-operational-layer         ops layer — server-less dashboard · conflict-free log · org map
│  ├─ 06-automation-and-ops-model  automation · read-only ops safety model · disclosure tiers
│  ├─ 07-dashboard-operating-guide dashboard rules & usage
│  └─ CHANGELOG                    program/structure change history
└─ reference-implementation/   ⭐ runnable anonymized builds (fictional samples)
   ├─ archive/                 ⭐ the third-brain engine — BM25 search server · intake · TUI + sample archive.html
   └─ dashboard/               AI collaboration dashboard — standalone repo: 11pyo/ai-collab-dashboard
```

> **Why docs come in pairs**: `*.human.md` is for people (narrative, rationale); `*.ai.md` is for other AI sessions (compact, directive). Same content, two forms — point an AI at `.ai.md`, read `.human.md` yourself.

> 🔗 **Sister repo**: the AI Collaboration Dashboard also has its own standalone repository → **https://github.com/11pyo/ai-collab-dashboard** (the `dashboard/` here is a convenience mirror).

---

## 🤝 Contributing / rules for AI agents

Full list in [`AGENTS.md`](./AGENTS.md). The essentials:
- **Public repo → fictional sample data only** (no real names/customers/T-Codes/secrets — see [`SECURITY.md`](./SECURITY.md))
- **Bilingual docs** (Korean + English)
- **Blueprint sync** on any program/structure change (`*.ai.md` + `*.human.md` + `CHANGELOG.*`)
- **Dashboard log is append-only** — use `log-inquiry.py`, never hand-edit `inquiry-log.js`

---

## 📄 License

**MIT License** ([`LICENSE`](./LICENSE)) — copy, modify, distribute, and adapt freely; keep the copyright notice; no warranty. Fill in your own categories, synonyms, and articles for your domain. When publishing, always keep the **no-sensitive-data** principle (accounts, passwords, internal IPs, contacts, real data must not be included).
