from dataclasses import dataclass
from typing import Any, Dict, Optional

from freestocklineskill_runtime.cli import handle_smart_query
from freestocklineskill_runtime.routing import entity_from_symbol


REMOTE_ENTITIES = {
    "海光信息": ("688041.SH", "海光信息"),
    "福耀玻璃": ("600660.SH", "福耀玻璃"),
    "山西汾酒": ("600809.SH", "山西汾酒"),
    "中国石油": ("601857.SH", "中国石油"),
    "中国中免": ("601888.SH", "中国中免"),
    "泸州老窖": ("000568.SZ", "泸州老窖"),
    "伊利股份": ("600887.SH", "伊利股份"),
    "海康威视": ("002415.SZ", "海康威视"),
    "美的集团": ("000333.SZ", "美的集团"),
    "京东方A": ("000725.SZ", "京东方A"),
}


@dataclass(frozen=True)
class QueryCase:
    query: str
    command: str
    symbol: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    no_entity: bool = False


class MatrixClient:
    def __init__(self):
        self.search_queries = []
        self.calls = []

    def search_entity(self, query):
        self.search_queries.append(query)
        if query not in REMOTE_ENTITIES:
            raise RuntimeError("not found: %s" % query)
        symbol, name = REMOTE_ENTITIES[query]
        return {
            "entity": entity_from_symbol(query, symbol, name=name, query=query),
            "source_chain": [{"source": "fake_suggest", "ok": True, "query": query}],
            "warnings": [],
        }

    def quote_realtime(self, entity):
        self.calls.append(("quote-realtime", entity.symbol, {}))
        return _result({"symbol": entity.symbol})

    def quote_history(self, entity, *, days, period, adjust):
        self.calls.append(("quote-history", entity.symbol, {"days": days, "period": period, "adjust": adjust}))
        return _result({"symbol": entity.symbol, "end_date": "2026-04-24", "candles": []})

    def market_snapshot(self):
        self.calls.append(("market-snapshot", None, {}))
        return _result({"indices": [], "breadth": {}})

    def rank(self, kind, limit, order="desc"):
        self.calls.append(("rank", None, {"kind": kind, "limit": limit, "order": order}))
        return _result({"kind": kind, "order": order, "items": []})

    def limit_pool(self, kind, query_date, limit):
        self.calls.append(("limit-pool", None, {"kind": kind, "date": query_date, "limit": limit}))
        return _result({"kind": kind, "date": query_date, "items": []})

    def money_flow(self, scope, period, entity, limit):
        self.calls.append(("money-flow", entity.symbol if entity else None, {"scope": scope, "period": period, "limit": limit}))
        return _result({"scope": scope, "symbol": entity.symbol if entity else None, "items": []})

    def sector(self, kind, action, entity, query, limit):
        self.calls.append(("sector", entity.symbol if entity else None, {"kind": kind, "action": action, "limit": limit, "query": query}))
        return _result({"kind": kind, "action": action, "symbol": entity.symbol if entity else None, "items": []})

    def fundamental(self, entity, pack):
        self.calls.append(("fundamental", entity.symbol, {"pack": pack}))
        return _result({"symbol": entity.symbol, "pack": pack})

    def announcement(self, entity, keyword, limit):
        self.calls.append(("announcement", entity.symbol if entity else None, {"keyword": keyword, "limit": limit}))
        return _result({"symbol": entity.symbol if entity else None, "keyword": keyword, "items": []})

    def dragon_tiger(self, query_date, entity, limit):
        self.calls.append(("dragon-tiger", entity.symbol if entity else None, {"date": query_date, "limit": limit}))
        return _result({"symbol": entity.symbol if entity else None, "date": query_date, "items": []})

    def news(self, entity, keyword, kind, limit):
        self.calls.append(("news", entity.symbol if entity else None, {"kind": kind, "keyword": keyword, "limit": limit}))
        return _result({"symbol": entity.symbol if entity else None, "kind": kind, "items": []})

    def chip(self, entity, limit):
        self.calls.append(("chip", entity.symbol, {"limit": limit}))
        return _result({"symbol": entity.symbol, "items": []})

    def block_trade(self, query_date, entity, limit):
        self.calls.append(("block-trade", entity.symbol if entity else None, {"date": query_date, "limit": limit}))
        return _result({"symbol": entity.symbol if entity else None, "date": query_date, "items": []})

    def margin_trading(self, query_date, entity, limit):
        self.calls.append(("margin-trading", entity.symbol if entity else None, {"date": query_date, "limit": limit}))
        return _result({"symbol": entity.symbol if entity else None, "date": query_date, "items": []})

    def bond(self, action, entity, limit, days):
        self.calls.append(("bond", entity.symbol if entity else None, {"action": action, "limit": limit, "days": days}))
        return _result({"action": action, "symbol": entity.symbol if entity else None, "items": []})


def _result(data):
    return {"data": data, "source_chain": [{"source": "fake", "ok": True}], "warnings": []}


def generated_query_cases():
    cases = []
    stock_templates = [
        ("{name}最新价", "quote-realtime"),
        ("查一下{name}行情", "quote-realtime"),
        ("{name}现在多少钱", "quote-realtime"),
        ("帮我看一下{name}今天涨跌幅", "quote-realtime"),
        ("{name}量比和换手率", "quote-realtime"),
        ("{name}开盘最高最低", "quote-realtime"),
    ]
    for name, (symbol, _) in REMOTE_ENTITIES.items():
        for template, command in stock_templates:
            cases.append(QueryCase(template.format(name=name), command, symbol))

    local_stock_templates = [
        ("贵州茅台最新价", "quote-realtime", "600519.SH"),
        ("宁德时代现在多少钱", "quote-realtime", "300750.SZ"),
        ("招商银行最新报价", "quote-realtime", "600036.SH"),
        ("比亚迪实时行情", "quote-realtime", "002594.SZ"),
        ("600519 今天涨跌幅", "quote-realtime", "600519.SH"),
        ("sh600519 行情", "quote-realtime", "600519.SH"),
        ("300750.SZ 最新价", "quote-realtime", "300750.SZ"),
        ("510300 现在多少钱", "quote-realtime", "510300.SH"),
        ("上证指数现在多少", "quote-realtime", "000001.SH"),
        ("科创50 最新表现", "quote-realtime", "000688.SH"),
    ]
    for query, command, symbol in local_stock_templates:
        cases.append(QueryCase(query, command, symbol))

    dirty_symbol_cases = [
        QueryCase("６００５１９ 最新价", "quote-realtime", "600519.SH"),
        QueryCase("ｓｈ６００５１９ 行情", "quote-realtime", "600519.SH"),
        QueryCase("sh 600519 行情", "quote-realtime", "600519.SH"),
        QueryCase("SZ 300750 最新价", "quote-realtime", "300750.SZ"),
        QueryCase("600519.SH最新价", "quote-realtime", "600519.SH"),
        QueryCase("  贵州 茅台   最新价？？ ", "quote-realtime", "600519.SH"),
        QueryCase("宁 德 时 代 现在多少钱", "quote-realtime", "300750.SZ"),
        QueryCase("请帮忙查下：海光信息，最新价格？", "quote-realtime", "688041.SH"),
        QueryCase("劳烦瞧瞧福耀玻璃行情", "quote-realtime", "600660.SH"),
        QueryCase("帮我看下美 的 集 团最新价", "quote-realtime", "000333.SZ"),
    ]
    cases.extend(dirty_symbol_cases)

    history_cases = [
        QueryCase("福耀玻璃最近一个月走势", "quote-history", "600660.SH", {"days": 30, "period": "daily"}),
        QueryCase("海光信息近30天走势", "quote-history", "688041.SH", {"days": 30}),
        QueryCase("山西汾酒近半年K线", "quote-history", "600809.SH", {"days": 180}),
        QueryCase("中国石油近一年日线", "quote-history", "601857.SH", {"days": 365, "period": "daily"}),
        QueryCase("泸州老窖周线走势", "quote-history", "000568.SZ", {"period": "weekly"}),
        QueryCase("伊利股份月线", "quote-history", "600887.SH", {"period": "monthly"}),
        QueryCase("宁德时代不复权日线", "quote-history", "300750.SZ", {"adjust": "none"}),
        QueryCase("贵州茅台后复权K线", "quote-history", "600519.SH", {"adjust": "hfq"}),
        QueryCase("510300 近三个月走势", "quote-history", "510300.SH", {"days": 90}),
        QueryCase("上证指数近5天走势", "quote-history", "000001.SH", {"days": 5}),
    ]
    cases.extend(history_cases)

    dirty_history_cases = [
        QueryCase("600519 qfq kline", "quote-history", "600519.SH", {"adjust": "qfq"}),
        QueryCase("300750 hfq kline", "quote-history", "300750.SZ", {"adjust": "hfq"}),
        QueryCase("贵州茅台不复权kline", "quote-history", "600519.SH", {"adjust": "none"}),
        QueryCase("宁德时代近三周走势", "quote-history", "300750.SZ", {"days": 21}),
        QueryCase("福耀玻璃近两个月走势", "quote-history", "600660.SH", {"days": 60}),
        QueryCase("海光信息过去十五天k线", "quote-history", "688041.SH", {"days": 15}),
        QueryCase("上 证 指 数 近 三 周 K线", "quote-history", "000001.SH", {"days": 21}),
        QueryCase("科创50ETF近两个月走势", "quote-history", "588000.SH", {"days": 60}),
        QueryCase("沪 深 300 ETF 走势", "quote-history", "510300.SH"),
    ]
    cases.extend(dirty_history_cases)

    market_cases = [
        "今天大盘怎么样",
        "三大指数现在如何",
        "A股市场整体表现",
        "看一下大盘",
        "今日市场涨跌家数",
        "上证深成创业板快照",
        "沪深300 和科创50 今天怎样",
        "市场宽度如何",
    ]
    cases.extend(QueryCase(query, "market-snapshot", no_entity=True) for query in market_cases)

    rank_cases = [
        QueryCase("A股涨幅榜前十", "rank", params={"kind": "gainers", "limit": 10, "order": "desc"}, no_entity=True),
        QueryCase("今日跌幅榜前20", "rank", params={"kind": "losers", "limit": 20, "order": "asc"}, no_entity=True),
        QueryCase("成交额最高的股票", "rank", params={"kind": "amount", "order": "desc"}, no_entity=True),
        QueryCase("A股成交额前十", "rank", params={"kind": "amount", "limit": 10}, no_entity=True),
        QueryCase("成交量榜前50", "rank", params={"kind": "volume", "limit": 50}, no_entity=True),
        QueryCase("换手率排行", "rank", params={"kind": "turnover"}, no_entity=True),
        QueryCase("量比榜前十", "rank", params={"kind": "volume-ratio", "limit": 10}, no_entity=True),
        QueryCase("振幅榜前二十", "rank", params={"kind": "amplitude", "limit": 20}, no_entity=True),
        QueryCase("总市值前十", "rank", params={"kind": "market-cap", "limit": 10}, no_entity=True),
        QueryCase("市盈率最高前十", "rank", params={"kind": "pe", "limit": 10, "order": "desc"}, no_entity=True),
        QueryCase("市净率最低的股票", "rank", params={"kind": "pb", "order": "asc"}, no_entity=True),
        QueryCase("top 30 成交额", "rank", params={"kind": "amount", "limit": 30}, no_entity=True),
    ]
    cases.extend(rank_cases)

    dirty_rank_cases = [
        QueryCase("top20 成交额", "rank", params={"kind": "amount", "limit": 20}, no_entity=True),
        QueryCase("TOP 50 换手率", "rank", params={"kind": "turnover", "limit": 50}, no_entity=True),
        QueryCase("PE lowest", "rank", params={"kind": "pe", "order": "asc"}, no_entity=True),
        QueryCase("PB highest top30", "rank", params={"kind": "pb", "order": "desc", "limit": 30}, no_entity=True),
        QueryCase("市净率 lowest 股票", "rank", params={"kind": "pb", "order": "asc"}, no_entity=True),
        QueryCase("A 股 成交额 TOP 20", "rank", params={"kind": "amount", "limit": 20}, no_entity=True),
        QueryCase("成交 量 top 003", "rank", params={"kind": "volume", "limit": 3}, no_entity=True),
        QueryCase("从低到高市盈率排行前十", "rank", params={"kind": "pe", "order": "asc", "limit": 10}, no_entity=True),
    ]
    cases.extend(dirty_rank_cases)

    limit_cases = [
        QueryCase("今日涨停", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("今天的A股涨停数据", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("跌停池", "limit-pool", params={"kind": "down"}, no_entity=True),
        QueryCase("今日跌停股票", "limit-pool", params={"kind": "down"}, no_entity=True),
        QueryCase("炸板股有哪些", "limit-pool", params={"kind": "broken"}, no_entity=True),
        QueryCase("强势股池", "limit-pool", params={"kind": "strong"}, no_entity=True),
        QueryCase("2026-04-24 涨停池", "limit-pool", params={"kind": "up", "date": "2026-04-24"}, no_entity=True),
        QueryCase("今日涨停前50", "limit-pool", params={"kind": "up", "limit": 50}, no_entity=True),
    ]
    cases.extend(limit_cases)

    dirty_limit_cases = [
        QueryCase("2026年4月24日涨停池", "limit-pool", params={"kind": "up", "date": "2026-04-24"}, no_entity=True),
        QueryCase("2026/4/24 炸板", "limit-pool", params={"kind": "broken", "date": "2026-04-24"}, no_entity=True),
        QueryCase("2026.04.24 强势股", "limit-pool", params={"kind": "strong", "date": "2026-04-24"}, no_entity=True),
        QueryCase("跌 停 池 前 十", "limit-pool", params={"kind": "down", "limit": 10}, no_entity=True),
    ]
    cases.extend(dirty_limit_cases)

    money_cases = [
        QueryCase("主力资金净流入前十", "money-flow", params={"scope": "market", "limit": 10}, no_entity=True),
        QueryCase("今天主力资金流入排行", "money-flow", params={"scope": "market"}, no_entity=True),
        QueryCase("主力资金净流出前20", "money-flow", params={"scope": "market", "limit": 20}, no_entity=True),
        QueryCase("海光信息资金流向", "money-flow", "688041.SH", {"scope": "stock"}),
        QueryCase("贵州茅台资金流", "money-flow", "600519.SH", {"scope": "stock"}),
        QueryCase("行业资金流排行", "money-flow", params={"scope": "industry"}, no_entity=True),
        QueryCase("概念资金流前十", "money-flow", params={"scope": "concept", "limit": 10}, no_entity=True),
        QueryCase("5日主力资金流入排行", "money-flow", params={"period": "5d"}, no_entity=True),
        QueryCase("10日资金净流入前十", "money-flow", params={"period": "10d", "limit": 10}, no_entity=True),
        QueryCase("20日资金净流出榜", "money-flow", params={"period": "20d"}, no_entity=True),
    ]
    cases.extend(money_cases)

    dirty_money_cases = [
        QueryCase("三日主力资金净流入榜", "money-flow", params={"period": "3d"}, no_entity=True),
        QueryCase("二十日资金净流出前二十", "money-flow", params={"period": "20d", "limit": 20}, no_entity=True),
        QueryCase("概念资金流 TOP 30", "money-flow", params={"scope": "concept", "limit": 30}, no_entity=True),
        QueryCase("行 业 资金净流入top10", "money-flow", params={"scope": "industry", "limit": 10}, no_entity=True),
        QueryCase("茅台主力资金", "money-flow", "600519.SH", {"scope": "stock"}),
    ]
    cases.extend(dirty_money_cases)

    sector_cases = [
        QueryCase("行业板块涨幅排行", "sector", params={"kind": "industry", "action": "rank"}, no_entity=True),
        QueryCase("概念板块排行", "sector", params={"kind": "concept", "action": "rank"}, no_entity=True),
        QueryCase("半导体板块成分股", "sector", params={"action": "constituents"}, no_entity=True),
        QueryCase("白酒板块有哪些股票", "sector", params={"action": "constituents"}, no_entity=True),
        QueryCase("贵州茅台属于什么行业", "sector", "600519.SH", {"action": "belong"}),
        QueryCase("海光信息属于什么概念", "sector", "688041.SH", {"kind": "concept", "action": "belong"}),
        QueryCase("新能源车概念成分股", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        QueryCase("AI 概念板块排行", "sector", params={"kind": "concept", "action": "rank"}, no_entity=True),
    ]
    cases.extend(sector_cases)

    dirty_sector_cases = [
        QueryCase("白酒 板块 成分股", "sector", params={"action": "constituents"}, no_entity=True),
        QueryCase("半导体概念包含哪些股票", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        QueryCase("AI概念TOP20", "sector", params={"kind": "concept", "action": "rank", "limit": 20}, no_entity=True),
        QueryCase("美的集团所属行业和概念", "sector", "000333.SZ", {"kind": "concept", "action": "belong"}),
        QueryCase("贵州 茅台 属于什么行业", "sector", "600519.SH", {"kind": "industry", "action": "belong"}),
        QueryCase("白 酒 板 块 有哪些股票", "sector", params={"action": "constituents"}, no_entity=True),
    ]
    cases.extend(dirty_sector_cases)

    fundamental_templates = [
        ("{name}基本面", "basic"),
        ("{name}估值怎么样", "valuation"),
        ("{name}ROE", "financials"),
        ("{name}毛利率净利率", "financials"),
        ("{name}资产负债率", "financials"),
        ("{name}股东户数", "holders"),
        ("{name}十大股东", "holders"),
        ("{name}分红记录", "dividend"),
        ("{name}全部基本面", "all"),
    ]
    for name, (symbol, _) in list(REMOTE_ENTITIES.items())[:5]:
        for template, pack in fundamental_templates:
            cases.append(QueryCase(template.format(name=name), "fundamental", symbol, {"pack": pack}))
    cases.extend(
        [
            QueryCase("600519 市盈率市净率", "fundamental", "600519.SH", {"pack": "valuation"}),
            QueryCase("300750 全部基本面", "fundamental", "300750.SZ", {"pack": "all"}),
            QueryCase("帮我瞅瞅美的集团 PE PB", "fundamental", "000333.SZ", {"pack": "valuation"}),
            QueryCase("宁德时代ROE和毛利率", "fundamental", "300750.SZ", {"pack": "financials"}),
            QueryCase("６００５１９ 市盈率市净率", "fundamental", "600519.SH", {"pack": "valuation"}),
            QueryCase("招商银行资产负债表", "fundamental", "600036.SH", {"pack": "financials"}),
            QueryCase("请查下比亚迪十大流通股东", "fundamental", "002594.SZ", {"pack": "holders"}),
        ]
    )

    event_cases = [
        QueryCase("山西汾酒公告", "announcement", "600809.SH"),
        QueryCase("宁德时代年报 PDF", "announcement", "300750.SZ", {"keyword": "年报"}),
        QueryCase("600519 业绩预告", "announcement", "600519.SH", {"keyword": "业绩预告"}),
        QueryCase("比亚迪回购公告", "announcement", "002594.SZ", {"keyword": "回购"}),
        QueryCase("回购公告", "announcement", params={"keyword": "回购"}, no_entity=True),
        QueryCase("今日龙虎榜", "dragon-tiger", no_entity=True),
        QueryCase("2026-04-24 龙虎榜", "dragon-tiger", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("贵州茅台龙虎榜", "dragon-tiger", "600519.SH"),
        QueryCase("新闻快讯里有没有海光信息", "news", "688041.SH", {"kind": "news"}),
        QueryCase("宁德时代新闻", "news", "300750.SZ", {"kind": "news"}),
        QueryCase("贵州茅台研报评级", "news", "600519.SH", {"kind": "research"}),
        QueryCase("比亚迪目标价研报", "news", "002594.SZ", {"kind": "research"}),
        QueryCase("贵州茅台筹码分布", "chip", "600519.SH"),
        QueryCase("海光信息筹码", "chip", "688041.SH"),
        QueryCase("2026-04-24 大宗交易", "block-trade", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("贵州茅台大宗交易", "block-trade", "600519.SH"),
        QueryCase("2026-04-24 融资融券", "margin-trading", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("宁德时代融资余额", "margin-trading", "300750.SZ"),
        QueryCase("20260424 龙虎榜", "dragon-tiger", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("有没有宁德时代新闻", "news", "300750.SZ", {"kind": "news"}),
        QueryCase("贵州茅台研究报告评级", "news", "600519.SH", {"kind": "research"}),
        QueryCase("麻烦查下：山西汾酒，年报PDF", "announcement", "600809.SH", {"keyword": "年报"}),
        QueryCase("２０２６０４２４ 大宗交易", "block-trade", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("2026年4月24日 融资融券", "margin-trading", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("600519 大宗成交", "block-trade", "600519.SH"),
        QueryCase("SZ300750 融资余额", "margin-trading", "300750.SZ"),
        QueryCase("回购 公告 top 5", "announcement", params={"keyword": "回购", "limit": 5}, no_entity=True),
    ]
    cases.extend(event_cases)

    bond_cases = [
        QueryCase("可转债涨幅榜前十", "bond", params={"action": "rank", "limit": 10}, no_entity=True),
        QueryCase("可转债成交额排行", "bond", params={"action": "rank"}, no_entity=True),
        QueryCase("123456 转债最新报价", "bond", "123456.SZ", {"action": "quote"}),
        QueryCase("可转债 123456 近30天走势", "bond", "123456.SZ", {"action": "history", "days": 30}),
        QueryCase("沪深300ETF最新价", "quote-realtime", "510300.SH"),
        QueryCase("科创50ETF走势", "quote-history", "588000.SH"),
        QueryCase("创业板ETF近三周kline", "quote-history", "159915.SZ", {"days": 21}),
        QueryCase("123456转债最新报价", "bond", "123456.SZ", {"action": "quote"}),
        QueryCase("sz123456 转债近一个月走势", "bond", "123456.SZ", {"action": "history", "days": 30}),
        QueryCase("可转债 TOP20 成交额", "bond", params={"action": "rank", "limit": 20}, no_entity=True),
        QueryCase("可 转 债 涨幅榜 前 十", "bond", params={"action": "rank", "limit": 10}, no_entity=True),
    ]
    cases.extend(bond_cases)

    expanded_edge_cases = [
        QueryCase("【贵州茅台】最新报价", "quote-realtime", "600519.SH"),
        QueryCase("茅台：开盘/最高/最低？", "quote-realtime", "600519.SH"),
        QueryCase("宁德时代PE/PB", "fundamental", "300750.SZ", {"pack": "valuation"}),
        QueryCase("宁德时代 pe pb", "fundamental", "300750.SZ", {"pack": "valuation"}),
        QueryCase("比亚迪 roe 毛利率", "fundamental", "002594.SZ", {"pack": "financials"}),
        QueryCase("万科A十大流通股东", "fundamental", "000002.SZ", {"pack": "holders"}),
        QueryCase("招商银行分红派息记录", "fundamental", "600036.SH", {"pack": "dividend"}),
        QueryCase("sh.600519 最新价", "quote-realtime", "600519.SH"),
        QueryCase("SH-600519 最新价", "quote-realtime", "600519.SH"),
        QueryCase("SH 600519 最新价", "quote-realtime", "600519.SH"),
        QueryCase("600519,最新价", "quote-realtime", "600519.SH"),
        QueryCase("600519/最新价", "quote-realtime", "600519.SH"),
        QueryCase("000001 股票最新价", "quote-realtime", "000001.SZ"),
        QueryCase("000001 上证指数走势", "quote-history", "000001.SH"),
        QueryCase("上 证 + 创 业 板 + 北 证 50 快照", "market-snapshot", no_entity=True),
        QueryCase("沪深300、科创50、北证50现在怎样", "market-snapshot", no_entity=True),
        QueryCase("两市涨跌家数", "market-snapshot", no_entity=True),
        QueryCase("全市场宽度", "market-snapshot", no_entity=True),
        QueryCase("成交额排行第前十", "rank", params={"kind": "amount", "limit": 10}, no_entity=True),
        QueryCase("成交额top001", "rank", params={"kind": "amount", "limit": 1}, no_entity=True),
        QueryCase("成交额TOP999", "rank", params={"kind": "amount", "limit": 300}, no_entity=True),
        QueryCase("PE从高到低top5", "rank", params={"kind": "pe", "order": "desc", "limit": 5}, no_entity=True),
        QueryCase("PB从低到高top5", "rank", params={"kind": "pb", "order": "asc", "limit": 5}, no_entity=True),
        QueryCase("A股领涨前二十名", "rank", params={"kind": "gainers", "limit": 20}, no_entity=True),
        QueryCase("A股领跌前二十名", "rank", params={"kind": "losers", "limit": 20, "order": "asc"}, no_entity=True),
        QueryCase("换手排行前一百", "rank", params={"kind": "turnover", "limit": 100}, no_entity=True),
        QueryCase("今日连板股", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("封板资金最大的涨停股", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("4月24日跌停池", "limit-pool", params={"kind": "down", "date": "2026-04-24"}, no_entity=True),
        QueryCase("2026-4-24涨停", "limit-pool", params={"kind": "up", "date": "2026-04-24"}, no_entity=True),
        QueryCase("二〇二六年四月二十四日涨停池", "limit-pool", params={"kind": "up", "date": "2026-04-24"}, no_entity=True),
        QueryCase("行业主力净流入5日排行", "money-flow", params={"scope": "industry", "period": "5d"}, no_entity=True),
        QueryCase("概念主力资金十日排行", "money-flow", params={"scope": "concept", "period": "10d"}, no_entity=True),
        QueryCase("贵州茅台三日资金流", "money-flow", "600519.SH", {"scope": "stock", "period": "3d"}),
        QueryCase("半导体行业资金净流入", "money-flow", params={"scope": "industry", "period": "instant"}, no_entity=True),
        QueryCase("机器人概念资金净流出top15", "money-flow", params={"scope": "concept", "period": "instant", "limit": 15}, no_entity=True),
        QueryCase("白酒行业板块成份股", "sector", params={"kind": "industry", "action": "constituents"}, no_entity=True),
        QueryCase("CPO概念有哪些", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        QueryCase("AI算力概念包含哪些股票", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        QueryCase("宁德时代属于哪个板块", "sector", "300750.SZ", {"action": "belong"}),
        QueryCase("中芯国际所属概念", "sector", "688981.SH", {"kind": "concept", "action": "belong"}),
        QueryCase("美的集团属于行业吗", "sector", "000333.SZ", {"kind": "industry", "action": "belong"}),
        QueryCase("600519公告列表", "announcement", "600519.SH"),
        QueryCase("600519年报公告PDF", "announcement", "600519.SH", {"keyword": "年报"}),
        QueryCase("宁德时代2025年年报", "announcement", "300750.SZ", {"keyword": "年报"}),
        QueryCase("增持减持公告", "announcement", params={"keyword": "减持"}, no_entity=True),
        QueryCase("今日龙虎榜前100", "dragon-tiger", params={"limit": 100}, no_entity=True),
        QueryCase("4月24号龙虎榜", "dragon-tiger", params={"date": "2026-04-24"}, no_entity=True),
        QueryCase("贵州茅台有没有上龙虎榜", "dragon-tiger", "600519.SH"),
        QueryCase("大宗交易贵州茅台", "block-trade", "600519.SH"),
        QueryCase("两融余额宁德时代", "margin-trading", "300750.SZ"),
        QueryCase("600519融资融券", "margin-trading", "600519.SH"),
        QueryCase("贵州茅台新闻快讯", "news", "600519.SH", {"kind": "news"}),
        QueryCase("宁德时代目标价", "news", "300750.SZ", {"kind": "research"}),
        QueryCase("比亚迪评级研报top5", "news", "002594.SZ", {"kind": "research", "limit": 5}),
        QueryCase("茅台筹码集中度", "chip", "600519.SH"),
        QueryCase("600519筹码分布图", "chip", "600519.SH"),
        QueryCase("可转债跌幅榜前十", "bond", params={"action": "rank", "limit": 10}, no_entity=True),
        QueryCase("转债成交额top30", "bond", params={"action": "rank", "limit": 30}, no_entity=True),
        QueryCase("sh113000转债走势", "bond", "113000.SH", {"action": "history"}),
        QueryCase("113000 转债 qfq kline", "bond", "113000.SH", {"action": "history"}),
        QueryCase("可转债123456最新价", "bond", "123456.SZ", {"action": "quote"}),
        QueryCase("沪深 300 ETF pe pb", "fundamental", "510300.SH", {"pack": "valuation"}),
        QueryCase("510300ETF走势", "quote-history", "510300.SH"),
        QueryCase("159915 创业板ETF 最新价", "quote-realtime", "159915.SZ"),
        QueryCase("别废话，给我查贵州茅台最新价", "quote-realtime", "600519.SH"),
        QueryCase("给我用免费的源查一下宁德时代公告", "announcement", "300750.SZ"),
        QueryCase("我不要分析，只要美的集团资金流", "money-flow", "000333.SZ", {"scope": "stock", "period": "instant"}),
        QueryCase("别给建议，查A股成交额前十", "rank", params={"kind": "amount", "limit": 10}, no_entity=True),
        QueryCase("近半个月贵州茅台走势", "quote-history", "600519.SH", {"days": 15}),
        QueryCase("宁德时代近2个星期走势", "quote-history", "300750.SZ", {"days": 14}),
        QueryCase("福耀玻璃过去两星期走势", "quote-history", "600660.SH", {"days": 14}),
        QueryCase("中证500近一百零五天走势", "quote-history", "000905.SH", {"days": 105}),
        QueryCase("创业板指5m分钟线", "quote-history", "399006.SZ", {"period": "minute"}),
        QueryCase("上证50ETF月线", "quote-history", "510050.SH", {"period": "monthly"}),
        QueryCase("中证500ETF周线", "quote-history", "510500.SH", {"period": "weekly"}),
        QueryCase("北证50最新行情", "quote-realtime", "899050.BJ"),
        QueryCase("bj920125 最新价", "quote-realtime", "920125.BJ"),
        QueryCase("９２０１２５ 北交所行情", "quote-realtime", "920125.BJ"),
        QueryCase("300059东方财富最新价", "quote-realtime", "300059.SZ"),
        QueryCase("中国移动A股最新价", "quote-realtime", "600941.SH"),
        QueryCase("隆基绿能现金流量表", "fundamental", "601012.SH", {"pack": "financials"}),
        QueryCase("长江电力完整财务", "fundamental", "600900.SH", {"pack": "financials"}),
        QueryCase("中国平安基本资料", "fundamental", "601318.SH", {"pack": "basic"}),
        QueryCase("平安银行派息", "fundamental", "000001.SZ", {"pack": "dividend"}),
        QueryCase("中信证券股东人数", "fundamental", "600030.SH", {"pack": "holders"}),
        QueryCase("药明康德减持公告", "announcement", "603259.SH", {"keyword": "减持"}),
        QueryCase("寒武纪重大事项公告", "announcement", "688256.SH", {"keyword": "重大事项"}),
        QueryCase("中芯国际大宗交易", "block-trade", "688981.SH"),
        QueryCase("迈瑞医疗融资融券余额", "margin-trading", "300760.SZ"),
        QueryCase("东方财富研报评级", "news", "300059.SZ", {"kind": "research"}),
        QueryCase("五粮液新闻", "news", "000858.SZ", {"kind": "news"}),
        QueryCase("紫金矿业筹码", "chip", "601899.SH"),
    ]
    cases.extend(expanded_edge_cases)

    retail_chat_cases = [
        QueryCase("茅台现在咋样", "quote-realtime", "600519.SH"),
        QueryCase("茅台今天红了吗", "quote-realtime", "600519.SH"),
        QueryCase("宁王今天啥价", "quote-realtime", "300750.SZ"),
        QueryCase("东财现在多少", "quote-realtime", "300059.SZ"),
        QueryCase("招行今天咋样", "quote-realtime", "600036.SH"),
        QueryCase("比王今天涨了吗", "quote-realtime", "002594.SZ"),
        QueryCase("中芯现在多少钱", "quote-realtime", "688981.SH"),
        QueryCase("大A今天红不红", "market-snapshot", no_entity=True),
        QueryCase("今天盘面咋样", "market-snapshot", no_entity=True),
        QueryCase("今天市场热不热", "market-snapshot", no_entity=True),
        QueryCase("两市有没有赚钱效应", "market-snapshot", no_entity=True),
        QueryCase("今天涨的多还是跌的多", "market-snapshot", no_entity=True),
        QueryCase("今天哪个票最猛", "rank", params={"kind": "gainers"}, no_entity=True),
        QueryCase("今天谁跌得最惨", "rank", params={"kind": "losers", "order": "asc"}, no_entity=True),
        QueryCase("成交最多的是谁", "rank", params={"kind": "amount"}, no_entity=True),
        QueryCase("谁最活跃", "rank", params={"kind": "turnover"}, no_entity=True),
        QueryCase("换手最高的是啥", "rank", params={"kind": "turnover"}, no_entity=True),
        QueryCase("便宜市盈率的票看看", "rank", params={"kind": "pe", "order": "asc"}, no_entity=True),
        QueryCase("今天有多少涨停", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("今天炸了哪些板", "limit-pool", params={"kind": "broken"}, no_entity=True),
        QueryCase("连板都有哪些", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("封单最大的票", "limit-pool", params={"kind": "up"}, no_entity=True),
        QueryCase("钱都往哪儿跑了", "money-flow", params={"scope": "market"}, no_entity=True),
        QueryCase("主力今天买啥了", "money-flow", params={"scope": "market"}, no_entity=True),
        QueryCase("主力在卖啥", "money-flow", params={"scope": "market"}, no_entity=True),
        QueryCase("白酒今天强不强", "sector", params={"kind": "industry", "action": "rank"}, no_entity=True),
        QueryCase("半导体今天咋样", "sector", params={"kind": "industry", "action": "rank"}, no_entity=True),
        QueryCase("机器人这条线有哪些票", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        QueryCase("AI这块有哪些股票", "sector", params={"kind": "concept", "action": "constituents"}, no_entity=True),
        QueryCase("茅台属于啥板块", "sector", "600519.SH", {"action": "belong"}),
        QueryCase("宁王是哪个行业", "sector", "300750.SZ", {"kind": "industry", "action": "belong"}),
        QueryCase("茅台财报好不好", "fundamental", "600519.SH", {"pack": "financials"}),
        QueryCase("宁德时代基本情况", "fundamental", "300750.SZ", {"pack": "basic"}),
        QueryCase("东财估值贵不贵", "fundamental", "300059.SZ", {"pack": "valuation"}),
        QueryCase("招行分不分红", "fundamental", "600036.SH", {"pack": "dividend"}),
        QueryCase("茅台有啥公告", "announcement", "600519.SH"),
        QueryCase("宁王最近公告", "announcement", "300750.SZ"),
        QueryCase("有没有回购的公告", "announcement", params={"keyword": "回购"}, no_entity=True),
        QueryCase("今天谁上榜了", "dragon-tiger", no_entity=True),
        QueryCase("茅台上榜没", "dragon-tiger", "600519.SH"),
        QueryCase("茅台有啥新闻", "news", "600519.SH", {"kind": "news"}),
        QueryCase("宁王有没有研报", "news", "300750.SZ", {"kind": "research"}),
        QueryCase("茅台筹码松不松", "chip", "600519.SH"),
        QueryCase("最近有没有大宗", "block-trade", no_entity=True),
        QueryCase("茅台有没有大宗", "block-trade", "600519.SH"),
        QueryCase("宁王两融咋样", "margin-trading", "300750.SZ"),
        QueryCase("转债今天谁最强", "bond", params={"action": "rank"}, no_entity=True),
        QueryCase("转债哪个成交最多", "bond", params={"action": "rank"}, no_entity=True),
        QueryCase("这个票600519怎么样", "quote-realtime", "600519.SH"),
        QueryCase("帮我瞅眼300750", "quote-realtime", "300750.SZ"),
        QueryCase("别讲道理，直接查茅台公告", "announcement", "600519.SH"),
        QueryCase("别整分析，看看大A", "market-snapshot", no_entity=True),
    ]
    cases.extend(retail_chat_cases)

    return cases


def test_generated_natural_language_matrix_is_large_enough():
    cases = generated_query_cases()

    assert len(cases) >= 400


def test_generated_natural_language_matrix_routes_and_executes():
    failures = []
    for case in generated_query_cases():
        client = MatrixClient()
        result = handle_smart_query(client, case.query)
        normalized = result.get("normalized", {})

        if not result.get("ok"):
            failures.append((case.query, result))
            continue
        if normalized.get("command") != case.command:
            failures.append((case.query, "command", normalized.get("command"), case.command))
        entity = normalized.get("entity")
        if case.symbol and (not entity or entity.get("symbol") != case.symbol):
            failures.append((case.query, "symbol", entity, case.symbol))
        if case.no_entity and entity is not None:
            failures.append((case.query, "unexpected_entity", entity))
        for key, expected_value in (case.params or {}).items():
            if normalized.get("params", {}).get(key) != expected_value:
                failures.append((case.query, "param", key, normalized.get("params", {}).get(key), expected_value))

    assert failures == []


def test_sector_board_queries_do_not_search_board_names_as_stocks():
    client = MatrixClient()

    result = handle_smart_query(client, "半导体板块成分股")

    assert result["ok"] is True
    assert result["normalized"]["command"] == "sector"
    assert result["normalized"]["params"]["action"] == "constituents"
    assert "entity" not in result["normalized"]
    assert client.search_queries == []


def test_global_event_queries_do_not_force_entity_lookup():
    for query, command in [("回购公告", "announcement"), ("2026-04-24 大宗交易", "block-trade"), ("2026-04-24 融资融券", "margin-trading")]:
        client = MatrixClient()
        result = handle_smart_query(client, query)

        assert result["ok"] is True
        assert result["normalized"]["command"] == command
        assert "entity" not in result["normalized"]
        assert client.search_queries == []


def test_predictive_or_advice_queries_fail_without_fetching_data():
    for query in ["给我保证明天涨停", "推荐一只明天能涨的股票", "贵州茅台未来会不会涨", "现在还能追茅台吗", "宁王明天能回本吗"]:
        client = MatrixClient()
        result = handle_smart_query(client, query)

        assert result["ok"] is False
        assert result["intent"] == "unsupported"
        assert result["error"]["type"] == "unsupported_request"
        assert result["normalized"]["command"] == "unsupported"
        assert client.calls == []
