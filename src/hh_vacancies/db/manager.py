from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

import psycopg2
from psycopg2.extras import execute_values
from psycopg2.extensions import connection as PGConnection

def _clean(s: str) -> str:
    return s.replace("\ufeff", "").replace("\xa0", " ").strip()


def env(key: str, default: Optional[str] = None) -> str:
    v = os.getenv(key, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {key}")
    return _clean(v)


def get_conn() -> PGConnection:
    return psycopg2.connect(
        host=env("PG_HOST"),
        port=int(env("PG_PORT", "5432")),
        user=env("PG_USER"),
        password=env("PG_PASSWORD"),
        dbname=env("PG_DATABASE"),
    )


class DBManager:
    """
    Класс для работы с БД PostgreSQL (psycopg2).
    Содержит требуемые методы по ТЗ и вспомогательные методы загрузки данных.
    """

    # ---------- Загрузка данных ----------
    def upsert_employers(self, rows: Sequence[Tuple[int, str, str, Optional[str], Optional[int]]]) -> None:
        """
        Вставляет/обновляет работодателей по hh_id.
        :param rows: [(hh_id, name, url, area, open_vacancies), ...]
        """
        sql = """
        INSERT INTO employers (hh_id, name, url, area, open_vacancies)
        VALUES %s
        ON CONFLICT (hh_id) DO UPDATE
        SET name = EXCLUDED.name,
            url = EXCLUDED.url,
            area = EXCLUDED.area,
            open_vacancies = EXCLUDED.open_vacancies
        """
        with get_conn() as conn, conn.cursor() as cur:
            execute_values(cur, sql, rows)

    def insert_vacancies(
        self,
        rows: Sequence[
            Tuple[
                int,
                str,
                str,
                Optional[str],
                Optional[float],
                Optional[float],
                Optional[str],
                Optional[str],
                Optional[str],
            ]
        ],
    ) -> None:
        """
        Вставляет вакансии.
        :param rows: [(employer_id, name, url, published_at_iso, salary_from, salary_to, currency, requirement, responsibility), ...]
        """
        sql = """
        INSERT INTO vacancies
        (employer_id, name, url, published_at, salary_from, salary_to, currency, requirement, responsibility)
        VALUES %s
        ON CONFLICT (url) DO NOTHING
        """
        with get_conn() as conn, conn.cursor() as cur:
            execute_values(cur, sql, rows)

    def map_hh_ids_to_internal_ids(self) -> dict[int, int]:
        """Возвращает словарь {hh_id: employers.id}."""
        sql = "SELECT hh_id, id FROM employers;"
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return {hh_id: eid for hh_id, eid in cur.fetchall()}

    # ---------- Методы по ТЗ ----------
    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Возвращает список (company_name, vacancies_count).
        """
        sql = """
        SELECT e.name, COUNT(v.id) AS vacancies_count
        FROM employers e
        LEFT JOIN vacancies v ON v.employer_id = e.id
        GROUP BY e.id
        ORDER BY vacancies_count DESC, e.name;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return [(r[0], int(r[1])) for r in cur.fetchall()]

    def get_all_vacancies(
        self,
    ) -> List[Tuple[str, str, Optional[float], Optional[float], Optional[str], str]]:
        """
        Возвращает список всех вакансий:
        (company_name, vacancy_name, salary_from, salary_to, currency, url)
        """
        sql = """
        SELECT e.name, v.name, v.salary_from, v.salary_to, v.currency, v.url
        FROM vacancies v
        JOIN employers e ON e.id = v.employer_id
        ORDER BY e.name, v.name;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def get_avg_salary(self) -> Optional[float]:
        """
        Средняя зарплата: берём среднее от средней вилки, где есть данные.
        avg(coalesce((salary_from+salary_to)/2, salary_from, salary_to))
        """
        sql = """
        SELECT AVG(COALESCE((salary_from + salary_to)/2, salary_from, salary_to))::float
        FROM vacancies
        WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def get_vacancies_with_higher_salary(
        self,
    ) -> List[Tuple[str, str, Optional[float], Optional[float], Optional[str], str]]:
        """
        Возвращает вакансии, у которых средняя по вилке > средней по всем вакансиям.
        """
        sql = """
        WITH avg_all AS (
            SELECT AVG(COALESCE((salary_from + salary_to)/2, salary_from, salary_to)) AS a
            FROM vacancies
            WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
        )
        SELECT e.name, v.name, v.salary_from, v.salary_to, v.currency, v.url
        FROM vacancies v
        JOIN employers e ON e.id = v.employer_id
        CROSS JOIN avg_all
        WHERE COALESCE((v.salary_from + v.salary_to)/2, v.salary_from, v.salary_to) > avg_all.a
        ORDER BY v.name;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, str, str]]:
        """
        Возвращает (company_name, vacancy_name, url) для вакансий, где в названии есть keyword (ILIKE).
        """
        sql = """
        SELECT e.name, v.name, v.url
        FROM vacancies v
        JOIN employers e ON e.id = v.employer_id
        WHERE v.name ILIKE %s
        ORDER BY e.name, v.name;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (f"%{keyword}%",))
            return cur.fetchall()
