import sys
from app.db.session import engine
from app.db.base import Base
import app.models  # Ensures all models are imported before metadata creation

def init_db():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
