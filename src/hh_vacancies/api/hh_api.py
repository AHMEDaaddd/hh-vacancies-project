from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple, Union

import requests

BASE = "https://api.hh.ru"


class HHClient:
    """Клиент для работы с публичным API hh.ru (без токена)."""

    def __init__(self, locale: str = "ru", pause_sec: float = 0.2) -> None:
        self.locale = locale
        self.pause_sec = pause_sec
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "hh-vacancies-edu-project/1.0 (+https://github.com/you)",
                "Accept": "application/json",
            }
        )

    def search_employers(self, names: Iterable[str], per_name: int = 1) -> Dict[str, Tuple[int, str]]:
        """
        Находит работодателей по именам.

        :param names: список имён компаний (строки).
        :param per_name: сколько топ-совпадений возвращать на имя (используем 1).
        :return: словарь {имя_из_входа: (hh_id, html_url)}
        """
        result: Dict[str, Tuple[int, str]] = {}
        for name in names:
            params: dict[str, Union[str, int]] = {"text": name, "per_page": per_name}
            resp = self.session.get(f"{BASE}/employers", params=params, timeout=20)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if not items:
                continue
            emp = items[0]
            hh_id = int(emp["id"])
            alt_url = emp.get("alternate_url") or f"https://hh.ru/employer/{hh_id}"
            result[name] = (hh_id, alt_url)
            time.sleep(self.pause_sec)
        return result

    def get_employer_info(self, hh_id: int) -> Dict[str, Any]:
        """Возвращает детальную информацию по работодателю."""
        resp = self.session.get(f"{BASE}/employers/{hh_id}", timeout=20)
        resp.raise_for_status()
        time.sleep(self.pause_sec)
        return resp.json()

    def iter_vacancies_by_employer(
            self, hh_id: int, per_page: int = 50, max_pages: int = 5
    ) -> Iterator[Dict[str, Any]]:
        """
        Итерирует вакансии работодателя постранично (ограничиваем по max_pages для проекта).
        """
        page = 0
        while page < max_pages:
            params: dict[str, int] = {"employer_id": hh_id, "per_page": per_page, "page": page}
            resp = self.session.get(f"{BASE}/vacancies", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            for v in items:
                yield v
            page += 1
            if page >= data.get("pages", 0):
                break
            time.sleep(self.pause_sec)

    @staticmethod
    def parse_salary(s: Optional[dict]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        if not s:
            return None, None, None
        return s.get("from"), s.get("to"), s.get("currency")

    @staticmethod
    def parse_dt(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        # hh.ru публикует ISO 8601
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
