import streamlit as st
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union
from search_movie import (
    search_movie,
    get_movie_details,
    get_recommendations,
    get_trending,
    get_popular,
    get_top_rated,
)

load_dotenv()

# rerun helper
def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# small helpers
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
    """
    Build a Netflix-style row with horizontal scroll.
    IMPORTANT FIX:
    - We return a string that STARTS with <section ...> (no leading spaces/newline)
      so Streamlit doesn't treat it as a code block.
    """
    cards_html_parts = []
    for m in movies:
        poster = get_poster_url(m.get("poster_path"))
        title = m.get("title", "Untitled")
        year = (m.get("release_date") or "")[:4]
        rating = m.get("vote_average", "N/A")

        card_html = (
            '<div class="nm-card">'
            '<div class="nm-card-inner">'
            f'<img src="{poster}" class="nm-card-img" alt="{title} poster"/>'
            '<div class="nm-card-info">'
            f'<div class="nm-card-title">{title}</div>'
            f'<div class="nm-card-meta">⭐ {rating} · {year}</div>'
            "</div>"
            "</div>"
            "</div>"
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
    """
    Show fullscreen overlay for "More Info".
    Also FIXED: first char of modal_html is '<', not newline.
    """
    title = details.get("title", "Untitled")
    year = (details.get("release_date") or "N/A")[:4]
    rating = details.get("vote_average", "N/A")

    genres_list = details.get("genres", [])
    genres = ", ".join([g.get("name", "") for g in genres_list]) or "N/A"

    overview = details.get("overview", "No description available.")
    poster_big = get_poster_url(details.get("poster_path"))

    # Build recommendations row
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

    st.markdown(modal_html, unsafe_allow_html=True)

    close_col, _ = st.columns([1, 5])
    with close_col:
        if st.button("Close ✕", key="close_modal"):
            st.session_state.selected_movie_id = None
            safe_rerun()


st.set_page_config(
    page_title="Netflix Explorer",
    layout="wide",
)

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None


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

/* CONTENT WRAPPER (to sit under navbar) */
.nm-content {
    padding-top: 64px;
    position: relative;
    z-index: 1;
}

/* HERO billboard */
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

/* MODAL (More Info overlay) */
.nm-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.8);
    backdrop-filter: blur(4px);
    z-index: 2000;
    overflow-y: auto;
    padding: 5vh 0 10vh 0;
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
    padding: 1.5rem 1.5rem 1rem 1.5rem;
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

/* Search bar (override Streamlit input) */
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

/* Streamlit buttons -> Netflix-style CTA */
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
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="nm-nav">'
    '<div class="nm-logo">NETFLIX</div>'
    '<div class="nm-links">'
    "<div>Home</div>"
    "<div>TV Shows</div>"
    "<div>Movies</div>"
    "<div>My List</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)



st.markdown('<div class="nm-content">', unsafe_allow_html=True)

search_query = st.text_input("🔍 Search for a movie", value="", key="search_box")

if search_query.strip():
    search_results = search_movie(search_query.strip())
else:
    search_results = []

trending_list = get_trending()
popular_list = get_popular()
top_rated_list = get_top_rated()


hero_movie = None
if trending_list:
    hero_movie = trending_list[0]
elif popular_list:
    hero_movie = popular_list[0]
elif search_results:
    hero_movie = search_results[0]


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
        if st.button(f"More Info on {hero_title} ▶", key="hero_moreinfo"):
            st.session_state.selected_movie_id = hero_movie.get("id")
            safe_rerun()

if search_results:
    st.markdown(
        render_row_html("Search Results", search_results[:12]),
        unsafe_allow_html=True,
    )

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

if st.session_state.selected_movie_id is not None:
    movie_id = st.session_state.selected_movie_id
    details = get_movie_details(movie_id)
    recs = get_recommendations(movie_id)

    if details:
        render_modal(details, recs)
    else:
        st.session_state.selected_movie_id = None
