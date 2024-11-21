import sqlite3

# Свържете се с базата данни (създайте нова, ако не съществува)
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# Проверете дали съществуват таблици в базата данни
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Таблици в базата данни:", tables)

# Проверете информация за колоните в таблицата "products"
cursor.execute("PRAGMA table_info(products);")
columns = cursor.fetchall()
print("Колони в таблицата 'products':", columns)

# Изпълнете SQL заявка, за да извлечете данни от таблицата "products"
cursor.execute("SELECT * FROM products")
rows = cursor.fetchall()

# Покажете резултатите от заявката
for row in rows:
    print(row)

# Затворете връзката
conn.close()
