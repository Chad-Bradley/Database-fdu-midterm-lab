from database import get_db
from datetime import datetime
from bill import add_bill
from log import add_log

# 进货管理

# 创建进货单
def create_purchase(user_id, book_id, purchase_price, quantity):
    if purchase_price <= 0:
        return False, "进货单价为正数"
    if quantity < 1:
        return False, "数量至少为1"
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn, cursor = get_db()
    cursor.execute('''
        INSERT INTO purchase (user_id, book_id, purchase_price, quantity, status, create_time)
        VALUES (?,?,?,?,?,?)
    ''', (user_id, book_id, purchase_price, quantity, "unpaid", create_time))
    conn.commit()
    conn.close()
    add_log(user_id, "新建进货", f"图书ID：{book_id}，数量：{quantity}")
    return True, "进货单创建成功（未付款）"

#查询所有进货单
def get_all_purchases(status=None):
    conn, cursor = get_db()
    if status:
        cursor.execute("SELECT * FROM purchase WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT * FROM purchase")
    purchases = cursor.fetchall()
    conn.close()
    return purchases

#进货单付款
def pay_purchase(operator_id, purchase_id):
    conn, cursor = get_db()
    cursor.execute("SELECT status, book_id, quantity, purchase_price FROM purchase WHERE id = ?", (purchase_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "进货单不存在"
    status, book_id, quantity, purchase_price = res
    if status != "unpaid":
        conn.close()
        return False, "只有未付款的单子才能付款"
    cursor.execute('''
        UPDATE purchase
        SET status = 'paid'
        WHERE id = ?
    ''', (purchase_id,))
    conn.commit()
    conn.close()
    add_bill("expense", purchase_price * quantity, purchase_id, f"进货付款 单号:{purchase_id}")
    add_log(operator_id, "进货付款", f"进货单ID：{purchase_id}")
    return True, "付款成功，已记录支出账单"

#退款
def return_purchase(operator_id, purchase_id):
    conn, cursor = get_db()
    cursor.execute("SELECT status FROM purchase WHERE id = ?", (purchase_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "进货单不存在"
    status = res[0]
    if status != "unpaid":
        conn.close()
        return False, "只有未付款的单子才能退货"
    cursor.execute('''
        UPDATE purchase
        SET status = 'returned'
        WHERE id = ?
    ''', (purchase_id,))
    conn.commit()
    conn.close()
    add_log(operator_id, "进货退货", f"进货单ID：{purchase_id}")
    return True, "退货成功"

#进货后入库处理
def stock_in_purchase(operator_id, purchase_id, retail_price=None):
    conn, cursor = get_db()
    cursor.execute("SELECT status, book_id, quantity FROM purchase WHERE id = ?", (purchase_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "进货单不存在"
    status, book_id, quantity = res
    if status != "paid":
        conn.close()
        return False, "只有已付款的单子才能入库"

    # 检查该书是否已有零售价
    cursor.execute('SELECT retail_price FROM book WHERE id = ?', (book_id,))
    row = cursor.fetchone()

    if row and row[0] is not None:
        # 已有零售价，只加库存，不覆盖
        msg = "入库成功！图书库存已增加（零售价保持不变）"
    else:
        # 没有零售价，必须提供
        if retail_price is None or retail_price <= 0:
            conn.close()
            return False, "该图书尚未设置零售价，入库时必须填写零售价"
        cursor.execute('UPDATE book SET retail_price = ? WHERE id = ?', (retail_price, book_id))
        msg = "入库成功！图书库存已增加，零售价已设置"

    # 更新进货单状态
    cursor.execute('UPDATE purchase SET status = "stocked" WHERE id = ?', (purchase_id,))

    # 增加库存
    cursor.execute('''
        UPDATE inventory SET stock_quantity = stock_quantity + ? WHERE book_id = ?
    ''', (quantity, book_id))

    conn.commit()
    conn.close()
    add_log(operator_id, "图书入库", f"进货单ID：{purchase_id}")
    return True, msg
