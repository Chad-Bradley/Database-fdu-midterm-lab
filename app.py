from flask import Flask, request, redirect, session, Response, flash, get_flashed_messages
import csv, io, html as _html
from collections import OrderedDict
from functools import wraps
from database import init_database
from user import login, add_user, get_all_users, init_admin, update_user_by_admin, reset_password, delete_users, change_password, get_my_info, update_my_info, import_users_csv
from book import add_book, get_all_books, get_book_by_isbn, get_book_by_id, get_book_by_bookname, get_book_by_author, get_book_by_publisher, update_book, delete_book, get_stock, get_all_stock, get_books_by_key_words, get_books_by_price, import_books_csv
from purchase import create_purchase, get_all_purchases, pay_purchase, return_purchase, stock_in_purchase
from sale import create_sale, get_all_sales
from bill import get_all_bills, get_bill_stat
from log import add_log, get_logs_with_filter

app = Flask(__name__)
app.secret_key = "test123456"

# ======================== 样式 & 页面模板 ========================
CSS = '''
<style>
:root {
    --primary: #4a6fa5;
    --primary-light: #6b8fc5;
    --primary-dark: #3a5a8a;
    --success: #28a745;
    --danger: #dc3545;
    --warning: #f0ad4e;
    --info: #17a2b8;
    --bg: #f4f6f9;
    --card: #ffffff;
    --text: #333333;
    --text-light: #666666;
    --border: #dee2e6;
    --radius: 8px;
    --shadow: 0 2px 8px rgba(0,0,0,0.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6; padding: 0;
}
.nav {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    padding: 12px 24px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15); position: sticky; top: 0; z-index: 100;
}
.nav .brand { color: #fff; font-size: 18px; font-weight: 700; margin-right: 16px; text-decoration: none; }
.nav a {
    color: rgba(255,255,255,0.85); text-decoration: none; padding: 6px 14px;
    border-radius: 6px; font-size: 14px; transition: all .2s;
}
.nav a:hover, .nav a.active { background: rgba(255,255,255,0.2); color: #fff; }
.nav .user-info { color: rgba(255,255,255,0.9); margin-left: auto; font-size: 14px; }
.nav .logout { color: #ffcdd2; }
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }
h1 { font-size: 24px; margin-bottom: 20px; color: var(--primary-dark); }
h3 { font-size: 16px; margin-bottom: 12px; color: var(--text); }
.card {
    background: var(--card); border-radius: var(--radius); padding: 20px;
    box-shadow: var(--shadow); margin-bottom: 20px;
}
.card-title {
    font-size: 16px; font-weight: 600; color: var(--primary); margin-bottom: 14px;
    padding-bottom: 10px; border-bottom: 2px solid var(--primary-light);
}
table {
    width: 100%; border-collapse: collapse; font-size: 14px;
}
th {
    background: var(--primary); color: #fff; padding: 10px 12px; text-align: left; font-weight: 500;
}
th a { color: #fff; text-decoration: underline; }
td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:hover td { background: #f0f4fa; }
input[type=text], input[type=password], input[type=number], input[type=date],
select, input[name=keyword], input[name=isbn], input[name=book_name],
input[name=author], input[name=publisher], input[name=price], input[name=quantity],
input[name=real_name], input[name=work_id], input[name=gender], input[name=age],
input[name=username], input[name=new_password], input[name=old_password],
input[name=sale_price], input[name=retail_price], input[name=purchase_price] {
    padding: 6px 10px; border: 1px solid var(--border); border-radius: 5px;
    font-size: 14px; outline: none; transition: border-color .2s;
}
input:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(74,111,165,0.15); }
input[size="3"] { width: 60px; }
input[size="5"] { width: 80px; }
button, .btn {
    padding: 7px 18px; border: none; border-radius: 5px; font-size: 14px;
    cursor: pointer; transition: all .2s; display: inline-block; text-decoration: none;
}
.btn-primary, button[type=submit] { background: var(--primary); color: #fff; }
.btn-primary:hover, button[type=submit]:hover { background: var(--primary-dark); }
.btn-success { background: var(--success); color: #fff; }
.btn-success:hover { background: #218838; }
.btn-danger { background: var(--danger); color: #fff; }
.btn-danger:hover { background: #c82333; }
.btn-warning { background: var(--warning); color: #fff; }
.btn-warning:hover { background: #e6972e; }
.btn-info { background: var(--info); color: #fff; }
.btn-info:hover { background: #138496; }
.btn-sm { padding: 4px 12px; font-size: 13px; }
.btn-outline {
    background: transparent; color: var(--primary); border: 1px solid var(--primary);
}
.btn-outline:hover { background: var(--primary); color: #fff; }
.form-group { margin-bottom: 10px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.form-group label { min-width: 80px; font-weight: 500; font-size: 14px; color: var(--text-light); }
.form-inline { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.filter-bar {
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px;
}
.filter-bar a { padding: 5px 12px; border-radius: 5px; font-size: 13px; text-decoration: none; color: var(--text-light); border: 1px solid var(--border); }
.filter-bar a:hover, .filter-bar a.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.alert { padding: 12px 16px; border-radius: var(--radius); margin-bottom: 16px; font-weight: 500; }
.alert-danger { background: #fde8e8; color: var(--danger); border-left: 4px solid var(--danger); }
.alert-warning { background: #fff8e1; color: #856404; border-left: 4px solid var(--warning); }
.alert-success { background: #e8f5e9; color: var(--success); border-left: 4px solid var(--success); }
.stat-cards { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card {
    flex: 1; min-width: 180px; padding: 20px; border-radius: var(--radius);
    background: var(--card); box-shadow: var(--shadow); text-align: center;
}
.stat-card .label { font-size: 13px; color: var(--text-light); margin-bottom: 6px; }
.stat-card .value { font-size: 28px; font-weight: 700; }
.stat-card.income .value { color: var(--success); }
.stat-card.expense .value { color: var(--danger); }
.stat-card.profit .value { color: var(--primary); }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
}
.badge-unpaid { background: #fff3cd; color: #856404; }
.badge-paid { background: #d4edda; color: #155724; }
.badge-returned { background: #e2e3e5; color: #6c757d; }
.badge-stocked { background: #cce5ff; color: #004085; }
.badge-super { background: #f8d7da; color: #721c24; }
.badge-normal { background: #d4edda; color: #155724; }
.actions { display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }
.actions form { display: inline; }
.msg-page { text-align: center; padding: 60px 20px; }
.msg-page p { font-size: 18px; margin-bottom: 20px; }
hr { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }
.toast-container { position: fixed; top: 70px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
.toast {
    padding: 14px 22px; border-radius: var(--radius); color: #fff; font-size: 15px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.18); max-width: 400px; display: flex; align-items: center; gap: 10px;
    animation: toastIn .3s forwards, toastOut .3s 3.2s forwards;
}
.toast.success { background: var(--success); }
.toast.error { background: var(--danger); }
.toast.warning { background: var(--warning); }
.toast.info { background: var(--info); }
.toast .close-btn { cursor: pointer; font-size: 18px; margin-left: auto; opacity: 0.7; }
.toast .close-btn:hover { opacity: 1; }
@keyframes toastIn { from { opacity: 0; transform: translateX(60px); } to { opacity: 1; transform: translateX(0); } }
@keyframes toastOut { to { opacity: 0; transform: translateX(60px); } }
</style>
'''

JS = '''
<script>
function dismissToast(btn) {
    var toast = btn.parentElement;
    toast.style.animation = 'toastOut .3s forwards';
    setTimeout(function() { toast.remove(); }, 300);
}
</script>
'''

def nav_bar(active=""):
    if "user" not in session:
        return ""
    u = session["user"]
    items = [
        ("book", "图书管理"), ("stock", "库存管理"), ("purchase", "进货管理"),
        ("sale", "销售管理"), ("bill", "财务报告"), ("log", "操作日志"),
    ]
    if u["role"] == "super":
        items.append(("user", "用户管理"))
    links = ""
    for href, name in items:
        cls = ' class="active"' if active == href else ""
        links += f'<a href="/{href}"{cls}>{name}</a>'
    return f'''<div class="nav">
        <a class="brand" href="/">图书管理系统</a>
        {links}
        <a href=/myinfo class="{"active" if active=="myinfo" else ""}" style="margin-left:auto">{u["real_name"]}（{"超管" if u["role"]=="super" else "普通管理员"}）</a>
        <a class="logout" href=/logout>退出</a>
    </div>'''

def page(title, body, active=""):
    # 直接渲染 flash 消息为 HTML 弹窗
    toast_html = ''
    for category, msg in get_flashed_messages(with_categories=True):
        t = 'error' if category == 'error' else ('success' if category == 'success' else ('warning' if category == 'warning' else 'info'))
        safe_msg = _html.escape(str(msg))
        toast_html += f'<div class="toast {t}"><span>{safe_msg}</span><span class="close-btn" onclick="dismissToast(this)">&times;</span></div>'
    return f'<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>{title}</title>{CSS}</head><body>{nav_bar(active)}<div class="container">{body}</div><div class="toast-container">{toast_html}</div>{JS}</body></html>'

def msg_page(text, href="/", link_text="返回"):
    return page("提示", f'<div class="msg-page"><p>{text}</p><a href="{href}" class="btn btn-primary">{link_text}</a></div>')

# 登录检查装饰器
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

# 初始化数据库
init_database()
init_admin()

# -------------------- 登录页面 --------------------
@app.route('/')
def home():
    if "user" not in session:
        error = request.args.get('error', '')
        error_html = f'<div style="color:var(--danger);font-size:14px;margin-bottom:12px;text-align:center;">{error}</div>' if error else ''
        return page("登录", f'''
        <div style="max-width:400px;margin:60px auto;">
            <div class="card">
                <div class="card-title">系统登录</div>
                {error_html}
                <form method=post action=/login autocomplete=off>
                    <div class="form-group"><label>用户名</label><input name=username></div>
                    <div class="form-group"><label>密码</label><input name=password type=password></div>
                    <div style="margin-top:16px"><button type=submit class=btn-primary style=width:100%>登 录</button></div>
                </form>
            </div>
        </div>
        ''')
    return redirect('/book')

# -------------------- 登录 --------------------
@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('/?error=用户名和密码不能为空')
    u, err = login(username, password)
    if u:
        session["user"] = {"id": u[0], "username": u[1], "real_name": u[2], "role": u[3]}
        add_log(u[0],"登录","用户登录系统")
        return redirect('/book')
    return redirect(f'/?error={err}')

# -------------------- 退出 --------------------
@app.route('/logout')
def logout():
    add_log(session["user"]["id"], "退出", "用户退出系统")
    session.clear()
    return redirect('/')

# -------------------- 用户管理 --------------------
@app.route('/user')
@login_required
def user_list():
    if session.get("user", {}).get("role") != "super":
        flash("无权限访问", "error")
        return redirect("/book")
    ok, users = get_all_users("super")
    # SELECT * FROM user 字段顺序: id, username, password, real_name, work_id, gender, age, role
    user_rows = ""
    for u in users:
        role_badge = '<span class="badge badge-super">超管</span>' if u[7]=='super' else '<span class="badge badge-normal">普通</span>'
        user_rows += f'''
        <tr>
            <td>{u[0]}</td><td>{u[1]}</td><td>{u[3]}</td><td>{u[4]}</td>
            <td>{u[5]}</td><td>{u[6]}</td><td>{role_badge}</td>
            <td>
                <div class="actions">
                <form method=post action=/user/update>
                    <input type=hidden name=user_id value={u[0]}>
                    <input name=real_name value="{u[3]}" placeholder=姓名 style=width:60px>
                    <input name=work_id value="{u[4]}" placeholder=工号 style=width:60px>
                    <input name=gender value="{u[5]}" placeholder=性别 style=width:40px>
                    <input name=age value="{u[6]}" placeholder=年龄 style=width:40px>
                    <select name=role style=width:70px>
                        <option value="super" {"selected" if u[7]=="super" else ""}>超管</option>
                        <option value="normal" {"selected" if u[7]=="normal" else ""}>普通</option>
                    </select>
                    <button type=submit class="btn btn-primary btn-sm">修改</button>
                </form>
                <form method=post action=/user/reset_pwd>
                    <input type=hidden name=user_id value={u[0]}>
                    <button type=submit class="btn btn-warning btn-sm">重置密码</button>
                </form>
                <form method=post action=/user/delete>
                    <input type=hidden name=user_id value={u[0]}>
                    <button type=submit class="btn btn-danger btn-sm" onclick="return confirm('确认删除？')">删除</button>
                </form>
                </div>
            </td>
        </tr>'''
    body = f'''
    <div class="card">
        <div class="card-title">添加用户</div>
        <form method=post action=/user/add>
            <div class="form-group"><label>用户名</label><input name=username></div>
            <div class="form-group"><label>密码</label><input name=password type=password></div>
            <div class="form-group"><label>姓名</label><input name=real_name></div>
            <div class="form-group"><label>工号</label><input name=work_id></div>
            <div class="form-group"><label>性别</label><input name=gender></div>
            <div class="form-group"><label>年龄</label><input name=age type=number></div>
            <button type=submit class=btn-primary>添加用户</button>
        </form>
    </div>
    <div class="card">
        <div class="card-title">CSV导入用户</div>
        <form method=post action=/user/import_csv enctype=multipart/form-data>
            <input type=file name=file accept=.csv>
            <button type=submit class=btn-primary>导入</button>
        </form>
        <p style="color:gray;font-size:12px;margin-top:8px">CSV格式：username,password,real_name,work_id,gender,age（首行标题会自动跳过）</p>
    </div>
    <div class="card">
        <div class="card-title">用户列表</div>
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>用户名</th><th>姓名</th><th>工号</th><th>性别</th><th>年龄</th><th>角色</th><th>操作</th></tr>
            {user_rows}
        </table>
        </div>
    </div>'''
    return page("用户管理", body, "user")

@app.route('/user/add', methods=['POST'])
@login_required
def user_add():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        flash("用户名和密码不能为空", "error")
        return redirect("/user")
    try:
        age = int(request.form['age'])
        if age <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("年龄不能为空或格式错误", "error")
        return redirect("/user")
    ok, msg = add_user(
        session["user"]["role"],
        session["user"]["id"],
        username,
        password,
        request.form['real_name'],
        request.form['work_id'],
        request.form['gender'],
        age
    )
    if not ok:
        flash(msg, "error")
        return redirect("/user")
    flash(msg, "success")
    return redirect('/user')

@app.route('/user/import_csv', methods=['POST'])
@login_required
def user_import_csv():
    if session.get("user", {}).get("role") != "super":
        flash("无权限", "error")
        return redirect("/user")
    f = request.files.get('file')
    if not f:
        flash("请选择文件", "error")
        return redirect("/user")
    reader = csv.reader(io.StringIO(f.read().decode('utf-8')))
    header = next(reader, None)
    users_data = []
    for row in reader:
        if len(row) < 6:
            continue
        users_data.append((row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(), row[4].strip(), row[5].strip()))
    success, fail = import_users_csv(session["user"]["role"], session["user"]["id"], users_data)
    flash(f"导入完成：成功 {success} 条，失败 {fail} 条", "success" if fail == 0 else "warning")
    return redirect("/user")

@app.route('/user/update', methods=['POST'])
@login_required
def user_update():
    try:
        age = int(request.form['age'])
        if age <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("年龄不能为空或格式错误", "error")
        return redirect("/user")
    try:
        user_id = int(request.form['user_id'])
    except (ValueError, TypeError):
        flash("用户ID格式错误", "error")
        return redirect("/user")
    ok, msg = update_user_by_admin(
        session["user"]["role"],
        session["user"]["id"],
        user_id,
        request.form['real_name'],
        request.form['work_id'],
        request.form['gender'],
        age,
        request.form['role']
    )
    if not ok:
        flash(msg, "error")
        return redirect("/user")
    flash("用户信息已修改", "success")
    return redirect('/user')

@app.route('/user/reset_pwd', methods=['POST'])
@login_required
def user_reset_pwd():
    try:
        user_id = int(request.form['user_id'])
    except (ValueError, TypeError):
        flash("用户ID格式错误", "error")
        return redirect("/user")
    ok, msg = reset_password(session["user"]["role"], session["user"]["id"], user_id)
    if not ok:
        flash(msg, "error")
        return redirect("/user")
    flash(msg, "success")
    return redirect('/user')

@app.route('/user/delete', methods=['POST'])
@login_required
def user_delete():
    try:
        user_id = int(request.form['user_id'])
    except (ValueError, TypeError):
        flash("用户ID格式错误", "error")
        return redirect("/user")
    ok, msg = delete_users(session["user"]["role"], session["user"]["id"], user_id)
    if not ok:
        flash(msg, "error")
        return redirect("/user")
    flash(msg, "success")
    return redirect('/user')

# -------------------- 个人中心 --------------------
@app.route('/myinfo')
@login_required
def my_info():
    info = get_my_info(session["user"]["id"])
    if not info:
        flash("用户不存在", "error")
        return redirect("/book")
    # info: id, username, real_name, work_id, gender, age, role
    role_badge = '<span class="badge badge-super">超级管理员</span>' if info[6]=='super' else '<span class="badge badge-normal">普通管理员</span>'
    body = f'''
    <div class="card">
        <div class="card-title">个人信息</div>
        <table>
            <tr><th style="width:100px">用户名</th><td>{info[1]}</td></tr>
            <tr><th>姓名</th><td>{info[2]}</td></tr>
            <tr><th>工号</th><td>{info[3]}</td></tr>
            <tr><th>性别</th><td>{info[4]}</td></tr>
            <tr><th>年龄</th><td>{info[5]}</td></tr>
            <tr><th>角色</th><td>{role_badge}</td></tr>
        </table>
    </div>
    <div class="card">
        <div class="card-title">修改个人信息</div>
        <form method=post action=/myinfo/update>
            <div class="form-group"><label>姓名</label><input name=real_name value="{info[2]}"></div>
            <div class="form-group"><label>性别</label><input name=gender value="{info[4]}" style=width:60px></div>
            <div class="form-group"><label>年龄</label><input name=age type=number value="{info[5]}" style=width:80px></div>
            <button type=submit class=btn-primary>保存修改</button>
        </form>
    </div>
    <div class="card">
        <div class="card-title">修改密码</div>
        <form method=post action=/myinfo/changepwd>
            <div class="form-group"><label>旧密码</label><input name=old_password type=password></div>
            <div class="form-group"><label>新密码</label><input name=new_password type=password></div>
            <button type=submit class=btn-primary>修改密码</button>
        </form>
    </div>'''
    return page("个人中心", body, "myinfo")

@app.route('/myinfo/update', methods=['POST'])
@login_required
def my_info_update():
    try:
        age = int(request.form['age'])
        if age <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("年龄不能为空或格式错误", "error")
        return redirect('/myinfo')
    ok, msg = update_my_info(
        session["user"]["id"],
        request.form['real_name'],
        request.form['gender'],
        age
    )
    if ok:
        session["user"]["real_name"] = request.form['real_name']
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect('/myinfo')

@app.route('/myinfo/changepwd', methods=['POST'])
@login_required
def my_changepwd():
    old_pwd = request.form.get('old_password', '')
    new_pwd = request.form.get('new_password', '')
    if not old_pwd or not new_pwd:
        flash("旧密码和新密码不能为空", "error")
        return redirect('/myinfo')
    ok, msg = change_password(
        session["user"]["id"],
        old_pwd,
        new_pwd
    )
    if ok:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect('/myinfo')

# -------------------- 图书管理 --------------------
@app.route('/book')
@login_required
def book_list():
    keyword = request.args.get('keyword', '').strip()
    price_low = request.args.get('price_low', '').strip()
    price_high = request.args.get('price_high', '').strip()
    # 优先使用价格筛选
    if price_low and price_high:
        try:
            books = get_books_by_price(float(price_low), float(price_high))
        except ValueError:
            books = get_all_books()
    elif keyword:
        books = get_books_by_key_words(keyword)
    else:
        books = get_all_books()
    stock_map = get_all_stock()
    book_rows = ""
    is_super = session.get("user", {}).get("role") == "super"
    for b in books:
        # b: id, isbn, book_name, author, publisher, retail_price
        stock = stock_map.get(b[0], 0)
        stock_style = "color:red;font-weight:bold" if stock <= 5 else ("color:orange;font-weight:bold" if stock <= 20 else "")
        price_display = b[5] if b[5] is not None else "未设置"
        book_rows += f'''
        <tr>
            <td>{b[0]}</td><td>{b[1]}</td><td>{b[2]}</td><td>{b[3]}</td>
            <td>{b[4]}</td><td>{price_display}</td><td style="{stock_style}">{stock}</td>
        </tr>'''
    add_book_card = '''
    <div class="card">
        <div class="card-title">添加图书</div>
        <form method=post action=/book/add>
            <div class="form-group"><label>ISBN</label><input name=isbn></div>
            <div class="form-group"><label>书名</label><input name=book_name></div>
            <div class="form-group"><label>作者</label><input name=author></div>
            <div class="form-group"><label>出版社</label><input name=publisher></div>
            <button type=submit class=btn-primary>添加图书</button>
        </form>
    </div>
    <div class="card">
        <div class="card-title">批量操作</div>
        <div class=form-inline>
            <form method=post action=/book/import_csv enctype=multipart/form-data>
                <input type=file name=file accept=.csv>
                <button type=submit class="btn btn-primary btn-sm">CSV导入</button>
            </form>
            <a href=/book/export_csv class="btn btn-info btn-sm">导出CSV</a>
        </div>
        <p style="color:gray;font-size:12px;margin-top:8px">CSV格式：isbn,book_name,author,publisher</p>
    </div>'''
    body = f'''
    <div class="card">
        <div class="card-title">书籍查询</div>
        <form method=get action=/book class=form-inline>
            <input name=keyword value="{keyword}" placeholder="输入ISBN/书名/作者/出版社" style=width:200px>
            <span style="margin:0 10px">或</span>
            价格从 <input name=price_low value="{price_low}" type=number step=0.01 min=0 style=width:80px>
            到 <input name=price_high value="{price_high}" type=number step=0.01 min=0 style=width:80px>
            <button type=submit class=btn-primary style="margin-left:10px">查询</button>
            <a href=/book class="btn btn-outline">清除</a>
        </form>
    </div>
    {add_book_card if is_super else ''}
    <div class="card">
        <div class="card-title">图书列表</div>
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>ISBN</th><th>书名</th><th>作者</th><th>出版社</th><th>零售价</th><th>库存</th></tr>
            {book_rows}
        </table>
        </div>
    </div>'''
    return page("图书管理", body, "book")

@app.route('/book/add', methods=['POST'])
@login_required
def book_add():
    isbn = request.form.get('isbn', '').strip()
    book_name = request.form.get('book_name', '').strip()
    if not isbn or not book_name:
        flash("ISBN和书名不能为空", "error")
        return redirect("/book")
    ok, msg = add_book(session["user"]["id"], request.form['isbn'], request.form['book_name'], request.form['author'], request.form['publisher'], role=session["user"]["role"])
    if not ok:
        flash(msg, "error")
        return redirect("/book")
    flash(msg, "success")
    return redirect('/book')

@app.route('/book/update', methods=['POST'])
@login_required
def book_update():
    try:
        price_str = request.form.get('price', '').strip()
        price = float(price_str) if price_str else None
        if price is not None and price <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("价格必须为正数", "error")
        return redirect("/book")
    try:
        book_id = int(request.form['book_id'])
    except (ValueError, TypeError):
        flash("图书ID格式错误", "error")
        return redirect("/book")
    ok, msg = update_book(
        session["user"]["id"],
        book_id,
        request.form['book_name'],
        request.form['author'],
        request.form['publisher'],
        price,
        role=session["user"]["role"]
    )
    if not ok:
        flash(msg, "error")
        return redirect("/book")
    flash(msg, "success")
    return redirect('/book')

@app.route('/book/delete', methods=['POST'])
@login_required
def book_delete():
    try:
        book_id = int(request.form['book_id'])
    except (ValueError, TypeError):
        flash("图书ID格式错误", "error")
        return redirect("/book")
    ok, msg = delete_book(session["user"]["id"], book_id, role=session["user"]["role"])
    if not ok:
        flash(msg, "error")
        return redirect("/book")
    flash(msg, "success")
    return redirect('/book')

@app.route('/book/import_csv', methods=['POST'])
@login_required
def book_import_csv():
    f = request.files.get('file')
    if not f:
        flash("请选择文件", "error")
        return redirect("/book")
    reader = csv.reader(io.StringIO(f.read().decode('utf-8')))
    header = next(reader, None)
    books_data = []
    for row in reader:
        if len(row) < 4:
            continue
        try:
            retail_price = float(row[4]) if len(row) > 4 and row[4].strip() else None
            books_data.append((row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(), retail_price))
        except:
            continue
    success, fail = import_books_csv(session["user"]["id"], books_data, role=session["user"]["role"])
    flash(f"导入完成：成功 {success} 条，失败 {fail} 条", "success" if fail == 0 else "warning")
    return redirect("/book")

@app.route('/book/export_csv')
@login_required
def book_export_csv():
    books = get_all_books()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id','isbn','book_name','author','publisher'])
    for b in books:
        writer.writerow([b[0], b[1], b[2], b[3], b[4]])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=books.csv'}
    )

# -------------------- 进货管理 --------------------
@app.route('/purchase')
@login_required
def purchase_list():
    status = request.args.get('status')
    ps = get_all_purchases(status)
    books = get_all_books()
    book_options = ''.join([f'<option value={b[0]}>{b[0]} - {b[2]}</option>' for b in books])
    # 构建book_id->retail_price映射
    book_price_map = {b[0]: b[5] for b in books}
    # purchase 字段: id, user_id, book_id, purchase_price, quantity, status, create_time
    purchase_rows = ""
    for p in ps:
        pid,user_id,book_id,price,qty,st,ctime=p[0],p[1],p[2],p[3],p[4],p[5],p[6]
        total = price * qty
        status_label = {"unpaid": "未付款", "paid": "已付款", "returned": "已退货", "stocked": "已入库"}.get(st, st)
        badge_cls = {"unpaid": "badge-unpaid", "paid": "badge-paid", "returned": "badge-returned", "stocked": "badge-stocked"}.get(st, "")
        actions = ""
        if st == "unpaid":
            actions = f'''
                <div class="actions">
                <form method=get action=/purchase/act>
                    <input type=hidden name=pid value={pid}>
                    <button name=act value=pay class="btn btn-success btn-sm">付款</button>
                    <button name=act value=ret class="btn btn-warning btn-sm">退货</button>
                </form>
                </div>'''
        elif st == "paid":
            existing_price = book_price_map.get(book_id)
            if existing_price is not None:
                price_input = f'<span style="color:var(--success);font-weight:600">{existing_price}元</span>'
            else:
                price_input = '<input name=retail_price type=number step=0.01 style=width:60px placeholder="必填">'
            actions = f'''
                <div class="actions">
                <form method=post action=/purchase/stock_in>
                    <input type=hidden name=pid value={pid}>
                    零售价：{price_input}
                    <button type=submit class="btn btn-info btn-sm">入库</button>
                </form>
                </div>'''
        book_name = ""
        for b in books:
            if b[0] == book_id:
                book_name = b[2]
                break
        purchase_rows += f'''
        <tr>
            <td>{pid}</td><td>{book_id} - {book_name}</td><td>{price}</td><td>{qty}</td>
            <td>{total}</td><td><span class="badge {badge_cls}">{status_label}</span></td><td>{ctime}</td>
            <td>{actions}</td>
        </tr>'''

    active_status = status or ""
    status_filter = f'''
    <div class="filter-bar">
        <a href=/purchase {"class=active" if active_status=="" else ""}>全部</a>
        <a href=/purchase?status=unpaid {"class=active" if active_status=="unpaid" else ""}>未付款</a>
        <a href=/purchase?status=paid {"class=active" if active_status=="paid" else ""}>已付款</a>
        <a href=/purchase?status=stocked {"class=active" if active_status=="stocked" else ""}>已入库</a>
        <a href=/purchase?status=returned {"class=active" if active_status=="returned" else ""}>已退货</a>
    </div>'''

    body = f'''
    <div class="card">
        <div class="card-title">已有图书进货</div>
        <form method=post action=/purchase/add>
            <div class="form-group"><label>图书</label><select name=book_id>{book_options}</select></div>
            <div class="form-group"><label>进货单价</label><input name=price type=number step=0.01></div>
            <div class="form-group"><label>数量</label><input name=quantity type=number></div>
            <button type=submit class=btn-primary>新建进货单</button>
        </form>
    </div>
    <div class="card">
        <div class="card-title">新书进货（库存中无此书时）</div>
        <form method=post action=/purchase/add_new>
            <div class="form-group"><label>ISBN</label><input name=isbn></div>
            <div class="form-group"><label>书名</label><input name=book_name></div>
            <div class="form-group"><label>作者</label><input name=author></div>
            <div class="form-group"><label>出版社</label><input name=publisher></div>
            <div class="form-group"><label>进货单价</label><input name=purchase_price type=number step=0.01></div>
            <div class="form-group"><label>数量</label><input name=quantity type=number></div>
            <button type=submit class=btn-primary>添加新书并进货</button>
        </form>
    </div>
    <div class="card">
        <div class="card-title">进货记录</div>
        {status_filter}
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>图书</th><th>进货单价</th><th>数量</th><th>总价</th><th>状态</th><th>创建时间</th><th>操作</th></tr>
            {purchase_rows}
        </table>
        </div>
    </div>'''
    return page("进货管理", body, "purchase")

@app.route('/purchase/add', methods=['POST'])
@login_required
def purchase_add():
    try:
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        if price <= 0 or quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("单价必须为正数，数量至少为1", "error")
        return redirect("/purchase")
    try:
        book_id = int(request.form['book_id'])
    except (ValueError, TypeError):
        flash("图书ID格式错误", "error")
        return redirect("/purchase")
    ok,msg=create_purchase(session["user"]["id"],book_id,price,quantity)
    if not ok:
        flash(msg, "error")
        return redirect("/purchase")
    flash(msg, "success")
    return redirect('/purchase')

@app.route('/purchase/add_new', methods=['POST'])
@login_required
def purchase_add_new():
    isbn = request.form.get('isbn', '').strip()
    book_name = request.form.get('book_name', '').strip()
    if not isbn or not book_name:
        flash("ISBN和书名不能为空", "error")
        return redirect("/purchase")
    try:
        purchase_price = float(request.form['purchase_price'])
        quantity = int(request.form['quantity'])
        if purchase_price <= 0 or quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("进价必须为正数，数量至少为1", "error")
        return redirect("/purchase")
    author = request.form['author']
    publisher = request.form['publisher']
    ok, msg = add_book(session["user"]["id"], isbn, book_name, author, publisher, role=session["user"]["role"])
    if not ok:
        flash(f"添加图书失败：{msg}", "error")
        return redirect("/purchase")
    book = get_book_by_isbn(isbn)
    if not book:
        flash("图书创建异常", "error")
        return redirect("/purchase")
    ok2,msg2=create_purchase(session["user"]["id"],book[0][0],purchase_price,quantity)
    flash(msg2, "success")
    return redirect('/purchase')

@app.route('/purchase/act')
@login_required
def purchase_act():
    try:
        pid = int(request.args['pid'])
    except (ValueError, TypeError):
        flash("进货单ID格式错误", "error")
        return redirect('/purchase')
    if request.args['act'] == 'pay':
        ok, msg = pay_purchase(session["user"]["id"], pid)
        if not ok:
            flash(msg, "error")
            return redirect('/purchase')
        flash(msg, "success")
    elif request.args['act'] == 'ret':
        ok, msg = return_purchase(session["user"]["id"], pid)
        if not ok:
            flash(msg, "error")
            return redirect('/purchase')
        flash(msg, "success")
    return redirect('/purchase')

@app.route('/purchase/stock_in', methods=['POST'])
@login_required
def purchase_stock_in():
    try:
        pid = int(request.form['pid'])
    except (ValueError, TypeError):
        flash("进货单ID格式错误", "error")
        return redirect("/purchase")
    retail_price_str = request.form.get('retail_price', '').strip()
    retail_price = float(retail_price_str) if retail_price_str else None
    if retail_price is not None and retail_price <= 0:
        flash("零售价必须为正数", "error")
        return redirect("/purchase")
    ok, msg = stock_in_purchase(session["user"]["id"], pid, retail_price)
    if not ok:
        flash(msg, "error")
        return redirect("/purchase")
    flash(msg, "success")
    return redirect('/purchase')

# -------------------- 销售管理 --------------------
@app.route('/sale')
@login_required
def sale_list():
    sales = get_all_sales()
    books = get_all_books()
    stock_map = get_all_stock()
    book_options = ''.join([f'<option value={b[0]}>{b[0]} - {b[2]}（库存:{stock_map.get(b[0],0)}，零售价:{"%.2f" % b[5] if b[5] is not None else "未设置"}）</option>' for b in books if stock_map.get(b[0],0)>0])
    # 构建book_id->retail_price映射，用于JS自动显示
    price_map_js = '{' + ','.join([f'{b[0]}:{b[5]}' for b in books if b[5] is not None]) + '}'

    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    if date_from or date_to:
        filtered = []
        for s in sales:
            # sale 字段: id, user_id, book_id, sale_price, quantity, sale_time
            stime=s[5]
            if date_from and stime < date_from:
                continue
            if date_to and stime > date_to + ' 23:59:59':
                continue
            filtered.append(s)
        sales = filtered

    sale_rows = ""
    for s in sales:
        sid,user_id,book_id,price,qty,stime=s[0],s[1],s[2],s[3],s[4],s[5]
        total = price * qty
        book_name = ""
        for b in books:
            if b[0] == book_id:
                book_name = b[2]
                break
        sale_rows += f'''
        <tr>
            <td>{sid}</td><td>{book_id} - {book_name}</td><td>{price}</td><td>{qty}</td>
            <td>{total}</td><td>{stime}</td>
        </tr>'''
    body = f'''
    <div class="card">
        <div class="card-title">录入销售</div>
        <form method=post action=/sale/add>
            <div class="form-group"><label>图书</label><select name=book_id onchange="document.getElementById('show_price').textContent=price_map[this.value]||''">{book_options}</select></div>
            <div class="form-group"><label>零售价</label><span id=show_price style="font-size:1.2em;font-weight:bold">{books[0][5] if books else ''}</span> 元（系统定价）</div>
            <div class="form-group"><label>数量</label><input name=quantity type=number min=1></div>
            <button type=submit class=btn-primary>确认销售</button>
        </form>
        <script>var price_map={price_map_js}</script>
    </div>
    <div class="card">
        <div class="card-title">销售记录</div>
        <form method=get action=/sale class=form-inline style=margin-bottom:12px>
            日期筛选：从 <input type=date name=date_from value="{date_from}"> 到 <input type=date name=date_to value="{date_to}">
            <button type=submit class="btn btn-primary btn-sm">筛选</button>
            <a href=/sale class="btn btn-outline btn-sm">清除</a>
        </form>
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>图书</th><th>销售单价</th><th>数量</th><th>总价</th><th>时间</th></tr>
            {sale_rows}
        </table>
        </div>
    </div>'''
    return page("销售管理", body, "sale")

@app.route('/sale/add', methods=['POST'])
@login_required
def sale_add():
    try:
        quantity = int(request.form['quantity'])
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("数量至少为1", "error")
        return redirect("/sale")
    try:
        book_id = int(request.form['book_id'])
    except (ValueError, TypeError):
        flash("图书ID格式错误", "error")
        return redirect("/sale")
    ok,msg=create_sale(session["user"]["id"],book_id,quantity)
    if not ok:
        flash(msg, "error")
        return redirect("/sale")
    flash(msg, "success")
    return redirect('/sale')

# -------------------- 库存管理 --------------------
@app.route('/stock')
@login_required
def stock_page():
    search_type = request.args.get('search_type', '').strip()
    search_value = request.args.get('search_value', '').strip()

    if search_type and search_value:
        if search_type == 'id':
            try:
                books = get_book_by_id(int(search_value))
            except (ValueError, TypeError):
                books = []
        elif search_type == 'isbn':
            books = get_book_by_isbn(search_value)
        elif search_type == 'book_name':
            books = get_book_by_bookname(search_value)
        elif search_type == 'author':
            books = get_book_by_author(search_value)
        elif search_type == 'publisher':
            books = get_book_by_publisher(search_value)
        else:
            books = get_all_books()
    else:
        books = get_all_books()

    stock_map = get_all_stock()
    books = sorted(books, key=lambda b: stock_map.get(b[0], 0))
    stock_rows = ""
    low_count = 0
    is_super = session.get("user", {}).get("role") == "super"
    for b in books:
        stock = stock_map.get(b[0], 0)
        if stock <= 5:
            low_count += 1
        stock_style = "color:red;font-weight:bold" if stock <= 5 else ("color:orange;font-weight:bold" if stock <= 20 else "")
        price_display = b[5] if b[5] is not None else "未设置"
        # 操作按钮：修改（弹窗）、删除
        _price_val = b[5] if b[5] is not None else ''
        if is_super:
            edit_btn = '<button type=button class="btn btn-primary btn-sm" onclick="showEditModal(%d, \'%s\', \'%s\', \'%s\', \'%s\')">修改</button>' % (b[0], _html.escape(str(b[2]), True), _html.escape(str(b[3]), True), _html.escape(str(b[4]), True), _html.escape(str(_price_val), True))
            delete_btn = '<form method=post action=/book/delete style="display:inline"><input type=hidden name=book_id value=%d><button type=submit class="btn btn-danger btn-sm" onclick="return confirm(\'确认删除？\')">删除</button></form>' % b[0]
        else:
            edit_btn = ''
            delete_btn = ''
        stock_rows += f'''
        <tr>
            <td>{b[0]}</td><td>{b[1]}</td><td>{b[2]}</td><td>{b[3]}</td>
            <td>{b[4]}</td><td>{price_display}</td><td style="{stock_style}">{stock}</td>
            <td><div style="display:flex;gap:6px;align-items:center">{edit_btn}{delete_btn}</div></td>
        </tr>'''
    alert = f'<div class="alert alert-danger">有 {low_count} 种图书库存不足（≤5）</div>' if low_count > 0 else ''
    search_opts = f'''
    <option value="id" {"selected" if search_type=="id" else ""}>书籍编号</option>
    <option value="isbn" {"selected" if search_type=="isbn" else ""}>ISBN号</option>
    <option value="book_name" {"selected" if search_type=="book_name" else ""}>书名</option>
    <option value="author" {"selected" if search_type=="author" else ""}>作者</option>
    <option value="publisher" {"selected" if search_type=="publisher" else ""}>出版社</option>
    '''
    body = f'''
    <h1>库存管理</h1>
    {alert}
    <div class="card">
        <div class="card-title">库存查询</div>
        <form method=get action=/stock class=form-inline>
            <select name=search_type style=width:100px>{search_opts}</select>
            <input name=search_value value="{search_value}" placeholder="输入查询内容" style=width:200px>
            <button type=submit class=btn-primary>查询</button>
            <a href=/stock class="btn btn-outline">清除</a>
        </form>
    </div>
    <div class="card">
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>ISBN</th><th>书名</th><th>作者</th><th>出版社</th><th>零售价</th><th>库存</th><th>操作</th></tr>
            {stock_rows}
        </table>
        </div>
    </div>
    <!-- 修改图书弹窗 -->
    <div id="editModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);z-index:1000" onclick="if(event.target===this)closeEditModal()">
        <div style="background:#fff;border-radius:8px;padding:24px;max-width:400px;margin:120px auto;box-shadow:0 4px 20px rgba(0,0,0,0.2)">
            <div style="font-size:18px;font-weight:600;margin-bottom:16px;color:var(--primary-dark)">修改图书信息</div>
            <form method=post action=/book/update>
                <input type=hidden name=book_id id=edit_book_id>
                <div class="form-group"><label>书名</label><input name=book_name id=edit_book_name style=width:220px></div>
                <div class="form-group"><label>作者</label><input name=author id=edit_author style=width:220px></div>
                <div class="form-group"><label>出版社</label><input name=publisher id=edit_publisher style=width:220px></div>
                <div class="form-group"><label>零售价</label><input name=price id=edit_price type=number step=0.01 style=width:100px></div>
                <div style="display:flex;gap:10px;margin-top:16px">
                    <button type=submit class="btn btn-primary">完成修改</button>
                    <button type=button class="btn btn-outline" onclick="closeEditModal()">取消</button>
                </div>
            </form>
        </div>
    </div>
    <script>
    function showEditModal(id, name, author, publisher, price) {{
        document.getElementById('edit_book_id').value = id;
        document.getElementById('edit_book_name').value = name;
        document.getElementById('edit_author').value = author;
        document.getElementById('edit_publisher').value = publisher;
        document.getElementById('edit_price').value = price;
        document.getElementById('editModal').style.display = 'block';
    }}
    function closeEditModal() {{
        document.getElementById('editModal').style.display = 'none';
    }}
    </script>'''
    return page("库存管理", body, "stock")

@app.route('/stock/quick_purchase', methods=['POST'])
@login_required
def stock_quick_purchase():
    try:
        book_id = int(request.form['book_id'])
    except (ValueError, TypeError):
        flash("图书ID格式错误", "error")
        return redirect("/stock")
    try:
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        if price <= 0 or quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("进货价必须为正数，数量至少为1", "error")
        return redirect("/stock")
    ok,msg=create_purchase(session["user"]["id"],book_id,price,quantity)
    if not ok:
        flash(msg, "error")
        return redirect("/stock")
    flash(msg, "success")
    return redirect('/stock')

@app.route('/stock/quick_sale', methods=['POST'])
@login_required
def stock_quick_sale():
    try:
        book_id = int(request.form['book_id'])
    except (ValueError, TypeError):
        flash("图书ID格式错误", "error")
        return redirect("/stock")
    try:
        quantity = int(request.form['quantity'])
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("数量至少为1", "error")
        return redirect("/stock")
    ok,msg=create_sale(session["user"]["id"],book_id,quantity)
    if not ok:
        flash(msg, "error")
        return redirect("/stock")
    flash(msg, "success")
    return redirect('/stock')

# -------------------- 财务报告 --------------------
@app.route('/bill')
@login_required
def bill_page():
    books = get_all_books()
    book_map = {b[0]: b[2] for b in books}

    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    bills = get_all_bills()
    if date_from or date_to:
        filtered = []
        for b in bills:
            btime = b[5]
            if date_from and btime < date_from:
                continue
            if date_to and btime > date_to + ' 23:59:59':
                continue
            filtered.append(b)
        bills = filtered

    income = sum(b[2] for b in bills if b[1] == 'income')
    expense = sum(b[2] for b in bills if b[1] == 'expense')
    profit = income - expense

    sales = get_all_sales()
    if date_from or date_to:
        sales = [s for s in sales if
                 (not date_from or s[5] >= date_from) and
                 (not date_to or s[5] <= date_to + ' 23:59:59')]

    book_sales = {}
    for s in sales:
        bid = s[2]
        if bid not in book_sales:
            book_sales[bid] = {'qty': 0, 'total': 0}
        book_sales[bid]['qty'] += s[4]
        book_sales[bid]['total'] += s[3] * s[4]

    ranked = sorted(book_sales.items(), key=lambda x: x[1]['total'], reverse=True)

    bill_rows = ""
    for b in bills:
        btype = "收入" if b[1] == 'income' else "支出"
        badge_cls = "badge-paid" if b[1] == 'income' else "badge-unpaid"
        bill_rows += f'<tr><td>{b[0]}</td><td><span class="badge {badge_cls}">{btype}</span></td><td>{b[2]}</td><td>{b[3]}</td><td>{b[4]}</td><td>{b[5]}</td></tr>'

    rank_rows = ""
    for i, (bid, info) in enumerate(ranked, 1):
        bname = book_map.get(bid, '未知')
        rank_rows += f'<tr><td>{i}</td><td>{bid} - {bname}</td><td>{info["qty"]}</td><td>{info["total"]}</td></tr>'

    period_label = f"{date_from or '起始'} ~ {date_to or '至今'}" if (date_from or date_to) else "全部"

    # ---- 图表数据准备 ----
    # 1. 收支按月汇总
    monthly = OrderedDict()
    for b in bills:
        btime = b[5]
        ym = btime[:7]  # "YYYY-MM"
        if ym not in monthly:
            monthly[ym] = {'income': 0, 'expense': 0}
        if b[1] == 'income':
            monthly[ym]['income'] += b[2]
        else:
            monthly[ym]['expense'] += b[2]
    month_labels = list(monthly.keys())
    month_income = [round(monthly[m]['income'], 2) for m in month_labels]
    month_expense = [round(monthly[m]['expense'], 2) for m in month_labels]
    month_profit = [round(monthly[m]['income'] - monthly[m]['expense'], 2) for m in month_labels]

    # 2. 销售排行榜 Top10
    top10 = ranked[:10]
    rank_names = [book_map.get(bid, '未知')[:8] for bid, _ in top10]
    rank_totals = [round(info['total'], 2) for _, info in top10]

    # 3. 收支比例
    income_pct = round(income / (income + expense) * 100, 1) if (income + expense) > 0 else 0
    expense_pct = round(expense / (income + expense) * 100, 1) if (income + expense) > 0 else 0

    # 4. 销售数量排行 Top10
    rank_qtys = [info['qty'] for _, info in top10]

    body = f'''
    <div class="card">
        <div class="card-title">时间段筛选</div>
        <form method=get action=/bill class=form-inline>
            从 <input type=date name=date_from value="{date_from}"> 到 <input type=date name=date_to value="{date_to}">
            <button type=submit class="btn btn-primary btn-sm">筛选</button>
            <a href=/bill class="btn btn-outline btn-sm">清除</a>
        </form>
    </div>
    <div class="stat-cards">
        <div class="stat-card income"><div class="label">总收入</div><div class="value">{income}</div></div>
        <div class="stat-card expense"><div class="label">总支出</div><div class="value">{expense}</div></div>
        <div class="stat-card profit"><div class="label">净利润</div><div class="value" style="color:{'var(--success)' if profit>=0 else 'var(--danger)'}">{profit}</div></div>
    </div>
    <div style="display:flex;justify-content:flex-end;margin-bottom:10px">
        <button type="button" class="btn btn-outline btn-sm" onclick="toggleCharts()" id="toggleBtn">收起图表</button>
    </div>
    <div id="chartsContainer" style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;transition:all .3s">
        <div class="card" style="margin-bottom:0">
            <div class="card-title">收支对比与利润趋势（按月）</div>
            <canvas id="chartMonthly" height="260"></canvas>
        </div>
        <div class="card" style="margin-bottom:0">
            <div class="card-title">收支占比</div>
            <canvas id="chartPie" height="260"></canvas>
        </div>
        <div class="card" style="margin-bottom:0">
            <div class="card-title">销售金额排行 Top10（{period_label}）</div>
            <canvas id="chartRankAmount" height="260"></canvas>
        </div>
        <div class="card" style="margin-bottom:0">
            <div class="card-title">销售数量排行 Top10（{period_label}）</div>
            <canvas id="chartRankQty" height="260"></canvas>
        </div>
    </div>
    <script>
    function toggleCharts() {{
        var container = document.getElementById('chartsContainer');
        var btn = document.getElementById('toggleBtn');
        if (container.style.display === 'none') {{
            container.style.display = 'grid';
            btn.textContent = '收起图表';
        }} else {{
            container.style.display = 'none';
            btn.textContent = '展开图表';
        }}
    }}
    </script>
    <div class="card">
        <div class="card-title">图书销售排行（{period_label}）</div>
        <div style="overflow-x:auto">
        <table>
            <tr><th>排名</th><th>图书</th><th>销售数量</th><th>销售总额</th></tr>
            {rank_rows if rank_rows else '<tr><td colspan=4 style="color:gray;text-align:center">暂无销售数据</td></tr>'}
        </table>
        </div>
    </div>
    <div class="card">
        <div class="card-title">收支明细（{period_label}）</div>
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>类型</th><th>金额</th><th>关联ID</th><th>备注</th><th>时间</th></tr>
            {bill_rows}
        </table>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <script>
    (function() {{
        var mLabels = {month_labels};
        var mIncome = {month_income};
        var mExpense = {month_expense};
        var mProfit = {month_profit};

        // 收支对比与利润趋势
        new Chart(document.getElementById('chartMonthly'), {{
            type: 'bar',
            data: {{
                labels: mLabels,
                datasets: [
                    {{ label: '收入', data: mIncome, backgroundColor: 'rgba(40,167,69,0.7)', borderRadius: 4 }},
                    {{ label: '支出', data: mExpense, backgroundColor: 'rgba(220,53,69,0.7)', borderRadius: 4 }},
                    {{ label: '利润', data: mProfit, type: 'line', borderColor: 'rgba(74,111,165,1)', backgroundColor: 'rgba(74,111,165,0.1)', fill: true, tension: 0.3, pointRadius: 4, borderWidth: 2 }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ position: 'top' }} }},
                scales: {{
                    y: {{ beginAtZero: true, ticks: {{ callback: function(v){{ return v + '元'; }} }} }}
                }}
            }}
        }});

        // 收支占比饼图
        new Chart(document.getElementById('chartPie'), {{
            type: 'doughnut',
            data: {{
                labels: ['收入 (' + {income_pct} + '%)', '支出 (' + {expense_pct} + '%)'],
                datasets: [{{
                    data: [{income}, {expense}],
                    backgroundColor: ['rgba(40,167,69,0.8)', 'rgba(220,53,69,0.8)'],
                    borderWidth: 2, borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }},
                    tooltip: {{ callbacks: {{ label: function(ctx){{ return ctx.label + ': ' + ctx.parsed + '元'; }} }} }}
                }}
            }}
        }});

        // 销售金额排行
        var rNames = {rank_names};
        var rTotals = {rank_totals};
        new Chart(document.getElementById('chartRankAmount'), {{
            type: 'bar',
            data: {{
                labels: rNames,
                datasets: [{{ label: '销售总额(元)', data: rTotals, backgroundColor: 'rgba(74,111,165,0.7)', borderRadius: 4 }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, ticks: {{ callback: function(v){{ return v + '元'; }} }} }}
                }}
            }}
        }});

        // 销售数量排行
        var rQtys = {rank_qtys};
        new Chart(document.getElementById('chartRankQty'), {{
            type: 'bar',
            data: {{
                labels: rNames,
                datasets: [{{ label: '销售数量', data: rQtys, backgroundColor: 'rgba(23,162,184,0.7)', borderRadius: 4 }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }}
                }}
            }}
        }});
    }})();
    </script>'''
    return page("财务报告", body, "bill")

# -------------------- 操作日志 --------------------
@app.route('/log')
@login_required
def log_page():
    u = session["user"]
    username_kw = request.args.get('username', '').strip()
    action_type = request.args.get('action', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    logs = get_logs_with_filter(u["id"], u["role"], username_kw, action_type, date_from, date_to)

    action_options = ['登录', '退出', '修改用户', '重置密码', '删除用户',
                      '修改密码', '修改个人信息', '添加图书', '修改图书', '删除图书',
                      '新建进货', '新书进货', '进货付款', '进货退货', '图书入库',
                      '录入销售', '快速进货', '快速销售']
    action_opts_html = '<option value="">全部</option>'
    for a in action_options:
        sel = ' selected' if a == action_type else ''
        action_opts_html += f'<option value="{a}"{sel}>{a}</option>'

    log_rows = ""
    for lg in logs:
        log_rows += f'''
        <tr>
            <td>{lg[0]}</td><td>{lg[1]}</td><td>{lg[2]}</td><td>{lg[3] or ''}</td>
            <td>{lg[4]}</td><td>{lg[5] or ''}</td><td>{lg[6]}</td>
        </tr>'''

    role_label = "所有用户" if u["role"] == "super" else "仅自己"
    body = f'''
    <div class="card">
        <div class="card-title">日志筛选（当前可见：{role_label}）</div>
        <form method=get action=/log class=form-inline>
            <input name=username value="{username_kw}" placeholder="用户名/姓名" style=width:120px>
            <select name=action style=width:120px>{action_opts_html}</select>
            从 <input type=date name=date_from value="{date_from}"> 到 <input type=date name=date_to value="{date_to}">
            <button type=submit class="btn btn-primary btn-sm">筛选</button>
            <a href=/log class="btn btn-outline btn-sm">清除</a>
        </form>
    </div>
    <div class="card">
        <div class="card-title">操作日志</div>
        <div style="overflow-x:auto">
        <table>
            <tr><th>ID</th><th>用户ID</th><th>用户名</th><th>姓名</th><th>操作</th><th>详情</th><th>时间</th></tr>
            {log_rows if log_rows else '<tr><td colspan=7 style="color:gray;text-align:center">暂无日志记录</td></tr>'}
        </table>
        </div>
    </div>'''
    return page("操作日志", body, "log")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
