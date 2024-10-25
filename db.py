from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize SQLAlchemy instance
db_use = SQLAlchemy()

# Initialize engine and session factory for non-ORM session usage
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Function to provide database session for Flask routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
