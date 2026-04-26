from datetime import date
import json

from freestocklineskill_runtime.cli import run_command
from freestocklineskill_runtime.cli import handle_smart_query
from freestocklineskill_runtime.envelope import success
from freestocklineskill_runtime.routing import entity_from_symbol


def test_endpoint_list_returns_catalog():
    result = run_command(["endpoint-list"])

    assert result["ok"] is True
    names = [item["name"] for item in result["data"]["endpoints"]]
    assert "smart-query" in names
    assert "fundamental" in names
    assert "bond" in names


def test_search_entity_local_alias_does_not_need_network():
    result = run_command(["search-entity", "--query", "贵州茅台"])

    assert result["ok"] is True
    assert result["data"]["symbol"] == "600519.SH"
    assert result["source_chain"][0]["source"] == "local_alias"


def test_smart_query_unknown_entity_returns_json_failure():
    result = run_command(["smart-query", "--query", "这家公司基本面怎么样"])

    assert result["ok"] is False
    assert result["error"]["type"] == "entity_not_found"
    assert "hints" in result["data"]


class EntitySearchClient:
    def __init__(self):
        self.search_queries = []

    def search_entity(self, query):
        self.search_queries.append(query)
        mapping = {
            "海光信息": entity_from_symbol(query, "688041.SH", name="海光信息", query=query),
            "山西汾酒": entity_from_symbol(query, "600809.SH", name="山西汾酒", query=query),
        }
        if query not in mapping:
            raise RuntimeError("not found")
        return {"entity": mapping[query], "source_chain": [{"source": "fake_suggest", "ok": True}], "warnings": []}

    def quote_realtime(self, entity):
        return {"data": {"symbol": entity.symbol, "name": entity.name}, "source_chain": [{"source": "fake_quote", "ok": True}], "warnings": []}

    def announcement(self, entity, keyword, limit):
        return {
            "data": {"symbol": entity.symbol if entity else None, "keyword": keyword, "items": []},
            "source_chain": [{"source": "fake_announcement", "ok": True}],
            "warnings": [],
        }


def test_smart_query_extracts_remote_chinese_name_before_searching():
    client = EntitySearchClient()

    result = handle_smart_query(client, "海光信息最新价")

    assert result["ok"] is True
    assert client.search_queries == ["海光信息"]
    assert result["normalized"]["entity"]["symbol"] == "688041.SH"


def test_smart_query_uses_extracted_entity_for_announcement():
    client = EntitySearchClient()

    result = handle_smart_query(client, "山西汾酒公告")

    assert result["ok"] is True
    assert client.search_queries == ["山西汾酒"]
    assert result["normalized"]["entity"]["symbol"] == "600809.SH"
    assert result["data"]["symbol"] == "600809.SH"


def test_envelope_sanitizes_public_source_date_values_for_json_output():
    result = success(intent="demo", data={"items": [{"date": date(2026, 4, 24)}]})

    encoded = json.dumps(result, ensure_ascii=False)

    assert "2026-04-24" in encoded
