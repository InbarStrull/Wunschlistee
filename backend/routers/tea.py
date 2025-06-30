from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import models, schemas
from backend.crud.tea import get_all_teas, get_tea, create_tea_process
from backend.database import get_db

router = APIRouter(
    prefix="/teas",
    tags=["teas"],
)


# GET /teas list all teas
@router.get("/", response_model=List[schemas.TeaOut])
def read_teas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    teas = get_all_teas(db, skip, limit)
    return teas

# GET /teas/{tea_id} get single tea by ID
@router.get("/{tea_id}", response_model=schemas.TeaOut)
def read_tea(tea_id: int, db: Session = Depends(get_db)):
    tea = get_tea(db, tea_id)
    if not tea:
        raise HTTPException(status_code=404, detail="Tea not found")

    return tea

# POST /teas create a new tea
@router.post("/", response_model=schemas.TeaOut, status_code=status.HTTP_201_CREATED)
def create_tea(tea_in: schemas.TeaCreate, db: Session = Depends(get_db)):
    tea_data = tea_in.model_dump()
    try:
        tea = create_tea_process(db, tea_data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    db.refresh(tea)

    return tea


# DELETE /teas/{tea_id} delete a tea
@router.delete("/{tea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tea(tea_id: int, db: Session = Depends(get_db)):
    tea = delete_tea(tea_id, db)

    if not tea:
        raise HTTPException(status_code=404, detail="Tea not found")

