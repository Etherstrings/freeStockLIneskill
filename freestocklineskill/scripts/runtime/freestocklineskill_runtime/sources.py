from __future__ import annotations

from contextlib import redirect_stderr
from contextlib import redirect_stdout
from datetime import date
import io
import json
import os
import re
import warnings
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL.*")

import requests

from .routing import Entity
from .routing import entity_from_symbol
from .routing import normalize_symbol


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
EASTMONEY_UT = "7eea3edcaed734bea9cbfc24409ed989"
A_STOCK_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"


class SourceError(RuntimeError):
    pass


class SourceClient:
    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "close",
            }
        )

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, referer: Optional[str] = None) -> requests.Response:
        headers = {"Referer": referer} if referer else None
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _post(self, url: str, data: Optional[Dict[str, Any]] = None, referer: Optional[str] = None) -> requests.Response:
        headers = {"Referer": referer} if referer else None
        response = self.session.post(url, data=data, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _json_get(self, url: str, params: Optional[Dict[str, Any]] = None, referer: Optional[str] = None) -> Dict[str, Any]:
        response = self._get(url, params=params, referer=referer)
        payload = response.json()
        if not isinstance(payload, dict):
            raise SourceError("response JSON is not an object")
        return payload

    def search_entity(self, query: str) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        warnings: List[str] = []
        for name, func in [
            ("tencent_smartbox", self._search_tencent),
            ("sina_suggest", self._search_sina),
        ]:
            try:
                entity = func(query)
                chain.append({"source": name, "ok": entity is not None})
                if entity is not None:
                    return {"entity": entity, "source_chain": chain, "warnings": warnings}
            except Exception as exc:
                chain.append({"source": name, "ok": False, "error": str(exc)})
                warnings.append("%s 解析失败: %s" % (name, exc))
        raise SourceError("无法解析标的：%s" % query)

    def _search_tencent(self, query: str) -> Optional[Entity]:
        response = self._get("https://smartbox.gtimg.cn/s3/", {"q": query, "t": "all"}, referer="https://gu.qq.com/")
        text = _decode_response(response)
        match = re.search(r'v_hint="(.*)"', text, flags=re.S)
        if not match:
            return None
        for row in match.group(1).split("^"):
            parts = row.split("~")
            if len(parts) < 5:
                continue
            market, code, name, _, kind = parts[:5]
            symbol = normalize_symbol("%s.%s" % (code, market))
            if symbol:
                return entity_from_symbol(query, symbol, name=_json_unescape(name), query=query if kind != "ZS" else "指数")
        return None

    def _search_sina(self, query: str) -> Optional[Entity]:
        response = self._get(
            "https://suggest3.sinajs.cn/suggest/type=11,12,13,14,15",
            {"key": query, "name": "suggestdata"},
            referer="https://finance.sina.com.cn/",
        )
        text = _decode_response(response)
        match = re.search(r'"(.*)"', text, flags=re.S)
        if not match:
            return None
        for row in match.group(1).split(";"):
            parts = row.split(",")
            if len(parts) < 4:
                continue
            name, code, provider_symbol = parts[0].strip(), parts[2].strip(), parts[3].strip().lower()
            symbol = normalize_symbol(provider_symbol)
            if symbol:
                return entity_from_symbol(query, symbol, name=name, query=query)
            if code:
                symbol = normalize_symbol(code)
                if symbol:
                    return entity_from_symbol(query, symbol, name=name, query=query)
        return None

    def quote_realtime(self, entity: Entity) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        try:
            data = self._quote_tencent([entity.symbol])
            chain.append({"source": "tencent_finance", "ok": True})
            return {"data": data[0], "source_chain": chain, "warnings": []}
        except Exception as exc:
            chain.append({"source": "tencent_finance", "ok": False, "error": str(exc)})
        try:
            rows = self._akshare_call("stock_zh_a_spot_em")
            item = _find_row(rows, entity.code)
            if item:
                chain.append({"source": "akshare.stock_zh_a_spot_em", "ok": True})
                return {"data": _normalize_akshare_quote(item, entity), "source_chain": chain, "warnings": []}
            raise SourceError("akshare did not return target code")
        except Exception as exc:
            chain.append({"source": "akshare.stock_zh_a_spot_em", "ok": False, "error": str(exc)})
            raise SourceError("实时行情所有免费源失败")

    def _quote_tencent(self, symbols: Iterable[str]) -> List[Dict[str, Any]]:
        provider_symbols = [to_tencent_symbol(symbol) for symbol in symbols]
        response = self._get("https://qt.gtimg.cn/q=" + ",".join(provider_symbols), referer="https://gu.qq.com/")
        text = _decode_response(response)
        quotes: List[Dict[str, Any]] = []
        for match in re.finditer(r"v_([a-z]{2}\d{6})=\"([^\"]*)\";", text):
            provider_symbol = match.group(1)
            fields = match.group(2).split("~")
            if len(fields) < 34 or not fields[1]:
                continue
            quotes.append(_parse_tencent_quote(provider_symbol, fields))
        if not quotes:
            raise SourceError("腾讯行情返回为空")
        return quotes

    def quote_history(self, entity: Entity, *, days: int, period: str, adjust: str) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        try:
            data = self._history_tencent(entity.symbol, days=days, period=period, adjust=adjust)
            chain.append({"source": "tencent_fqkline", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": []}
        except Exception as exc:
            chain.append({"source": "tencent_fqkline", "ok": False, "error": str(exc)})
        try:
            data = self._history_efinance(entity, days=days)
            chain.append({"source": "efinance.get_quote_history", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": ["已从腾讯 K 线回退到 efinance"]}
        except Exception as exc:
            chain.append({"source": "efinance.get_quote_history", "ok": False, "error": str(exc)})
            if period == "minute":
                return {
                    "data": {"symbol": entity.symbol, "period": period, "adjust": adjust, "count": 0, "candles": []},
                    "source_chain": chain,
                    "warnings": ["分钟 K 线公开源暂时不可用，已返回空列表和失败详情"],
                }
            raise SourceError("历史行情所有免费源失败")

    def _history_tencent(self, symbol: str, *, days: int, period: str, adjust: str) -> Dict[str, Any]:
        provider_symbol = to_tencent_symbol(symbol)
        period_key = {"daily": "day", "weekly": "week", "monthly": "month", "minute": "mline"}.get(period, "day")
        adjust_key = {"qfq": "qfq", "hfq": "hfq", "none": ""}.get(adjust, "qfq")
        if period_key == "mline":
            param = "%s,m1,,,%d" % (provider_symbol, max(1, min(days, 240)))
        else:
            param = "%s,%s,,,%d,%s" % (provider_symbol, period_key, max(1, min(days, 5000)), adjust_key)
        payload = self._json_get(
            "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            {"param": param},
            referer="https://gu.qq.com/",
        )
        node = payload.get("data", {}).get(provider_symbol, {})
        rows = node.get("%s%s" % (adjust_key, period_key)) or node.get(period_key) or node.get("data") or []
        candles = [_parse_kline_row(row) for row in rows if isinstance(row, list) and len(row) >= 6]
        if not candles:
            raise SourceError("腾讯 K 线为空")
        qt = node.get("qt", {}).get(provider_symbol)
        quote = _parse_tencent_quote(provider_symbol, qt) if isinstance(qt, list) else None
        return {
            "symbol": symbol,
            "period": period,
            "adjust": adjust,
            "count": len(candles),
            "start_date": candles[0].get("date"),
            "end_date": candles[-1].get("date"),
            "latest_quote": quote,
            "candles": candles,
        }

    def _history_efinance(self, entity: Entity, *, days: int) -> Dict[str, Any]:
        import efinance as ef

        df = _quiet_call(ef.stock.get_quote_history, stock_codes=entity.code)
        rows = _df_to_records(df)[-days:]
        candles = [
            {
                "date": _pick(row, ["日期", "date"]),
                "open": _to_float(_pick(row, ["开盘", "open"])),
                "close": _to_float(_pick(row, ["收盘", "close"])),
                "high": _to_float(_pick(row, ["最高", "high"])),
                "low": _to_float(_pick(row, ["最低", "low"])),
                "volume": _to_float(_pick(row, ["成交量", "volume"])),
                "amount": _to_float(_pick(row, ["成交额", "amount"])),
            }
            for row in rows
        ]
        return {"symbol": entity.symbol, "period": "daily", "adjust": "provider_default", "count": len(candles), "candles": candles}

    def market_snapshot(self) -> Dict[str, Any]:
        symbols = ["000001.SH", "399001.SZ", "399006.SZ", "000300.SH", "000688.SH", "899050.BJ"]
        chain: List[Dict[str, Any]] = []
        data = {"indices": [], "breadth": None}
        warnings: List[str] = []
        try:
            data["indices"] = self._quote_tencent(symbols)
            chain.append({"source": "tencent_finance", "ok": True})
        except Exception as exc:
            chain.append({"source": "tencent_finance", "ok": False, "error": str(exc)})
            warnings.append("主要指数获取失败: %s" % exc)
        try:
            data["breadth"] = self._market_breadth_eastmoney()
            chain.append({"source": "eastmoney_market_breadth", "ok": True})
        except Exception as exc:
            chain.append({"source": "eastmoney_market_breadth", "ok": False, "error": str(exc)})
            warnings.append("市场宽度获取失败: %s" % exc)
        if not data["indices"] and not data["breadth"]:
            raise SourceError("大盘快照所有免费源失败")
        return {"data": data, "source_chain": chain, "warnings": warnings}

    def _market_breadth_eastmoney(self) -> Dict[str, Any]:
        payload = self._json_get(
            "https://push2.eastmoney.com/api/qt/ulist.np/get",
            {
                "fltt": 2,
                "fields": "f104,f105,f106,f3,f6",
                "secids": "1.000001,0.399001,0.399006",
            },
            referer="https://quote.eastmoney.com/",
        )
        rows = payload.get("data", {}).get("diff") or []
        up = sum(_to_int(row.get("f104")) or 0 for row in rows if isinstance(row, dict))
        down = sum(_to_int(row.get("f105")) or 0 for row in rows if isinstance(row, dict))
        flat = sum(_to_int(row.get("f106")) or 0 for row in rows if isinstance(row, dict))
        return {"up_count": up, "down_count": down, "flat_count": flat}

    def rank(self, kind: str, limit: int, order: str = "desc") -> Dict[str, Any]:
        if order == "auto":
            order = "asc" if kind == "losers" else "desc"
        chain: List[Dict[str, Any]] = []
        try:
            data = self._rank_eastmoney(kind, limit, order)
            chain.append({"source": "eastmoney_clist", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": []}
        except Exception as exc:
            chain.append({"source": "eastmoney_clist", "ok": False, "error": str(exc)})
        try:
            data = self._rank_sina(kind, limit, order)
            chain.append({"source": "sina_market_center", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": ["已从东方财富排行回退到新浪公开接口"]}
        except Exception as exc:
            chain.append({"source": "sina_market_center", "ok": False, "error": str(exc)})
            raise SourceError("榜单所有免费源失败")

    def _rank_eastmoney(self, kind: str, limit: int, order: str = "desc") -> Dict[str, Any]:
        config = {
            "gainers": "f3",
            "losers": "f3",
            "amount": "f6",
            "volume": "f5",
            "turnover": "f8",
            "volume-ratio": "f10",
            "amplitude": "f7",
            "market-cap": "f20",
            "pe": "f9",
            "pb": "f23",
        }.get(kind)
        if config is None:
            raise SourceError("unsupported rank kind: %s" % kind)
        fid = config
        po = 0 if order == "asc" else 1
        params = {
            "pn": 1,
            "pz": max(1, min(limit, 200)),
            "po": po,
            "np": 1,
            "ut": EASTMONEY_UT,
            "fltt": 2,
            "invt": 2,
            "fid": fid,
            "fs": A_STOCK_FS,
            "fields": "f12,f13,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f15,f16,f17,f18,f20,f21,f23",
        }
        payload = None
        last_error: Optional[Exception] = None
        for url in [
            "https://push2.eastmoney.com/api/qt/clist/get",
            "https://push2delay.eastmoney.com/api/qt/clist/get",
        ]:
            try:
                payload = self._json_get(url, params, referer="https://quote.eastmoney.com/")
                break
            except Exception as exc:
                last_error = exc
        if payload is None:
            raise SourceError("东方财富排行失败: %s" % last_error)
        rows = payload.get("data", {}).get("diff") or []
        items = [_parse_eastmoney_rank_row(row, index + 1) for index, row in enumerate(rows) if isinstance(row, dict)]
        if not items:
            raise SourceError("东方财富排行为空")
        return {"kind": kind, "order": order, "items": items, "returned_count": len(items), "total_count": payload.get("data", {}).get("total")}

    def _rank_sina(self, kind: str, limit: int, order: str = "desc") -> Dict[str, Any]:
        mapping = {
            "gainers": "changepercent",
            "losers": "changepercent",
            "amount": "amount",
            "volume": "volume",
            "turnover": "turnoverratio",
            "market-cap": "mktcap",
            "pe": "per",
            "pb": "pb",
        }
        if kind not in mapping:
            raise SourceError("sina does not support rank kind: %s" % kind)
        sort = mapping[kind]
        asc = 1 if order == "asc" else 0
        response = self._get(
            "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData",
            {"page": 1, "num": max(1, min(limit, 100)), "sort": sort, "asc": asc, "node": "hs_a", "symbol": "", "_s_r_a": "page"},
            referer="https://finance.sina.com.cn/",
        )
        rows = json.loads(_decode_response(response))
        items = [_parse_sina_rank_row(row, index + 1) for index, row in enumerate(rows) if isinstance(row, dict)]
        if not items:
            raise SourceError("新浪排行为空")
        return {"kind": kind, "order": order, "items": items, "returned_count": len(items)}

    def limit_pool(self, kind: str, query_date: Optional[str], limit: int) -> Dict[str, Any]:
        endpoint = {"up": "getTopicZTPool", "down": "getTopicDTPool", "broken": "getTopicZBPool", "strong": "getTopicQSPool"}.get(kind, "getTopicZTPool")
        sort = "fbt:asc" if kind in {"up", "down", "broken"} else "zdp:desc"
        date_text = (query_date or date.today().isoformat()).replace("-", "")
        payload = self._json_get(
            "https://push2ex.eastmoney.com/%s" % endpoint,
            {"ut": EASTMONEY_UT, "dpt": "wz.ztzt", "Pageindex": 0, "pagesize": max(1, min(limit, 500)), "sort": sort, "date": date_text},
            referer="https://quote.eastmoney.com/ztb/detail",
        )
        data = payload.get("data") or {}
        pool = data.get("pool") or []
        items = [_parse_pool_row(row, index + 1) for index, row in enumerate(pool) if isinstance(row, dict)]
        return {
            "data": {"kind": kind, "query_date": date_text, "trade_date": str(data.get("qdate") or ""), "total_count": data.get("tc"), "items": items},
            "source_chain": [{"source": "eastmoney_%s" % endpoint, "ok": True}],
            "warnings": [] if items else ["公开源返回空池，可能是非交易日或接口短暂不可用"],
        }

    def money_flow(self, scope: str, period: str, entity: Optional[Entity], limit: int) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        if scope == "market":
            try:
                data = self._money_flow_sina_market(limit)
                chain.append({"source": "sina_moneyflow", "ok": True})
                return {"data": data, "source_chain": chain, "warnings": []}
            except Exception as exc:
                chain.append({"source": "sina_moneyflow", "ok": False, "error": str(exc)})
        if scope == "stock":
            try:
                if entity is None:
                    raise SourceError("个股资金流需要 symbol")
                data = self._money_flow_eastmoney_stock(entity, period, limit)
                chain.append({"source": "eastmoney_stock_moneyflow", "ok": True})
                return {"data": data, "source_chain": chain, "warnings": []}
            except Exception as exc:
                chain.append({"source": "eastmoney_stock_moneyflow", "ok": False, "error": str(exc)})
        try:
            data = self._money_flow_akshare(scope, period, entity, limit)
            chain.append({"source": "akshare_moneyflow", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": ["资金流为公开源 best-effort 数据"]}
        except Exception as exc:
            chain.append({"source": "akshare_moneyflow", "ok": False, "error": str(exc)})
        try:
            if scope == "stock":
                data = self._money_flow_ths(scope, period, limit, entity)
            else:
                data = self._money_flow_ths(scope, period, limit)
            chain.append({"source": "akshare_ths_moneyflow", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": ["已从东方财富资金流回退到同花顺公开源"]}
        except Exception as exc:
            chain.append({"source": "akshare_ths_moneyflow", "ok": False, "error": str(exc)})
            if scope == "stock":
                return {
                    "data": {"scope": scope, "symbol": entity.symbol if entity else None, "period": period, "items": [], "returned_count": 0},
                    "source_chain": chain,
                    "warnings": ["个股资金流公开源暂时不可用，已返回空列表和失败详情"],
                }
            raise SourceError("资金流公开源失败")

    def _money_flow_sina_market(self, limit: int) -> Dict[str, Any]:
        response = self._get(
            "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_ssggzj",
            {"page": 1, "num": max(1, min(limit, 100)), "sort": "netamount", "asc": 0},
            referer="https://finance.sina.com.cn/",
        )
        rows = json.loads(_decode_response(response))
        return {"scope": "market", "period": "instant", "items": [_parse_sina_money_row(row, i + 1) for i, row in enumerate(rows) if isinstance(row, dict)]}

    def _money_flow_eastmoney_stock(self, entity: Entity, period: str, limit: int) -> Dict[str, Any]:
        secid = "%s.%s" % (1 if entity.market == "SH" else 0, entity.code)
        try:
            payload = self._json_get(
                "https://push2his.eastmoney.com/api/qt/stock/fflow/kline/get",
                {
                    "lmt": 0,
                    "klt": 101,
                    "secid": secid,
                    "fields1": "f1,f2,f3,f7",
                    "fields2": "f51,f52,f53,f54,f55,f56",
                    "ut": "b2884a393a59ad64002292a3e90d46a5",
                },
                referer="https://quote.eastmoney.com/",
            )
            source_data = payload.get("data") or {}
            rows = [_parse_eastmoney_stock_money_flow_line(line) for line in source_data.get("klines") or []]
            rows = [row for row in rows if row]
            if not rows:
                raise SourceError("东方财富个股资金流为空")
            lookback = {"instant": 1, "3d": 3, "5d": 5, "10d": 10, "20d": 20}.get(period, max(1, min(limit, 120)))
            selected = rows[-lookback:]
            summary = {
                "main_net_inflow": sum(_to_float(row.get("main_net_inflow")) or 0 for row in selected),
                "small_net_inflow": sum(_to_float(row.get("small_net_inflow")) or 0 for row in selected),
                "medium_net_inflow": sum(_to_float(row.get("medium_net_inflow")) or 0 for row in selected),
                "large_net_inflow": sum(_to_float(row.get("large_net_inflow")) or 0 for row in selected),
                "super_large_net_inflow": sum(_to_float(row.get("super_large_net_inflow")) or 0 for row in selected),
            }
            return {
                "scope": "stock",
                "symbol": entity.symbol,
                "name": source_data.get("name") or entity.name,
                "period": period,
                "items": selected,
                "returned_count": len(selected),
                "summary": summary,
            }
        except Exception as exc:
            if period == "20d":
                raise
            return self._money_flow_eastmoney_stock_rank(entity, period, limit, str(exc))

    def _money_flow_eastmoney_stock_rank(self, entity: Entity, period: str, limit: int, fallback_reason: str) -> Dict[str, Any]:
        config = {
            "instant": ("f62", "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124", "今日"),
            "3d": ("f267", "f12,f14,f2,f127,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f257,f258,f124", "3日"),
            "5d": ("f164", "f12,f14,f2,f109,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f257,f258,f124", "5日"),
            "10d": ("f174", "f12,f14,f2,f160,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f260,f261,f124", "10日"),
        }.get(period)
        if config is None:
            raise SourceError("东方财富排行式个股资金流不支持周期 %s: %s" % (period, fallback_reason))
        fid, fields, label = config
        base_params = {
            "fid": fid,
            "po": "1",
            "pz": "100",
            "pn": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "fs": "m:0+t:6+f:!2,m:0+t:13+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:7+f:!2,m:1+t:3+f:!2",
            "fields": fields,
        }
        total = 6000
        matched: List[Dict[str, Any]] = []
        for page in range(1, 61):
            params = dict(base_params)
            params["pn"] = str(page)
            payload = self._json_get("https://push2delay.eastmoney.com/api/qt/clist/get", params, referer="https://data.eastmoney.com/")
            data = payload.get("data") or {}
            rows = data.get("diff") or []
            total = _to_int(data.get("total")) or total
            for row in rows:
                if isinstance(row, dict) and str(row.get("f12")) == entity.code:
                    matched.append(_parse_eastmoney_stock_money_flow_rank_row(row, period, label))
            if matched or page * 100 >= total or not rows:
                break
        if not matched:
            raise SourceError("东方财富排行式个股资金流未匹配到 %s: %s" % (entity.code, fallback_reason))
        return {
            "scope": "stock",
            "symbol": entity.symbol,
            "name": matched[0].get("name") or entity.name,
            "period": period,
            "items": matched[:limit],
            "returned_count": len(matched[:limit]),
            "source_note": "东方财富资金流排行公开接口；历史明细接口失败后按排行页匹配个股",
        }

    def _money_flow_akshare(self, scope: str, period: str, entity: Optional[Entity], limit: int) -> Dict[str, Any]:
        import akshare as ak

        if scope == "stock":
            if entity is None:
                raise SourceError("个股资金流需要 symbol")
            df = _quiet_call(ak.stock_individual_fund_flow, stock=entity.code, market=entity.market.lower())
            return {"scope": scope, "symbol": entity.symbol, "period": period, "items": _df_to_records(df)[-limit:]}
        indicator = {"instant": "今日", "3d": "3日", "5d": "5日", "10d": "10日", "20d": "20日"}.get(period, "今日")
        sector_type = "行业资金流" if scope == "industry" else "概念资金流"
        df = _quiet_call(ak.stock_sector_fund_flow_rank, indicator=indicator, sector_type=sector_type)
        return {"scope": scope, "period": period, "items": _df_to_records(df)[:limit]}

    def _money_flow_ths(self, scope: str, period: str, limit: int, entity: Optional[Entity] = None) -> Dict[str, Any]:
        import akshare as ak

        symbol = {"instant": "即时", "3d": "3日排行", "5d": "5日排行", "10d": "10日排行", "20d": "20日排行"}.get(period, "即时")
        if scope == "stock":
            if entity is None:
                raise SourceError("个股资金流需要 symbol")
            try:
                matched = self._money_flow_ths_stock_by_code(period, entity, limit)
            except Exception:
                rows = _df_to_records(_quiet_call(ak.stock_fund_flow_individual, symbol=symbol))
                matched = [row for row in rows if _row_matches_code(row, entity.code)]
            if not matched:
                raise SourceError("同花顺个股资金流未匹配到 %s" % entity.code)
            return {
                "scope": scope,
                "symbol": entity.symbol,
                "period": period,
                "items": matched[:limit],
                "returned_count": len(matched[:limit]),
                "source_note": "同花顺资金流公开页",
            }
        if scope not in {"industry", "concept"}:
            raise SourceError("同花顺资金流兜底仅支持个股/行业/概念")
        func = ak.stock_fund_flow_industry if scope == "industry" else ak.stock_fund_flow_concept
        rows = _df_to_records(_quiet_call(func, symbol=symbol))
        return {"scope": scope, "period": period, "items": rows[:limit], "source_note": "同花顺资金流公开页"}

    def _money_flow_ths_stock_by_code(self, period: str, entity: Entity, limit: int) -> List[Dict[str, Any]]:
        import pandas as pd
        import py_mini_racer
        from akshare.stock_feature.stock_fund_flow import _get_file_content_ths

        board = {"3d": "3", "5d": "5", "10d": "10", "20d": "20"}.get(period)
        path = "board/%s/field/code/order/asc/page/{}/ajax/1/free/1/" % board if board else "field/code/order/asc/page/{}/ajax/1/free/1/"
        url_template = "http://data.10jqka.com.cn/funds/ggzjl/%s" % path
        js_code = py_mini_racer.MiniRacer()
        js_code.eval(_get_file_content_ths("ths.js"))
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "hexin-v": js_code.call("v"),
            "Host": "data.10jqka.com.cn",
            "Referer": "http://data.10jqka.com.cn/funds/hyzjl/",
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
        }

        cache: Dict[int, Tuple[List[Dict[str, Any]], str]] = {}

        def fetch_page(page: int) -> Tuple[List[Dict[str, Any]], str]:
            if page in cache:
                return cache[page]
            response = self.session.get(url_template.format(page), headers=headers, timeout=self.timeout)
            response.raise_for_status()
            text = _decode_response(response)
            tables = pd.read_html(io.StringIO(text))
            rows = _df_to_records(tables[0]) if tables else []
            cache[page] = (rows, text)
            return cache[page]

        rows, text = fetch_page(1)
        total_pages = _extract_ths_total_pages(text) or 120
        target = int(entity.code)
        low, high = 1, total_pages
        while low <= high:
            page = (low + high) // 2
            rows, _ = fetch_page(page)
            codes = sorted(_row_code_as_int(row) for row in rows if _row_code_as_int(row) is not None)
            if not codes:
                break
            matched = [row for row in rows if _row_matches_code(row, entity.code)]
            if matched:
                return matched[:limit]
            if target < codes[0]:
                high = page - 1
            elif target > codes[-1]:
                low = page + 1
            else:
                break
        return []

    def sector(self, kind: str, action: str, entity: Optional[Entity], query: str, limit: int) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        try:
            data = self._sector_akshare(kind, action, entity, query, limit)
            chain.append({"source": "akshare_sector", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": []}
        except Exception as exc:
            chain.append({"source": "akshare_sector", "ok": False, "error": str(exc)})
        try:
            data = self._sector_ths(kind, action, entity, query, limit)
            chain.append({"source": "akshare_ths_or_sina_sector", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": ["已从东方财富板块源回退到同花顺/新浪公开源"]}
        except Exception as exc:
            chain.append({"source": "akshare_ths_or_sina_sector", "ok": False, "error": str(exc)})
            if action == "constituents":
                return {
                    "data": {"kind": kind, "action": action, "board": _extract_board_name(query), "items": [], "returned_count": 0},
                    "source_chain": chain,
                    "warnings": ["板块成分股公开源暂时不可用或未匹配到板块，已返回空列表和失败详情"],
                }
            raise SourceError("板块公开源失败: %s" % exc)

    def _sector_akshare(self, kind: str, action: str, entity: Optional[Entity], query: str, limit: int) -> Dict[str, Any]:
        import akshare as ak

        if action == "rank":
            func = ak.stock_board_concept_name_em if kind == "concept" else ak.stock_board_industry_name_em
            return {"kind": kind, "action": action, "items": _df_to_records(_quiet_call(func))[:limit]}
        if action == "constituents":
            name = _extract_board_name(query)
            if not name:
                raise SourceError("缺少板块名称")
            func = ak.stock_board_concept_cons_em if kind == "concept" else ak.stock_board_industry_cons_em
            return {"kind": kind, "action": action, "board": name, "items": _df_to_records(_quiet_call(func, symbol=name))[:limit]}
        if action == "belong":
            if entity is None:
                raise SourceError("所属板块需要股票代码")
            import efinance as ef

            df = _quiet_call(ef.stock.get_belong_board, entity.code)
            return {"kind": kind, "action": action, "symbol": entity.symbol, "items": _df_to_records(df)[:limit]}
        raise SourceError("unknown sector action")

    def _sector_ths(self, kind: str, action: str, entity: Optional[Entity], query: str, limit: int) -> Dict[str, Any]:
        import akshare as ak
        import pandas as pd

        if action == "rank":
            if kind == "industry":
                df = _quiet_call(ak.stock_sector_spot, indicator="新浪行业")
                rows = _df_to_records(df)
                rows = sorted(rows, key=lambda row: _to_float(row.get("涨跌幅")) or -999999, reverse=True)
                return {"kind": kind, "action": action, "items": rows[:limit]}
            df = _quiet_call(ak.stock_board_concept_name_ths)
            rows = _df_to_records(df)
            return {"kind": kind, "action": action, "items": rows[:limit], "note": "同花顺概念板块兜底仅返回名称和代码"}
        if action == "constituents":
            name = _extract_board_name(query)
            if not name:
                raise SourceError("缺少板块名称")
            listing_func = ak.stock_board_concept_name_ths if kind == "concept" else ak.stock_board_industry_name_ths
            listing = _df_to_records(_quiet_call(listing_func))
            matched = _match_board_row(listing, name)
            if not matched:
                raise SourceError("同花顺未找到板块：%s" % name)
            code = str(matched.get("code") or matched.get("代码") or "").strip()
            path = "gn" if kind == "concept" else "thshy"
            response = self._get(
                "https://q.10jqka.com.cn/%s/detail/code/%s/" % (path, code),
                referer="https://q.10jqka.com.cn/",
            )
            tables = _quiet_call(pd.read_html, io.StringIO(_decode_response(response)))
            if not tables:
                raise SourceError("同花顺板块成分股表格为空")
            selected = tables[0]
            for table in tables:
                columns = {str(column) for column in getattr(table, "columns", [])}
                lowered_columns = {column.lower() for column in columns}
                if {"代码", "名称"}.issubset(columns) or {"code", "name"}.issubset(lowered_columns):
                    selected = table
                    break
            return {"kind": kind, "action": action, "board": matched.get("name") or matched.get("名称") or name, "items": _df_to_records(selected)[:limit]}
        if action == "belong":
            raise SourceError("同花顺兜底不支持个股所属板块")
        raise SourceError("unknown sector action")

    def fundamental(self, entity: Entity, pack: str) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        data: Dict[str, Any] = {"symbol": entity.symbol, "pack": pack}
        warnings: List[str] = []
        try:
            data["quote_valuation"] = self.quote_realtime(entity)["data"]
            chain.append({"source": "tencent_quote_valuation", "ok": True})
        except Exception as exc:
            chain.append({"source": "tencent_quote_valuation", "ok": False, "error": str(exc)})
            warnings.append("估值快照失败: %s" % exc)
        try:
            data.update(self._fundamental_akshare(entity, pack))
            chain.append({"source": "akshare_fundamental", "ok": True})
        except Exception as exc:
            chain.append({"source": "akshare_fundamental", "ok": False, "error": str(exc)})
            warnings.append("akshare 基本面 best-effort 失败: %s" % exc)
        if len(data) <= 2:
            raise SourceError("基本面公开源失败")
        return {"data": data, "source_chain": chain, "warnings": warnings}

    def _fundamental_akshare(self, entity: Entity, pack: str) -> Dict[str, Any]:
        import akshare as ak

        result: Dict[str, Any] = {}
        if pack in {"basic", "all"}:
            result["basic"] = _df_to_records(_quiet_call(ak.stock_individual_info_em, symbol=entity.code))
        if pack in {"financials", "all"}:
            result["financial_abstract"] = _df_to_records(_quiet_call(ak.stock_financial_abstract, symbol=entity.code))
            result["financial_indicator"] = _df_to_records(_quiet_call(ak.stock_financial_analysis_indicator, symbol=entity.code))
        if pack in {"holders", "all"}:
            holder_count_history = _optional_ak_call(ak, "stock_zh_a_gdhs_detail_em", symbol=entity.code)
            main_holders = _optional_ak_call(ak, "stock_main_stock_holder", stock=entity.code)
            result["holder_count_history"] = _tail_records(holder_count_history, 40)
            result["main_holders"] = _latest_records(main_holders, ["截至日期", "报告期"], 20)
            result["holders_scope"] = {
                "holder_count_history": "latest_40_records",
                "main_holders": "latest_report_period_top_20",
            }
        if pack in {"dividend", "all"}:
            result["dividend"] = _optional_ak_call(ak, "stock_dividend_cninfo", symbol=entity.code)
        return result

    def announcement(self, entity: Optional[Entity], keyword: Optional[str], limit: int) -> Dict[str, Any]:
        chain: List[Dict[str, Any]] = []
        try:
            data = self._announcement_cninfo(entity, keyword, limit)
            chain.append({"source": "cninfo_public", "ok": True})
            return {"data": data, "source_chain": chain, "warnings": []}
        except Exception as exc:
            chain.append({"source": "cninfo_public", "ok": False, "error": str(exc)})
            raise SourceError("公告公开源失败")

    def _announcement_cninfo(self, entity: Optional[Entity], keyword: Optional[str], limit: int) -> Dict[str, Any]:
        data = {
            "pageNum": 1,
            "pageSize": max(1, min(limit, 50)),
            "column": "szse",
            "tabName": "fulltext",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        if entity is not None:
            search_name = _canonical_entity_search_name(entity)
            search_parts = [search_name or entity.code]
            if keyword:
                search_parts.append(_announcement_search_keyword(keyword))
            data["searchkey"] = " ".join(search_parts)
        elif keyword:
            data["searchkey"] = _announcement_search_keyword(keyword)
        payload = self._post("https://www.cninfo.com.cn/new/hisAnnouncement/query", data=data, referer="https://www.cninfo.com.cn/").json()
        rows = payload.get("announcements") or []
        items = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            adjunct_url = row.get("adjunctUrl")
            items.append(
                {
                    "title": _strip_html(row.get("announcementTitle")),
                    "code": row.get("secCode"),
                    "name": row.get("secName"),
                    "announcement_time": row.get("announcementTime"),
                    "announcement_id": row.get("announcementId"),
                    "pdf_url": "https://static.cninfo.com.cn/%s" % adjunct_url if adjunct_url else None,
                }
            )
        return {"symbol": entity.symbol if entity else None, "keyword": keyword, "items": items, "returned_count": len(items)}

    def dragon_tiger(self, query_date: Optional[str], entity: Optional[Entity], limit: int) -> Dict[str, Any]:
        import akshare as ak

        date_text = (query_date or date.today().isoformat()).replace("-", "")
        try:
            df = _quiet_call(ak.stock_lhb_detail_em, start_date=date_text, end_date=date_text)
            rows = _df_to_records(df)
            chain = [{"source": "akshare.stock_lhb_detail_em", "ok": True}]
            warnings_list = ["龙虎榜为公开源 best-effort 数据"]
        except Exception as exc:
            rows = []
            chain = [{"source": "akshare.stock_lhb_detail_em", "ok": False, "error": str(exc)}]
            warnings_list = ["龙虎榜公开源暂时不可用，已返回空列表和失败详情"]
        if entity is not None:
            rows = [row for row in rows if entity.code in json.dumps(row, ensure_ascii=False, default=str)]
        return {"data": {"date": date_text, "symbol": entity.symbol if entity else None, "items": rows[:limit], "returned_count": min(len(rows), limit)}, "source_chain": chain, "warnings": warnings_list}

    def news(self, entity: Optional[Entity], keyword: Optional[str], kind: str, limit: int) -> Dict[str, Any]:
        import akshare as ak

        source = "akshare.stock_research_report_em" if kind == "research" else "akshare.stock_news_em" if entity is not None else "akshare.stock_news_main_cx"
        try:
            if kind == "research":
                if entity is None:
                    raise SourceError("研报/评级需要股票代码或名称")
                df = _quiet_call(ak.stock_research_report_em, symbol=entity.code)
            elif entity is not None:
                df = _quiet_call(ak.stock_news_em, symbol=entity.code)
            else:
                df = _quiet_call(ak.stock_news_main_cx)
            rows = _df_to_records(df)
            chain = [{"source": source, "ok": True}]
            warnings_list = ["新闻/研报为公开源 best-effort 数据"]
        except Exception as exc:
            rows = []
            chain = [{"source": source, "ok": False, "error": str(exc)}]
            warnings_list = ["新闻/研报公开源暂时不可用，已返回空列表和失败详情"]
        non_filter_keywords = {"新闻", "快讯", "消息", "资讯", "利好", "利空", "有雷", "爆雷", "研报", "评级", "目标价", "机构评级", "机构怎么看", "机构看法"}
        if keyword and keyword not in non_filter_keywords:
            rows = [row for row in rows if keyword in json.dumps(row, ensure_ascii=False, default=str)]
        return {
            "data": {"kind": kind, "symbol": entity.symbol if entity else None, "keyword": keyword, "items": rows[:limit], "returned_count": min(len(rows), limit)},
            "source_chain": chain,
            "warnings": warnings_list,
        }

    def chip(self, entity: Entity, limit: int) -> Dict[str, Any]:
        import akshare as ak

        try:
            df = _quiet_call(ak.stock_cyq_em, symbol=entity.code)
            rows = _df_to_records(df)
            chain = [{"source": "akshare.stock_cyq_em", "ok": True}]
            warnings_list = ["筹码分布为公开源 best-effort 数据，字段和复权口径可能随公开源变化"]
        except Exception as exc:
            rows = []
            chain = [{"source": "akshare.stock_cyq_em", "ok": False, "error": str(exc)}]
            warnings_list = ["筹码分布公开源暂时不可用，已返回空列表和失败详情"]
        return {
            "data": {"symbol": entity.symbol, "items": rows[-limit:], "returned_count": min(len(rows), limit)},
            "source_chain": chain,
            "warnings": warnings_list,
        }

    def block_trade(self, query_date: Optional[str], entity: Optional[Entity], limit: int) -> Dict[str, Any]:
        import akshare as ak

        date_text = (query_date or date.today().isoformat()).replace("-", "")
        try:
            df = _quiet_call(ak.stock_dzjy_mrmx, symbol="A股", start_date=date_text, end_date=date_text)
            rows = _df_to_records(df)
            chain = [{"source": "akshare.stock_dzjy_mrmx", "ok": True}]
            warnings_list = ["大宗交易为公开源 best-effort 数据，非交易日可能返回空列表"]
        except Exception as exc:
            rows = []
            chain = [{"source": "akshare.stock_dzjy_mrmx", "ok": False, "error": str(exc)}]
            warnings_list = ["大宗交易公开源暂时不可用，已返回空列表和失败详情"]
        if entity is not None:
            rows = [row for row in rows if entity.code in json.dumps(row, ensure_ascii=False, default=str)]
        return {
            "data": {"date": date_text, "symbol": entity.symbol if entity else None, "items": rows[:limit], "returned_count": min(len(rows), limit)},
            "source_chain": chain,
            "warnings": warnings_list,
        }

    def margin_trading(self, query_date: Optional[str], entity: Optional[Entity], limit: int) -> Dict[str, Any]:
        import akshare as ak

        date_text = (query_date or date.today().isoformat()).replace("-", "")
        chain: List[Dict[str, Any]] = []
        rows: List[Dict[str, Any]] = []
        for source, func, kwargs in [
            ("akshare.stock_margin_detail_sse", ak.stock_margin_detail_sse, {"date": date_text}),
            ("akshare.stock_margin_detail_szse", ak.stock_margin_detail_szse, {"date": date_text}),
        ]:
            try:
                part = _df_to_records(_quiet_call(func, **kwargs))
                rows.extend(part)
                chain.append({"source": source, "ok": True})
            except Exception as exc:
                chain.append({"source": source, "ok": False, "error": str(exc)})
        if entity is not None:
            rows = [row for row in rows if entity.code in json.dumps(row, ensure_ascii=False, default=str)]
        if not rows and not any(item.get("ok") for item in chain):
            raise SourceError("融资融券公开源失败")
        return {
            "data": {"date": date_text, "symbol": entity.symbol if entity else None, "items": rows[:limit], "returned_count": min(len(rows), limit)},
            "source_chain": chain,
            "warnings": ["融资融券为交易所公开源 best-effort 数据，深沪字段可能不完全一致"],
        }

    def bond(self, action: str, entity: Optional[Entity], limit: int, days: int) -> Dict[str, Any]:
        import akshare as ak

        if action in {"rank", "quote"}:
            df = _quiet_call(ak.bond_zh_hs_cov_spot)
            rows = _df_to_records(df)
            if entity is not None:
                rows = [row for row in rows if entity.code in json.dumps(row, ensure_ascii=False, default=str)]
            return {"data": {"action": action, "items": rows[:limit]}, "source_chain": [{"source": "akshare.bond_zh_hs_cov_spot", "ok": True}], "warnings": []}
        if action == "history":
            if entity is None:
                raise SourceError("可转债历史需要 symbol")
            chain: List[Dict[str, Any]] = []
            warnings_list: List[str] = []
            try:
                data = self._history_tencent(entity.symbol, days=days, period="daily", adjust="qfq")
                data["action"] = action
                data["asset_type"] = "bond"
                chain.append({"source": "tencent_fqkline", "ok": True})
                return {"data": data, "source_chain": chain, "warnings": warnings_list}
            except Exception as exc:
                chain.append({"source": "tencent_fqkline", "ok": False, "error": str(exc)})
            try:
                df = _quiet_call(ak.bond_zh_hs_cov_daily, symbol=entity.code)
                rows = _df_to_records(df)[-days:]
                chain.append({"source": "akshare.bond_zh_hs_cov_daily", "ok": True})
            except Exception as exc:
                rows = []
                chain.append({"source": "akshare.bond_zh_hs_cov_daily", "ok": False, "error": str(exc)})
                warnings_list = ["可转债历史公开源暂时不可用，已返回空列表和失败详情"]
            return {"data": {"action": action, "symbol": entity.symbol, "items": rows, "returned_count": len(rows)}, "source_chain": chain, "warnings": warnings_list}
        raise SourceError("unsupported bond action")

    def _akshare_call(self, name: str, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        import akshare as ak

        func = getattr(ak, name)
        return _df_to_records(_quiet_call(func, *args, **kwargs))


def to_tencent_symbol(symbol: str) -> str:
    normalized = normalize_symbol(symbol)
    if not normalized:
        return symbol.lower()
    code, market = normalized.split(".", 1)
    return market.lower() + code


def _decode_response(response: requests.Response) -> str:
    content = response.content
    for encoding in ("utf-8", "gb18030", "gbk"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return response.text


def _json_unescape(text: str) -> str:
    if "\\u" not in text:
        return text
    try:
        return json.loads('"%s"' % text)
    except Exception:
        return text


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text in {"", "-", "--", "None", "false"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> Optional[int]:
    number = _to_float(value)
    if number is None:
        return None
    return int(number)


def _parse_tencent_quote(provider_symbol: str, fields: List[Any]) -> Dict[str, Any]:
    def field(index: int) -> str:
        return str(fields[index]).strip() if index < len(fields) else ""

    code = field(2)
    symbol = normalize_symbol("%s.%s" % (code, provider_symbol[:2])) or provider_symbol
    return {
        "symbol": symbol,
        "provider_symbol": provider_symbol,
        "code": code,
        "name": field(1),
        "latest": _to_float(field(3)),
        "previous_close": _to_float(field(4)),
        "open": _to_float(field(5)),
        "volume": _to_float(field(6)),
        "market_time": field(30),
        "change": _to_float(field(31)),
        "change_ratio": _to_float(field(32)),
        "high": _to_float(field(33)),
        "low": _to_float(field(34)),
        "amount": _to_float(field(37)),
        "turnover_ratio": _to_float(field(38)),
        "pe": _to_float(field(39)),
        "amplitude": _to_float(field(43)),
        "total_market_cap": _to_float(field(44)),
        "float_market_cap": _to_float(field(45)),
        "pb": _to_float(field(46)),
        "volume_ratio": _to_float(field(49)),
    }


def _parse_kline_row(row: List[Any]) -> Dict[str, Any]:
    return {
        "date": row[0],
        "open": _to_float(row[1]),
        "close": _to_float(row[2]),
        "high": _to_float(row[3]),
        "low": _to_float(row[4]),
        "volume": _to_float(row[5]),
        "amount": _to_float(row[6]) if len(row) > 6 else None,
    }


def _parse_eastmoney_rank_row(row: Dict[str, Any], rank: int) -> Dict[str, Any]:
    code = str(row.get("f12", "")).strip()
    symbol = normalize_symbol(code) or code
    return {
        "rank": rank,
        "symbol": symbol,
        "code": code,
        "name": row.get("f14"),
        "latest": _to_float(row.get("f2")),
        "change_ratio": _to_float(row.get("f3")),
        "change": _to_float(row.get("f4")),
        "volume": _to_float(row.get("f5")),
        "amount": _to_float(row.get("f6")),
        "amplitude": _to_float(row.get("f7")),
        "turnover_ratio": _to_float(row.get("f8")),
        "pe": _to_float(row.get("f9")),
        "volume_ratio": _to_float(row.get("f10")),
        "high": _to_float(row.get("f15")),
        "low": _to_float(row.get("f16")),
        "open": _to_float(row.get("f17")),
        "previous_close": _to_float(row.get("f18")),
        "total_market_cap": _to_float(row.get("f20")),
        "float_market_cap": _to_float(row.get("f21")),
        "pb": _to_float(row.get("f23")),
    }


def _parse_sina_rank_row(row: Dict[str, Any], rank: int) -> Dict[str, Any]:
    return {
        "rank": rank,
        "symbol": row.get("symbol"),
        "code": row.get("code"),
        "name": row.get("name"),
        "latest": _to_float(row.get("trade")),
        "change": _to_float(row.get("pricechange")),
        "change_ratio": _to_float(row.get("changepercent")),
        "volume": _to_float(row.get("volume")),
        "amount": _to_float(row.get("amount")),
        "turnover_ratio": _to_float(row.get("turnoverratio")),
        "pe": _to_float(row.get("per")),
        "pb": _to_float(row.get("pb")),
        "tick_time": row.get("ticktime"),
    }


def _parse_sina_money_row(row: Dict[str, Any], rank: int) -> Dict[str, Any]:
    symbol = row.get("symbol")
    return {
        "rank": rank,
        "symbol": symbol,
        "code": str(symbol)[-6:] if symbol else None,
        "name": row.get("name") or "",
        "latest": _to_float(row.get("trade")),
        "change_ratio": _to_float(row.get("changeratio")),
        "amount": _to_float(row.get("amount")),
        "net_amount": _to_float(row.get("netamount")),
        "main_net_amount": _to_float(row.get("r0_net")),
        "turnover": _to_float(row.get("turnover")),
    }


def _parse_eastmoney_stock_money_flow_line(line: Any) -> Dict[str, Any]:
    parts = str(line).split(",")
    if len(parts) < 6:
        return {}
    return {
        "date": parts[0],
        "main_net_inflow": _to_float(parts[1]),
        "small_net_inflow": _to_float(parts[2]),
        "medium_net_inflow": _to_float(parts[3]),
        "large_net_inflow": _to_float(parts[4]),
        "super_large_net_inflow": _to_float(parts[5]),
    }


def _parse_eastmoney_stock_money_flow_rank_row(row: Dict[str, Any], period: str, label: str) -> Dict[str, Any]:
    if period == "instant":
        return {
            "code": str(row.get("f12") or ""),
            "name": row.get("f14"),
            "latest": _to_float(row.get("f2")),
            "change_ratio": _to_float(row.get("f3")),
            "period": label,
            "main_net_inflow": _to_float(row.get("f62")),
            "main_net_inflow_ratio": _to_float(row.get("f184")),
            "super_large_net_inflow": _to_float(row.get("f66")),
            "super_large_net_inflow_ratio": _to_float(row.get("f69")),
            "large_net_inflow": _to_float(row.get("f72")),
            "large_net_inflow_ratio": _to_float(row.get("f75")),
            "medium_net_inflow": _to_float(row.get("f78")),
            "medium_net_inflow_ratio": _to_float(row.get("f81")),
            "small_net_inflow": _to_float(row.get("f84")),
            "small_net_inflow_ratio": _to_float(row.get("f87")),
        }
    field_map = {
        "3d": ("f127", "f267", "f268", "f269", "f270", "f271", "f272", "f273", "f274", "f275", "f276"),
        "5d": ("f109", "f164", "f165", "f166", "f167", "f168", "f169", "f170", "f171", "f172", "f173"),
        "10d": ("f160", "f174", "f175", "f176", "f177", "f178", "f179", "f180", "f181", "f182", "f183"),
    }
    change_key, main_key, main_ratio_key, super_key, super_ratio_key, large_key, large_ratio_key, medium_key, medium_ratio_key, small_key, small_ratio_key = field_map[period]
    return {
        "code": str(row.get("f12") or ""),
        "name": row.get("f14"),
        "latest": _to_float(row.get("f2")),
        "change_ratio": _to_float(row.get(change_key)),
        "period": label,
        "main_net_inflow": _to_float(row.get(main_key)),
        "main_net_inflow_ratio": _to_float(row.get(main_ratio_key)),
        "super_large_net_inflow": _to_float(row.get(super_key)),
        "super_large_net_inflow_ratio": _to_float(row.get(super_ratio_key)),
        "large_net_inflow": _to_float(row.get(large_key)),
        "large_net_inflow_ratio": _to_float(row.get(large_ratio_key)),
        "medium_net_inflow": _to_float(row.get(medium_key)),
        "medium_net_inflow_ratio": _to_float(row.get(medium_ratio_key)),
        "small_net_inflow": _to_float(row.get(small_key)),
        "small_net_inflow_ratio": _to_float(row.get(small_ratio_key)),
    }


def _parse_pool_row(row: Dict[str, Any], rank: int) -> Dict[str, Any]:
    code = str(row.get("c", "")).strip()
    symbol = normalize_symbol(code) or code
    price_raw = _to_float(row.get("p"))
    stat = row.get("zttj") if isinstance(row.get("zttj"), dict) else {}
    return {
        "rank": rank,
        "symbol": symbol,
        "code": code,
        "name": row.get("n"),
        "latest": round(price_raw / 1000, 3) if price_raw is not None else None,
        "change_ratio": _to_float(row.get("zdp")),
        "amount": _to_float(row.get("amount")),
        "turnover_ratio": _to_float(row.get("hs")),
        "board_count": _to_int(row.get("lbc")),
        "first_limit_time": _format_hhmmss(row.get("fbt")),
        "last_limit_time": _format_hhmmss(row.get("lbt")),
        "sealed_fund": _to_float(row.get("fund")),
        "break_count": _to_int(row.get("zbc")),
        "sector": row.get("hybk"),
        "limit_stat_days": stat.get("days"),
        "limit_stat_count": stat.get("ct"),
    }


def _format_hhmmss(value: Any) -> Optional[str]:
    number = _to_int(value)
    if number is None:
        return None
    text = "%06d" % number
    return "%s:%s:%s" % (text[0:2], text[2:4], text[4:6])


def _df_to_records(df: Any) -> List[Dict[str, Any]]:
    if df is None:
        return []
    if isinstance(df, list):
        return df
    if hasattr(df, "to_dict"):
        return df.to_dict(orient="records")
    return []


def _find_row(rows: List[Dict[str, Any]], code: str) -> Optional[Dict[str, Any]]:
    for row in rows:
        if str(row.get("代码") or row.get("code") or row.get("股票代码") or "") == code:
            return row
    return None


def _row_matches_code(row: Dict[str, Any], code: str) -> bool:
    for key in ["代码", "code", "股票代码", "证券代码"]:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text.endswith(".0"):
            text = text[:-2]
        if text.zfill(6) == code:
            return True
    return False


def _row_code_as_int(row: Dict[str, Any]) -> Optional[int]:
    for key in ["代码", "code", "股票代码", "证券代码"]:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text.endswith(".0"):
            text = text[:-2]
        if text.isdigit():
            return int(text)
    return None


def _extract_ths_total_pages(text: str) -> Optional[int]:
    match = re.search(r'class=["\']page_info["\'][^>]*>\s*\d+\s*/\s*(\d+)', text)
    if match:
        return _to_int(match.group(1))
    match = re.search(r">\s*\d+\s*/\s*(\d+)\s*<", text)
    if match:
        return _to_int(match.group(1))
    return None


def _normalize_akshare_quote(row: Dict[str, Any], entity: Entity) -> Dict[str, Any]:
    return {
        "symbol": entity.symbol,
        "code": entity.code,
        "name": _pick(row, ["名称", "股票名称", "name"]),
        "latest": _to_float(_pick(row, ["最新价", "最新", "price"])),
        "change_ratio": _to_float(_pick(row, ["涨跌幅", "change_ratio"])),
        "change": _to_float(_pick(row, ["涨跌额", "change"])),
        "volume": _to_float(_pick(row, ["成交量", "volume"])),
        "amount": _to_float(_pick(row, ["成交额", "amount"])),
        "turnover_ratio": _to_float(_pick(row, ["换手率", "turnover"])),
        "volume_ratio": _to_float(_pick(row, ["量比", "volume_ratio"])),
        "pe": _to_float(_pick(row, ["市盈率-动态", "市盈率", "pe"])),
        "pb": _to_float(_pick(row, ["市净率", "pb"])),
    }


def _pick(row: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _optional_ak_call(module: Any, name: str, **kwargs: Any) -> List[Dict[str, Any]]:
    func = getattr(module, name, None)
    if func is None:
        return []
    try:
        return _df_to_records(_quiet_call(func, **kwargs))
    except TypeError:
        return _df_to_records(_quiet_call(func))


def _tail_records(records: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    return records[-limit:]


def _latest_records(records: List[Dict[str, Any]], date_keys: Iterable[str], limit: int) -> List[Dict[str, Any]]:
    if not records or limit <= 0:
        return []
    latest_value: Optional[str] = None
    for row in records:
        for key in date_keys:
            value = row.get(key)
            if value is None:
                continue
            text = str(value)
            if latest_value is None or text > latest_value:
                latest_value = text
            break
    if latest_value is None:
        return records[:limit]
    latest_rows = [
        row
        for row in records
        if any(row.get(key) is not None and str(row.get(key)) == latest_value for key in date_keys)
    ]
    return latest_rows[:limit]


def _strip_html(value: Any) -> str:
    text = str(value or "")
    return re.sub(r"<[^>]+>", "", text).strip()


def _canonical_entity_search_name(entity: Entity) -> Optional[str]:
    canonical_by_code = {
        "600519": "贵州茅台",
        "300750": "宁德时代",
        "300059": "东方财富",
        "600036": "招商银行",
        "002594": "比亚迪",
        "688981": "中芯国际",
        "603288": "海天味业",
        "600031": "三一重工",
        "002714": "牧原股份",
        "603501": "韦尔股份",
        "600150": "中国船舶",
        "601127": "赛力斯",
        "601138": "工业富联",
        "300274": "阳光电源",
        "300308": "中际旭创",
        "601088": "中国神华",
        "002371": "北方华创",
        "688012": "中微公司",
    }
    return canonical_by_code.get(entity.code) or entity.name


def _announcement_search_keyword(keyword: str) -> str:
    mapping = {
        "年报": "年度报告",
        "半年报": "半年度报告",
        "一季报": "第一季度报告",
        "三季报": "第三季度报告",
    }
    return mapping.get(keyword, keyword)


def _extract_board_name(query: str) -> Optional[str]:
    text = re.sub(r"\s+", "", query or "")
    aliases = [
        "低空经济",
        "人形机器人",
        "机器人",
        "CPO",
        "算力",
        "AI",
        "光伏",
        "猪肉",
        "券商",
        "证券",
        "银行",
        "白酒",
        "半导体",
        "新能源车",
    ]
    for alias in aliases:
        if alias.lower() in text.lower():
            return alias
    for noise in [
        "有哪些股票",
        "哪些股票",
        "有什么股票",
        "成分股",
        "板块",
        "行业",
        "概念",
        "包含",
        "排行",
        "排名",
        "有哪些",
        "哪些",
        "有啥票",
        "有啥股票",
        "都有谁",
        "都有啥",
        "方向",
        "这块",
        "这条线",
        "那条线",
        "谁在涨",
        "今天",
        "强不强",
        "咋样",
        "怎么样",
        "股票",
    ]:
        text = text.replace(noise, " ")
    text = re.sub(r"\s+", "", text)
    return text or None


def _match_board_row(rows: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for row in rows:
        row_name = str(row.get("name") or row.get("名称") or row.get("板块名称") or "")
        if row_name == name:
            return row
    for row in rows:
        row_name = str(row.get("name") or row.get("名称") or row.get("板块名称") or "")
        if name in row_name or row_name in name:
            return row
    return None


def _quiet_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    sink = io.StringIO()
    proxy_names = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "NO_PROXY", "no_proxy"]
    env = os.environ
    saved = {name: env.get(name) for name in proxy_names}
    for name in proxy_names:
        if name.lower() == "no_proxy":
            env[name] = "*"
        else:
            env.pop(name, None)
    try:
        with redirect_stdout(sink), redirect_stderr(sink):
            return func(*args, **kwargs)
    finally:
        for name, value in saved.items():
            if value is None:
                env.pop(name, None)
            else:
                env[name] = value
