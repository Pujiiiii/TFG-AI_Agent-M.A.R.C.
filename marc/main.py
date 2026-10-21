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
    db_get_sync_summary,
    get_db_connection
)
from marc.services.sync_manager import (
    run_full_synchronization,
    check_internet_connection
)
from marc.services.calendar_service import (
    fetch_calendar_events,
    add_calendar_event,
    is_google_calendar_connected
)
from marc.services.email_service import (
    fetch_unread_emails,
    is_email_configured
)
from marc.services.spotify_service import (
    play_music,
    control_playback,
    is_spotify_api_configured
)

# Inicialització de FastAPI per a M.A.R.C. Assistent Personal i Secretari
app = FastAPI(title="M.A.R.C. Executive Assistant API", version="2.5")

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

class CreateEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str = ""
    location: str = ""
    description: str = ""

class SpotifyPlayRequest(BaseModel):
    query: str
    music_type: str = "track"

class SpotifyControlRequest(BaseModel):
    command: str

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
            output_text = "⚠️ M.A.R.C. ha processat la comanda sense generar text de resposta."
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

    db_ok = False
    try:
        conn = get_db_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    gcal_mode = "GOOGLE_API" if is_google_calendar_connected() else "LOCAL_DB"
    email_mode = "IMAP_SMTP_REAL" if is_email_configured() else "LOCAL_HUB"
    spotify_mode = "SPOTIPY_API" if is_spotify_api_configured() else "NATIVE_APP"
    telegram_ready = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    has_internet = check_internet_connection()
    sync_summary = db_get_sync_summary()

    return {
        "services": {
            "backend": "ONLINE",
            "database": "ONLINE" if db_ok else "ERROR",
            "internet": "ONLINE" if has_internet else "OFFLINE",
            "searxng": "ONLINE" if searxng_online else "OFFLINE",
            "calendar": gcal_mode,
            "email_hub": email_mode,
            "spotify": spotify_mode,
            "telegram": "ONLINE" if telegram_ready else "STANDBY"
        },
        "sync": {
            "pending": sync_summary,
            "internet": has_internet
        },
        "sessions": list(store.keys()) if store else ["sessio_per_defecte"]
    }

@app.get("/api/sync")
def trigger_sync():
    """Executa la sincronització de cites i correus desats fora de línia."""
    return run_full_synchronization()

@app.get("/api/dashboard")
def get_dashboard():
    """Retorna les tasques, totes les cites properes de l'agenda i correus no llegits."""
    tasques = db_get_tasks()
    # Obtenim TOTS els esdeveniments (sense filtrar només avui per poder mostrar cites de demà i pròximes)
    tots_esdeveniments = fetch_calendar_events()
    correus_no_llegits = fetch_unread_emails(limit=5)

    pendents_count = sum(1 for t in tasques if t["status"] == "pendent")
    completades_count = sum(1 for t in tasques if t["status"] == "completada")

    return {
        "today_date": datetime.now().strftime("%d/%m/%Y"),
        "tasks": tasques,
        "events": tots_esdeveniments,
        "unread_emails_count": len(correus_no_llegits),
        "unread_emails": correus_no_llegits,
        "stats": {
            "pending_tasks": pendents_count,
            "completed_tasks": completades_count,
            "total_events": len(tots_esdeveniments)
        }
    }

# --- ACCIONS DIRECTES DES DE LA UI ---
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

@app.post("/api/events/create")
def create_event_endpoint(req: CreateEventRequest):
    if not req.title.strip() or not req.start_time.strip():
        raise HTTPException(status_code=400, detail="El títol i la data/hora són obligatoris.")
    res = add_calendar_event(
        title=req.title,
        start_time=req.start_time,
        end_time=req.end_time,
        location=req.location,
        description=req.description
    )
    return {"success": True, "result": res, "message": "Cita afegida a l'agenda."}

@app.post("/api/spotify/play")
def spotify_play_endpoint(req: SpotifyPlayRequest):
    res = play_music(req.query, req.music_type)
    return res

@app.post("/api/spotify/control")
def spotify_control_endpoint(req: SpotifyControlRequest):
    res = control_playback(req.command)
    return res

# --- FITXERS ESTÀTICS I VISTA WEB ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))