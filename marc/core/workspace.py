# marc/core/workspace.py
import os

WORKSPACE_ROOT = "marc_test_dropzone"

def get_workspace() -> str:
    global WORKSPACE_ROOT
    ruta_norm = os.path.normpath(WORKSPACE_ROOT).replace("\\", "/")
    if not os.path.exists(ruta_norm):
        os.makedirs(ruta_norm, exist_ok=True)
    return ruta_norm

def set_workspace(nou_path: str) -> bool:
    global WORKSPACE_ROOT
    if not nou_path:
        return False
    ruta_neta = os.path.normpath(nou_path.strip()).replace("\\", "/")
    if os.path.exists(ruta_neta) and os.path.isdir(ruta_neta):
        WORKSPACE_ROOT = ruta_neta
        return True
    return False