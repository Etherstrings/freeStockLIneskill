# 能力矩阵

给 Agent 用，不是营销文档。先判断能力，再调用命令。

## 稳定支持

| 能力 | 入口 | 免费源 |
|---|---|---|
| 股票/指数/ETF/可转债实时行情 | `smart-query` / `quote-realtime` | 腾讯财经、AKShare |
| 日/周/月/分钟 K 线 | `smart-query` / `quote-history` | 腾讯财经、efinance |
| 大盘与市场宽度 | `smart-query` / `market-snapshot` | 腾讯财经、东方财富 |
| 涨跌幅/成交额/成交量/换手率/量比/振幅/市值/PE/PB 榜 | `smart-query` / `rank` | 东方财富、新浪 |
| 涨停池/跌停池/炸板池/强势股池 | `smart-query` / `limit-pool` | 东方财富 |
| 全市场主力资金净流入排行 | `smart-query` / `money-flow` | 新浪、AKShare |
| 行业/概念板块排行 | `smart-query` / `sector` | AKShare |
| 板块成分股 | `sector --action constituents` | AKShare |
| 个股所属板块 | `sector --action belong` | efinance |
| 公司基础信息/估值 | `smart-query` / `fundamental` | 腾讯、AKShare |
| 公告列表/PDF 链接 | `smart-query` / `announcement` | 巨潮资讯 |
| 龙虎榜 | `smart-query` / `dragon-tiger` | AKShare |
| 可转债排行/报价/K 线 | `smart-query` / `bond` | AKShare |
| 新闻快讯/公开研报/评级 | `smart-query` / `news` | AKShare/东方财富公开源 |
| 大宗交易 | `smart-query` / `block-trade` | AKShare/东方财富公开源 |
| 融资融券 | `smart-query` / `margin-trading` | AKShare/交易所公开源 |

## Best-effort

| 能力 | 入口 | 说明 |
|---|---|---|
| 个股资金流 | `money-flow --scope stock` | 公开源字段和接口稳定性随网站变化 |
| 行业/概念资金流 | `money-flow --scope industry/concept` | 返回时必须保留 warning |
| 筹码分布 | `smart-query` / `chip` | 免费源不稳定，必须保留 warning |
| 股东/分红/研报/新闻快讯 | `fundamental` / `news` | 按公开源可得字段返回 |

## 不要假装能做

- 需要登录、Cookie、Token、API Key、付费账号的数据。
- Wind、Choice、iFinD、Tushare Pro 专属字段。
- 实时逐笔成交、Level-2 盘口队列。
- 自动生成买卖建议、目标价承诺、收益保证。
- 全市场复杂组合条件选股如果现有 `rank`、`sector`、`fundamental` 无法表达，就返回当前未覆盖。

## 回答口径

- 稳定能力：直接调用并说明来源。
- Best-effort：调用，返回时说明公开源波动和 warning。
- 不支持：不要编 payload，不要编数据，直接说明当前 skill 不覆盖。
