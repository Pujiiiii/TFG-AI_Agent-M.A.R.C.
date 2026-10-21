import os
import sys
import urllib.parse
import webbrowser
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

def send_windows_media_key(key_code: int) -> bool:
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
    1. Si Spotipy està configurat i hi ha un dispositiu actiu, reprodueix directament via API.
    2. En cas contrari, utilitza la comanda nativa os.startfile de Windows per obrir directament Spotify
       sense cap finestra de consola emergent (sense cmd).
    3. Si falla, obre el reproductor web a open.spotify.com.
    """
    query_clean = query.strip().strip("'\"")
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
                    print(f"[Spotipy] Dispositiu no actiu, recorrent a llançament natiu: {playback_err}")
        except Exception as e:
            print(f"[Spotify API Error]: {e}")

    # Llançament natiu a Windows via os.startfile (sense cmd.exe intermedi)
    encoded = urllib.parse.quote(query_clean)
    spotify_uri = f"spotify:search:{encoded}"

    if sys.platform == "win32" and hasattr(os, "startfile"):
        try:
            os.startfile(spotify_uri)
            return {
                "success": True,
                "mode": "windows_app",
                "title": query_clean,
                "message": f"🎧 S'ha obert Spotify preparant la reproducció de: **'{query_clean}'**."
            }
        except Exception as err_startfile:
            print(f"[Spotify startfile error]: {err_startfile}")

    # Fallback al navegador web oficial de Spotify
    web_url = f"https://open.spotify.com/search/{encoded}"
    try:
        webbrowser.open(web_url)
        return {
            "success": True,
            "mode": "web_browser",
            "title": query_clean,
            "message": f"🌐 S'ha obert Spotify Web per a: **'{query_clean}'**."
        }
    except Exception as e:
        return {
            "success": False,
            "mode": "error",
            "title": query_clean,
            "message": f"⚠️ No s'ha pogut obrir Spotify: {e}"
        }

def control_playback(command: str) -> dict:
    """Controla la reproducció de música (pausa, reprendre, següent, anterior)."""
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

    # Control natiu per tecles multimèdia de Windows (sense consola)
    if sys.platform == "win32":
        if cmd in ["pause", "pausa", "play", "resume", "reprendre", "aturar"]:
            send_windows_media_key(0xB3) # VK_MEDIA_PLAY_PAUSE
            return {"success": True, "message": "⏯️ Commutat Play/Pausa al reproductor de Windows."}
        elif cmd in ["next", "seguent", "següent", "passar"]:
            send_windows_media_key(0xB0) # VK_MEDIA_NEXT_TRACK
            return {"success": True, "message": "⏭️ Ordre de següent pista enviada a Windows."}
        elif cmd in ["prev", "previous", "anterior"]:
            send_windows_media_key(0xB1) # VK_MEDIA_PREV_TRACK
            return {"success": True, "message": "⏮️ Ordre de pista anterior enviada a Windows."}

    return {"success": False, "message": f"Comanda '{command}' no reconeguda."}
