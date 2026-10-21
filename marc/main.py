import os
import requests
from datetime import datetime
import groq
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from marc.core.agent import agent_amb_historial, store
from marc.core.actions import executar_accio, consumir_ultima_accio
from marc.core.db import (
    db_get_tasks,
    db_add_task,
    db_toggle_task,
    db_get_events,
    db_get_emails,
    get_db_connection
)

# Inicialització de FastAPI per a M.A.R.C. Assistent Personal i Secretari
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

class ToggleTaskRequest(BaseModel):
    task_id: int

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "mitjana"
    due_date: str = ""
    description: str = ""

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
            output_text = "⚠️ M.A.R.C. ha processat la sol·licitud sense generar resposta de text."
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

# --- ESTAT DEL SISTEMA I DASHBOARD EXECUTIU ---
@app.get("/api/system-status")
def get_system_status():
    searxng_online = False
    try:
        r = requests.get("http://localhost:8080", timeout=1)
        searxng_online = (r.status_code == 200)
    except Exception:
        searxng_online = False

    # Verificació de connectivitat de base de dades
    db_ok = False
    try:
        conn = get_db_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    smtp_ready = bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER"))
    telegram_ready = bool(os.getenv("TELEGRAM_BOT_TOKEN"))

    return {
        "services": {
            "backend": "ONLINE",
            "database": "ONLINE" if db_ok else "ERROR",
            "searxng": "ONLINE" if searxng_online else "OFFLINE",
            "email_hub": "SMTP_REAL" if smtp_ready else "LOCAL_HUB",
            "telegram": "ONLINE" if telegram_ready else "STANDBY"
        },
        "sessions": list(store.keys()) if store else ["sessio_per_defecte"]
    }

@app.get("/api/dashboard")
def get_dashboard():
    """Retorna les dades actualitzades per pintar l'agenda i les tasques al panell lateral."""
    avui_str = datetime.now().strftime("%Y-%m-%d")
    tasques = db_get_tasks()
    esdeveniments_avui = db_get_events(date_prefix=avui_str)
    correus_no_llegits = db_get_emails(folder="inbox", limit=5, unread_only=True)

    pendents_count = sum(1 for t in tasques if t["status"] == "pendent")
    completades_count = sum(1 for t in tasques if t["status"] == "completada")

    return {
        "today_date": datetime.now().strftime("%d/%m/%Y"),
        "tasks": tasques,
        "events": esdeveniments_avui,
        "unread_emails_count": len(correus_no_llegits),
        "unread_emails": correus_no_llegits,
        "stats": {
            "pending_tasks": pendents_count,
            "completed_tasks": completades_count,
            "today_events_count": len(esdeveniments_avui)
        }
    }

# --- ACCIONS RÀPIDES DE TASQUES DES DE LA INTERFÍCIE ---
@app.post("/api/tasks/toggle")
def toggle_task_endpoint(req: ToggleTaskRequest):
    nou_estat = db_toggle_task(req.task_id)
    if nou_estat is None:
        raise HTTPException(status_code=404, detail="Tasca no trobada.")
    return {"success": True, "task_id": req.task_id, "new_status": nou_estat}

@app.post("/api/tasks/create")
def create_task_endpoint(req: CreateTaskRequest):
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="El títol de la tasca és obligatori.")
    tid = db_add_task(
        title=req.title,
        priority=req.priority,
        due_date=req.due_date,
        description=req.description
    )
    return {"success": True, "task_id": tid, "message": "Tasca creada correctament."}

# --- FITXERS ESTÀTICS I VISTA WEB ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))