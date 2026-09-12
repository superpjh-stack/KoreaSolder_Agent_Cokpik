from goryeo_solder_agent.data_hub import GoryeoSolderRepository


def test_demo_hub_has_trace_and_documents(tmp_path):
    repo = GoryeoSolderRepository(tmp_path / "demo.db")
    assert repo.dashboard()["active_orders"] == 3
    assert len(repo.knowledge_documents()) == 10
    assert len(repo.get_rules()) == 7
    trace = repo.get_process_trace("WO-KS-260901")
    assert trace["melting"] and trace["casting_rolling"]


def test_read_only_tools_are_whitelisted(tmp_path):
    from goryeo_solder_agent.factory_tools import GoryeoSolderToolRegistry
    import json
    result = json.loads(GoryeoSolderToolRegistry(GoryeoSolderRepository(tmp_path / "demo.db")).execute("get_material_lots", {"material_lot": None, "issues_only": True}))
    assert result["status"] == "ok" and result["demo_data"] is True
