from database import get_db
from log import add_log

#书籍管理

#添加书籍
def add_book(operator_id, isbn, book_name, author, publisher, retail_price=None, role=None):
    if role is not None and role != "super":
        return False,"普通员工无权修改图书信息"
    if retail_price is not None and retail_price<=0:
        return False,"价格必须为正数"
    try:
        conn,cursor=get_db()
        cursor.execute('''
            INSERT INTO book(isbn,book_name,author,publisher,retail_price)
            VALUES(?,?,?,?,?)
        ''',(isbn,book_name,author,publisher,retail_price))
        book_id=cursor.lastrowid
        cursor.execute('''
            INSERT INTO inventory(book_id,stock_quantity)
            VALUES(?,0)
        ''',(book_id,))
        conn.commit()
        conn.close()
        add_log(operator_id, "添加图书", f"添加图书：{book_name}(ISBN:{isbn})")
        return True,"图书添加成功"
    except Exception as e:
        return False,"图书添加失败"

#查询所有书籍
def get_all_books():
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price FROM book
    ''')
    books=cursor.fetchall()
    conn.close()
    return books

#根据书籍编号查询
def get_book_by_id(book_id):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price FROM book
        WHERE id=?
    ''',(book_id,))
    book=cursor.fetchall()
    conn.close()
    return book

#根据ISBN查询
def get_book_by_isbn(isbn):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price FROM book
        WHERE isbn=?
    ''',(isbn,))
    book=cursor.fetchall()
    conn.close()
    return book
#根据书名查询
def get_book_by_bookname(book_name):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price FROM book
        WHERE book_name=?
    ''',(book_name,))
    book=cursor.fetchall()
    conn.close()
    return book
#根据作者查询
def get_book_by_author(author):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price FROM book
        WHERE author=?
    ''',(author,))
    book=cursor.fetchall()
    conn.close()
    return book
#根据出版商查询
def get_book_by_publisher(publisher):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price FROM book
        WHERE publisher=?
    ''',(publisher,))
    book=cursor.fetchall()
    conn.close()
    return book
#根据关键词模糊查询
def get_books_by_key_words(words):
    conn,cursor=get_db()
    keyword=f"%{words}%"
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price
        FROM book
        WHERE isbn LIKE ?
        OR book_name LIKE ?
        OR author LIKE ?
        OR publisher LIKE ?
    ''',(keyword,keyword,keyword,keyword))
    books=cursor.fetchall()
    conn.close()
    return books

#根据价格区间查询
def get_books_by_price(low,high):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,isbn,book_name,author,publisher,retail_price
        FROM book
        WHERE retail_price>=? AND retail_price<=?
    ''',(low,high))
    books=cursor.fetchall()
    conn.close()
    return books

#根据库存数量查询书籍（支持分页和排序）
def get_books_by_stock(min_stock=None, max_stock=None):
    conn,cursor=get_db()
    if min_stock is not None and max_stock is not None:
        cursor.execute('''
            SELECT b.id,b.isbn,b.book_name,b.author,b.publisher,b.retail_price,i.stock_quantity
            FROM book b
            JOIN inventory i ON b.id=i.book_id
            WHERE i.stock_quantity>=? AND i.stock_quantity<=?
            ORDER BY i.stock_quantity
        ''',(min_stock,max_stock))
    elif min_stock is not None:
        cursor.execute('''
            SELECT b.id,b.isbn,b.book_name,b.author,b.publisher,b.retail_price,i.stock_quantity
            FROM book b
            JOIN inventory i ON b.id=i.book_id
            WHERE i.stock_quantity>=?
            ORDER BY i.stock_quantity
        ''',(min_stock,))
    elif max_stock is not None:
        cursor.execute('''
            SELECT b.id,b.isbn,b.book_name,b.author,b.publisher,b.retail_price,i.stock_quantity
            FROM book b
            JOIN inventory i ON b.id=i.book_id
            WHERE i.stock_quantity<=?
            ORDER BY i.stock_quantity
        ''',(max_stock,))
    else:
        cursor.execute('''
            SELECT b.id,b.isbn,b.book_name,b.author,b.publisher,b.retail_price,i.stock_quantity
            FROM book b
            JOIN inventory i ON b.id=i.book_id
            ORDER BY i.stock_quantity
        ''')
    books=cursor.fetchall()
    conn.close()
    return books

    
#更新书籍信息
def update_book(operator_id, book_id, book_name, author, publisher, retail_price, role=None):
    if role is not None and role != "super":
        return False,"普通员工无权修改图书信息"
    if retail_price is not None and retail_price<=0:
        return False,"价格必须为正数"
    try:
        conn,cursor=get_db()
        cursor.execute('''
            UPDATE book
            SET book_name=?,author=?,publisher=?,retail_price=?
            WHERE id=?
        ''',(book_name,author,publisher,retail_price,book_id))
        conn.commit()
        conn.close()
        add_log(operator_id, "修改图书", f"修改图书ID：{book_id}")
        return True,"图书修改成功"
    except Exception as e:
        return False,"图书修改失败"

#删除书籍
def delete_book(operator_id, book_id, role=None):
    if role is not None and role != "super":
        return False,"普通员工无权修改图书信息"
    conn,cursor=get_db()
    try:
        cursor.execute('DELETE FROM book WHERE id=?', (book_id,))
        conn.commit()
        conn.close()
        add_log(operator_id, "删除图书", f"删除图书ID：{book_id}")
        return True,"图书删除成功"
    except Exception as e:
        conn.rollback()
        return False,f"图书删除失败: {e}"
    finally:
        conn.close()

# 批量导入图书（由CSV导入）
def import_books_csv(operator_id, books_data, role=None):
    """批量导入图书，books_data为列表，每项为(isbn, book_name, author, publisher, retail_price)"""
    if role is not None and role != "super":
        return 0, "权限不足"
    
    success = 0
    fail = 0
    conn, cursor = get_db()
    
    for book_data in books_data:
        try:
            isbn, book_name, author, publisher, retail_price = book_data
            if retail_price is not None and retail_price <= 0:
                fail += 1
                continue
            cursor.execute('''
                INSERT INTO book (isbn, book_name, author, publisher, retail_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (isbn, book_name, author, publisher, retail_price))
            book_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO inventory (book_id, stock_quantity)
                VALUES (?, 0)
            ''', (book_id,))
            success += 1
        except Exception:
            fail += 1
    
    conn.commit()
    conn.close()
    
    if success > 0:
        add_log(operator_id, "导入图书", f"CSV导入图书：成功{success}条，失败{fail}条")
    
    return success, fail

#查询某本书的库存
def get_stock(book_id):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT stock_quantity
        FROM inventory
        WHERE book_id=?
    ''',(book_id,))
    stock=cursor.fetchone()
    conn.close()
    if not stock:
        return "仓库里没有该书籍"
    return stock

#查询所有书籍的库存
def get_all_stock():
    conn,cursor=get_db()
    cursor.execute('SELECT book_id,stock_quantity FROM inventory')
    stock_map={row[0]:row[1] for row in cursor.fetchall()}
    conn.close()
    return stock_map

#根据书籍编号查询零售价
def get_retail_price(book_id):
    conn,cursor=get_db()
    cursor.execute('SELECT retail_price FROM book WHERE id=?',(book_id,))
    res=cursor.fetchone()
    conn.close()
    return res[0] if res else None

