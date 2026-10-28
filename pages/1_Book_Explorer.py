"""
pages/1_Book_Explorer.py
------------------------
Search and filter books using MongoDB queries.
"""

import streamlit as st
import pandas as pd
from db import get_collection, ping

st.set_page_config(page_title="Book Explorer | BookBuddy", page_icon="🔍", layout="wide")

# ── Shared CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: linear-gradient(180deg,#1a1a2e,#16213e,#0f3460); }
[data-testid="stSidebar"] * { color:#e0e0e0!important; }
.stApp { background-color:#0d1117; }
.block-container { padding-top:1.5rem!important; }
h1,h2,h3 { color:#e8f0fe!important; }
p,li { color:#c9d1d9!important; }
.book-card {
    background:linear-gradient(135deg,#1e2a45,#16213e);
    border:1px solid #2d4a7a; border-radius:10px;
    padding:14px 16px; margin-bottom:10px;
}
.book-card h4 { color:#7eb8f7!important; margin:0 0 4px 0; font-size:1rem; }
.book-card p  { color:#8fa8d0!important; margin:2px 0; font-size:0.85rem; }
.badge {
    display:inline-block; padding:2px 8px; border-radius:12px;
    font-size:0.75rem; font-weight:600; margin-right:4px;
}
.badge-genre  { background:#1a3a5c; color:#7eb8f7; }
.badge-rating { background:#1a3a2c; color:#56d364; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 BookBuddy")
    st.markdown("---")
    st.page_link("app.py",                      label="Dashboard",        icon="🏠")
    st.page_link("pages/1_Book_Explorer.py",     label="Book Explorer",    icon="🔍")
    st.page_link("pages/2_Recommendations.py",   label="Recommendations",  icon="✨")
    st.page_link("pages/3_Manage_Books.py",      label="Manage Books",     icon="📝")
    st.page_link("pages/4_MongoDB_Insights.py",  label="MongoDB Insights", icon="📊")
    st.markdown("---")
    st.caption("Powered by MongoDB Atlas & Streamlit")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🔍 Book Explorer")
st.markdown("Search and filter books from the database.")
st.markdown("---")

# ── Connection check ──────────────────────────────────────────────────────────
if not ping():
    st.error("Cannot connect to MongoDB Atlas. Check your .env file.")
    st.stop()

col = get_collection("books")
total = col.count_documents({})

if total == 0:
    st.info("The database is empty. Run `python import_data.py` to populate it first.")
    st.stop()

# ── Genre list (for filter dropdown) ─────────────────────────────────────────
@st.cache_data(ttl=120)
def get_genres():
    pipeline = [
        {"$group": {"_id": "$genre"}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"_id": 1}},
    ]
    return ["All"] + [g["_id"] for g in col.aggregate(pipeline) if g["_id"]]

genres = get_genres()

# ── Filter controls ───────────────────────────────────────────────────────────
f1, f2, f3, f4 = st.columns([3, 2, 2, 2])

with f1:
    search_text = st.text_input("Search title or author", placeholder="e.g. Harry Potter")
with f2:
    selected_genre = st.selectbox("Genre", genres)
with f3:
    min_rating = st.slider("Min rating", 0.0, 5.0, 0.0, 0.1)
with f4:
    sort_by = st.selectbox("Sort by", ["Rating (high-low)", "Rating (low-high)", "Title A-Z", "Title Z-A"])

# ── Build MongoDB query ───────────────────────────────────────────────────────
query: dict = {}

if search_text.strip():
    query["$or"] = [
        {"title":  {"$regex": search_text.strip(), "$options": "i"}},
        {"author": {"$regex": search_text.strip(), "$options": "i"}},
    ]

if selected_genre != "All":
    query["genre"] = selected_genre

if min_rating > 0.0:
    query["rating"] = {"$gte": min_rating}

sort_map = {
    "Rating (high-low)": [("rating", -1)],
    "Rating (low-high)": [("rating",  1)],
    "Title A-Z":         [("title",   1)],
    "Title Z-A":         [("title",  -1)],
}
sort_order = sort_map[sort_by]

# ── Execute query ─────────────────────────────────────────────────────────────
LIMIT = 50
with st.spinner("Searching..."):
    docs = list(
        col.find(query, {"title": 1, "author": 1, "genre": 1, "rating": 1, "year": 1, "description": 1})
           .sort(sort_order)
           .limit(LIMIT)
    )
    result_count = col.count_documents(query)

# ── Result header ─────────────────────────────────────────────────────────────
st.markdown(f"**{result_count:,} books found** (showing up to {LIMIT})")
st.markdown("---")

# ── Empty state ───────────────────────────────────────────────────────────────
if not docs:
    st.warning("No books matched your filters. Try a different search or lower the minimum rating.")
    st.stop()

# ── Book cards ────────────────────────────────────────────────────────────────
for doc in docs:
    title   = doc.get("title", "Unknown")
    author  = doc.get("author", "Unknown")
    genre   = doc.get("genre", "—")
    rating  = doc.get("rating")
    year    = doc.get("year")
    desc    = doc.get("description") or ""

    rating_str = f"{rating:.2f}" if rating is not None else "N/A"
    year_str   = str(int(year)) if year else ""

    meta = f"{author}"
    if year_str:
        meta += f" &bull; {year_str}"

    st.markdown(f"""
    <div class="book-card">
        <h4>{title}</h4>
        <p>{meta}</p>
        <span class="badge badge-genre">{genre}</span>
        <span class="badge badge-rating">&#9733; {rating_str}</span>
        {"<p style='margin-top:8px;font-size:0.82rem;color:#8fa8d0'>" + desc[:200] + ("..." if len(desc) > 200 else "") + "</p>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)

if result_count > LIMIT:
    st.caption(f"Showing first {LIMIT} of {result_count:,} results. Refine your search to see more.")
