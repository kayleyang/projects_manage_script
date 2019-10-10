#!/usr/bin/env python
# -*-coding:utf-8-*-

import os
import threading
import pymysql
import subprocess
threadLock = threading.Lock()

work_dir = "C:/WorkSpaces/gitlab/"

groupId_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.groupId -q -DforceStdout -f "
artifactId_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.artifactId -q -DforceStdout -f "
version_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.version -q -DforceStdout -f "
packaging_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.packaging -q -DforceStdout -f "


# query = 'select `group`, name, http from projects where id = 2'
query_projects = 'select id, `group`, name, http from projects where `group` <> "front-end" and is_online = 1 and is_offline = 0 order by `group`, name;'
query_items = 'select id, project_id, name, pom, groupId, artifactId, version, packaging from items;'
insert_items = "insert into items (project_id, name, pom, groupId, artifactId, version, packaging) values (%s, %s, %s, %s, %s, %s, %s);"
update_items = "update items set pom = %s, groupId = %s, artifactId = %s, version = %s, packaging = %s where name = %s and project_id = %s ;"

def get_items():
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='mysql123', database='project',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(query_projects)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    for result in results:
        id = result[0]
        group = result[1]
        name = result[2]
        http = result[3]
        http = http.replace('http://', 'http://root:richgo30@', 1)
        MyThread(id, group, name, http).start()


class MyThread(threading.Thread):
    def __init__(self, id, group, name, http):
        threading.Thread.__init__(self)
        self.id = id
        self.group = group
        self.name = name
        self.http = http

    def run(self):
        pull_project(self.group, self.name, self.http)
        # print("结束处理: " + self.group + "/" + self.name)
        poms = find_pom(self.group, self.name, "")
        process_pom(self.id, poms)


def pull_project(group, project, http):

    threadLock.acquire()
    group_path = work_dir + group
    is_exists = os.path.exists(group_path)
    if not is_exists:
        print("创建目录:", group_path)
        os.makedirs(group_path)
    threadLock.release()

    os.chdir(group_path)
    project_path = group_path + "/" + project
    if os.path.exists(project_path):
        if os.path.exists(project_path + "/.git"):
            os.chdir(project_path)
            print(group + '/' + project, "=== 项目已存在，git pull")
            print(group + '/' + project, "===", subprocess.getoutput("git pull"))
        else:
            os.removedirs(project)
            print(group + '/' + project, "=== 目录已存在，删除目录、git clone ", http)
            print(group + '/' + project, "===", subprocess.getoutput("git clone " + http + " " + project_path))
    else:
        print(group + '/' + project, "=== 目录不存在，git clone", http)
        print(group + '/' + project, "===", subprocess.getoutput("git clone " + http + " " + project_path))


def find_pom(group, project, inner_path):

    group_path = work_dir + group
    project_path = group_path + "/" + project

    poms = []
    files = os.listdir(project_path + "/" + inner_path)
    for file in files:
        _inner_path = inner_path + "/" + file
        path = project_path + _inner_path
        if os.path.isfile(path) and file == "pom.xml":
            print("找到", path)
            poms.append(path)
        if os.path.isdir(path) and file != ".git":
            # print("进入", path)
            poms.extend(find_pom(group, project, _inner_path))
    return poms


def process_pom(id, poms):
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='mysql123',
                           database='project',
                           charset='utf8mb4')

    cursor = conn.cursor()
    cursor.execute(query_items)
    results = cursor.fetchall()
    cursor.close()

    items = []
    for pom in poms:
        print("处理", pom)
        item = {
            "project_id": id,
            "name": pom.split('/')[-2],
            "pom": pom.replace(work_dir, ''),
            "groupId": subprocess.getoutput(groupId_cmd + pom),
            "artifactId": subprocess.getoutput(artifactId_cmd + pom),
            "version": subprocess.getoutput(version_cmd + pom),
            "packaging": subprocess.getoutput(packaging_cmd + pom),
        }
        items.append(item)

        cursor = conn.cursor()
        if results is None or len(results) == 0:
            print("插入", item)
            cursor.execute(insert_items, [item['project_id'], item['name'], item['pom'], item['groupId'], item['artifactId'],
                                          item['version'], item['packaging']])
        else:
            for result in results:
                if item['project_id'] == result[1] and item['name'] == result[2]:
                    print("更新", item)
                    cursor.execute(update_items, [item['pom'], item['groupId'], item['artifactId'],
                                                  item['version'], item['packaging'], item['name'], item['project_id']])
                    break

        conn.commit()
        cursor.close()
    conn.close()


get_items()