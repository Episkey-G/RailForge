from __future__ import annotations

from typing import Any, Dict

try:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - fallback exercised in tests without dependency
    InMemorySaver = None
    StateGraph = None
    START = END = None


class LangGraphBridge:
    def __init__(self) -> None:
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

    def record(self, run_id: str, state: str, payload: Dict[str, Any]) -> Dict[str, str]:
        self._sequence += 1
        thread_id = "lg-thread-%s" % run_id
        if self._graph is None:
            return {
                "thread_id": thread_id,
                "checkpoint_ref": "lg-checkpoint-%04d-%s" % (self._sequence, state.lower()),
            }

        config = {"configurable": {"thread_id": thread_id}}
        self._graph.invoke({"state": state, "payload": payload}, config)
        snapshot = self._graph.get_state(config)
        checkpoint_ref = snapshot.config.get("configurable", {}).get("checkpoint_id")
        if not checkpoint_ref:
            checkpoint_ref = "lg-checkpoint-%04d-%s" % (self._sequence, state.lower())
        return {"thread_id": thread_id, "checkpoint_ref": checkpoint_ref}
