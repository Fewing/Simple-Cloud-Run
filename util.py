import sqlite3
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


SECRET_KEY = '\xc9ixnRb\xe40\xc4\xa5\x7f\x04\xd0y6\x02\x1f\x96\xeao+\x8a\x9f\xe4'


def create_token(user_id):
    s = Serializer(SECRET_KEY,
                   expires_in=720000)
    token = s.dumps({"id": user_id}).decode('ascii')
    return token


def verify_token(token):
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except Exception:
        return None
    return data["id"]


def get_username(id):
    # todo
    conn = sqlite3.connect(
        '/Users/zhk/大学/大四上/大数据与云计算/云计算paas平台/Simple-Cloud-Run/sqlite.db')
    cursor = conn.cursor()
    cursor.execute(
        'select * from USER where ID=?', (str(id)))
    values = cursor.fetchall()
    cursor.close()
    conn.close()
    return values[0][1]