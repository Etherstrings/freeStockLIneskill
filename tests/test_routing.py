from datetime import date

from freestocklineskill_runtime.routing import build_route_plan
from freestocklineskill_runtime.routing import entity_search_candidates
from freestocklineskill_runtime.routing import extract_days
from freestocklineskill_runtime.routing import extract_limit
from freestocklineskill_runtime.routing import normalize_symbol
from freestocklineskill_runtime.routing import parse_chinese_number
from freestocklineskill_runtime.routing import resolve_local_entity


def test_normalize_a_share_etf_index_and_bond_symbols():
    assert normalize_symbol("600519") == "600519.SH"
    assert normalize_symbol("300750") == "300750.SZ"
    assert normalize_symbol("920125") == "920125.BJ"
    assert normalize_symbol("510300") == "510300.SH"
    assert normalize_symbol("159915") == "159915.SZ"
    assert normalize_symbol("123456", asset_hint="bond") == "123456.SZ"
    assert normalize_symbol("sh600519") == "600519.SH"
    assert normalize_symbol("600519.SH") == "600519.SH"


def test_chinese_number_limit_and_days():
    assert parse_chinese_number("十") == 10
    assert parse_chinese_number("二十") == 20
    assert parse_chinese_number("一百零五") == 105
    assert extract_limit("成交额前二十") == 20
    assert extract_limit("top 50 涨幅榜") == 50
    assert extract_days("最近三十天走势") == 30
    assert extract_days("近半年走势") == 180


def test_route_realtime_history_market_rank_limit_and_money_flow():
    assert build_route_plan("贵州茅台最新价").command == "quote-realtime"
    history = build_route_plan("宁德时代近一个月走势")
    assert history.command == "quote-history"
    assert history.params["days"] == 30
    assert history.params["period"] == "daily"
    assert build_route_plan("今天大盘怎么样").command == "market-snapshot"
    rank = build_route_plan("A股成交额前十")
    assert rank.command == "rank"
    assert rank.params["kind"] == "amount"
    assert rank.params["limit"] == 10
    limit_pool = build_route_plan("2026-04-24 涨停池", today=date(2026, 4, 25))
    assert limit_pool.command == "limit-pool"
    assert limit_pool.params["date"] == "2026-04-24"
    money = build_route_plan("主力资金净流入前十")
    assert money.command == "money-flow"
    assert money.params["scope"] == "market"


def test_route_sector_fundamental_announcement_dragon_tiger_and_bond():
    assert build_route_plan("行业板块涨幅排行").command == "sector"
    assert build_route_plan("贵州茅台基本面").command == "fundamental"
    assert build_route_plan("宁德时代年报 PDF").command == "announcement"
    assert build_route_plan("今日龙虎榜").command == "dragon-tiger"
    bond = build_route_plan("可转债涨幅榜前十")
    assert bond.command == "bond"
    assert bond.params["action"] == "rank"


def test_resolve_local_entity_aliases():
    assert resolve_local_entity("贵州茅台最新价").symbol == "600519.SH"
    assert resolve_local_entity("上证指数现在多少").asset_type == "index"
    assert resolve_local_entity("510300 最新价").asset_type == "fund"


def test_entity_search_candidates_extract_chinese_stock_names_from_normal_questions():
    assert entity_search_candidates("海光信息最新价")[0] == "海光信息"
    assert entity_search_candidates("帮我看一下福耀玻璃最近一个月走势")[0] == "福耀玻璃"
    assert entity_search_candidates("山西汾酒公告")[0] == "山西汾酒"
    assert entity_search_candidates("主力资金净流入前十") == []
