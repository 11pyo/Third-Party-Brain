# Skills Index · 스킬 색인

> **EN**: Operational Job Manuals (Skills) built with the 3-layer architecture (Process, Toolbox, Proof). The AI agent autonomously loads, extracts, and heals these skills.  
> **KO**: 3단 레이어(프로세스, 툴박스, 증명)로 구축된 운영 업무 매뉴얼(스킬) 모음입니다. AI 에이전트가 스스로 로드하고, 추출하며, 치유합니다.

---

## Registered Skills · 등록된 스킬 목록

| Skill ID | Trigger / When to use | Deliverable | Path |
|---|---|---|---|
| `weekly-client-update` | "Prepare weekly update", "주간 보고 작성해줘" | Verified 200-word client update email | [`skills/weekly-client-update/`](./weekly-client-update/SKILL.md) |

---

## Autonomous Protocol for AI Agents · AI 자율 운영 지침

1. **Auto-Invoke**: When a user's instruction matches a trigger, load the corresponding `SKILL.md`, run its toolbox tools, and satisfy the Proof checklist prior to outputting.
2. **Self-Extraction**: When a routine task repeats $\ge 2$ times or a user approves a high-quality ad-hoc output, copy `_template/`, create `skills/<new-id>/`, and register it in this table.
3. **Self-Healing Loop**: If output contains defects, diagnose whether it failed at Process, Toolbox, or Proof. Patch the skill files and record the lesson in `notes.md`.
