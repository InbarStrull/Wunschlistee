from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import backend.crud.brand
from backend import schemas
from backend.crud.brand import get_all_brands, get_brand, create_brand
from backend.database import get_db

router = APIRouter(
    prefix="/brands",
    tags=["brands"],
)


# GET get all brands
@router.get("/", response_model=List[schemas.BrandOut])
def read_brands(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    brands = get_all_brands(db, skip, limit)
    return brands

# GET get brand by id
@router.get("/{brand_id}", response_model=schemas.BrandOut)
def read_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = get_brand(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand

@router.post("/", response_model=schemas.BrandOut, status_code=status.HTTP_201_CREATED)
def create_new_brand(brand_in: schemas.BrandCreate, db: Session = Depends(get_db)):
    brand_data = brand_in.model_dump()
    try:
        brand = create_brand(db, brand_data)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    db.refresh(brand)

    return brand