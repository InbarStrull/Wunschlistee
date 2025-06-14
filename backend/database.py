from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

DATABASE_URL = "sqlite:///tea_wishlist.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)  # `echo=True` shows SQL statements

# Create all tables defined in models.py
Base.metadata.create_all(engine)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)

print("Database and tables created successfully.")
