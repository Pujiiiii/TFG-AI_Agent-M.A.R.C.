import os
import requests
import difflib
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from marc.core.actions import registrar_accio

@tool
def llistar_arxius(directori: str = "marc_test_dropzone") -> str:
    """
    Llista els arxius i carpetes d'un directori específic. 
    """
    try:
        arxius = os.listdir(directori)
        if not arxius:
            return "El directori està buit."
        return f"Arxius trobats al directori '{directori}': {', '.join(arxius)}"
    except Exception as e:
        return f"Error en llegir el directori: {e}"

@tool
def llegir_arxiu(ruta: str) -> str:
    """
    Llegeix el contingut d'un arxiu. 
    Sempre has d'utilitzar aquesta eina per entendre el codi font o el context d'un arxiu abans de proposar-ne modificacions.
    """
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contingut = f.read()
            if not contingut.strip():
                return f"L'arxiu {ruta} existeix però està buit."
            return contingut
    except Exception as e:
        return f"Error en llegir l'arxiu: {e}"

@tool
def crear_carpeta(ruta: str) -> str:
    """
    Crea una nova carpeta o directori al sistema.
    """
    try:
        os.makedirs(ruta, exist_ok=True)
        return f"Carpeta creada correctament a: {ruta}"
    except Exception as e:
        return f"Error en crear la carpeta: {e}"

@tool
def esborrar_arxiu(ruta: str) -> str:
    """
    Sol·licita confirmació a l'usuari per eliminar un arxiu del sistema de fitxers.
    """
    if not os.path.exists(ruta):
        return f"L'arxiu {ruta} no existeix."

    def aplicar_esborrat(data):
        os.remove(data["ruta"])
        return f"S'ha eliminat correctament l'arxiu {data['ruta']}."

    accio = registrar_accio(
        tipus="delete",
        resum=f"Eliminar l'arxiu {ruta}",
        dades={"ruta": ruta},
        funcio_execucio=aplicar_esborrat
    )
    return f"[ACCIÓ PENDENT DE CONFIRMACIÓ]\nID: {accio['action_id']}\nTipus: Eliminar fitxer\nRuta: {ruta}"

@tool
def buscar_informacio_internet(consulta: str) -> str:
    """
    Busca informació actualitzada a internet utilitzant el motor privat SearxNG.
    """
    url = "http://localhost:8080/search"
    params = {
        "q": consulta,
        "format": "json"
    }
    # Fem que sembli el navegador Google Chrome d'un ordinador Windows
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return "No s'han trobat resultats per a aquesta cerca."
            
            resum_resultats = []
            for r in results[:3]:
                titol = r.get("title", "")
                content = r.get("content", "")
                resum_resultats.append(f"- **{titol}**: {content}")
                
            return "\n".join(resum_resultats)
        else:
            return f"Error en el servidor de cerca: {response.status_code}"
    except Exception as e:
        return f"No s'ha pogut connectar amb el motor de cerca local: {e}"

@tool
def buscar_text_en_projecte(paraula_clau: str, directori_base: str = ".") -> str:
    """
    Busca una paraula clau o patró a tots els fitxers de codi d'un projecte.
    Molt útil per trobar on es defineix una funció, classe o variable a gran escala.
    """
    resultats = []
    ignorar_carpetes = {".git", "__pycache__", "venv", "env", "node_modules", ".pytest_cache"}
    
    for root, dirs, files in os.walk(directori_base):
        # Filtrem carpetes innecessàries per escalar millor
        dirs[:] = [d for d in dirs if d not in ignorar_carpetes]
        
        for file in files:
            # Només busquem en fitxers de codi/text típics
            if file.endswith((".py", ".js", ".ts", ".json", ".md", ".txt", ".html", ".css")):
                ruta_fitxer = os.path.join(root, file)
                try:
                    with open(ruta_fitxer, "r", encoding="utf-8") as f:
                        for num_linia, linia in enumerate(f, 1):
                            if paraula_clau.lower() in linia.lower():
                                resultats.append(f"{ruta_fitxer}:{num_linia} -> {linia.strip()}")
                except Exception:
                    continue
                    
    if not resultats:
        return f"No s'ha trobat cap coincidència per a '{paraula_clau}' al projecte."
        
    # Limitem a 20 resultats per no saturar el context de l'LLM
    return "\n".join(resultats[:20])

@tool
def editar_arxiu_amb_diff(ruta: str, text_a_substituir: str, text_nou: str) -> str:
    """
    Proposa un canvi quirúrgic a un fitxer mostrant un diff per a aprovació de l'usuari a la web.
    """
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contingut_actual = f.read()

        if text_a_substituir not in contingut_actual:
            return f"Error: No s'ha trobat el text exacte a substituir dins de {ruta}."

        contingut_modificat = contingut_actual.replace(text_a_substituir, text_nou)

        diff = list(difflib.unified_diff(
            contingut_actual.splitlines(keepends=True),
            contingut_modificat.splitlines(keepends=True),
            fromfile=f"a/{ruta}",
            tofile=f"b/{ruta}"
        ))
        diff_text = "".join(diff)

        def aplicar_edicio(data):
            with open(data["ruta"], "w", encoding="utf-8") as f:
                f.write(data["contingut"])
            return f"Canvis aplicats correctament a {data['ruta']}."

        accio = registrar_accio(
            tipus="diff",
            resum=f"Modificar l'arxiu {ruta}",
            dades={"ruta": ruta, "contingut": contingut_modificat, "diff": diff_text},
            funcio_execucio=aplicar_edicio
        )

        return f"[ACCIÓ PENDENT DE CONFIRMACIÓ]\nID: {accio['action_id']}\nTipus: Edició amb diff\nRuta: {ruta}\n```diff\n{diff_text}\n```"

    except Exception as e:
        return f"Error en preparar l'edició: {e}"

@tool
def visitar_pagina_web(url: str) -> str:
    """
    Visita una pàgina web concreta (URL completa) i n'extreu el text net.
    Útil per consultar articles, documentació oficial o contingut d'un enllaç.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MARC-Agent/1.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Error en accedir a la URL: Codi de resposta {res.status_code}"
        
        soup = BeautifulSoup(res.text, "html.parser")
        # Netejar scripts i estils
        for s in soup(["script", "style", "nav", "footer"]):
            s.decompose()
            
        text = soup.get_text(separator="\n", strip=True)
        # Limitem a 3500 caràcters per no desbordar el context de l'LLM
        return text[:3500] if len(text) > 3500 else text
    except Exception as e:
        return f"Error en llegir la pàgina {url}: {e}"

@tool
def descarregar_recurs_internet(url: str, nom_fitxer_desti: str) -> str:
    """
    Sol·licita permís per descarregar un fitxer des d'una URL cap al disc local.
    """
    def aplicar_descarrega(data):
        carpeta = os.path.dirname(data["desti"])
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        r = requests.get(data["url"], stream=True, timeout=20)
        with open(data["desti"], "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return f"Descarregat {data['desti']} correctament des de {data['url']}."

    accio = registrar_accio(
        tipus="download",
        resum=f"Descarregar fitxer a {nom_fitxer_desti}",
        dades={"url": url, "desti": nom_fitxer_desti},
        funcio_execucio=aplicar_descarrega
    )

    return f"[ACCIÓ PENDENT DE CONFIRMACIÓ]\nID: {accio['action_id']}\nTipus: Descàrrega\nURL: {url}\nDestí: {nom_fitxer_desti}"