from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import timedelta
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


INDEX_ALIASES = {
    "上证指数": ("上证指数", "000001.SH"),
    "上证综指": ("上证指数", "000001.SH"),
    "沪指": ("上证指数", "000001.SH"),
    "上证": ("上证指数", "000001.SH"),
    "上证50": ("上证50", "000016.SH"),
    "深证成指": ("深证成指", "399001.SZ"),
    "深成指": ("深证成指", "399001.SZ"),
    "深证": ("深证成指", "399001.SZ"),
    "创业板指": ("创业板指", "399006.SZ"),
    "创业板": ("创业板指", "399006.SZ"),
    "沪深300": ("沪深300", "000300.SH"),
    "科创50": ("科创50", "000688.SH"),
    "北证50": ("北证50", "899050.BJ"),
    "中证500": ("中证500", "000905.SH"),
    "中证1000": ("中证1000", "000852.SH"),
    "国证2000": ("国证2000", "399303.SZ"),
    "中证红利指数": ("中证红利", "000922.SH"),
    "中证红利": ("中证红利", "000922.SH"),
}

ETF_ALIASES = {
    "沪深300ETF": ("沪深300ETF", "510300.SH"),
    "300ETF": ("沪深300ETF", "510300.SH"),
    "科创50ETF": ("科创50ETF", "588000.SH"),
    "科创板50ETF": ("科创板50ETF", "588080.SH"),
    "科创板ETF": ("科创板ETF", "588080.SH"),
    "创业板ETF": ("创业板ETF", "159915.SZ"),
    "创业板50ETF": ("创业板50ETF", "159949.SZ"),
    "中证500ETF": ("中证500ETF", "510500.SH"),
    "中证1000ETF": ("中证1000ETF", "512100.SH"),
    "上证50ETF": ("上证50ETF", "510050.SH"),
}

COMMON_SYMBOLS = {
    "美的集团": "000333.SZ",
    "贵州茅台": "600519.SH",
    "茅子": "600519.SH",
    "茅台": "600519.SH",
    "宁德时代": "300750.SZ",
    "宁王": "300750.SZ",
    "宁德": "300750.SZ",
    "东方财富": "300059.SZ",
    "东财": "300059.SZ",
    "中国平安": "601318.SH",
    "平安银行": "000001.SZ",
    "招商银行": "600036.SH",
    "招行": "600036.SH",
    "五粮液": "000858.SZ",
    "比亚迪": "002594.SZ",
    "比王": "002594.SZ",
    "万科A": "000002.SZ",
    "万科": "000002.SZ",
    "中信证券": "600030.SH",
    "工商银行": "601398.SH",
    "农业银行": "601288.SH",
    "中国银行": "601988.SH",
    "建设银行": "601939.SH",
    "中芯国际": "688981.SH",
    "中芯": "688981.SH",
    "寒武纪": "688256.SH",
    "药明康德": "603259.SH",
    "迈瑞医疗": "300760.SZ",
    "隆基绿能": "601012.SH",
    "立讯精密": "002475.SZ",
    "紫金矿业": "601899.SH",
    "长江电力": "600900.SH",
    "中国移动": "600941.SH",
    "中移动": "600941.SH",
    "海天味业": "603288.SH",
    "海天": "603288.SH",
    "三一重工": "600031.SH",
    "三一": "600031.SH",
    "牧原股份": "002714.SZ",
    "牧原": "002714.SZ",
    "牧原猪肉": "002714.SZ",
    "韦尔股份": "603501.SH",
    "韦尔": "603501.SH",
    "中国船舶": "600150.SH",
    "船舶": "600150.SH",
    "赛力斯": "601127.SH",
    "工业富联": "601138.SH",
    "阳光电源": "300274.SZ",
    "爱尔眼科": "300015.SZ",
    "中国神华": "601088.SH",
    "长城汽车": "601633.SH",
    "保利发展": "600048.SH",
    "中际旭创": "300308.SZ",
    "新易盛": "300502.SZ",
    "江淮汽车": "600418.SH",
    "北方华创": "002371.SZ",
    "中微公司": "688012.SH",
    "中航沈飞": "600760.SH",
    "歌尔股份": "002241.SZ",
    "海螺水泥": "600585.SH",
}

BOARD_HINTS = {
    "白酒": "industry",
    "半导体": "industry",
    "券商": "industry",
    "证券": "industry",
    "银行": "industry",
    "猪肉": "concept",
    "光伏": "concept",
    "低空经济": "concept",
    "人形机器人": "concept",
    "机器人": "concept",
    "AI": "concept",
    "CPO": "concept",
    "算力": "concept",
    "新能源车": "concept",
}

CN_NUM = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "俩": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "百": 100,
    "〇": 0,
}

SYMBOL_RE = re.compile(r"(?i)(?<![a-z0-9])(?:(?:sh|sz|bj)[.\-]?)?\d{6}(?:\.(?:sh|sz|bj))?(?![a-z0-9])")
DATE_SPAN_RE = re.compile(r"(?:近|最近|过去)\s*(?:\d{1,4}|[零〇一二三四五六七八九十两俩百]+|一|半)\s*(?:天|日|周|个?星期|个月|月|年|个?交易日)")
FULL_DATE_RE = re.compile(r"20\d{2}[-/.年]?\s*\d{1,2}[-/.月]?\s*\d{1,2}日?")
CHINESE_FULL_DATE_RE = re.compile(r"[二〇零一二三四五六七八九]{4}年[一二三四五六七八九十两俩]{1,3}月[一二三四五六七八九十两俩]{1,3}[日号]?")
MONTH_DAY_RE = re.compile(r"\d{1,2}月\d{1,2}[日号]?")

ENTITY_QUERY_NOISE = [
    "帮我看一下",
    "帮我看看",
    "帮我查一下",
    "帮我查下",
    "帮我看下",
    "帮我瞅瞅",
    "别废话",
    "别整分析",
    "别分析",
    "不要分析",
    "我不要分析",
    "别给建议",
    "不要建议",
    "不要投资建议",
    "只要数据",
    "只查数据",
    "只要",
    "给我用免费的源",
    "用免费的源",
    "免费源",
    "麻烦看一下",
    "麻烦查一下",
    "麻烦看下",
    "麻烦查下",
    "我想看看",
    "我想查",
    "给我看一下",
    "看一下",
    "看下",
    "查一下",
    "查下",
    "查询",
    "看看",
    "瞅瞅",
    "瞧瞧",
    "帮我",
    "麻烦",
    "劳烦",
    "请帮忙",
    "请问",
    "请",
    "一下",
    "今天",
    "今日",
    "昨天",
    "明天",
    "现在",
    "最近",
    "去年",
    "全市场",
    "半年K线",
    "半年k线",
    "半年走势",
    "这只股票",
    "这个票",
    "这只票",
    "这公司",
    "这票",
    "这货",
    "这个债",
    "这只债",
    "最新价格",
    "最新价",
    "最新",
    "现在多少钱",
    "现在价格",
    "现在价",
    "多少钱",
    "啥价",
    "咋样",
    "咋走的",
    "咋走",
    "走的",
    "走得",
    "啥样",
    "啥情况",
    "好不好",
    "顶不顶",
    "红不红",
    "红绿",
    "崩了",
    "跌了没",
    "强不强",
    "最火",
    "是不是",
    "涨了吗",
    "跌了吗",
    "贵不贵",
    "钱",
    "都往哪儿跑了",
    "都往哪儿跑",
    "往哪儿跑",
    "往哪跑",
    "跑了",
    "股价",
    "价格",
    "行情",
    "开盘价",
    "开盘",
    "收盘价",
    "收盘",
    "昨收",
    "最高最低",
    "最高价",
    "最低价",
    "涨跌幅",
    "涨跌额",
    "涨跌",
    "成交额",
    "成交量",
    "量比和换手率",
    "换手率",
    "换手",
    "量比",
    "走势",
    "近况",
    "历史走势",
    "历史",
    "k线",
    "K线",
    "kline",
    "日线",
    "周线",
    "月线",
    "周K",
    "月K",
    "周k",
    "月k",
    "分钟线",
    "分钟",
    "分时",
    "公告",
    "年报",
    "半年报",
    "季报",
    "一季报",
    "三季报",
    "业绩预告",
    "披露",
    "PDF",
    "pdf",
    "龙虎榜",
    "上龙虎榜了吗",
    "上龙虎榜",
    "了吗",
    "吗",
    "资金流向",
    "资金流",
    "资金去哪了",
    "资金去哪",
    "资金在进还是出",
    "在进还是出",
    "进还是出",
    "钱流哪去了",
    "钱流哪",
    "钱去哪了",
    "钱去哪",
    "资金抱团哪里",
    "资金抱团",
    "主力跑路",
    "跑路最多",
    "资金在买",
    "吸金",
    "钱进没",
    "还有人买",
    "人买吗",
    "资金",
    "主力资金",
    "主力",
    "净流入",
    "净流出",
    "流入",
    "流出",
    "在卖",
    "所属行业",
    "所属概念",
    "属于什么行业",
    "属于什么概念",
    "属于",
    "所属",
    "板块",
    "行业",
    "概念",
    "成分股",
    "成份股",
    "成分",
    "成份",
    "有哪些股票",
    "有哪些",
    "包含",
    "基本面",
    "财务",
    "估值",
    "市盈率",
    "市净率",
    "毛利率",
    "净利率",
    "资产负债表",
    "资产负债率",
    "资产负债",
    "利润表",
    "现金流量表",
    "现金流",
    "股东户数",
    "十大股东",
    "股东",
    "分红",
    "派息",
    "记录",
    "全部",
    "排行",
    "排名",
    "涨幅榜",
    "跌幅榜",
    "成交额榜",
    "成交量榜",
    "换手率榜",
    "量比榜",
    "振幅榜",
    "市值榜",
    "榜",
    "前二十",
    "前五十",
    "前十",
    "最高",
    "最低",
    "最大",
    "最小",
    "回购",
    "减持",
    "增持",
    "重大事项",
    "新闻",
    "快讯",
    "消息",
    "利好",
    "利空",
    "有雷",
    "爆雷",
    "有没有",
    "有啥",
    "被研报提到",
    "被提到",
    "机构怎么看",
    "机构看法",
    "里",
    "研报",
    "评级",
    "目标价",
    "筹码分布",
    "筹码",
    "大宗交易",
    "大宗成交",
    "大宗",
    "大宗卖出",
    "上榜",
    "上榜没",
    "融资融券",
    "两融",
    "融资",
    "融资余额",
    "融资盘",
    "余额",
    "融券",
    "多少",
    "怎么样",
    "如何",
    "什么",
    "啥",
    "哪个",
    "哪儿",
    "谁",
    "股票",
    "A股",
    "a股",
]


@dataclass(frozen=True)
class Entity:
    raw: str
    symbol: str
    code: str
    market: str
    name: Optional[str]
    asset_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw": self.raw,
            "symbol": self.symbol,
            "code": self.code,
            "market": self.market,
            "name": self.name,
            "asset_type": self.asset_type,
        }


@dataclass(frozen=True)
class RoutePlan:
    intent: str
    command: str
    query: str
    entity: Optional[Entity]
    params: Dict[str, Any]

    def normalized(self) -> Dict[str, Any]:
        result = {
            "command": self.command,
            "params": self.params,
        }
        if self.entity is not None:
            result["entity"] = self.entity.to_dict()
        return result


def normalize_symbol(text: str, prefer_index: bool = False, asset_hint: Optional[str] = None) -> Optional[str]:
    raw = normalize_query_text(text).strip().upper().replace(" ", "").replace("-", "")
    if not raw:
        return None
    if raw.startswith(("SH.", "SZ.", "BJ.")) and len(raw) == 9 and raw[3:].isdigit():
        raw = "%s.%s" % (raw[3:], raw[:2])
    if raw.startswith(("SH", "SZ", "BJ")) and len(raw) == 8 and raw[2:].isdigit():
        raw = "%s.%s" % (raw[2:], raw[:2])
    if "." in raw:
        code, market = raw.split(".", 1)
        market = market.upper()
        if code.isdigit() and len(code) == 6 and market in {"SH", "SZ", "BJ"}:
            return "%s.%s" % (code, market)
        return None
    if not raw.isdigit() or len(raw) != 6:
        return None
    market = infer_market(raw, prefer_index=prefer_index, asset_hint=asset_hint)
    return "%s.%s" % (raw, market)


def infer_market(code: str, prefer_index: bool = False, asset_hint: Optional[str] = None) -> str:
    if prefer_index and code in {"000001", "000300", "000688", "000905"}:
        return "SH"
    if prefer_index and code.startswith("399"):
        return "SZ"
    if prefer_index and code.startswith("899"):
        return "BJ"
    if asset_hint == "bond":
        if code.startswith(("110", "113", "118")):
            return "SH"
        return "SZ"
    if code.startswith(("50", "51", "52", "56", "58")):
        return "SH"
    if code.startswith(("15", "16", "18")):
        return "SZ"
    if code.startswith(("4", "8", "92")):
        return "BJ"
    if code.startswith(("6", "9")):
        return "SH"
    return "SZ"


def asset_type_for_symbol(symbol: str, query: str = "") -> str:
    code, market = symbol.split(".", 1)
    if "转债" in query or code.startswith(("110", "113", "118", "123", "127", "128")):
        return "bond"
    if any(name for name, (_, value) in INDEX_ALIASES.items() if value == symbol):
        return "index"
    if code.startswith(("000", "399", "899")) and market in {"SH", "SZ", "BJ"} and "股票" not in query:
        if symbol in {item[1] for item in INDEX_ALIASES.values()}:
            return "index"
    if code.startswith(("50", "51", "52", "56", "58", "15", "16", "18")):
        return "fund"
    return "stock"


def entity_from_symbol(raw: str, symbol: str, name: Optional[str] = None, query: str = "") -> Entity:
    code, market = symbol.split(".", 1)
    return Entity(
        raw=raw,
        symbol=symbol,
        code=code,
        market=market,
        name=name,
        asset_type=asset_type_for_symbol(symbol, query=query),
    )


def resolve_local_entity(query: str, prefer_index: bool = False, asset_hint: Optional[str] = None) -> Optional[Entity]:
    text = normalize_query_text(query)
    compact_text = re.sub(r"\s+", "", text)
    for alias, (name, symbol) in sorted(ETF_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias.lower() in text.lower() or alias.lower() in compact_text.lower():
            return entity_from_symbol(alias, symbol, name=name, query=text)
    for alias, (name, symbol) in sorted(INDEX_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias.lower() in text.lower() or alias.lower() in compact_text.lower():
            return entity_from_symbol(alias, symbol, name=name, query=text)
    match = SYMBOL_RE.search(re.sub(r"\s+", "", text))
    if match:
        raw = match.group(0)
        symbol = normalize_symbol(raw, prefer_index=prefer_index, asset_hint=asset_hint)
        if symbol:
            return entity_from_symbol(raw, symbol, query=text)
    for name, symbol in sorted(COMMON_SYMBOLS.items(), key=lambda item: len(item[0]), reverse=True):
        if name in text or name in compact_text:
            return entity_from_symbol(name, symbol, name=name, query=text)
    return None


def entity_search_candidates(query: str) -> List[str]:
    text = normalize_query_text(query).strip()
    if not text:
        return []
    candidates: List[str] = []

    def add(value: str) -> None:
        cleaned = _clean_entity_candidate(value)
        if cleaned and cleaned not in candidates and not _looks_like_non_entity_query(cleaned):
            candidates.append(cleaned)

    symbol_match = SYMBOL_RE.search(text)
    if symbol_match:
        add(symbol_match.group(0))

    compact = re.sub(r"[\s,，。！？?！：:；;、（）()【】\[\]\"'“”‘’]+", "", text)
    stripped = FULL_DATE_RE.sub("", compact)
    stripped = CHINESE_FULL_DATE_RE.sub("", stripped)
    stripped = MONTH_DAY_RE.sub("", stripped)
    stripped = DATE_SPAN_RE.sub("", stripped)
    for noise in ENTITY_QUERY_NOISE:
        stripped = stripped.replace(noise, "")
    stripped = re.sub(r"(?i)(?:pe|pb|roe|top|pdf)", "", stripped)
    stripped = re.sub(r"\d{1,3}", "", stripped)
    add(stripped)
    if stripped == compact:
        add(text)

    for segment in re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,12}", compact):
        candidate = segment
        candidate = FULL_DATE_RE.sub("", candidate)
        candidate = CHINESE_FULL_DATE_RE.sub("", candidate)
        candidate = MONTH_DAY_RE.sub("", candidate)
        candidate = DATE_SPAN_RE.sub("", candidate)
        for noise in ENTITY_QUERY_NOISE:
            candidate = candidate.replace(noise, "")
        candidate = re.sub(r"(?i)(pe|pb|roe|top|pdf)", "", candidate)
        add(candidate)

    return candidates[:8]


def parse_chinese_number(text: str) -> Optional[int]:
    cleaned = normalize_query_text(text).strip()
    if not cleaned:
        return None
    if cleaned.isdigit():
        return int(cleaned)
    if cleaned.startswith("零") and len(cleaned) > 1:
        return parse_chinese_number(cleaned[1:])
    if cleaned == "十":
        return 10
    if "百" in cleaned:
        left, right = cleaned.split("百", 1)
        hundreds = CN_NUM.get(left, 1) if left else 1
        rest = parse_chinese_number(right) if right else 0
        if rest is None:
            return None
        return hundreds * 100 + rest
    if "十" in cleaned:
        left, right = cleaned.split("十", 1)
        tens = CN_NUM.get(left, 1) if left else 1
        units = CN_NUM.get(right, 0) if right else 0
        return tens * 10 + units
    return CN_NUM.get(cleaned)


def extract_limit(query: str, default: int = 20) -> int:
    query = normalize_query_text(query)
    lowered = query.lower()
    match = re.search(r"(?:top|前)\s*(\d{1,3})", lowered)
    if match:
        return max(1, min(300, int(match.group(1))))
    compact = re.sub(r"\s+", "", lowered)
    match = re.search(r"前\s*([一二三四五六七八九十两俩百]+)", lowered) or re.search(r"前([一二三四五六七八九十两俩百]+)", compact)
    if match:
        parsed = parse_chinese_number(match.group(1))
        if parsed is not None:
            return max(1, min(300, parsed))
    if "前十" in query or "前十" in compact:
        return 10
    if "前二十" in query or "前二十" in compact:
        return 20
    if "前五十" in query or "前五十" in compact:
        return 50
    return default


def extract_date(query: str, today: Optional[date] = None) -> Optional[str]:
    effective_today = today or date.today()
    text = normalize_query_text(query)
    compact_match = re.search(r"(20\d{2})(\d{2})(\d{2})", re.sub(r"\D", "", text))
    if compact_match:
        year, month, day = compact_match.groups()
        return "%04d-%02d-%02d" % (int(year), int(month), int(day))
    match = re.search(r"(20\d{2})[-/.年]?\s*(\d{1,2})[-/.月]?\s*(\d{1,2})日?", text)
    if match:
        year, month, day = match.groups()
        return "%04d-%02d-%02d" % (int(year), int(month), int(day))
    chinese = _extract_chinese_date(text)
    if chinese:
        return chinese
    match = re.search(r"(\d{1,2})月(\d{1,2})[日号]?", text)
    if match:
        month, day = match.groups()
        return "%04d-%02d-%02d" % (effective_today.year, int(month), int(day))
    if "昨天" in text:
        return (effective_today - timedelta(days=1)).isoformat()
    if "今天" in text or "今日" in text:
        return effective_today.isoformat()
    return None


def _extract_chinese_date(text: str) -> Optional[str]:
    match = re.search(r"([二〇零一二三四五六七八九]{4})年([一二三四五六七八九十两俩]{1,3})月([一二三四五六七八九十两俩]{1,3})[日号]?", text)
    if not match:
        return None
    raw_year, raw_month, raw_day = match.groups()
    year_digits = []
    for char in raw_year:
        digit = CN_NUM.get(char)
        if digit is None or digit >= 10:
            return None
        year_digits.append(str(digit))
    month = parse_chinese_number(raw_month)
    day = parse_chinese_number(raw_day)
    if month is None or day is None:
        return None
    return "%04d-%02d-%02d" % (int("".join(year_digits)), month, day)


def extract_days(query: str, default: int = 30) -> int:
    text = normalize_query_text(query)
    if any(word in text for word in ["近半个月", "最近半个月", "过去半个月", "近半月", "最近半月", "过去半月"]):
        return 15
    match = re.search(r"(?:近|最近|过去)\s*(\d{1,4})\s*(?:天|日|个?交易日)", text)
    if match:
        return max(1, min(5000, int(match.group(1))))
    match = re.search(r"(?:近|最近|过去)\s*([零〇一二三四五六七八九十两俩百]+)\s*(?:天|日|个?交易日)", text)
    if match:
        parsed = parse_chinese_number(match.group(1))
        if parsed is not None:
            return max(1, min(5000, parsed))
    if any(word in text for word in ["近一周", "最近一周"]):
        return 7
    match = re.search(r"(?:近|最近|过去)\s*(\d{1,3}|[零〇一二三四五六七八九十两俩百]+)\s*(周|个?星期|个月|月|年)", text)
    if match:
        raw_count, unit = match.groups()
        count = int(raw_count) if raw_count.isdigit() else parse_chinese_number(raw_count)
        if count is not None:
            multiplier = 7 if unit in {"周", "星期", "个星期"} else 30 if unit in {"个月", "月"} else 365
            return max(1, min(5000, count * multiplier))
    if any(word in text for word in ["近一个月", "最近一个月"]):
        return 30
    if any(word in text for word in ["近三个月", "最近三个月"]):
        return 90
    if "近半年" in text:
        return 180
    if "近一年" in text:
        return 365
    if "半年报" not in text and ("半年" in text or "半年度" in text):
        return 180
    if "去年" in text or "一年走势" in text or "一年K线" in text or "一年k线" in text:
        return 365
    return default


def history_period(query: str) -> str:
    lowered = normalize_query_text(query).lower()
    if any(word in lowered for word in ["分钟", "分时", "minute", "1m", "5m", "15m", "30m", "60m"]):
        return "minute"
    if any(word in lowered for word in ["周k", "周线", "weekly", "week"]):
        return "weekly"
    if any(word in lowered for word in ["月k", "月线", "monthly"]):
        return "monthly"
    return "daily"


def adjust_mode(query: str) -> str:
    lowered = normalize_query_text(query).lower()
    if "后复权" in lowered or "hfq" in lowered:
        return "hfq"
    if "不复权" in lowered or "bfq" in lowered:
        return "none"
    return "qfq"


def rank_kind(query: str) -> str:
    lowered = normalize_query_text(query).lower()
    scan = lowered + re.sub(r"\s+", "", lowered)
    if any(word in scan for word in ["跌幅", "领跌", "跌得", "最惨", "最狠"]):
        return "losers"
    if "成交额" in scan or "金额" in scan or "成交最多" in scan:
        return "amount"
    if "成交量" in scan:
        return "volume"
    if "换手" in scan or "最活跃" in scan:
        return "turnover"
    if "量比" in scan:
        return "volume-ratio"
    if "振幅" in scan:
        return "amplitude"
    if "市值" in scan:
        return "market-cap"
    if "市盈" in scan or "pe" in scan:
        return "pe"
    if "市净" in scan or "pb" in scan:
        return "pb"
    return "gainers"


def rank_order(query: str, kind: str) -> str:
    lowered = normalize_query_text(query).lower()
    scan = lowered + re.sub(r"\s+", "", lowered)
    if kind == "losers":
        return "asc"
    if any(word in scan for word in ["最低", "最小", "从低到高", "低到高", "便宜", "别太高", "不太高", "lowest", "asc"]):
        return "asc"
    return "desc"


def money_period(query: str) -> str:
    text = normalize_query_text(query)
    scan = re.sub(r"(?i)top\s*\d{1,3}", "", text)
    scan = re.sub(r"前\s*(?:\d{1,3}|[一二三四五六七八九十两俩百]+)", "", scan)
    if re.search(r"20\s*[日天]", scan) or "二十日" in scan or "二十天" in scan:
        return "20d"
    if re.search(r"10\s*[日天]", scan) or "十日" in scan or "十天" in scan:
        return "10d"
    if re.search(r"5\s*[日天]", scan) or "五日" in scan or "五天" in scan:
        return "5d"
    if re.search(r"3\s*[日天]", scan) or "三日" in scan or "三天" in scan:
        return "3d"
    return "instant"


def generic_market_query(query: str) -> bool:
    text = normalize_query_text(query)
    compact = re.sub(r"\s+", "", text)
    if any(alias in text or alias in compact for alias in INDEX_ALIASES):
        return False
    return any(
        word in text or word in compact
        for word in [
            "大盘",
            "大A",
            "股市",
            "盘面",
            "两市",
            "市场整体",
            "三大指数",
            "今天市场",
            "市场怎么样",
            "市场热不热",
            "市场涨跌家数",
            "涨跌家数",
            "市场宽度",
            "赚钱效应",
            "涨的多还是跌的多",
            "涨多还是跌多",
            "指数们",
        ]
    )


def major_index_mention_count(query: str) -> int:
    text = normalize_query_text(query)
    compact = re.sub(r"[\s+＋,，、/]+", "", text)
    scan = text + compact
    groups = [
        ["上证指数", "上证综指", "沪指", "上证"],
        ["深证成指", "深成指", "深证"],
        ["创业板指", "创业板"],
        ["沪深300"],
        ["科创50"],
        ["北证50"],
        ["中证500"],
        ["中证1000"],
        ["国证2000"],
        ["中证红利"],
    ]
    return sum(1 for aliases in groups if any(alias in scan for alias in aliases))


def detect_intent(query: str) -> str:
    query = normalize_query_text(query)
    lowered = query.lower()
    scan = lowered + re.sub(r"\s+", "", lowered)
    if unsupported_query(query):
        return "unsupported"
    if generic_market_query(query) or major_index_mention_count(query) >= 2 or any(word in scan for word in ["指数快照", "大盘快照"]):
        return "market_snapshot"
    if any(word in scan for word in ["可转债", "转债"]) or ("债" in scan and SYMBOL_RE.search(re.sub(r"\s+", "", query))):
        return "bond"
    if any(word in scan for word in ["筹码", "筹码分布"]):
        return "chip"
    if any(word in scan for word in ["研报", "评级", "目标价", "机构怎么看", "机构看法", "机构评级"]):
        return "news"
    if any(word in scan for word in ["新闻", "快讯", "消息", "资讯", "利好", "利空", "有雷", "啥雷", "有没有雷", "有没有啥雷", "雷不雷", "雷没雷", "爆雷", "暴雷"]):
        return "news"
    if any(word in scan for word in ["大宗交易", "大宗成交", "有没有大宗", "有啥大宗", "大宗"]):
        return "block_trade"
    if any(word in scan for word in ["融资融券", "两融", "融资余额", "融资盘", "融券"]):
        return "margin_trading"
    if any(word in scan for word in ["公告", "年报", "季报", "业绩预告", "pdf", "披露", "减持", "增持", "回购"]):
        return "announcement"
    if "龙虎榜" in scan or "上榜" in scan:
        return "dragon_tiger"
    board_money_query = "资金" in scan and board_scope_hint(query) is not None
    if board_money_query or any(word in scan for word in ["资金流", "主力资金", "净流入", "净流出", "钱都往哪", "钱往哪", "钱流哪", "钱去哪", "资金去哪", "资金往哪", "资金在进还是出", "资金抱团", "资金在买", "吸金", "钱进没", "还有人买", "主力买", "主力卖", "主力在买", "主力在卖", "主力跑路", "跑路"]) or ("主力" in scan and any(word in scan for word in ["买啥", "卖啥", "买什么", "卖什么"])):
        return "money_flow"
    if any(word in scan for word in ["涨停", "跌停", "炸板", "炸了哪些板", "连板", "封板", "封单", "强势股", "回封", "地天板", "天地板", "封得", "封死", "开板", "跌停潮"]):
        return "limit_pool"
    if any(word in scan for word in ["板块", "行业", "概念", "题材", "这条线", "这块"]) or _looks_like_board_chat(query):
        return "sector"
    has_rank_word = any(word in scan for word in ["排行", "排名", "榜", "top", "前十", "前二十", "前50", "领涨", "领跌"])
    has_chat_rank_word = any(word in scan for word in ["哪个票最猛", "最猛", "最能打", "跌得最惨", "最惨", "最狠", "杀得最狠", "成交最多", "最活跃", "谁涨", "谁跌", "谁最", "换手最高", "便宜市盈率"])
    has_extreme_word = any(word in scan for word in ["最高", "最低", "最大", "最小", "highest", "lowest"])
    if not has_rank_word and not has_chat_rank_word and any(word in scan for word in ["开盘", "收盘", "昨收", "最高最低", "最高价", "最低价", "量比"]):
        return "quote_realtime"
    has_valuation_rank = (
        ("市盈" in scan or "市净" in scan or "pe" in scan or "pb" in scan)
        and any(word in scan for word in ["最高", "最低", "最大", "最小", "highest", "lowest", "股票"])
    )
    if has_rank_word or has_chat_rank_word or has_valuation_rank or has_extreme_word:
        return "rank"
    if any(word in scan for word in ["财务", "财报", "财务底子", "基本面", "基本资料", "基本情况", "估值", "roe", "毛利率", "净利率", "资产负债", "利润表", "现金流", "股东", "分红", "派息", "每年分", "市盈率", "市净率", "便宜了", "便宜不便宜"]):
        return "fundamental"
    if re.search(r"\b(?:pe|pb)\b", lowered):
        return "fundamental"
    if DATE_SPAN_RE.search(query) or any(word in scan for word in ["走势", "历史", "k线", "kline", "日线", "周线", "月线", "周k", "月k", "分钟", "分时", "近一个月", "最近", "咋走", "走的", "走得"]):
        return "quote_history"
    return "quote_realtime"


def unsupported_query(query: str) -> bool:
    lowered = normalize_query_text(query).lower()
    compact = re.sub(r"\s+", "", lowered)
    if any(word in compact for word in ["推荐股票", "推荐一只", "推荐一个", "买哪只", "买什么", "能买", "能不能买", "现在买", "值得买", "该买", "卖不卖", "买不买", "投资建议", "还能追", "能不能追", "能回本", "回本吗", "抄底吗", "能抄底"]):
        return True
    if any(word in compact for word in ["保证", "预测", "预判", "一定", "稳赚", "翻倍"]):
        return True
    if "明天" in compact and any(word in compact for word in ["涨", "跌", "涨停", "走势", "大盘", "买", "卖", "回本"]):
        return True
    if any(word in compact for word in ["会不会涨", "会不会跌", "能不能涨", "能不能跌", "会不会反弹", "能不能反弹", "反弹吗", "未来会涨", "未来会跌", "下周会涨", "下周会跌"]):
        return True
    return False


def limit_kind(query: str) -> str:
    lowered = (query or "").lower()
    scan = lowered + re.sub(r"\s+", "", lowered)
    if "跌停" in scan:
        return "down"
    if "强势" in scan or "回封" in scan or "地天板" in scan:
        return "strong"
    if "炸板" in scan or "炸了" in scan or "开板" in scan:
        return "broken"
    return "up"


def sector_kind(query: str) -> str:
    text = normalize_query_text(query)
    compact = re.sub(r"\s+", "", text)
    if "概念" in text or "概念" in compact:
        return "concept"
    for board, kind in BOARD_HINTS.items():
        if board.lower() in text.lower() or board.lower() in compact.lower():
            return kind
    return "industry"


def board_scope_hint(query: str) -> Optional[str]:
    text = normalize_query_text(query)
    compact = re.sub(r"\s+", "", text)
    for board, kind in BOARD_HINTS.items():
        if board.lower() in text.lower() or board.lower() in compact.lower():
            return kind
    return None


def sector_action(query: str, has_entity: bool) -> str:
    query = normalize_query_text(query)
    scan = query + re.sub(r"\s+", "", query)
    if has_entity or any(word in scan for word in ["属于", "所属", "哪个行业", "啥板块", "是哪个行业"]):
        return "belong"
    if any(word in scan for word in ["成分", "成份", "包含", "有哪些股票", "有哪些", "有哪些票", "有啥票", "有啥股票", "什么票", "哪些股票", "哪些票", "都有谁", "都有啥"]):
        return "constituents"
    return "rank"


def fundamental_pack(query: str) -> str:
    lowered = normalize_query_text(query).lower()
    scan = lowered + re.sub(r"\s+", "", lowered)
    if any(word in scan for word in ["股东", "十大股东", "户数"]):
        return "holders"
    if "分红" in scan or "派息" in scan or "分不分红" in scan or "每年分" in scan:
        return "dividend"
    if any(word in scan for word in ["财务", "财务底子", "资产负债", "利润表", "现金流", "财报", "roe", "毛利率", "净利率", "资产负债率"]):
        return "financials"
    if any(word in scan for word in ["估值", "贵不贵", "便宜了", "便宜不便宜", "市盈", "市净", "pe", "pb", "市值"]):
        return "valuation"
    if "全部" in scan or "完整" in scan:
        return "all"
    return "basic"


def build_route_plan(query: str, entity: Optional[Entity] = None, today: Optional[date] = None) -> RoutePlan:
    query = normalize_query_text(query)
    intent = detect_intent(query)
    resolved = entity or resolve_local_entity(
        query,
        prefer_index=intent in {"market_snapshot", "quote_history"},
        asset_hint="bond" if intent == "bond" else None,
    )

    if intent == "quote_realtime":
        return RoutePlan(intent, "quote-realtime", query, resolved, {})
    if intent == "quote_history":
        return RoutePlan(
            intent,
            "quote-history",
            query,
            resolved,
            {"days": extract_days(query), "period": history_period(query), "adjust": adjust_mode(query), "date": extract_date(query, today)},
        )
    if intent == "market_snapshot":
        return RoutePlan(intent, "market-snapshot", query, None, {})
    if intent == "rank":
        kind = rank_kind(query)
        return RoutePlan(intent, "rank", query, None, {"kind": kind, "order": rank_order(query, kind), "limit": extract_limit(query)})
    if intent == "limit_pool":
        return RoutePlan(intent, "limit-pool", query, None, {"kind": limit_kind(query), "date": extract_date(query, today), "limit": extract_limit(query, 50)})
    if intent == "money_flow":
        scope = "stock" if resolved is not None else "market"
        compact = re.sub(r"\s+", "", query)
        if "行业" in query or "行业" in compact:
            scope = "industry"
        if "概念" in query or "概念" in compact:
            scope = "concept"
        board_scope = board_scope_hint(query)
        if resolved is None and board_scope is not None:
            scope = board_scope
        return RoutePlan(intent, "money-flow", query, resolved, {"scope": scope, "period": money_period(query), "limit": extract_limit(query)})
    if intent == "sector":
        return RoutePlan(intent, "sector", query, resolved, {"kind": sector_kind(query), "action": sector_action(query, resolved is not None), "limit": extract_limit(query, 20)})
    if intent == "fundamental":
        return RoutePlan(intent, "fundamental", query, resolved, {"pack": fundamental_pack(query)})
    if intent == "announcement":
        return RoutePlan(intent, "announcement", query, resolved, {"keyword": announcement_keyword(query), "limit": extract_limit(query, 20), "date": extract_date(query, today)})
    if intent == "dragon_tiger":
        return RoutePlan(intent, "dragon-tiger", query, resolved, {"date": extract_date(query, today), "limit": extract_limit(query, 50)})
    if intent == "news":
        return RoutePlan(intent, "news", query, resolved, {"kind": news_kind(query), "keyword": news_keyword(query), "limit": extract_limit(query, 20)})
    if intent == "chip":
        return RoutePlan(intent, "chip", query, resolved, {"limit": extract_limit(query, 200)})
    if intent == "block_trade":
        return RoutePlan(intent, "block-trade", query, resolved, {"date": extract_date(query, today), "limit": extract_limit(query, 50)})
    if intent == "margin_trading":
        return RoutePlan(intent, "margin-trading", query, resolved, {"date": extract_date(query, today), "limit": extract_limit(query, 100)})
    if intent == "bond":
        action = "rank"
        bond_scan = query.lower() + re.sub(r"\s+", "", query.lower())
        if resolved is not None and (DATE_SPAN_RE.search(query) or any(word in bond_scan for word in ["走势", "历史", "k线", "kline", "日线", "最近", "咋走", "走的", "走得"])):
            action = "history"
        elif resolved is not None:
            action = "quote"
        return RoutePlan(intent, "bond", query, resolved, {"action": action, "limit": extract_limit(query), "days": extract_days(query)})
    if intent == "unsupported":
        return RoutePlan(intent, "unsupported", query, resolved, {})
    return RoutePlan("unknown", "smart-query", query, resolved, {})


def announcement_keyword(query: str) -> Optional[str]:
    query = normalize_query_text(query)
    scan = query + re.sub(r"\s+", "", query)
    for word in ["年报", "半年报", "季报", "一季报", "三季报", "业绩预告", "分红", "减持", "增持", "回购", "重大事项"]:
        if word in scan:
            return word
    return None


def news_kind(query: str) -> str:
    lowered = normalize_query_text(query).lower()
    scan = lowered + re.sub(r"\s+", "", lowered)
    if any(word in scan for word in ["研报", "评级", "目标价", "机构怎么看", "机构看法", "机构评级"]):
        return "research"
    return "news"


def news_keyword(query: str) -> Optional[str]:
    query = normalize_query_text(query)
    scan = query + re.sub(r"\s+", "", query)
    if any(word in scan for word in ["机构评级", "机构怎么看", "机构看法"]):
        return "研报"
    if any(word in scan for word in ["消息", "资讯", "利好", "利空", "有雷", "爆雷"]):
        return None
    for word in ["研报", "评级", "目标价", "新闻", "快讯"]:
        if word in scan:
            return word
    return None


def _looks_like_board_chat(query: str) -> bool:
    text = normalize_query_text(query)
    compact = re.sub(r"\s+", "", text)
    if not any(board.lower() in compact.lower() for board in BOARD_HINTS):
        return False
    explicit_board = any(word in compact for word in ["板块", "行业", "概念", "题材", "这条线", "这块", "这个方向", "方向"])
    if not explicit_board and resolve_local_entity(query) is not None:
        return False
    return any(word in compact for word in ["强不强", "最强", "哪个最强", "咋样", "怎么样", "有动静", "动静没", "拉了吗", "趴着", "起来了", "谁在涨", "有哪些", "有哪些票", "有啥票", "什么票", "哪些票", "都有谁", "这条线", "这块", "这个方向", "方向", "题材"])


def _clean_entity_candidate(value: str) -> str:
    cleaned = normalize_query_text(value).strip()
    cleaned = re.sub(r"^[的了呢吧啊呀嘛吗]+|[的了呢吧啊呀嘛吗]+$", "", cleaned)
    cleaned = re.sub(r"[\s,，。！？?！：:；;、（）()【】\[\]\"'“”‘’]+", "", cleaned)
    cleaned = re.sub(r"^[和与及]+|[和与及]+$", "", cleaned)
    return cleaned


def normalize_query_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\u200b", "").replace("\ufeff", "")
    normalized = normalized.replace("﹣", "-").replace("－", "-")
    return normalized


def _looks_like_non_entity_query(value: str) -> bool:
    if len(value) < 2:
        return True
    lowered = value.lower()
    if lowered in {"pe", "pb", "roe", "top"}:
        return True
    if value.isdigit() and len(value) != 6:
        return True
    if re.fullmatch(r"前?\d{1,3}", value):
        return True
    if re.fullmatch(r"前?[一二三四五六七八九十两俩百]+条?", value):
        return True
    if "年" in value and "月" in value and re.fullmatch(r"[二〇零一二三四五六七八九十两俩年月日号]+", value):
        return True
    if re.fullmatch(r"\d{0,3}日(?:入|出|资金)?", value):
        return True
    if re.fullmatch(r"[一二三四五六七八九十两俩百]+日(?:入|出|资金)?", value):
        return True
    generic_words = [
        "大盘",
        "市场",
        "指数",
        "涨停",
        "跌停",
        "炸板",
        "排行",
        "排名",
        "主力资金",
        "资金流",
        "资金",
        "流入",
        "流出",
        "成交额",
        "成交量",
        "可转债",
        "转债",
        "行业",
        "概念",
        "板块",
        "成分股",
        "成分",
        "有哪些股票",
        "有哪些",
        "包含",
        "最低",
        "最高",
        "最大",
        "最小",
        "回购",
        "减持",
        "增持",
        "重大事项",
        "新闻",
        "快讯",
        "有没有",
        "里",
        "研报",
        "评级",
        "目标价",
        "筹码",
        "筹码分布",
        "大宗交易",
        "大宗成交",
        "大宗",
        "融资融券",
        "两融",
        "融资",
        "融资余额",
        "融券",
        "全市场",
        "余额",
        "最火",
        "现在",
        "这票",
        "这个票",
        "这只票",
        "这公司",
        "有啥",
        "最近",
        "都往跑",
        "往跑",
        "在卖",
        "记录",
        "全部",
        "资产负债率",
    ]
    return value in generic_words
