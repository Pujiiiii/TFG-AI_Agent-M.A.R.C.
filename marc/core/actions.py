import uuid

ACCIONS_PENDENTS = {}
ULTIMA_ACCIO_GENERADA = None

def registrar_accio(tipus: str, resum: str, dades: dict, funcio_execucio) -> dict:
    global ULTIMA_ACCIO_GENERADA
    action_id = str(uuid.uuid4())[:8]
    info = {
        "action_id": action_id,
        "type": tipus,
        "summary": resum,
        "data": dades,
        "executor": funcio_execucio
    }
    ACCIONS_PENDENTS[action_id] = info
    ULTIMA_ACCIO_GENERADA = info
    return {
        "pending": True,
        "action_id": action_id,
        "type": tipus,
        "summary": resum
    }

def consumir_ultima_accio():
    """Retorna i neteja l'última acció generada en el torn actual."""
    global ULTIMA_ACCIO_GENERADA
    accio = ULTIMA_ACCIO_GENERADA
    ULTIMA_ACCIO_GENERADA = None
    return accio

def executar_accio(action_id: str, aprovat: bool) -> dict:
    if action_id not in ACCIONS_PENDENTS:
        return {"success": False, "message": "Acció no trobada o ja processada."}
    
    accio = ACCIONS_PENDENTS.pop(action_id)
    if not aprovat:
        return {"success": True, "message": f"Acció cancel·lada: Has rebutjat '{accio['summary']}'."}
    
    try:
        missatge_exit = accio["executor"](accio["data"])
        return {"success": True, "message": missatge_exit}
    except Exception as e:
        return {"success": False, "message": f"Error executant l'acció: {e}"}