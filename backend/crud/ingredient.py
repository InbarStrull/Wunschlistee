from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import Ingredient
#from ..utils import create_ingredient_data


def create_ingredient(db, ingredient_data):
    ingredient = Ingredient(
        name_en=ingredient_data["name_en"],
        name_he=ingredient_data["name_iw"],
        name_de=ingredient_data["name_de"],
        #wikipedia_url=ingredient_data.get("wikipedia_url")
    )

    return add_commit_flush(db, ingredient)


def get_or_create_ingredient(db, ingredient_data, lang='de'):
    column = getattr(Ingredient, f"name_{lang}")

    ingredient = db.query(Ingredient).filter(column == ingredient_data[f"name_{lang}"]).first()

    if not ingredient:
        ingredient = create_ingredient(db, ingredient_data)

    return ingredient

def get_ingredient(db, ingredient_id):
    return get_instance(db, Ingredient, ingredient_id)


def update_ingredient(db, ingredient_id, ingredient_data):
    return update_instance(db, Ingredient, ingredient_data, ingredient_id)


def delete_ingredient(db, ingredient_id):
    return delete_instance(db, Ingredient, ingredient_id)


def get_all_ingredients(db, skip=0, limit=100):
    return get_all_instances(db, Ingredient, skip, limit)
