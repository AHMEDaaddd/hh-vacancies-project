from __future__ import annotations

from typing import Iterable, List, Tuple

from hh_vacancies.api.hh_api import HHClient
from hh_vacancies.db.manager import DBManager


def collect_and_load_companies_and_vacancies(company_names: Iterable[str], max_pages: int = 3) -> None:
    """
    Ищет работодателей по именам, сохраняет их и их вакансии в БД.

    :param company_names: список названий компаний (строки).
    :param max_pages: сколько страниц вакансий брать у hh.ru на компанию.
    """
    api = HHClient()
    db = DBManager()

    found = api.search_employers(company_names, per_name=1)

    # Работодатели
    employers_rows: List[Tuple[int, str, str, str | None, int | None]] = []
    for input_name, (hh_id, alt_url) in found.items():
        info = api.get_employer_info(hh_id)
        employers_rows.append(
            (
                hh_id,
                info.get("name") or input_name,
                info.get("alternate_url") or alt_url,
                (info.get("area") or {}).get("name"),
                info.get("open_vacancies"),
            )
        )
    if employers_rows:
        db.upsert_employers(employers_rows)

    # Карта hh_id -> employers.id
    mapping = db.map_hh_ids_to_internal_ids()

    # Вакансии
    vacancy_rows: List[
        Tuple[
            int,
            str,
            str,
            str | None,
            float | None,
            float | None,
            str | None,
            str | None,
            str | None,
        ]
    ] = []

    for _, (hh_id, _) in found.items():
        for v in api.iter_vacancies_by_employer(hh_id, per_page=50, max_pages=max_pages):
            salary_from, salary_to, currency = api.parse_salary(v.get("salary"))
            published_dt = api.parse_dt(v.get("published_at"))
            published_iso = published_dt.isoformat() if published_dt else None
            snippet = v.get("snippet") or {}
            requirement = snippet.get("requirement")
            responsibility = snippet.get("responsibility")

            employer_id = mapping.get(hh_id)
            if employer_id is None:
                continue

                url = v.get("alternate_url") or v.get("url") or f"https://hh.ru/vacancy/{v.get('id')}"
                vacancy_rows.append(
                    (
                        employer_id,
                        v.get("name") or "",
                        url,
                        published_iso,
                        float(salary_from) if salary_from is not None else None,
                        float(salary_to) if salary_to is not None else None,
                        currency,
                        requirement,
                        responsibility,
                    )
                )

            vacancy_rows.append(
                (
                    employer_id,
                    v.get("name") or "",
                    v.get("alternate_url") or v.get("url") or "",
                    published_iso,
                    float(salary_from) if salary_from is not None else None,
                    float(salary_to) if salary_to is not None else None,
                    currency,
                    requirement,
                    responsibility,
                )
            )

    if vacancy_rows:
        db.insert_vacancies(vacancy_rows)
