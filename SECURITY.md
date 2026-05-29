# Security Policy / 보안 정책

## This repository contains NO real operational data
This is a **public methodology (blueprint)** repository. It deliberately contains **no real operational data,
credentials, internal hostnames/IPs, personal contacts, or company-identifying information**.
The original archive (with actual operational content) is kept **private and local** — only the genericized
methodology is published here.

## When you replicate this pattern
If you build your own archive from this blueprint, **never commit**:
- Passwords, API keys, tokens, certificates
- Internal IP addresses, server names, connection strings
- Personal data or contact details (names, emails, phone numbers)
- Real operational records (actual transactions, customer data, etc.)

Keep your real archive (`archive.html`, logs, tool configs) **out of any public repository**.
Use a local/private location, and `.gitignore` anything that could leak (e.g. `conversations.jsonl`, `*.log`).

## Reporting a concern
Found sensitive data accidentally committed, or have a security concern?
- Open a **private** GitHub Security Advisory (Security → Advisories), or
- Start a thread in **Discussions** (for non-sensitive issues).

Please do **not** post secrets or real data in public issues/discussions.

---

## 이 저장소에는 실제 운영 데이터가 없습니다
여기는 **공개 방법론(블루프린트)** 저장소입니다. **실제 운영 데이터·계정·내부 IP/호스트명·개인 연락처·
회사 식별정보를 일절 포함하지 않습니다.** 실제 내용이 담긴 원본 아카이브는 **비공개·로컬**로 보관하며,
여기에는 일반화된 방법론만 공개합니다.

## 이 패턴을 복제할 때
블루프린트로 본인 아카이브를 만들 때 **절대 커밋하지 마세요**:
- 비밀번호, API 키, 토큰, 인증서
- 내부 IP·서버명·접속 문자열
- 개인정보·연락처(이름·이메일·전화번호)
- 실제 운영 기록(실제 거래·고객 데이터 등)

실제 아카이브(`archive.html`, 로그, 도구 설정)는 **공개 저장소 밖**(로컬/비공개)에 두고,
유출 가능 파일(`conversations.jsonl`, `*.log` 등)은 `.gitignore`로 차단하세요.

## 문제 신고
민감정보가 실수로 커밋됐거나 보안 우려가 있으면:
- **비공개** GitHub Security Advisory(Security → Advisories) 사용, 또는
- 민감하지 않은 사안은 **Discussions**에 작성.

공개 이슈/디스커션에 **비밀·실데이터를 올리지 마세요.**
