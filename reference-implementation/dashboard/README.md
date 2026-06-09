# 운영 대시보드 — 참조 구현 (익명 동작본)

> `archive-blueprint/07-dashboard-operating-guide`에서 **설명만** 하던 대시보드를, 실제로 **더블클릭하면 돌아가는** 익명 동작본으로 제공합니다.
> ⚠️ **여기 들어있는 모든 데이터(태스크·문의·요청자 이름)는 가상 샘플입니다.** 실제 회사 데이터는 포함되지 않습니다.

---

## 무엇인가
서버·DB·빌드 없이 **파일 4개**로 도는 운영 작업판입니다. 칸반(일회성)·정기업무(주/월/연)·문의 처리이력 3보드를 한 화면에 표시하고, 문의 로그는 **추가전용 id-병합** 방식이라 여러 세션이 동시에 기록해도 충돌하지 않습니다.

원리·규칙·상세 설계는 블루프린트 문서를 보세요:
- `archive-blueprint/07-dashboard-operating-guide.human.md` (규칙 R1~R8·사용법)
- `archive-blueprint/05-operational-layer.human.md` (왜 이런 레이어인가)

## 구성 파일

| 파일 | 역할 |
|------|------|
| `task-board.html` | **화면.** 더블클릭하면 브라우저에서 열림(서버 불요). 안에 `const TASKS=[…]` 샘플 카드 배열을 품고, `inquiry-log.js`를 `<script src>`로 읽음. |
| `tasks.md` | **정본(正本).** 프로젝트 태스크의 원본(마크다운). 화면은 이걸 미러링한 것. |
| `inquiry-log.js` | **문의 처리이력 데이터.** 추가전용 푸시로그(같은 id 재push=상태 전이 병합). |
| `log-inquiry.py` | **문의 로그 헬퍼 CLI.** 로그를 직접 편집하지 않고 이 스크립트로 한 줄씩 안전하게 덧붙임(OS 파일락). |

## 실행

```bash
# 1) 화면 보기 — task-board.html 더블클릭 (또는 브라우저로 열기)

# 2) 문의 한 건 기록 (접수 → 전이 → 완료)
python log-inquiry.py --new --type 단순문의 --q "<문의 요약>" --by <기록자> --req "<요청자·조직>"
#   → 'NEW id=INQ-YYMMDD-HHMMSS' 의 id 를 기억
python log-inquiry.py --id <그-id> --status 진행중
python log-inquiry.py --done --id <그-id> --a "<처리 요약>" --ref "#<관련-앵커>"

# 3) 브라우저 새로고침 = 반영
```

- 카드의 **✏️수정**은 이 브라우저(localStorage)에만 저장됩니다. 정본 `tasks.md`에 반영하려면 편집바의 **「변경분 내보내기(JSON)」**로 뽑아 옮깁니다.
- 완료 열은 높이 고정+스크롤이고, 열 머리의 **`⤢ 전체보기`**로 완료 카드를 큰 모달에서 모아 봅니다.

## 자기 도메인에 맞추기
1. `tasks.md` + `task-board.html`의 `const TASKS` 배열을 본인 업무 카드로 교체(둘 다 동기화).
2. `inquiry-log.js`의 샘플 push를 지우고, 실제 문의는 `log-inquiry.py`로만 덧붙임.
3. 카드 분류 색상(dev/ops/ts/adm)·정기 주기(주례/월례/연례)는 그대로 쓰거나 도메인에 맞게.

> 🔒 **공개 주의**: 이 작업판을 다시 외부에 공유한다면, `tasks.md`·`inquiry-log.js`·`task-board.html`의 `TASKS`에 들어간 **실제 고객명·문서번호·금액·실명은 반드시 가린 뒤** 공유하세요. (이 참조 구현이 그 익명화의 본보기입니다.)
