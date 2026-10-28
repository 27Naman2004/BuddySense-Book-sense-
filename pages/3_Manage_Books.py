import streamlit as st
from db import get_collection, ping
from bson import ObjectId

st.set_page_config(page_title="Manage Books - BookBuddy", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background:linear-gradient(180deg,#1a1a2e,#16213e,#0f3460); }
[data-testid="stSidebar"] * { color:#e0e0e0!important; }
.stApp { background-color:#0d1117; }
.block-container { padding-top:1.5rem!important; }
h1,h2,h3 { color:#e8f0fe!important; }
p,li { color:#c9d1d9!important; }
.form-section {
    background:linear-gradient(135deg,#1e2a45,#16213e);
    border:1px solid #2d4a7a; border-radius:12px; padding:20px; margin:10px 0;
}
.book-row {
    background:#1e2a45; border:1px solid #2d4a7a; border-radius:8px;
    padding:10px 14px; margin-bottom:6px;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## BookBuddy")
    st.markdown("---")
    st.page_link("app.py",                      label="Dashboard")
    st.page_link("pages/1_Book_Explorer.py",     label="Book Explorer")
    st.page_link("pages/2_Recommendations.py",   label="Recommendations")
    st.page_link("pages/3_Manage_Books.py",      label="Manage Books")
    st.page_link("pages/4_MongoDB_Insights.py",  label="MongoDB Insights")
    st.markdown("---")
    st.caption("Powered by MongoDB Atlas & Streamlit")

st.markdown("# Manage Books")
st.markdown("Add, edit, and delete books in the MongoDB database.")
st.markdown("---")

if not ping():
    st.error("Cannot connect to MongoDB Atlas.")
    st.stop()

col = get_collection("books")

def validate_book(title: str, author: str, genre: str, rating_str: str) -> tuple[dict | None, str]:
    errors = []

    title = title.strip()
    author = author.strip()
    genre = genre.strip()

    if not title:
        errors.append("Title is required.")
    if not author:
        errors.append("Author is required.")

    rating = None
    if rating_str.strip():
        try:
            rating = float(rating_str.strip())
            if not (0.0 <= rating <= 5.0):
                errors.append("Rating must be between 0.0 and 5.0.")
        except ValueError:
            errors.append("Rating must be a number (e.g. 4.2).")

    if errors:
        return None, " | ".join(errors)

    return {
        "title":       title,
        "author":      author,
        "genre":       genre or "Unknown",
        "rating":      rating,
        "description": None,
        "tags":        [a.strip() for a in author.split(",")][:3],
        "cover_url":   None,
    }, ""

tab_add, tab_edit, tab_delete, tab_browse = st.tabs(["Add Book", "Edit Book", "Delete Book", "Browse All"])

with tab_add:
    st.markdown("### Add a New Book")

    with st.form("add_form"):
        a_title = st.text_input("Title *", placeholder="e.g. The Great Gatsby")
        a_author = st.text_input("Author *", placeholder="e.g. F. Scott Fitzgerald")
        a_genre = st.text_input("Genre", placeholder="e.g. Classic Fiction")
        a_rating = st.text_input("Rating (0.0 – 5.0)", placeholder="e.g. 4.2")
        a_desc = st.text_area("Description (optional)", height=80)
        submitted = st.form_submit_button("Add Book", type="primary")

    if submitted:
        doc, err = validate_book(a_title, a_author, a_genre, a_rating)
        if err:
            st.error(f"Validation failed: {err}")
        else:
            if a_desc.strip():
                doc["description"] = a_desc.strip()
            existing = col.find_one({"title": doc["title"], "author": doc["author"]})
            if existing:
                st.warning(f"A book with this title and author already exists (ID: {existing['_id']}).")
            else:
                result = col.insert_one(doc)
                st.success(f"Book added successfully. MongoDB ID: {result.inserted_id}")
                st.cache_data.clear()

with tab_edit:
    st.markdown("### Edit an Existing Book")

    search_edit = st.text_input("Search by title to find book to edit", key="edit_search",
                                 placeholder="Start typing a title...")

    if search_edit.strip():
        matches = list(col.find(
            {"title": {"$regex": search_edit.strip(), "$options": "i"}},
            {"title": 1, "author": 1}
        ).limit(10))

        if not matches:
            st.info("No books found matching that title.")
        else:
            labels = [f"{m['title']} — {m['author']}" for m in matches]
            chosen = st.selectbox("Select a book to edit:", labels, key="edit_select")
            chosen_doc = matches[labels.index(chosen)]
            book = col.find_one({"_id": chosen_doc["_id"]})

            if book:
                with st.form("edit_form"):
                    e_title = st.text_input("Title *", value=book.get("title", ""))
                    e_author = st.text_input("Author *", value=book.get("author", ""))
                    e_genre = st.text_input("Genre", value=book.get("genre", ""))
                    cur_r = book.get("rating")
                    e_rating = st.text_input("Rating", value=str(cur_r) if cur_r else "")
                    e_desc = st.text_area("Description", value=book.get("description") or "", height=80)
                    save = st.form_submit_button("Save Changes", type="primary")

                if save:
                    doc, err = validate_book(e_title, e_author, e_genre, e_rating)
                    if err:
                        st.error(f"Validation failed: {err}")
                    else:
                        if e_desc.strip():
                            doc["description"] = e_desc.strip()
                        doc["tags"] = [a.strip() for a in e_author.split(",")][:3]

                        result = col.update_one(
                            {"_id": book["_id"]},
                            {"$set": doc}
                        )
                        if result.modified_count:
                            st.success("Book updated successfully.")
                            st.cache_data.clear()
                        else:
                            st.info("No changes were made (values unchanged).")

with tab_delete:
    st.markdown("### Delete a Book")
    st.warning("Deletion is permanent and cannot be undone.")

    search_del = st.text_input("Search by title to find book to delete", key="del_search",
                                placeholder="Start typing a title...")

    if search_del.strip():
        del_matches = list(col.find(
            {"title": {"$regex": search_del.strip(), "$options": "i"}},
            {"title": 1, "author": 1}
        ).limit(10))

        if not del_matches:
            st.info("No books found.")
        else:
            del_labels = [f"{m['title']} — {m['author']}" for m in del_matches]
            del_chosen = st.selectbox("Select a book to delete:", del_labels, key="del_select")
            del_doc = del_matches[del_labels.index(del_chosen)]

            st.markdown(f"**Selected:** {del_doc['title']} by {del_doc['author']}")

            confirm = st.checkbox("I confirm I want to permanently delete this book.")
            if confirm:
                if st.button("Delete Book", type="primary"):
                    result = col.delete_one({"_id": del_doc["_id"]})
                    if result.deleted_count:
                        st.success(f"'{del_doc['title']}' has been deleted from the database.")
                        st.cache_data.clear()
                    else:
                        st.error("Deletion failed. The book may have already been removed.")

with tab_browse:
    st.markdown("### All Books in Database")
    total = col.count_documents({})
    st.caption(f"Total: {total:,} books")

    page = st.number_input("Page", min_value=1, value=1, step=1)
    PAGE_SIZE = 20
    skip = (page - 1) * PAGE_SIZE

    docs = list(
        col.find({}, {"title": 1, "author": 1, "genre": 1, "rating": 1})
           .sort("title", 1)
           .skip(skip)
           .limit(PAGE_SIZE)
    )

    if docs:
        import pandas as pd
        df = pd.DataFrame([{
            "Title":  d.get("title", ""),
            "Author": d.get("author", ""),
            "Genre":  d.get("genre", ""),
            "Rating": f"{d['rating']:.2f}" if d.get("rating") else "N/A",
        } for d in docs])
        df.index = range(skip + 1, skip + len(df) + 1)
        st.dataframe(df, use_container_width=True)

        max_pages = -(-total // PAGE_SIZE)
        st.caption(f"Page {page} of {max_pages}")
    else:
        st.info("No books found on this page.")
