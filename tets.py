import shelve

shelf = shelve.open('Database/cache')

print(dict(shelf))