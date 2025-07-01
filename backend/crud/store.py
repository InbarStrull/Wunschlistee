from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import Store

def create_store(db, store_data):
    store = Store(name = store_data["name"])

    return add_commit_flush(db, store)


def get_store(db, store_id):
    return get_instance(db, Store, store_id)


def get_or_create_store(db, store_data):
    store = db.query(Store).filter_by(name=store_data["name"]).first()

    if store:
        return store

    return create_store(db, store_data)


def update_store(db, store_id, store_data):
    return update_instance(db, Store, store_data, store_id)


def delete_store(db, store_id):
    return delete_instance(db, Store, store_id)


def get_all_stores(db, skip=0, limit=100):
    return get_all_instances(db, Store, skip, limit)