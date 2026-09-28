import subprocess
import sys
from datetime import datetime

def fer_auto_commit_final():
    print("\n[M.A.R.C. Shutdown] Servidor aturat manualment (Ctrl + C). Verificant Git...")
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
        print(f"[M.A.R.C. Shutdown] Fent commit: '{missatge}'...")

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
    comanda = [
        sys.executable, "-m", "uvicorn", 
        "marc.main:app", 
        "--reload", 
        "--reload-dir", "marc", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    try:
        # Executa el servidor Uvicorn
        subprocess.run(comanda)
    except KeyboardInterrupt:
        pass
    finally:
        # S'executa ÚNICAMENT quan la sessió de terminal finalitza definitivament
        fer_auto_commit_final()