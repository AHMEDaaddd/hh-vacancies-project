HH Vacancies → PostgreSQL (Курсовой проект 3, Skypro)

Скрипт собирает вакансии с hh.ru по списку компаний, загружает их в PostgreSQL, а затем позволяет выполнять аналитические запросы через CLI (консольное меню).
Проект оформлен с типизацией, линтингом и автосозданием таблиц/индексов.

TL;DR (быстрый старт)
# В корне проекта
poetry install
Copy-Item .env.example .env   # и отредактируй .env

poetry run python main.py
# 1) Инициализировать базу и таблицы
# 2) Загрузить работодателей и вакансии из hh.ru
# 3) Запросы к базе (DBManager)

Возможности

Получение работодателей и вакансий по публичному API hh.ru (requests).

Хранение данных в PostgreSQL (psycopg2).

Конфиг через .env (python-dotenv), секреты не в коде.

Антидубликаты: UNIQUE INDEX (url) + ON CONFLICT (url) DO NOTHING.

Индексы под JOIN/поиск/агрегации; поддержка pg_trgm (если доступно).

DBManager со всеми методами по ТЗ:
get_companies_and_vacancies_count, get_all_vacancies, get_avg_salary,
get_vacancies_with_higher_salary, get_vacancies_with_keyword.

Удобное меню (CLI) и табличный вывод (tabulate).

Типизация (mypy), форматирование (black, isort), линтинг (flake8).

Структура проекта
hh-vacancies-project/
├─ pyproject.toml
├─ README.md
├─ .gitignore
├─ .flake8
├─ .env.example
├─ main.py
└─ src/
   └─ hh_vacancies/
      ├─ __init__.py
      ├─ cli.py                 # меню и сценарии
      ├─ models.py              # dataclasses для сущностей
      ├─ utils/
      │  ├─ __init__.py
      │  └─ loader.py           # сбор и загрузка данных из hh в БД
      ├─ api/
      │  ├─ __init__.py
      │  └─ hh_api.py           # клиент hh.ru
      └─ db/
         ├─ __init__.py
         ├─ setup.py            # создание БД/таблиц/индексов
         └─ manager.py          # DBManager и вставка данных

Требования

Python 3.11+ (рекомендовано 3.11/3.12; 3.13 тоже ок)

PostgreSQL 15+ (сервер и клиент psql)

Poetry 1.6+

Интернет-доступ (для API hh.ru)

Установка
poetry install


Если poetry.lock отсутствует/устарел:

poetry lock
poetry install

Настройка окружения (.env)

Скопируй .env.example → .env и заполни своими значениями:

PG_HOST=127.0.0.1
PG_PORT=5432
PG_USER=appuser
PG_PASSWORD=mypass
PG_DATABASE=hh_vacancies_db

# не обязательно — для автосоздания БД
PG_SUPERUSER=postgres
PG_SUPERPASS=postgres

HH_LOCALE=ru


Важно (Windows): сохраняй .env как UTF-8 без BOM и без «невидимых» символов.

Инициализация БД
Вариант A (автоматически из приложения)

В меню выбери 1) Инициализировать базу и таблицы.
Если в .env заданы PG_SUPERUSER/PG_SUPERPASS и есть права — БД будет создана. В любом случае создадутся таблицы/индексы.

Вариант B (вручную через psql)
-- под суперпользователем postgres
CREATE ROLE appuser WITH LOGIN PASSWORD 'mypass';
CREATE DATABASE hh_vacancies_db OWNER appuser;
GRANT ALL PRIVILEGES ON DATABASE hh_vacancies_db TO appuser;

-- опционально для быстрого ILIKE-поиска
\c hh_vacancies_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;

Запуск и использование
poetry run python main.py


Меню:

Инициализировать базу и таблицы — создаёт employers и vacancies, индексы.

Загрузить работодателей и вакансии из hh.ru — введи 10+ компаний или нажми Enter для дефолтного списка.

Запросы к базе (DBManager) — все методы по ТЗ с табличным выводом:

Компании и количество вакансий

Все вакансии (компания, должность, зарплата, ссылка)

Средняя зарплата

Вакансии выше средней

Поиск по ключевому слову в названии (например, python)

Модель данных

employers

id — PK

hh_id — ID работодателя на hh.ru (UNIQUE)

name, url, area, open_vacancies

vacancies

id — PK

employer_id — FK → employers(id) (ON DELETE CASCADE)

name, url (UNIQUE), published_at, salary_from, salary_to, currency, requirement, responsibility

Индексы:

idx_vacancies_employer (employer_id)

uq_vacancy_url (url UNIQUE)

idx_vacancies_name_trgm (если есть pg_trgm) или idx_vacancies_name_lower

idx_salary_avg на выражении coalesce((from+to)/2, from, to)

Качество кода
# автоформатирование
poetry run black . -l 120
poetry run isort . --profile black --line-length 120

# линтинг
poetry run flake8

# типы
poetry run mypy src --explicit-package-bases


В проект добавлены стабы: types-requests, types-tabulate.
Конфигурации: .flake8 (лимит строки 120), [tool.black] и [tool.isort] в pyproject.toml.

Полезные SQL-проверки
-- всего строк
SELECT COUNT(*) FROM employers;
SELECT COUNT(*) FROM vacancies;

-- ТОП компаний по числу вакансий
SELECT e.name, COUNT(v.id) AS c
FROM employers e LEFT JOIN vacancies v ON v.employer_id = e.id
GROUP BY e.id
ORDER BY c DESC
LIMIT 10;

-- средняя зарплата по всем вакансиям, где она указана
SELECT AVG(COALESCE((salary_from + salary_to)/2, salary_from, salary_to))
FROM vacancies
WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;

-- поиск по ключевому слову
SELECT e.name, v.name, v.url
FROM vacancies v JOIN employers e ON e.id = v.employer_id
WHERE v.name ILIKE '%python%'
LIMIT 10;

Типичные проблемы и решения

UnicodeDecodeError ... 0xC2 при подключении к БД
В .env попал «неразрывный пробел» или BOM. Пересохрани .env как UTF-8 без BOM, набери значения руками.
В коде есть «очистка» переменных (_clean()), но лучше иметь чистый .env.

UndefinedObject: gin_trgm_ops при инициализации
Нет расширения pg_trgm.
Либо установить CREATE EXTENSION IF NOT EXISTS pg_trgm;, либо проект создаст fallback-индекс lower(name) и продолжит работу.

Повторная загрузка добавляет дубли
Создан UNIQUE INDEX (url) и используется ON CONFLICT (url) DO NOTHING.
Старые дубли можно убрать:

WITH d AS (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY url ORDER BY id) rn
  FROM vacancies
)
DELETE FROM vacancies v USING d WHERE v.id = d.id AND d.rn > 1;


FATAL: password authentication failed
Проверь логин/пароль из .env; попробуй войти через psql теми же данными.
При необходимости: ALTER ROLE appuser WITH PASSWORD 'новыйпароль';

Windows вывод «кракозябр»
В PowerShell/консоли: chcp 65001 перед запуском.

Экспорт в CSV (опционально)

Если нужно показать «модуль работы с файлами», можно добавить простую выгрузку:

# пример запроса в CSV
\copy (
  SELECT e.name AS company, v.name AS vacancy, v.salary_from, v.salary_to, v.currency, v.url
  FROM vacancies v JOIN employers e ON e.id = v.employer_id
) TO 'vacancies.csv' WITH CSV HEADER ENCODING 'UTF8';