from __future__ import annotations
import json


def nullable(description): return {"type": ["string", "null"], "description": description}


class GoryeoSolderToolRegistry:
    def __init__(self, repository):
        self.repository = repository
        self.handlers = {
            "get_work_orders": repository.get_work_orders,
            "get_material_lots": repository.get_material_lots,
            "get_melting_status": repository.get_melting_status,
            "get_process_trace": repository.get_process_trace,
            "get_quality_status": repository.get_quality_status,
            "get_shipment_status": repository.get_shipment_status,
            "search_knowledge": repository.search_knowledge,
            "get_rules": repository.get_rules,
            "list_tables": repository.table_inventory,
            "browse_table": repository.table_records,
        }

    @property
    def definitions(self):
        specs = [
            ("get_work_orders", "작업지시와 납기·진척을 조회한다.", {"work_order": nullable("작업지시, 전체 null"), "status": nullable("상태, 전체 null")}),
            ("get_material_lots", "원료 LOT·성적서·수입검사·보류를 조회한다.", {"material_lot": nullable("원료 LOT, 전체 null"), "issues_only": {"type":"boolean"}}),
            ("get_melting_status", "용해 배치와 가상 공정 측정값을 조회한다.", {"melt_batch": nullable("용해 배치, 전체 null"), "alerts_only": {"type":"boolean"}}),
            ("get_process_trace", "작업지시의 용해·주조·압연·검사·포장·출하 계보를 조회한다.", {"work_order": {"type":"string"}}),
            ("get_quality_status", "공정·완료 품질검사를 조회한다.", {"work_order": nullable("작업지시, 전체 null"), "issues_only": {"type":"boolean"}}),
            ("get_shipment_status", "포장 LOT와 출하 검토 상태를 조회한다.", {"work_order": nullable("작업지시, 전체 null")}),
            ("search_knowledge", "절차·기준·승인 문서를 검색한다.", {"query":{"type":"string"}, "limit":{"type":"integer","minimum":1,"maximum":20}}),
            ("get_rules", "데모 확인 규칙을 조회한다.", {"query": nullable("검색어, 전체 null")}),
            ("list_tables", "허용된 테이블과 행 수를 조회한다.", {}),
            ("browse_table", "허용 테이블을 읽기 전용 조회한다.", {"table_name":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":100},"offset":{"type":"integer","minimum":0}}),
        ]
        return [{"type":"function","name":n,"description":d,"strict":True,"parameters":{"type":"object","properties":p,"required":list(p),"additionalProperties":False}} for n,d,p in specs]

    def execute(self, name, arguments):
        if name not in self.handlers: return json.dumps({"error":f"허용되지 않은 도구: {name}","tool":name}, ensure_ascii=False)
        try:
            values = json.loads(arguments) if isinstance(arguments, str) else arguments
            if not isinstance(values, dict): raise ValueError("도구 인자는 객체여야 합니다.")
            return json.dumps({"status":"ok","demo_data":True,"source":"고려솔더 Data Hub · 가상 데모","tool":name,"result":self.handlers[name](**values)}, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"error":str(exc),"tool":name}, ensure_ascii=False)
