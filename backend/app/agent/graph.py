import json
from typing import Any, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from backend.app.agent.prompts import SYSTEM_PROMPT
from backend.app.agent.validator import validate_pipeline
from backend.app.agent.executor import execute_pipeline


class GeneratedQuery(BaseModel):
    pipeline: list[dict[str, Any]] = Field(
        description="MongoDB aggregation pipeline as a JSON array"
    )
    explanation: str = Field(
        description="Short explanation of the query"
    )


class AgentState(TypedDict, total=False):
    question: str
    pipeline: list
    explanation: str
    results: list
    answer: str


llm = ChatOllama(
    model="qwen2.5-coder:3b",
    temperature=0,
    num_ctx=4096
)

structured_llm = llm.with_structured_output(
    GeneratedQuery,
    method="json_schema"
)


def generate_query(state: AgentState) -> dict:
    result = structured_llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", state["question"])
    ])

    if result is None:
        raise ValueError("Ollama returned no structured output")

    return {
        "pipeline": result.pipeline,
        "explanation": result.explanation
    }


def check_query(state: AgentState) -> dict:
    validate_pipeline(state["pipeline"])
    return {}


def retrieve_data(state: AgentState) -> dict:
    results = execute_pipeline(state["pipeline"])
    return {"results": results}



def format_answer(state: AgentState) -> dict:
    results = state["results"]

    if not results:
        return {"answer": "No matching records were found."}

    if len(results) == 1 and len(results[0]) == 1:
        field, value = next(iter(results[0].items()))

        if isinstance(value, (int, float)):
            label = field.replace("_", " ").title()
            if field.endswith("_cents"):
                return {"answer": f"{label[:-6]}: ${value / 100:,.2f}"}
            return {"answer": f"{label}: {value:,}"}

    lines = []

    for i, record in enumerate(results, start=1):
        name = str(record.get("_id", record.get("supplier", "Unknown")))
        metrics = []

        for key, value in record.items():
            if key in ("_id", "supplier"):
                continue

            if isinstance(value, (int, float)):
                if "price" in key or "spending" in key:
                    if key.endswith("_cents") or key == "total_spending":
                        metrics.append(f"${value / 100:,.2f}")
                    else:
                        metrics.append(f"{key}: {value:,.2f} (unit unverified)")
                else:
                    metrics.append(f"{key.replace('_', ' ')}: {value:,}")
            else:
                metrics.append(f"{key}: {value}")

        lines.append(f"{i}. {name} — {', '.join(metrics)}")

    return {"answer": "\\n".join(lines)}

workflow = StateGraph(AgentState)

workflow.add_node("generate_query", generate_query)
workflow.add_node("validate_query", check_query)
workflow.add_node("execute_query", retrieve_data)
workflow.add_node("format_answer", format_answer)

workflow.add_edge(START, "generate_query")
workflow.add_edge("generate_query", "validate_query")
workflow.add_edge("validate_query", "execute_query")
workflow.add_edge("execute_query", "format_answer")
workflow.add_edge("format_answer", END)

agent = workflow.compile()
