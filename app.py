import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="BookBuddy - Smart Book Discovery",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { color: #b0b8d0 !important; }

[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e2a45 0%, #16213e 100%);
    border: 1px solid #2d4a7a;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
[data-testid="metric-container"] label { color: #8fa8d0 !important; font-size: 0.85rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8f0fe !important; font-size: 2rem !important; font-weight: 700 !important;
}

.stApp { background-color: #0d1117; }
.block-container { padding-top: 1.5rem !important; }

h1, h2, h3 { color: #e8f0fe !important; }
p, li { color: #c9d1d9 !important; }

.section-divider {
    border: none; border-top: 1px solid #2d4a7a; margin: 1.5rem 0;
}

.book-card {
    background: linear-gradient(135deg, #1e2a45, #16213e);
    border: 1px solid #2d4a7a;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.book-card h4 { color: #7eb8f7 !important; margin: 0 0 4px 0; font-size: 1rem; }
.book-card p  { color: #8fa8d0 !important; margin: 2px 0; font-size: 0.85rem; }

.info-banner {
    background: linear-gradient(135deg, #1a2d4a, #1e3a5f);
    border-left: 4px solid #4a9eff;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 1rem 0;
    color: #c9d1d9 !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def _get_collection():
    from db import get_collection, ping
    if not ping():
        return None
    return get_collection("books")

def get_col():
    c = _get_collection()
    if c is None:
        st.error("Cannot connect to MongoDB Atlas. Check your .env and network.")
        st.stop()
    return c

@st.cache_data(ttl=60, show_spinner=False)
def load_stats():
    col = get_col()
    total = col.count_documents({})
    if total == 0:
        return None

    genre_pipeline = [
        {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    genres = list(col.aggregate(genre_pipeline))

    rating_pipeline = [
        {"$match": {"rating": {"$ne": None}}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    rating_res = list(col.aggregate(rating_pipeline))
    avg_rating = round(rating_res[0]["avg"], 2) if rating_res else None
    rated_count = rating_res[0]["count"] if rating_res else 0

    top_books = list(
        col.find(
            {"rating": {"$ne": None}},
            {"title": 1, "author": 1, "genre": 1, "rating": 1}
        ).sort("rating", -1).limit(10)
    )

    return {
        "total": total,
        "genres": genres,
        "num_genres": len([g for g in genres if g["_id"] not in (None, "Unknown")]),
        "avg_rating": avg_rating,
        "rated_count": rated_count,
        "top_books": top_books,
    }

with st.sidebar:
    st.markdown("## BookBuddy")
    st.markdown("*Smart Book Discovery System*")
    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("app.py",                      label="Dashboard")
    st.page_link("pages/1_Book_Explorer.py",     label="Book Explorer")
    st.page_link("pages/2_Recommendations.py",   label="Recommendations")
    st.page_link("pages/3_Manage_Books.py",      label="Manage Books")
    st.page_link("pages/4_MongoDB_Insights.py",  label="MongoDB Insights")
    st.markdown("---")
    st.caption("Powered by MongoDB Atlas & Streamlit")

st.markdown("# BookBuddy")
st.markdown("#### Smart Book Discovery System")
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

with st.spinner("Loading dashboard..."):
    stats = load_stats()

if stats is None:
    st.markdown("""
    <div class="info-banner">
        <h3 style="color:#4a9eff!important;margin-top:0">Database is empty</h3>
        <p>No books found in the <code>bookbuddy.books</code> collection.</p>
        <p>Run the import script to populate the database:</p>
        <pre style="background:#0d1117;padding:10px;border-radius:6px;color:#7eb8f7">
python import_data.py --limit 500</pre>
        <p>Then refresh this page.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Books",   f"{stats['total']:,}")
c2.metric("Genres",        f"{stats['num_genres']}")
c3.metric("Avg Rating",    f"{stats['avg_rating']:.2f} / 5.00" if stats['avg_rating'] else "N/A")
c4.metric("Rated Books",   f"{stats['rated_count']:,}")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

left, right = st.columns([3, 2])

with left:
    st.markdown("### Books by Genre")
    genres_df = pd.DataFrame(stats["genres"])
    genres_df.columns = ["Genre", "Count"]
    genres_df = genres_df[genres_df["Genre"].notna() & (genres_df["Genre"] != "Unknown")]

    fig_bar = px.bar(
        genres_df.head(12),
        x="Count", y="Genre",
        orientation="h",
        color="Count",
        color_continuous_scale="Blues",
        template="plotly_dark",
    )
    fig_bar.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(autorange="reversed"),
        font=dict(color="#c9d1d9"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.markdown("### Genre Distribution")
    top_genres = genres_df.head(8)
    fig_pie = px.pie(
        top_genres,
        names="Genre", values="Count",
        color_discrete_sequence=px.colors.sequential.Blues_r,
        hole=0.4,
        template="plotly_dark",
    )
    fig_pie.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(font=dict(color="#c9d1d9", size=11)),
        font=dict(color="#c9d1d9"),
    )
    fig_pie.update_traces(textfont_color="#ffffff")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

st.markdown("### Top Rated Books")

top_df = pd.DataFrame(stats["top_books"])
if not top_df.empty:
    top_df = top_df[["title", "author", "genre", "rating"]].copy()
    top_df.columns = ["Title", "Author", "Genre", "Rating"]
    top_df["Rating"] = top_df["Rating"].apply(lambda r: f"{r:.2f}" if r else "—")
    top_df.index = range(1, len(top_df) + 1)

    fig_top = go.Figure(go.Bar(
        x=[float(r) if r != "—" else 0 for r in top_df["Rating"]],
        y=top_df["Title"].apply(lambda t: t[:35] + "..." if len(t) > 35 else t),
        orientation="h",
        marker=dict(color="#4a9eff", opacity=0.85),
        text=top_df["Rating"],
        textposition="outside",
        textfont=dict(color="#c9d1d9"),
    ))
    fig_top.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        xaxis=dict(range=[3.5, 5.1], gridcolor="#2d4a7a", color="#c9d1d9"),
        yaxis=dict(autorange="reversed", color="#c9d1d9"),
        margin=dict(l=0, r=60, t=10, b=0),
        font=dict(color="#c9d1d9"),
        height=320,
    )
    st.plotly_chart(fig_top, use_container_width=True)

    with st.expander("View as table"):
        st.dataframe(top_df, use_container_width=True)
