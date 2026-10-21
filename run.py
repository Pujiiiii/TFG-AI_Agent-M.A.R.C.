import os
import sys
import time
import subprocess
from datetime import datetime

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

def fer_auto_commit_final():
    print("\n[M.A.R.C. Shutdown] Aturada de servidor detectada (Ctrl + C). Verificant Git...")
    try:
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
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

        subprocess.run(["git", "add", "-A"], check=True, timeout=15)
        subprocess.run(["git", "commit", "-m", missatge], check=True, timeout=15)

        print("[M.A.R.C. Shutdown] Pujant commits al remot (git push)...")
        push_res = subprocess.run(["git", "push"], capture_output=True, text=True, timeout=30)

        if push_res.returncode == 0:
            print("[M.A.R.C. Shutdown] ✓ Commit i push completats correctament!")
        else:
            print(f"[M.A.R.C. Shutdown] ⚠️ Error en fer push:\n{push_res.stderr.strip()}")
    except Exception as e:
        print(f"[M.A.R.C. Shutdown] ⚠️ Error en el commit de tancament: {e}")

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
        proc = subprocess.run(comanda)
        temps_durada = time.time() - temps_inici
        if proc.returncode != 0 and temps_durada < 2:
            print(f"\n⚠️ Error en executar el servidor (codi {proc.returncode}).")
            print("Consell: Assegura't que l'entorn virtual té instal·lades les dependències:")
            print("         .\\venv\\Scripts\\pip install -r requirements.txt")
        else:
            servidor_executat = True
    except KeyboardInterrupt:
        servidor_executat = True
    finally:
        # Només fem commit si el servidor ha estat funcionant de debò i s'ha aturat
        if servidor_executat or (time.time() - temps_inici) > 4:
            fer_auto_commit_final()