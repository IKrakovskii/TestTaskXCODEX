import dbm
import shelve

db = dbm.open('Database/cache.db', 'c')
shelf = shelve.Shelf(db)


def save_key_value(key, value):
    shelf[key] = value
    shelf.sync()


def get_data_from_key(key):
    try:
        return shelf[key]
    except:
        return False


def delete_by_key(key):
    shelf.pop(key)