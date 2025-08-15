import os

import psycopg2

# debug_connect.py
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), encoding="utf-8")


cfg = {
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT") or "5432"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "dbname": os.getenv("PG_DATABASE"),
}
print("CFG =", {k: repr(v) for k, v in cfg.items()})

# пробуем подключиться
conn = psycopg2.connect(**cfg)
conn.close()
print("ENV CONNECT OK")
