import os
# debug_env.py
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), encoding="utf-8")


def check(k: str) -> None:
    v = os.getenv(k)
    print(f"{k} = {repr(v)}")
    if v:
        bad = [f"U+{ord(c):04X}" for c in v if c in "\ufeff\xa0"]
        if bad:
            print("  -> ВНИМАНИЕ: найдены мусорные символы:", bad)


for key in ["PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DATABASE"]:
    check(key)
