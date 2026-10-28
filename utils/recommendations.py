from db import get_collection

def get_recommendations(book: dict, limit: int = 6) -> list[dict]:
    collection = get_collection("books")

    book_id = book.get("_id")
    genre = book.get("genre", "")
    author = book.get("author", "")
    tags = book.get("tags", [])

    seen_ids = {book_id}
    results = []

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
