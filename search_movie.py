import requests, os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
API_KEY=os.getenv("TMDB_API_KEY")

def search_movie(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_name}"
    res = requests.get(url).json()
    return res["results"]

st.title("Movie Search")
movie_name = st.text_input("Enter movie title:")
if movie_name:
    results = search_movie(movie_name)

    if "results" not in results or len(results) == 0:
        st.write("No movies found.")

    else: 
        if "show_limit" not in st.session_state:
            st.session_state.show_limit = 5

            for movie in results[:st.session_state.show_limit]:
                st.write(f"{movie['title']} ({movie.get('release_date', 'N/A')[:4]}) - {movie['vote_average']}")

                if st.session_state.show_limit < len(results):
                    if st.button("Show More"):
                        st.session_state.show_limit += 5
                        st.experimental_rerun()