import os
import shutil
import requests
import groq
import subprocess
import sys
import ctypes
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager
from marc.core.tools import obtenir_arrel_git
from marc.core.agent import agent_amb_historial, store
from marc.core.actions import executar_accio, consumir_ultima_accio
from marc.core.workspace import get_workspace, set_workspace

def fer_auto_commit_git():
    """Detecta canvis sense desar i fa commit i push."""
    git_root = obtenir_arrel_git()
    print("\n[M.A.R.C. Shutdown] Verificant l'estat del repositori Git...")

    try:
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        canvis = status_res.stdout.strip()
        if not canvis:
            print("[M.A.R.C. Shutdown] Repositori al dia. No cal fer cap commit.")
            return

        ara = datetime.now().strftime("%d/%m/%Y %H:%M")
        missatge = f"Canvis finals dia {ara}"
        print(f"[M.A.R.C. Shutdown] Canvis detectats. Fent commit: '{missatge}'...")

        subprocess.run(["git", "add", "-A"], cwd=git_root, check=True, timeout=15)
        subprocess.run(["git", "commit", "-m", missatge], cwd=git_root, check=True, timeout=15)

        print("[M.A.R.C. Shutdown] Pujant commits al remot (git push)...")
        push_res = subprocess.run(["git", "push"], cwd=git_root, capture_output=True, text=True, timeout=30)
        
        if push_res.returncode == 0:
            print("[M.A.R.C. Shutdown] ✓ Commit i push completats correctament!")
        else:
            print(f"[M.A.R.C. Shutdown] ⚠️ Error en fer push:\n{push_res.stderr.strip()}")

    except Exception as e:
        print(f"[M.A.R.C. Shutdown] ⚠️ No s'ha pogut completar l'auto-commit: {e}")

# Manejador exclusiu de Ctrl+C per a la consola de Windows
if sys.platform == "win32":
    CTRL_C_EVENT = 0
    CTRL_CLOSE_EVENT = 2

    def console_handler(ctrl_type):
        if ctrl_type in (CTRL_C_EVENT, CTRL_CLOSE_EVENT):
            fer_auto_commit_git()
            return False  # Permet que el procés de tancament continuï amb normalitat
        return False

    _handler_ref = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)(console_handler)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_handler_ref, True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Buit: ja no intercepta les recàrregues de fitxers (Ctrl + S)

app = FastAPI(title="M.A.R.C. API", version="1.0", lifespan=lifespan)

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

class WorkspaceRequest(BaseModel):
    path: str

class FileReadRequest(BaseModel):
    path: str

class FileSaveRequest(BaseModel):
    path: str
    content: str

class FileMoveRequest(BaseModel):
    old_path: str
    new_path: str

class FileDeleteRequest(BaseModel):
    path: str

class CreateItemRequest(BaseModel):
    path: str
    is_folder: bool = False

# --- ARBRE DE FITXERS DINÀMIC ---
def construir_arbre(ruta):
    """Construeix l'arbre de fitxers suportant rutes absolutes externes i relatives."""
    ignorar = {".git", "__pycache__", "venv", "env", "searxng", ".pytest_cache", "$RECYCLE.BIN", "System Volume Information"}
    arbre = []
    
    ruta_norm = os.path.normpath(ruta)
    if not os.path.exists(ruta_norm):
        return arbre

    try:
        elements = sorted(os.listdir(ruta_norm))
    except Exception:
        return arbre

    for el in elements:
        if el in ignorar:
            continue
        ruta_completa = os.path.join(ruta_norm, el)
        # Normalitzem sempre amb barres '/' per evitar problemes a la web
        path_net = os.path.normpath(ruta_completa).replace("\\", "/")
        
        try:
            if os.path.isdir(ruta_completa):
                arbre.append({
                    "type": "folder",
                    "name": el,
                    "path": path_net,
                    "children": construir_arbre(ruta_completa)
                })
            else:
                arbre.append({
                    "type": "file",
                    "name": el,
                    "path": path_net
                })
        except PermissionError:
            continue
    return arbre

# --- ENDPOINTS CHAT I ACTIONS ---
@app.post("/chat")
def xat(peticio: ChatRequest):
    try:
        resposta = agent_amb_historial.invoke(
            {"input": peticio.message},
            config={"configurable": {"session_id": peticio.session_id}}
        )
        output_text = resposta.get("output", "")
        if not output_text or not output_text.strip():
            output_text = "⚠️ L'assistent ha finalitzat sense generar text de resposta."
    except groq.RateLimitError:
        output_text = "⚠️ **Límit d'ús assolit (Rate Limit 429)**. Espera uns segons i torna a provar-ho."
    except Exception as e:
        output_text = f"⚠️ S'ha produït un error: {str(e)}"
    
    accio = consumir_ultima_accio()
    pending = None
    if accio:
        pending = {
            "action_id": accio["action_id"],
            "type": accio["type"],
            "summary": accio["summary"],
            "files": accio["data"].get("files", []),
            "command": accio["data"].get("comanda", "")
        }

    return {"response": output_text, "pending_action": pending}

@app.post("/api/confirm-action")
async def confirm_action_endpoint(body: ConfirmRequest):
    try:
        # Utilitzem el nom real de la funció del teu actions.py
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

# --- ENDPOINTS WORKSPACE & GESTIÓ DE FITXERS ---
@app.get("/api/system-status")
def get_system_status():
    searxng_online = False
    try:
        r = requests.get("http://localhost:8080", timeout=1)
        searxng_online = (r.status_code == 200)
    except Exception:
        searxng_online = False

    ws = get_workspace()
    return {
        "services": {
            "searxng": "ONLINE" if searxng_online else "OFFLINE",
            "llm_engine": "Groq",
            "backend": "ONLINE"
        },
        "workspace": ws,
        "file_tree": construir_arbre(ws),
        "sessions": list(store.keys()) if store else ["sessio_per_defecte"]
    }

@app.post("/api/workspace")
def canviar_workspace(req: WorkspaceRequest):
    if set_workspace(req.path):
        return {"success": True, "workspace": get_workspace()}
    raise HTTPException(status_code=400, detail="La ruta indicada no existeix o no és un directori vàlid.")

@app.post("/api/fs/read")
def llegir_fitxer(req: FileReadRequest):
    if not os.path.exists(req.path) or os.path.isdir(req.path):
        raise HTTPException(status_code=404, detail="Fitxer no trobat.")
    try:
        with open(req.path, "r", encoding="utf-8") as f:
            return {"path": req.path, "content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en llegir: {e}")

@app.post("/api/fs/save")
def desar_fitxer(req: FileSaveRequest):
    try:
        with open(req.path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"success": True, "message": f"Fitxer {req.path} desat."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en desar: {e}")

@app.post("/api/fs/move")
def moure_o_reanomenar(req: FileMoveRequest):
    old_p = os.path.normpath(req.old_path)
    new_p = os.path.normpath(req.new_path)
    
    # Si s'arrossega cap a una carpeta existent, col·loquem el fitxer a dins
    if os.path.isdir(new_p):
        nom_fitxer = os.path.basename(old_p)
        new_p = os.path.join(new_p, nom_fitxer)

    if not os.path.exists(old_p):
        raise HTTPException(status_code=404, detail="L'arxiu d'origen no existeix.")
    try:
        carpeta_desti = os.path.dirname(new_p)
        if carpeta_desti:
            os.makedirs(carpeta_desti, exist_ok=True)
        shutil.move(old_p, new_p)
        return {"success": True, "message": f"Mogut a {new_p.replace(chr(92), '/')}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en moure: {str(e)}")

@app.post("/api/fs/delete")
def esborrar_element(req: FileDeleteRequest):
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="Element no trobat.")
    try:
        if os.path.isdir(req.path):
            shutil.rmtree(req.path)
        else:
            os.remove(req.path)
        return {"success": True, "message": f"Element {req.path} eliminat."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en eliminar: {e}")

@app.post("/api/fs/create")
def crear_element(req: CreateItemRequest):
    try:
        if req.is_folder:
            os.makedirs(req.path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(req.path), exist_ok=True)
            with open(req.path, "a", encoding="utf-8"):
                pass
        return {"success": True, "message": f"Creat: {req.path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en crear: {e}")

# --- FITXERS ESTÀTICS ---
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))
