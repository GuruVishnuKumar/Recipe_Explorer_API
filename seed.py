"""
seed.py — Parse recipes.json and populate the SQLite database.

Usage:
    python seed.py                       # looks for recipes.json in current dir
    python seed.py /path/to/recipes.json
"""

import json
import math
import re
import sys
import os

from database import engine, SessionLocal
import models
from models import Recipe


# ── NaN / type-safety helpers ─────────────────────────────────────────────────

def is_nan(value) -> bool:
    """Return True if value is NaN, None, or the string 'NaN'/'nan'."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() == "nan":
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def safe_float(value):
    """Return float or None — never lets NaN into the DB."""
    if is_nan(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value):
    """Return int or None — never lets NaN into the DB."""
    if is_nan(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def extract_calories(nutrients: dict):
    """
    Parse the integer kcal value from the nutrients dict.
    e.g. {"calories": "389 kcal"} -> 389

    Stored as a dedicated INTEGER column so calorie range queries
    are handled by SQLite's index rather than a Python-side loop.
    """
    if not nutrients:
        return None
    raw = nutrients.get("calories", "")
    if not raw:
        return None
    m = re.search(r"(\d+)", str(raw))
    return int(m.group(1)) if m else None


# ── Seeding ───────────────────────────────────────────────────────────────────

def seed(json_path: str = "recipes.json") -> None:
    if not os.path.exists(json_path):
        print(f"[ERROR] File not found: {json_path}")
        sys.exit(1)

    # Create tables if they don't exist
    models.Base.metadata.create_all(bind=engine)
    print("[INFO] Tables ready.")

    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # JSON is a dict keyed by string indices {"0": {...}, "1": {...}, ...}
    records = list(raw.values()) if isinstance(raw, dict) else raw
    print(f"[INFO] {len(records):,} records found in {json_path}")

    db = SessionLocal()
    inserted = skipped = 0

    try:
        # Idempotent: clear before re-seed so running twice is safe
        deleted = db.query(Recipe).delete()
        db.commit()
        if deleted:
            print(f"[INFO] Cleared {deleted:,} existing rows.")

        batch = []
        for item in records:
            try:
                nutrients = item.get("nutrients") or {}
                batch.append(Recipe(
                    cuisine     = item.get("cuisine"),
                    title       = item.get("title"),
                    rating      = safe_float(item.get("rating")),
                    prep_time   = safe_int(item.get("prep_time")),
                    cook_time   = safe_int(item.get("cook_time")),
                    total_time  = safe_int(item.get("total_time")),
                    description = item.get("description"),
                    serves      = item.get("serves"),
                    calories    = extract_calories(nutrients),
                    nutrients   = nutrients,
                ))
                inserted += 1
            except Exception as e:
                skipped += 1
                print(f"[WARN] Skipped record — {e}")

            # Flush in batches of 500 to keep memory usage flat on large files
            if len(batch) >= 500:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []

        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        print(f"[OK] Done: {inserted:,} inserted, {skipped} skipped.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "recipes.json"
    seed(path)