"""
import_data.py
-------------
Downloads (or reads a local copy of) the Open Library Books dataset CSV,
cleans it, and upserts records into bookbuddy.books on MongoDB Atlas.

Dataset: CMU Book Summary Dataset (publically available on Kaggle)
We use a simpler alternative: the "Books" dataset from Kaggle's
"goodbooks-10k" project, but since direct Kaggle download requires auth,
we use the Books Dataset from UC Irvine / arXiv that is freely available.

ACTUAL DATASET USED
-------------------
"Best Books Ever" compiled from Goodreads, available on the web as a
clean CSV.  We fetch a well-known mirror hosted on GitHub that has been
used in many student projects.

Source  : https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv
Fields  : book_id, goodreads_book_id, best_book_id, work_id, books_count,
          isbn, isbn13, authors, original_publication_year, original_title,
          title, language_code, average_rating, ratings_count,
          work_ratings_count, work_text_reviews_count, ratings_1 .. ratings_5,
          image_url, small_image_url

We map: title, authors -> author, average_rating -> rating.
Genre is not in this dataset; we derive a tag from language_code and
original_publication_year for demonstration purposes.

Usage
-----
    python import_data.py            # full import
    python import_data.py --dry-run  # preview first 10 rows, no DB write
    python import_data.py --limit 200 # import only first 200 records
"""

import sys
import argparse
import math
import pandas as pd
import urllib.request
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

# ── Dataset location ──────────────────────────────────────────────────────────
DATASET_URL = (
    "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv"
)
LOCAL_CSV = "data/books_raw.csv"

# ── Column map: CSV column -> our field name ──────────────────────────────────
COL_TITLE    = "title"
COL_AUTHOR   = "authors"
COL_RATING   = "average_rating"
COL_ISBN     = "isbn"
COL_YEAR     = "original_publication_year"
COL_LANG     = "language_code"
COL_IMG      = "image_url"
COL_ORIG_TTL = "original_title"

REQUIRED_COLS = [COL_TITLE, COL_AUTHOR]

# ── Genre mapping by language (simple rule for demo) ─────────────────────────
LANG_GENRE = {
    "en":    "English Fiction",
    "eng":   "English Fiction",
    "en-US": "English Fiction",
    "en-GB": "English Fiction",
    "fre":   "French Literature",
    "spa":   "Spanish Literature",
    "ger":   "German Literature",
    "jpn":   "Japanese Literature",
    "por":   "Portuguese Literature",
    "ita":   "Italian Literature",
    "ara":   "Arabic Literature",
    "rus":   "Russian Literature",
    "zho":   "Chinese Literature",
    "lat":   "Classical Literature",
    "grc":   "Classical Literature",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def download_csv() -> bool:
    """Download the raw CSV into data/ folder. Returns True on success."""
    import os
    os.makedirs("data", exist_ok=True)
    print(f"Downloading dataset from GitHub...")
    try:
        urllib.request.urlretrieve(DATASET_URL, LOCAL_CSV)
        print(f"  Saved to: {LOCAL_CSV}")
        return True
    except Exception as exc:
        print(f"  [WARN] Download failed: {exc}")
        return False


def load_csv(path: str) -> pd.DataFrame:
    """Load CSV with low_memory=False to avoid dtype warnings."""
    try:
        df = pd.read_csv(path, low_memory=False)
        print(f"  Loaded {len(df):,} rows from {path}")
        return df
    except FileNotFoundError:
        print(f"[ERROR] CSV file not found: {path}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Cannot read CSV: {exc}")
        sys.exit(1)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Validate, clean, and map columns to the BookBuddy schema."""

    # 1. Check required columns exist
    for col in REQUIRED_COLS:
        if col not in df.columns:
            print(f"[ERROR] Required column '{col}' not found in CSV.")
            print(f"  Available columns: {list(df.columns)}")
            sys.exit(1)

    # 2. Drop rows without a usable title
    before = len(df)
    df = df.dropna(subset=[COL_TITLE])
    df = df[df[COL_TITLE].str.strip() != ""]
    print(f"  Dropped {before - len(df)} rows with blank titles")

    # 3. Fill missing authors
    df[COL_AUTHOR] = df[COL_AUTHOR].fillna("Unknown")

    # 4. Clean rating: convert to float, keep only 0.0 – 5.0
    def parse_rating(val):
        try:
            f = float(val)
            return round(f, 2) if 0.0 <= f <= 5.0 else None
        except (ValueError, TypeError):
            return None

    df["rating"] = df[COL_RATING].apply(parse_rating) if COL_RATING in df.columns else None

    # 5. Derive genre from language_code
    if COL_LANG in df.columns:
        df["genre"] = df[COL_LANG].apply(
            lambda lc: LANG_GENRE.get(str(lc).strip(), "World Literature")
            if pd.notna(lc) else "Unknown"
        )
    else:
        df["genre"] = "Unknown"

    # 6. Year field
    if COL_YEAR in df.columns:
        def safe_year(v):
            try:
                y = int(float(v))
                return y if 0 < y <= 2030 else None
            except (ValueError, TypeError):
                return None
        df["year"] = df[COL_YEAR].apply(safe_year)
    else:
        df["year"] = None

    # 7. Tags: author names split into list (simple tag source)
    df["tags"] = df[COL_AUTHOR].apply(
        lambda a: [x.strip() for x in str(a).split(",")][:3]
    )

    # 8. Image URL
    df["cover_url"] = df[COL_IMG].where(df[COL_IMG].notna(), None) if COL_IMG in df.columns else None

    # 9. Drop duplicates on (title, author)
    before = len(df)
    df = df.drop_duplicates(subset=[COL_TITLE, COL_AUTHOR])
    print(f"  Dropped {before - len(df)} duplicate (title, author) rows")

    return df


def build_doc(row) -> dict:
    """Build a MongoDB document from a cleaned DataFrame row."""
    return {
        "title":       str(row[COL_TITLE]).strip(),
        "author":      str(row[COL_AUTHOR]).strip(),
        "genre":       str(row.get("genre", "Unknown")),
        "rating":      row.get("rating"),
        "year":        row.get("year"),
        "tags":        row.get("tags", []),
        "cover_url":   row.get("cover_url"),
        "description": None,   # not available in this dataset
    }


def upsert_to_mongo(docs: list, dry_run: bool = False) -> dict:
    """
    Upsert documents using (title, author) as the natural key.
    Returns a dict with inserted, modified, and skipped counts.
    """
    if dry_run:
        print(f"\n[DRY RUN] Would upsert {len(docs)} documents -- no DB write performed.")
        for doc in docs[:5]:
            print(f"  {doc['title']} | {doc['author']} | {doc['genre']} | rating={doc['rating']}")
        return {"inserted": 0, "modified": 0, "skipped": 0}

    # Import here so dry-run doesn't need a live connection
    from db import get_collection
    collection = get_collection("books")

    # Ensure a unique index so upserts are idempotent
    collection.create_index(
        [("title", 1), ("author", 1)],
        unique=True,
        name="title_author_unique"
    )

    BATCH = 500
    inserted = modified = 0

    for i in range(0, len(docs), BATCH):
        batch = docs[i : i + BATCH]
        ops = [
            UpdateOne(
                {"title": d["title"], "author": d["author"]},
                {"$setOnInsert": d},   # only set fields on new inserts
                upsert=True,
            )
            for d in batch
        ]
        try:
            result = collection.bulk_write(ops, ordered=False)
            inserted += result.upserted_count
            modified += result.modified_count
        except BulkWriteError as bwe:
            # Some may have been duplicate-key errors on existing docs -- fine
            inserted += bwe.details.get("nInserted", 0)
            modified += bwe.details.get("nModified", 0)

        done = min(i + BATCH, len(docs))
        print(f"  Progress: {done:,} / {len(docs):,}", end="\r")

    print()
    return {"inserted": inserted, "modified": modified, "skipped": len(docs) - inserted - modified}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import books into MongoDB Atlas")
    parser.add_argument("--dry-run", action="store_true", help="Preview data without writing to DB")
    parser.add_argument("--limit",   type=int, default=0, help="Import only first N records (0 = all)")
    args = parser.parse_args()

    print("=" * 55)
    print("  BookBuddy -- Dataset Import")
    print("=" * 55)

    # 1. Get the CSV (local copy preferred)
    import os
    if not os.path.exists(LOCAL_CSV):
        ok = download_csv()
        if not ok:
            print("\n[ERROR] Could not download the dataset automatically.")
            print("  Please download it manually:")
            print(f"  URL : {DATASET_URL}")
            print(f"  Save to: {LOCAL_CSV}")
            sys.exit(1)
    else:
        print(f"Using existing local file: {LOCAL_CSV}")

    # 2. Load
    print("\nStep 1: Loading CSV...")
    df = load_csv(LOCAL_CSV)

    print("\nActual columns in dataset:")
    print(" ", list(df.columns))

    # 3. Clean
    print("\nStep 2: Cleaning data...")
    df = clean(df)

    # 4. Limit
    if args.limit > 0:
        df = df.head(args.limit)
        print(f"  Limited to {len(df)} records (--limit flag)")

    print(f"\n  Records ready to import: {len(df):,}")

    # 5. Preview sample
    print("\nSample of cleaned records:")
    sample_cols = [COL_TITLE, COL_AUTHOR, "genre", "rating", "year"]
    print(df[[c for c in sample_cols if c in df.columns]].head(5).to_string(index=False))

    # 6. Upsert
    print("\nStep 3: Upserting into MongoDB Atlas...")
    docs = [build_doc(row) for _, row in df.iterrows()]
    stats = upsert_to_mongo(docs, dry_run=args.dry_run)

    # 7. Report
    print("\n" + "=" * 55)
    if args.dry_run:
        print("  DRY RUN complete -- no records written.")
    else:
        print(f"  Import complete!")
        print(f"  Inserted : {stats['inserted']:,}")
        print(f"  Modified : {stats['modified']:,}")
        print(f"  Skipped  : {stats['skipped']:,}  (already existed)")
    print("=" * 55)


if __name__ == "__main__":
    main()
