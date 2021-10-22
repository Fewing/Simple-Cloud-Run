from flask import Flask
from flask import request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

import docker
import sqlite3

client = docker.from_env()

conn = sqlite3.connect('sqlite.db')

app = Flask(__name__)
SECRET_KEY = '\xc9ixnRb\xe40\xc4\xa5\x7f\x04\xd0y6\x02\x1f\x96\xeao+\x8a\x9f\xe4'


def create_token(user_id):
    s = Serializer(SECRET_KEY,
                   expires_in=7200)
    token = s.dumps({"id": user_id}).decode('ascii')
    return token


def verify_token(token):
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except Exception:
        return None
    return data["id"]


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/register", methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    cursor = conn.cursor()
    cursor.execute('select * from USER where NAME=?', (username,))
    values = cursor.fetchall()
    if(len(values) != 0):
        cursor.close()
        return{
            'success': False,
            'message': '用户名已存在'}
    cursor.execute(
        "INSERT INTO USER (ID,NAME,PASSWORD) VALUES (NULL,?,?)", (username, password))
    cursor.close()
    conn.commit()
    return{
        'success': True,
        'message': '注册成功'}


@app.route("/login", methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    cursor = conn.cursor()
    cursor.execute(
        'select * from USER where NAME=? AND PASSWORD=?', (username, password))
    values = cursor.fetchall()
    cursor.close()
    if(len(values) != 0):
        id = values[0][0]
        data = {'token': create_token(id)}
        return{
            'success': True,
            'data': data},
    else:
        return{
            'success': False,
            'message': '用户名或密码不正确'}


@app.route("/images", methods=['GET'])
def user_imags():
    if request.headers.has_key('token'):
        id = verify_token(request.headers.get('token'))

@app.route("/containers", methods=['GET'])
def user_containers():
    if request.headers.has_key('token'):
        id = verify_token(request.headers.get('token'))
    


if __name__ == "__main__":
    app.run(host="::", port=5000)
