from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. The Database URL (This will create a local file named 'sentry.db')
SQLALCHEMY_DATABASE_URL = "sqlite:///./sentry.db"

# 2. The Engine (The core interface to the database)
# check_same_thread=False is a specific requirement for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. The Session (The temporary connection used to talk to the DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. The Base (The master class that all our database tables will inherit from)
Base = declarative_base()