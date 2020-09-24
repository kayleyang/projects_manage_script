#!/usr/bin/env python
# -*-coding:utf-8-*-

import pymysql
import subprocess
from concurrent.futures import ThreadPoolExecutor
work_dir = '/root/gitlab/'
dependency_cmd = 'mvn dependency:list -f %s%s'

query_items = 'select id, name, pom from items /*where project_id in (102, 103)*/ '
query_dependencies = 'select id, groupId, artifactId, version, scope from dependencies where item_id = %s '
insert = 'insert into dependencies (item_id, groupId, artifactId, version, scope) values (%s, %s, %s, %s, %s)'
update = 'update dependencies set version = %s , scope = %s where id = %s '
delete_by_id = 'delete from dependencies where id = %s '
delete_by_item = 'delete from dependencies where item_id = %s '


def get_dependencies():
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='password', database='project',
                           charset='utf8mb4')

    cursor = conn.cursor()
    cursor.execute(query_items)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    executor = ThreadPoolExecutor(max_workers=16)
    for result in results:
        executor.submit(process_item, result)
        # process_item(result)


def process_item(item):
    item_id = item[0]
    item_name = item[1]
    item_pom = item[2]
    cmd = dependency_cmd % (work_dir, item_pom)
    print('--------------------------------------')
    print(item_name, ' 查找依赖 ', cmd)
    dependencies_lines = subprocess.getoutput(cmd)

    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='password', database='project',
                           charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute(query_dependencies, item_id)
    dependencies_db = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()

    dependencies = []
    building_count = 0
    for line in dependencies_lines.split('\n'):
        if line.startswith('[INFO] Building'):
            building_count = building_count + 1
        if building_count >= 2:
            break
        if line.startswith('[INFO]    ') and len(line.split(':')) == 5:
            dependency = line[10:].split(':')
            dependencies.append(dependency)

    if len(dependencies) == 0:
        print(item_name, ' 没有依赖 itemId:', item_id, ' ', item_pom)
        cursor.execute(delete_by_item, [item_id])
    else:
        for dependency in dependencies:
            group_id = dependency[0]
            artifact_id = dependency[1]
            version = dependency[3]
            scope = dependency[4]
            is_in_db = False
            for dependency_db in dependencies_db:
                if dependency_db[1] == group_id and dependency_db[2] == artifact_id:
                    is_in_db = True
                    print(item_name, ' 存在依赖', dependency_db)
                    if dependency_db[3] != version or dependency_db[4] != scope:
                        print(item_name, ' 更新依赖', dependency_db)
                        cursor.execute(update, [version, scope, dependency_db[0]])
                        conn.commit()
                    break
            if not is_in_db:
                print(item_name, ' 插入依赖', dependency)
                cursor.execute(insert, [item_id, group_id, artifact_id, version, scope])
                conn.commit()
        for dependency_db in dependencies_db:
            is_in_db = False
            for dependency in dependencies:
                group_id = dependency[0]
                artifact_id = dependency[1]
                if dependency_db[1] == group_id and dependency_db[2] == artifact_id:
                    is_in_db = True
                    break
            if not is_in_db:
                print(item_name, ' 移除依赖', dependency_db)
                cursor.execute(delete_by_id, [dependency_db[0]])
                conn.commit()

    cursor.close()
    conn.close()


if __name__ == '__main__':
    get_dependencies()
