import os
import sys
import urllib.parse
import subprocess
import ctypes

def is_spotify_api_configured() -> bool:
    return bool(os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"))

def get_spotipy_client():
    if not is_spotify_api_configured():
        return None
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
        
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=True
        ))
        return sp
    except Exception as e:
        print(f"[Spotify Service] Error inicialitzant Spotipy: {e}")
        return None

def send_windows_media_key(key_code: int):
    """Envia una pulsació de tecla multimèdia nativa de Windows (Play/Pause, Següent, etc.)."""
    if sys.platform == "win32":
        try:
            # 0xB3 = VK_MEDIA_PLAY_PAUSE, 0xB0 = VK_MEDIA_NEXT_TRACK, 0xB1 = VK_MEDIA_PREV_TRACK
            ctypes.windll.user32.keybd_event(key_code, 0, 0, 0) # Key Down
            ctypes.windll.user32.keybd_event(key_code, 0, 2, 0) # Key Up
            return True
        except Exception:
            return False
    return False

def play_music(query: str, music_type: str = "track") -> dict:
    """
    Cerca i posa en marxa una cançó, àlbum o artista a Spotify.
    Si Spotipy està configurat i hi ha un dispositiu actiu, reprodueix directament.
    En cas contrari, obre l'aplicació nativa de Spotify a Windows amb la cerca a punt.
    """
    query_clean = query.strip()
    sp = get_spotipy_client()
    
    if sp:
        try:
            results = sp.search(q=query_clean, type=music_type, limit=1)
            items = results.get(f"{music_type}s", {}).get("items", [])
            if items:
                item = items[0]
                item_name = item.get("name")
                item_uri = item.get("uri")
                artist_name = item.get("artists", [{}])[0].get("name", "") if "artists" in item else ""
                
                # Intentem enviar l'ordre de reproducció al dispositiu actiu
                try:
                    sp.start_playback(uris=[item_uri] if music_type == "track" else None, context_uri=item_uri if music_type != "track" else None)
                    return {
                        "success": True,
                        "mode": "spotipy_api",
                        "title": item_name,
                        "artist": artist_name,
                        "message": f"🎵 Reproduint ara a Spotify: **{item_name}** - {artist_name}"
                    }
                except Exception as playback_err:
                    print(f"[Spotipy] Dispositiu no actiu, obrint protocol local: {playback_err}")
        except Exception as e:
            print(f"[Spotify API Error]: {e}")

    # Fallback zero-config: Llançament directe a l'aplicació Spotify de Windows o navegador
    encoded = urllib.parse.quote(query_clean)
    if sys.platform == "win32":
        try:
            # Obre directament l'aplicació d'escriptori de Spotify
            subprocess.run(["cmd", "/c", "start", f"spotify:search:{query_clean}"], shell=False)
            return {
                "success": True,
                "mode": "windows_app",
                "title": query_clean,
                "message": f"🎧 S'ha obert Spotify cercant i preparant la reproducció de: **'{query_clean}'**."
            }
        except Exception:
            pass

    # Fallback navegador web
    web_url = f"https://open.spotify.com/search/{encoded}"
    import webbrowser
    webbrowser.open(web_url)
    return {
        "success": True,
        "mode": "web_browser",
        "title": query_clean,
        "message": f"🌐 S'ha obert Spotify Web per a: **'{query_clean}'** ({web_url})."
    }

def control_playback(command: str) -> dict:
    """
    Controla la reproducció de música (pausa, reprendre, següent, anterior).
    """
    cmd = command.lower().strip()
    sp = get_spotipy_client()
    
    if sp:
        try:
            if cmd in ["pause", "pausa", "aturar", "stop"]:
                sp.pause_playback()
                return {"success": True, "message": "⏸️ Reproducció pausada a Spotify."}
            elif cmd in ["play", "resume", "reprendre", "reproduir"]:
                sp.start_playback()
                return {"success": True, "message": "▶️ Reproducció represa a Spotify."}
            elif cmd in ["next", "seguent", "següent", "passar"]:
                sp.next_track()
                return {"success": True, "message": "⏭️ Saltant a la següent pista."}
            elif cmd in ["prev", "previous", "anterior"]:
                sp.previous_track()
                return {"success": True, "message": "⏮️ Tornant a la pista anterior."}
        except Exception as e:
            print(f"[Spotipy Control Error]: {e}")

    # Control per tecles multimèdia de Windows
    if sys.platform == "win32":
        if cmd in ["pause", "pausa", "play", "resume", "reprendre", "aturar"]:
            send_windows_media_key(0xB3) # VK_MEDIA_PLAY_PAUSE
            return {"success": True, "message": "⏯️ Commutat Play/Pausa al sistema multimèdia de Windows."}
        elif cmd in ["next", "seguent", "següent", "passar"]:
            send_windows_media_key(0xB0) # VK_MEDIA_NEXT_TRACK
            return {"success": True, "message": "⏭️ Ordre de següent pista enviada a Windows."}
        elif cmd in ["prev", "previous", "anterior"]:
            send_windows_media_key(0xB1) # VK_MEDIA_PREV_TRACK
            return {"success": True, "message": "⏮️ Ordre de pista anterior enviada a Windows."}

    return {"success": False, "message": f"Comanda '{command}' no reconeguda o no suportada."}
