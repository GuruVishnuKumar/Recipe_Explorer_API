from pydantic import BaseModel
from typing import Optional, Any, List


class RecipeOut(BaseModel):
    id:          int
    cuisine:     Optional[str]   = None
    title:       Optional[str]   = None
    rating:      Optional[float] = None
    prep_time:   Optional[int]   = None
    cook_time:   Optional[int]   = None
    total_time:  Optional[int]   = None
    description: Optional[str]   = None
    serves:      Optional[str]   = None
    calories:    Optional[int]   = None   # extracted at seed time for SQL filtering
    nutrients:   Optional[Any]   = None   # full JSON blob for display

    class Config:
        from_attributes = True


class PaginatedRecipes(BaseModel):
    page:  int
    limit: int
    total: int
    data:  List[RecipeOut]


class SearchRecipes(BaseModel):
    total: int
    data:  List[RecipeOut]