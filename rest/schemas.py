# your_app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

# Mirroring the Exercise Django model
class ExerciseSchema(BaseModel):
    name: str = Field(..., description="e.g., 'Push-ups', 'Squats', 'Ampe (Jumping Game)'")
    sets: int
    reps: str = Field(..., description="e.g., '10-12', 'AMRAP (As Many Reps As Possible)'")
    rest_period_seconds: int = Field(..., description="Rest time in seconds between sets.")
    notes: Optional[str] = Field(None, description="Specific instructions or Ghanaian context.")

# Mirroring the WorkoutDay Django model
class WorkoutDaySchema(BaseModel):
    day_of_week: int = Field(..., ge=1, le=7, description="1 for Monday, 7 for Sunday.")
    title: str = Field(..., description="e.g., 'Upper Body Strength' or 'Rest Day'")
    is_rest_day: bool = False
    description: Optional[str] = Field(None, description="General instructions for the day's workout.")
    exercises: List[ExerciseSchema] = []

# Mirroring the Meal Django model
class MealSchema(BaseModel):
    meal_type: str = Field(..., description="One of 'breakfast', 'lunch', 'dinner', 'snack'.")
    description: str = Field(..., description="e.g., 'Waakye with boiled egg and fish'")
    calories: int
    protein_grams: float
    carbs_grams: float
    fats_grams: float
    portion_size: Optional[str] = Field(None, description="e.g., '1 medium ladle', '2 pieces of chicken'")

# Mirroring the NutritionDay Django model
class NutritionDaySchema(BaseModel):
    day_of_week: int = Field(..., ge=1, le=7, description="1 for Monday, 7 for Sunday.")
    target_calories: int
    target_protein_grams: int
    target_carbs_grams: int
    target_fats_grams: int
    notes: Optional[str] = Field(None, description="General advice for the day, e.g., 'Drink 3L of water.'")
    meals: List[MealSchema]

# This is the main, top-level schema you will pass to Gemini
class GeneratedPlanSchema(BaseModel):
    workout_days: List[WorkoutDaySchema]
    nutrition_days: List[NutritionDaySchema]