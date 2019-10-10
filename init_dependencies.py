#!/usr/bin/env python
# -*-coding:utf-8-*-

import pymysql
import subprocess
import threading

work_dir = "D:/gitlab/"
dependency_cmd = "mvn dependency:list -f %s%s"

query_items = 'select id, name, pom from items '
query_dependencies = 'select id, groupId, artifactId, version, scope from dependencies where item_id = %s '
insert = 'insert into dependencies (item_id, groupId, artifactId, version, scope) values (%s, %s, %s, %s, %s)'
update = 'update dependencies set version = %s , scope = %s where id = %s '


def get_dependencies():
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='mysql123', database='project',
                           charset='utf8mb4')

    cursor = conn.cursor()
    cursor.execute(query_items)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    for result in results:
        MyThread(result).start()


class MyThread(threading.Thread):
    def __init__(self, result):
        threading.Thread.__init__(self)
        self.result = result

    def run(self):
        process_item(self.result)


def process_item(item):
    item_id = item[0]
    item_name = item[1]
    item_pom = item[2]
    cmd = dependency_cmd % (work_dir, item_pom)
    print("查找依赖", item_name, cmd)
    dependencies = subprocess.getoutput(cmd)

    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='mysql123', database='project',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(query_dependencies, item_id)
    results = cursor.fetchall()
    cursor.close()
    for line in dependencies.split('\n'):
        if line.startswith('[INFO]    '):
            dependency = line[10:].split(':')
            dependency_groupId = dependency[0]
            dependency_artifactId = dependency[1]
            dependency_version = dependency[3]
            dependency_scope = dependency[4]

            has_data = False
            cursor = conn.cursor()
            for result in results:
                if result[1] == dependency_groupId and result[2] == dependency_artifactId:
                    has_data = True
                    print('存在依赖', dependency)
                    if result[3] != dependency_version or result[4] != dependency_scope:
                        print('更新依赖', dependency)
                        cursor.execute(update, [dependency_version, dependency_scope, result[0]])
                    break
            if not has_data:
                print('插入依赖', dependency)
                cursor.execute(insert, [item_id, dependency_groupId, dependency_artifactId, dependency_version, dependency_scope])
            conn.commit()
            cursor.close()
    conn.close()


get_dependencies()
