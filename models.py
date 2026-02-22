from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.types import JSON
from database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cuisine     = Column(String,  index=True, nullable=True)
    title       = Column(String,  index=True, nullable=True)
    rating      = Column(Float,   nullable=True)
    prep_time   = Column(Integer, nullable=True)
    cook_time   = Column(Integer, nullable=True)
    total_time  = Column(Integer, nullable=True)
    description = Column(Text,    nullable=True)
    serves      = Column(String,  nullable=True)

    # Extracted from nutrients JSON at seed time for efficient SQL-level filtering.
    # "389 kcal" -> 389  avoids a full-table Python scan on every calorie query.
    calories    = Column(Integer, index=True, nullable=True)

    # Full nutrients blob kept for display purposes (all nutrient fields).
    nutrients   = Column(JSON, nullable=True)
