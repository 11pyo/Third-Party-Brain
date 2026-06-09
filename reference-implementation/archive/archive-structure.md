# archive.html — structure map (read this before editing the archive)

This file is the **blueprint** for `archive.html`. The tools (`archive-server.py`,
`archive-intake.py`, `archive-menu.py`) parse the archive by regex, so the HTML
**shape matters**. Keep this map in sync whenever you add/remove/move an article.

> The shipped `archive.html` is a small, fully **fictional sample**. Replace its
> articles with your own knowledge base — just keep the structure below.

---

## Article counts (sample) — 9 articles / 5 categories

| Category | Badge text | Badge class | Count | Article ids |
|----------|-----------|-------------|-------|-------------|
| 기초용어 (Basics) | `기초용어` | `b-기초` | 3 | `order-type-io`, `tcode-master`, `ztsd-tables` |
| 프로세스 (Process) | `프로세스` | `b-프로세스` | 2 | `base-order-flow`, `proc-sales-cancel` |
| 기술설정 (Tech) | `기술설정` | `b-기술` | 1 | `month-end-closing` |
| 트러블슈팅 (Troubleshooting) | `트러블슈팅` | `b-트러블` | 2 | `ts-tax-invoice`, `ts-credit-check` |
| 운영참조매뉴얼 (Manual) | `운영참조매뉴얼` | `b-매뉴얼` | 1 | `ops-system-env` |

---

## Article HTML pattern (what the parser expects)

Each article **must** follow this shape — the tools key off `id`, `class="at"`,
`class="badge…"`, `class="db"`, and `data-tags`:

```html
<article class="article" id="UNIQUE-ID" data-tags="space separated keywords for search">
  <div class="ah">
    <div class="at">Article Title</div>
    <span class="badge b-기초">기초용어</span>   <!-- badge text = category name -->
    <span class="db">2026-01-10</span>            <!-- date -->
  </div>
  <div class="tags"><span class="tag">keyword</span></div>
  <div class="sec">
    <div class="st">Section title</div>
    <div class="dt"><p>Body…</p></div>
  </div>
</article>
```

**Why each part matters**
- `id` — anchor target; the AI panel scrolls/highlights by this id.
- `data-tags` — boosts search recall (title + tags are weighted in BM25).
- `class="at"` — title extraction.
- `class="badge…">TEXT` — the **text** is the category; the class (`b-기초` etc.) is just color.
- `class="db"` — date, used by the TUI's "recent updates".

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
