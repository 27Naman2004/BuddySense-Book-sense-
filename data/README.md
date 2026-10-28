# data/README.md
# Data Directory

This folder holds the raw CSV file used to populate the BookBuddy database.

## Dataset

**Source**: goodbooks-10k  
**URL**: https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv  
**File**: `books_raw.csv` (downloaded automatically by `import_data.py`)

## Fields Used

| CSV Column              | BookBuddy Field | Notes                          |
|-------------------------|-----------------|--------------------------------|
| title                   | title           | Required                       |
| authors                 | author          | Required                       |
| average_rating          | rating          | Float 0.0–5.0                  |
| language_code           | genre           | Mapped to genre category       |
| original_publication_year | year          | Integer                        |
| image_url               | cover_url       | Optional                       |

## How to Import

```powershell
python import_data.py           # full import (~10,000 records)
python import_data.py --limit 500  # import first 500 only
python import_data.py --dry-run    # preview without writing to DB
```

The CSV is excluded from Git to keep the repository lightweight.
