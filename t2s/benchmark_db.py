"""Построение баз SQLite для собственного бенчмарка.

Данные генерируются детерминированно (фиксированный seed), поэтому эталонные
ответы на вопросы из benchmark/questions.jsonl воспроизводимы на любой машине.

Запуск:  python -m t2s.benchmark_db --out benchmark/dbs
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = 42

FIRST_NAMES = [
    "Alexei", "Maria", "Ivan", "Olga", "Dmitry", "Anna", "Sergei", "Elena",
    "Nikolai", "Tatiana", "Pavel", "Irina", "Mikhail", "Natalia", "Andrei",
    "Svetlana", "Artem", "Yulia", "Kirill", "Daria", "Roman", "Polina",
    "Egor", "Ksenia", "Maxim", "Sofia", "Denis", "Vera", "Gleb", "Alina",
]
LAST_NAMES = [
    "Ivanov", "Smirnov", "Kuznetsov", "Popov", "Vasiliev", "Petrov",
    "Sokolov", "Mikhailov", "Novikov", "Fedorov", "Morozov", "Volkov",
    "Alekseev", "Lebedev", "Semenov", "Egorov", "Pavlov", "Kozlov",
    "Stepanov", "Nikolaev", "Orlov", "Andreev", "Makarov", "Zaitsev",
]
CITIES = ["Moscow", "Kazan", "Yekaterinburg", "Novosibirsk", "Samara", "Perm"]


def _person(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def _rand_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


# --------------------------------------------------------------------------- shop
SHOP_SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    is_premium INTEGER NOT NULL
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""

PRODUCT_CATALOG = {
    "Electronics": (["Laptop", "Smartphone", "Headphones", "Monitor", "Tablet",
                     "Smartwatch", "Camera", "Speaker"], (150, 900)),
    "Books": (["Python Guide", "SQL Cookbook", "Data Science Handbook", "Novel",
               "History Atlas", "Poetry Collection", "Math Workbook", "Comics"], (5, 40)),
    "Clothing": (["Jacket", "Sneakers", "T-shirt", "Jeans", "Hoodie", "Scarf",
                  "Cap", "Dress"], (20, 150)),
    "Home": (["Coffee Maker", "Lamp", "Blender", "Pillow", "Vacuum Cleaner",
              "Kettle", "Mirror", "Rug"], (15, 300)),
    "Sports": (["Yoga Mat", "Dumbbells", "Bicycle Helmet", "Tennis Racket",
                "Running Shorts", "Water Bottle", "Ski Goggles", "Football"], (10, 250)),
}


def build_shop(conn: sqlite3.Connection, rng: random.Random) -> None:
    conn.executescript(SHOP_SCHEMA)
    start, end = date(2024, 1, 1), date(2025, 12, 31)

    customers = []
    for cid in range(1, 121):
        customers.append((cid, _person(rng), rng.choice(CITIES),
                          _rand_date(rng, date(2022, 1, 1), date(2025, 6, 30)).isoformat(),
                          1 if rng.random() < 0.25 else 0))
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers)

    products, pid = [], 1
    for category, (names, (lo, hi)) in PRODUCT_CATALOG.items():
        for name in names:
            price = round(rng.uniform(lo, hi), 2)
            products.append((pid, name, category, price, rng.randint(0, 200)))
            pid += 1
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

    # Клиенты 101..120 никогда не делают заказов, товары 37..40 никто не покупает —
    # это нужно для вопросов вида «кто никогда не...».
    buyers = list(range(1, 101))
    sellable = [p for p in products if p[0] <= 36]
    statuses = ["delivered"] * 6 + ["shipped"] * 2 + ["pending", "cancelled"]
    orders, items = [], []
    for oid in range(1, 501):
        orders.append((oid, rng.choice(buyers), _rand_date(rng, start, end).isoformat(),
                       rng.choice(statuses)))
        for prod in rng.sample(sellable, rng.randint(1, 4)):
            items.append((oid, prod[0], rng.randint(1, 5), prod[3]))
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?)", items)


# --------------------------------------------------------------------- university
UNIVERSITY_SCHEMA = """
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    building TEXT NOT NULL
);
CREATE TABLE teachers (
    teacher_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    hire_year INTEGER NOT NULL
);
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    enrollment_year INTEGER NOT NULL,
    scholarship INTEGER NOT NULL
);
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL,
    teacher_id INTEGER REFERENCES teachers(teacher_id)
);
CREATE TABLE enrollments (
    student_id INTEGER NOT NULL REFERENCES students(student_id),
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    grade INTEGER,
    semester TEXT NOT NULL
);
"""

DEPARTMENTS = [
    ("Computer Science", "A"), ("Mathematics", "B"), ("Physics", "B"),
    ("Economics", "C"), ("Linguistics", "D"),
]
COURSE_TITLES = [
    "Databases", "Algorithms", "Operating Systems", "Computer Networks",
    "Machine Learning", "Linear Algebra", "Calculus", "Probability Theory",
    "Discrete Mathematics", "Mechanics", "Electrodynamics", "Quantum Physics",
    "Microeconomics", "Macroeconomics", "Econometrics", "English for IT",
    "Technical Writing", "Compiler Design", "Computer Graphics", "Statistics",
    "Cryptography", "Game Theory",
]
GROUPS = ["IT-301", "IT-302", "IT-303", "MATH-201", "PHYS-101", "ECON-401"]


def build_university(conn: sqlite3.Connection, rng: random.Random) -> None:
    conn.executescript(UNIVERSITY_SCHEMA)
    conn.executemany("INSERT INTO departments VALUES (?,?,?)",
                     [(i + 1, n, b) for i, (n, b) in enumerate(DEPARTMENTS)])

    # Кафедре Linguistics достаётся только 2 преподавателя — вопросы с HAVING.
    teachers = []
    for tid in range(1, 23):
        dep = rng.choice([1, 1, 2, 2, 3, 4, 4]) if tid > 2 else 5
        teachers.append((tid, _person(rng), dep, rng.randint(2000, 2024)))
    conn.executemany("INSERT INTO teachers VALUES (?,?,?,?)", teachers)

    students = []
    for sid in range(1, 151):
        students.append((sid, _person(rng), rng.choice(GROUPS), rng.randint(2021, 2025),
                         1 if rng.random() < 0.4 else 0))
    conn.executemany("INSERT INTO students VALUES (?,?,?,?,?)", students)

    # Преподаватели 19..22 курсов не ведут; курсы 21..22 никто не выбрал.
    courses = []
    for cid, title in enumerate(COURSE_TITLES, start=1):
        courses.append((cid, title, rng.randint(2, 6), rng.randint(1, 18)))
    conn.executemany("INSERT INTO courses VALUES (?,?,?,?)", courses)

    enrollments = []
    for sid in range(1, 151):
        for cid in rng.sample(range(1, 21), rng.randint(3, 7)):
            grade = rng.choices([2, 3, 4, 5], weights=[1, 3, 4, 3])[0]
            semester = rng.choice(["2024-fall", "2025-spring", "2025-fall"])
            enrollments.append((sid, cid, grade, semester))
    conn.executemany("INSERT INTO enrollments VALUES (?,?,?,?)", enrollments)


# ------------------------------------------------------------------------ library
LIBRARY_SCHEMA = """
CREATE TABLE authors (
    author_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    birth_year INTEGER NOT NULL
);
CREATE TABLE books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES authors(author_id),
    genre TEXT NOT NULL,
    published_year INTEGER NOT NULL,
    pages INTEGER NOT NULL
);
CREATE TABLE readers (
    reader_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    join_year INTEGER NOT NULL
);
CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(book_id),
    reader_id INTEGER NOT NULL REFERENCES readers(reader_id),
    loan_date TEXT NOT NULL,
    return_date TEXT
);
"""

AUTHORS = [
    ("Anna Volkova", "Russia"), ("Boris Lebedev", "Russia"), ("Clara Stone", "UK"),
    ("David Reyes", "Spain"), ("Emma Larsen", "Norway"), ("Felix Wagner", "Germany"),
    ("Grace Chen", "USA"), ("Hugo Martin", "France"), ("Irina Sokolova", "Russia"),
    ("James Carter", "USA"), ("Kenji Sato", "Japan"), ("Lena Fischer", "Germany"),
]
GENRES = ["Fantasy", "Detective", "Science Fiction", "Classic", "Biography", "Poetry"]
TITLE_A = ["The Silent", "The Last", "A Hidden", "The Broken", "The Golden", "A Distant",
           "The Forgotten", "The Burning", "A Quiet", "The Endless"]
TITLE_B = ["River", "Kingdom", "Garden", "Signal", "Mirror", "Winter", "Harbor",
           "Library", "Mountain", "Voyage"]


def build_library(conn: sqlite3.Connection, rng: random.Random) -> None:
    conn.executescript(LIBRARY_SCHEMA)
    conn.executemany("INSERT INTO authors VALUES (?,?,?,?)",
                     [(i + 1, n, c, rng.randint(1820, 1990)) for i, (n, c) in enumerate(AUTHORS)])

    titles = [f"{a} {b}" for a in TITLE_A for b in TITLE_B]
    rng.shuffle(titles)
    books = []
    for bid in range(1, 81):
        books.append((bid, titles[bid - 1], rng.randint(1, 12), rng.choice(GENRES),
                      rng.randint(1890, 2024), rng.randint(90, 900)))
    conn.executemany("INSERT INTO books VALUES (?,?,?,?,?,?)", books)

    readers = [(rid, _person(rng), rng.choice(CITIES), rng.randint(2018, 2025))
               for rid in range(1, 91)]
    conn.executemany("INSERT INTO readers VALUES (?,?,?,?)", readers)

    # Книги авторов 11 и 12 никто не брал.
    borrowable = [b[0] for b in books if b[2] not in (11, 12)]
    weights = [rng.random() ** 2 + 0.05 for _ in borrowable]
    loans = []
    for lid in range(1, 601):
        loan_day = _rand_date(rng, date(2024, 1, 1), date(2025, 12, 31))
        returned = rng.random() < 0.8 or loan_day < date(2025, 9, 1)
        ret = (loan_day + timedelta(days=rng.randint(3, 45))).isoformat() if returned else None
        loans.append((lid, rng.choices(borrowable, weights=weights)[0],
                      rng.randint(1, 90), loan_day.isoformat(), ret))
    conn.executemany("INSERT INTO loans VALUES (?,?,?,?,?)", loans)


BUILDERS = {"shop": build_shop, "university": build_university, "library": build_library}


def build_all(out_dir: str | Path, overwrite: bool = False) -> dict[str, Path]:
    """Создаёт все базы бенчмарка и возвращает {имя: путь}."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for i, (name, builder) in enumerate(BUILDERS.items()):
        path = out / f"{name}.sqlite"
        paths[name] = path
        if path.exists() and not overwrite:
            continue
        path.unlink(missing_ok=True)
        conn = sqlite3.connect(path)
        try:
            builder(conn, random.Random(SEED + i))
            conn.commit()
        finally:
            conn.close()
    return paths


def schema_of(db_path: str | Path) -> str:
    """Схема базы в виде CREATE TABLE — ровно то, что видит модель в промпте."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' ORDER BY rowid").fetchall()
    finally:
        conn.close()
    return "\n".join(r[0].strip() + ";" for r in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="benchmark/dbs")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    for name, path in build_all(args.out, args.overwrite).items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
