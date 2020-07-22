#!/usr/bin/env python
# -*-coding:utf-8-*-

import requests
import pymysql

url = 'http://172.16.165.171/api/v4/'
private_token = '?private_token=NFjuzxfWMQpgucj93kGh'


def get_projects():
    projects = []
    per_page = 50
    page = 1
    while True:
        projects_url = '{0}projects{1}&per_page={2}&page={3}'.format(url, private_token, per_page, page)
        response = requests.get(projects_url)
        data = response.json()
        if len(data) == 0:
            break
        for item in data:
            project = {
                'git': item['ssh_url_to_repo'],
                'http': item['http_url_to_repo'],
                'name': item['name'],
                'group': item['namespace']['name'],
                'description': item['description']
            }
            if 'front-end' in project['git']:
                continue
            projects.append(project)
        page = page + 1
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='password', database='project',
                           charset='utf8mb4')

    query = 'select id, name, `group`, description, git, http from projects'
    update = 'update projects set description = %s, git = %s, http = %s where id = %s'
    insert = "insert into projects (name, `group`, description, git, http) values (%s, %s, %s, %s, %s);"

    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    for project in projects:
        result = get_item_from_db(project, results)
        if result is not None:
            print('项目[', project['group'], '/', project['name'], '] 在数据库中已存在')
            if project['description'] != result[3] or project['git'] != result[4] or project['http'] != result[5]:
                cursor = conn.cursor()
                print('更新 id 为', result[0], project)
                cursor.execute(update, [project['description'], project['git'], project['http'], result[0]])
                conn.commit()
                cursor.close()
        else:
            cursor = conn.cursor()
            print('插入', project)
            cursor.execute(insert, [project['name'], project['group'], project['description'], project['git'], project['http']])
            conn.commit()
            cursor.close()
    conn.close()


def get_item_from_db(project, results):
    if results is None or len(results) == 0:
        return None
    for result in results:
        if project['name'] == result[1] and project['group'] == result[2]:
            return result


if __name__ == '__main__':
    get_projects()
