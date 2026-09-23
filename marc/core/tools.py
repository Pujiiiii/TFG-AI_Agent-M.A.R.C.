import os
import requests
import difflib
from langchain_core.tools import tool

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
def editar_arxiu(ruta: str, nou_contingut: str) -> str:
    """
    Modifica o crea un arxiu amb el contingut proporcionat.
    Utilitza aquesta eina sempre que l'usuari et demani escriure, modificar o refactoritzar codi.
    """
    # 1. Mostrem per la terminal l'acció que vol fer la IA
    print("\n" + "="*50)
    print(f"⚠️ ATENCIÓ: M.A.R.C. sol·licita permís per modificar l'arxiu -> {ruta}")
    print("--- NOU CONTINGUT PROPOSAT ---")
    print(nou_contingut)
    print("------------------------------")
    
    # 2. Human-in-the-Loop: Esperem l'aprovació manual de l'usuari
    confirmacio = input("Aproves aquest canvi? (s/n): ")
    
    if confirmacio.lower() == 's':
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(nou_contingut)
            return f"Operació completada: L'usuari ha aprovat els canvis a {ruta}."
        except Exception as e:
            return f"Error en escriure l'arxiu: {e}"
    else:
        # 3. Retornem la denegació a l'agent perquè sàpiga què ha passat
        return f"Operació cancel·lada: L'usuari ha DENEGAT la modificació de {ruta}."

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
    Esborra un arxiu del sistema. Utilitza aquesta eina només quan l'usuari et demani eliminar un fitxer.
    """
    print("\n" + "="*50)
    print(f"⚠️ PERILL: M.A.R.C. sol·licita permís per ESBORRAR l'arxiu -> {ruta}")
    print("="*50)
    
    confirmacio = input("Aproves aquesta eliminació? (s/n): ")
    
    if confirmacio.lower() == 's':
        try:
            os.remove(ruta)
            return f"Operació completada: L'usuari ha aprovat l'eliminació de {ruta}."
        except FileNotFoundError:
            return f"L'arxiu {ruta} no existeix."
        except Exception as e:
            return f"Error en esborrar l'arxiu: {e}"
    else:
        return f"Operació cancel·lada: L'usuari ha DENEGAT l'eliminació de {ruta}."

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
    Realitza un canvi quirúrgic (substitució de text exacte) en un arxiu existent.
    Mostra una comparació (diff) dels canvis abans de demanar l'aprovació de l'usuari.
    """
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contingut_actual = f.read()
            
        if text_a_substituir not in contingut_actual:
            return f"Error: No s'ha trobat el text exacte a substituir dins de {ruta}. Revisa el codi original amb llegir_arxiu primer."
            
        contingut_modificat = contingut_actual.replace(text_a_substituir, text_nou)
        
        diff = list(difflib.unified_diff(
            contingut_actual.splitlines(keepends=True),
            contingut_modificat.splitlines(keepends=True),
            fromfile=f"a/{ruta}",
            tofile=f"b/{ruta}"
        ))
        
        print("\n" + "="*60)
        print(f"⚠️ M.A.R.C. proposa un canvi quirúrgic a -> {ruta}")
        print("="*60)
        print("".join(diff))
        print("="*60)
        
        confirmacio = input("Aproves aquesta refactorització? (s/n): ")
        
        if confirmacio.lower() == 's':
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contingut_modificat)
            return f"Operació completada: Canvis aplicats amb èxit a {ruta}."
        else:
            return "Operació cancel·lada: L'usuari ha denegat la modificació del codi."
            
    except Exception as e:
        return f"Error en processar l'edició de l'arxiu: {e}"