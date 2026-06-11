"""
Live AQI data fetcher using WAQI (World Air Quality Index) API.
Uses physical ground stations.
"""
import time
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()

# WAQI API Token
WAQI_API_TOKEN = os.getenv("WAQI_API_TOKEN", "")

# Cache duration in seconds
LIVE_CACHE_DURATION = 1800  # 30 minutes

# In-memory cache for live AQI data
_live_cache = {}

def get_cached_live_data(cache_key: str):
    """Get data from cache if not expired."""
    if cache_key in _live_cache:
        data, timestamp = _live_cache[cache_key]
        if time.time() - timestamp < LIVE_CACHE_DURATION:
            return data
    return None

def set_live_cache(cache_key: str, data):
    """Store data in live cache."""
    _live_cache[cache_key] = (data, time.time())

def _make_cache_key(lat: float, lng: float) -> str:
    return f"live_waqi_{lat:.4f}_{lng:.4f}"

def _parse_waqi_data(data: dict) -> dict:
    """
    Parse pollutant data from a WAQI response.
    WAQI returns individual pollutants under 'iaqi' with a 'v' value.
    """
    if not data or 'iaqi' not in data:
        return None
        
    iaqi = data.get("iaqi", {})
    
    # Extract available pollutants
    pm25 = iaqi.get("pm25", {}).get("v")
    pm10 = iaqi.get("pm10", {}).get("v")
    no2 = iaqi.get("no2", {}).get("v")
    so2 = iaqi.get("so2", {}).get("v")
    co = iaqi.get("co", {}).get("v")
    o3 = iaqi.get("o3", {}).get("v")

    # If neither PM2.5 nor PM10 is available, we can't reliably calculate AQI
    if pm25 is None and pm10 is None:
        return None

    return {
        "pm25": float(pm25) if pm25 is not None else None,
        "pm10": float(pm10) if pm10 is not None else None,
        "no2": float(no2) if no2 is not None else None,
        "so2": float(so2) if so2 is not None else None,
        "co": float(co) if co is not None else None,
        "o3": float(o3) if o3 is not None else None,
        "is_precalculated_aqi": True,
        "main_aqi": float(data.get("aqi", 0)) if str(data.get("aqi", "")).isdigit() else None
    }

def fetch_live_aqi(lat: float, lng: float) -> dict:
    """Fetch live AQI pollutant data for a SINGLE city from WAQI."""
    if not WAQI_API_TOKEN:
        print("Live AQI: WAQI API token not found")
        return None

    cache_key = _make_cache_key(lat, lng)
    cached = get_cached_live_data(cache_key)
    if cached:
        return cached

    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lng}/"
        response = requests.get(
            url,
            params={"token": WAQI_API_TOKEN},
            timeout=10
        )

        if response.status_code == 200:
            result_json = response.json()
            if result_json.get("status") == "ok":
                data = result_json.get("data", {})
                parsed_data = _parse_waqi_data(data)
                
                if parsed_data:
                    set_live_cache(cache_key, parsed_data)
                    return parsed_data
            else:
                print(f"Live AQI: WAQI API returned status '{result_json.get('status')}' for ({lat}, {lng})")
        else:
            print(f"Live AQI: WAQI API HTTP {response.status_code} for ({lat}, {lng})")

    except Exception as e:
        print(f"Live AQI API error for ({lat}, {lng}): {e}")

    return None

def _fetch_worker(city_data: tuple) -> tuple:
    """Worker function for concurrent fetching."""
    index, lat, lng = city_data
    result = fetch_live_aqi(lat, lng)
    return index, result

def fetch_live_aqi_batch(cities: list) -> dict:
    """
    Fetch live AQI data for MULTIPLE cities concurrently using WAQI.
    Uses a ThreadPoolExecutor for high performance.
    """
    results = {}
    cities_to_fetch = []

    for i, city in enumerate(cities):
        lat = city.get('lat')
        lng = city.get('lng')
        if lat is None or lng is None:
            continue

        cache_key = _make_cache_key(lat, lng)
        cached = get_cached_live_data(cache_key)
        if cached:
            results[i] = cached
        else:
            cities_to_fetch.append((i, lat, lng))

    if not cities_to_fetch:
        return results

    if not WAQI_API_TOKEN:
        print("Live AQI Batch: WAQI API token not found")
        return results

    # Fetch concurrently
    # Use max 20 workers to avoid overwhelming the API too fast
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_index = {
            executor.submit(_fetch_worker, city_data): city_data[0] 
            for city_data in cities_to_fetch
        }
        
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                idx, parsed_data = future.result()
                if parsed_data:
                    results[idx] = parsed_data
            except Exception as e:
                print(f"Live AQI Batch: Exception for index {index}: {e}")

    return results
