# /usr/bin/python
# coding=utf-8
import gitlab

plist = ''


def allprojects():
    #######获取gitlab的所有projects###
    projects = gl.projects.list(all=True)
    for project in projects:
        print(project.name, project.id)


def allgroups():
    #######获取gitlab的所有group名称以及ID###
    all_groups = gl.groups.list(all=True)
    for group in all_groups:
        print(group.name, group.id)


def allusers():
    #######获取gitlab的所有user名称以及ID###
    users = gl.users.list(all=True)
    for user in users:
        print(user.username, user.id, user.name, user.state)


def assgroup():
    #######获取gitlab指定组内所有user以及project名称以及ID信息，本例中组ID为58###
    gid = int(input('Input the group ID: '))
    group = gl.groups.get(gid)
    print(group.name)
    # members = group.members.list(all=True)
    # for me in members:
    #    print(me.username,me.id)
    projects = group.projects.list(all=True)
    for project in projects:
        print(group.name, project.name)
    #######################################


def projectinfo():
    pid = int(input('Input the project ID: '))
    projects = gl.projects.get(pid)
    print(projects.name, projects.http_url_to_repo)


def projectid():
    gid = int(input('Input the group ID: '))
    group = gl.groups.get(gid)
    repo = str(input('Input your repo name: '))
    project = gl.projects.get(group.name + '/' + repo)
    print(project.id)


def assuser():
    #######获取gitlab指定user###
    uid = int(input('Input the user ID: '))
    user = gl.users.get(uid)
    print(user.name)


if __name__ == '__main__':
    gl = gitlab.Gitlab('http://172.16.165.171/', private_token='Lsk82z2hhokfgfa2XPH4')
    info = {1: 'allprojects()', 2: 'allgroups()', 3: 'allusers()', 4: 'projectinfo()', 5: 'projectid()', 6: 'assuser()',
            7: 'assgroup()'}
    serp = '-' * 20
    print('''%s
        1. 列出所有的projects
        2. 列出所有的groups
        3. 列出所有的users
        4. 根据project的ID列出project的所有信息
        5. 列出指定的project ID
        6. 列出指定的user
        7. 列出指定的组内的信息  
        %s''' % (serp, serp))
    num = int(input('Input yout choice: '))
    exec(info[num])
