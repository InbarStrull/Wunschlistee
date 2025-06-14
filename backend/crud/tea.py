from .ingredient import get_or_create_ingredient
from ..models import Tea, Brand, Ingredient, Store, Wishlist, TeaIngredient, TeaPrice, WishlistItem
from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from .brand import get_or_create_brand
from .tea_ingredient import add_ingredient_to_tea
from .store import get_or_create_store
from .tea_price import add_tea_and_price_to_store
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session


def create_tea(db, tea_data, brand_id):
    tea = Tea(
        name=tea_data["name"],
        image_url=tea_data["image_url"],
        brand_id=brand_id,
        brand_page_url=tea_data.get("brand_page_url"),
        weight=tea_data["weight"],
        bag_quantity=tea_data["bag_quantity"],
        description=tea_data.get("description"),
        type=tea_data.get("type")
    )

    return add_commit_flush(db, tea)


def get_tea_by_brand_url(db, brang_page_url):
    tea = db.query(Tea).filter(Tea.brand_page_url == brang_page_url).first()

    return tea


def create_or_update_tea_by_url(db, tea_data):
    """
    assuming brand exists
    :param db:
    :param tea_data:
    :return:
    """
    tea = get_tea_by_brand_url(db, tea_data["brand_page_url"])

    if tea:
        tea = update_tea(db, tea.id, tea_data)

    else:
        tea = create_tea_process(db, tea_data)

    return tea


def create_tea_process(db, tea_data):
    # create brand if not found
    brand = get_or_create_brand(db, {"name": tea_data["brand"]})

    tea = get_tea_by_name_brand_weight_bag(db, brand.id, tea_data["name"], tea_data["weight"], tea_data["bag_quantity"])

    if not tea:
        tea = create_tea(db, tea_data, brand.id)

        process_tea_ingredients(db, tea, tea_data["ingredients"], "de")

    if tea_data.get("store"):
        link_tea_with_store_and_price(db, tea_data, tea.id)

    return tea


def get_tea(db, tea_id):
    return get_instance(db, Tea, tea_id)


def get_or_create_tea(db, brand_id, tea_data):
    tea = get_tea_by_name_brand_weight_bag(brand_id, tea_data["name"], tea_data["weight"], tea_data["bag_quantity"])

    if not tea:
        tea = create_tea(db, tea_data, brand_id)

    return tea


def get_tea_by_name_brand_weight_bag(db, brand_id, name, weight, bag_quantity):
    tea = db.query(Tea).filter(Tea.name == name,
                               Tea.brand_id == brand_id,
                               Tea.weight == weight,
                               Tea.bag_quantity == bag_quantity).first()

    return tea

def update_tea(db, tea_id, tea_data):
    return update_instance(db, Tea, tea_data, tea_id)


def delete_tea(db, tea_id):
    return delete_instance(db, Tea, tea_id)


def filter_teas(
    db: Session,
    name: Optional[str] = None,
    brand_names: Optional[List[str]] = None,
    min_weight: Optional[Decimal] = None,
    max_weight: Optional[Decimal] = None,
    min_bag_quantity: Optional[int] = None,
    max_bag_quantity: Optional[int] = None,
    types: Optional[List[str]] = None,
    ingredients_en: Optional[List[str]] = None,
    ingredients_he: Optional[List[str]] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    store_names: Optional[List[str]] = None,
    wishlist_names: Optional[List[str]] = None
) -> List[Tea]:

    query = db.query(Tea)

    # filter by tea name
    if name:
        query = query.filter(Tea.name.ilike(f"%{name}%"))

    # filter by tea brands
    if brand_names:
        query = query.join(Tea.brand).filter(Brand.name.in_(brand_names))

    # filter by weight range
    if min_weight is not None:
        query = query.filter(Tea.weight >= min_weight)

    if max_weight is not None:
        query = query.filter(Tea.weight <= max_weight)

    # filter by bag quantity
    if min_bag_quantity is not None:
        query = query.filter(Tea.bag_quantity >= min_bag_quantity)

    if max_bag_quantity is not None:
        query = query.filter(Tea.bag_quantity <= max_bag_quantity)

    # filter by tea type (black, herbal etc.)
    if types:
        query = query.filter(Tea.type.in_(types))

    # filter by ingredient
    if ingredients_he or ingredients_en:
        query = query.join(Tea.ingredients).join(TeaIngredient.ingredient)

    # filter by ingredient in english (tea contains any of the ingredients)
    if ingredients_en:
        query = query.filter(Ingredient.name_en.in_(ingredients_en))

    #  filter by ingredient in english (tea contains any of the ingredients)
    if ingredients_he:
        query = query.filter(Ingredient.name_he.in_(ingredients_he))

    # filter by store name and prices
    # each tea has its own price range according to the stores it is available in
    if store_names or min_price is not None or max_price is not None:
        query = query.join(Tea.prices).join(TeaPrice.store)

        # filter by store name
        if store_names:
            query = query.filter(Store.name.in_(store_names))

        # filter by price range (include only selected stores)
        # include only teas that their price is specified
        if min_price is not None:
            query = query.filter(TeaPrice.price != None, TeaPrice.price >= min_price)

        if max_price is not None:
            query = query.filter(TeaPrice.price != None, TeaPrice.price <= max_price)

    # filter by wishlist name
    if wishlist_names:
        query = query.join(Tea.wishlists).join(WishlistItem.wishlist).filter(Wishlist.name.in_(wishlist_names))

    # some teas will appear more than once, for example:
    # teas that appear in multiple stores
    # teas that contain both ingredient X and Y
    return query.distinct().all()


def get_all_teas(db):
    return get_all_instances(db, Tea)


def process_tea_ingredients(db, tea, ingredients_data, lang="de"):
    # de stands for german
    for ingredient_data in ingredients_data:
        ingredient = get_or_create_ingredient(db, ingredient_data, lang)

        tea_ingredient_data = {"tea_id": tea.id,
                               "ingredient_id": ingredient.id,
                               "percentage": ingredient_data["percentage"]}

        add_ingredient_to_tea(db, tea_ingredient_data)


def link_tea_with_store_and_price(db, tea_data, tea_id):
    # Link tea to store and price, including optional store URL
    store_name = tea_data["store"]

    # get store id
    store = get_or_create_store(db, {"name": store_name})

    tea_store_data = {"tea_id": tea_id,
                      "store_id": store.id,
                      "price": tea_data["price"],
                      "store_page_url": tea_data["store_page_url"]}

    add_tea_and_price_to_store(db, tea_store_data)


def delete_tea_according_to_brand(db, brand_name):
    brand = db.query(Brand).filter_by(name=brand_name).first()
    if not brand:
        print(f"No brand found with name '{brand_name}'")
        return

    teas = db.query(Tea).filter(Tea.brand_id == brand.id).all()

    for tea in teas:
        db.delete(tea)

    db.commit()