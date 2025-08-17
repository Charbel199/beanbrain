import os
BEANCOUNT_FILE="/data/budget.beancount"
DEFAULT_CURRENCY = "USD"
DEFAULT_TZ = os.getenv(
    "DEFAULT_TZ", "Asia/Beirut"
)
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", 10)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./automations.db"
)

POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 20))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", 30))
DB_LOG_ENABLED = bool(int(os.getenv("BACKEND_DB_LOG", 0)))