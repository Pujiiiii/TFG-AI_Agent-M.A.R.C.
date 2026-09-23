import os
from langchain_core.tools import tool

@tool
def llistar_arxius(directori: str = "jarvis_test_dropzone") -> str:
    """
    Llista els arxius i carpetes d'un directori específic. 
    Sempre has d'utilitzar aquesta eina quan l'usuari et pregunti quins arxius hi ha a la seva carpeta o directori.
    """
    try:
        arxius = os.listdir(directori)
        if not arxius:
            return "El directori està buit."
        return f"Arxius trobats al directori '{directori}': {', '.join(arxius)}"
    except Exception as e:
        return f"Error en llegir el directori: {e}"