from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import WishlistItem


def add_item_to_wishlist(db, item_data):
    wishlist_item = get_wishlist_item_by_tea_and_wishlist(db, item_data["tea_id"],
                                                          item_data["wishlist_id"])

    if not wishlist_item:
        wishlist_item = create_wishlist_item(db, item_data)

    return wishlist_item



def create_wishlist_item(db, item_data):
    wishlist_item = WishlistItem(
        tea_id = item_data["tea_id"],
        wishlist_id = item_data["wishlist_id"]
    )

    return add_commit_flush(db, wishlist_item)


def get_wishlist_item_by_tea_and_wishlist(db, tea_id, wishlist_id):
    wishlist_item = (db.query(WishlistItem).filter_by
                      (tea_id=tea_id,
                       wishlist_id=wishlist_id)
                      .first())

    return wishlist_item


def get_wishlist_item(db, wishlist_item_id):
    return get_instance(db, WishlistItem, wishlist_item_id)


def update_wishlist_item(db, wishlist_item_id, wishlist_item_data):
    return update_instance(db, WishlistItem, wishlist_item_data, wishlist_item_id)


def delete_wishlist_item(db, wishlist_item_id):
    return delete_instance(db, WishlistItem, wishlist_item_id)


def get_all_wishlist_items(db):
    return get_all_instances(db, WishlistItem)