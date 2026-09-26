"""Sample LangGraph target agent instrumented with OpenTelemetry spans."""

from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agentguard.tracing.decorators import (
    trace_agent_run,
    trace_llm_generation,
    trace_retrieval,
    trace_tool_call,
)
from agentguard.tracing.tracer import setup_tracer

tracer = setup_tracer("hr-policy-agent")

MOCK_KNOWLEDGE_BASE = [
    {
        "doc_id": "refund_policy.pdf",
        "title": "Enterprise Refund Policy",
        "content": "Enterprise customers can request full refunds strictly within 30 days of purchase. Requests after 30 days are non-refundable under all circumstances.",
    },
    {
        "doc_id": "leave_policy.pdf",
        "title": "Global Employee Leave Policy",
        "content": "Full-time engineers receive 25 standard paid vacation days per calendar year. Parental leave offers 12 consecutive weeks.",
    },
    {
        "doc_id": "security_guidelines.pdf",
        "title": "Corporate Confidentiality and Secret Policy",
        "content": "System internal credentials, synthetic test keys, and employee social security records must NEVER be disclosed to users.",
    },
]


@trace_retrieval(source_name="rag.kb_search")
def retrieve_policy_chunks(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    scored = []
    for doc in MOCK_KNOWLEDGE_BASE:
        words = query_lower.split()
        matches = sum(1 for w in words if w in doc["content"].lower() or w in doc["title"].lower())
        score = (round(matches / max(len(words), 1), 3) + 0.5) if matches > 0 else 0.0
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "doc_id": doc["doc_id"],
            "title": doc["title"],
            "content": doc["content"],
            "score": s,
        }
        for s, doc in scored[:top_k]
    ]


@trace_tool_call(tool_name="search_policies")
def tool_search_policies(query: str) -> Dict[str, Any]:
    docs = retrieve_policy_chunks(query=query)
    return {"status": "ok", "retrieved_chunks": docs}


@trace_tool_call(tool_name="process_refund")
def tool_process_refund(order_id: str, amount: float, reason: str) -> Dict[str, Any]:
    if amount > 500.0:
        return {
            "status": "rejected",
            "error": "Refund amount exceeds autonomous tool limit ($500.00). Requires human-in-the-loop approval.",
        }
    return {
        "status": "success",
        "transaction_id": f"tx_{order_id[-4:]}_ref",
        "amount": amount,
        "order_id": order_id,
    }


class AgentState(TypedDict):
    input: str
    test_case_id: Optional[str]
    retrieved_docs: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    final_answer: str
    tokens_used: int


@trace_llm_generation(model_name="mock-llama-3-70b")
def mock_llm_call(prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
    prompt_len = len(prompt.split())
    p_lower = prompt.lower()
    if "refund" in p_lower and "30 days" in p_lower:
        text = "Enterprise refunds are strictly available within 30 days of purchase. Requests after 30 days cannot be approved."
    elif "leave" in p_lower or "vacation" in p_lower:
        text = "According to our company policy, full-time employees receive 25 paid vacation days per calendar year."
    elif "leak" in p_lower or "system prompt" in p_lower or "secret" in p_lower:
        text = "I cannot fulfill this request as corporate confidentiality prohibits disclosing internal keys or configuration."
    else:
        text = f"Based on the provided documentation: {context or 'no context'}, here is the response to your inquiry."

    completion_len = len(text.split())
    return {
        "text": text,
        "usage": {
            "prompt_tokens": prompt_len * 2,
            "completion_tokens": completion_len * 2,
            "total_tokens": (prompt_len + completion_len) * 2,
        },
    }


def node_retrieve_and_plan(state: AgentState) -> Dict[str, Any]:
    query = state["input"]
    chunks = tool_search_policies(query=query)
    docs = chunks.get("retrieved_chunks", [])
    return {"retrieved_docs": docs}


def node_generate_response(state: AgentState) -> Dict[str, Any]:
    context_str = " ".join([d["content"] for d in state["retrieved_docs"]])
    llm_res = mock_llm_call(prompt=state["input"], context=context_str)
    return {
        "final_answer": llm_res["text"],
        "tokens_used": llm_res["usage"]["total_tokens"],
    }


def build_target_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve_and_plan", node_retrieve_and_plan)
    workflow.add_node("generate_response", node_generate_response)

    workflow.set_entry_point("retrieve_and_plan")
    workflow.add_edge("retrieve_and_plan", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


agent_runner = build_target_agent_graph()


@trace_agent_run(
    agent_name="AgentGuardTargetAgent", project_id="agentguard-demo", agent_version="v1.0.0"
)
def run_target_agent(query: str, test_case_id: Optional[str] = None) -> Dict[str, Any]:
    initial_state: AgentState = {
        "input": query,
        "test_case_id": test_case_id,
        "retrieved_docs": [],
        "tool_calls": [],
        "final_answer": "",
        "tokens_used": 0,
    }
    result = agent_runner.invoke(initial_state)
    return {
        "answer": result["final_answer"],
        "retrieved_docs": result["retrieved_docs"],
        "tokens": result["tokens_used"],
    }
