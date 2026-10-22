import os
import time
import threading
import requests
from dotenv import load_dotenv

load_dotenv()

_TELEGRAM_THREAD = None
_STOP_EVENT = threading.Event()

def send_telegram_message(chat_id, text: str):
    """Envia un missatge a Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            # Reintenta sense markdown per evitar errors d'escapat
            payload.pop("parse_mode", None)
            requests.post(url, json=payload, timeout=10)
        return True
    except Exception as e:
        print(f"[Telegram Bot Send Error]: {e}")
        return False

def _transcribe_telegram_audio(bot_token: str, file_id: str) -> str:
    """Descarrega i transcriu una nota de veu de Telegram usant Google Gemini."""
    try:
        # 1. Obtenir ruta del fitxer
        info_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        r_info = requests.get(info_url, timeout=10).json()
        file_path = r_info.get("result", {}).get("file_path")
        if not file_path:
            return ""

        # 2. Descarregar àudio (.ogg)
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        audio_bytes = requests.get(download_url, timeout=20).content

        # 3. Transcriure amb Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=google_key)
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            res = client.models.generate_content(
                model=gemini_model,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                    "Transcriu exactament el que diu aquesta nota de veu en català o castellà (retorna únicament el text transcrit):"
                ]
            )
            return res.text.strip()
    except Exception as e:
        print(f"[Telegram Voice Transcription Error]: {e}")
    return ""

def _poll_telegram_updates():
    """Bucle en segon pla per rebre missatges i interactuar amb M.A.R.C."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("[Telegram Bot] TELEGRAM_BOT_TOKEN no definit. El bot bidireccional romandrà inactiu.")
        return

    print("[Telegram Bot] Bot bidireccional de M.A.R.C. iniciat correctament.")
    last_update_id = 0

    while not _STOP_EVENT.is_set():
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={last_update_id + 1}&timeout=20"
            resp = requests.get(url, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    last_update_id = max(last_update_id, update.get("update_id", 0))
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    if not chat_id:
                        continue

                    # Text directe o transcripció de veu
                    user_text = msg.get("text", "")
                    if not user_text and "voice" in msg:
                        file_id = msg["voice"].get("file_id")
                        send_telegram_message(chat_id, "🎙️ *Processant nota de veu amb M.A.R.C....*")
                        user_text = _transcribe_telegram_audio(bot_token, file_id)

                    if not user_text:
                        continue

                    # Comanda /start
                    if user_text.strip().lower() == "/start":
                        send_telegram_message(
                            chat_id,
                            "👋 **Hola! Soc en M.A.R.C.**, el teu secretari executiu i assistent personal autònom.\n\n"
                            "Pots demanar-me que consulti la teva agenda, creï tasques, revisi correus de la UdG, "
                            "posi música a Spotify o activi el mode focus. Pots escriure'm o enviar-me notes de veu!"
                        )
                        continue

                    # Processar comanda amb l'agent M.A.R.C.
                    try:
                        from marc.core.agent import agent_amb_historial
                        session_id = f"telegram_{chat_id}"
                        resposta = agent_amb_historial.invoke(
                            {"input": user_text},
                            config={"configurable": {"session_id": session_id}}
                        )
                        output = resposta.get("output", "Comanda processada.")
                        send_telegram_message(chat_id, output)
                    except Exception as ag_err:
                        send_telegram_message(chat_id, f"⚠️ Error processant petició: {ag_err}")

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            time.sleep(5)

def start_telegram_bot_background():
    """Inicia el bot en un fil de segon pla si no està corrent."""
    global _TELEGRAM_THREAD
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return
    if _TELEGRAM_THREAD and _TELEGRAM_THREAD.is_alive():
        return
    _STOP_EVENT.clear()
    _TELEGRAM_THREAD = threading.Thread(target=_poll_telegram_updates, daemon=True, name="TelegramBotThread")
    _TELEGRAM_THREAD.start()

def stop_telegram_bot():
    """Atura el bot en tancar el servidor."""
    _STOP_EVENT.set()
