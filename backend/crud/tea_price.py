from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import TeaPrice

def add_tea_and_price_to_store(db, tea_store_data):
    # entry for each tea and store to trace tea availability in stores, and prices
    tea_store = get_price_by_tea_and_store(db, tea_store_data["tea_id"],
                                                     tea_store_data["store_id"])

    if not tea_store:
        tea_store = create_tea_price_and_store_entry(db, tea_store_data)

    return tea_store


def create_tea_price_and_store_entry(db, tea_store_data):
    tea_store = TeaPrice(
        tea_id = tea_store_data["tea_id"],
        store_id = tea_store_data["store_id"],
        price = tea_store_data.get("price"),
        store_page_url = tea_store_data.get("store_page_url")
    )

    return add_commit_flush(db, tea_store)


def get_price_by_tea_and_store(db, tea_id, store_id):
    tea_store = (db.query(TeaPrice).filter_by
                      (tea_id=tea_id,store_id=store_id).first())

    return tea_store


def get_tea_price_and_store(db, tea_store_id):
    return get_instance(db, TeaPrice, tea_store_id)


def update_tea_price_and_store(db, tea_store_id, tea_store_data):
    return update_instance(db, TeaPrice, tea_store_data, tea_store_id)


def delete_tea_price_and_store(db, tea_store_id):
    return delete_instance(db, TeaPrice, tea_store_id)


def get_all_tea_stores_and_prices(db):
    return get_all_instances(db, TeaPrice)