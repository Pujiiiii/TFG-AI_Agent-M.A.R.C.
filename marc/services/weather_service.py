import requests
from datetime import datetime

WMO_WEATHER_CODES = {
    0: "Cel completament serè ☀️",
    1: "Principalment serè 🌤️",
    2: "Parcialment ennuvolat ⛅",
    3: "Ennuvolat ☁️",
    45: "Boira 🌫️",
    48: "Boira amb gebre 🌫️",
    51: "Plugim lleuger 🌦️",
    53: "Plugim moderat 🌧️",
    55: "Plugim intens 🌧️",
    61: "Pluja feble 🌧️",
    63: "Pluja moderada 🌧️",
    65: "Pluja intensa 🌧️",
    71: "Nevada feble 🌨️",
    73: "Nevada moderada 🌨️",
    75: "Nevada forta ❄️",
    80: "Ruixats de pluja febles 🌦️",
    81: "Ruixats de pluja moderats 🌧️",
    82: "Ruixats violents ⛈️",
    95: "Tempesta elèctrica ⚡",
    96: "Tempesta amb calamarsa feble ⛈️",
    99: "Tempesta amb calamarsa forta ⛈️"
}

def get_girona_weather(date_str: str = None) -> dict:
    """
    Obté la informació meteorològica en viu per a Girona (Campus Montilivi / EPS) via Open-Meteo API.
    Totalment gratuïta i sense requerir claus d'API.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 41.9794,
        "longitude": 2.8214,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
        "timezone": "Europe/Madrid"
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            curr = data.get("current", {})
            daily = data.get("daily", {})
            
            code = curr.get("weather_code", 0)
            condicio = WMO_WEATHER_CODES.get(code, "Variable 🌤️")
            temp = curr.get("temperature_2m", 0)
            sensacio = curr.get("apparent_temperature", temp)
            pluja = curr.get("precipitation", 0)
            vent = curr.get("wind_speed_10m", 0)
            
            t_max = daily.get("temperature_2m_max", [temp])[0]
            t_min = daily.get("temperature_2m_min", [temp])[0]
            prob_pluja = daily.get("precipitation_probability_max", [0])[0]
            
            recomanacio = "⚠️ Pluja o ruixats previstos: recomanable agafar paraigua per anar a l'EPS." if prob_pluja >= 40 or pluja > 0 else "Bones condicions: sense risc important de pluja."
            
            is_rainy = (prob_pluja >= 40 or pluja > 0)
            return {
                "success": True,
                "location": "Girona (Campus Montilivi / EPS)",
                "temperature": temp,
                "temperature_c": temp,
                "apparent_temperature": sensacio,
                "condition": condicio,
                "precipitation": pluja,
                "precipitation_mm": pluja,
                "wind_speed": vent,
                "wind_speed_kmh": vent,
                "temp_max": t_max,
                "temp_max_c": t_max,
                "temp_min": t_min,
                "temp_min_c": t_min,
                "rain_probability": prob_pluja,
                "is_rainy": is_rainy,
                "rain_alert": recomanacio if is_rainy else "",
                "recommendation": recomanacio,
                "summary": f"🌡️ {temp}°C (Mín: {t_min}°C / Màx: {t_max}°C) - {condicio}. Probabilitat de pluja: {prob_pluja}%. {recomanacio}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": "No s'ha pogut carregar la informació del temps en aquest moment."
        }
