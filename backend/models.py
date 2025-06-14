from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Text, UniqueConstraint, Enum, Numeric, DateTime, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    teas = relationship("Tea", back_populates="brand")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    tea_prices = relationship("TeaPrice", back_populates="store", cascade="all, delete")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name_en = Column(String, nullable=False)
    name_he = Column(String, nullable=False)
    name_de = Column(String, nullable=False, unique=True)

    normalized_id = Column(Integer, ForeignKey("normalized_ingredients.id"), nullable=True)

    tea_ingredients = relationship("TeaIngredient", back_populates="ingredient", cascade="all, delete-orphan")
    normalized_ingredient = relationship("NormalizedIngredient", back_populates="ingredients")


class NormalizedIngredient(Base):
    __tablename__ = "normalized_ingredients"

    id = Column(Integer, primary_key=True)
    name_en = Column(String, nullable=False)
    name_he = Column(String, nullable=False)
    name_de = Column(String, nullable=False, unique=True)

    # metadata not supported yet
    wikipedia_url = Column(String, nullable=True)
    # for pepper for example (white, black, green....)
    color = Column(String, nullable=True)
    # for cinnamon for example (ceylon, cassia...)
    ingredient_type = Column(String, nullable=True)
    # for chamomile for example (flowers, stem, root...)
    plant_part = Column(String, nullable=True)

    ingredients = relationship("Ingredient", back_populates="normalized_ingredient", cascade="all, delete-orphan")


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")


class Tea(Base):
    __tablename__ = "teas"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    image_url = Column(String)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    brand_page_url = Column(String)
    weight = Column(Numeric(10, 2), nullable=True)
    bag_quantity = Column(Integer)
    description = Column(Text)
    type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    brand = relationship("Brand", back_populates="teas")
    tea_ingredients  = relationship("TeaIngredient", back_populates="teas", cascade="all, delete-orphan")
    prices = relationship("TeaPrice", back_populates="tea", cascade="all, delete-orphan")
    #wishlists = relationship("WishlistItem", back_populates="teas", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="tea", cascade="all, delete-orphan")

class TeaIngredient(Base):
    __tablename__ = "tea_ingredients"

    id = Column(Integer, primary_key=True)
    tea_id = Column(Integer, ForeignKey("teas.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=True)

    teas = relationship("Tea", back_populates="tea_ingredients")
    ingredient = relationship("Ingredient", back_populates="tea_ingredients")

    __table_args__ = (
        UniqueConstraint("tea_id", "ingredient_id", name="_tea_ingredient_uc"),
    )


class TeaPrice(Base):
    __tablename__ = "tea_prices"

    id = Column(Integer, primary_key=True)
    tea_id = Column(Integer, ForeignKey("teas.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    price = Column(Numeric(10, 2) , nullable=True)
    store_page_url = Column(String)

    tea = relationship("Tea", back_populates="prices")
    store = relationship("Store", back_populates="tea_prices")

    __table_args__ = (
        UniqueConstraint("tea_id", "store_id", name="_tea_store_uc"),
    )


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id"), nullable=False)
    tea_id = Column(Integer, ForeignKey("teas.id"), nullable=False)

    wishlist = relationship("Wishlist", back_populates="items")
    tea = relationship("Tea", back_populates="wishlist_items")

    __table_args__ = (
        UniqueConstraint("wishlist_id", "tea_id", name="_wishlist_tea_uc"),
    )
