"""
Script d'autenticació inicial amb Google Calendar.
Només cal executar-lo un sol cop:
python auth_google.py
"""
import sys
import os
import subprocess

def obtenir_executable_python():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_win = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    venv_unix = os.path.join(base_dir, "venv", "bin", "python")
    if os.path.exists(venv_win):
        return venv_win
    elif os.path.exists(venv_unix):
        return venv_unix
    return sys.executable

def main():
    print("==================================================")
    print("  M.A.R.C. // Google Calendar OAuth 2.0 Setup")
    print("==================================================")
    print("\nS'obrirà el teu navegador web predeterminat...")
    print("1. Inicia sessió amb el teu compte de Google.")
    print("2. Si et surt l'avís 'Google hasn't verified this app', prem 'Advanced' (Avançat) i després 'Go to MARC Assistant (unsafe)'.")
    print("3. Concedeix els permisos de lectura i escriptura de Calendar.")
    print("--------------------------------------------------\n")

    try:
        from marc.services.calendar_service import get_google_calendar_service
        service = get_google_calendar_service()
        if service:
            print("\n✓ Autenticació completada amb èxit!")
            print("✓ S'ha generat el fitxer 'token.json'.")
            print("Ara M.A.R.C. té accés complet al teu Google Calendar real!")
        else:
            print("\n⚠️ No s'ha pogut obtenir el servei de Google Calendar.")
            print("Revisa que el teu compte de correu estigui afegit a 'Test users' a la pantalla de consentiment de Google Cloud.")
    except Exception as e:
        print(f"\n⚠️ Error durant l'autorització: {e}")

if __name__ == "__main__":
    venv_py = obtenir_executable_python()
    if os.path.abspath(sys.executable).lower() != os.path.abspath(venv_py).lower() and os.path.exists(venv_py):
        subprocess.run([venv_py, __file__] + sys.argv[1:])
        sys.exit(0)
    main()
