// ── 일반·단순·긴급 문의 처리 이력 (append-only 푸시로그, id 병합) ─────
// 한 줄 = push 1개. 같은 id로 나중에 push하면 필드 병합(덮어쓰기) → 상태 전이 기록.
// 추가: log-inquiry.py 로 append (직접 편집 금지, 헬퍼 사용).
//   ① 접수:  python log-inquiry.py --new --type 단순문의 --q "..." --by 담당자 --req "요청자·조직"  → id 출력
//   ② 전이:  python log-inquiry.py --id <그id> --status 진행중|대기
//   ③ 완료:  python log-inquiry.py --done --id <그id> --a "처리/답변" --ref "#앵커"
// 필드: {id, date, type, q, a, by(기록담당), req(요청자·조직), ref, status:"접수"|"진행중"|"대기"|"완료"}
// ⚠️ 아래는 전부 가상 샘플입니다.
window.INQUIRY_LOG = window.INQUIRY_LOG || [];

// 예시 A — 단순문의: 접수 → 진행중 → 완료 (같은 id로 3줄 append, 렌더 시 병합)
window.INQUIRY_LOG.push({id:"INQ-260601-100000", date:"2026-06-01", type:"단순문의", q:"사용자 계정 조회 방법 문의", by:"담당자", req:"영업팀 A매니저", status:"접수"});
window.INQUIRY_LOG.push({id:"INQ-260601-100000", status:"진행중"});
window.INQUIRY_LOG.push({id:"INQ-260601-100000", status:"완료", a:"표준 사용자 조회 트랜잭션으로 안내 — 시스템 변경 없이 종료", ref:"#some-article"});

// 예시 B — 일반요청: 접수 → 대기 (담당 부서 회신 대기)
window.INQUIRY_LOG.push({id:"INQ-260601-110000", date:"2026-06-01", type:"일반요청", q:"리포트 추출 권한 요청", by:"담당자", req:"기획팀 B담당", status:"접수"});
window.INQUIRY_LOG.push({id:"INQ-260601-110000", status:"대기"});

// 예시 C — 긴급문의: 접수+즉답 동시 완료 (id-merge 2줄)
window.INQUIRY_LOG.push({id:"INQ-260602-090000", date:"2026-06-02", type:"긴급문의", q:"마감 중 특정 화면 오류 — 긴급", by:"담당자", req:"회계팀", status:"접수"});
window.INQUIRY_LOG.push({id:"INQ-260602-090000", status:"완료", a:"입력값 형식 오류로 확인 → 표준 양식으로 정정해 해결", ref:"#some-article"});

// 예시 D — 단순문의: 접수 상태 그대로 ('접수' 열 시연)
window.INQUIRY_LOG.push({id:"INQ-260603-101500", date:"2026-06-03", type:"단순문의", q:"권한 그룹 차이 문의", by:"담당자", req:"영업팀 A매니저", status:"접수"});

// 예시 E — 일반요청: 접수 → 진행중 (처리 중, '진행중' 열 시연)
window.INQUIRY_LOG.push({id:"INQ-260603-140000", date:"2026-06-03", type:"일반요청", q:"신규 사용자 화면 구성 요청", by:"담당자", req:"C팀", status:"접수"});
window.INQUIRY_LOG.push({id:"INQ-260603-140000", status:"진행중"});
