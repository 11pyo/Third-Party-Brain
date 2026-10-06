# [job-id] — [One-line Job Description · 업무명 한 줄]

> **Purpose · 목적**: [Core purpose in one sentence]  
> **When to use (Trigger) · 트리거**: [Explicit natural language triggers, e.g. "Draft weekly update", "Check overdue invoices"]  
> **Inputs & Paths · 입력 및 경로**: [Files, metrics, T-Codes, or URLs]

---

## 1. Process Layer · 프로세스 레이어
1. **Prep**: 
2. **Extraction / Query**: 
3. **Drafting / Generation**: 
4. **Decision Rules ("If X then Y")**:
   - If [condition A] -> [action A]
   - If [condition B] -> [action B]

---

## 2. Toolbox Layer · 툴박스 레이어
- Scripts: `files/[script-name].py` — [deterministic automation]
- Templates: `files/[template-name].md` — [skeleton with `[BRACKETED_PLACEHOLDERS]`]
- References: `files/[reference-data].md` — [static IDs, client names]
- Goldens: `examples/[YYYY-MM-DD-good].md` — [approved past output for tone & structure]

---

## 3. Proof Layer (Falsifiable Checklist) · 증명 레이어
*No subjective claims ("it looks good"). Must be verifiable by objective external facts.*

- [ ] **1. Exact Metrics Match**: Numbers match raw extracted files.
- [ ] **2. No Unresolved Placeholders**: Zero remaining `[PLACEHOLDER]` brackets.
- [ ] **3. Strict Identifiers**: Complies with domain nomenclature (e.g. `ID — Name`).
- [ ] **4. Falsifiable Constraints**: Length constraint, active links, or 0-diff tests satisfied.
