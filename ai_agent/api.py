from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent_graph import ask, build_agent

app = FastAPI(title="NYC Mobility Copilot")
agent = build_agent()   # compiled once, when the server starts

class Question(BaseModel):
    question: str = Field(min_length=3, max_length=300)

class Answer(BaseModel):
    answer: str
    sql: str | None
    failed_attempts: int


@app.post("/get", response_model=Answer)
def ask_endpoint(body: Question):
    final = ask(agent=agent, question=body.question)

    return Answer(
        answer=final["answer"] or "I wasn't able to answer that.",
        sql=final['sql'],
        failed_attempts=final['retry_count']
    )

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app=app, port=8000, host="127.0.0.1")
