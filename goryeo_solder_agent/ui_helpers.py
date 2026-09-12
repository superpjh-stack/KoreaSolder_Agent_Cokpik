from datetime import datetime

QUESTION_GROUPS = {
 "지식베이스": ["원료 입고검사 절차는?","합금 배합 변경 승인 절차는?","용해 작업 전 확인사항은?","용해 공정 편차는 어떻게 검토해?","주조·압연 LOT 추적 절차는?","완료검사 기준이 없으면 어떻게 처리해?","포장 라벨 확인 절차는?","출하 승인 절차는?","원료 대체 승인 절차는?","클레임 역추적 절차는?"],
 "DB": ["현재 작업지시와 납기를 알려줘","보류된 원료 LOT를 보여줘","용해 주의 배치를 알려줘","WO-KS-260901 공정을 추적해줘","MB-260901-02 측정값은?","품질 조건부 건을 알려줘","포장 LOT 상태를 보여줘","출하 승인대기 건은?","조회 가능한 테이블과 행 수는?","raw_material_lots 테이블을 보여줘"],
 "룰": ["성적서 미첨부 규칙은?","원료 보류 규칙은?","용해 주의 규칙은?","배합 버전 미승인 규칙은?","조성 기준 미등록 규칙은?","수율 편차 규칙은?","표면검사 조건부 규칙은?","라벨 미확인 규칙은?","출하 승인대기 규칙은?","규칙별 담당자와 근거 문서는?"],
}
WELCOME_MESSAGE={"role":"assistant","content":"고려솔더 제조 현황을 근거와 함께 확인합니다.  \n현재 자료는 2026년 9월 가상 데모이며 실제 합금 조성·공정 기준은 미등록입니다.","sources":[],"evidence":[],"data_tools":[],"created_at":"시작"}
def timestamp(): return datetime.now().strftime("%H:%M")
def user_question_history(messages, limit=8): return [{"content":str(m.get("content","")),"created_at":str(m.get("created_at",""))} for m in reversed(messages) if m.get("role")=="user"][:limit]
def work_order_snapshot(repo, work_order):
    trace=repo.get_process_trace(work_order); job=trace["work_order"] or {}
    risks=[r for r in trace["readings"] if "주의" in str(r.get("status"))]
    incoming=[]
    for melt in trace["melting"]:
        incoming.extend(repo.get_material_lots(issues_only=False))
        break
    return {"job":job,"trace":trace,"risks":risks,"processes":trace["casting_rolling"],
            "press":trace["readings"],"die":trace["melting"],"incoming":incoming,
            "outgoing":trace["quality"],"shipments":trace["shipments"]}
def risk_label(snapshot):
    if not snapshot["job"]: return "미확인","⚪"
    if snapshot["risks"] or any(q.get("final_result") not in {"합격"} for q in snapshot["trace"]["quality"]): return "주의","🟠"
    return "안정","🟢"
