from cockpit_agent.manual import manual_retriever


def test_tpms_search_returns_tpms_section() -> None:
    results = manual_retriever.search("胎压报警是什么意思", top_k=2)
    assert results
    assert any("TPMS" in item or "胎压" in item for item in results)
