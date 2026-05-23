from database import get_db
from datetime import datetime

#账单管理

#添加账单
def add_bill(bill_type, amount, related_id, comment):
    if amount <= 0:
        return False, "金额必须大于0"
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn, cursor = get_db()
    cursor.execute('''
        INSERT INTO bill (type, amount, related_id, comment, create_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (bill_type, amount, related_id, comment, create_time))
    conn.commit()
    conn.close()
    return True, "账单记录成功"
#查询所有账单
def get_all_bills():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM bill ORDER BY create_time DESC")
    bills = cursor.fetchall()
    conn.close()
    return bills
#根据账单来源分类
def get_bill_stat():
    conn, cursor = get_db()
    cursor.execute("SELECT SUM(amount) FROM bill WHERE type = 'income'")
    income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM bill WHERE type = 'expense'")
    expense = cursor.fetchone()[0] or 0
    conn.close()
    profit = income - expense
    return income, expense, profit
