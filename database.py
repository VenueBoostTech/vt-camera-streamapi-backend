from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from config import settings

# Check if using SQLite and add appropriate connection settings
is_sqlite = settings.DATABASE_URL.startswith('sqlite')
connect_args = {
    'timeout': 30,  # Increases wait time for locks
    'check_same_thread': False
} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=QueuePool,
    pool_size=5,          # Number of permanent connections
    max_overflow=10,      # Number of additional connections when pool is full
    pool_timeout=30,      # Seconds to wait for available connection
    pool_recycle=1800,    # Recycle connections after 30 minutes
    pool_pre_ping=True    # Verify connection health before using
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()