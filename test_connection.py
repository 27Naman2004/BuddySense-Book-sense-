"""
test_connection.py
------------------
Phase 1 -- Verify that Python can reach MongoDB Atlas.

Run this script once to confirm everything is wired up correctly
before building the rest of the application.

Usage (inside activated .venv):
    python test_connection.py
"""

import sys
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, OperationFailure

# ── Step 1: Load environment variables ────────────────────────────────────────
print("=" * 55)
print("  BookBuddy -- MongoDB Atlas Connection Test")
print("=" * 55)

load_dotenv()  # reads .env from the current directory

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    print("\n[FAIL]  MONGODB_URI not found in .env")
    print("        Make sure .env exists and contains:")
    print('        MONGODB_URI="mongodb+srv://..."')
    sys.exit(1)

print("\n[OK]  Step 1 passed -- .env loaded successfully")
print(f"      URI starts with: {MONGODB_URI[:30]}...")   # never print the full URI

# ── Step 2: Create the MongoClient ────────────────────────────────────────────
try:
    # serverSelectionTimeoutMS = 5000 means "give up after 5 seconds" instead
    # of waiting the default 30 seconds when the cluster is unreachable.
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    print("\n[OK]  Step 2 passed -- MongoClient created")
except ConfigurationError as exc:
    print(f"\n[FAIL]  Step 2 failed -- bad connection string: {exc}")
    sys.exit(1)

# ── Step 3: Ping the cluster ──────────────────────────────────────────────────
try:
    # The 'ping' command is the lightest possible round-trip to the server.
    client.admin.command("ping")
    print("[OK]  Step 3 passed -- Atlas cluster responded to ping")
except ConnectionFailure as exc:
    print(f"\n[FAIL]  Step 3 failed -- cannot reach Atlas: {exc}")
    print("\n        Things to check:")
    print("        - Is your laptop's IP in the Atlas Access List?")
    print("        - Is the URI correct (username, password, cluster address)?")
    print("        - Do you have an active internet connection?")
    sys.exit(1)
except OperationFailure as exc:
    print(f"\n[FAIL]  Step 3 failed -- authentication error: {exc}")
    print("        Check your Atlas username and password in .env.")
    sys.exit(1)

# ── Step 4: Access the bookbuddy database and books collection ────────────────
try:
    db = client["bookbuddy"]
    collection = db["books"]

    # list_collection_names() actually talks to the server, confirming auth.
    existing_collections = db.list_collection_names()

    print(f"[OK]  Step 4 passed -- connected to database: bookbuddy")
    print(f"      Collections found: {existing_collections or ['(none yet)']}")

    # Count documents (will be 0 if the collection is empty -- that is fine).
    doc_count = collection.count_documents({})
    print(f"      Documents in 'books' collection: {doc_count}")

except OperationFailure as exc:
    print(f"\n[FAIL]  Step 4 failed -- permission error: {exc}")
    print("        Make sure the Atlas database user has readWrite access to 'bookbuddy'.")
    sys.exit(1)

# ── Done ──────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  All checks passed -- Atlas connection is working!")
print("  You are ready to move on to Phase 2.")
print("=" * 55)

client.close()
