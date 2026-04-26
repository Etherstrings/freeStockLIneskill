# freeStockLIneskill

<div align="center">

**让 OpenClaw / Hermes Agent 用自然语言查询免费的 A 股生态公开数据。**

![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-1D4ED8?style=flat-square)
![ClawHub](https://img.shields.io/badge/Registry-ClawHub-0F766E?style=flat-square)
![Hermes](https://img.shields.io/badge/Agent-Hermes-7C3AED?style=flat-square)
![A-Share](https://img.shields.io/badge/Market-A--Share-C62828?style=flat-square)
![No API Key](https://img.shields.io/badge/API_Key-Not_Required-16A34A?style=flat-square)

自然语言路由 · 免费公开源 · 股票/指数/ETF/可转债 · 板块/资金/公告/财务 · 统一 JSON

[安装使用](#安装) · [自然语言入口](#使用) · [能力边界](freestocklineskill/references/capability-matrix.md) · [路由规则](freestocklineskill/references/natural-language-routing.md) · [常见问法](freestocklineskill/references/use-cases.md) · [Skill 地址](#skill-地址)

</div>

OpenClaw / Hermes 用的免费 A 股生态数据查询 skill。

核心承诺：不需要用户输入任何 apikey/API Key、Token、Cookie 或付费账号。首版在完全免费信源下已经覆盖较大范围的 A 股数据查询：股票、指数、ETF/LOF、可转债、行业/概念板块、实时行情、K 线、排行、涨停/跌停/炸板、资金流、财务估值、公告、龙虎榜等。

这个仓库不是 Codex 本机 skill。它发布和安装的目标是：

- OpenClaw：`~/.openclaw/workspace/skills/freestocklineskill`
- Hermes：GitHub skill 源指向 `freestocklineskill/`
- ClawHub：slug 使用 `freestocklineskill`

## Agent 快速安装

如果你是负责安装和调用的 Agent，按下面顺序执行，不要改名字，也不要猜路径：

```bash
bash scripts/install_skill.sh
```

安装后 skill 目录应是：

```text
~/.openclaw/workspace/skills/freestocklineskill
```

查询时永远先用自然语言入口：

```bash
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "贵州茅台最新价"
```

不要要求用户提供 API Key、Token、Cookie、iFinD、Wind、Choice、Tushare Pro 或任何付费账号。

## 能力

- 股票、指数、ETF/LOF、可转债标的解析
- 实时行情、K 线、大盘快照、市场宽度
- 涨跌幅、成交额、成交量、换手率、量比、振幅、市值、PE/PB 排行
- 涨停池、跌停池、炸板池、强势股池
- 个股/市场/行业/概念资金流
- 行业/概念板块排行、成分股、所属板块
- 基本面、估值、财务摘要、公告 PDF、龙虎榜、新闻/研报、筹码分布、大宗交易、融资融券、可转债

不需要用户填写 API Key、Token、Cookie 或付费账号。

## 安装

```bash
uv sync
bash scripts/install_skill.sh
```

默认安装到：

```text
~/.openclaw/workspace/skills/freestocklineskill
```

自定义安装位置：

```bash
OPENCLAW_SKILL_DIR=/path/to/freestocklineskill bash scripts/install_skill.sh
```

## 使用

自然语言主入口：

```bash
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "贵州茅台最新价"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "宁德时代近一个月走势"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "今天大盘怎么样"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "A股成交额前十"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "今日涨停"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "主力资金净流入前十"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "贵州茅台公告"
python3 freestocklineskill/scripts/stockline_cli.py smart-query --query "可转债涨幅榜前十"
```

列出显式能力：

```bash
python3 freestocklineskill/scripts/stockline_cli.py endpoint-list
```

## 验证

```bash
uv run pytest -q
bash scripts/validate_skill.sh
```

## Skill 地址

当前外部 skill 入口：

- ClawHub / OpenClaw 页面：`https://clawhub.ai/etherstrings/freestocklineskill`
- Hermes Agent GitHub skill 源：`https://github.com/Etherstrings/freeStockLIneskill/tree/main/freestocklineskill`

补充说明：

- 当前准备发布版本：`0.1.0`
- GitHub 仓库名使用展示名 `freeStockLIneskill`
- OpenClaw / Hermes slug 和目录名使用合法小写 `freestocklineskill`

## 发布到 ClawHub

```bash
clawhub publish freestocklineskill \
  --slug freestocklineskill \
  --name "freeStockLIneskill" \
  --version 0.1.0 \
  --changelog "首版免费 A 股生态自然语言数据查询 skill。"
```

## 结构

```text
freestocklineskill/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/stockline_cli.py
  scripts/runtime/freestocklineskill_runtime/
scripts/
  install_skill.sh
  validate_skill.sh
tests/
```
