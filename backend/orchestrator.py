"""
ORCHESTRATOR — LangGraph Agent State Machine
Coordinates SCOUT → SCREEN → ENGAGE → COORD → TRACK
Each node is an agent. State flows through the pipeline.
"""
from __future__ import annotations
from typing import TypedDict, Optional, List, Any
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False

from agents.scout import run_scout
from agents.screen import screen_all_sourced
from agents.engage import engage_bulk, run_followup_sweep
from agents.track import run_track, compute_pipeline_health
from utils.logger import log_event


# ── State definition ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    role_id: int
    keywords: Optional[List[str]]
    max_candidates: int
    sourced_count: int
    screened_results: List[dict]
    engaged_results: List[dict]
    top_candidate_ids: List[int]
    pipeline_health: dict
    errors: List[str]
    completed_steps: List[str]
    started_at: str


# ── Node functions ────────────────────────────────────────────────────────────

async def scout_node(state: PipelineState) -> PipelineState:
    await log_event("ORCHESTRATOR", "step", "Running SCOUT node", role_id=state["role_id"])
    count = 0
    async for event in run_scout(state["role_id"], state.get("keywords"), state.get("max_candidates", 20)):
        if event.get("event") == "completed":
            count = event.get("count", 0)
    state["sourced_count"] = count
    state["completed_steps"] = state.get("completed_steps", []) + ["scout"]
    return state


async def screen_node(state: PipelineState) -> PipelineState:
    await log_event("ORCHESTRATOR", "step", "Running SCREEN node", role_id=state["role_id"])
    results = await screen_all_sourced(state["role_id"])
    state["screened_results"] = results

    # Pick top candidates (score >= 60) for engagement
    top_ids = [
        r["candidate_id"] for r in results
        if r.get("brief", {}).get("overall_score", 0) >= 60
    ]
    state["top_candidate_ids"] = top_ids[:10]
    state["completed_steps"] = state.get("completed_steps", []) + ["screen"]
    return state


async def engage_node(state: PipelineState) -> PipelineState:
    await log_event("ORCHESTRATOR", "step", "Running ENGAGE node", role_id=state["role_id"])
    if state.get("top_candidate_ids"):
        results = await engage_bulk(state["top_candidate_ids"])
        state["engaged_results"] = results
    state["completed_steps"] = state.get("completed_steps", []) + ["engage"]
    return state


async def followup_node(state: PipelineState) -> PipelineState:
    await log_event("ORCHESTRATOR", "step", "Running follow-up sweep", role_id=state["role_id"])
    await run_followup_sweep(state["role_id"])
    state["completed_steps"] = state.get("completed_steps", []) + ["followup"]
    return state


async def track_node(state: PipelineState) -> PipelineState:
    await log_event("ORCHESTRATOR", "step", "Running TRACK node", role_id=state["role_id"])
    result = await run_track(state["role_id"])
    health = result["results"].get(state["role_id"], {})
    state["pipeline_health"] = health
    state["completed_steps"] = state.get("completed_steps", []) + ["track"]
    return state


# ── Conditional edges ─────────────────────────────────────────────────────────

def should_engage(state: PipelineState) -> str:
    """Only engage if we have top candidates."""
    return "engage" if state.get("top_candidate_ids") else "track"


def should_followup(state: PipelineState) -> str:
    """Always run followup sweep after engage."""
    return "followup"


# ── Build graph ───────────────────────────────────────────────────────────────

def build_pipeline_graph():
    if not HAS_LANGGRAPH:
        return None

    graph = StateGraph(PipelineState)

    graph.add_node("scout", scout_node)
    graph.add_node("screen", screen_node)
    graph.add_node("engage", engage_node)
    graph.add_node("followup", followup_node)
    graph.add_node("track", track_node)

    graph.set_entry_point("scout")
    graph.add_edge("scout", "screen")
    graph.add_conditional_edges("screen", should_engage, {"engage": "engage", "track": "track"})
    graph.add_conditional_edges("engage", should_followup, {"followup": "followup"})
    graph.add_edge("followup", "track")
    graph.add_edge("track", END)

    return graph.compile()


# ── Run entrypoint ────────────────────────────────────────────────────────────

async def run_full_pipeline(
    role_id: int,
    keywords: list[str] | None = None,
    max_candidates: int = 20,
) -> dict:
    """
    Runs the full SCOUT→SCREEN→ENGAGE→FOLLOWUP→TRACK pipeline.
    Works with or without LangGraph installed.
    """
    initial_state: PipelineState = {
        "role_id": role_id,
        "keywords": keywords,
        "max_candidates": max_candidates,
        "sourced_count": 0,
        "screened_results": [],
        "engaged_results": [],
        "top_candidate_ids": [],
        "pipeline_health": {},
        "errors": [],
        "completed_steps": [],
        "started_at": datetime.utcnow().isoformat(),
    }

    graph = build_pipeline_graph()

    if graph:
        # LangGraph path
        final_state = await graph.ainvoke(initial_state)
    else:
        # Fallback: sequential execution without LangGraph
        await log_event("ORCHESTRATOR", "info", "LangGraph not available — running sequential fallback", role_id=role_id)
        state = initial_state
        state = await scout_node(state)
        state = await screen_node(state)
        if state.get("top_candidate_ids"):
            state = await engage_node(state)
            state = await followup_node(state)
        state = await track_node(state)
        final_state = state

    await log_event(
        "ORCHESTRATOR", "pipeline_complete",
        f"Pipeline done. Steps: {final_state.get('completed_steps')}. Sourced: {final_state.get('sourced_count')}",
        role_id=role_id,
        data={"steps": final_state.get("completed_steps"), "sourced": final_state.get("sourced_count")},
    )

    return {
        "role_id": role_id,
        "completed_steps": final_state.get("completed_steps", []),
        "sourced_count": final_state.get("sourced_count", 0),
        "screened_count": len(final_state.get("screened_results", [])),
        "engaged_count": len(final_state.get("engaged_results", [])),
        "top_candidates": len(final_state.get("top_candidate_ids", [])),
        "pipeline_health": final_state.get("pipeline_health", {}),
        "started_at": final_state.get("started_at"),
        "completed_at": datetime.utcnow().isoformat(),
    }
