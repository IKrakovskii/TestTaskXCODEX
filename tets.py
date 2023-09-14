import shelve

shelf = shelve.open('Database/cache')


def get_all_cache():
    return dict(shelf)

