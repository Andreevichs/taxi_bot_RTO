import httpx
from typing import Optional
from datetime import datetime, timedelta

_weather_cache = {"data": None, "expires": datetime.min}


async def get_minsk_weather() -> Optional[str]:
    """Получить погоду в Минске (Open-Meteo, бесплатное API) с кэшированием на 10 минут"""
    global _weather_cache

    now = datetime.now()
    if _weather_cache["expires"] > now and _weather_cache["data"]:
        return _weather_cache["data"]

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
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})
        temp = current.get("temperature_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        code = current.get("weather_code", 0)

        weather_emojis = {
            0: "☀️ Ясно",
            1: "🌤️ Преимущественно ясно",
            2: "⛅ Переменная облачность",
            3: "☁️ Пасмурно",
            45: "🌫️ Туман",
            48: "🌫️ Иней",
            51: "🌦️ Лёгкая морось",
            53: "🌧️ Морось",
            55: "🌧️ Сильная морось",
            56: "🌧️ Ледяная морось",
            57: "🌧️ Сильная ледяная морось",
            61: "🌧️ Небольшой дождь",
            63: "🌧️ Дождь",
            65: "🌧️ Сильный дождь",
            66: "🌧️ Ледяной дождь",
            67: "🌧️ Сильный ледяной дождь",
            71: "🌨️ Небольшой снег",
            73: "🌨️ Снег",
            75: "🌨️ Сильный снег",
            77: "🌨️ Снежные зёрна",
            80: "🌧️ Ливневый дождь",
            81: "🌧️ Сильный ливень",
            82: "🌧️ Очень сильный ливень",
            85: "🌨️ Снежный ливень",
            86: "🌨️ Сильный снежный ливень",
            95: "⛈️ Гроза",
            96: "⛈️ Гроза с градом",
            99: "⛈️ Сильная гроза с градом"
        }
        weather_desc = weather_emojis.get(code, "🌡️ Неизвестно")

        result = f"{weather_desc}\n🌡️ {temp}°C\n💨 Ветер {wind} м/с"

        _weather_cache = {"data": result, "expires": now + timedelta(minutes=10)}

        return result

    except Exception as e:
        if _weather_cache["data"]:
            return _weather_cache["data"] + "\n(данные могут быть устаревшими)"
        return None
