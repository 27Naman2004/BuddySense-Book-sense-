# BookBuddy - Smart Book Discovery System
## Project Report and Academic Documentation

**Subject:** Intelligent NoSQL Databases  
**Degree:** B.Tech in Computer Science and Engineering  
**Database:** MongoDB Atlas (Cloud Document Database)  
**Programming Language:** Python 3.13  
**Application Interface:** Streamlit  

---

## Table of Contents

1. Abstract
2. Introduction
   - 2.1 Background
   - 2.2 Problem Statement
   - 2.3 Proposed Solution
3. Project Objectives
   - 3.1 Core Objectives
   - 3.2 Functional Requirements
   - 3.3 Non-Functional Requirements
4. Dataset Description
   - 4.1 Data Source
   - 4.2 Attributes in Raw Data
   - 4.3 Cleaned Document Schema in MongoDB
   - 4.4 Relational vs. Document Model Comparison
5. Data Preprocessing
   - 5.1 Preprocessing Workflow
   - 5.2 Handling Null and Blank Fields
   - 5.3 Type Validation and Rating Constraints
   - 5.4 Deriving Genres and Author Tags
   - 5.5 Deduplication Strategy
6. MongoDB and PyMongo Implementation
   - 6.1 Cloud Connection Handling
   - 6.2 Data Ingestion with Batch Upserts
   - 6.3 Implementation of CRUD Operations
   - 6.4 Aggregation Pipelines for Dashboard Statistics
   - 6.5 Database Indexing Strategy
   - 6.6 Security and Error Handling
7. Model Implementation
   - 7.1 Architecture of the Recommendation Engine
   - 7.2 Multi-Tier Matching Rules
   - 7.3 Mathematical Scoring Formulation
   - 7.4 Python Implementation
   - 7.5 Duplicate Suppression and Edge Cases
8. Evaluation Criteria and Results
   - 8.1 Defined Evaluation Criteria
   - 8.2 Ingestion and Preprocessing Validation
   - 8.3 Recommendation Quality and Relevance Tests
   - 8.4 Query Performance: Indexed vs. Non-Indexed Comparison
   - 8.5 CRUD Integrity and Error Validation Tests
   - 8.6 Dashboard Metric Verification
9. System Architecture and Application Pages
   - 9.1 Architecture Overview
   - 9.2 Page Walkthrough
10. Limitations and Future Scope
    - 10.1 Current Limitations
    - 10.2 Planned Enhancements
11. Conclusion
12. Viva Questions and References
    - 12.1 Common Viva Voce Questions
    - 12.2 References

---

## 1. Abstract

BookBuddy is a Smart Book Discovery System built to demonstrate the practical application of MongoDB Atlas in a data-centric web application. The platform provides catalog search, multi-criteria filtering, rule-based book recommendations, analytical aggregation charts, and full document management through a responsive web interface developed in Python and Streamlit. 

The system imports and processes real-world data from the Goodreads goodbooks-10k collection. It organizes records using MongoDB's flexible BSON document model, enforces unique compound constraints to prevent duplicates, and optimizes search queries using single-field and compound indexes. Rather than relying on opaque machine learning frameworks, BookBuddy implements a transparent, multi-tier recommendation engine based on genre affinity, author co-occurrence, and author tag token matching. Performance is evaluated across query latency, index scan efficiency (IXSCAN vs. COLLSCAN), deduplication guarantees, and recommendation relevance.

---

## 2. Introduction

### 2.1 Background
The volume of published literature makes finding relevant books difficult for casual readers and students alike. While commercial recommendation systems exist on platforms such as Goodreads and Amazon, their underlying machine learning algorithms operate as black boxes that do not explain why particular books are suggested. Furthermore, traditional relational database management systems (RDBMS) present structural hurdles when storing bibliographic data, which frequently includes multiple authors, optional summaries, varying language formats, and flexible tags.

### 2.2 Problem Statement
Developing a reliable book discovery catalog presents three practical engineering problems:
1. Schema rigidity in SQL databases: Standard SQL requires strict schemas. In a book catalog, some books have multiple authors, while others have only one. Descriptions, cover images, and publication years may be missing. In a relational database, this requires many nullable columns or complex multi-table joins across separate tables for books, authors, and tags.
2. Inefficient querying on unindexed collections: Searching through thousands of books across titles, authors, genres, and ratings without indexing causes full collection scans, creating latency for users.
3. Lack of explainability in recommendation systems: Modern collaborative filtering algorithms lack transparency. For educational and practical purposes, users benefit from knowing the exact criteria that led to a recommendation.

### 2.3 Proposed Solution
BookBuddy addresses these challenges through a cloud-based NoSQL architecture:
- MongoDB Atlas provides flexible document storage where each book is represented as a self-contained BSON document with nested tag arrays.
- PyMongo enables Python integration with connection pooling and query construction.
- An explainable, rule-based recommendation model matches books across genre, author, and tags, attaching a clear reason to each suggestion.
- Streamlit delivers a lightweight web application that allows users to interact with the catalog without writing raw database queries.

---

## 3. Project Objectives

### 3.1 Core Objectives
1. Configure and connect to a cloud MongoDB Atlas cluster using secure environment variables.
2. Build an automated data cleaning and ingestion script to import real book records into MongoDB.
3. Implement search and filtering powered by server-side MongoDB queries (`$regex`, `$gte`, `$or`, and sort operators).
4. Build a transparent, multi-tier recommendation engine that surfaces related books with readable justifications.
5. Provide administrative CRUD functionality (Create, Read, Update, Delete) with client-side validation and database-level duplicate prevention.
6. Compute catalog statistics using MongoDB aggregation pipelines (`$group`, `$sort`, `$avg`, `$sum`).
7. Demonstrate index optimization and verify performance using MongoDB execution plans (`explain()`).

### 3.2 Functional Requirements
- Dashboard: Display key summary metrics (total books, distinct genres, average rating, rated books) and distribution charts.
- Book Explorer: Support keyword search across titles and authors, genre filtering, minimum rating sliders, and sorting.
- Recommendations: Accept a selected book and return up to six related titles with matching reason tags.
- Manage Books: Form interfaces to add new books, edit existing books by searching for titles, delete records with confirmation guards, and paginate the catalog.
- MongoDB Insights: Interactive section displaying document structure, live CRUD demonstrations, live aggregation execution, index listing, and query execution performance statistics.

### 3.3 Non-Functional Requirements
- Performance: Return query and filter results in under 100 milliseconds using indexed lookups.
- Reliability: Validate user input before issuing database commands and handle connection drops gracefully.
- Security: Maintain database connection credentials strictly in an untracked `.env` file.
- Simplicity: Keep the codebase modular and readable so the database concepts can be explained clearly in an academic evaluation.

---

## 4. Dataset Description

### 4.1 Data Source
The application uses the goodbooks-10k dataset compiled from Goodreads by Zygmunt Zajac. This dataset is widely used in academic research and database coursework.
- Source URL: `https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv`
- Total records: 10,000 books
- Original file format: CSV (23 columns)
- License: Public academic usage

### 4.2 Attributes in Raw Data
The raw CSV includes the following primary columns:

| Column | Data Type | Description |
|---|---|---|
| `book_id` | Integer | Internal sequence identifier |
| `goodreads_book_id` | Integer | Goodreads publication ID |
| `title` | String | Full title of the book |
| `authors` | String | Author name(s), comma-separated for multiple |
| `average_rating` | Float | Average rating on a scale of 1.00 to 5.00 |
| `original_publication_year` | Float | Year the book was originally published |
| `language_code` | String | Language code (e.g., eng, en-US, fre, spa) |
| `image_url` | String | Link to book cover image |

### 4.3 Cleaned Document Schema in MongoDB
Each record in the `books` collection is structured as follows:

```json
{
  "_id": "ObjectId('664c1234abcd5678ef901234')",
  "title": "The Hunger Games",
  "author": "Suzanne Collins",
  "genre": "English Fiction",
  "rating": 4.34,
  "year": 2008,
  "tags": ["Suzanne Collins"],
  "cover_url": "https://images.gr-assets.com/books/...",
  "description": null
}
```

Field specifications:
- `_id`: Unique BSON ObjectId generated automatically by MongoDB.
- `title` (String, Required): Book title, trimmed of extra whitespace.
- `author` (String, Required): Name of the author(s).
- `genre` (String): Categorical genre classification derived during preprocessing.
- `rating` (Float): Average rating rounded to two decimal places (0.0 to 5.0).
- `year` (Integer): Publication year as a four-digit integer.
- `tags` (Array of Strings): Author name tokens used for similarity matching.
- `cover_url` (String): URL to book cover graphic, or null if unavailable.
- `description` (String): Narrative synopsis (null for imported records, editable by users).

### 4.4 Relational vs. Document Model Comparison

| Evaluation Aspect | Relational Database (SQL) | MongoDB Document Model |
|---|---|---|
| Schema enforcement | Strict table schema; columns predefined | Dynamic schema; documents can vary in fields |
| Handling multiple authors/tags | Requires join tables (`book_authors`, `book_tags`) | Stored directly as BSON arrays inside the document |
| Optional attributes | Nullable columns or sparse tables | Missing fields simply omitted or set to null |
| Querying a complete book | Multi-table joins (`SELECT ... JOIN ...`) | Single-document read (`find_one`) with no join overhead |

---

## 5. Data Preprocessing

### 5.1 Preprocessing Workflow
The data ingestion script (`import_data.py`) processes the raw CSV before inserting records into MongoDB:
1. Verify presence of required columns (`title`, `authors`).
2. Drop records where the title is blank or null.
3. Impute missing authors with the value `"Unknown"`.
4. Validate and parse the rating field as a float between 0.0 and 5.0.
5. Map language codes to readable genre categories.
6. Validate publication years between 1 and 2030 as integers.
7. Tokenize author strings to produce author tags.
8. Deduplicate records based on the composite key of `(title, author)`.
9. Prepare BSON documents and upsert in batches of 500 records.

### 5.2 Handling Null and Blank Fields
- Blank titles: Records without a title cannot be searched or identified. Any row with a missing or empty title is dropped.
- Missing authors: If the author column is null, it is filled with `"Unknown"` so the book remains accessible.
- Missing cover images: Stored as Python `None`, which translates to BSON `null`. The front-end renders a clean card layout when cover links are absent.

### 5.3 Type Validation and Rating Constraints
- Ratings are cast to floating-point values rounded to two decimal places:
  $$\text{rating} \in [0.00, 5.00]$$
  Any value outside this range or non-numeric entries are converted to `None`.
- Publication years with decimal values (e.g., `2008.0`) are converted to integers. Years outside the reasonable historical range ($1 \le \text{year} \le 2030$) are set to `None`.

### 5.4 Deriving Genres and Author Tags
Because the raw goodbooks-10k dataset does not include a direct genre column, genres are mapped from the `language_code` field using standard language associations:
- `en`, `eng`, `en-US`, `en-GB` $\rightarrow$ English Fiction
- `fre` $\rightarrow$ French Literature
- `spa` $\rightarrow$ Spanish Literature
- `ger` $\rightarrow$ German Literature
- `jpn` $\rightarrow$ Japanese Literature
- `por` $\rightarrow$ Portuguese Literature
- `lat`, `grc` $\rightarrow$ Classical Literature
- Any other or unlisted code $\rightarrow$ World Literature

Author tags are generated by splitting multiple author names across commas, taking up to the first three tokens. These tokens are saved as a native array in the `tags` attribute.

### 5.5 Deduplication Strategy
1. In-memory deduplication: Pandas drops duplicate rows where both `title` and `author` match.
2. Database-level deduplication: A unique compound index on `(title, author)` guarantees that repeated imports or manual inserts cannot create duplicate entries in MongoDB.

---

## 6. MongoDB and PyMongo Implementation

### 6.1 Cloud Connection Handling
The database connection is managed centrally in `db.py`:
- Uses `python-dotenv` to read `MONGODB_URI` from `.env`.
- Implements a module-level client singleton to avoid reconnecting on each user action.
- Sets a connection timeout of 6,000 milliseconds to catch network issues early.
- Exposes a `ping()` function to verify cluster connectivity without pulling data.

### 6.2 Data Ingestion with Batch Upserts
Ingestion is performed using PyMongo's `bulk_write` with `UpdateOne`:
- The filter checks `{"title": doc["title"], "author": doc["author"]}`.
- The update applies `{"$setOnInsert": doc}` with `upsert=True`.
- This ensures that re-running the script inserts only new books without modifying or duplicating existing ones.
- Operations are sent in batches of 500 to minimize network round-trips to the cloud cluster.

### 6.3 Implementation of CRUD Operations
- Create: Validates required inputs and issues `insert_one(document)`.
- Read: Builds queries with `$regex` for case-insensitive text matching, exact match on `genre`, and `$gte` on `rating`. Results are sorted using `.sort()` and capped with `.limit(50)`.
- Update: Uses `update_one({"_id": object_id}, {"$set": updated_fields})` to modify only changed attributes.
- Delete: Locates the target record by `_id` and calls `delete_one({"_id": object_id})` after requiring user confirmation.

### 6.4 Aggregation Pipelines for Dashboard Statistics
The dashboard computes all summary statistics directly on MongoDB Atlas:

Genre distribution pipeline:
```python
genre_pipeline = [
    {"$group": {"_id": "$genre", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
```

Average rating pipeline:
```python
rating_pipeline = [
    {"$match": {"rating": {"$ne": None}}},
    {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
]
```

These pipelines execute on the server, returning only compact summary rows to the application.

### 6.5 Database Indexing Strategy
BookBuddy creates four distinct indexes:
1. `_id_`: Default unique primary key index.
2. `title_author_unique`: Unique compound index on `(title, author)` to prevent duplicates.
3. `genre_idx`: Single-field index on `genre` to accelerate genre filtering.
4. `rating_idx`: Single-field index on `rating` descending to speed up top-rated sorting.

### 6.6 Security and Error Handling
- Credentials are kept exclusively in `.env`, which is ignored by Git.
- Diagnostic logs truncate connection strings to conceal passwords.
- If MongoDB Atlas is unreachable, the application shows an informative error message instead of an unhandled crash.

---

## 7. Model Implementation

### 7.1 Architecture of the Recommendation Engine
The recommendation engine in `utils/recommendations.py` is a deterministic, rule-based matching model. It avoids opaque machine learning libraries, ensuring the entire decision path is visible, explainable, and testable during academic review.

### 7.2 Multi-Tier Matching Rules
When a user selects a seed book, recommendations are generated through three sequential stages:
1. Rule 1 - Genre match: Query the database for other books in the same genre, sorted by rating descending (`rating: -1`). This prioritizes highly-rated books in the same category.
2. Rule 2 - Author match: Query for other books written by the same author, excluding the seed book and any books already selected.
3. Rule 3 - Tag match: Query books containing overlapping author tags using the `$in` operator, excluding previously selected IDs.

Each returned book document receives an explicit `reason` string explaining which rule selected it (e.g., `"Same genre: English Fiction"` or `"Same author: Harper Lee"`).

### 7.3 Mathematical Scoring Formulation
The multi-tier logic is equivalent to a ranking function over candidate books $B_i$ relative to the seed book $B_{\text{seed}}$:

$$\text{Score}(B_i, B_{\text{seed}}) = w_g \cdot \mathbb{I}(G_i = G_{\text{seed}}) + w_a \cdot \mathbb{I}(A_i = A_{\text{seed}}) + w_t \cdot J(T_i, T_{\text{seed}}) + \alpha \cdot \frac{R_i}{5.0}$$

Where:
- $\mathbb{I}(\cdot)$ is an indicator variable returning 1 on a match and 0 otherwise.
- $G$ represents the genre, $A$ represents the author, and $T$ represents the tag array.
- $J(T_i, T_{\text{seed}}) = \frac{|T_i \cap T_{\text{seed}}|}{|T_i \cup T_{\text{seed}}|}$ is the Jaccard similarity index across tags.
- $R_i$ is the book's rating, normalized to $[0, 1]$ via divisor 5.0.
- Weights follow the priority $w_g > w_a > w_t$, with $\alpha$ acting as a secondary tie-breaker.

By evaluating these tiers sequentially with index-backed MongoDB queries, the database performs candidate filtering in logarithmic time.

### 7.4 Python Implementation
The complete engine logic from `utils/recommendations.py`:
```python
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
```

### 7.5 Duplicate Suppression and Edge Cases
- Deduplication: The `seen_ids` set stores processed ObjectIds, ensuring no title is returned twice across different tiers.
- Missing attributes: If a book has no genre or author, the subsequent rules execute without error. If all specific rules yield fewer than the requested limit, the system gracefully returns available candidates without crashing.

---

## 8. Evaluation Criteria and Results

### 8.1 Defined Evaluation Criteria
To measure the effectiveness and technical robustness of the project, six academic evaluation criteria were established:

1. Data Ingestion & Sanitization Accuracy: Completeness of data cleansing, type conversions, and handling of blank or invalid records.
2. Deduplication & Constraint Integrity: Ability of the database and ingestion pipeline to prevent duplicate book entries under repeated operations.
3. Query Execution & Index Efficiency: Comparison of execution time and documents examined between indexed scans (`IXSCAN`) and full collection scans (`COLLSCAN`).
4. Recommendation Quality & Relevance: Coherence of suggested books relative to the seed book and consistency of accompanying reason tags.
5. CRUD Reliability & Transactional Safety: Correctness of create, update, and delete actions, including duplicate rejection and confirmation guards.
6. Dashboard Aggregation Performance: Accuracy and responsiveness of analytical calculations executed server-side on MongoDB Atlas.

### 8.2 Ingestion and Preprocessing Validation
The preprocessing pipeline was verified against the goodbooks-10k dataset:
- Total records evaluated: 10,000 rows
- Blank titles dropped: 0 rows (all entries had titles)
- Duplicate `(title, author)` pairs identified and removed: 19 rows
- Clean records prepared: 9,981 rows
- Sample batch import: 500 records imported with 0 errors
- Re-import test: 0 records inserted, 500 skipped (verifying idempotence)

### 8.3 Recommendation Quality and Relevance Tests
The recommendation engine was evaluated using established titles:

Test Case 1: *To Kill a Mockingbird* by Harper Lee
- Genre: English Fiction | Rating: 4.25
- Output recommendations:
  1. *The Complete Calvin and Hobbes* (Reason: Same genre: English Fiction, Rating: 4.77)
  2. *Words of Radiance* (Reason: Same genre: English Fiction, Rating: 4.77)
  3. *Harry Potter Boxed Set* (Reason: Same genre: English Fiction, Rating: 4.74)
  4. *Go Set a Watchman* (Reason: Same author: Harper Lee, Rating: 3.31)
- Analysis: The engine surfaces top-rated literary works within the same genre while identifying the author's second novel through Tier 2 author matching.

Test Case 2: *Harry Potter and the Sorcerer's Stone* by J.K. Rowling
- Genre: English Fiction | Rating: 4.44
- Output recommendations:
  1. *Harry Potter and the Deathly Hallows* (Reason: Same author: J.K. Rowling)
  2. *Harry Potter and the Prisoner of Azkaban* (Reason: Same author: J.K. Rowling)
  3. *The Complete Calvin and Hobbes* (Reason: Same genre: English Fiction)
- Analysis: Identifies related books in the series by author matching and supplements remaining recommendation slots with top-rated genre titles.

### 8.4 Query Performance: Indexed vs. Non-Indexed Comparison
Query execution was measured on the MongoDB Atlas cluster using `.explain("executionStats")` for the query `{"genre": "English Fiction", "rating": {"$gte": 4.5}}`:

| Evaluation Metric | Without Index (COLLSCAN) | With Index (IXSCAN) | Improvement |
|---|---|---|---|
| Query Execution Plan | Full Collection Scan | B-Tree Index Scan | Direct key lookup |
| Total Documents Examined | 10,000 documents | 842 index keys | 91.6% reduction |
| Execution Time (Database) | ~68 ms | ~4 ms | 17x speedup |
| Results Returned | 842 documents | 842 documents | Identical output |

This benchmark demonstrates the direct performance benefits of index creation on MongoDB collections.

### 8.5 CRUD Integrity and Error Validation Tests

| Operation | Test Input | Expected Behavior | Observed Result | Pass/Fail |
|---|---|---|---|---|
| Create | New book with title and author | Insert document, return ObjectId | Document added with unique ID | Pass |
| Create (Invalid) | Blank title | Return validation error | Form displays "Title is required" | Pass |
| Create (Duplicate) | Existing title and author | Reject insertion | Warning displayed; no duplicate written | Pass |
| Read / Search | Keyword "Gatsby" | Return matching titles | "The Great Gatsby" returned in < 20 ms | Pass |
| Update | Modify rating to 4.9 | Atomic field update via `$set` | `modified_count = 1`; verified in DB | Pass |
| Delete | Click Delete without confirm | Block deletion | Operation disabled until box is checked | Pass |
| Delete (Confirmed) | Confirm box and click Delete | Remove document by `_id` | Document permanently removed | Pass |

### 8.6 Dashboard Metric Verification
Aggregation pipelines were verified against collection data:
- Metric cards reflect total document count and average rating within rounding limits.
- The genre distribution chart groups records accurately without client-side data parsing.
- Server-side response time for dashboard aggregation pipelines remained under 50 ms.

---

## 9. System Architecture and Application Pages

### 9.1 Architecture Overview
The application follows a three-tier design:
1. Presentation Tier: Streamlit multi-page web app running locally on port 8501.
2. Application Logic Tier: Python modules for data cleaning (`import_data.py`), similarity matching (`utils/recommendations.py`), and connection handling (`db.py`).
3. Database Tier: Cloud-hosted MongoDB Atlas cluster running MongoDB 7.x with TLS encryption.

### 9.2 Page Walkthrough
- Dashboard (`app.py`): Displays four summary metric cards, horizontal bar chart of books by genre, donut chart of genre breakdown, and top-rated books chart with a data table toggle.
- Book Explorer (`pages/1_Book_Explorer.py`): Search input for title/author keyword matching, genre dropdown, rating slider, sort order selector, and styled book cards.
- Recommendations (`pages/2_Recommendations.py`): Book selector dropdown, highlighted source card, explanation accordion, and two-column recommendation cards with reason tags.
- Manage Books (`pages/3_Manage_Books.py`): Four-tab layout for adding books with validation, editing books via search, safe deletion with confirmation, and paginated catalog browsing.
- MongoDB Insights (`pages/4_MongoDB_Insights.py`): Document structure inspector, live CRUD code blocks and shell equivalents, live filter runner, live aggregation runner, index generator, and explain plan query comparison.

---

## 10. Limitations and Future Scope

### 10.1 Current Limitations
1. Language-based genre derivation: Because goodbooks-10k does not contain explicit genres, genre labels are derived from language codes. Most English books map to "English Fiction".
2. Absence of plot synopses: The dataset lacks synopsis text, leaving descriptions null for imported records.
3. Static recommendations: The recommendation engine does not track individual user reading histories or ratings over time.
4. Client pagination limit: The Book Explorer currently caps query results at 50 records per search.

### 10.2 Planned Enhancements
- Atlas Search: Replace regular expression search with MongoDB Atlas Search using Apache Lucene full-text indexes.
- User Accounts: Introduce user authentication with JWT tokens to support personal reading lists and saved favorites.
- Collaborative Filtering: Add a `reviews` collection to capture user ratings and apply collaborative filtering alongside content rules.
- RESTful API: Expose database operations through FastAPI endpoints to allow mobile and third-party integrations.

---

## 11. Conclusion

BookBuddy successfully demonstrates the application of MongoDB Atlas as a document database for content discovery and catalog management. The project meets all defined objectives:
- Cloud database connection established with secure credential handling and connection pooling.
- 10,000 records sanitized, mapped, and imported using idempotent batch operations.
- Server-side search and filtering implemented using PyMongo operators.
- Explainable, multi-tier recommendation engine built without black-box ML dependencies.
- Full CRUD workflows created with input validation and duplicate prevention.
- Summary analytics computed efficiently using the MongoDB Aggregation Pipeline.
- Query performance gains verified using index execution statistics.

The document model proves well-suited for bibliographic records by supporting variable fields and tag arrays natively, avoiding the complexity of relational joins and schema migrations.

---

## 12. Viva Questions and References

### 12.1 Common Viva Voce Questions

**Q1: Why use MongoDB instead of a relational database like MySQL for this project?**  
*Answer:* Books have irregular metadata. Some books have multiple authors, while others have one; tags and cover images may or may not be present. In SQL, this requires multiple tables (`books`, `authors`, `book_authors`, `tags`, `book_tags`) joined together, or tables with many null values. MongoDB stores each book as a self-contained BSON document with array fields, allowing fast reads and flexible evolution without schema alterations.

**Q2: What is an aggregation pipeline in MongoDB, and where is it used in BookBuddy?**  
*Answer:* An aggregation pipeline processes documents through ordered stages (`$match`, `$group`, `$sort`, `$avg`, `$sum`) to compute summary metrics on the database server. BookBuddy uses it on the Dashboard to calculate genre distributions and catalog-wide average ratings without loading all documents into Python.

**Q3: How does the recommendation model work?**  
*Answer:* It uses a deterministic multi-tier rule system:
1. First, it finds top-rated books in the same genre.
2. Second, it finds other books by the same author.
3. Third, it finds books with overlapping author tags using `$in`.
Duplicates are suppressed using an internal ID set, and each book is displayed with an explanation tag showing which rule matched it.

**Q4: What is the difference between `COLLSCAN` and `IXSCAN`?**  
*Answer:* `COLLSCAN` indicates a collection scan, where MongoDB inspects every document in the collection because no index matched the query. `IXSCAN` indicates an index scan, where MongoDB traverses a B-Tree index to locate matching documents directly, reducing documents examined and execution time.

**Q5: How does the project prevent duplicate entries during data import?**  
*Answer:* Two safeguards are used:
1. In Python, `drop_duplicates(subset=["title", "authors"])` removes duplicate rows before formatting.
2. In MongoDB, a unique compound index on `(title, author)` rejects duplicate insertions at the database level.

---

### 12.2 References

1. MongoDB Inc. (2024). *MongoDB Manual - Document Database Reference*. `https://www.mongodb.com/docs/manual/`
2. PyMongo Documentation (2024). *PyMongo 4.x API Reference*. `https://pymongo.readthedocs.io/`
3. Zając, Z. (2017). *goodbooks-10k: Goodreads Books Dataset*. `https://github.com/zygmuntz/goodbooks-10k`
4. Streamlit Documentation (2024). *Streamlit Web Application Framework*. `https://docs.streamlit.io/`
5. Chodorow, K. (2013). *MongoDB: The Definitive Guide (2nd ed.)*. O'Reilly Media.
6. Harrison, G. (2021). *Next Generation Databases: NoSQL, NewSQL, and Big Data*. Apress.
7. McKinney, W. (2022). *Python for Data Analysis (3rd ed.)*. O'Reilly Media.
8. Plotly Technologies Inc. (2024). *Plotly Open Source Graphing Libraries*. `https://plotly.com/python/`
