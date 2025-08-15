import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from conf import DATABASE_URL, DB_LOG_ENABLED, POOL_SIZE, MAX_OVERFLOW, POOL_TIMEOUT

# Create engine
# echo=True prints all executed SQL. Set to 0 (False) for production unless debugging.
engine = create_engine(
    DATABASE_URL,
    echo=DB_LOG_ENABLED,
    pool_size=POOL_SIZE,  # Set the core pool size
    max_overflow=MAX_OVERFLOW,  # Set the max number of connections to create beyond the pool_size
    pool_timeout=POOL_TIMEOUT  # Set the timeout to wait for a connection
)

@event.listens_for(engine, "connect")
def set_pg_timezone(dbapi_connection, connection_record):
    """
    Sets the session timezone to UTC for PostgreSQL connections.
    This ensures that func.now() and other database-side operations
    return timestamps in UTC, and also affects how TIMESTAMP WITH TIME ZONE
    is handled on the connection.
    
    For SQLite, this is not needed as it doesn't have timezone support.
    """
    # Check if we're using PostgreSQL
    if hasattr(dbapi_connection, 'server_version'):  # PostgreSQL connection
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET TIMEZONE TO 'UTC'")
        except Exception as e:
            # Log the error but don't fail the connection
            print(f"Warning: Could not set timezone to UTC: {e}")
    
    # For SQLite, we don't need to do anything
    # SQLite stores datetime as text/integer and doesn't have timezone support

# Create session
# autoflush=False: Changes are not flushed automatically to the DB until commit or explicit flush.
# autocommit=False: Requires explicit session.commit() for changes to be persisted.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
Base.metadata.create_all(bind=engine) 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()