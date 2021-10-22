from os import name
from flask import Flask
from flask import request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

import docker
import sqlite3
import git
import time


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
    conn = sqlite3.connect('sqlite.db')
    cursor = conn.cursor()
    cursor.execute('select * from USER where NAME=?', (username,))
    values = cursor.fetchall()
    if(len(values) != 0):
        cursor.close()
        conn.close()
        return{
            'success': False,
            'message': '用户名已存在'}
    cursor.execute(
        "INSERT INTO USER (ID,NAME,PASSWORD) VALUES (NULL,?,?)", (username, password))
    cursor.close()
    conn.commit()
    conn.close()
    return{
        'success': True,
        'message': '注册成功'}


@app.route("/login", methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('sqlite.db')
    cursor = conn.cursor()
    cursor.execute(
        'select * from USER where NAME=? AND PASSWORD=?', (username, password))
    values = cursor.fetchall()
    cursor.close()
    conn.close()
    if(len(values) != 0):
        id = values[0][0]
        data = {'token': create_token(id)}
        return{
            'success': True,
            'data': data}
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


@app.route("/deploy", methods=["POST"])
def deploy():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        repo_name = request.form['repo_name']
        repo_url = request.form['repo_url']
        port = int(request.form['port'])
        if port < 5000 and port > 65535:
            return{
                'success': False,
                'message': '端口范围错误'}
        conn = sqlite3.connect('sqlite.db')
        cursor = conn.cursor()
        cursor.execute(
            'select * from USER where ID=?', (str(id)))
        values = cursor.fetchall()
        username = values[0][1]
        cursor.close()
        conn.close()
        git_path = f'temp/{username}/{repo_name}-{str(int(time.time()))}'
        repo = git.Repo.clone_from(
            url=repo_url, to_path=git_path)

        client = docker.from_env()
        image_name = f'{username}/{repo_name}'
        if len(client.images.list(name = image_name)) > 0:
            return{
                'success': False,
                'message': '项目已存在'}
        image, logs = client.images.build(
            path=git_path, tag=image_name, rm=True)
        output = ''
        for log in logs:
            if 'stream' in log:
                output += log['stream']

        container = client.containers.run(image_name, ports={'80/tcp': port},
                                          name=f'{username}-{repo_name}-{str(int(time.time()))}',
                                          detach=True, environment=["PORT=80"])
        client.close()
        return{
            'success': True,
            'output': output}


if __name__ == "__main__":
    app.run(host="::", port=5000)
