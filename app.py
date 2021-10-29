from flask import Flask
from flask import request
from flask_cors import CORS
from util import create_token, verify_token, get_username

import docker
import sqlite3
import git
import time


app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/register", methods=['POST'])
def register():
    username = request.form['username']
    if(not username.isalnum()):
        return{
            'success': False,
            'message': '用户名仅能包含数字或字母'}
    username = username.lower()
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
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        client = docker.from_env()
        data = []
        for image in client.images.list():
            if len(image.attrs['RepoTags']) == 0:
                continue
            name = str(image.attrs['RepoTags'][0])
            if (name.split('/')[0] == username):
                containers = []
                for container in client.containers.list(all=True):
                    if str(container.image.attrs['RepoTags'][0]) == name:
                        containers.append(container.name.split('-')[1])
                data.append({
                    'name': name.split('/')[1].split(':')[0],
                    'url': image.labels['url'],
                    'history': image.history(),
                    'created': str(image.attrs['Created']),
                    'size': str(image.attrs['Size']),
                    'architecture': str(image.attrs['Architecture']),
                    'containers': containers,
                })
        return{
            'success': True,
            'data': data}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/images/delete", methods=['POST'])
def delete_imags():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        repo_name = str(request.form['image_name'])
        image_name = f'{username}/{repo_name}'
        client = docker.from_env()
        for container in client.containers.list(all=True):
            if str(container.image.attrs['RepoTags'][0]).split(":")[0] == image_name:
                return{
                    'success': False,
                    'message': '镜像正在被容器使用'}
        client.images.remove(image_name)
        return{
            'success': True,
            'message': '删除成功'}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/images/rename", methods=['POST'])
def rename_imags():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        repo_name = str(request.form['image_name'])
        new_repo_name = str(request.form['new_image_name'])
        image_name = f'{username}/{repo_name}'
        client = docker.from_env()
        image = client.images.get(image_name)
        image.tag(f'{username}/{new_repo_name}')
        client.images.remove(image_name)
        return{
            'success': True,
            'message': '重命名镜像成功'}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/build-image", methods=['POST'])
def build_image():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        repo_name = request.form['image_name']
        if(not repo_name.isalnum()):
            return{
                'success': False,
                'message': '镜像名仅能包含数字或字母'}
        repo_name = repo_name.lower()
        repo_url = request.form['repo_url']
        username = get_username(id)
        git_path = f'temp/{username}/{repo_name}-{str(int(time.time()))}'
        repo = git.Repo.clone_from(
            url=repo_url, to_path=git_path)

        client = docker.from_env()
        client.images.prune(filters={
            'dangling': True
        })
        image_name = f'{username}/{repo_name}'
        if len(client.images.list(name=image_name)) > 0:
            return{
                'success': False,
                'message': '镜像名已存在'}
        image, logs = client.images.build(
            path=git_path, tag=image_name, labels={'url': repo_url}, rm=True, forcerm=True)
        client.images.prune(filters={
            'dangling': True
        })
        output = ''
        for log in logs:
            if 'stream' in log:
                output += log['stream']

        client.close()
        return{
            'success': True,
            'data': output}
    else:
        return{
            'success': False,
            'data': "token无效"}


@app.route("/containers", methods=['GET'])
def user_containers():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        client = docker.from_env()
        data = []
        for container in client.containers.list(all=True):
            name = str(container.name)
            if name.split('-')[0] == username:
                data.append({
                    'name': name.split('-')[1],
                    'status': container.status,
                    'port': container.ports['80/tcp'][0]['HostPort'],
                    'created': container.attrs['Created'],
                    'image': str(container.image.attrs['RepoTags'][0].split('/')[1].split(':')[0])
                })
        return{
            'success': True,
            'data': data}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/containers/stop", methods=['POST'])
def pause_container():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        container_name = f'{username}-{request.form["container_name"]}'
        client = docker.from_env()
        for container in client.containers.list(all=True):
            if container.name == container_name:
                container.pause()
        return{
            'success': True,
            'message': '停止成功'}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/containers/start", methods=['POST'])
def start_container():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        container_name = f'{username}-{request.form["container_name"]}'
        client = docker.from_env()
        for container in client.containers.list(all=True):
            if container.name == container_name:
                container.unpause()
        return{
            'success': True,
            'message': '启动成功'}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/containers/log", methods=['POST'])
def container_log():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        container_name = f'{username}-{request.form["container_name"]}'
        client = docker.from_env()
        data = {}
        for container in client.containers.list(all=True):
            if container.name == container_name:
                data = {
                    "log": container.logs().decode('utf-8')
                }
        return{
            'success': True,
            'data': data}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/containers/modify", methods=['POST'])
def modify_container():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        container_name = f'{username}-{request.form["container_name"]}'
        new_container_name = request.form["new_container_name"]
        port = request.form['port']
        client = docker.from_env()
        for container in client.containers.list(all=True):
            if container.name == container_name:
                container.stop()
                container.remove()
                container = client.containers.run(container.image.attrs['RepoTags'][0].split(':')[0], ports={'80/tcp': port},
                                                  name=f'{username}-{new_container_name}',
                                                  detach=True, environment=["PORT=80"])
        return{
            'success': True,
            'message': "修改成功"}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/containers/delete", methods=['POST'])
def delete_container():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        username = get_username(id)
        container_name = f'{username}-{request.form["container_name"]}'
        client = docker.from_env()
        for container in client.containers.list(all=True):
            if container.name == container_name:
                container.stop()
                container.remove()
        return{
            'success': True,
            'message': '删除成功'}
    return{
        'success': False,
        'data': "token无效"}


@app.route("/run-image", methods=['POST'])
def run_image():
    if 'token' in request.headers:
        id = verify_token(request.headers.get('token'))
        if id == None:
            return{
                'success': False,
                'data': "token无效"}
        container_name = str(request.form['container_name'])
        if(not container_name.isalnum()):
            return{
                'success': False,
                'message': '容器名仅能包含数字或字母'}
        repo_name = str(request.form['image_name'])
        port = int(request.form['port'])
        if port < 5000 and port > 65535:
            return{
                'success': False,
                'message': '端口范围错误'}
        if(not container_name.isalnum()):
            return{
                'success': False,
                'message': '容器名仅能包含数字或字母'}
        username = get_username(id)
        client = docker.from_env()
        image_name = f'{username}/{repo_name}'
        if len(client.images.list(name=image_name)) > 0:
            container = client.containers.run(image_name, ports={'80/tcp': port},
                                              name=f'{username}-{container_name}',
                                              detach=True, environment=["PORT=80"])
            return{
                'success': True,
                'message': '容器运行成功'}
        else:
            return{
                'success': False,
                'message': '镜像不存在'}
    return{
        'success': False,
        'data': "token无效"}


if __name__ == "__main__":
    app.run(host="::", port=4999)
