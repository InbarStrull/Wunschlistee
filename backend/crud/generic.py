import logging


# generic fetch by id
def get_instance(db, model, instance_id):
    return db.query(model).filter(model.id == instance_id).first()


# generic delete by id
def delete_instance(db, model, instance_id):
    instance = get_instance(db, model, instance_id)

    if instance:
        db.delete(instance)
        db.commit()
        return instance

# compare between old instance and updated instance without updating db
def print_changes_in_instance(db, model, new_instance_data, instance_id):
    instance = get_instance(db, model, instance_id)
    print("~~~~~~~~~~~~~~")
    if instance:
        for key, new_value in new_instance_data.items():

            # check key is part of the model and not a new column
            if not hasattr(instance, key):
                continue

            current_value = getattr(instance, key)

            # check key is not a relational field
            if hasattr(current_value, "_sa_instance_state") and not hasattr(new_value, "_sa_instance_state"):
                continue


            if current_value != new_value:
                print(f"before {key}: {current_value}, after {key}: {new_value}")

    print("~~~~~~~~~~~~~~")


# generic update by id, without relational fields
def update_instance(db, model, new_instance_data, instance_id):
    instance = get_instance(db, model, instance_id)
    updated = False

    if instance:
        for key, new_value in new_instance_data.items():

            # check key is part of the model and not a new column
            if not hasattr(instance, key):
                continue

            current_value = getattr(instance, key)

            # check key is not a relational field
            if hasattr(current_value, "_sa_instance_state") and not hasattr(new_value, "_sa_instance_state"):
                continue


            if current_value != new_value:
                print(f"*****updating {key} from {current_value} to {new_value}********")
                setattr(instance, key, new_value)
                updated = True

        if updated:
            db.flush()
            db.refresh(instance)
            db.commit()


    return instance


# generic fetch for all instances of a model
def get_all_instances(db, model):
    return db.query(model).all()


# add and auto generate instance id
def add_commit_flush(db, instance):
    try:
        db.add(instance)
        # auto generate instance id
        db.flush()
        return instance

    except Exception as e:
        logging.exception("Failed to add and flush instance")
        raise