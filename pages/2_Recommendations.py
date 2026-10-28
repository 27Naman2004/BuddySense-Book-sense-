"""
pages/2_Recommendations.py
--------------------------
Smart (rule-based) book recommendations.
"""

import streamlit as st
from db import get_collection, ping
from utils.recommendations import get_recommendations

st.set_page_config(page_title="Recommendations | BookBuddy", page_icon="✨", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background:linear-gradient(180deg,#1a1a2e,#16213e,#0f3460); }
[data-testid="stSidebar"] * { color:#e0e0e0!important; }
.stApp { background-color:#0d1117; }
.block-container { padding-top:1.5rem!important; }
h1,h2,h3 { color:#e8f0fe!important; }
p,li { color:#c9d1d9!important; }
.rec-card {
    background:linear-gradient(135deg,#1e2a45,#16213e);
    border:1px solid #2d4a7a; border-radius:10px;
    padding:14px 16px; margin-bottom:10px;
    border-left: 4px solid #4a9eff;
}
.rec-card h4 { color:#7eb8f7!important; margin:0 0 4px 0; font-size:1rem; }
.rec-card p  { color:#8fa8d0!important; margin:2px 0; font-size:0.85rem; }
.reason-tag {
    display:inline-block; background:#1a2d4a; border:1px solid #4a9eff;
    color:#4a9eff!important; padding:2px 10px; border-radius:12px;
    font-size:0.75rem; margin-top:6px;
}
.source-card {
    background:linear-gradient(135deg,#1a3a5c,#1e2a45);
    border:2px solid #4a9eff; border-radius:12px; padding:18px;
}
</style>
""", unsafe_allow_html=True)

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

st.markdown("# ✨ Smart Recommendations")
st.markdown("Select a book and discover similar titles based on genre, author, and tags.")
st.markdown("---")

if not ping():
    st.error("Cannot connect to MongoDB Atlas.")
    st.stop()

col = get_collection("books")

if col.count_documents({}) == 0:
    st.info("Database is empty. Run `python import_data.py` first.")
    st.stop()

# ── Book selector ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def get_book_titles():
    return [(d["title"], str(d["_id"]))
            for d in col.find({}, {"title": 1}).sort("title", 1).limit(2000)]

titles_ids = get_book_titles()
title_map  = {t: i for t, i in titles_ids}
titles     = [t for t, _ in titles_ids]

selected_title = st.selectbox("Choose a book to get recommendations for:", titles)

if not selected_title:
    st.stop()

from bson import ObjectId
book_id = title_map.get(selected_title)
book    = col.find_one({"_id": ObjectId(book_id)}) if book_id else None

if not book:
    st.warning("Book not found. Please refresh the page.")
    st.stop()

# ── Source book info ──────────────────────────────────────────────────────────
st.markdown("### Selected Book")
genre  = book.get("genre", "Unknown")
author = book.get("author", "Unknown")
rating = book.get("rating")
r_str  = f"{rating:.2f}" if rating else "N/A"

st.markdown(f"""
<div class="source-card">
    <h4 style="color:#7eb8f7;margin:0 0 6px 0">{book['title']}</h4>
    <p style="color:#8fa8d0;margin:2px 0"><b>Author:</b> {author}</p>
    <p style="color:#8fa8d0;margin:2px 0"><b>Genre:</b>  {genre}</p>
    <p style="color:#8fa8d0;margin:2px 0"><b>Rating:</b> {r_str} / 5.00</p>
</div>
""", unsafe_allow_html=True)

# ── How recommendations work ──────────────────────────────────────────────────
with st.expander("How do recommendations work?"):
    st.markdown("""
    BookBuddy uses **three simple rules** to find similar books:

    1. **Genre match** — Books in the same genre are recommended first.
    2. **Author match** — Other books by the same author come next.
    3. **Tag match** — Books sharing author-name tags fill any remaining slots.

    These rules are entirely transparent — no hidden algorithms or AI models.
    Each recommendation shows exactly why it was suggested.
    """)

# ── Generate recommendations ──────────────────────────────────────────────────
st.markdown("### Recommended Books")

with st.spinner("Finding recommendations..."):
    recs = get_recommendations(book, limit=6)

if not recs:
    st.info("No recommendations found for this book. The dataset may not have enough books in the same genre or by the same author.")
    st.stop()

st.markdown(f"*Found {len(recs)} recommendations*")

cols = st.columns(2)
for i, rec in enumerate(recs):
    r_title  = rec.get("title", "Unknown")
    r_author = rec.get("author", "Unknown")
    r_genre  = rec.get("genre", "Unknown")
    r_rating = rec.get("rating")
    r_r_str  = f"{r_rating:.2f}" if r_rating else "N/A"
    reason   = rec.get("reason", "Similar book")

    with cols[i % 2]:
        st.markdown(f"""
        <div class="rec-card">
            <h4>{r_title}</h4>
            <p><b>Author:</b> {r_author}</p>
            <p><b>Genre:</b>  {r_genre} &bull; <b>Rating:</b> {r_r_str}</p>
            <span class="reason-tag">&#128270; {reason}</span>
        </div>
        """, unsafe_allow_html=True)
