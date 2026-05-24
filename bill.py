from database import get_db
from datetime import datetime

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
