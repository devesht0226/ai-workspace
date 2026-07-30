"""SQL Assistant: schema-aware NL→SQL with safe read-only execution."""

from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.models import UsageEvent, User
from app.providers.llm import ChatMessage, get_llm_provider

SAMPLE_SCHEMA = """
Tables:
- customers(id INTEGER PK, name TEXT, email TEXT, country TEXT)
- orders(id INTEGER PK, customer_id INTEGER FK→customers.id, product TEXT, amount REAL, created_at TEXT)
- products(id INTEGER PK, name TEXT, category TEXT, price REAL)

IMPORTANT:
- orders.product is TEXT (product name), NOT a foreign key. There is NO orders.product_id.
- To join orders→products use: orders.product = products.name
- The only FK is orders.customer_id → customers.id
- Prefer the simplest correct SELECT. Do not invent columns.
"""

# Canonical columns for post-generation validation (tiny models often invent FKs)
_SCHEMA_COLUMNS: dict[str, set[str]] = {
    "customers": {"id", "name", "email", "country"},
    "orders": {"id", "customer_id", "product", "amount", "created_at"},
    "products": {"id", "name", "category", "price"},
}

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|INTO)\b",
    re.IGNORECASE,
)
_QUALIFIED_COLUMN = re.compile(
    r"\b(customers|orders|products)\s*\.\s*([a-zA-Z_][a-zA-Z0-9_]*)\b",
    re.IGNORECASE,
)


def _demo_db_path() -> Path:
    path = Path(get_settings().upload_dir) / "demo_analytics.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ensure_demo_db() -> Path:
    path = _demo_db_path()
    if path.exists():
        return path
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE customers (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              email TEXT NOT NULL,
              country TEXT NOT NULL
            );
            CREATE TABLE products (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              category TEXT NOT NULL,
              price REAL NOT NULL
            );
            CREATE TABLE orders (
              id INTEGER PRIMARY KEY,
              customer_id INTEGER NOT NULL REFERENCES customers(id),
              product TEXT NOT NULL,
              amount REAL NOT NULL,
              created_at TEXT NOT NULL
            );
            INSERT INTO customers VALUES
              (1,'Ada Lovelace','ada@example.com','UK'),
              (2,'Alan Turing','alan@example.com','UK'),
              (3,'Grace Hopper','grace@example.com','US');
            INSERT INTO products VALUES
              (1,'Laptop','Hardware',1200),
              (2,'Notebook','Stationery',12),
              (3,'Cloud Seat','Software',29);
            INSERT INTO orders VALUES
              (1,1,'Laptop',1200,'2026-01-10'),
              (2,1,'Cloud Seat',29,'2026-02-01'),
              (3,2,'Notebook',12,'2026-02-11'),
              (4,3,'Laptop',1200,'2026-03-01'),
              (5,3,'Cloud Seat',58,'2026-03-15');
            """
        )
        conn.commit()
    finally:
        conn.close()
    return path


def get_schema() -> dict:
    ensure_demo_db()
    return {
        "dialect": "sqlite",
        "description": "Read-only demo analytics schema for SQL Assistant",
        "schema_text": SAMPLE_SCHEMA.strip(),
        "tables": [
            {
                "name": "customers",
                "columns": ["id", "name", "email", "country"],
            },
            {
                "name": "products",
                "columns": ["id", "name", "category", "price"],
            },
            {
                "name": "orders",
                "columns": ["id", "customer_id", "product", "amount", "created_at"],
            },
        ],
    }


def schema_er_graph() -> dict:
    """Return a lightweight graph representation of the demo schema."""
    return {
        "nodes": [
            {"id": "customers", "label": "customers", "type": "table"},
            {"id": "orders", "label": "orders", "type": "table"},
            {"id": "products", "label": "products", "type": "table"},
        ],
        "edges": [
            {
                "source": "orders",
                "target": "customers",
                "label": "customer_id → customers.id",
            }
        ],
    }


def export_results_csv(columns: list[str], rows: list[dict]) -> str:
    """Serialize SQL result rows safely and consistently as CSV."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _track(db: Session, user: User, event_type: str, meta: dict | None = None) -> None:
    db.add(
        UsageEvent(
            user_id=user.id,
            event_type=event_type,
            model_name=get_settings().ollama_chat_model,
            metadata_json=meta or {},
        )
    )
    db.commit()


def _extract_sql(text: str) -> str:
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    sql = fence.group(1).strip() if fence else text.strip()
    sql = sql.rstrip(";")
    return sql


def _heuristic_sql(question: str) -> str | None:
    """Reliable templates for common demo questions (small local models hallucinate FKs)."""
    q = question.lower()
    if any(k in q for k in ("total revenue", "total amount", "sum of", "revenue from orders")):
        return "SELECT SUM(amount) AS total_revenue FROM orders"
    if "revenue" in q and "order" in q:
        return "SELECT SUM(amount) AS total_revenue FROM orders"
    if "by country" in q or ("customer" in q and "country" in q and "count" in q):
        return "SELECT country, COUNT(*) AS customers FROM customers GROUP BY country"
    if "country" in q and ("count" in q or "how many" in q):
        return "SELECT country, COUNT(*) AS customers FROM customers GROUP BY country"
    if "top" in q and "customer" in q:
        return (
            "SELECT c.name, SUM(o.amount) AS total "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.name ORDER BY total DESC LIMIT 10"
        )
    if "list" in q and "customer" in q:
        return "SELECT name, email, country FROM customers ORDER BY name"
    if "product" in q and ("category" in q or "list" in q):
        return "SELECT name, category, price FROM products ORDER BY name"
    return None


def _unknown_columns(sql: str) -> list[str]:
    """Return qualified column refs that are not in the demo schema."""
    bad: list[str] = []
    for match in _QUALIFIED_COLUMN.finditer(sql):
        table = match.group(1).lower()
        column = match.group(2).lower()
        allowed = _SCHEMA_COLUMNS.get(table, set())
        if column not in allowed:
            bad.append(f"{table}.{column}")
    # Bare common hallucination
    if re.search(r"\bproduct_id\b", sql, re.IGNORECASE):
        if "orders.product_id" not in bad:
            bad.append("product_id")
    return bad


def generate_sql(db: Session, user: User, question: str) -> dict:
    # Prefer deterministic SQL for common questions — tinyllama invents columns like product_id
    sql = _heuristic_sql(question)
    used_heuristic = sql is not None

    if sql is None:
        llm = get_llm_provider()
        prompt = (
            "You are a SQL expert for ONE demo SQLite database. "
            "Write exactly one SELECT query. Use ONLY columns listed in the schema. "
            "Never invent columns (especially never use product_id). "
            "orders.product is TEXT; join products with orders.product = products.name if needed. "
            "Return only SQL.\n\n"
            f"SCHEMA:\n{SAMPLE_SCHEMA}\n\nQUESTION: {question}"
        )
        raw = llm.chat([ChatMessage(role="user", content=prompt)])
        sql = _extract_sql(raw)

    if get_settings().environment == "test" or get_settings().llm_provider == "fake":
        sql = _heuristic_sql(question) or (
            "SELECT name, email FROM customers ORDER BY name LIMIT 10"
        )
        used_heuristic = True

    bad = _unknown_columns(sql)
    if bad and not used_heuristic:
        fallback = _heuristic_sql(question)
        if fallback:
            sql = fallback
        else:
            # Common tiny-model mistake: invent orders.product_id FK
            fixed = re.sub(
                r"`?orders`?\s*\.\s*`?product_id`?\s*=\s*`?products`?\s*\.\s*`?id`?",
                "orders.product = products.name",
                sql,
                flags=re.IGNORECASE,
            )
            if _unknown_columns(fixed):
                raise ValidationAppError(
                    "Generated SQL used columns that are not in the demo schema "
                    f"({', '.join(bad)}). Try rephrasing, e.g. "
                    "'What is total revenue from orders?'"
                )
            sql = fixed

    _validate_readonly(sql)
    _track(
        db,
        user,
        "sql_generate",
        {"question": question, "heuristic": used_heuristic or bool(bad)},
    )
    return {"sql": sql, "question": question, "schema": get_schema()}


def explain_sql(db: Session, user: User, sql: str) -> dict:
    _validate_readonly(sql)
    llm = get_llm_provider()
    if get_settings().environment == "test" or get_settings().llm_provider == "fake":
        explanation = f"This read-only query retrieves data using: {sql}"
    else:
        explanation = llm.chat(
            [
                ChatMessage(
                    role="user",
                    content=f"Explain this SQLite SQL in plain language for a junior engineer:\n{sql}",
                )
            ]
        )
    _track(db, user, "sql_explain")
    return {"sql": sql, "explanation": explanation}


def optimize_sql(db: Session, user: User, sql: str) -> dict:
    _validate_readonly(sql)
    tips: list[str] = []
    if "SELECT *" in sql.upper():
        tips.append("Prefer explicit columns instead of SELECT *.")
    if "JOIN" not in sql.upper() and "customer" in sql.lower() and "order" in sql.lower():
        tips.append("Consider an explicit JOIN between customers and orders.")
    if "LIMIT" not in sql.upper():
        tips.append("Add LIMIT for exploratory queries.")
    if not tips:
        tips.append("Query looks reasonable for the demo schema.")
    llm = get_llm_provider()
    if get_settings().environment != "test" and get_settings().llm_provider != "fake":
        extra = llm.chat(
            [
                ChatMessage(
                    role="user",
                    content=(
                        "Suggest brief optimization tips for this SQLite SELECT "
                        f"(indexes, joins, filters):\n{sql}"
                    ),
                )
            ]
        )
        tips.append(extra.strip())
    _track(db, user, "sql_optimize")
    return {"sql": sql, "suggestions": tips}


def _validate_readonly(sql: str) -> None:
    cleaned = sql.strip()
    if not cleaned:
        raise ValidationAppError("SQL is empty")
    if _FORBIDDEN.search(cleaned):
        raise ValidationAppError("Only read-only SELECT queries are allowed")
    if not cleaned.lower().lstrip().startswith("select"):
        raise ValidationAppError("Query must start with SELECT")
    if ";" in cleaned.rstrip(";"):
        raise ValidationAppError("Multiple statements are not allowed")


def execute_sql(db: Session, user: User, sql: str, *, max_rows: int = 100) -> dict:
    _validate_readonly(sql)
    path = ensure_demo_db()
    limited = sql
    if "limit" not in sql.lower():
        limited = f"{sql} LIMIT {max_rows}"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(limited)
        rows = [dict(r) for r in cursor.fetchall()]
        columns = list(rows[0].keys()) if rows else [d[0] for d in cursor.description or []]
    except sqlite3.Error as exc:
        raise ValidationAppError(f"SQL execution failed: {exc}") from exc
    finally:
        conn.close()
    _track(db, user, "sql_execute", {"row_count": len(rows)})
    return {
        "sql": limited,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "chart_hint": {
            "type": "table",
            "x": columns[0] if columns else None,
            "y": columns[1] if len(columns) > 1 else None,
        },
    }


def dump_debug() -> str:
    return json.dumps(get_schema())
