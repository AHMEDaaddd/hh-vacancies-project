from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Employer:
    """Модель работодателя (данные с HH)."""

    hh_id: int
    name: str
    url: str
    area: Optional[str] = None
    open_vacancies: Optional[int] = None


@dataclass(frozen=True)
class Vacancy:
    """Модель вакансии (данные с HH)."""

    employer_hh_id: int
    name: str
    url: str
    published_at: Optional[datetime]
    salary_from: Optional[float]
    salary_to: Optional[float]
    currency: Optional[str]
    requirement: Optional[str]
    responsibility: Optional[str]
