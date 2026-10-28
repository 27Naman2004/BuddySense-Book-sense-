"""
utils/recommendations.py
------------------------
Simple, rule-based book recommendation engine.

Rules (applied in order, results merged and deduplicated):
  1. Same genre  -- strongest signal
  2. Same author -- secondary signal
  3. Shared tags -- tertiary signal

Each returned book carries a 'reason' field explaining why it was suggested.
No machine learning is used. The logic is intentionally transparent so it
can be explained clearly during a college viva.
"""

from db import get_collection


def get_recommendations(book: dict, limit: int = 6) -> list[dict]:
    """
    Return up to `limit` books similar to `book`.

    Parameters
    ----------
    book  : dict  -- a MongoDB document from the books collection
    limit : int   -- maximum number of recommendations to return

    Returns
    -------
    List of dicts, each with the book fields plus a 'reason' key.
    """
    collection = get_collection("books")

    book_id = book.get("_id")
    genre   = book.get("genre", "")
    author  = book.get("author", "")
    tags    = book.get("tags", [])

    seen_ids = {book_id}   # exclude the source book
    results  = []

    # ── Rule 1: Same genre ────────────────────────────────────────────────────
    if genre and genre not in ("Unknown", ""):
        cursor = collection.find(
            {"genre": genre, "_id": {"$ne": book_id}},
            {"title": 1, "author": 1, "genre": 1, "rating": 1, "cover_url": 1}
        ).sort("rating", -1).limit(limit * 2)

        for doc in cursor:
            if doc["_id"] not in seen_ids:
                doc["reason"] = f"Same genre: {genre}"
                results.append(doc)
                seen_ids.add(doc["_id"])
            if len(results) >= limit:
                break

    # ── Rule 2: Same author ───────────────────────────────────────────────────
    if author and author != "Unknown" and len(results) < limit:
        cursor = collection.find(
            {"author": author, "_id": {"$ne": book_id}},
            {"title": 1, "author": 1, "genre": 1, "rating": 1, "cover_url": 1}
        ).limit(limit)

        for doc in cursor:
            if doc["_id"] not in seen_ids:
                doc["reason"] = f"Same author: {author}"
                results.append(doc)
                seen_ids.add(doc["_id"])
            if len(results) >= limit:
                break

    # ── Rule 3: Shared tags ───────────────────────────────────────────────────
    if tags and len(results) < limit:
        cursor = collection.find(
            {"tags": {"$in": tags}, "_id": {"$nin": list(seen_ids)}},
            {"title": 1, "author": 1, "genre": 1, "rating": 1, "cover_url": 1}
        ).limit(limit)

        for doc in cursor:
            if doc["_id"] not in seen_ids:
                shared = [t for t in tags if t in doc.get("tags", [])]
                doc["reason"] = f"Shared tag: {shared[0]}" if shared else "Similar tags"
                results.append(doc)
                seen_ids.add(doc["_id"])
            if len(results) >= limit:
                break

    return results[:limit]
