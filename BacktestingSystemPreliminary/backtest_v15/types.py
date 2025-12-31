from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

class SignalType(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    NONE = "NONE"

@dataclass(frozen=True)
class Signal:
    type: SignalType
    reason_codes: tuple[str, ...] = ()
    metadata: Dict[str, Any] = None

@dataclass
class Position:
    ticker: str
    entry_ts: Any
    entry_price: float
    size: float
    stop_close: float
    risk_pct: float
    catalyst_class: str
    regime: str
