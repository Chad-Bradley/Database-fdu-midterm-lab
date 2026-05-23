import sqlite3
import hashlib
from database import get_db
from log import add_log

#用户管理函数

# 转换为MD5
def md5(password):
    return hashlib.md5(password.encode()).hexdigest()

# 登录校验，查询是否有用户名以及对应的密码
def login(username,password):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,username,real_name,role,password
        FROM user
        WHERE username=?
    ''',(username,))
    row=cursor.fetchone()
    conn.close()
    if not row:
        return None,'用户名不存在'
    pwd_md5=md5(password)
    if row[4]!=pwd_md5:
        return None,'密码错误'
    return (row[0],row[1],row[2],row[3]),None

#超级管理员相关操作
#初始化，添加超级管理员账户
def init_admin():
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id FROM user WHERE username='admin'
    ''')
    exists=cursor.fetchone()
    if not exists:
        admin_pwd=md5("123456")
        cursor.execute('''
            INSERT INTO user(username,password,real_name,work_id,gender,age,role)
            VALUES("admin",?,"超级管理员","0001","女",20,"super")
        ''',(admin_pwd,))
        conn.commit()
        print("默认超级管理员已创建")
    conn.close()



#超级管理员添加用户
def add_user(admin_role, operator_id, username, password, real_name, work_id, gender, age):
    if admin_role!="super":
        return False,"权限不足，只有超级管理员可以添加用户"
    pwd_md5=md5(password)
    conn,cursor=get_db()
    try:
        cursor.execute('''
            INSERT INTO user
            (username,password,real_name,work_id,gender,age,role)
            VALUES (?,?,?,?,?,?,?)
        ''',(username,pwd_md5,real_name,work_id,gender,age,"normal"))
        conn.commit()
        conn.close()
        add_log(operator_id, "添加用户", f"添加用户：{username}")
        return True,"用户创建成功"
    except sqlite3.IntegrityError:
        conn.close()
        return False,"用户名或工号已存在"

#超级管理员查询所有用户
def get_all_users(admin_role):
    if admin_role!="super":
        return False,"权限不足"
    conn,cursor=get_db()
    cursor.execute('''
        SELECT * FROM user
    ''')
    users=cursor.fetchall()
    conn.close()
    return True,users

#超级管理员修改某个用户信息
def update_user_by_admin(admin_role, operator_id, user_id, real_name, work_id, gender, age, role):
    if admin_role!="super":
        return False,"权限不足"
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id FROM user
        WHERE work_id=? AND id!=?
    ''',(work_id,user_id))
    if cursor.fetchone():
        conn.close()
        return False,"工号已存在"
    cursor.execute('''
        UPDATE user
        SET real_name=?,work_id=?,gender=?,age=?,role=?
        WHERE id=?
    ''',(real_name,work_id,gender,age,role,user_id))
    conn.commit()
    conn.close()
    add_log(operator_id, "修改用户", f"修改用户ID：{user_id}")
    return True,"用户信息已修改"

#超级管理员重置某个用户密码
def reset_password(admin_role, operator_id, user_id):
    if admin_role!="super":
        return False,"权限不足"
    conn,cursor=get_db()
    new_md5=md5("123456")
    cursor.execute('''
        UPDATE user
        SET password=?
        WHERE id=?
    ''',(new_md5,user_id))
    conn.commit()
    conn.close()
    add_log(operator_id, "重置密码", f"重置用户ID：{user_id}的密码")
    return True,"密码已重置为默认密码"

#超级管理员删除某个用户（不能删除超级管理员）
def delete_users(admin_role, operator_id, user_id):
    if admin_role!="super":
        return False,"权限不足"
    conn,cursor=get_db()
    cursor.execute('''
        SELECT role FROM user WHERE id=?
    ''',(user_id,))
    row=cursor.fetchone()
    if not row:
        return False,"用户不存在"
    if row[0]=="super":
        return False,"不能删除超级管理员"
    cursor.execute('''
        DELETE FROM user
        WHERE id=?
    ''',(user_id,))
    conn.commit()
    conn.close()
    add_log(operator_id, "删除用户", f"删除用户ID：{user_id}")
    return True,"用户已删除"


#普通用户（也包括超级管理员）

#普通用户查询自己信息
def get_my_info(user_id):
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id,username,real_name,work_id,gender,age,role
        FROM user
        WHERE id=?
    ''',(user_id,))
    user_info=cursor.fetchone()
    conn.close()
    return user_info

# 普通用户更新自己的信息
def update_my_info(user_id, real_name, gender, age):
    conn,cursor=get_db()
    cursor.execute('''
        UPDATE user
        SET real_name=?,gender=?,age=?
        WHERE id=?
    ''',(real_name,gender,age,user_id))
    conn.commit()
    conn.close()
    add_log(user_id, "修改个人信息", "修改个人基本信息")
    return True,"个人信息修改成功"

#普通用户修改自己的密码
def change_password(user_id, old_password, new_password):
    old_md5=md5(old_password)
    conn,cursor=get_db()
    cursor.execute('''
        SELECT id
        FROM user
        WHERE id=? AND password=?
    ''',(user_id,old_md5))
    user=cursor.fetchone()
    if not user:
        conn.close()
        return False,"旧密码错误"
    new_md5=md5(new_password)
    cursor.execute('''
        UPDATE user
        SET password=?
        WHERE id=?
    ''',(new_md5,user_id))
    conn.commit()
    conn.close()
    add_log(user_id, "修改密码", "修改个人密码")
    return True,"密码修改成功"

# 批量导入用户（由CSV导入）
def import_users_csv(admin_role, operator_id, users_data):
    """批量导入用户，users_data为列表，每项为(username, password, real_name, work_id, gender, age)"""
    if admin_role != "super":
        return 0, "权限不足"
    
    success = 0
    fail = 0
    conn, cursor = get_db()
    
    for user_data in users_data:
        try:
            username, password, real_name, work_id, gender, age = user_data
            pwd_md5 = md5(password)
            cursor.execute('''
                INSERT INTO user (username, password, real_name, work_id, gender, age, role)
                VALUES (?, ?, ?, ?, ?, ?, 'normal')
            ''', (username, pwd_md5, real_name, work_id, gender, age))
            success += 1
        except sqlite3.IntegrityError:
            fail += 1
    
    conn.commit()
    conn.close()
    
    if success > 0:
        add_log(operator_id, "导入用户", f"CSV导入用户：成功{success}条，失败{fail}条")
    
    return success, fail

if __name__=="__main__":
    init_admin()
