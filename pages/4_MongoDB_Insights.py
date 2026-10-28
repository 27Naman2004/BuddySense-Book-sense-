"""
pages/4_MongoDB_Insights.py
---------------------------
Educational page demonstrating MongoDB concepts used in this project.
"""

import streamlit as st
import time
from db import get_collection, ping

st.set_page_config(page_title="MongoDB Insights | BookBuddy", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background:linear-gradient(180deg,#1a1a2e,#16213e,#0f3460); }
[data-testid="stSidebar"] * { color:#e0e0e0!important; }
.stApp { background-color:#0d1117; }
.block-container { padding-top:1.5rem!important; }
h1,h2,h3,h4 { color:#e8f0fe!important; }
p,li { color:#c9d1d9!important; }
code { background:#1e2a45!important; color:#7eb8f7!important; padding:2px 6px; border-radius:4px; }
pre  { background:#0d1117!important; }
.concept-card {
    background:linear-gradient(135deg,#1e2a45,#16213e);
    border:1px solid #2d4a7a; border-left:4px solid #4a9eff;
    border-radius:10px; padding:16px 20px; margin-bottom:16px;
}
.concept-card h4 { color:#7eb8f7!important; margin:0 0 8px 0; }
.result-box {
    background:#0d1117; border:1px solid #2d4a7a; border-radius:8px;
    padding:12px; margin-top:8px; font-family:monospace; font-size:0.85rem;
    color:#56d364;
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

st.markdown("# 📊 MongoDB Insights")
st.markdown("A live demonstration of the MongoDB concepts used in BookBuddy.")
st.markdown("---")

if not ping():
    st.error("Cannot connect to MongoDB Atlas.")
    st.stop()

col = get_collection("books")
total = col.count_documents({})

if total == 0:
    st.info("Import some books first: `python import_data.py --limit 500`")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Document Structure
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("## 1. Document Structure")
st.markdown("""
Unlike relational databases that store data in rigid rows and columns,
MongoDB stores data as **JSON-like documents**. Each document can have
different fields — perfect for a book database where some books have
descriptions and others do not.
""")

sample = col.find_one({"rating": {"$ne": None}}, {"_id": 0})
if sample:
    st.code(str(sample).replace(", '", ",\n  '"), language="python")


# ─────────────────────────────────────────────────────────────────────────────
# 2. CRUD Operations
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 2. CRUD Operations")
st.markdown("CRUD stands for **Create, Read, Update, Delete** — the four basic database operations.")

tab_c, tab_r, tab_u, tab_d = st.tabs(["Create", "Read", "Update", "Delete"])

with tab_c:
    st.markdown("**INSERT a new document:**")
    st.code("""
# Python (PyMongo)
doc = {
    "title":  "My Book",
    "author": "Test Author",
    "genre":  "Fiction",
    "rating": 4.5,
}
result = collection.insert_one(doc)
print("Inserted ID:", result.inserted_id)
    """, language="python")
    st.markdown("**MongoDB Shell equivalent:**")
    st.code('db.books.insertOne({ title: "My Book", author: "Test Author" })', language="javascript")

with tab_r:
    st.markdown("**READ documents matching a filter:**")
    st.code("""
# Find all books with rating >= 4.5
books = collection.find({"rating": {"$gte": 4.5}}).sort("rating", -1)
    """, language="python")
    st.markdown("**Live result (top 3 rated books):**")
    top3 = list(col.find({"rating": {"$ne": None}},
                          {"title": 1, "author": 1, "rating": 1, "_id": 0})
                   .sort("rating", -1).limit(3))
    for b in top3:
        st.markdown(f"""<div class="result-box">{b}</div>""", unsafe_allow_html=True)

with tab_u:
    st.markdown("**UPDATE a document:**")
    st.code("""
# Update the rating of a specific book
collection.update_one(
    {"title": "Some Book"},          # filter
    {"$set": {"rating": 4.8}}        # update
)
    """, language="python")
    st.markdown("**`$set`** replaces only the specified fields — all other fields remain unchanged.")

with tab_d:
    st.markdown("**DELETE a document:**")
    st.code("""
# Delete a specific book by its MongoDB ID
from bson import ObjectId
collection.delete_one({"_id": ObjectId("...")})
    """, language="python")
    st.warning("BookBuddy requires a confirmation checkbox before deleting — this prevents accidental loss.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Filtering & Sorting
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 3. Filtering and Sorting")
st.markdown("MongoDB supports rich query operators for flexible filtering.")

st.code("""
# Find English Fiction books rated >= 4.0, sorted best-first
collection.find(
    {
        "genre":  "English Fiction",
        "rating": {"$gte": 4.0}
    }
).sort("rating", -1).limit(10)
""", language="python")

st.markdown("**Run this query live:**")
if st.button("Execute Filter Query"):
    docs = list(col.find(
        {"genre": "English Fiction", "rating": {"$gte": 4.0}},
        {"title": 1, "author": 1, "rating": 1, "_id": 0}
    ).sort("rating", -1).limit(5))
    if docs:
        import pandas as pd
        st.dataframe(pd.DataFrame(docs), use_container_width=True)
    else:
        st.info("No English Fiction books with rating >= 4.0 found in the current dataset.")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Aggregation Pipeline
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 4. Aggregation Pipeline")
st.markdown("""
Aggregation lets MongoDB perform calculations **on the server**, so only
summary results are sent to your application — not thousands of raw records.
""")

st.code("""
pipeline = [
    {"$group": {
        "_id":        "$genre",
        "book_count": {"$sum":  1},
        "avg_rating": {"$avg": "$rating"}
    }},
    {"$sort": {"book_count": -1}},
    {"$limit": 10}
]
results = list(collection.aggregate(pipeline))
""", language="python")

if st.button("Run Aggregation"):
    pipeline = [
        {"$group": {
            "_id":        "$genre",
            "book_count": {"$sum": 1},
            "avg_rating": {"$avg": "$rating"}
        }},
        {"$sort": {"book_count": -1}},
        {"$limit": 10}
    ]
    results = list(col.aggregate(pipeline))
    import pandas as pd
    df = pd.DataFrame([{
        "Genre": r["_id"] or "Unknown",
        "Books": r["book_count"],
        "Avg Rating": f"{r['avg_rating']:.2f}" if r["avg_rating"] else "N/A"
    } for r in results])
    st.dataframe(df, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Indexes
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 5. Indexes")
st.markdown("""
An **index** is a data structure that speeds up queries on specific fields.
Without an index, MongoDB scans every document (**COLLSCAN**).
With an index, it jumps directly to matching documents (**IXSCAN**).

BookBuddy uses:
- A **unique compound index** on `(title, author)` to prevent duplicate imports.
- A **single-field index** on `genre` for fast genre filtering.
- A **single-field index** on `rating` for fast rating sorting.
""")

st.code("""
# Create a text index for full-text search on title and author
collection.create_index([("title", "text"), ("author", "text")])

# Create an index on genre
collection.create_index("genre")

# Create a unique compound index to prevent duplicate books
collection.create_index(
    [("title", 1), ("author", 1)],
    unique=True,
    name="title_author_unique"
)
""", language="python")

if st.button("Create / Verify Indexes Now"):
    from pymongo import ASCENDING, TEXT
    col.create_index([("title", TEXT), ("author", TEXT)], name="text_search")
    col.create_index("genre", name="genre_idx")
    col.create_index("rating", name="rating_idx")
    col.create_index([("title", ASCENDING), ("author", ASCENDING)],
                      unique=True, name="title_author_unique")

    indexes = list(col.list_indexes())
    st.success(f"Indexes confirmed. {len(indexes)} indexes exist on the books collection:")
    for idx in indexes:
        st.markdown(f"- **{idx['name']}**: `{dict(idx['key'])}`")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Query Performance Comparison
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 6. Query Performance")
st.markdown("""
We use MongoDB's `explain()` to inspect how a query is executed.

`executionStats.executionTimeMillis` shows actual execution time.  
`executionStats.totalDocsExamined` shows how many documents were scanned.

**Important:** With only ~10,000 documents in MongoDB Atlas (a shared cluster),
both indexed and unindexed queries may complete in under 1ms — the network
round-trip often dominates. The concepts shown here scale to millions of records.
""")

if st.button("Compare: with vs without index (explain output)"):
    try:
        # Query WITH an index (rating field is indexed after clicking button above)
        explain_result = col.find({"rating": {"$gte": 4.5}}).explain()
        exec_stats = explain_result.get("executionStats", {})
        winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})

        st.markdown("**Execution stats for `rating >= 4.5` query:**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Execution Time", f"{exec_stats.get('executionTimeMillis', 'N/A')} ms")
        col2.metric("Docs Examined",  f"{exec_stats.get('totalDocsExamined', 'N/A')}")
        col3.metric("Docs Returned",  f"{exec_stats.get('nReturned', 'N/A')}")

        stage = winning_plan.get("stage", "Unknown")
        if "IXSCAN" in str(winning_plan):
            st.success(f"Query used an INDEX (IXSCAN) -- efficient!")
        elif "COLLSCAN" in str(winning_plan):
            st.warning(f"Query used a COLLECTION SCAN (COLLSCAN) -- create the index first.")
        else:
            st.info(f"Winning plan stage: {stage}")

    except Exception as exc:
        st.error(f"Could not retrieve explain output: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Why MongoDB for BookBuddy?
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 7. Why MongoDB for BookBuddy?")
st.markdown("""
| Feature | MongoDB | Traditional SQL |
|---------|---------|-----------------|
| Schema flexibility | Documents can have different fields | All rows must match the table schema |
| Nested data | Tags stored as arrays inside the document | Requires a separate join table |
| Horizontal scaling | Built-in sharding | More complex to set up |
| Cloud hosting | Atlas free tier available | Varies |
| Python integration | PyMongo is simple and well-documented | Multiple driver options |
| Aggregation | Powerful pipeline operators | SQL GROUP BY and window functions |

For BookBuddy, the **flexible schema** is the key benefit: some books have
descriptions and cover images, others do not — MongoDB handles this naturally
without `NULL` columns spread across a rigid table.
""")
