#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
import sys
import requests
import threading
import pymysql
import subprocess
from concurrent.futures import ThreadPoolExecutor

threadLock = threading.Lock()

work_dir = "/root/gitlab/"
# work_dir = "D:/gitlab/"

url = 'http://172.16.165.171/api/v4/'
private_token = '?private_token=NFjuzxfWMQpgucj93kGh'

# query = 'select `group`, name, http from projects where id = 2'
query_projects = 'select id, project_id, namespace, name from projects where is_online = 1 and is_offline = 0;'

query_users = 'select id, project_id, user_id from users where project_id = %s;'
insert_users = "insert into users (project_id, user_id, name, username, web_url, state, access_level) values (%s, %s, %s, %s, %s, %s, %s);"
update_users = "update users set state = %s, access_level = %s where id = %s;"

def get_projects():
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='password', database='project',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(query_projects)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    executor = ThreadPoolExecutor(max_workers=16)
    for result in results:
        project_id = result[1]
        namespace = result[2]
        name = result[3]
        print('开始处理', result)
        # executor.submit(run, project_id)
        run(project_id)


def run(project_id):

    users = []
    per_page = 50
    page = 1
    while True:
        project_users_url = '{0}projects/{1}/members{2}&per_page={3}&page={4}'.format(url, project_id, private_token, per_page, page)
        response = requests.get(project_users_url)

        data = response.json()
        if len(data) == 0:
            break

        for item in data:
            user = {
                'project_id': project_id,
                'user_id': item['id'],
                'name': item['name'],
                'username': item['username'],
                'web_url': item['web_url'],
                'state': item['state'],
                'access_level': item['access_level']
            }
            users.append(user)
        page = page + 1

    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='password',
                           database='project',
                           charset='utf8mb4')

    cursor = conn.cursor()
    cursor.execute(query_users, [project_id])
    results = cursor.fetchall()
    cursor.close()

    for user in users:

        result = get_item_from_db(user, results)
        cursor = conn.cursor()
        if result is None:
            print("插入", user)
            cursor.execute(insert_users, [user['project_id'], user['user_id'], user['name'], user['username'],
                                          user['web_url'], user['state'], user['access_level']])
        else:
            print("更新", user)
            cursor.execute(update_users, [user['state'], user['access_level'], result[0]])

        conn.commit()
        cursor.close()
    conn.close()


def get_item_from_db(user, results):
    if results is None or len(results) == 0:
        return None
    for result in results:
        if user['project_id'] == result[1] and user['user_id'] == result[2]:
            return result


if __name__ == '__main__':
    get_projects()
