"""
db.py
-----
Central database connection module for BookBuddy.

All other modules import `get_collection()` from here.
Credentials are loaded from .env -- never hardcoded.
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, OperationFailure

# Load .env once when this module is imported
load_dotenv()

_client = None  # module-level singleton


def get_client() -> MongoClient:
    """Return a cached MongoClient, creating one on first call."""
    global _client
    if _client is not None:
        return _client

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise EnvironmentError(
            "MONGODB_URI is not set. Add it to your .env file."
        )

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=6000)
    except ConfigurationError as exc:
        raise EnvironmentError(f"Invalid MONGODB_URI format: {exc}") from exc

    return _client


def get_db():
    """Return the 'bookbuddy' database object."""
    return get_client()["bookbuddy"]


def get_collection(name: str = "books"):
    """Return a collection from the bookbuddy database."""
    return get_db()[name]


def ping() -> bool:
    """
    Attempt a lightweight ping to Atlas.
    Returns True on success, False on failure.
    """
    try:
        get_client().admin.command("ping")
        return True
    except (ConnectionFailure, OperationFailure):
        return False
