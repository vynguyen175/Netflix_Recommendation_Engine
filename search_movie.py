import os
import requests
from typing import Dict, List, Union
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY") or ""
BASE_URL = "https://api.themoviedb.org/3"


def _safe_get(url: str, params: Dict) -> Union[Dict, List]:
    if not API_KEY:
        return {}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            return {}
        return res.json()
    except requests.RequestException:
        return {}


def search_movie(query: str) -> List[Dict]:
    if not query:
        return []
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": API_KEY,
        "query": query,
        "language": "en-US",
        "page": 1,
        "include_adult": False,
    }
    data = _safe_get(url, params)
    if isinstance(data, dict):
        return data.get("results", [])
    return []


def get_movie_details(movie_id: Union[int, str]) -> Dict:
    if not movie_id:
        return {}
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    data = _safe_get(url, params)
    if isinstance(data, dict):
        return data
    return {}


def get_recommendations(movie_id: Union[int, str]) -> List[Dict]:
    if not movie_id:
        return []
    url = f"{BASE_URL}/movie/{movie_id}/recommendations"
    params = {"api_key": API_KEY, "language": "en-US", "page": 1}
    data = _safe_get(url, params)
    if isinstance(data, dict):
        return data.get("results", [])
    return []


def get_trending() -> List[Dict]:
    url = f"{BASE_URL}/trending/movie/day"
    params = {"api_key": API_KEY, "language": "en-US"}
    data = _safe_get(url, params)
    if isinstance(data, dict):
        return data.get("results", [])
    return []


def get_popular() -> List[Dict]:
    url = f"{BASE_URL}/movie/popular"
    params = {"api_key": API_KEY, "language": "en-US", "page": 1}
    data = _safe_get(url, params)
    if isinstance(data, dict):
        return data.get("results", [])
    return []


def get_top_rated() -> List[Dict]:
    url = f"{BASE_URL}/movie/top_rated"
    params = {"api_key": API_KEY, "language": "en-US", "page": 1}
    data = _safe_get(url, params)
    if isinstance(data, dict):
        return data.get("results", [])
    return []
