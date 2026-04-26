from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timezone
from decimal import Decimal
import math
from typing import Any, Dict, Iterable, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def success(
    *,
    intent: str,
    query: str = "",
    normalized: Optional[Dict[str, Any]] = None,
    source_chain: Optional[List[Dict[str, Any]]] = None,
    data: Any = None,
    warnings: Optional[Iterable[str]] = None,
    trade_date: Optional[str] = None,
    source_status: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "query": query,
        "normalized": json_safe(normalized or {}),
        "source_chain": json_safe(source_chain or []),
        "data": json_safe(data),
        "warnings": list(warnings or []),
        "meta": {
            "generated_at": utc_now_iso(),
            "trade_date": json_safe(trade_date),
            "source_status": json_safe(source_status or {}),
        },
    }


def failure(
    *,
    intent: str,
    query: str = "",
    error_type: str = "runtime_failed",
    error_message: str,
    normalized: Optional[Dict[str, Any]] = None,
    source_chain: Optional[List[Dict[str, Any]]] = None,
    warnings: Optional[Iterable[str]] = None,
    source_status: Optional[Dict[str, Any]] = None,
    data: Any = None,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "intent": intent,
        "query": query,
        "normalized": json_safe(normalized or {}),
        "source_chain": json_safe(source_chain or []),
        "data": json_safe(data),
        "warnings": list(warnings or []),
        "error": {
            "type": error_type,
            "message": error_message,
        },
        "meta": {
            "generated_at": utc_now_iso(),
            "trade_date": None,
            "source_status": json_safe(source_status or {}),
        },
    }


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        return float(value) if value.is_finite() else None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)
