# weekly-client-update — Weekly Operational Client Update · 주간 고객 업데이트

> **Purpose · 목적**: Generate a concise (<200 words), verified weekly status report for clients from raw campaign numbers.  
> **When to use (Trigger) · 트리거**: "Draft the weekly client update", "주간 고객 업데이트 작성해줘", "이번 주 광고 성과 보고서 써줘"  
> **Inputs & Paths · 입력 및 경로**: `metrics-summary.json`, `files/client-names.md`, `files/tone-rules.md`

---

## 1. Process Layer · 프로세스 레이어

1. **Pull Metrics**: Read `metrics-summary.json` (clicks, spend, conversions).
2. **Compare to Plan**: Identify the metric with the largest percentage delta.
3. **Drafting Order**:
   - Lead immediately with the single largest delta (no introductory filler).
   - State what moved and the exact reason why.
   - Outline the concrete action committed for next week.
4. **Tone Enforcement**: Keep it strictly under 200 words. No speculative adverbs ("tremendous", "hopefully").

---

## 2. Toolbox Layer · 툴박스 레이어

- Template: `files/update-template.md` (Bracketed structure)
- Reference: `files/client-names.md` (Exact approved spellings of client stakeholders & products)
- Rules: `files/tone-rules.md` (Banned words: "pleased to report", "synergy")
- Golden: `examples/2026-09-08-good.md` (Client-praised past deliverable)

---

## 3. Proof Layer (5 Falsifiable Tests) · 증명 레이어

- [ ] **P1. Numeric Verification**: Every number cited exists verbatim in `metrics-summary.json`.
- [ ] **P2. Zero Speculative Adjectives**: 0 instances of numbers described without underlying data.
- [ ] **P3. Word Count Constraint**: Output contains $\le 200$ words.
- [ ] **P4. Client Name Integrity**: Client name strictly matches `files/client-names.md`.
- [ ] **P5. Next Action Commitment**: Exactly one explicit next-week deliverable is stated.
