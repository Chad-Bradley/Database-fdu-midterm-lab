from database import get_db
from book import get_stock, get_retail_price
from datetime import datetime
from bill import add_bill
from log import add_log

# 销售管理

#创建销售单
def create_sale(user_id,book_id,quantity):
    conn,cursor=get_db()
    sale_price=get_retail_price(book_id)
    if sale_price is None:
        conn.close()
        return False,"该图书尚未设置零售价，请先入库设置"
    cursor.execute('SELECT stock_quantity FROM inventory WHERE book_id=?',(book_id,))
    res=cursor.fetchone()
    current_stock=res[0] if res else 0

    if current_stock<quantity:
        conn.close()
        return False,f"库存不足（当前库存：{current_stock}）"

    sale_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO sale(user_id,book_id,sale_price,quantity,sale_time)
        VALUES(?,?,?,?,?)
    ''',(user_id,book_id,sale_price,quantity,sale_time))
    sale_id=cursor.lastrowid
    cursor.execute('''
        UPDATE inventory
        SET stock_quantity=stock_quantity-?
        WHERE book_id=?
    ''',(quantity,book_id))
    conn.commit()
    conn.close()
    add_bill("income",sale_price*quantity,sale_id,f"销售图书，收入{sale_price*quantity}元")
    add_log(user_id, "录入销售", f"图书ID：{book_id}，数量：{quantity}")
    return True,f"销售成功！单价：{sale_price}，总金额：{sale_price*quantity}"

#查询所有销售单
def get_all_sales():
    conn,cursor=get_db()
    cursor.execute("SELECT * FROM sale ORDER BY sale_time DESC")
    sales=cursor.fetchall()
    conn.close()
    return sales
