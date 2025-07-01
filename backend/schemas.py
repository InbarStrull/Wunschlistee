from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from pydantic.v1 import Field


# --- Brand ---
class BrandBase(BaseModel):
    name: str

class BrandCreate(BrandBase):
    pass

class BrandOut(BrandBase):
    id: int

    class Config:
        orm_mode = True


# --- Store ---
class StoreBase(BaseModel):
    name: str

class StoreCreate(StoreBase):
    pass

class StoreOut(StoreBase):
    id: int

    class Config:
        orm_mode = True


# --- Ingredient ---
class IngredientBase(BaseModel):
    name_en: str
    name_he: str
    name_de: str

class IngredientCreate(IngredientBase):
    pass

class IngredientOut(IngredientBase):
    id: int

    class Config:
        orm_mode = True


# --- TeaIngredient ---
class TeaIngredientCreate(BaseModel):
    name_en: str
    name_he: str
    name_de: str
    percentage: Optional[Decimal]

class TeaIngredientOut(BaseModel):
    id: int
    percentage: Optional[Decimal]
    ingredient: IngredientOut

    class Config:
        orm_mode = True


# --- Tea ---
class TeaBase(BaseModel):
    name: str
    brand: str
    brand_page_url: Optional[str]
    weight: Optional[Decimal]
    bag_quantity: Optional[int]
    image_url: Optional[str]
    description: Optional[str]
    type: Optional[str]

class TeaCreate(TeaBase):
    ingredients: List[TeaIngredientCreate] = Field(default_factory=list)
    store: Optional[str] = None          # store name
    price: Optional[Decimal] = None      # price at this store
    store_page_url: Optional[str] = None # optional link to product page in the store

class TeaOut(TeaBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    brand: BrandOut # overrides brand form teabase
    tea_ingredients: List[TeaIngredientOut] = Field(default_factory=list)

    class Config:
        orm_mode = True


# --- TeaPrice ---
class TeaPriceCreate(BaseModel):
    tea_id: int
    store_id: int
    price: Optional[Decimal]
    store_page_url: Optional[str]

class TeaPriceOut(TeaPriceCreate):
    id: int
    store: StoreOut

    class Config:
        orm_mode = True


# --- Wishlist & WishlistItem ---
class WishlistBase(BaseModel):
    name: str

class WishlistCreate(WishlistBase):
    pass

class WishlistOut(WishlistBase):
    id: int
    items: List["WishlistItemOut"] = Field(default_factory=list)

    class Config:
        orm_mode = True

class WishlistUpdate(BaseModel):
    name: Optional[str] = None

class WishlistItemCreate(BaseModel):
    wishlist_id: int
    tea_id: int

class WishlistItemOut(BaseModel):
    id: int
    tea: TeaOut

    class Config:
        orm_mode = True


# Required for self-referencing nested models
WishlistOut.update_forward_refs()
