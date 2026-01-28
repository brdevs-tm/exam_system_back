from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List, Any, Optional

MAX_EVENTS_PER_ATTEMPT = 500  # xohlasang 2000 qil

class MonitorStore:
    """
    Attempt bo‘yicha eventlarni RAM’da ring buffer qilib saqlaydi.
    Reconnect bo‘lganda history yo‘qolmaydi.
    """
    def __init__(self) -> None:
        self.by_attempt: Dict[int, Deque[dict]] = defaultdict(lambda: deque(maxlen=MAX_EVENTS_PER_ATTEMPT))

    def add(self, attempt_id: int, event: dict) -> None:
        self.by_attempt[int(attempt_id)].append(event)

    def list(self, attempt_id: Optional[int] = None, limit: int = 100) -> List[dict]:
        if attempt_id is None:
            # hammasidan umumiy last limit
            merged: List[dict] = []
            for dq in self.by_attempt.values():
                merged.extend(list(dq))
            merged.sort(key=lambda x: x.get("ts", ""))
            return merged[-limit:]
        dq = self.by_attempt.get(int(attempt_id), deque())
        return list(dq)[-limit:]


monitor_store = MonitorStore()
