import httpx
from typing import Optional

async def get_minsk_weather() -> Optional[str]:
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 53.9,
            "longitude": 27.57,
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "timezone": "Europe/Minsk"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            data = response.json()
            current = data.get("current", {})
            temp = current.get("temperature_2m", 0)
            wind = current.get("wind_speed_10m", 0)
            code = current.get("weather_code", 0)
            weather_emojis = {
                0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
                45: "🌫️", 48: "🌫️",
                51: "🌦️", 53: "🌧️", 55: "🌧️",
                61: "🌧️", 63: "🌧️", 65: "🌧️",
                71: "🌨️", 73: "🌨️", 75: "🌨️",
                95: "⛈️", 96: "⛈️", 99: "⛈️"
            }
            emoji = weather_emojis.get(code, "🌡️")
            return f"{emoji} {temp}°C, ветер {wind} м/с"
    except Exception:
        return None
