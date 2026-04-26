from dataclasses import dataclass
from typing import Any, Dict, Optional

from freestocklineskill_runtime.cli import handle_smart_query
from freestocklineskill_runtime.routing import entity_from_symbol


FRESH_ENTITIES = {
    "海天味业": ("603288.SH", "海天味业"),
    "三一重工": ("600031.SH", "三一重工"),
    "牧原股份": ("002714.SZ", "牧原股份"),
    "韦尔股份": ("603501.SH", "韦尔股份"),
    "中国船舶": ("600150.SH", "中国船舶"),
    "船舶": ("600150.SH", "中国船舶"),
    "赛力斯": ("601127.SH", "赛力斯"),
    "工业富联": ("601138.SH", "工业富联"),
    "阳光电源": ("300274.SZ", "阳光电源"),
    "爱尔眼科": ("300015.SZ", "爱尔眼科"),
    "中国神华": ("601088.SH", "中国神华"),
    "长城汽车": ("601633.SH", "长城汽车"),
    "保利发展": ("600048.SH", "保利发展"),
    "中际旭创": ("300308.SZ", "中际旭创"),
    "新易盛": ("300502.SZ", "新易盛"),
    "江淮汽车": ("600418.SH", "江淮汽车"),
    "北方华创": ("002371.SZ", "北方华创"),
    "中微公司": ("688012.SH", "中微公司"),
    "中航沈飞": ("600760.SH", "中航沈飞"),
    "歌尔股份": ("002241.SZ", "歌尔股份"),
    "海螺水泥": ("600585.SH", "海螺水泥"),
}


@dataclass(frozen=True)
class FreshCase:
    query: str
    command: str
    symbol: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    no_entity: bool = False
    ok: bool = True


class FreshClient:
    def search_entity(self, query):
        if query not in FRESH_ENTITIES:
            raise RuntimeError("not found: %s" % query)
        symbol, name = FRESH_ENTITIES[query]
        return {
            "entity": entity_from_symbol(query, symbol, name=name, query=query),
            "source_chain": [{"source": "fresh_fake", "ok": True, "query": query}],
            "warnings": [],
        }

    def quote_realtime(self, entity):
        return _result({"symbol": entity.symbol})

    def quote_history(self, entity, *, days, period, adjust):
        return _result({"symbol": entity.symbol, "days": days, "period": period, "adjust": adjust})

    def market_snapshot(self):
        return _result({"indices": [], "breadth": {}})

    def rank(self, kind, limit, order="desc"):
        return _result({"kind": kind, "limit": limit, "order": order, "items": []})

    def limit_pool(self, kind, query_date, limit):
        return _result({"kind": kind, "date": query_date, "limit": limit, "items": []})

    def money_flow(self, scope, period, entity, limit):
        return _result({"scope": scope, "symbol": entity.symbol if entity else None, "items": []})

    def sector(self, kind, action, entity, query, limit):
        return _result({"kind": kind, "action": action, "symbol": entity.symbol if entity else None, "items": []})

    def fundamental(self, entity, pack):
        return _result({"symbol": entity.symbol, "pack": pack})

    def announcement(self, entity, keyword, limit):
        return _result({"symbol": entity.symbol if entity else None, "keyword": keyword, "items": []})

    def dragon_tiger(self, query_date, entity, limit):
        return _result({"date": query_date, "symbol": entity.symbol if entity else None, "items": []})

    def news(self, entity, keyword, kind, limit):
        return _result({"symbol": entity.symbol if entity else None, "kind": kind, "keyword": keyword, "items": []})

    def chip(self, entity, limit):
        return _result({"symbol": entity.symbol, "items": []})

    def block_trade(self, query_date, entity, limit):
        return _result({"date": query_date, "symbol": entity.symbol if entity else None, "items": []})

    def margin_trading(self, query_date, entity, limit):
        return _result({"date": query_date, "symbol": entity.symbol if entity else None, "items": []})

    def bond(self, action, entity, limit, days):
        return _result({"action": action, "symbol": entity.symbol if entity else None, "items": []})


def _result(data):
    return {"data": data, "source_chain": [{"source": "fresh_fake", "ok": True}], "warnings": []}


def fresh_natural_language_cases():
    cases = []
    for name, (symbol, _) in FRESH_ENTITIES.items():
        if name == "船舶":
            continue
        cases.extend(
            [
                FreshCase("%s现在啥价" % name, "quote-realtime", symbol),
                FreshCase("帮我看看%s这票今天红不红" % name, "quote-realtime", symbol),
                FreshCase("%s近俩月走势" % name, "quote-history", symbol, {"days": 60}),
                FreshCase("%s半年K线" % name, "quote-history", symbol, {"days": 180}),
                FreshCase("%s估值贵不贵" % name, "fundamental", symbol, {"pack": "valuation"}),
                FreshCase("%s财报好不好" % name, "fundamental", symbol, {"pack": "financials"}),
                FreshCase("%s有啥公告" % name, "announcement", symbol),
            ]
        )

    cases.extend(
        [
            FreshCase("中国船舶今天顶不顶", "quote-realtime", "600150.SH"),
            FreshCase("船舶今天顶不顶", "quote-realtime", "600150.SH"),
            FreshCase("三一这票换手咋样", "quote-realtime", "600031.SH"),
            FreshCase("海天这公司分不分红", "fundamental", "603288.SH", {"pack": "dividend"}),
            FreshCase("牧原猪肉这票资金在进还是出", "money-flow", "002714.SZ", {"scope": "stock"}),
            FreshCase("韦尔有没有被研报提到", "news", "603501.SH", {"kind": "research"}),
            FreshCase("工业富联有没有大宗", "block-trade", "601138.SH"),
            FreshCase("阳光电源两融咋样", "margin-trading", "300274.SZ"),
            FreshCase("中际旭创筹码松不松", "chip", "300308.SZ"),
            FreshCase("新易盛5分钟线", "quote-history", "300502.SZ", {"period": "minute"}),
            FreshCase("北方华创周K", "quote-history", "002371.SZ", {"period": "weekly"}),
            FreshCase("中微公司月K", "quote-history", "688012.SH", {"period": "monthly"}),
            FreshCase("海螺水泥去年走势", "quote-history", "600585.SH", {"days": 365}),
            FreshCase("爱尔眼科过去一百二十天走势", "quote-history", "300015.SZ", {"days": 120}),
            FreshCase("赛力斯近三个星期咋走的", "quote-history", "601127.SH", {"days": 21}),
            FreshCase("601127.SH 现在多少", "quote-realtime", "601127.SH"),
            FreshCase("SH-600150 今天涨了吗", "quote-realtime", "600150.SH"),
            FreshCase("ｓｚ３００２７４ 走势", "quote-history", "300274.SZ"),
            FreshCase("００２７１４最新", "quote-realtime", "002714.SZ"),
            FreshCase("588080科创板ETF现在啥价", "quote-realtime", "588080.SH"),
            FreshCase("512100中证1000ETF近2个月", "quote-history", "512100.SH", {"days": 60}),
            FreshCase("159949创业板50ETF行情", "quote-realtime", "159949.SZ"),
            FreshCase("上证50今天咋样", "quote-realtime", "000016.SH"),
            FreshCase("中证1000走势", "quote-history", "000852.SH"),
            FreshCase("国证2000近一个月", "quote-history", "399303.SZ", {"days": 30}),
            FreshCase("中证红利指数现在多少", "quote-realtime", "000922.SH"),
            FreshCase("113052转债今天啥价", "bond", "113052.SH", {"action": "quote"}),
            FreshCase("127099 转债近两个月走势", "bond", "127099.SZ", {"action": "history", "days": 60}),
            FreshCase("可转债今天哪个最猛前15", "bond", params={"action": "rank", "limit": 15}, no_entity=True),
            FreshCase("转债成交最多top 25", "bond", params={"action": "rank", "limit": 25}, no_entity=True),
            FreshCase("大A今天绿成啥样", "market-snapshot", no_entity=True),
            FreshCase("今天盘面有没有赚钱效应", "market-snapshot", no_entity=True),
            FreshCase("全市场是涨多还是跌多", "market-snapshot", no_entity=True),
            FreshCase("指数们现在都啥情况", "market-snapshot", no_entity=True),
            FreshCase("今天哪个板块最火", "sector", params={"action": "rank"}, no_entity=True),
            FreshCase("猪肉股咋样", "sector", params={"kind": "concept", "action": "rank"}, no_entity=True),
            FreshCase("算力钱流哪去了", "money-flow", params={"scope": "concept"}, no_entity=True),
            FreshCase("券商有动静没", "sector", params={"kind": "industry", "action": "rank"}, no_entity=True),
            FreshCase("低空经济有哪些票", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
            FreshCase("光伏这条线今天强不强", "sector", params={"kind": "concept", "action": "rank"}, no_entity=True),
            FreshCase("银行板块钱流哪", "money-flow", params={"scope": "industry"}, no_entity=True),
            FreshCase("半导体资金去哪了", "money-flow", params={"scope": "industry"}, no_entity=True),
            FreshCase("机器人概念今天有啥票", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
            FreshCase("CPO票哪个最强", "sector", params={"kind": "concept"}, no_entity=True),
            FreshCase("AI算力这个方向有哪些", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
            FreshCase("成交额最大的前一百二十", "rank", params={"kind": "amount", "limit": 120}, no_entity=True),
            FreshCase("谁跌得最狠top30", "rank", params={"kind": "losers", "order": "asc", "limit": 30}, no_entity=True),
            FreshCase("便宜PB的票前二十", "rank", params={"kind": "pb", "order": "asc", "limit": 20}, no_entity=True),
            FreshCase("市盈率别太高的排行", "rank", params={"kind": "pe", "order": "asc"}, no_entity=True),
            FreshCase("今天封板最早的是哪些", "limit-pool", params={"kind": "up"}, no_entity=True),
            FreshCase("今天开板又回封的", "limit-pool", params={"kind": "strong"}, no_entity=True),
            FreshCase("今天跌停的都谁", "limit-pool", params={"kind": "down"}, no_entity=True),
            FreshCase("4月25号炸板票", "limit-pool", params={"kind": "broken"}, no_entity=True),
            FreshCase("二〇二六年四月二十五号龙虎榜", "dragon-tiger", params={"date": "2026-04-25"}, no_entity=True),
            FreshCase("最近回购公告前七条", "announcement", params={"keyword": "回购", "limit": 7}, no_entity=True),
            FreshCase("最近有啥减持公告", "announcement", params={"keyword": "减持"}, no_entity=True),
            FreshCase("最近大宗成交看看", "block-trade", no_entity=True),
            FreshCase("两融余额全市场", "margin-trading", no_entity=True),
            FreshCase("给我保证赛力斯明天涨停", "unsupported", ok=False),
            FreshCase("现在能不能买海天味业", "unsupported", ok=False),
        ]
    )
    return cases


def test_fresh_validation_dataset_is_full_size():
    assert len(fresh_natural_language_cases()) == 200


def test_fresh_validation_dataset_routes_and_executes():
    failures = []
    for case in fresh_natural_language_cases():
        result = handle_smart_query(FreshClient(), case.query)
        normalized = result.get("normalized", {})

        if not case.ok:
            if result.get("ok") or result.get("error", {}).get("type") != "unsupported_request":
                failures.append((case.query, "expected_unsupported", result))
            continue
        if not result.get("ok"):
            failures.append((case.query, "not_ok", result))
            continue
        if normalized.get("command") != case.command:
            failures.append((case.query, "command", normalized.get("command"), case.command))
        entity = normalized.get("entity")
        if case.symbol and (not entity or entity.get("symbol") != case.symbol):
            failures.append((case.query, "symbol", entity, case.symbol))
        if case.no_entity and entity is not None:
            failures.append((case.query, "unexpected_entity", entity))
        for key, expected_value in (case.params or {}).items():
            actual_value = normalized.get("params", {}).get(key)
            if actual_value != expected_value:
                failures.append((case.query, "param", key, actual_value, expected_value))

    assert failures == []
