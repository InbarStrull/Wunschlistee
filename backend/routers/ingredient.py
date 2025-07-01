from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import schemas
from backend.crud.ingredient import get_all_ingredients, get_ingredient, create_ingredient
from backend.database import get_db

router = APIRouter(
    prefix="/ingredients",
    tags=["ingredients"],
)


# GET get all ingredients
@router.get("/", response_model=List[schemas.IngredientOut])
def read_ingredients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ingredients = get_all_ingredients(db, skip, limit)
    return ingredients

# GET get ingredient by id
@router.get("/{ingredient_id}", response_model=schemas.IngredientOut)
def read_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    ingredient = get_ingredient(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return ingredient

@router.post("/", response_model=schemas.IngredientOut, status_code=status.HTTP_201_CREATED)
def create_new_ingredient(ingredient_in: schemas.IngredientCreate, db: Session = Depends(get_db)):
    ingredient_data = ingredient_in.model_dump()
    try:
        ingredient = create_ingredient(db, ingredient_data)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    db.refresh(ingredient)

    return ingredient