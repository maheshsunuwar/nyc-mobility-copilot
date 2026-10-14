from typing import Optional, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import os
import psycopg2
from schema_context import DB_CONFIG

from schema_context import get_live_schema, FEW_SHOT_EXAMPLES

class AgentState(TypedDict):
    question: str
    schema: str
    sql: Optional[str]
    result: Optional[list]
    error: Optional[str]
    retry_count: int
    answer: Optional[str]

load_dotenv()

REFUSAL = ("I can only read data, so I can't modify or delete records. "
           "I can answer questions about trip counts, fares, busy hours, and pickup zones.")
TERMINAL_ERRORS = ("permission denied", "must be owner")

llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

def get_schema_node(state: AgentState) -> AgentState:
    state['schema'] = get_live_schema()

    return state

def generate_sql_node(state: AgentState) -> AgentState:
    examples_text = "\n\n".join(
        f"Q: {ex['question']}\nSQL: {ex['sql']}" for ex in FEW_SHOT_EXAMPLES
    )
    # print("--- generate_sql_node called ---")
    # print("incoming error:", state.get("error"))
    # print("incoming sql:", state.get("sql"))
    # print("incoming retry_count:", state.get("retry_count"))

    error_context = ""
    if state.get("error"):
        error_context = f"""
            Your previous attempt failed with this error:
            {state['error']}

            The query you wrote was:
            {state['sql']}

            If the error says a column or table does not exist, re-check the Schema section above and use the exact names listed there. Do not just add type casts.
            If the error says the query was rejected, write a read-only SELECT query instead. If the question asks to modify or delete data, you cannot do that.
            Carefully re-check the Schema section above. The error likely means you used a column or table name that does not exist in the schema. Find the correct column name from the schema and rewrite the query. Do not just add type casts or try minor syntax tweaks -- identify which specific name in your query is wrong.
        """

    prompt = f"""You are a SQL assistant for a NYC taxi mobility database.

        Schema:
        {state['schema']}

        Example questions and their correct SQL:
        {examples_text}
        {error_context}

        Write ONE PostgreSQL SELECT query to answer this question. Return ONLY the SQL, no explanation.

        Question: {state['question']}"""
    response = llm.invoke(prompt)
    sql = response.content.strip()
    # strip markdown code fences if the model added them despite instructions
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.lower().startswith("sql"):
            sql = sql[3:]
        sql = sql.strip()

    state["sql"] = sql
    return state

def validate_sql_node(state: AgentState) -> AgentState:
    sql = state['sql'].strip()
    sql_upper = sql.upper()

    if not sql_upper.startswith("SELECT"):
        state['error'] = f"Rejected: query does not start with SELECT. Got: {sql[:50]}"
        state['sql'] = None
        state['answer'] = REFUSAL
        return state

    forbidden = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "CREATE"]
    for word in forbidden:
        if word in sql_upper:
            state['error'] = f"Rejected: query contains forbidden keyword {word}"
            state['sql'] = None
            state['answer'] = REFUSAL
            return state
    state['error'] = None
    return state

def after_validation(state: AgentState) -> str:
    return "rejected" if state['sql'] is None else "ok"

def execute_sql_node(state: AgentState) -> AgentState:
    if state['sql'] == None:
        state['retry_count'] += 1 # a validation rejection is still a failed attempt
        return state

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(state['sql'])
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()

        state['result'] = [dict(zip(columns, row)) for row in rows]
        state['error'] = None
    except Exception as e:
        state['result'] = None
        state['error'] = str(e)
        state['retry_count'] += 1
        conn.rollback() if 'conn' in dir() else None
    return state

def generate_response_node(state: AgentState) -> AgentState:
    if state['error'] is not None:
        state['answer'] = "I wasn't able to answer that question against the available data."
        return state

    clean_result = []
    for row in state['result']:
        clean_row = {k: (float(v) if hasattr(v, 'as_tuple') else v) for k, v in row.items()}
        clean_result.append(clean_row)

    prompt = f"""Given this question and the SQL result, write one clear, direct sentence answering it. Use real numbers from the result, don't round unnecessarily.
    Describe only what the Result contains. If the question mentions creating, copying, or changing anything, say that did not happen." This is a soft backup. The refusal node is the structural fix.

    Question: {state['question']}
    Result: {clean_result}"""

    response = llm.invoke(prompt)
    state['answer'] = response.content.strip()

    return state

def refuse_node(state: AgentState) -> AgentState:
    print(f"[refused] db error: {state['error']}", file=sys.stderr)
    err = state['error'].lower()
    if "permission denied for schema" in err:
        state['answer'] = REFUSAL
    else:
        state['answer'] = ("I couldn't read that data because of a database access problem. "
                           "This looks like a system issue, not a problem with your question.")
    state['result'] = None
    return state

def should_retry(state: AgentState) -> str:
    err = state['error']
    if state['error'] is None:
        return 'success'
    if any(t in err.lower() for t in TERMINAL_ERRORS):
        return 'refuse'
    if state['retry_count'] >= 3:
        return 'give_up'

def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("get_schema", get_schema_node)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("refuse", refuse_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("generate_response", generate_response_node)

    graph.set_entry_point("generate_sql")
    graph.add_edge("get_schema", "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_conditional_edges(
        "validate_sql",
        after_validation,
        {
            "rejected": END,
            "ok": "execute_sql"
        }
    )
    graph.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            'retry': "generate_sql",
            'give_up': "generate_response",
            'success': "generate_response",
            'refuse': "refuse"
        }
    )
    graph.add_edge("refuse", END)
    graph.add_edge("generate_response", END)

    return graph.compile()

def ask(agent, question: str) -> AgentState:
    # a brand-new state dict on every call, so requests can never leak into each other
    return agent.invoke({
        "question": question, "schema": "", "sql": None, "result": None,
        "error": None, "retry_count": 0, "answer": None,
    })

if __name__ == "__main__":
    import sys
    question = sys.argv[1] if len(sys.argv) > 1 else "Which hour is the busiest for taxi pickups overall?"

    final = ask(build_agent(), question=question)
    print("SQL:   ", final["sql"])
    print("Retries:", final["retry_count"])
    print("Answer:", final["answer"])
