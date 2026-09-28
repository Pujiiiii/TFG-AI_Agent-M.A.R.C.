import os
import requests
import difflib
import subprocess
import fnmatch
from typing import Optional
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from marc.core.actions import registrar_accio
from marc.core.workspace import get_workspace

def obtenir_arrel_git(ruta_inicial: str = None) -> str:
    """Troba el directori pare que conté la carpeta .git."""
    if not ruta_inicial:
        ruta_inicial = get_workspace()
    
    ruta_actual = os.path.abspath(ruta_inicial)
    while True:
        if os.path.exists(os.path.join(ruta_actual, ".git")):
            return ruta_actual
        pare = os.path.dirname(ruta_actual)
        if pare == ruta_actual:
            return os.path.abspath(get_workspace())
        ruta_actual = pare

def resoldre_ruta_fitxer(nom_o_ruta: str, ws: Optional[str] = None) -> str:
    """Cerca recursivament el fitxer a l'arbre si la ruta directa no existeix."""
    if ws is None:
        ws = get_workspace()

    nom_net = nom_o_ruta.strip().strip("'\"")
    if not nom_net:
        return nom_o_ruta

    ruta_directa = os.path.join(ws, nom_net)
    if os.path.exists(ruta_directa):
        return nom_net

    nom_objectiu = os.path.basename(nom_net).lower()
    ignorar = {".git", "__pycache__", "venv", "env", "node_modules", ".pytest_cache"}

    for arrel, directoris, fitxers in os.walk(ws):
        directoris[:] = [d for d in directoris if d.lower() not in ignorar]
        for f in fitxers:
            if f.lower() == nom_objectiu:
                ruta_completa = os.path.join(arrel, f)
                return os.path.relpath(ruta_completa, ws).replace("\\", "/")

    return nom_net

@tool
def llistar_arxius(directori: str = None) -> str:
    """
    Llista els arxius i carpetes del directori especificat o de l'espai de treball actual si no s'indica cap ruta.
    """
    target = directori if directori and directori.strip() else get_workspace()
    try:
        arxius = os.listdir(target)
        if not arxius:
            return f"El directori '{target}' està buit."
        return f"Arxius trobats a '{target}': {', '.join(arxius)}"
    except Exception as e:
        return f"Error en llegir el directori: {e}"

@tool
def llegir_arxiu(ruta: str) -> str:
    """Llegeix el contingut d'un arxiu de text. Si no es proporciona la ruta completa, es busca automàticament."""
    ws = get_workspace()
    ruta_real = resoldre_ruta_fitxer(ruta, ws)
    ruta_completa = os.path.join(ws, ruta_real)

    if not os.path.exists(ruta_completa):
        return f"Error: L'arxiu '{ruta}' no existeix a l'espai de treball."
    try:
        with open(ruta_completa, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error en llegir l'arxiu: {str(e)}"

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
def editar_arxiu_amb_diff(ruta: str, contingut_nou: str) -> str:
    """Proposa canvis a un arxiu mitjançant una revisió diff abans d'escriure a disc. Resol la ruta si només es dóna el nom."""
    ws = get_workspace()
    ruta_real = resoldre_ruta_fitxer(ruta, ws)
    ruta_completa = os.path.join(ws, ruta_real)

    contingut_antic = ""
    if os.path.exists(ruta_completa):
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                contingut_antic = f.read()
        except Exception as e:
            return f"Error en llegir l'arxiu original: {str(e)}"

    def executar_edicio(*args, **kwargs):
        os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contingut_nou)
        return f"Fitxer '{ruta_real}' desat correctament."

    aid = registrar_accio(
        tipus="file_diff",
        resum=f"Modificació del fitxer: {ruta_real}",
        dades={
            "files": [{
                "ruta": ruta_real,
                "contingut_antic": contingut_antic,
                "contingut_nou": contingut_nou
            }]
        },
        funcio_execucio=executar_edicio
    )
    return f"[ACCIÓ PENDENT - ID: {aid}] S'ha proposat una edició per a '{ruta_real}'. L'usuari l'ha de revisar i confirmar."

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

@tool
def executar_script_o_comanda(comanda: str) -> str:
    """
    Executa un script o ordre del sistema (ex: 'python script.py', 'pip install ...').
    SEMPRE sol·licita aprovació interactiva a l'usuari abans d'executar-se.
    """
    def aplicar_execucio(data):
        cmd = data["comanda"]
        # Executem capturant sortida estàndard i errors
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        sortida = proc.stdout if proc.stdout else "(Sense sortida estàndard)"
        errors = f"\nErrors:\n{proc.stderr}" if proc.stderr else ""
        return f"Codi de retorn: {proc.returncode}\nSortida:\n{sortida}{errors}"

    accio = registrar_accio(
        tipus="exec",
        resum=f"Executar ordre: `{comanda}`",
        dades={"comanda": comanda},
        funcio_execucio=aplicar_execucio
    )
    return f"S'ha preparat l'execució de la comanda: `{comanda}` (ID acció: {accio['action_id']}). Esperant aprovació."

@tool
def gestio_git(comanda: str, parametres: str = "") -> str:
    """
    Gestiona el repositori Git del projecte.
    
    Comandes de lectura:
      - 'status': Estat dels fitxers.
      - 'log': Historial de commits.
      - 'diff': Diferències pendents.
      - 'branch': Llista branques.
      
    Comandes d'escriptura (requereixen confirmació):
      - 'add': Afegeix fitxers a staging (resol automàticament noms aïllats).
      - 'commit': Fa el commit (parametres: missatge, SENSE -m).
      - 'push': Puja al remot.
      - 'commit_and_push': Fa commit i push de cop.
      - 'reset': Treu fitxers de staging.
      - 'checkout': Canvia de branca.
    """
    git_root = obtenir_arrel_git()
    comanda = comanda.strip().lower()
    parametres = parametres.strip()

    # Comandes de lectura immediata
    if comanda in ["status", "log", "diff", "branch"]:
        cmd = ["git"]
        if comanda == "status":
            cmd += ["status", "-s"]
        elif comanda == "log":
            n = parametres if parametres.isdigit() else "5"
            cmd += ["log", f"-n{n}", "--oneline", "--decorate"]
        elif comanda == "diff":
            cmd += ["diff"]
            if parametres:
                cmd.extend(parametres.split())
        elif comanda == "branch":
            cmd += ["branch", "-a"]

        try:
            res = subprocess.run(cmd, cwd=git_root, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                return f"Error executant 'git {comanda}': {res.stderr.strip()}"
            return res.stdout.strip() or f"La comanda 'git {comanda}' s'ha completat sense canvis."
        except Exception as e:
            return f"Error en executar git: {str(e)}"

    # Comandes d'escriptura (Human-in-the-Loop)
    elif comanda in ["commit", "push", "commit_and_push", "checkout", "add", "reset"]:
        if comanda == "commit":
            if not parametres:
                return "Error: Has d'indicar un missatge per al commit."
            msg_net = parametres.removeprefix("-m ").strip("'\"")
            comanda_shell = f'git commit -m "{msg_net}"'
            resum = f"Fer commit: '{msg_net}'"

        elif comanda == "push":
            target = f" {parametres}" if parametres else ""
            comanda_shell = f"git push{target}"
            resum = f"Pujar al remot: git push{target}"

        elif comanda == "commit_and_push":
            if not parametres:
                return "Error: Has d'indicar un missatge per al commit."
            msg_net = parametres.removeprefix("-m ").strip("'\"")
            comanda_shell = f'git commit -m "{msg_net}" && git push'
            resum = f"Fer commit i pujar al remot: '{msg_net}'"

        elif comanda == "checkout":
            comanda_shell = f"git checkout {parametres}"
            resum = f"Canviar branca: {parametres}"

        elif comanda == "add":
            target = parametres if parametres else "."
            if target != ".":
                parts = [p.strip().strip("'\"") for p in target.split() if p.strip()]
                # Resolem cada fitxer respecte a l'arrel real de Git
                targets_resolts = [resoldre_ruta_fitxer(p, git_root) for p in parts]
                target = " ".join(targets_resolts)
            comanda_shell = f"git add {target}"
            resum = f"Afegir fitxers a staging: {target}"

        elif comanda == "reset":
            target = parametres if parametres else "."
            if target != ".":
                parts = [p.strip().strip("'\"") for p in target.split() if p.strip()]
                targets_resolts = [resoldre_ruta_fitxer(p, git_root) for p in parts]
                target = " ".join(targets_resolts)
            comanda_shell = f"git reset {target}"
            resum = f"Treure fitxers de staging: {target}"

        def executar_ordre_git(*args, **kwargs):
            exec_res = subprocess.run(
                comanda_shell,
                shell=True,
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=45
            )
            if exec_res.returncode != 0:
                detall = exec_res.stderr.strip() or exec_res.stdout.strip()
                raise RuntimeError(detall or f"Error executant: {comanda_shell}")
            return exec_res.stdout.strip() or f"Ordre executada correctament: {comanda_shell}"

        aid = registrar_accio(
            tipus="exec",
            resum=resum,
            dades={"comanda": comanda_shell},
            funcio_execucio=executar_ordre_git
        )
        return f"[ACCIÓ PENDENT - ID: {aid}] S'ha sol·licitat l'execució de '{comanda_shell}'. Confirma des de la interfície."

    return f"Comanda Git '{comanda}' no reconeguda."

@tool
def buscar_arxiu_per_nom(patro: str) -> str:
    """
    Cerca fitxers o carpetes pel seu nom o patró dins de l'espai de treball (ex: 'agent.py', 'tools.py', '*.json').
    Útil per localitzar la ruta exacta d'un arxiu abans de llegir-lo, editar-lo o fer-ne commit.
    """
    ws = get_workspace()
    ignorar = {".git", "__pycache__", "venv", "env", "node_modules", ".pytest_cache"}
    coincidencies = []

    patro_net = patro.strip().strip("'\"").lower()
    te_wildcard = any(c in patro_net for c in ["*", "?", "["])

    for arrel, directoris, fitxers in os.walk(ws):
        directoris[:] = [d for d in directoris if d.lower() not in ignorar]
        
        # Comprovem tant fitxers com carpetes
        for nom in fitxers:
            nom_low = nom.lower()
            if te_wildcard:
                match = fnmatch.fnmatch(nom_low, patro_net)
            else:
                match = (nom_low == patro_net) or (patro_net in nom_low)
            
            if match:
                ruta_rel = os.path.relpath(os.path.join(arrel, nom), ws).replace("\\", "/")
                coincidencies.append(ruta_rel)

    if not coincidencies:
        return f"No s'ha trobat cap fitxer o carpeta que coincideixi amb '{patro}'."

    return "Arxius trobats:\n- " + "\n- ".join(coincidencies[:30])