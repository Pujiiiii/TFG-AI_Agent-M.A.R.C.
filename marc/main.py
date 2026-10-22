import os
import requests
from datetime import datetime
import groq
from fastapi import FastAPI, HTTPException, UploadFile, File, Response
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
    db_delete_task,
    db_get_sync_summary,
    get_db_connection,
    db_get_all_sessions,
    db_get_session_messages,
    db_add_chat_message
)
from marc.services.sync_manager import (
    run_full_synchronization,
    check_internet_connection
)
from marc.services.calendar_service import (
    fetch_calendar_events,
    add_calendar_event,
    delete_calendar_event,
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

class UpdateTaskRequest(BaseModel):
    task_id: int
    title: str
    priority: str = "mitjana"
    due_date: str = ""
    description: str = ""

class DeleteTaskRequest(BaseModel):
    task_id: int

class CreateEventRequest(BaseModel):
    title: str
    start_time: str
    end_time: str = ""
    location: str = ""
    description: str = ""

class UpdateEventRequest(BaseModel):
    event_id: str
    calendar_id: str = "primary"
    title: str
    start_time: str
    end_time: str = ""
    location: str = ""
    description: str = ""

class DeleteEventRequest(BaseModel):
    event_id: str
    calendar_id: str = "primary"

class AdvanceWorkflowRequest(BaseModel):
    action: str
    confirmed_date: str = ""
    counter_proposal_text: str = ""

class SpotifyPlayRequest(BaseModel):
    query: str
    music_type: str = "track"

class SpotifyControlRequest(BaseModel):
    command: str

# --- ENDPOINTS CHAT I ACTIONS (HITL) ---
@app.post("/chat")
def xat(peticio: ChatRequest):
    # Persistència del missatge de l'usuari a SQLite
    try:
        from marc.core.db import db_add_chat_message
        db_add_chat_message(peticio.session_id, "user", peticio.message)
    except Exception as e:
        print(f"[DB Chat Save Error]: {e}")

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
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "RateLimit" in type(e).__name__:
            output_text = "⚠️ **Límit d'ús assolit (Rate Limit 429)**. Si us plau, espera uns segons i torna a provar-ho."
        else:
            output_text = f"⚠️ S'ha produït un error processant la petició: {err_str}"

    # Persistència de la resposta de M.A.R.C. a SQLite
    try:
        from marc.core.db import db_add_chat_message
        db_add_chat_message(peticio.session_id, "assistant", output_text)
    except Exception as e:
        print(f"[DB Chat Save Error]: {e}")

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

@app.get("/api/sessions/{session_id}/messages")
def get_session_messages_endpoint(session_id: str):
    """Retorna tots els missatges guardats d'una sessió per restaurar-los al navegador."""
    from marc.core.db import db_get_session_messages
    return db_get_session_messages(session_id)

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
        r = requests.get("http://127.0.0.1:8080", timeout=0.5)
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
        "sessions": db_get_all_sessions()
    }

@app.get("/api/sync")
def trigger_sync():
    """Executa la sincronització de cites i correus desats fora de línia, processa correus de la UdG i avalua fluxos asíncrons."""
    from marc.services.udg_email_service import process_all_pending_udg_emails
    from marc.services.workflow_engine import run_workflow_cycle
    sync_res = run_full_synchronization()
    udg_res = process_all_pending_udg_emails()
    wf_res = run_workflow_cycle()
    
    combined_msg = sync_res.get("message", "")
    if udg_res.get("processed_count", 0) > 0:
        combined_msg += f" | UdG: {udg_res['total_tasks']} tasques creades, {udg_res['total_events']} terminis programats."
    if wf_res.get("total_triggered", 0) > 0:
        combined_msg += f" | Fluxos: {wf_res['total_triggered']} automatitzacions resoltes."
    
    return {
        "online": sync_res.get("online", True),
        "status": sync_res.get("status", "online"),
        "sync": sync_res,
        "udg": udg_res,
        "workflows": wf_res,
        "message": combined_msg
    }

@app.get("/api/workflows")
def get_workflows_endpoint(status: str = None):
    """Retorna els fluxos de treball asíncrons registrats."""
    from marc.core.db import db_get_workflows
    return db_get_workflows(status=status)

@app.post("/api/workflows/run")
def run_workflows_endpoint():
    """Executa un cicle de verificació de triggers asíncrons."""
    from marc.services.workflow_engine import run_workflow_cycle
    return run_workflow_cycle()

@app.get("/api/udg/analyze")
@app.post("/api/udg/analyze")
def analyze_udg_endpoint():
    """Analitza automàticament els correus pendents de la UdG i crea les tasques i terminis oportuns."""
    from marc.services.udg_email_service import process_all_pending_udg_emails
    return process_all_pending_udg_emails()

@app.get("/api/dashboard")
def get_dashboard(limit_agenda: int = 15, limit_tasks: int = 15, force_refresh: bool = False):
    """Retorna les tasques, cites de l'agenda (amb paginació suau) i correus no llegits."""
    from marc.core.db import db_get_workflows
    tasques = db_get_tasks()
    tots_esdeveniments = fetch_calendar_events(force_refresh=force_refresh)
    correus_no_llegits = fetch_unread_emails(limit=5)
    tots_fluxos = db_get_workflows()

    pendents_count = sum(1 for t in tasques if t["status"] == "pendent")
    completades_count = sum(1 for t in tasques if t["status"] == "completada")
    total_events_count = len(tots_esdeveniments)
    total_tasks_count = len(tasques)
    active_workflows_count = sum(1 for w in tots_fluxos if w["status"] == "pending")

    return {
        "today_date": datetime.now().strftime("%d/%m/%Y"),
        "tasks": tasques[:limit_tasks],
        "all_tasks": tasques,
        "total_tasks": total_tasks_count,
        "pending_tasks": pendents_count,
        "events": tots_esdeveniments[:limit_agenda],
        "all_events": tots_esdeveniments,
        "total_events": total_events_count,
        "unread_emails_count": len(correus_no_llegits),
        "unread_emails": correus_no_llegits,
        "workflows": tots_fluxos,
        "active_workflows_count": active_workflows_count,
        "stats": {
            "pending_tasks": pendents_count,
            "completed_tasks": completades_count,
            "total_events": total_events_count,
            "active_workflows": active_workflows_count
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

@app.post("/api/tasks/update")
def update_task_endpoint(req: UpdateTaskRequest):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE tasks SET title = ?, priority = ?, due_date = ?, description = ? WHERE id = ?",
        (req.title.strip(), req.priority.strip(), req.due_date.strip() if req.due_date else None, req.description.strip(), req.task_id)
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Tasca actualitzada correctament."}

@app.post("/api/tasks/delete")
def delete_task_endpoint(req: DeleteTaskRequest):
    db_delete_task(req.task_id)
    return {"success": True, "message": "Tasca eliminada correctament."}

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

@app.post("/api/events/update")
def update_event_endpoint(req: UpdateEventRequest):
    delete_calendar_event(req.event_id, req.calendar_id)
    res = add_calendar_event(
        title=req.title,
        start_time=req.start_time,
        end_time=req.end_time,
        location=req.location,
        description=req.description
    )
    return {"success": True, "result": res, "message": "Esdeveniment actualitzat correctament."}

@app.post("/api/events/delete")
def delete_event_endpoint(req: DeleteEventRequest):
    res = delete_calendar_event(req.event_id, req.calendar_id)
    return {"success": True, "message": res}

@app.get("/api/workflows/{workflow_id}/logs")
def get_workflow_logs_endpoint(workflow_id: int):
    from marc.core.db import db_get_workflow_logs
    return db_get_workflow_logs(workflow_id)

@app.post("/api/workflows/{workflow_id}/advance")
def advance_workflow_endpoint(workflow_id: int, req: AdvanceWorkflowRequest):
    from marc.core.db import db_get_workflow, db_update_workflow, db_add_workflow_log
    from marc.services.calendar_service import add_calendar_event
    wf = db_get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Flux no trobat.")
        
    if req.action == "accept_alternative":
        date_to_use = req.confirmed_date or wf.get("context_data", {}).get("proposed_datetime", "")
        event_title = wf.get("action_config", {}).get("event_title") or wf["title"]
        add_calendar_event(event_title, date_to_use, "", wf.get("action_config", {}).get("location", "Despatx / Online"), "Acordat en negociació.")
        db_update_workflow(workflow_id, status="completed", result_summary=f"Data alternativa acceptada: {date_to_use}")
        db_add_workflow_log(workflow_id, "user_accepted_alternative", f"L'usuari ha acceptat la data {date_to_use}")
        return {"success": True, "message": f"Reunió programada el {date_to_use}."}
    elif req.action == "cancel":
        db_update_workflow(workflow_id, status="cancelled", result_summary="Cancel·lat per l'usuari.")
        db_add_workflow_log(workflow_id, "user_cancelled", "Cancel·lat des de la interfície.")
        return {"success": True, "message": "Flux cancel·lat."}
    elif req.action == "propose_counter":
        db_update_workflow(workflow_id, status="pending", context_update={"last_counter_proposal": req.counter_proposal_text}, result_summary="Nova contraproposta enviada. Esperant resposta.")
        db_add_workflow_log(workflow_id, "counter_proposal_sent", f"Nova proposta: {req.counter_proposal_text}")
        return {"success": True, "message": "Nova proposta registrada. S'espera la confirmació."}
    return {"success": False, "message": "Acció no reconeguda."}

@app.delete("/api/workflows/{workflow_id}")
def delete_workflow_endpoint(workflow_id: int):
    """Elimina un flux de treball acabat o cancel·lat definitivament."""
    from marc.core.db import db_delete_workflow
    success = db_delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Flux no trobat.")
    return {"success": True, "message": f"Flux #{workflow_id} eliminat correctament."}

@app.post("/api/spotify/play")
def spotify_play_endpoint(req: SpotifyPlayRequest):
    res = play_music(req.query, req.music_type)
    return res

@app.post("/api/spotify/control")
def spotify_control_endpoint(req: SpotifyControlRequest):
    res = control_playback(req.command)
    return res

# --- ENDPOINTS NOUS: TEMPS, MÈTRIQUES TFG, AGENDA I DOCUMENTS ---

def _background_workflow_worker():
    """Bucle en segon pla per comprovar periòdicament respostes de correu i disparadors de fluxos."""
    import time
    while True:
        try:
            from marc.services.udg_email_service import sync_imap_udg_emails
            from marc.services.workflow_engine import run_workflow_cycle
            sync_imap_udg_emails()
            run_workflow_cycle()
        except Exception:
            pass
        time.sleep(30)

@app.on_event("startup")
def startup_event():
    import threading
    from marc.services.telegram_service import start_telegram_bot_background
    start_telegram_bot_background()
    threading.Thread(target=_background_workflow_worker, daemon=True, name="WorkflowAutoWorker").start()

@app.on_event("shutdown")
def shutdown_event():
    from marc.services.telegram_service import stop_telegram_bot
    stop_telegram_bot()

@app.get("/api/weather/girona")
def get_weather_endpoint():
    """Retorna la meteorologia en viu i recomanacions per a Girona (Campus Montilivi / EPS)."""
    from marc.services.weather_service import get_girona_weather
    return get_girona_weather()

@app.get("/api/analytics/stats")
def get_analytics_stats_endpoint():
    """Retorna les mètriques i dades empíriques de funcionament per a la memòria del TFG."""
    from marc.core.db import db_get_analytics_stats
    return db_get_analytics_stats()

@app.get("/api/calendar/free-slots")
def get_free_slots_endpoint(date: str = None, duration: int = 60):
    """Retorna les franges lliures de l'agenda per a un dia determinat."""
    from marc.services.calendar_service import suggest_free_slots
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    return {"date": date, "duration": duration, "slots": suggest_free_slots(date, duration)}

@app.get("/api/documents")
def get_documents_endpoint():
    """Llista els documents i enunciats de pràctiques desats."""
    from marc.services.document_service import list_stored_documents
    return list_stored_documents()

@app.post("/api/documents/upload")
async def upload_document_endpoint(file: UploadFile = File(...), auto_analyze: bool = True):
    """Permet carregar un enunciat en PDF/TXT/MD i analitzar-lo automàticament amb IA."""
    from marc.services.document_service import DOCS_DIR, analyze_document_with_ai, format_document_analysis_markdown
    os.makedirs(DOCS_DIR, exist_ok=True)
    file_path = os.path.join(DOCS_DIR, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    analysis_text = None
    if auto_analyze:
        raw_res = analyze_document_with_ai(file_path)
        analysis_text = format_document_analysis_markdown(raw_res)
        
        # Inserció automàtica de les tasques recomanades al To-Do
        if raw_res.get("success") and isinstance(raw_res.get("analysis"), dict):
            from marc.core.db import db_add_task
            for t in raw_res["analysis"].get("recommended_tasks", []):
                try:
                    db_add_task(
                        title=t.get("title", f"Tasca extreta de {file.filename}"),
                        priority=t.get("priority", "alta"),
                        due_date=t.get("due_date"),
                        description=f"Auto-generat per l'anàlisi de document: {file.filename}"
                    )
                except Exception as e:
                    print(f"[Auto Task Add Error]: {e}")
        
    return {
        "success": True, 
        "filename": file.filename, 
        "size_bytes": len(content), 
        "analysis": analysis_text
    }

# --- ELEVENLABS TEXT-TO-SPEECH (TTS) ---
class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None

@app.post("/api/tts")
def text_to_speech_endpoint(req: TTSRequest):
    """Genera àudio d'alta fidelitat utilitzant ElevenLabs si la clau ELEVENLABS_API_KEY està configurada."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        return {"available": False, "reason": "ELEVENLABS_API_KEY no configurada al fitxer .env"}

    # Voice ID per defecte (Adam: pNInz6obpgDQGcFmaJgB, o George: JBFqnCBsd6RMkjVDRZzb)
    voice_id = req.voice_id or os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB").strip()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": req.text[:1000],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=12)
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="audio/mpeg")
        else:
            print(f"[ElevenLabs TTS Error] Status {resp.status_code}: {resp.text}")
            return {"available": False, "error": f"ElevenLabs API Error {resp.status_code}"}
    except Exception as e:
        print(f"[ElevenLabs TTS Exception]: {e}")
        return {"available": False, "error": str(e)}

@app.get("/api/tts/status")
def tts_status_endpoint():
    from dotenv import load_dotenv
    load_dotenv(override=True)
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    return {
        "elevenlabs_available": bool(api_key),
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"),
        "provider": "elevenlabs" if api_key else "browser"
    }

# --- FITXERS ESTÀTICS I VISTA WEB ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))