#!/usr/bin/env python
# -*-coding:utf-8-*-

import pymysql
import subprocess

work_dir = "D:/gitlab/"

groupId_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.groupId -q -DforceStdout -f "
artifactId_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.artifactId -q -DforceStdout -f "
version_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.version -q -DforceStdout -f "
packaging_cmd = "mvn org.apache.maven.plugins:maven-help-plugin:3.2.0:evaluate -Dexpression=project.packaging -q -DforceStdout -f "

query_items = 'select id, pom from items where groupId = "";'
update_items = 'update items set groupId = %s, artifactId = %s, version = %s, packaging = %s where id = %s ;'


def update_items_pom():
    conn = pymysql.connect(host='172.16.162.211', port=3306, user='root', password='mysql123', database='project',
                           charset='utf8mb4')

    cursor = conn.cursor()
    cursor.execute(query_items)
    results = cursor.fetchall()
    cursor.close()

    for result in results:
        project = {
            "id": result[0],
            "groupId": subprocess.getoutput(groupId_cmd + work_dir + result[1]),
            "artifactId": subprocess.getoutput(artifactId_cmd + work_dir + result[1]),
            "version": subprocess.getoutput(version_cmd + work_dir + result[1]),
            "packaging": subprocess.getoutput(packaging_cmd + work_dir + result[1]),
        }
        print("更新", project)
        cursor = conn.cursor()
        cursor.execute(update_items, [project['groupId'], project['artifactId'], project['version'], project['packaging'], project['id']])
        conn.commit()
        cursor.close()
    conn.close()


update_items_pom()
