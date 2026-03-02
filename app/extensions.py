"""
Database extensions and initialization
Handles MongoDB connection
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

# Global MongoDB client and database
mongo_client = None
db = None


def init_db(app):
    """Initialize MongoDB connection"""
    global mongo_client, db

    mongo_uri = app.config.get('MONGO_URI')

    if not mongo_uri:
        raise ValueError("MONGO_URI not found in environment variables")

    try:
        # Create MongoDB client
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # Test connection
        mongo_client.admin.command('ping')

        # Get database (database name from URI or default to 'webhook_db')
        # db = mongo_client.get_default_database() if mongo_client.get_default_database() else mongo_client.webhook_db
        db = mongo_client.get_default_database()

        # Create indexes for better query performance
        # Sort by timestamp descending
        db.events.create_index([("timestamp", -1)])
        # Prevent duplicate events
        db.events.create_index("request_id", unique=True)

        print(f"✅ MongoDB connected successfully to: {db.name}")

    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise
    except Exception as e:
        print(f"❌ MongoDB initialization error: {e}")
        raise


def get_db():
    """Get database instance"""
    return db


def close_db():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("MongoDB connection closed")
