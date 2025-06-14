from .generic import add_commit_flush, get_instance, update_instance, delete_instance, get_all_instances
from ..models import Wishlist

def create_wishlist(db, wishlist_data):
    wishlist = db.query(Wishlist).filter_by(name=wishlist_data["name"]).first()

    if wishlist:
        return wishlist

    wishlist = Wishlist(name = wishlist_data["name"])

    return add_commit_flush(db, wishlist)


def get_wishlist(db, wishlist_id):
    return get_instance(db, Wishlist, wishlist_id)


def update_wishlist(db, wishlist_id, wishlist_data):
    return update_instance(db, Wishlist, wishlist_data, wishlist_id)


def delete_wishlist(db, wishlist_id):
    return delete_instance(db, Wishlist, wishlist_id)


def get_all_wishlists(db):
    return get_all_instances(db, Wishlist)