import os
import sys
import time
import signal
import subprocess
from datetime import datetime
from collections import defaultdict

def obtenir_executable_python():
    """Troba automàticament l'intèrpret de l'entorn virtual 'venv' del projecte."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_win = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    venv_unix = os.path.join(base_dir, "venv", "bin", "python")

    if os.path.exists(venv_win):
        return venv_win
    elif os.path.exists(venv_unix):
        return venv_unix
    return sys.executable

def generar_missatge_commit(status_output):
    """
    Genera un títol i descripció semàntics i intel·ligents per al commit
    en correlació directa amb els mòduls i fitxers modificats.
    """
    raw_lines = [l for l in status_output.splitlines() if l.strip()]
    if not raw_lines:
        return None, None

    # Mapeig de patrons de fitxers a mòduls i prioritat semàntica
    MODULE_MAP = [
        ('marc/static/', 'Frontend / UI', 10),
        ('marc/main.py', 'Backend API', 9),
        ('marc/core/agent.py', 'Agent IA', 8),
        ('marc/core/tools.py', 'Eines Agent', 8),
        ('marc/core/actions.py', 'Accions', 7),
        ('marc/core/db.py', 'Base de Dades', 7),
        ('workflow_engine', 'Motor de Fluxos', 7),
        ('udg_email', 'Correu UdG', 7),
        ('email_service', 'Correu Gmail', 7),
        ('calendar_service', 'Calendari', 6),
        ('spotify_service', 'Spotify', 5),
        ('telegram_service', 'Telegram', 5),
        ('document_service', 'Documents', 5),
        ('voice', 'Veu / TTS', 6),
        ('marc/services/', 'Serveis', 6),
        ('run.py', 'Launcher', 4),
        ('.gitignore', 'Configuració Git', 3),
        ('requirements.txt', 'Dependències', 3),
        ('README.md', 'Documentació', 3),
    ]

    def categoritzar(path):
        normalized = path.replace('\\', '/')
        for pattern, cat, prio in MODULE_MAP:
            if pattern in normalized:
                return cat, prio
        return 'Altres', 1

    fitxers_detall = []
    cats_count = defaultdict(int)
    cats_prio = {}

    for line in raw_lines:
        codi = line[:2].strip()
        path = line[3:].strip().replace('\\', '/')
        if ' -> ' in path:
            path = path.split(' -> ')[1]

        nom = os.path.basename(path)
        cat, prio = categoritzar(path)
        cats_count[cat] += 1
        cats_prio[cat] = prio

        accio = 'Modificat'
        if 'A' in codi or '?' in codi:
            accio = 'Afegit'
        elif 'D' in codi:
            accio = 'Eliminat'
        elif 'R' in codi:
            accio = 'Renombrat'

        fitxers_detall.append({
            'path': path,
            'nom': nom,
            'cat': cat,
            'accio': accio,
            'codi': codi
        })

    total_fitxers = len(fitxers_detall)

    # Ordenem categories per: 1) prioritat d'importància, 2) nombre de fitxers modificats
    categories_ordenades = sorted(
        cats_count.keys(),
        key=lambda c: (cats_prio.get(c, 0), cats_count[c]),
        reverse=True
    )

    # 1. GENERACIÓ DEL TÍTOL (SUBJECT)
    if total_fitxers == 1:
        f = fitxers_detall[0]
        if f['accio'] == 'Afegit':
            titol = f"{f['cat']}: afegit nou fitxer '{f['nom']}'"
        elif f['accio'] == 'Eliminat':
            titol = f"{f['cat']}: eliminat fitxer '{f['nom']}'"
        else:
            titol = f"{f['cat']}: actualització a {f['nom']}"
    elif len(categories_ordenades) == 1:
        cat = categories_ordenades[0]
        noms = [f['nom'] for f in fitxers_detall[:3]]
        extra = f" (+{total_fitxers - 3} més)" if total_fitxers > 3 else ""
        titol = f"{cat}: canvis a {', '.join(noms)}{extra}"
    elif len(categories_ordenades) == 2:
        top_cats = f"{categories_ordenades[0]} i {categories_ordenades[1]}"
        noms = [f['nom'] for f in fitxers_detall[:3]]
        extra = f" (+{total_fitxers - 3} més)" if total_fitxers > 3 else ""
        titol = f"{top_cats}: canvis a {', '.join(noms)}{extra}"
    elif len(categories_ordenades) == 3:
        top_cats = f"{categories_ordenades[0]}, {categories_ordenades[1]} i {categories_ordenades[2]}"
        noms = [f['nom'] for f in fitxers_detall[:3]]
        extra = f" (+{total_fitxers - 3} més)" if total_fitxers > 3 else ""
        titol = f"{top_cats}: canvis a {', '.join(noms)}{extra}"
    else:
        top_cats = f"{categories_ordenades[0]}, {categories_ordenades[1]} i {categories_ordenades[2]}"
        restants = len(categories_ordenades) - 3
        titol = f"Actualització de {top_cats} (+{restants} mòduls): {total_fitxers} fitxers"

    # 2. GENERACIÓ DEL COS EXTÈS (BODY)
    ara = datetime.now().strftime("%d/%m/%Y %H:%M")
    cos_linies = [
        f"Tancament automàtic de sessió M.A.R.C. ({ara})",
        "",
        f"Mòduls afectats: {', '.join(categories_ordenades)}",
        "Detall de canvis:",
    ]

    for f in fitxers_detall:
        cos_linies.append(f"  * [{f['accio']}] {f['path']} ({f['cat']})")

    # Resum de línies de codi de git diff --stat
    try:
        diff_res = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, timeout=5)
        stat_lines = [l.strip() for l in diff_res.stdout.strip().splitlines() if l.strip()]
        if stat_lines:
            cos_linies.append("")
            cos_linies.append(f"Resum de línies: {stat_lines[-1]}")
    except Exception:
        pass

    cos = "\n".join(cos_linies)
    return titol, cos

def fer_auto_commit_final():
    print("\n[M.A.R.C. Shutdown] Aturada de servidor detectada (Ctrl + C). Verificant Git...")

    # Ignorem nous Ctrl+C durant el commit i push per no interrompre ni corrompre l'índex de Git
    try:
        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    except Exception:
        original_sigint = None

    try:
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if status_res.returncode != 0:
            print("[M.A.R.C. Shutdown] ⚠️ No s'ha pogut verificar l'estat de Git.")
            return

        canvis = status_res.stdout.strip()
        if not canvis:
            print("[M.A.R.C. Shutdown] Repositori al dia. No cal fer cap commit.")
            return

        titol, cos = generar_missatge_commit(status_res.stdout)
        print(f"[M.A.R.C. Shutdown] Canvis detectats!")
        print(f"[M.A.R.C. Shutdown] Commit: \"{titol}\"")

        subprocess.run(["git", "add", "-A"], check=True, timeout=15)

        commit_cmd = ["git", "commit", "-m", titol]
        if cos:
            commit_cmd.extend(["-m", cos])

        commit_res = subprocess.run(commit_cmd, capture_output=True, text=True, timeout=15)
        if commit_res.returncode != 0:
            print(f"[M.A.R.C. Shutdown] ⚠️ Error en fer commit: {commit_res.stderr.strip()}")
            return

        print("[M.A.R.C. Shutdown] Pujant commits al remot (git push)...")
        push_res = subprocess.run(["git", "push"], capture_output=True, text=True, timeout=30)

        if push_res.returncode == 0:
            print("[M.A.R.C. Shutdown] ✓ Commit i push completats correctament!")
        else:
            print(f"[M.A.R.C. Shutdown] ⚠️ Error en fer push:\n{push_res.stderr.strip()}")
            print("[M.A.R.C. Shutdown] (Els canvis s'han desat al repositori local de forma segura).")
    except Exception as e:
        print(f"[M.A.R.C. Shutdown] ⚠️ Error en el commit de tancament: {e}")
    finally:
        if original_sigint is not None:
            try:
                signal.signal(signal.SIGINT, original_sigint)
            except Exception:
                pass

if __name__ == "__main__":
    python_exe = obtenir_executable_python()
    print(f"[M.A.R.C. Launcher] Utilitzant intèrpret: {python_exe}")

    comanda = [
        python_exe, "-m", "uvicorn", 
        "marc.main:app", 
        "--reload", 
        "--reload-dir", "marc", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]

    temps_inici = time.time()
    servidor_executat = False

    try:
        proc = subprocess.Popen(comanda)
        try:
            proc.wait()
            temps_durada = time.time() - temps_inici
            if proc.returncode != 0 and temps_durada < 2:
                print(f"\n⚠️ Error en executar el servidor (codi {proc.returncode}).")
                print("Consell: Assegura't que l'entorn virtual té instal·lades les dependències:")
                print("         .\\venv\\Scripts\\pip install -r requirements.txt")
            else:
                servidor_executat = True
        except KeyboardInterrupt:
            print("\n[M.A.R.C. Launcher] Aturada sol·licitada (Ctrl + C). Tancant servidor...")
            servidor_executat = True
            try:
                proc.wait(timeout=6)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except Exception:
                    pass
    except Exception as e:
        print(f"[M.A.R.C. Launcher] Error inesperat: {e}")
    finally:
        # Només fem commit si el servidor ha estat funcionant de debò i s'ha aturat
        if servidor_executat or (time.time() - temps_inici) > 4:
            fer_auto_commit_final()