import os
import sys
import time

import psycopg


def to_psycopg_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


url = to_psycopg_url(os.environ["DATABASE_URL"])

for _ in range(60):
    try:
        with psycopg.connect(url):
            sys.exit(0)
    except psycopg.OperationalError:
        time.sleep(1)

print("Database connection timed out", file=sys.stderr)
sys.exit(1)
