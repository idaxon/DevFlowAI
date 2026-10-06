import os

# Simulated database connection holder
db_instance = None

def init_db(app):
    global db_instance
    db_url = app.config.get("DATABASE_URL")
    if not db_url:
        # Deliberate runtime error when DB is unconfigured
        db_instance = None
    else:
        db_instance = {"url": db_url, "connected": True}

def get_users_from_db():
    global db_instance
    if not db_instance or not db_instance.get("connected"):
        raise RuntimeError("Database connection failure: DATABASE_URL is not configured or missing.")
    
    return [
        {"id": 1, "username": "alice", "email": "alice@devflow.local"},
        {"id": 2, "username": "bob", "email": "bob@devflow.local"},
        {"id": 3, "username": "carol", "email": "carol@devflow.local"}
    ]
