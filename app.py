from dotenv import load_dotenv
import os
import streamlit as st
from search_movie import get_recommendations, search_movie, get_movie_details

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

def get_poster_url(poster_path):
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    else:
        # reliable fixed-size fallback image (same aspect ratio)
        return "https://www.themoviedb.org/assets/2/v4/logos/stacked-blue-2b2b2b9ef3c2a132.png"

st.set_page_config(page_title="Netflix Movie Explorer", layout="wide")
st.title("🎬 Netflix Movie Explorer")

movie_name = st.text_input("Enter movie title:")

if movie_name:
    results = search_movie(movie_name)

    if not results:
        st.warning("No movies found.")
    else:
        if "show_limit" not in st.session_state:
            st.session_state.show_limit = 5

        cols = st.columns(5)
        selected_movie_id = None

        for i, movie in enumerate(results[:st.session_state.show_limit]):
            with cols[i % 5]:
                poster_url = get_poster_url(movie.get("poster_path"))
                st.markdown(
                    f"""
                    <div style="height: 450px; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                        <img src="{poster_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;">
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(movie["title"], key=movie["id"]):
                    selected_movie_id = movie["id"]

        if st.session_state.show_limit < len(results):
            if st.button("Show More"):
                st.session_state.show_limit += 5
                st.rerun()

        if selected_movie_id:
            details = get_movie_details(selected_movie_id)
            st.subheader(details["title"])
            st.write(f"**Release Date:** {details.get('release_date', 'N/A')}")
            st.write(f"**Rating:** ⭐ {details.get('vote_average', 'N/A')}")
            genres = [g["name"] for g in details.get("genres", [])]
            st.write("**Genres:**", ", ".join(genres) if genres else "N/A")
            st.write(f"**Overview:** {details.get('overview', 'No description available.')}")
            st.markdown("---")

            recs = get_recommendations(selected_movie_id)
            if recs:
                st.markdown("### 🎞️ Recommended for You")
                rec_cols = st.columns(5)
                for i, rec in enumerate(recs[:10]):
                    with rec_cols[i % 5]:
                        rec_poster = get_poster_url(rec.get("poster_path"))
                        st.markdown(
                            f"""
                            <div style="height: 450px; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                                <img src="{rec_poster}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;">
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.caption(f"{rec['title']} ({rec.get('release_date', 'N/A')[:4]})")
            # add back to search button
            st.markdown("---")
            if st.button("🔙 Back to Search"):
                st.session_state.seletected_movie_id = None
                st.experimental_rerun()    