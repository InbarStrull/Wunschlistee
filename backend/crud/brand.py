from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import Brand

def create_brand(db, brand_data):
    brand = Brand(name=brand_data["name"])

    return add_commit_flush(db, brand)


def get_brand(db, brand_id):
    return get_instance(db, Brand, brand_id)


def get_or_create_brand(db, brand_data):
    brand = db.query(Brand).filter_by(name=brand_data["name"]).first()

    if brand:
        return brand

    return create_brand(db, brand_data)

def update_brand(db, brand_id, brand_data):
    return update_instance(db, Brand, brand_data, brand_id)


def delete_brand(db, brand_id):
    return delete_instance(db, Brand, brand_id)


def get_all_brands(db):
    return get_all_instances(db, Brand)