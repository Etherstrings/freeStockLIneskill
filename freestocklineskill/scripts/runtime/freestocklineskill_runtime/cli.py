from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .endpoint_catalog import ENDPOINTS
from .envelope import failure
from .envelope import success
from .routing import Entity
from .routing import RoutePlan
from .routing import build_route_plan
from .routing import entity_search_candidates
from .routing import entity_from_symbol
from .routing import normalize_symbol
from .routing import resolve_local_entity
from .sources import SourceClient


def main(argv: Optional[List[str]] = None) -> int:
    result = run_command(sys.argv[1:] if argv is None else argv)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def run_command(argv: List[str]) -> Dict[str, Any]:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return failure(intent="cli", error_type="invalid_request", error_message="invalid arguments")

    client = SourceClient(timeout=getattr(args, "timeout", 12.0))
    try:
        if args.command == "endpoint-list":
            return success(intent="endpoint_list", data={"endpoints": ENDPOINTS})
        if args.command == "search-entity":
            return handle_search_entity(client, args.query)
        if args.command == "smart-query":
            return handle_smart_query(client, args.query)
        if args.command == "quote-realtime":
            entity = resolve_entity_for_arg(client, args.symbol, "quote_realtime")
            return wrap_result("quote_realtime", args.symbol, entity.to_dict(), client.quote_realtime(entity))
        if args.command == "quote-history":
            entity = resolve_entity_for_arg(client, args.symbol, "quote_history")
            return wrap_result(
                "quote_history",
                args.symbol,
                entity.to_dict(),
                client.quote_history(entity, days=args.days, period=args.period, adjust=args.adjust),
            )
        if args.command == "market-snapshot":
            return wrap_result("market_snapshot", "", {}, client.market_snapshot())
        if args.command == "rank":
            return wrap_result("rank", "", {"kind": args.kind, "order": args.order, "limit": args.limit}, client.rank(args.kind, args.limit, args.order))
        if args.command == "limit-pool":
            return wrap_result(
                "limit_pool",
                "",
                {"kind": args.kind, "date": args.date, "limit": args.limit},
                client.limit_pool(args.kind, args.date, args.limit),
            )
        if args.command == "money-flow":
            entity = resolve_entity_for_arg(client, args.symbol, "money_flow") if args.symbol else None
            normalized = {"scope": args.scope, "period": args.period, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("money_flow", args.symbol or "", normalized, client.money_flow(args.scope, args.period, entity, args.limit))
        if args.command == "sector":
            entity = resolve_entity_for_arg(client, args.symbol, "sector") if args.symbol else None
            normalized = {"kind": args.kind, "action": args.action, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("sector", args.symbol or "", normalized, client.sector(args.kind, args.action, entity, args.query or "", args.limit))
        if args.command == "fundamental":
            entity = resolve_entity_for_arg(client, args.symbol, "fundamental")
            return wrap_result("fundamental", args.symbol, {"entity": entity.to_dict(), "pack": args.pack}, client.fundamental(entity, args.pack))
        if args.command == "announcement":
            entity = resolve_entity_for_arg(client, args.symbol, "announcement") if args.symbol else None
            normalized = {"keyword": args.keyword, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("announcement", args.symbol or "", normalized, client.announcement(entity, args.keyword, args.limit))
        if args.command == "dragon-tiger":
            entity = resolve_entity_for_arg(client, args.symbol, "dragon_tiger") if args.symbol else None
            normalized = {"date": args.date, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("dragon_tiger", args.symbol or "", normalized, client.dragon_tiger(args.date, entity, args.limit))
        if args.command == "news":
            entity = resolve_entity_for_arg(client, args.symbol, "news") if args.symbol else None
            normalized = {"kind": args.kind, "keyword": args.keyword, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("news", args.symbol or args.keyword or "", normalized, client.news(entity, args.keyword, args.kind, args.limit))
        if args.command == "chip":
            entity = resolve_entity_for_arg(client, args.symbol, "chip")
            return wrap_result("chip", args.symbol, {"entity": entity.to_dict(), "limit": args.limit}, client.chip(entity, args.limit))
        if args.command == "block-trade":
            entity = resolve_entity_for_arg(client, args.symbol, "block_trade") if args.symbol else None
            normalized = {"date": args.date, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("block_trade", args.symbol or "", normalized, client.block_trade(args.date, entity, args.limit))
        if args.command == "margin-trading":
            entity = resolve_entity_for_arg(client, args.symbol, "margin_trading") if args.symbol else None
            normalized = {"date": args.date, "limit": args.limit}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("margin_trading", args.symbol or "", normalized, client.margin_trading(args.date, entity, args.limit))
        if args.command == "bond":
            entity = resolve_entity_for_arg(client, args.symbol, "bond") if args.symbol else None
            normalized = {"action": args.action, "limit": args.limit, "days": args.days}
            if entity is not None:
                normalized["entity"] = entity.to_dict()
            return wrap_result("bond", args.symbol or "", normalized, client.bond(args.action, entity, args.limit, args.days))
    except Exception as exc:
        return failure(
            intent=command_to_intent(args.command),
            query=getattr(args, "query", "") or getattr(args, "symbol", "") or "",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    return failure(intent="cli", error_type="invalid_request", error_message="unknown command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stockline-cli")
    parser.add_argument("--timeout", type=float, default=12.0)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("smart-query")
    p.add_argument("--query", required=True)

    p = subparsers.add_parser("search-entity")
    p.add_argument("--query", required=True)

    p = subparsers.add_parser("quote-realtime")
    p.add_argument("--symbol", required=True)

    p = subparsers.add_parser("quote-history")
    p.add_argument("--symbol", required=True)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--period", choices=["daily", "weekly", "monthly", "minute"], default="daily")
    p.add_argument("--adjust", choices=["qfq", "hfq", "none"], default="qfq")

    subparsers.add_parser("market-snapshot")

    p = subparsers.add_parser("rank")
    p.add_argument("--kind", choices=["gainers", "losers", "amount", "volume", "turnover", "volume-ratio", "amplitude", "market-cap", "pe", "pb"], default="gainers")
    p.add_argument("--order", choices=["auto", "asc", "desc"], default="auto")
    p.add_argument("--limit", type=int, default=20)

    p = subparsers.add_parser("limit-pool")
    p.add_argument("--kind", choices=["up", "down", "broken", "strong"], default="up")
    p.add_argument("--date")
    p.add_argument("--limit", type=int, default=50)

    p = subparsers.add_parser("money-flow")
    p.add_argument("--scope", choices=["stock", "market", "industry", "concept"], default="market")
    p.add_argument("--symbol")
    p.add_argument("--period", choices=["instant", "3d", "5d", "10d", "20d"], default="instant")
    p.add_argument("--limit", type=int, default=20)

    p = subparsers.add_parser("sector")
    p.add_argument("--kind", choices=["industry", "concept"], default="industry")
    p.add_argument("--action", choices=["rank", "constituents", "belong"], default="rank")
    p.add_argument("--symbol")
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=20)

    p = subparsers.add_parser("fundamental")
    p.add_argument("--symbol", required=True)
    p.add_argument("--pack", choices=["basic", "valuation", "financials", "holders", "dividend", "all"], default="basic")

    p = subparsers.add_parser("announcement")
    p.add_argument("--symbol")
    p.add_argument("--keyword")
    p.add_argument("--limit", type=int, default=20)

    p = subparsers.add_parser("dragon-tiger")
    p.add_argument("--date")
    p.add_argument("--symbol")
    p.add_argument("--limit", type=int, default=50)

    p = subparsers.add_parser("news")
    p.add_argument("--symbol")
    p.add_argument("--keyword")
    p.add_argument("--kind", choices=["news", "research"], default="news")
    p.add_argument("--limit", type=int, default=20)

    p = subparsers.add_parser("chip")
    p.add_argument("--symbol", required=True)
    p.add_argument("--limit", type=int, default=200)

    p = subparsers.add_parser("block-trade")
    p.add_argument("--date")
    p.add_argument("--symbol")
    p.add_argument("--limit", type=int, default=50)

    p = subparsers.add_parser("margin-trading")
    p.add_argument("--date")
    p.add_argument("--symbol")
    p.add_argument("--limit", type=int, default=100)

    p = subparsers.add_parser("bond")
    p.add_argument("--action", choices=["quote", "history", "rank"], default="rank")
    p.add_argument("--symbol")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--days", type=int, default=30)

    subparsers.add_parser("endpoint-list")
    return parser


def handle_search_entity(client: SourceClient, query: str) -> Dict[str, Any]:
    local = resolve_local_entity(query)
    if local is not None:
        return success(intent="search_entity", query=query, normalized={"entity": local.to_dict()}, source_chain=[{"source": "local_alias", "ok": True}], data=local.to_dict())
    resolved = search_entity_candidates(client, query)
    entity = resolved["entity"]
    return success(
        intent="search_entity",
        query=query,
        normalized={"entity": entity.to_dict()},
        source_chain=resolved["source_chain"],
        data=entity.to_dict(),
        warnings=resolved["warnings"],
    )


def handle_smart_query(client: SourceClient, query: str) -> Dict[str, Any]:
    plan = build_route_plan(query)
    if plan.command == "unsupported":
        return failure(
            intent=plan.intent,
            query=query,
            error_type="unsupported_request",
            error_message="freeStockLIneskill 只做免费公开数据查询，不做预测、荐股或收益保证",
            normalized=plan.normalized(),
            data={"hints": ["可以改问：某股票最新价、近一个月走势、公告、资金流、龙虎榜、板块成分股等"]},
        )
    may_have_entity = bool(entity_search_candidates(query))
    should_search_entity = plan.command in {
        "quote-realtime",
        "quote-history",
        "fundamental",
        "money-flow",
        "announcement",
        "dragon-tiger",
        "news",
        "chip",
        "block-trade",
        "margin-trading",
        "bond",
    }
    if plan.command == "sector" and plan.params.get("action") == "belong":
        should_search_entity = True
    if plan.command == "money-flow" and plan.params.get("scope") in {"industry", "concept"}:
        should_search_entity = False
    if plan.command == "bond" and plan.params.get("action") == "rank":
        should_search_entity = False
    if should_search_entity and plan.entity is None and may_have_entity:
        try:
            plan = build_route_plan(query, entity=search_entity_candidates(client, query, asset_hint="bond" if plan.intent == "bond" else None)["entity"])
        except Exception:
            pass
    required_entity_missing = plan.command in {"quote-realtime", "quote-history", "fundamental"} and plan.entity is None
    optional_entity_was_requested = may_have_entity and plan.command in {"money-flow", "announcement", "dragon-tiger", "news", "block-trade", "margin-trading", "bond"} and plan.entity is None
    if plan.command == "money-flow" and plan.params.get("scope") in {"market", "industry", "concept"}:
        optional_entity_was_requested = False
    if plan.command == "bond" and plan.params.get("action") == "rank":
        optional_entity_was_requested = False
    required_entity_missing = required_entity_missing or (plan.command in {"chip"} and plan.entity is None)
    if plan.command == "sector" and plan.params.get("action") == "belong" and plan.entity is None:
        required_entity_missing = True
    if required_entity_missing or optional_entity_was_requested:
        return failure(
            intent=plan.intent,
            query=query,
            error_type="entity_not_found",
            error_message="无法从自然语言中稳定识别股票、指数、ETF 或可转债标的",
            normalized=plan.normalized(),
            data={"hints": ["请提供 6 位代码，如 600519", "请提供更完整的中文简称，如 贵州茅台"]},
        )
    try:
        result = execute_plan(client, plan)
        return wrap_result(plan.intent, query, plan.normalized(), result)
    except Exception as exc:
        return failure(
            intent=plan.intent,
            query=query,
            error_type=type(exc).__name__,
            error_message=str(exc),
            normalized=plan.normalized(),
        )


def search_entity_candidates(client: SourceClient, query: str, asset_hint: Optional[str] = None) -> Dict[str, Any]:
    warnings: List[str] = []
    tried: List[str] = []
    for candidate in entity_search_candidates(query):
        if candidate in tried:
            continue
        tried.append(candidate)
        local = resolve_local_entity(candidate, asset_hint=asset_hint)
        if local is not None:
            return {
                "entity": local,
                "source_chain": [{"source": "local_alias", "ok": True, "query": candidate}],
                "warnings": warnings,
            }
        normalized = normalize_symbol(candidate, asset_hint=asset_hint)
        if normalized:
            return {
                "entity": entity_from_symbol(candidate, normalized, query=query),
                "source_chain": [{"source": "symbol_rule", "ok": True, "query": candidate}],
                "warnings": warnings,
            }
        try:
            resolved = client.search_entity(candidate)
            for item in resolved.get("source_chain", []):
                if isinstance(item, dict):
                    item.setdefault("query", candidate)
            if candidate != query:
                resolved.setdefault("warnings", []).append("已从自然语言中抽取标的候选：%s" % candidate)
            return resolved
        except Exception as exc:
            warnings.append("候选标的 %s 解析失败: %s" % (candidate, exc))
    raise RuntimeError("无法解析标的：%s" % query)


def execute_plan(client: SourceClient, plan: RoutePlan) -> Dict[str, Any]:
    if plan.command == "quote-realtime":
        return client.quote_realtime(plan.entity)  # type: ignore[arg-type]
    if plan.command == "quote-history":
        return client.quote_history(
            plan.entity,  # type: ignore[arg-type]
            days=plan.params.get("days", 30),
            period=plan.params.get("period", "daily"),
            adjust=plan.params.get("adjust", "qfq"),
        )
    if plan.command == "market-snapshot":
        return client.market_snapshot()
    if plan.command == "rank":
        return client.rank(plan.params.get("kind", "gainers"), plan.params.get("limit", 20), plan.params.get("order", "desc"))
    if plan.command == "limit-pool":
        return client.limit_pool(plan.params.get("kind", "up"), plan.params.get("date"), plan.params.get("limit", 50))
    if plan.command == "money-flow":
        return client.money_flow(plan.params.get("scope", "market"), plan.params.get("period", "instant"), plan.entity, plan.params.get("limit", 20))
    if plan.command == "sector":
        return client.sector(plan.params.get("kind", "industry"), plan.params.get("action", "rank"), plan.entity, plan.query, plan.params.get("limit", 20))
    if plan.command == "fundamental":
        return client.fundamental(plan.entity, plan.params.get("pack", "basic"))  # type: ignore[arg-type]
    if plan.command == "announcement":
        return client.announcement(plan.entity, plan.params.get("keyword"), plan.params.get("limit", 20))
    if plan.command == "dragon-tiger":
        return client.dragon_tiger(plan.params.get("date"), plan.entity, plan.params.get("limit", 50))
    if plan.command == "news":
        return client.news(plan.entity, plan.params.get("keyword"), plan.params.get("kind", "news"), plan.params.get("limit", 20))
    if plan.command == "chip":
        return client.chip(plan.entity, plan.params.get("limit", 200))  # type: ignore[arg-type]
    if plan.command == "block-trade":
        return client.block_trade(plan.params.get("date"), plan.entity, plan.params.get("limit", 50))
    if plan.command == "margin-trading":
        return client.margin_trading(plan.params.get("date"), plan.entity, plan.params.get("limit", 100))
    if plan.command == "bond":
        return client.bond(plan.params.get("action", "rank"), plan.entity, plan.params.get("limit", 20), plan.params.get("days", 30))
    raise RuntimeError("unsupported route command: %s" % plan.command)


def wrap_result(intent: str, query: str, normalized: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    return success(
        intent=intent,
        query=query,
        normalized=normalized,
        source_chain=result.get("source_chain", []),
        data=result.get("data"),
        warnings=result.get("warnings", []),
        trade_date=_extract_trade_date(result.get("data")),
        source_status=_source_status(result.get("source_chain", [])),
    )


def resolve_entity_for_arg(client: SourceClient, raw: str, intent: str) -> Entity:
    local = resolve_local_entity(raw, asset_hint="bond" if intent == "bond" else None)
    if local is not None:
        return local
    normalized = normalize_symbol(raw, asset_hint="bond" if intent == "bond" else None)
    if normalized:
        return entity_from_symbol(raw, normalized, query="转债" if intent == "bond" else "")
    return client.search_entity(raw)["entity"]


def command_to_intent(command: str) -> str:
    return command.replace("-", "_")


def _source_status(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {str(item.get("source")): bool(item.get("ok")) for item in chain}


def _extract_trade_date(data: Any) -> Any:
    if isinstance(data, dict):
        for key in ("trade_date", "end_date", "date"):
            if data.get(key):
                return data[key]
        if isinstance(data.get("data"), dict):
            return _extract_trade_date(data["data"])
    return None
