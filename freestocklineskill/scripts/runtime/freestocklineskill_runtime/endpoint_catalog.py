from __future__ import annotations

from typing import Dict, List


ENDPOINTS: List[Dict[str, object]] = [
    {
        "name": "smart-query",
        "description": "自然语言万能入口。Agent 首选，把用户原话放进 --query。",
        "example": 'python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "贵州茅台最新价"',
    },
    {"name": "search-entity", "description": "解析股票/指数/ETF/可转债名称或代码。"},
    {"name": "quote-realtime", "description": "个股、指数、ETF、可转债实时行情。"},
    {"name": "quote-history", "description": "日/周/月/分钟 K 线，支持 qfq/hfq/none。"},
    {"name": "market-snapshot", "description": "主要指数与市场宽度快照。"},
    {"name": "rank", "description": "涨跌幅、成交额、成交量、换手率、量比、振幅、市值、PE/PB 榜。"},
    {"name": "limit-pool", "description": "涨停池、跌停池、炸板池、强势股池。"},
    {"name": "money-flow", "description": "个股、全市场、行业、概念资金流。"},
    {"name": "sector", "description": "行业/概念板块排行、成分股、个股所属板块。"},
    {"name": "fundamental", "description": "基本信息、估值、财务报表、股东、分红。"},
    {"name": "announcement", "description": "公告列表与 PDF 链接。"},
    {"name": "dragon-tiger", "description": "龙虎榜。"},
    {"name": "news", "description": "公开新闻、快讯、研报、评级。"},
    {"name": "chip", "description": "筹码分布 best-effort。"},
    {"name": "block-trade", "description": "大宗交易明细。"},
    {"name": "margin-trading", "description": "融资融券明细。"},
    {"name": "bond", "description": "可转债报价、K 线、排行。"},
]
