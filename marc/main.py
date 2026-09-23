from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from marc.core.agent import get_agent_executor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

app = FastAPI(title="API de M.A.R.C.", description="Core del TFG - Assistent Agèntic")
agent_executor = get_agent_executor()

# 1. Base de dades temporal per guardar l'historial de cada sessió
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 2. Embolcallem el nostre agent amb el gestor d'historial automàtic
agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# 3. Afegim el camp session_id a les dades d'entrada
class ChatRequest(BaseModel):
    message: str
    session_id: str = "sessio_per_defecte" 

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Invoquem l'agent passant-li la configuració de la sessió
        response = agent_with_chat_history.invoke(
            {"input": request.message},
            config={"configurable": {"session_id": request.session_id}}
        )
        return ChatResponse(reply=response["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))