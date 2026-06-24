# 🧠 Third-Party-Brain

> **거의 모든 생각과 수행을 AI에게 맡기는 "뇌 + 손발"을 만드는 프로젝트.**
> 그 첫 조각 — **파일 하나로 바로 쓰는** AI 검색 지식 아카이브("제3의 뇌")와, 내 것으로 복제하는 방법론.

🌐 [English](./README.en.md) · 🤖 [AGENTS.md](./AGENTS.md) · 🗂️ [AI 협업 대시보드](https://github.com/11pyo/ai-collab-dashboard) · 💬 [Discussions (질문·피드백)](https://github.com/11pyo/Third-Party-Brain/discussions) · 🆕 [v2.0 릴리스](https://github.com/11pyo/Third-Party-Brain/releases/tag/v2.0)

---

## ⚡ 30초 체험 — 코딩·설치 0

> **개발 몰라도 됩니다.** 이 3단계면 끝:

1. **내려받기** — 이 페이지 위 초록색 **`Code` ▸ `Download ZIP`** → 압축 풀기
2. **열기** — `reference-implementation/archive/archive.html` **더블클릭** (그냥 브라우저에서 열립니다)
3. **쓰기** — 우하단 **✏️ 편집** → **➕ 새 글**로 지식 추가 → **💾 저장**

터미널도, 파이썬도, 그 무엇도 필요 없습니다. **HTML 파일 하나가 곧 검색되는 지식창고**입니다 — 이게 전체 가치의 90%.

> 여기에 더해 *"월초에 뭐 해요?"* 처럼 **자연어로 AI에게 물어보는 검색**까지 원하면 → 아래 [난이도 ②](#-난이도별-3가지-경로).

---

## 🚨 왜 쓰나 — "그 사람 없으면 멈추는" 위험을 없앤다

운영 지식이 **한 사람 머릿속·흩어진 메신저·메일**에만 있으면, 그 사람이 떠나는 순간 업무가 멈춥니다 (이른바 *버스 팩터 1*).
이 도구는 그 지식을 **검색되는 HTML 한 장**으로 바꿉니다 → 후임은 **자연어로 물어** 답을 얻고, 원문 위치까지 바로 안내받습니다. 두꺼운 매뉴얼을 처음부터 읽지 않아도 됩니다.

> 실제로 이 블루프린트는 **SAP SD 운영 담당 인수인계** 과정에서, 선임의 지식을 빠르게 구조화하고 검증받으려고 만들어졌습니다.

**그 밖의 쓰임** — 신규 입사자 온보딩 · 1인 의존 업무 분산 · 흩어진 노하우 단일화 · 감사·규정 대응(절차+근거+이력 보존) · 다른 부서/모듈로 복제.

---

## 🎚️ 난이도별 3가지 경로

원하는 만큼만 하면 됩니다. **①만 해도 충분히 쓸모 있습니다.**

| 단계 | 무엇을 | 필요한 것 | 대상 |
|------|--------|-----------|------|
| **① 그냥 쓰기** | `archive.html`에 지식 쌓고 키워드 검색 | **브라우저만** | **누구나 (코딩 0)** |
| **② AI 검색 켜기** | "자연어 질문 → AI 답변 + 원문 자동 이동" | Python 설치 + (선택) Claude CLI | 한 번만 설치 |
| **③ 내 시스템 구축** | 내 도메인 아카이브를 0부터 재현 | 블루프린트 + (선택) AI 에이전트 | 직접 또는 AI 대행 |

<details>
<summary><b>② AI 검색 켜는 법</b> — 펼치기</summary>

```bash
cd reference-implementation/archive
pip install -r requirements.txt     # BM25 검색 활성화 (미설치 시 자동 폴백)
python archive-server.py            # → http://localhost:5174 접속
```
- **Windows**: `run-server.bat` **더블클릭**이면 위 두 줄을 대신 해줍니다 (단, Python은 [python.org](https://www.python.org/downloads/)에서 먼저 설치).
- `--share` 를 붙이면 같은 사무실 LAN에 링크 공유 (`python archive-server.py --share`).
- **Claude CLI는 "자연어 AI 답변"에만** 필요합니다. 키워드 검색·인테이크·터미널 UI는 CLI 없이도 동작합니다.

</details>

<details>
<summary><b>③ 내 시스템(내 도메인 아카이브) 구축</b> — 펼치기</summary>

**가장 쉬운 길 — AI에게 맡기기:** 폴더를 AI 에이전트(예: Claude Code)에게 주고
> *"이 `AGENTS.md`와 `archive-blueprint` 읽고, 내 ○○ 업무용 아카이브 셋업해줘"*

라고 하면, AI가 **먼저 당신에게 묻습니다(STEP 0)** — 주제(도메인)·카테고리·**민감정보 금지목록**·코드 표기·동의어, 그리고 **실제로 채울 지식 내용**(지어내지 않습니다). 이후 [`04-replication-playbook`](./archive-blueprint/04-replication-playbook.human.md)의 6단계대로 만들어 줍니다.

**직접 하려면:**
```bash
git clone https://github.com/11pyo/Third-Party-Brain.git
cd Third-Party-Brain
```
1. **읽기** — [`archive-blueprint/00-INDEX.human.md`](./archive-blueprint/00-INDEX.human.md)부터 번호 순서대로
2. **이해** — `01`(아키텍처) → `03`(검색/인테이크 알고리즘)
3. **복제** — `04-replication-playbook`의 6단계(도메인 파라미터 → 골격 HTML → 아티클 규격 → 경량 인덱스 → 파이썬 도구 3종 → 검증 → 운영 인계)

</details>

---

## 🔬 작동 원리 & 기술 스펙 (에센스)

> 대문은 단순하지만 속은 단단합니다. 아래는 "왜 이렇게 만들었나"와 핵심 로직 — 펼쳐 보세요.

<details>
<summary><b>검색이 왜 정확한가 — BM25 (Recall@1 42.9% → 81.6%)</b></summary>

- 서버 기동 시 모든 아티클(제목+태그+본문)을 **char-2gram**으로 토큰화 → **BM25** 색인 1회 구축. 질의가 들어오면 BM25 점수 상위 3개를 골라 AI에게 근거로 넘깁니다.
- BM25는 "단어가 전체에서 얼마나 특이한가(IDF)"와 "글 길이"를 함께 보정 → 흔한 코드 노이즈·긴 글 편향에 강함.
- **동의어 확장은 *랭킹*엔 안 씁니다** (실측상 정확도 하락) — 고른 글 안에서 *어디를 발췌할지* 찾을 때만 사용.
- 자체 오프라인 평가(65문서·49질의)에서 정답 1순위 적중률 **42.9% → 81.6%**(거의 2배). 라이브러리 없으면 옛 방식으로 자동 폴백.
- 상세: [`03-algorithms-scaling`](./archive-blueprint/03-algorithms-scaling.human.md)
</details>

<details>
<summary><b>중복·모순을 추가 전에 잡는 인테이크</b></summary>

새 내용을 넣기 전 자동 점검: **중복**(기존과 70%+ 겹침) · **충돌**(절차 순서 역전) · **정의 불일치**(사전 글끼리 같은 코드의 설명이 크게 다름) · **배치 추천**(5개 카테고리 중). → 지식이 쌓여도 서로 어긋나지 않게.
</details>

<details>
<summary><b>Obsidian식 양방향 링크 · backlink · 태그 필터 (v2.0)</b></summary>

Obsidian 앱 없이 그 **연결 패턴만** 흡수. 각 글에 `data-related` 속성만 더하면, 글 하단에 **「🔗 관련」 / 「↩ 여기를 참조」** 칩이 자동으로 달립니다(한쪽만 적어도 양방향). 태그 클릭=그 태그로 검색. 본문 무손상·검색 효율 그대로. → [v2.0 릴리스 노트](https://github.com/11pyo/Third-Party-Brain/releases/tag/v2.0)에 *로직·알고리즘 비교표*까지.
</details>

<details>
<summary><b>핵심 설계 원칙 & 확장 임계점</b></summary>

1. **이식성** — 데이터는 단일 HTML. 외부 DB 없음. 복사만 하면 어디서든 열림(오프라인 OK).
2. **단순함** — 파이썬 표준 라이브러리만. `python x.py` 한 줄(비개발자 친화).
3. **검색 친화** — 모든 아티클에 검색 키워드(`data-tags`).
4. **안전** — 비밀번호·IP·계정·인증서 등 **민감정보 절대 미저장**.
5. **로컬 AI 결합** — 로컬 LLM CLI로 자연어 검색. API 키·비용·데이터 유출 없음.

불변식(INV1~INV9)·규모별 확장 임계점(N≤200 / 500 / 1000)은 [`00-INDEX`](./archive-blueprint/00-INDEX.human.md)·[`03-algorithms-scaling`](./archive-blueprint/03-algorithms-scaling.human.md).
</details>

---

## 📦 저장소 구조

**방법론(블루프린트)** + **바로 도는 익명 레퍼런스 구현**으로 구성됩니다. 데이터는 전부 **가상 샘플**입니다.

```
Third-Party-Brain/
├─ README.md / README.en.md   ← 시작점 (KO / EN)
├─ AGENTS.md / CLAUDE.md       ← ⭐ AI 자동 온보딩 (기능·룰·방향)
├─ archive-blueprint/          📘 방법론 (사람용 .human.md + AI용 .ai.md 2벌씩)
│  ├─ 00-INDEX               진입점 · 아티팩트 맵 · 불변식(INV) · ⛔동기화 지침
│  ├─ 01-overview-architecture     개요 · 아키텍처 · 기술스택
│  ├─ 02-buildup-process           구축 이력 · 흔한 함정
│  ├─ 03-algorithms-scaling   ⭐   검색·인테이크 알고리즘 + 확장 임계점
│  ├─ 04-replication-playbook      새 아카이브 만들기 단계별 절차
│  ├─ 05-operational-layer         운영 레이어 — 무서버 대시보드·충돌없는 로그·조직맵
│  ├─ 06-automation-and-ops-model  자동화·읽기전용 운영 안전모델·공개수준 계층
│  ├─ 07-dashboard-operating-guide 대시보드 운영 규칙 & 사용법
│  └─ CHANGELOG                    프로그램·구조 변경 이력
└─ reference-implementation/   ⭐ 바로 도는 익명 동작본 (가상 샘플)
   ├─ archive/                 ⭐ 제3의뇌 엔진 — BM25 검색서버·인테이크·TUI + 샘플 archive.html
   └─ dashboard/               AI 협업 대시보드 — 별도 전용 레포: 11pyo/ai-collab-dashboard
```

> **문서가 2벌씩인 이유**: `*.human.md`는 사람이 읽는 용(배경·이유 서술), `*.ai.md`는 다른 AI 세션이 읽는 용(압축·지시형). 같은 내용의 다른 표현 — AI에게 맡길 땐 `.ai.md`, 직접 이해할 땐 `.human.md`.

> 🔗 **자매 레포**: AI 협업 대시보드는 별도 전용 저장소로도 존재 → **https://github.com/11pyo/ai-collab-dashboard** (이 안의 `dashboard/`는 편의용 미러).

---

## 🤝 기여 / AI 에이전트 규칙

전체는 [`AGENTS.md`](./AGENTS.md). 핵심만:
- **공개 레포 → 가상 샘플 데이터만** (실명·고객·실 T-Code·자격증명 금지 — [`SECURITY.md`](./SECURITY.md))
- **문서는 한/영 병기**
- **프로그램·구조 변경 시 블루프린트 동기화** (`*.ai.md`+`*.human.md` + `CHANGELOG.*`)
- **대시보드 로그는 추가전용** — `log-inquiry.py`로만, `inquiry-log.js` 직접 편집 금지

---

## 📄 라이선스

**MIT License** ([`LICENSE`](./LICENSE)) — 자유롭게 복제·수정·배포·응용 가능. 저작권 표시만 유지, 무보증.
본인 도메인에 맞춰 카테고리·동의어·아티클을 새로 채우세요. 공개 시 **민감정보(계정·비번·내부 IP·연락처·실데이터) 미포함** 원칙을 반드시 지키세요.
