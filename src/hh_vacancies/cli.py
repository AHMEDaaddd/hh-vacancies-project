from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv
from tabulate import tabulate

from hh_vacancies.db.manager import DBManager
from hh_vacancies.db.setup import create_database_if_needed, create_tables
from hh_vacancies.utils.loader import collect_and_load_companies_and_vacancies


def _print_title(s: str) -> None:
    print("\n" + "=" * 80)
    print(s)
    print("=" * 80)


def initialize_database() -> None:
    _print_title("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    created, dbname = create_database_if_needed()
    print(f"База данных: {dbname} ({'создана' if created else 'существует/нет прав на создание'})")
    create_tables()
    print("Таблицы готовы.")


def seed_and_load() -> None:
    _print_title("ЗАГРУЗКА ДАННЫХ ИЗ HH.RU")

    default_companies = [
        "Яндекс",
        "Сбер",
        "Т-Банк",
        "VK",
        "Ozon",
        "Авито",
        "MTS",
        "Альфа-Банк",
        "X5 Group",
        "Тинькофф Инвестиции",
    ]
    print("По умолчанию будут использованы такие компании:")
    for c in default_companies:
        print(" -", c)
    print("\nМожно ввести свои компании через запятую или нажать Enter, чтобы оставить по умолчанию:")
    user_input = input("Компании: ").strip()
    companies: List[str] = [s.strip() for s in user_input.split(",") if s.strip()] if user_input else default_companies

    collect_and_load_companies_and_vacancies(companies, max_pages=3)
    print("Готово. Данные загружены.")


def run_queries() -> None:
    _print_title("ЗАПРОСЫ К БД")
    db = DBManager()
    while True:
        print(
            """
1) Список компаний и количество вакансий
2) Все вакансии (компания, вакансия, зарплата, ссылка)
3) Средняя зарплата по всем вакансиям
4) Вакансии с зарплатой выше средней
5) Поиск вакансий по ключевому слову в названии
0) Назад
"""
        )
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            rows = db.get_companies_and_vacancies_count()
            print(tabulate(rows, headers=["Компания", "Количество вакансий"], tablefmt="github"))
        elif choice == "2":
            rows = db.get_all_vacancies()
            hdr = ["Компания", "Вакансия", "От", "До", "Валюта", "Ссылка"]
            print(tabulate(rows, headers=hdr, tablefmt="github"))
        elif choice == "3":
            avg = db.get_avg_salary()
            print(f"Средняя зарплата: {avg:.2f}" if avg is not None else "Данных по зарплатам нет.")
        elif choice == "4":
            rows = db.get_vacancies_with_higher_salary()
            hdr = ["Компания", "Вакансия", "От", "До", "Валюта", "Ссылка"]
            print(tabulate(rows, headers=hdr, tablefmt="github"))
        elif choice == "5":
            kw = input("Ключевое слово (например, python): ").strip()
            rows = db.get_vacancies_with_keyword(kw)
            print(tabulate(rows, headers=["Компания", "Вакансия", "Ссылка"], tablefmt="github"))
        elif choice == "0":
            break
        else:
            print("Неверный выбор.")


def run_cli() -> None:
    load_dotenv(encoding="utf-8")  # так и должно быть
    while True:
        _print_title("HH ВАКАНСИИ — МЕНЮ")
        print(
            """
1) Инициализировать базу и таблицы
2) Загрузить работодателей и вакансии из hh.ru
3) Запросы к базе (DBManager)
0) Выход
"""
        )
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            initialize_database()
        elif choice == "2":
            seed_and_load()
        elif choice == "3":
            run_queries()
        elif choice == "0":
            print("Пока!")
            break
        else:
            print("Неверный выбор.")
