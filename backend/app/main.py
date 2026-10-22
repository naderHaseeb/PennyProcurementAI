
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.agent.reliable import try_answer
from backend.app.agent.graph import agent

app = FastAPI(title="Penny Procurement AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # FIRST: Use known, verified procurement pipelines
        result = try_answer(request.question)

        if result is not None:
            source = "reliable_pipeline"

        else:
            # SECOND: Use Ollama for other questions
            result = agent.invoke({
                "question": request.question
            })
            source = "ollama_langgraph"

        return {
            "question": request.question,
            "answer": result["answer"],
            "pipeline": result["pipeline"],
            "results": result["results"],
            "source": source
        }

    except ValueError as error:
        print("QUERY ERROR:", repr(error), flush=True)
        raise HTTPException(
            status_code=422,
            detail="The generated query could not be processed safely."
        )

    except Exception as error:
        print("BACKEND ERROR:", repr(error), flush=True)
        raise HTTPException(
            status_code=503,
            detail="The assistant could not complete the request."
        )
