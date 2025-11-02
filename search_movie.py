import requests, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

def search_movie(movie_name, page=1):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": API_KEY, "query": movie_name, "page": page, "language": "en-US"}
    res = requests.get(url, params=params)
    return res.json().get("results", [])

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    res = requests.get(url, params=params)
    return res.json()

def get_recommendations(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
    params = {"api_key": API_KEY, "language": "en-US"}
    res = requests.get(url, params=params)
    return res.json().get("results", [])
