from __future__ import annotations

import json
from typing import Any, Dict

from railforge.core.models import WorkspaceLayout

try:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - fallback exercised in tests without dependency
    InMemorySaver = None
    StateGraph = None
    START = END = None


class LangGraphBridge:
    def __init__(self, layout: WorkspaceLayout | None = None) -> None:
        self._layout = layout
        self._sequence = 0
        self._graph = None
        if StateGraph is not None and InMemorySaver is not None:
            workflow = StateGraph(dict)
            workflow.add_node("persist", self._persist)
            workflow.add_edge(START, "persist")
            workflow.add_edge("persist", END)
            self._graph = workflow.compile(checkpointer=InMemorySaver())

    @staticmethod
    def _persist(state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def _latest_path(self, run_id: str):
        if self._layout is None:
            return None
        self._layout.ensure()
        return self._layout.langgraph_dir / ("%s.latest.json" % run_id)

    def _history_path(self, run_id: str, sequence: int, state: str):
        if self._layout is None:
            return None
        self._layout.ensure()
        return self._layout.langgraph_dir / ("%s-%04d-%s.json" % (run_id, sequence, state.lower()))

    def _next_sequence(self, run_id: str) -> int:
        latest = self._load_latest_metadata(run_id)
        if latest:
            return int(latest.get("sequence", 0)) + 1
        self._sequence += 1
        return self._sequence

    def _persist_record(self, run_id: str, state: str, payload: Dict[str, Any], ref: Dict[str, str], sequence: int) -> None:
        latest_path = self._latest_path(run_id)
        history_path = self._history_path(run_id, sequence, state)
        if latest_path is None or history_path is None:
            return
        persisted = {
            "run_id": run_id,
            "sequence": sequence,
            "state": state,
            "payload": payload,
            "thread_id": ref["thread_id"],
            "checkpoint_ref": ref["checkpoint_ref"],
        }
        latest_path.write_text(json.dumps(persisted, indent=2, ensure_ascii=False), encoding="utf-8")
        history_path.write_text(json.dumps(persisted, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_latest_metadata(self, run_id: str) -> Dict[str, Any]:
        latest_path = self._latest_path(run_id)
        if latest_path is None or not latest_path.exists():
            return {}
        return json.loads(latest_path.read_text(encoding="utf-8"))

    def load_latest(self, run_id: str) -> Dict[str, str]:
        payload = self._load_latest_metadata(run_id)
        if not payload:
            return {}
        return {
            "thread_id": payload.get("thread_id", ""),
            "checkpoint_ref": payload.get("checkpoint_ref", ""),
        }

    def record(self, run_id: str, state: str, payload: Dict[str, Any]) -> Dict[str, str]:
        sequence = self._next_sequence(run_id)
        latest = self.load_latest(run_id)
        thread_id = latest.get("thread_id") or "lg-thread-%s" % run_id
        if self._graph is None:
            ref = {
                "thread_id": thread_id,
                "checkpoint_ref": "lg-checkpoint-%04d-%s" % (sequence, state.lower()),
            }
            self._persist_record(run_id, state, payload, ref, sequence)
            return ref

        config = {"configurable": {"thread_id": thread_id}}
        self._graph.invoke({"state": state, "payload": payload}, config)
        snapshot = self._graph.get_state(config)
        checkpoint_ref = snapshot.config.get("configurable", {}).get("checkpoint_id")
        if not checkpoint_ref:
            checkpoint_ref = "lg-checkpoint-%04d-%s" % (sequence, state.lower())
        ref = {"thread_id": thread_id, "checkpoint_ref": checkpoint_ref}
        self._persist_record(run_id, state, payload, ref, sequence)
        return ref
