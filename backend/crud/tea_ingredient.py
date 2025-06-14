from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import TeaIngredient


# add ingredient of a from its ingredient list to the TeaIngredient table
def add_ingredient_to_tea(db, tea_ingredient_data):
    tea_ingredient = get_tea_ingredient_by_tea_and_ingredient(db, tea_ingredient_data["tea_id"],
                                                              tea_ingredient_data["ingredient_id"])

    if not tea_ingredient:
        tea_ingredient = create_tea_ingredient(db, tea_ingredient_data)

    return tea_ingredient


def create_tea_ingredient(db, tea_ingredient_data):
    tea_ingredient = TeaIngredient(
        tea_id = tea_ingredient_data["tea_id"],
        ingredient_id = tea_ingredient_data["ingredient_id"],
        percentage = tea_ingredient_data.get("percentage")
    )

    return add_commit_flush(db, tea_ingredient)


def get_tea_ingredient_by_tea_and_ingredient(db, tea_id, ingredient_id):
    tea_ingredient = db.query(TeaIngredient).filter_by(
        tea_id=tea_id,ingredient_id=ingredient_id).first()

    return tea_ingredient


def get_tea_ingredient(db, tea_ingredient_id):
    return get_instance(db, TeaIngredient, tea_ingredient_id)


def update_tea_ingredient(db, tea_ingredient_id, tea_ingredient_data):
    return update_instance(db, TeaIngredient, tea_ingredient_data, tea_ingredient_id)


def delete_tea_ingredient(db, tea_ingredient_id):
    return delete_instance(db, TeaIngredient, tea_ingredient_id)


def get_all_tea_ingredients(db):
    return get_all_instances(db, TeaIngredient)