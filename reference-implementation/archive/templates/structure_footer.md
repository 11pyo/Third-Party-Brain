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
