"""
main.py — FastAPI Recipe API

ONE command runs everything:
    uvicorn main:app --port 8000 --reload

URLs:
    http://127.0.0.1:8000           → Frontend UI (Recipe Explorer)
    http://127.0.0.1:8000/docs      → Swagger API docs
    http://127.0.0.1:8000/api/recipes         → Paginated recipe list
    http://127.0.0.1:8000/api/recipes/search  → Search / filter
    http://127.0.0.1:8000/api/recipes/{id}    → Single recipe
"""

import re
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import get_db
from models import Recipe
from schemas import RecipeOut, PaginatedRecipes, SearchRecipes

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Recipes API",
    version="1.0.0",
    description="RESTful API for browsing, searching, and filtering recipes.",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Static files (CSS, JS, images if any) ────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── Serve index.html at root "/" ──────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def serve_frontend():
    """
    Serves the Recipe Explorer UI.
    Visiting http://127.0.0.1:8000 opens the frontend directly.
    The API docs are still at http://127.0.0.1:8000/docs
    """
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(
            status_code=404,
            detail="frontend/index.html not found. Make sure the frontend folder is present."
        )
    return FileResponse(index)


# ── Filter helpers ────────────────────────────────────────────────────────────

# Accepts: ">=4.5"  "<=400"  ">3"  "<200"  "=5"  or just "5"
_FILTER_RE = re.compile(r"^(>=|<=|>|<|=)?(-?\d+(?:\.\d+)?)$")


def parse_numeric_filter(param: Optional[str]) -> tuple:
    """
    Parse a numeric filter string into (operator, value).
    Returns (None, None) when param is absent.
    Raises HTTP 422 with a clear message on bad format.
    """
    if param is None:
        return None, None
    m = _FILTER_RE.match(param.strip())
    if not m:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid filter value '{param}'. "
                "Expected a number with an optional operator — "
                "e.g. '>=4.5', '<=400', '>3', '<200', '=5', or just '400'."
            ),
        )
    op  = m.group(1) or "="
    val = float(m.group(2))
    return op, val


_OP_MAP = {
    ">=": lambda col, v: col >= v,
    "<=": lambda col, v: col <= v,
    ">":  lambda col, v: col >  v,
    "<":  lambda col, v: col <  v,
    "=":  lambda col, v: col == v,
}


def apply_filter(query, column, op: str, val: float):
    """Apply a SQLAlchemy column filter using the parsed operator."""
    return query.filter(_OP_MAP[op](column, val))


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get(
    "/api/recipes",
    response_model=PaginatedRecipes,
    summary="Get all recipes — paginated, sorted by rating desc",
    tags=["Recipes"],
)
def get_recipes(
    page:  int = Query(default=1,  ge=1,        description="Page number (1-based)"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
):
    """
    Returns all recipes sorted by rating descending.
    Recipes with no rating appear last.
    Supports pagination via `page` and `limit`.
    """
    base    = db.query(Recipe).order_by(Recipe.rating.desc().nulls_last())
    total   = base.count()
    recipes = base.offset((page - 1) * limit).limit(limit).all()
    return PaginatedRecipes(page=page, limit=limit, total=total, data=recipes)


@app.get(
    "/api/recipes/search",
    response_model=SearchRecipes,
    summary="Search and filter recipes",
    tags=["Recipes"],
)
def search_recipes(
    title:      Optional[str] = Query(default=None, description="Partial title match (case-insensitive)"),
    cuisine:    Optional[str] = Query(default=None, description="Partial cuisine match (case-insensitive)"),
    rating:     Optional[str] = Query(default=None, description="Rating filter — e.g. '>=4.5', '<=3', '=5'"),
    total_time: Optional[str] = Query(default=None, description="Total time in minutes — e.g. '<=60', '>=30'"),
    calories:   Optional[str] = Query(default=None, description="Calories in kcal — e.g. '<=400', '>=200'"),
    page:  int = Query(default=1,  ge=1,        description="Page number (1-based)"),
    limit: int = Query(default=15, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
):
    """
    Filter recipes by any combination of fields. All parameters are optional.

    Numeric filters (rating, total_time, calories) support operators:
    >=  <=  >  <  =  — e.g. calories=<=400&rating=>=4.5

    Calories is filtered via an indexed SQL INTEGER column (not a Python loop),
    so it scales efficiently regardless of table size.
    """
    query = db.query(Recipe)

    # Text filters — partial, case-insensitive
    if title:
        query = query.filter(Recipe.title.ilike(f"%{title}%"))
    if cuisine:
        query = query.filter(Recipe.cuisine.ilike(f"%{cuisine}%"))

    # Numeric filters — all handled in SQL, all indexed
    r_op, r_val = parse_numeric_filter(rating)
    if r_op:
        query = apply_filter(query, Recipe.rating, r_op, r_val)

    t_op, t_val = parse_numeric_filter(total_time)
    if t_op:
        query = apply_filter(query, Recipe.total_time, t_op, t_val)

    c_op, c_val = parse_numeric_filter(calories)
    if c_op:
        query = apply_filter(query, Recipe.calories, c_op, c_val)

    query   = query.order_by(Recipe.rating.desc().nulls_last())
    total   = query.count()
    recipes = query.offset((page - 1) * limit).limit(limit).all()

    return SearchRecipes(data=recipes, total=total)


@app.get(
    "/api/recipes/{recipe_id}",
    response_model=RecipeOut,
    summary="Get a single recipe by ID",
    tags=["Recipes"],
)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Returns a single recipe by its ID. Returns 404 if not found."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=f"Recipe with id={recipe_id} not found."
        )
    return recipe