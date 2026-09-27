"""In-memory conversation state for multi-turn flows (the formulation classifier).

Kept in RAM only and keyed by the anonymous session id: nothing about the product is
written to disk, and state expires after 30 minutes of inactivity.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class FlowState:
    flow: str  # "formulation"
    step: int = 0
    answers: dict[str, str] = field(default_factory=dict)  # question id -> option id
    original_question: str = ""
    updated_at: float = field(default_factory=time.monotonic)


class SessionStore:
    def __init__(self, ttl_seconds: float = 1800, max_sessions: int = 2000) -> None:
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._states: OrderedDict[str, FlowState] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session_id: str) -> FlowState | None:
        with self._lock:
            state = self._states.get(session_id)
            if state is None:
                return None
            if time.monotonic() - state.updated_at > self._ttl:
                del self._states[session_id]
                return None
            return state

    def set(self, session_id: str, state: FlowState) -> None:
        with self._lock:
            state.updated_at = time.monotonic()
            self._states[session_id] = state
            self._states.move_to_end(session_id)
            while len(self._states) > self._max:
                self._states.popitem(last=False)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._states.pop(session_id, None)
