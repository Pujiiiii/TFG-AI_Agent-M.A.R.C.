import os
import requests
import groq
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from marc.core.agent import agent_amb_historial, store
from marc.core.actions import executar_accio, consumir_ultima_accio

# Inicialització de FastAPI per al secretari executiu M.A.R.C.
app = FastAPI(title="M.A.R.C. Executive Assistant API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS DE DADES ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "sessio_per_defecte"

class ConfirmRequest(BaseModel):
    action_id: str
    approved: bool
    session_id: str = "sessio_per_defecte"

# --- ENDPOINTS CHAT I ACTIONS (HITL) ---
@app.post("/chat")
def xat(peticio: ChatRequest):
    try:
        resposta = agent_amb_historial.invoke(
            {"input": peticio.message},
            config={"configurable": {"session_id": peticio.session_id}}
        )
        output_text = resposta.get("output", "")
        if not output_text or not output_text.strip():
            output_text = "⚠️ M.A.R.C. ha finalitzat la comanda sense generar text de resposta."
    except groq.RateLimitError:
        output_text = "⚠️ **Límit d'ús assolit (Rate Limit 429)**. Si us plau, espera uns segons i torna a provar-ho."
    except Exception as e:
        output_text = f"⚠️ S'ha produït un error processant la petició: {str(e)}"
    
    accio = consumir_ultima_accio()
    pending = None
    if accio:
        pending = {
            "action_id": accio["action_id"],
            "type": accio["type"],
            "summary": accio["summary"],
            "data": accio.get("data", {})
        }

    return {"response": output_text, "pending_action": pending}

@app.post("/api/confirm-action")
async def confirm_action_endpoint(body: ConfirmRequest):
    try:
        resultat = executar_accio(body.action_id, body.approved)
        return {
            "status": "approved" if body.approved else "rejected",
            "message": resultat.get("message", "Acció processada."),
            "success": resultat.get("success", False)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error intern executant l'acció: {str(e)}",
            "success": False
        }

# --- ESTAT DEL SISTEMA I SERVEIS ---
@app.get("/api/system-status")
def get_system_status():
    searxng_online = False
    try:
        r = requests.get("http://localhost:8080", timeout=1)
        searxng_online = (r.status_code == 200)
    except Exception:
        searxng_online = False

    return {
        "services": {
            "searxng": "ONLINE" if searxng_online else "OFFLINE",
            "llm_engine": "Groq",
            "backend": "ONLINE"
        },
        "sessions": list(store.keys()) if store else ["sessio_per_defecte"]
    }

# --- FITXERS ESTÀTICS I VISTA WEB ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))