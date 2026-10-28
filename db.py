import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError, OperationFailure

load_dotenv()

_client = None

def get_client() -> MongoClient:
    global _client
    if _client is not None:
        return _client

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise EnvironmentError("MONGODB_URI is not set. Add it to your .env file.")

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=6000)
    except ConfigurationError as exc:
        raise EnvironmentError(f"Invalid MONGODB_URI format: {exc}") from exc

    return _client

def get_db():
    return get_client()["bookbuddy"]

def get_collection(name: str = "books"):
    return get_db()[name]

def ping() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except (ConnectionFailure, OperationFailure):
        return False
