from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import schemas
from backend.crud.store import get_all_stores, get_store, create_store
from backend.database import get_db

router = APIRouter(
    prefix="/stores",
    tags=["stores"],
)


# GET get all stores
@router.get("/", response_model=List[schemas.StoreOut])
def read_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stores = get_all_stores(db, skip, limit)
    return stores

# GET get store by id
@router.get("/{store_id}", response_model=schemas.StoreOut)
def read_store(store_id: int, db: Session = Depends(get_db)):
    store = get_store(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    return store

@router.post("/", response_model=schemas.StoreOut, status_code=status.HTTP_201_CREATED)
def create_new_store(store_in: schemas.StoreCreate, db: Session = Depends(get_db)):
    store_data = store_in.model_dump()
    try:
        store = create_store(db, store_data)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    db.refresh(store)

    return store