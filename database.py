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
        FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchase (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        purchase_price REAL NOT NULL CHECK(purchase_price>0),
        quantity INTEGER NOT NULL CHECK(quantity>=1),
        status TEXT NOT NULL CHECK(status IN ('unpaid','paid','returned','stocked')),
        create_time TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sale (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        sale_price REAL NOT NULL CHECK(sale_price>0),
        quantity INTEGER NOT NULL CHECK(quantity >= 1),
        sale_time TEXT NOT NULL
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
        create_time TEXT NOT NULL
    )''')

    cursor.execute('''

    CREATE TRIGGER IF NOT EXISTS after_sale_insert_bill
    AFTER INSERT ON sale
    BEGIN
        INSERT INTO bill(type,amount,related_id,comment,create_time)
        VALUES ('income',NEW.sale_price*NEW.quantity,NEW.id,
                '销售图书，收入'||printf('%.2f',NEW.sale_price*NEW.quantity)||'元',
                NEW.sale_time);
    END;
    ''')
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS after_purchase_pay_bill
    AFTER UPDATE OF status ON purchase
    WHEN NEW.status='paid' AND OLD.status='unpaid'
    BEGIN
        INSERT INTO bill (type,amount,related_id,comment,create_time)
        VALUES('expense',NEW.purchase_price*NEW.quantity,NEW.id,
                '进货付款 单号:'||NEW.id,
                datetime('now','localtime'));
    END;
    ''')



    conn.commit()
    conn.close()
    print("初始化完成")



if __name__ == "__main__":
    init_database()
