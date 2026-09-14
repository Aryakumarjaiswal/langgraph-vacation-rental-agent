from __future__ import annotations

import re
from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy import text

from Database import SessionLocal
from services.llm import get_chat_llm, message_text

SCHEMA = """
Table bookings_info (
  _id VARCHAR,
  platform VARCHAR,          -- airbnb, homeaway, etc.
  platform_id VARCHAR,
  listing_id VARCHAR,
  confirmation_code VARCHAR,
  check_in DATETIME,
  check_out DATETIME,
  listing_title VARCHAR,
  account_id VARCHAR,
  guest_id VARCHAR,
  guest_name VARCHAR,
  commission DECIMAL
)
"""

FORBIDDEN = re.compile(
    r"\b(drop|alter|truncate|create|grant|revoke|shutdown|replace)\b",
    re.IGNORECASE,
)
ALLOWED_START = re.compile(r"^(select|insert|update|delete)\b", re.IGNORECASE)


class OpsState(TypedDict):
    question: str
    intent: str
    sql: str
    db_result: str
    answer: str


class SQLPlan(BaseModel):
    intent: Literal["read", "write", "clarify"] = Field(
        description="read=SELECT, write=INSERT/UPDATE/DELETE, clarify=need more info"
    )
    sql_query: str = Field(description="Single MySQL statement or empty if clarifying")
    task_review: str = Field(description="Short note on whether the request is safe and doable")


def _llm():
    return get_chat_llm(temperature=0)


def _clean_sql(sql: str) -> str:
    cleaned = sql.replace("```sql", "").replace("```", "").strip().rstrip(";")
    return " ".join(cleaned.split())


def _validate_sql(sql: str, intent: str) -> str:
    cleaned = _clean_sql(sql)
    if not cleaned:
        raise ValueError("No SQL was generated.")
    if ";" in cleaned:
        raise ValueError("Only one SQL statement is allowed.")
    if FORBIDDEN.search(cleaned):
        raise ValueError("That statement type is blocked (no DDL).")
    if "bookings_info" not in cleaned.lower():
        raise ValueError("Queries must target bookings_info.")
    if not ALLOWED_START.search(cleaned):
        raise ValueError("Only SELECT, INSERT, UPDATE, or DELETE are allowed.")
    head = cleaned.split()[0].lower()
    if intent == "read" and head != "select":
        raise ValueError("Read intent must be a SELECT.")
    if head in {"update", "delete"} and " where " not in f" {cleaned.lower()} ":
        raise ValueError("UPDATE/DELETE must include a WHERE clause.")
    return cleaned


def plan_sql(state: OpsState) -> OpsState:
    planner = _llm().with_structured_output(SQLPlan)
    plan = planner.invoke(
        [
            SystemMessage(
                content=(
                    "You convert operations questions into a single MySQL statement "
                    "against bookings_info only. Use date(column) for date filters. "
                    f"Schema:\n{SCHEMA}\n"
                    "If the request is ambiguous, set intent=clarify and leave sql_query empty. "
                    "Never use DROP/ALTER/CREATE or any DDL. "
                    "UPDATE and DELETE must include a WHERE clause."
                )
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    state["intent"] = plan.intent
    state["sql"] = plan.sql_query
    state["answer"] = plan.task_review
    return state


def execute_sql(state: OpsState) -> OpsState:
    if state["intent"] == "clarify":
        state["db_result"] = ""
        return state
    sql = _validate_sql(state["sql"], state["intent"])
    state["sql"] = sql
    db = SessionLocal()
    try:
        result = db.execute(text(sql))
        if sql.lower().startswith("select"):
            rows = result.fetchall()
            payload = str([tuple(row) for row in rows[:50]])
            if len(rows) > 50:
                payload += f" ... ({len(rows)} rows total)"
        else:
            db.commit()
            payload = f"Write succeeded. rowcount={result.rowcount}"
        state["db_result"] = payload
    except Exception as exc:
        db.rollback()
        state["db_result"] = f"SQL error: {exc}"
    finally:
        db.close()
    return state


def explain(state: OpsState) -> OpsState:
    if state["intent"] == "clarify" and not state.get("db_result"):
        return state
    response = _llm().invoke(
        [
            SystemMessage(
                content=(
                    "Act as a property recptionist.You will be given exact user question and database result.You have to answer user question based on the database result."
                    "Be concise. Never mention SQL, queries, tables, columns, or technical jargon. "
                    "Never invent rows."
                )
            ),
            HumanMessage(
                content=(
                    f"Question: {state['question']}\n"
                    f"Result: {state.get('db_result')}"
                )
            ),
        ]
    )
    state["answer"] = message_text(response.content)
    return state


graph = StateGraph(OpsState)
graph.add_node("plan_sql", plan_sql)
graph.add_node("execute_sql", execute_sql)
graph.add_node("explain", explain)
graph.add_edge(START, "plan_sql")
graph.add_edge("plan_sql", "execute_sql")
graph.add_edge("execute_sql", "explain")
graph.add_edge("explain", END)
ops_agent = graph.compile()


def ask_ops(question: str) -> dict[str, Any]:
    result = ops_agent.invoke(
        {
            "question": question,
            "intent": "",
            "sql": "",
            "db_result": "",
            "answer": "",
        }
    )
    return result
