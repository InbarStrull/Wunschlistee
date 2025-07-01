from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend import schemas
from backend.crud.wishlist import get_all_wishlists, get_wishlist, create_wishlist, update_wishlist, delete_wishlist
from backend.database import get_db

router = APIRouter(
    prefix="/wishlists",
    tags=["wishlists"],
)


# GET get all wishlists
@router.get("/", response_model=List[schemas.WishlistOut])
def read_wishlists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    wishlists = get_all_wishlists(db, skip, limit)
    return wishlists

# GET get wishlist by id
@router.get("/{wishlist_id}", response_model=schemas.WishlistOut)
def read_wishlist(wishlist_id: int, db: Session = Depends(get_db)):
    wishlist = get_wishlist(db, wishlist_id)
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    return wishlist

@router.post("/", response_model=schemas.WishlistOut, status_code=status.HTTP_201_CREATED)
def create_new_wishlist(wishlist_in: schemas.WishlistCreate, db: Session = Depends(get_db)):
    wishlist_data = wishlist_in.model_dump()
    try:
        wishlist = create_wishlist(db, wishlist_data)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    db.refresh(wishlist)

    return wishlist

@router.patch("/{wishlist_id", response_model=schemas.WishlistOut)
def rename_wishlist(wishlist_id: int, update_in: schemas.WishlistUpdate, db: Session = Depends(get_db)):
    wishlist_data = update_in.model_dump()
    wishlist = update_wishlist(db, wishlist_id, wishlist_data)

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    db.commit()

    return wishlist

# DELETE /wishlists/{wishlist_id} delete a wishlist
@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wishlist_from_db(wishlist_id: int, db: Session = Depends(get_db)):
    wishlist = delete_wishlist(db, wishlist_id)

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

