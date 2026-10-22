
import os

from dotenv import load_dotenv
from pymongo import MongoClient

# Read configuration from the .env file
load_dotenv()

# Get the MongoDB connection address
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017"
)

# Connect to MongoDB
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

# Select our database and collection
database = client["procurement_ai"]
purchases = database["purchases"]


def test_connection():
    """Check whether MongoDB is reachable."""

    client.admin.command("ping")
    return purchases.count_documents({})
