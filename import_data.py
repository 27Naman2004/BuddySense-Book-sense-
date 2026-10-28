import sys
import argparse
import os
import urllib.request
import pandas as pd
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

DATASET_URL = "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv"
LOCAL_CSV = "data/books_raw.csv"

COL_TITLE = "title"
COL_AUTHOR = "authors"
COL_RATING = "average_rating"
COL_ISBN = "isbn"
COL_YEAR = "original_publication_year"
COL_LANG = "language_code"
COL_IMG = "image_url"

REQUIRED_COLS = [COL_TITLE, COL_AUTHOR]

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

def download_csv() -> bool:
    os.makedirs("data", exist_ok=True)
    print("Downloading dataset from GitHub...")
    try:
        urllib.request.urlretrieve(DATASET_URL, LOCAL_CSV)
        print(f"Saved to: {LOCAL_CSV}")
        return True
    except Exception as exc:
        print(f"Download failed: {exc}")
        return False

def load_csv(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, low_memory=False)
        print(f"Loaded {len(df):,} rows from {path}")
        return df
    except FileNotFoundError:
        print(f"CSV file not found: {path}")
        sys.exit(1)
    except Exception as exc:
        print(f"Cannot read CSV: {exc}")
        sys.exit(1)

def clean(df: pd.DataFrame) -> pd.DataFrame:
    for col in REQUIRED_COLS:
        if col not in df.columns:
            print(f"Required column '{col}' not found in CSV.")
            sys.exit(1)

    before = len(df)
    df = df.dropna(subset=[COL_TITLE])
    df = df[df[COL_TITLE].str.strip() != ""]
    print(f"Dropped {before - len(df)} rows with blank titles")

    df[COL_AUTHOR] = df[COL_AUTHOR].fillna("Unknown")

    def parse_rating(val):
        try:
            f = float(val)
            return round(f, 2) if 0.0 <= f <= 5.0 else None
        except (ValueError, TypeError):
            return None

    df["rating"] = df[COL_RATING].apply(parse_rating) if COL_RATING in df.columns else None

    if COL_LANG in df.columns:
        df["genre"] = df[COL_LANG].apply(
            lambda lc: LANG_GENRE.get(str(lc).strip(), "World Literature")
            if pd.notna(lc) else "Unknown"
        )
    else:
        df["genre"] = "Unknown"

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

    df["tags"] = df[COL_AUTHOR].apply(
        lambda a: [x.strip() for x in str(a).split(",")][:3]
    )

    df["cover_url"] = df[COL_IMG].where(df[COL_IMG].notna(), None) if COL_IMG in df.columns else None

    before = len(df)
    df = df.drop_duplicates(subset=[COL_TITLE, COL_AUTHOR])
    print(f"Dropped {before - len(df)} duplicate (title, author) rows")

    return df

def build_doc(row) -> dict:
    return {
        "title":       str(row[COL_TITLE]).strip(),
        "author":      str(row[COL_AUTHOR]).strip(),
        "genre":       str(row.get("genre", "Unknown")),
        "rating":      row.get("rating"),
        "year":        row.get("year"),
        "tags":        row.get("tags", []),
        "cover_url":   row.get("cover_url"),
        "description": None,
    }

def upsert_to_mongo(docs: list, dry_run: bool = False) -> dict:
    if dry_run:
        print(f"\n[DRY RUN] Would upsert {len(docs)} documents without writing to database.")
        for doc in docs[:5]:
            print(f"  {doc['title']} | {doc['author']} | {doc['genre']} | rating={doc['rating']}")
        return {"inserted": 0, "modified": 0, "skipped": 0}

    from db import get_collection
    collection = get_collection("books")

    collection.create_index(
        [("title", 1), ("author", 1)],
        unique=True,
        name="title_author_unique"
    )

    batch_size = 500
    inserted = modified = 0

    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        ops = [
            UpdateOne(
                {"title": d["title"], "author": d["author"]},
                {"$setOnInsert": d},
                upsert=True,
            )
            for d in batch
        ]
        try:
            result = collection.bulk_write(ops, ordered=False)
            inserted += result.upserted_count
            modified += result.modified_count
        except BulkWriteError as bwe:
            inserted += bwe.details.get("nInserted", 0)
            modified += bwe.details.get("nModified", 0)

        done = min(i + batch_size, len(docs))
        print(f"Progress: {done:,} / {len(docs):,}", end="\r")

    print()
    return {"inserted": inserted, "modified": modified, "skipped": len(docs) - inserted - modified}

def main():
    parser = argparse.ArgumentParser(description="Import books into MongoDB Atlas")
    parser.add_argument("--dry-run", action="store_true", help="Preview data without writing to DB")
    parser.add_argument("--limit", type=int, default=0, help="Import only first N records (0 = all)")
    args = parser.parse_args()

    print("BookBuddy - Dataset Import")

    if not os.path.exists(LOCAL_CSV):
        ok = download_csv()
        if not ok:
            print("Could not download the dataset automatically.")
            sys.exit(1)
    else:
        print(f"Using existing local file: {LOCAL_CSV}")

    df = load_csv(LOCAL_CSV)
    df = clean(df)

    if args.limit > 0:
        df = df.head(args.limit)
        print(f"Limited to {len(df)} records (--limit flag)")

    print(f"Records ready to import: {len(df):,}")

    docs = [build_doc(row) for _, row in df.iterrows()]
    stats = upsert_to_mongo(docs, dry_run=args.dry_run)

    if args.dry_run:
        print("DRY RUN complete. No records written.")
    else:
        print("Import complete.")
        print(f"Inserted: {stats['inserted']:,}")
        print(f"Modified: {stats['modified']:,}")
        print(f"Skipped:  {stats['skipped']:,}")

if __name__ == "__main__":
    main()
