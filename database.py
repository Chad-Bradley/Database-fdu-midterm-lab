import sqlite3

# 连接数据库
def get_db():
    conn = sqlite3.connect("bookstore.db", timeout=30)
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()
    return conn, cursor

# 初始化
def init_database():
    conn, cursor = get_db()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        real_name TEXT,
        work_id TEXT UNIQUE,
        gender TEXT CHECK(gender IN ('男','女')),
        age INTEGER CHECK(age>0),
        role TEXT NOT NULL CHECK(role IN ('super','normal'))
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT UNIQUE NOT NULL,
        book_name TEXT NOT NULL,
        author TEXT,
        publisher TEXT,
        retail_price REAL CHECK(retail_price IS NULL OR retail_price > 0)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL UNIQUE,
        stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
        FOREIGN KEY (book_id) REFERENCES book(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        purchase_price REAL NOT NULL CHECK(purchase_price>0),
        quantity INTEGER NOT NULL CHECK(quantity>=1),
        status TEXT NOT NULL CHECK(status IN ('unpaid','paid','returned','stocked')),
        create_time TEXT NOT NULL,
        FOREIGN KEY (book_id) REFERENCES book(id),
        FOREIGN KEY (user_id) REFERENCES user(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sale (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        sale_price REAL NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 1),
        sale_time TEXT NOT NULL,
        FOREIGN KEY (book_id) REFERENCES book(id),
        FOREIGN KEY (user_id) REFERENCES user(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bill (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
        amount REAL NOT NULL CHECK(amount > 0),
        related_id INTEGER,
        comment TEXT,
        create_time TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        detail TEXT,
        create_time TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id)
    )''')

    conn.commit()
    conn.close()
    print("初始化完成")

if __name__ == "__main__":
    init_database()
