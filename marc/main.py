import os
import requests
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from marc.core.agent import agent_amb_historial, store
from marc.core.actions import executar_accio, consumir_ultima_accio

app = FastAPI(title="M.A.R.C. API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "sessio_per_defecte"

class ConfirmRequest(BaseModel):
    action_id: str
    approved: bool
    session_id: str = "sessio_per_defecte"

def construir_arbre(ruta="."):
    """Construeix recursivament l'arbre de directoris i fitxers."""
    ignorar = {".git", "__pycache__", "venv", "env", "searxng", ".pytest_cache"}
    arbre = []
    try:
        elements = sorted(os.listdir(ruta))
    except Exception:
        return arbre

    for el in elements:
        if el in ignorar:
            continue
        ruta_completa = os.path.join(ruta, el)
        rel_path = os.path.relpath(ruta_completa, ".")
        if os.path.isdir(ruta_completa):
            arbre.append({
                "type": "folder",
                "name": el,
                "path": rel_path,
                "children": construir_arbre(ruta_completa)
            })
        else:
            arbre.append({
                "type": "file",
                "name": el,
                "path": rel_path
            })
    return arbre

@app.post("/chat")
def xat(peticio: ChatRequest):
    resposta = agent_amb_historial.invoke(
        {"input": peticio.message},
        config={"configurable": {"session_id": peticio.session_id}}
    )
    
    # Comprovem si alguna eina ha registrat una acció durant aquest torn
    accio = consumir_ultima_accio()
    pending = None
    if accio:
        pending = {
            "action_id": accio["action_id"],
            "type": accio["type"],
            "summary": accio["summary"],
            "diff": accio["data"].get("diff", "")
        }

    return {
        "response": resposta["output"],
        "pending_action": pending
    }

@app.post("/api/confirm-action")
def confirmar_accio(req: ConfirmRequest):
    resultat = executar_accio(req.action_id, req.approved)
    
    # Notifiquem a l'historial de l'agent la resolució
    agent_amb_historial.invoke(
        {"input": f"[SISTEMA INTERN]: L'usuari ha {'aprovat' if req.approved else 'rebutjat'} l'acció amb ID {req.action_id}. Resultat: {resultat['message']}"},
        config={"configurable": {"session_id": req.session_id}}
    )
    
    return resultat

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
        "file_tree": construir_arbre("."),
        "sessions": list(store.keys()) if store else ["sessio_per_defecte"]
    }

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))