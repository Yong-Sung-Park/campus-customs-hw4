"""SQLite access for the Campus Customs catalogue.

All paths are resolved from this file, so the backend works no matter which
folder uvicorn is started from.
"""

import json
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from difflib import SequenceMatcher
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCTS_DIR = DATA_DIR / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# garment_type is spelled 22 different ways in the data; these are the
# shopper-facing categories it is normalized to (checked in this order).
CATEGORIES = ["hoodie", "crewneck", "quarter-zip", "jacket", "t-shirt", "long-sleeve"]
_CATEGORY_RULES = [
    ("quarter-zip", ("quarter-zip", "1/4 zip", "1-4 zip", "¼")),
    ("jacket", ("jacket",)),
    ("hoodie", ("hood",)),
    ("t-shirt", ("t-shirt", "tee")),
    ("long-sleeve", ("long-sleeve", "long sleeve")),
    ("crewneck", ("crewneck", "crew neck", "mockneck", "sweatshirt", "sweater")),
]

COLOR_SYNONYMS = {
    "grey": ["gray"],
    "gray": ["gray", "charcoal"],
    "blue": ["blue", "navy"],
    "navy": ["navy"],
    "white": ["white", "ivory", "cream"],
    "red": ["red", "coral"],
}

_STOPWORDS = {
    "a", "an", "the", "any", "some", "with", "for", "of", "and", "or", "in", "on", "do", "you", "have",
    "got", "yale", "campus", "customs", "merch", "gear", "item", "items", "something", "stuff", "show",
    "me", "what", "which", "your", "i", "want", "need", "looking",
}


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def image_url(image_file_path: str) -> str:
    # catalogue stores "products/<id>.jpg"; FastAPI serves data/products at /media/products
    return f"/media/{image_file_path}"


def category_of(garment_type: str, name: str = "") -> str:
    text = f"{garment_type} {name}".lower()
    for category, needles in _CATEGORY_RULES:
        if any(n in text for n in needles):
            return category
    return "other"


def short_description(text: str, limit: int = 110) -> str:
    if len(text) <= limit:
        return text
    return text[: text.rfind(" ", 0, limit)].rstrip(",;") + "…"


def _sort_sizes(sizes: list[dict]) -> list[dict]:
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)


def _product_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": category_of(row["garment_type"], row["name"]),
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_url": image_url(row["image_file_path"]),
        "price": row["price"],
    }


def _all_products_with_inventory() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inv = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    by_product: dict[str, list[dict]] = {}
    for r in inv:
        by_product.setdefault(r["product_id"], []).append({"size": r["size"], "quantity": r["quantity"]})
    products = []
    for r in rows:
        p = _product_row_to_dict(r)
        p["inventory"] = _sort_sizes(by_product.get(p["product_id"], []))
        p["total_stock"] = sum(s["quantity"] for s in p["inventory"])
        products.append(p)
    return products


def list_products() -> list[dict]:
    products = _all_products_with_inventory()
    for p in products:
        p["sizes_in_stock"] = [s["size"] for s in p.pop("inventory") if s["quantity"] > 0]
    return products


def get_product(product_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        product = _product_row_to_dict(row)
        inv = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    product["inventory"] = _sort_sizes([{"size": r["size"], "quantity": r["quantity"]} for r in inv])
    product["total_stock"] = sum(s["quantity"] for s in product["inventory"])
    return product


def card(product: dict) -> dict:
    """The small shape the front end renders as a product card."""
    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "price": product["price"],
        "image_url": product["image_url"],
        "short_description": short_description(product["description"]),
    }


# ---------- lookup by name ----------

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def resolve_product(ref: str) -> tuple[dict | None, list[str]]:
    """Find a product by id or (approximate) name.

    Returns (product, []) on a confident match, or (None, [up to 3 close names])
    so the caller can ask "did you mean ...?" instead of guessing.
    """
    ref_n = _norm(ref)
    if not ref_n:
        return None, []
    products = _all_products_with_inventory()
    for p in products:
        if ref_n in (_norm(p["product_id"]), _norm(p["name"])):
            return get_product(p["product_id"]), []

    def score(p: dict) -> float:
        name_n = _norm(p["name"])
        ratio = SequenceMatcher(None, ref_n, name_n).ratio()
        words = set(ref_n.split())
        overlap = len(words & set(name_n.split())) / max(len(words), 1)
        return max(ratio, overlap * 0.95)

    ranked = sorted(products, key=score, reverse=True)
    best = score(ranked[0])
    second = score(ranked[1]) if len(ranked) > 1 else 0
    if best >= 0.85 and best - second >= 0.05:
        return get_product(ranked[0]["product_id"]), []
    return None, [p["name"] for p in ranked[:3] if score(p) >= 0.35]


# ---------- search ----------

def _tokens(text: str) -> list[str]:
    words = [w for w in _norm(text).split() if w not in _STOPWORDS]
    # cheap plural handling: hoodies -> hoodie, tees -> tee
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words]


def _color_matches(wanted: str, colors: list[str]) -> bool:
    wanted = _norm(wanted)
    needles = COLOR_SYNONYMS.get(wanted, [wanted])
    return any(n in c.lower() for c in colors for n in needles)


def search_products(
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size_in_stock: str | None = None,
    limit: int = 8,
) -> tuple[list[dict], int]:
    """Text + filter search over the catalogue. Returns (top matches, total matches)."""
    tokens = _tokens(query)
    results = []
    for p in _all_products_with_inventory():
        if category and p["category"] != category:
            continue
        if color and not _color_matches(color, p["colors"]):
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if size_in_stock and not any(s["size"] == size_in_stock and s["quantity"] > 0 for s in p["inventory"]):
            continue

        score = 0.0
        if tokens:
            name = _norm(p["name"])
            tags = _norm(" ".join(p["search_tags"]))
            kind = _norm(f"{p['garment_type']} {p['category']}")
            colors = _norm(" ".join(p["colors"]))
            desc = _norm(p["description"])
            for t in tokens:
                hit = 3 * (t in name) + 3 * (t in kind) + 2 * (t in tags) + 2 * (t in colors) + 1 * (t in desc)
                score += hit
            if score == 0:
                continue
        results.append((score, p["total_stock"] > 0, p))

    results.sort(key=lambda r: (-r[0], not r[1], r[2]["price"]))
    return [r[2] for r in results[:limit]], len(results)


def summarize(p: dict) -> dict:
    """Compact product facts for tool results (keeps agent context small)."""
    return {
        "product_id": p["product_id"],
        "name": p["name"],
        "category": p["category"],
        "price": p["price"],
        "colors": p["colors"],
        "sizes_in_stock": [s["size"] for s in p["inventory"] if s["quantity"] > 0],
        "short_description": short_description(p["description"]),
    }


# ---------- chat history (Problem 8) ----------

def save_chat_message(user_id: int, role: str, content: str, products: list[dict] | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, json.dumps(products) if products else None),
        )


def load_chat_history(user_id: int, limit: int = 50) -> list[dict]:
    """The user's most recent messages, oldest first. Cards are rebuilt from the
    catalogue by product_id so prices are current even for old messages."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    history = []
    for r in reversed(rows):
        cards = []
        for item in json.loads(r["products_json"] or "[]"):
            product = get_product(item.get("product_id", "")) if isinstance(item, dict) else None
            if product:
                cards.append(card(product))
        history.append({"role": r["role"], "content": r["content"], "products": cards, "created_at": r["created_at"]})
    return history


# ---------- alternatives (Problem 9) ----------

def find_alternatives(product: dict, size: str, limit: int = 4) -> list[dict]:
    """Other items in the same category that have `size` in stock, most similar first."""
    base_words = set(_tokens(" ".join(product["search_tags"] + product["colors"])))
    candidates = []
    for p in _all_products_with_inventory():
        if p["product_id"] == product["product_id"] or p["category"] != product["category"]:
            continue
        if not any(s["size"] == size and s["quantity"] > 0 for s in p["inventory"]):
            continue
        overlap = len(base_words & set(_tokens(" ".join(p["search_tags"] + p["colors"]))))
        candidates.append((-overlap, abs(p["price"] - product["price"]), p))
    candidates.sort(key=lambda c: (c[0], c[1]))
    return [c[2] for c in candidates[:limit]]
