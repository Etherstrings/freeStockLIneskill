# 免费信源

本 skill 不要求用户配置任何 API Key、Token、Cookie 或付费账号。

## 高频直连源

- 腾讯财经公开接口：实时行情、指数行情、K 线。
- 新浪财经公开接口：A 股排行、主力资金榜、名称 suggest。
- 东方财富公开接口：排行、涨停/跌停/炸板/强势股池、市场宽度。
- 巨潮资讯公开接口：公告列表、PDF 附件链接。

## 免费 Python 库

- AKShare：财务、资金流、龙虎榜、板块、可转债等广覆盖能力。
- efinance：东方财富封装，适合行情、K 线、ETF、所属板块等兜底。
- pandas：把 DataFrame 统一转成 JSON records。

## 数据使用注意

- 免费源可能延迟、限流、反爬或字段调整。
- 返回 JSON 中 `source_chain` 表示尝试过哪些源。
- 返回 JSON 中 `warnings` 表示 best-effort 或回退情况。
- 公开源返回的日期可能是最近交易日，不一定等于自然日今天。
