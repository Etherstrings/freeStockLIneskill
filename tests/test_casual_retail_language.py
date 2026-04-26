from dataclasses import dataclass
from typing import Any, Dict, Optional

from freestocklineskill_runtime.cli import handle_smart_query
from freestocklineskill_runtime.routing import entity_from_symbol


CASUAL_ENTITIES = {
    "贵州茅台": ("600519.SH", "贵州茅台"),
    "茅台": ("600519.SH", "贵州茅台"),
    "宁德时代": ("300750.SZ", "宁德时代"),
    "宁王": ("300750.SZ", "宁德时代"),
    "东方财富": ("300059.SZ", "东方财富"),
    "东财": ("300059.SZ", "东方财富"),
    "招商银行": ("600036.SH", "招商银行"),
    "招行": ("600036.SH", "招商银行"),
    "比亚迪": ("002594.SZ", "比亚迪"),
    "比王": ("002594.SZ", "比亚迪"),
    "中芯国际": ("688981.SH", "中芯国际"),
    "中芯": ("688981.SH", "中芯国际"),
    "海天味业": ("603288.SH", "海天味业"),
    "海天": ("603288.SH", "海天味业"),
    "三一重工": ("600031.SH", "三一重工"),
    "三一": ("600031.SH", "三一重工"),
    "牧原股份": ("002714.SZ", "牧原股份"),
    "牧原": ("002714.SZ", "牧原股份"),
    "牧原猪肉": ("002714.SZ", "牧原股份"),
    "韦尔股份": ("603501.SH", "韦尔股份"),
    "韦尔": ("603501.SH", "韦尔股份"),
    "赛力斯": ("601127.SH", "赛力斯"),
    "工业富联": ("601138.SH", "工业富联"),
    "中国船舶": ("600150.SH", "中国船舶"),
    "船舶": ("600150.SH", "中国船舶"),
    "阳光电源": ("300274.SZ", "阳光电源"),
    "中际旭创": ("300308.SZ", "中际旭创"),
}


@dataclass(frozen=True)
class CasualCase:
    query: str
    command: str
    symbol: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    no_entity: bool = False
    ok: bool = True


class CasualClient:
    def search_entity(self, query):
        if query not in CASUAL_ENTITIES:
            raise RuntimeError("not found: %s" % query)
        symbol, name = CASUAL_ENTITIES[query]
        return {
            "entity": entity_from_symbol(query, symbol, name=name, query=query),
            "source_chain": [{"source": "casual_fake", "ok": True, "query": query}],
            "warnings": [],
        }

    def _result(self):
        return {"data": {}, "source_chain": [{"source": "casual_fake", "ok": True}], "warnings": []}

    def quote_realtime(self, entity):
        return self._result()

    def quote_history(self, entity, *, days, period, adjust):
        return self._result()

    def market_snapshot(self):
        return self._result()

    def rank(self, kind, limit, order="desc"):
        return self._result()

    def limit_pool(self, kind, query_date, limit):
        return self._result()

    def money_flow(self, scope, period, entity, limit):
        return self._result()

    def sector(self, kind, action, entity, query, limit):
        return self._result()

    def fundamental(self, entity, pack):
        return self._result()

    def announcement(self, entity, keyword, limit):
        return self._result()

    def dragon_tiger(self, query_date, entity, limit):
        return self._result()

    def news(self, entity, keyword, kind, limit):
        return self._result()

    def chip(self, entity, limit):
        return self._result()

    def block_trade(self, query_date, entity, limit):
        return self._result()

    def margin_trading(self, query_date, entity, limit):
        return self._result()

    def bond(self, action, entity, limit, days):
        return self._result()


def casual_retail_cases():
    return [
        CasualCase("茅台今天咋了", "quote-realtime", "600519.SH"),
        CasualCase("茅台是不是崩了", "quote-realtime", "600519.SH"),
        CasualCase("宁王又跌了没", "quote-realtime", "300750.SZ"),
        CasualCase("东财今天红绿", "quote-realtime", "300059.SZ"),
        CasualCase("赛力斯最近咋走", "quote-history", "601127.SH"),
        CasualCase("这个票600519啥情况", "quote-realtime", "600519.SH"),
        CasualCase("600519这货最近咋走", "quote-history", "600519.SH"),
        CasualCase("韦尔今天量怎么样", "quote-realtime", "603501.SH"),
        CasualCase("三一今天换手高不高", "quote-realtime", "600031.SH"),
        CasualCase("海天是不是便宜了", "fundamental", "603288.SH", {"pack": "valuation"}),
        CasualCase("茅台有没有雷", "news", "600519.SH", {"kind": "news"}),
        CasualCase("宁王最近有啥消息", "news", "300750.SZ", {"kind": "news"}),
        CasualCase("赛力斯有没有利好利空", "news", "601127.SH", {"kind": "news"}),
        CasualCase("韦尔研报说啥", "news", "603501.SH", {"kind": "research"}),
        CasualCase("工业富联机构怎么看", "news", "601138.SH", {"kind": "research"}),
        CasualCase("牧原年报出了没", "announcement", "002714.SZ", {"keyword": "年报"}),
        CasualCase("三一有减持吗", "announcement", "600031.SH", {"keyword": "减持"}),
        CasualCase("中芯有回购没", "announcement", "688981.SH", {"keyword": "回购"}),
        CasualCase("今天有没有地天板", "limit-pool", params={"kind": "strong"}, no_entity=True),
        CasualCase("今天谁封得最死", "limit-pool", params={"kind": "up"}, no_entity=True),
        CasualCase("哪些票开板了", "limit-pool", params={"kind": "broken"}, no_entity=True),
        CasualCase("有没有跌停潮", "limit-pool", params={"kind": "down"}, no_entity=True),
        CasualCase("今天资金抱团哪里", "money-flow", params={"scope": "market"}, no_entity=True),
        CasualCase("主力跑路最多的是谁", "money-flow", params={"scope": "market"}, no_entity=True),
        CasualCase("资金在买哪些方向", "money-flow", params={"scope": "market"}, no_entity=True),
        CasualCase("AI今天吸金吗", "money-flow", params={"scope": "concept"}, no_entity=True),
        CasualCase("算力方向钱进没", "money-flow", params={"scope": "concept"}, no_entity=True),
        CasualCase("光伏还有人买吗", "money-flow", params={"scope": "concept"}, no_entity=True),
        CasualCase("券商今天拉了吗", "sector", params={"kind": "industry", "action": "rank"}, no_entity=True),
        CasualCase("白酒趴着还是起来了", "sector", params={"kind": "industry", "action": "rank"}, no_entity=True),
        CasualCase("低空经济这块谁在涨", "sector", params={"kind": "concept", "action": "rank"}, no_entity=True),
        CasualCase("机器人方向都有谁", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        CasualCase("CPO那条线有哪些", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        CasualCase("今天最能打的票", "rank", params={"kind": "gainers"}, no_entity=True),
        CasualCase("今天杀得最狠的票", "rank", params={"kind": "losers", "order": "asc"}, no_entity=True),
        CasualCase("最吸金的股票前10", "money-flow", params={"scope": "market", "limit": 10}, no_entity=True),
        CasualCase("换手最离谱的前二十", "rank", params={"kind": "turnover", "limit": 20}, no_entity=True),
        CasualCase("小票里市值最小的", "rank", params={"kind": "market-cap", "order": "asc"}, no_entity=True),
        CasualCase("茅台财务底子", "fundamental", "600519.SH", {"pack": "financials"}),
        CasualCase("招行每年分多少钱", "fundamental", "600036.SH", {"pack": "dividend"}),
        CasualCase("比王股东人数变没变", "fundamental", "002594.SZ", {"pack": "holders"}),
        CasualCase("中际旭创筹码集中吗", "chip", "300308.SZ"),
        CasualCase("船舶上龙虎榜了吗", "dragon-tiger", "600150.SH"),
        CasualCase("阳光电源有没有大宗卖出", "block-trade", "300274.SZ"),
        CasualCase("东财融资盘多不多", "margin-trading", "300059.SZ"),
        CasualCase("转债今天热不热", "bond", params={"action": "rank"}, no_entity=True),
        CasualCase("113052这个债咋样", "bond", "113052.SH", {"action": "quote"}),
        CasualCase("127099转债最近咋走", "bond", "127099.SZ", {"action": "history"}),
        CasualCase("茅台明天能买吗", "unsupported", ok=False),
        CasualCase("宁王会不会反弹", "unsupported", ok=False),
    ]


def test_casual_retail_dataset_routes_and_executes():
    failures = []
    for case in casual_retail_cases():
        result = handle_smart_query(CasualClient(), case.query)
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
