---
name: freestocklineskill
description: Free no-API-key A-share ecosystem data query skill for OpenClaw and Hermes. Use when users ask for A股、沪深京股票、指数、ETF/LOF、可转债、行业/概念板块、实时行情、K线、涨跌排行、涨停/跌停/炸板、资金流、财务估值、公告、龙虎榜、大宗交易、融资融券、新闻快讯、筹码等公开数据查询，并且不希望填写 API Key、Token、Cookie 或付费账号。
version: "0.1.1"
homepage: https://github.com/Etherstrings/freeStockLIneskill#donate
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# freeStockLIneskill

## Payment / Donation Notice

This skill is free to install on ClawHub, but it is donation-supported.

If freeStockLIneskill helps you save time, please support ongoing use and maintenance here:

- Donate / Sponsor: <https://github.com/Etherstrings/freeStockLIneskill#donate>
- Afdian: <https://ifdian.net/a/etherstrings>
- ClawHub page: <https://clawhub.ai/etherstrings/freestocklineskill>

这是给 OpenClaw / Hermes 用的 A 股免费公开源数据查询 skill。

它的设计目标很明确：不需要用户输入任何 apikey/API Key、Token、Cookie 或付费账号；在完全免费信源下尽量覆盖较大范围的 A 股生态数据，包括股票、指数、ETF/LOF、可转债、行业/概念板块、行情/K 线、排行、涨停/跌停/炸板、资金流、财务估值、公告、龙虎榜等。

## 先执行这个

只要用户是自然语言提问，Agent 不要猜接口，直接把用户原话交给 `smart-query`：

```bash
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "贵州茅台最新价"
```

脚本会自动完成：

- 判断意图：行情、K 线、大盘、榜单、涨停、资金流、板块、财务、公告、龙虎榜、可转债等。
- 解析标的：股票名、6 位代码、`600519.SH`、`sh600519`、指数、ETF、可转债、行业/概念。
- 调用免费源：腾讯财经、新浪财经、东方财富、巨潮资讯、AKShare、efinance。
- 输出统一 JSON：成功和失败都包含 `ok`、`intent`、`normalized`、`source_chain`、`data`、`warnings`、`meta`。

不要要求用户提供 API Key、Token、Cookie、iFinD、Wind、Choice、Tushare Pro 或任何付费账号。

## 常用命令

```bash
python3 freestocklineskill/scripts/stockline_cli.py endpoint-list
python3 freestocklineskill/scripts/stockline_cli.py search-entity --query "宁德时代"
python3 freestocklineskill/scripts/stockline_cli.py quote-realtime --symbol 600519
python3 freestocklineskill/scripts/stockline_cli.py quote-history --symbol 300750 --days 30 --period daily --adjust qfq
python3 freestocklineskill/scripts/stockline_cli.py market-snapshot
python3 freestocklineskill/scripts/stockline_cli.py rank --kind amount --limit 10
python3 freestocklineskill/scripts/stockline_cli.py limit-pool --kind up --limit 30
python3 freestocklineskill/scripts/stockline_cli.py money-flow --scope market --period instant --limit 20
python3 freestocklineskill/scripts/stockline_cli.py sector --kind industry --action rank
python3 freestocklineskill/scripts/stockline_cli.py fundamental --symbol 600519 --pack all
python3 freestocklineskill/scripts/stockline_cli.py announcement --symbol 600519 --keyword 年报
python3 freestocklineskill/scripts/stockline_cli.py dragon-tiger --date 2026-04-24
python3 freestocklineskill/scripts/stockline_cli.py news --symbol 300750 --kind news --limit 10
python3 freestocklineskill/scripts/stockline_cli.py news --symbol 300750 --kind research --limit 10
python3 freestocklineskill/scripts/stockline_cli.py chip --symbol 600519 --limit 100
python3 freestocklineskill/scripts/stockline_cli.py block-trade --date 2026-04-24 --limit 50
python3 freestocklineskill/scripts/stockline_cli.py margin-trading --date 2026-04-24 --limit 100
python3 freestocklineskill/scripts/stockline_cli.py bond --action rank --limit 20
```

## Agent 规则

1. 高频自然语言先用 `smart-query`。
2. 用户明确说查某类数据时，才使用显式命令。
3. 读 [references/capability-matrix.md](references/capability-matrix.md) 判断稳定支持、best-effort、还是不要假装能做。
4. 读 [references/natural-language-routing.md](references/natural-language-routing.md) 了解关键词如何路由。
5. 读 [references/use-cases.md](references/use-cases.md) 找类似用户问法。
6. 输出给用户时必须带来源、交易日/时间戳、必要 warning。
7. `ok: false` 时不要编造数据，复述 `error.message` 和可尝试的下一步。

## 能力边界

稳定支持：

- 个股、指数、ETF、可转债实时行情
- 日/周/月/分钟 K 线
- 大盘指数与市场宽度
- A 股涨跌幅、成交额、成交量、换手率、量比、振幅、市值、PE/PB 排行
- 涨停池、跌停池、炸板池、强势股池
- 全市场主力资金流排行
- 行业/概念板块排行、成分股、个股所属板块
- 基本信息、估值、公开财务摘要、公告 PDF、龙虎榜、可转债排行
- 新闻快讯、公开研报/评级、筹码分布、大宗交易、融资融券 best-effort

Best-effort：

- 个股资金流、行业/概念资金流
- 筹码分布
- 股东、分红、研报、新闻快讯、大宗交易、融资融券
- 公开源字段会随网站变化，返回中必须保留 `warnings`

不要假装能做：

- 实时交易所 Level-2 逐笔、盘口队列
- Wind/Choice/iFinD 专属字段
- 需要登录、Cookie、Token 或付费授权的数据
- 投资建议、买卖点承诺、收益保证

## Support

- Support ongoing development: <https://github.com/Etherstrings/freeStockLIneskill#donate>
- OpenClaw / ClawHub skill page: <https://clawhub.ai/etherstrings/freestocklineskill>

### Donate

Alipay:

![Alipay QR](https://raw.githubusercontent.com/Etherstrings/freeStockLIneskill/main/docs/assets/donate/alipay_clawhub.jpg)

WeChat Pay:

![WeChat Pay QR](https://raw.githubusercontent.com/Etherstrings/freeStockLIneskill/main/docs/assets/donate/wechat_clawhub.jpg)
