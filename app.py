import os
import json
from pathlib import Path
from typing import List, Dict, Optional

import streamlit as st
from dotenv import load_dotenv

from search_movie import (
    search_movie,
    get_movie_details,
    get_recommendations,
    get_trending,
    get_popular,
    get_top_rated,
)

# -------------------------------------------------
# Setup
# -------------------------------------------------
load_dotenv()

MY_LIST_FILE = Path("my_list.json")


def load_my_list_from_disk() -> list:
    if MY_LIST_FILE.exists():
        try:
            return json.loads(MY_LIST_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def save_my_list_to_disk(mylist: list) -> None:
    try:
        MY_LIST_FILE.write_text(json.dumps(mylist), encoding="utf-8")
    except OSError:
        # If something goes wrong writing to disk, just ignore
        pass


# Helpers to modify `st.session_state.my_list` and persist immediately
def add_to_my_list(movie_id: int) -> None:
    if movie_id is None:
        return
    if movie_id not in st.session_state.my_list:
        st.session_state.my_list.append(movie_id)
        save_my_list_to_disk(st.session_state.my_list)


def remove_from_my_list(movie_id: int) -> None:
    if movie_id is None:
        return
    st.session_state.my_list = [mid for mid in st.session_state.my_list if mid != movie_id]
    save_my_list_to_disk(st.session_state.my_list)



# Helpful runtime guard: show a clear message if TMDb API key is not configured
if not os.getenv("TMDB_API_KEY"):
    st.error(
        "TMDb API key not found. Please create a `.env` with "
        "TMDB_API_KEY=your_key and restart the app."
    )
    st.stop()


def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()


# -------------------------------------------------
# Small helpers
# -------------------------------------------------
def get_poster_url(path: Optional[str]) -> str:
    if path:
        return f"https://image.tmdb.org/t/p/w500{path}"
    return (
        "https://www.themoviedb.org/assets/2/v4/logos/"
        "stacked-blue-2b2b2b9ef3c2a132.png"
    )


def get_backdrop_url(movie: Dict) -> str:
    backdrop = movie.get("backdrop_path")
    poster = movie.get("poster_path")
    if backdrop:
        return f"https://image.tmdb.org/t/p/original{backdrop}"
    if poster:
        return f"https://image.tmdb.org/t/p/original{poster}"
    return (
        "https://www.themoviedb.org/assets/2/v4/logos/"
        "stacked-blue-2b2b2b9ef3c2a132.png"
    )


def truncate(text: Optional[str], n: int = 240) -> str:
    if not text:
        return ""
    if len(text) <= n:
        return text
    return text[:n].rstrip() + "..."


def render_row_html(row_title: str, movies: List[Dict]) -> str:
    cards_html_parts = []
    for m in movies:
        if (not m.get("poster_path")) and (m.get("vote_average", 0) == 0):
            continue

        poster = get_poster_url(m.get("poster_path"))
        title = m.get("title", "Untitled")
        year = (m.get("release_date") or "")[:4]
        rating = m.get("vote_average", "N/A")
        movie_id = m.get("id")

        # if movie_id is missing, just don't make it a link
        href = f"?movie={movie_id}" if movie_id is not None else "#"

        card_html = (
            f'<a class="nm-card-link" href="{href}">'     # <-- NEW
            '<div class="nm-card">'
            '<div class="nm-card-inner">'
            f'<img src="{poster}" class="nm-card-img" alt="{title} poster"/>'
            '<div class="nm-card-info">'
            f'<div class="nm-card-title">{title}</div>'
            f'<div class="nm-card-meta">⭐ {rating} · {year}</div>'
            "</div>"
            "</div>"
            "</div>"
            "</a>"                                        # <-- NEW
        )
        cards_html_parts.append(card_html)

    cards_html = "".join(cards_html_parts)
    row_html = (
        '<section class="nm-row">'
        f'<div class="nm-row-header">{row_title}</div>'
        f'<div class="nm-row-scroll">{cards_html}</div>'
        "</section>"
    )
    return row_html



def render_modal(details: Dict, recs: List[Dict]) -> None:
    """Full‐screen modal for 'More Info'."""
    title = details.get("title", "Untitled")
    year = (details.get("release_date") or "N/A")[:4]
    rating = details.get("vote_average", "N/A")

    genres_list = details.get("genres", [])
    genres = ", ".join([g.get("name", "") for g in genres_list]) or "N/A"

    overview = details.get("overview", "No description available.")
    poster_big = get_poster_url(details.get("poster_path"))

    recs_html_block = ""
    if recs:
        recs_html_block = render_row_html("More Like This", recs[:10])

    modal_html = (
        '<div class="nm-modal-backdrop">'
        '<div class="nm-modal-card">'
        '<div class="nm-modal-left">'
        f'<img src="{poster_big}" class="nm-modal-poster" alt="{title} poster"/>'
        "</div>"
        '<div class="nm-modal-right">'
        f'<div class="nm-modal-title">{title} '
        f'<span class="nm-modal-year">({year})</span></div>'
        f'<div class="nm-modal-stats">⭐ {rating} · {genres}</div>'
        f'<div class="nm-modal-overview">{overview}</div>'
        "</div>"
        "</div>"
        f'<div class="nm-modal-recs">{recs_html_block}</div>'
        "</div>"
    )

    # Top-left back arrow (inside app)
    st.markdown('<div class="nm-modal-back-top">', unsafe_allow_html=True)
    if st.button("←", key="back_modal"):
        # Clear selection in state
        st.session_state.selected_movie_id = None
        # Remove ?movie= from the URL so browser Back also works
        # clear all query params (removes ?movie=...)
        st.query_params = {}
        safe_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Main modal card
    st.markdown(modal_html, unsafe_allow_html=True)

    # Add / Remove from My List button, aligned under description
    st.markdown('<div class="nm-modal-add">', unsafe_allow_html=True)
    movie_id = details.get("id")
    in_list = movie_id in st.session_state.my_list if movie_id is not None else False
    label = "Remove from My List" if in_list else "Add to My List"
    if st.button(label, key=f"toggle_mylist_{movie_id}"):
        if movie_id is not None:
            if in_list:
                remove_from_my_list(movie_id)
            else:
                add_to_my_list(movie_id)

            safe_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------
# Page & session setup
# -------------------------------------------------
st.set_page_config(page_title="Netflix Explorer", layout="wide")

if "my_list" not in st.session_state:
    st.session_state.my_list = load_my_list_from_disk()

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

# current page (used for simple routing/views)
if "page" not in st.session_state:
    st.session_state.page = "home"

# -------------------------------------------------
# 🔗 URL <-> state synchronisation
#    (THIS must be before `if st.session_state.selected_movie_id is not None`)
# -------------------------------------------------
qp = st.query_params

# Get movie id from ?movie= in the URL (handles str or list)
if "movie" in qp:
    raw_val = qp["movie"]
    if isinstance(raw_val, list):
        movie_from_url = raw_val[0] if raw_val else None
    else:
        movie_from_url = raw_val
else:
    movie_from_url = None

if movie_from_url:
    try:
        st.session_state.selected_movie_id = int(movie_from_url)
    except ValueError:
        st.session_state.selected_movie_id = None
else:
    # No ?movie= in URL → no modal
    st.session_state.selected_movie_id = None

# -------------------------------------------------
# Global styles
# -------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

:root {
    --bg-page: #000;
    --bg-nav: #141414;
    --accent: #E50914;
    --text-main: #fff;
    --text-dim: #b3b3b3;
    --row-gap: 1rem;
    --radius-card: 8px;
    --radius-modal: 12px;
    --font-main: 'Poppins', sans-serif;
}

body, .stApp {
    background-color: var(--bg-page);
    color: var(--text-main);
    font-family: var(--font-main);
    margin: 0;
    padding: 0;
}

/* NAVBAR */
.nm-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 64px;
    background-color: var(--bg-nav);
    display: flex;
    align-items: center;
    padding: 0 2rem;
    z-index: 1000;
    box-shadow: 0 20px 40px rgba(0,0,0,0.8);
}
.nm-logo {
    color: var(--accent);
    font-weight: 700;
    font-size: 1.4rem;
    letter-spacing: -0.02em;
    text-shadow: 0 0 20px rgba(229,9,20,0.6);
    margin-right: 2rem;
}
.nm-links {
    display: flex;
    gap: 1.2rem;
    font-size: 0.9rem;
    font-weight: 500;
}
.nm-links div {
    color: #e6e6e6;
    cursor: pointer;
}
.nm-links div:hover {
    color: var(--text-main);
    text-shadow: 0 0 10px rgba(255,255,255,0.4);
}

/* CONTENT WRAPPER */
.nm-content {
    padding-top: 64px;
    position: relative;
    z-index: 1;
}

/* HERO */
.nm-hero {
    position: relative;
    width: 100%;
    height: 55vh;
    min-height: 420px;
    max-height: 620px;
    background-size: cover;
    background-position: center center;
    display: flex;
    align-items: flex-end;
    box-shadow: 0 60px 120px rgba(0,0,0,0.9);
}
.nm-hero-gradient {
    width: 100%;
    height: 100%;
    background:
        radial-gradient(circle at 20% 30%, rgba(0,0,0,0) 0%, rgba(0,0,0,0.6) 60%),
        linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.8) 70%, rgba(0,0,0,1) 100%);
    display: flex;
    align-items: flex-end;
}
.nm-hero-inner {
    padding: 2rem 2rem 3rem 2rem;
    max-width: 60%;
    color: var(--text-main);
    text-shadow: 0 2px 12px rgba(0,0,0,0.95);
}
.nm-hero-title {
    font-size: clamp(1.8rem, 1.2vw + 1rem, 2.6rem);
    font-weight: 700;
    line-height: 1.15;
    margin: 0 0 0.6rem 0;
}
.nm-hero-desc {
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--text-dim);
    margin: 0 0 1rem 0;
}

/* ROW / CAROUSEL */
.nm-row {
    margin-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
.nm-row-header {
    color: var(--text-main);
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 8px rgba(0,0,0,0.8);
}
.nm-row-scroll {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: var(--row-gap);
    padding-bottom: 1rem;
    scrollbar-width: thin;
    scrollbar-color: var(--accent) rgba(255,255,255,0.05);
}
.nm-row-scroll::-webkit-scrollbar {
    height: 8px;
}
.nm-row-scroll::-webkit-scrollbar-thumb {
    background: var(--accent);
    border-radius: 999px;
}

/* CARD */
.nm-card {
    flex: 0 0 auto;
    width: 180px;
    border-radius: var(--radius-card);
    box-shadow: 0 30px 60px rgba(0,0,0,0.9);
    transition: all 0.25s ease;
    cursor: pointer;
    background-color: #000;
    position: relative;
}
.nm-card-inner {
    background-color: #000;
    border-radius: var(--radius-card);
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.07);
    box-shadow: 0 18px 40px rgba(0,0,0,0.75);
}
.nm-card-link {
    text-decoration: none;
    color: inherit;
    display: inline-block;
}
.nm-card:hover {
    transform: scale(1.07);
    box-shadow: 0 40px 120px rgba(229,9,20,0.6);
}
.nm-card-img {
    width: 100%;
    height: 260px;
    object-fit: cover;
    display: block;
    background-color: #111;
}
.nm-card-info {
    padding: 0.6rem 0.75rem 0.9rem 0.75rem;
    background: linear-gradient(
        180deg,
        rgba(0,0,0,0) 0%,
        rgba(0,0,0,0.7) 60%,
        rgba(0,0,0,1) 100%
    );
    min-height: 70px;
}
.nm-card-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-main);
    line-height: 1.3;
    text-shadow: 0 2px 6px rgba(0,0,0,0.9);
}
.nm-card-meta {
    color: var(--text-dim);
    font-size: 0.7rem;
    margin-top: 0.25rem;
    font-weight: 500;
}

/* MODAL */
.nm-modal-backdrop {
    background: rgba(0,0,0,0.8);
    border-radius: 12px;
    margin: 2rem auto;
    padding: 2rem 1.5rem 2.5rem 1.5rem;
    max-width: 960px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.nm-modal-card {
    width: min(900px, 90%);
    border-radius: var(--radius-modal);
    background:
        radial-gradient(circle at 20% 20%, rgba(255,255,255,0.07) 0%, rgba(0,0,0,0) 60%),
        rgba(20,20,20,0.9);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 60px 160px rgba(0,0,0,1);
    display: flex;
    flex-wrap: wrap;
    padding: 1.5rem 1.5rem 0.5rem 1.5rem;
    color: var(--text-main);
}
.nm-modal-left {
    flex: 0 0 200px;
    max-width: 200px;
    margin-right: 1.5rem;
}
.nm-modal-poster {
    width: 100%;
    border-radius: var(--radius-card);
    box-shadow: 0 30px 80px rgba(229,9,20,0.4);
    border: 1px solid rgba(255,255,255,0.15);
}
.nm-modal-right {
    flex: 1 1 auto;
    min-width: 200px;
}
.nm-modal-title {
    font-weight: 700;
    font-size: 1.3rem;
    line-height: 1.3;
    color: var(--text-main);
    text-shadow: 0 2px 8px rgba(0,0,0,0.8);
}
.nm-modal-year {
    color: var(--text-dim);
    font-weight: 500;
    font-size: 0.9rem;
}
.nm-modal-stats {
    font-size: 0.9rem;
    color: var(--text-dim);
    margin-top: 0.4rem;
    margin-bottom: 0.8rem;
}
.nm-modal-overview {
    font-size: 0.9rem;
    line-height: 1.5;
    color: #e5e5e5;
    text-shadow: 0 2px 8px rgba(0,0,0,1);
}
.nm-modal-recs {
    width: min(900px, 90%);
    margin-top: 2rem;
}

/* Back arrow container */
.nm-modal-back-top {
    width: min(900px, 90%);
    margin: 1.2rem auto 0 auto;
    display: flex;
    justify-content: flex-start;
}
.nm-modal-back-top .stButton {
    display: inline-flex;
}
.nm-modal-back-top .stButton > button {
    width: 40px;
    height: 40px;
    padding: 0 !important;
    border-radius: 999px !important;
    background: rgba(0,0,0,0.75) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    line-height: 1 !important;
}

/* Add button under description */
.nm-modal-add {
    width: min(900px, 90%);
    margin: -0.25rem auto 0 auto;
    padding: 0 1.5rem 1.5rem 1.5rem;
    display: flex;
    justify-content: flex-start;
}
.nm-modal-add .stButton {
    margin-left: 230px; /* ≈ poster width (200) + gap (30) */
}
.nm-modal-add .stButton > button {
    background: linear-gradient(135deg, #e50914, #f40612) !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}

/* Search bar */
.stTextInput > div > div > input {
    background-color: #1a1a1a !important;
    color: var(--text-main) !important;
    border-radius: 6px !important;
    border: 1px solid #333 !important;
    padding: 10px 12px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.8);
}
.stTextInput > div > div > input:focus {
    border: 1px solid var(--accent) !important;
    outline: 2px solid var(--accent) !important;
    box-shadow: 0 0 20px rgba(229,9,20,0.7) !important;
}

/* Global button style */
.stButton>button {
    background: var(--accent) !important;
    color: #fff !important;
    border: 0 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 20px 60px rgba(229,9,20,0.5) !important;
    cursor: pointer !important;
}
.stButton>button:hover {
    box-shadow: 0 30px 80px rgba(229,9,20,0.8) !important;
}
.nm-link {
    padding: 0 0.75rem;
    color: #e6e6e6;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: color 0.2s ease, border-color 0.2s ease;
    border-bottom: 2px solid transparent;
}

.nm-link:hover {
    color: #ffffff;
}

.nm-link-active {
    color: #ffffff;
    font-weight: 600;
    border-bottom-color: #E50914;
}

</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Top nav + main content wrapper
# -------------------------------------------------
# Dynamic navbar (highlights active page)
current_page = st.session_state.page  # "home" or "my_list"

nav_html = f"""
<div class="nm-nav">
  <div class="nm-logo">NETFLIX</div>
  <div class="nm-links">
    <span class="nm-link {'nm-link-active' if current_page == 'home' else ''}">
        Home
    </span>
    <span class="nm-link {'nm-link-active' if current_page == 'my_list' else ''}">
        My List
    </span>
  </div>
</div>
"""

st.markdown(nav_html, unsafe_allow_html=True)

st.markdown('<div class="nm-content">', unsafe_allow_html=True)

# -------------------------------------------------
# Search + fetch lists
# -------------------------------------------------
search_query = st.text_input("Search for a movie", value="", key="search_box")
is_searching = bool(search_query.strip())

if is_searching:
    search_results = search_movie(search_query.strip())
else:
    search_results = []

trending_list = get_trending()
popular_list = get_popular()
top_rated_list = get_top_rated()

# -------------------------------------------------
# If a movie is selected, show modal and stop drawing the rest
# (URL sync above ensures browser Back updates this)
# -------------------------------------------------
if st.session_state.selected_movie_id is not None:
    movie_id = st.session_state.selected_movie_id
    details = get_movie_details(movie_id)
    recs = get_recommendations(movie_id)

    if details:
        render_modal(details, recs)
        st.markdown("</div>", unsafe_allow_html=True)  # close nm-content
        st.stop()
    else:
        st.session_state.selected_movie_id = None

# -------------------------------------------------
# Main page (no modal open)
# -------------------------------------------------
hero_movie = None
if is_searching:
    if search_results:
        hero_movie = search_results[0]
else:
    if trending_list:
        hero_movie = trending_list[0]
    elif popular_list:
        hero_movie = popular_list[0]
    elif top_rated_list:
        hero_movie = top_rated_list[0]

if is_searching and not search_results:
    st.info("No results found.")

if is_searching and search_results:
    st.markdown(
        render_row_html("Search Results", search_results[:12]),
        unsafe_allow_html=True,
    )
    for m in search_results[:12]:
        if st.button(
            f"More Info on {m.get('title', 'Untitled')} ▶",
            key=f"open-{m['id']}",
        ):
            mid = m["id"]
            st.session_state.selected_movie_id = mid
            st.query_params = {"movie": str(mid)}
            safe_rerun()

# Show "My List" row when not searching
if (not is_searching) and st.session_state.my_list:
    saved_movies = []
    for mid in st.session_state.my_list:
        data = get_movie_details(mid)
        if data:
            saved_movies.append(data)
    if saved_movies:
        st.markdown(
            render_row_html("My List", saved_movies),
            unsafe_allow_html=True,
        )
        # Add Remove buttons beneath each poster so users can remove items directly from My List
        # Layout uses 6 columns to match the poster grid width
        remove_cols = st.columns(6)
        for i, m in enumerate(saved_movies):
            mid = m.get("id")
            if mid is None:
                continue
            with remove_cols[i % 6]:
                if st.button("Remove", key=f"remove-{mid}"):
                    # Remove and persist immediately, then rerun to refresh UI
                    remove_from_my_list(mid)
                    safe_rerun()

# (URL -> state sync earlier handles modal display when ?movie= is present)

# ----------------- PAGE ROUTING -----------------
if st.session_state.page == "my_list":
    # 3a. render My List page
    if not st.session_state.my_list:
        st.subheader("My List")
        st.write("You haven't added any movies yet.")
    else:
        # fetch details for each saved movie
        saved_movies = []
        for mid in st.session_state.my_list:
            data = get_movie_details(mid)
            if data:
                saved_movies.append(data)

        st.subheader("My List")
        st.markdown(
            render_row_html("Saved movies", saved_movies),
            unsafe_allow_html=True,
        )

        # optional: show remove buttons
        for m in saved_movies:
            if st.button(f"Remove {m.get('title','Untitled')}", key=f"remove_{m['id']}"):
                st.session_state.my_list = [
                    x for x in st.session_state.my_list if x != m["id"]
                ]
                save_my_list_to_disk(st.session_state.my_list)
                safe_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Hero section
if hero_movie:
    hero_backdrop = get_backdrop_url(hero_movie)
    hero_title = hero_movie.get("title", "Untitled")
    hero_desc = truncate(hero_movie.get("overview", ""), 240)

    hero_html = (
        '<section class="nm-hero" '
        f'style="background-image:url(\'{hero_backdrop}\');">'
        '<div class="nm-hero-gradient">'
        '<div class="nm-hero-inner">'
        f'<div class="nm-hero-title">{hero_title}</div>'
        f'<div class="nm-hero-desc">{hero_desc}</div>'
        "</div>"
        "</div>"
        "</section>"
    )

    st.markdown(hero_html, unsafe_allow_html=True)

    moreinfo_col, _ = st.columns([1, 5])
    with moreinfo_col:
        if st.button(
            f"More Info on {hero_title} ▶",
            key="hero_moreinfo",
        ):
            mid = hero_movie.get("id")
            if mid is not None:
                st.session_state.selected_movie_id = mid
                st.query_params = {"movie": str(mid)}
                safe_rerun()

# Recommendations based on hero
if hero_movie:
    recs_for_hero = get_recommendations(hero_movie.get("id"))
    if recs_for_hero:
        st.markdown(
            render_row_html(
                "Because you watched " + hero_movie.get("title", ""),
                recs_for_hero[:12],
            ),
            unsafe_allow_html=True,
        )

# Default rows when not searching
if not is_searching:
    if trending_list:
        st.markdown(
            render_row_html("Trending Now", trending_list[:12]),
            unsafe_allow_html=True,
        )
    if popular_list:
        st.markdown(
            render_row_html("Popular on Netflix", popular_list[:12]),
            unsafe_allow_html=True,
        )
    if top_rated_list:
        st.markdown(
            render_row_html("Top Rated", top_rated_list[:12]),
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)
