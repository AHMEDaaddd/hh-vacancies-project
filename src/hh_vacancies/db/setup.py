from __future__ import annotations

import os
from typing import Optional, Tuple

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, connection as PGConnection


def _clean(s: str) -> str:
    return s.replace("\ufeff", "").replace("\xa0", " ").strip()


def env(key: str, default: Optional[str] = None) -> str:
    v = os.getenv(key, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {key}")
    return _clean(v)


def get_super_conn() -> PGConnection:
    host = env("PG_HOST")
    port = int(env("PG_PORT", "5432"))
    user = env("PG_SUPERUSER", env("PG_USER"))
    password = env("PG_SUPERPASS", env("PG_PASSWORD"))
    return psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")


def get_work_conn(db_required: bool = True) -> PGConnection:
    host = env("PG_HOST")
    port = int(env("PG_PORT", "5432"))
    user = env("PG_USER")
    password = env("PG_PASSWORD")
    dbname = env("PG_DATABASE")
    if not db_required:
        return psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
    return psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)


def create_database_if_needed() -> Tuple[bool, str]:
    """
    Создает базу PG_DATABASE, если её нет. Возвращает (was_created, dbname).
    Если нет прав — просто пропускаем (вернём False).
    """
    dbname = env("PG_DATABASE")
    try:
        conn = get_super_conn()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(f'CREATE DATABASE "{dbname}"')
        conn.close()
        return True, dbname
    except Exception:
        # Нет прав или другая причина — продолжаем работу, полагая, что БД уже существует
        return False, dbname


def create_tables() -> None:
    """
    Создает таблицы employers и vacancies с FK и полезными индексами.
    """
    conn = get_work_conn(db_required=True)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employers (
                id SERIAL PRIMARY KEY,
                hh_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                area TEXT,
                open_vacancies INTEGER
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vacancies (
                id SERIAL PRIMARY KEY,
                employer_id INTEGER NOT NULL REFERENCES employers(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at TIMESTAMPTZ,
                salary_from NUMERIC,
                salary_to NUMERIC,
                currency TEXT,
                requirement TEXT,
                responsibility TEXT
            );
            """
        )

        # Индексы под запросы
        cur.execute("CREATE INDEX IF NOT EXISTS idx_vacancies_employer ON vacancies (employer_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_vacancies_name_trgm ON vacancies USING gin (name gin_trgm_ops);")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_salary_avg ON vacancies ((coalesce((salary_from+salary_to)/2, salary_from, salary_to)));"
        )
    conn.close()
