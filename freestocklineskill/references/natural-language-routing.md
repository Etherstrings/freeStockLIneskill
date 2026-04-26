# 自然语言路由

默认入口：

```bash
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "<用户原话>"
```

## 路由优先级

1. `可转债`、`转债` -> `bond`
2. `新闻`、`快讯`、`研报`、`评级`、`目标价` -> `news`
3. `筹码`、`筹码分布` -> `chip`
4. `大宗交易`、`大宗成交` -> `block-trade`
5. `融资融券`、`两融`、`融资余额`、`融券` -> `margin-trading`
6. `公告`、`年报`、`季报`、`业绩预告`、`PDF`、`披露` -> `announcement`
7. `龙虎榜` -> `dragon-tiger`
8. `资金流`、`主力资金`、`净流入`、`净流出` -> `money-flow`
9. `涨停`、`跌停`、`炸板`、`连板`、`封板`、`强势股` -> `limit-pool`
10. `排行`、`排名`、`榜`、`top`、`前十`、`最高`、`最低` -> `rank`
11. `板块`、`行业`、`概念` -> `sector`
12. `财务`、`基本面`、`估值`、`ROE`、`毛利率`、`市盈率`、`市净率`、`股东`、`分红` -> `fundamental`
13. `走势`、`历史`、`K线`、`日线`、`周线`、`月线`、`分钟`、`最近` -> `quote-history`
14. `大盘`、`三大指数`、`市场整体`、`涨跌家数`、多指数同问 -> `market-snapshot`
15. 默认 -> `quote-realtime`

## 常见参数解析

- `前十`、`前20`、`top 50` -> `limit`
- `近30天`、`最近一个月`、`近半年` -> `days`
- `2026-04-24`、`20260424`、`4月24日`、`今天`、`昨天` -> `date`
- `前复权` -> `qfq`
- `后复权` -> `hfq`
- `不复权` -> `none`
- `行业` -> `sector --kind industry`
- `概念` -> `sector --kind concept`
- `属于什么板块` -> `sector --action belong`
- `板块成分股` -> `sector --action constituents`

## 标的解析

优先顺序：

1. 指数别名：上证指数、深成指、创业板指、沪深300、科创50、北证50。
2. 代码：`600519`、`600519.SH`、`sh600519`。
3. 常见中文名：贵州茅台、宁德时代等内置别名。
4. 腾讯 smartbox / 新浪 suggest 免费接口。

无法稳定识别时返回 `ok: false` 和候选提示，不让 Agent 猜。
