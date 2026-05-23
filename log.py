from datetime import datetime
from database import get_db
#所有管理员操作日志管理

#添加日志
def add_log(user_id,action,detail=""):
    conn,cursor=get_db()
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO log(user_id,action,detail,create_time)
        VALUES(?,?,?,?)
    ''',(user_id,action,detail,now))
    conn.commit()
    conn.close()
#日志查询
#根据角色查询所有日志
def get_logs_by_role(user_id,role):
    conn,cursor=get_db()
    if role=="super":
        cursor.execute('''
            SELECT l.id,l.user_id,u.username,u.real_name,l.action,l.detail,l.create_time
            FROM log l
            JOIN user u ON l.user_id=u.id
            ORDER BY l.id DESC
        ''')
    else:
        cursor.execute('''
            SELECT l.id,l.user_id,u.username,u.real_name,l.action,l.detail,l.create_time
            FROM log l
            JOIN user u ON l.user_id=u.id
            WHERE l.user_id=?
            ORDER BY l.id DESC
        ''',(user_id,))
    logs=cursor.fetchall()
    conn.close()
    return logs

#条件查询日志
def get_logs_with_filter(user_id,role,username_kw="",action_type="",date_from="",date_to=""):
    conn,cursor=get_db()
    sql='''
        SELECT l.id,l.user_id,u.username,u.real_name,l.action,l.detail,l.create_time
        FROM log l
        JOIN user u ON l.user_id=u.id
        WHERE 1=1
    '''
    params=[]

    if role!="super":
        sql+=" AND l.user_id=?"
        params.append(user_id)

    if username_kw:
        sql+=" AND (u.username LIKE ? OR u.real_name LIKE ?)"
        keyword=f"%{username_kw}%"
        params.extend([keyword,keyword])

    if action_type:
        sql+=" AND l.action=?"
        params.append(action_type)

    if date_from:
        sql+=" AND l.create_time>=?"
        params.append(date_from)
    if date_to:
        sql+=" AND l.create_time<=?"
        params.append(date_to+' 23:59:59')

    sql+=" ORDER BY l.id DESC"

    cursor.execute(sql,params)
    logs=cursor.fetchall()
    conn.close()
    return logs
