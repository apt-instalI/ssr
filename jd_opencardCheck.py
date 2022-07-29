#!/usr/bin/python3
# -*- coding: utf8 -*-
"""
# 注意！不支持青龙2.10.3以下版本
# 如果请求api.github.com失败请自行想办法，用拉库用的Github加速代理是没用的
# 青龙里面要有监控的Github仓库的拉库命令，通过监控Github仓库来查看是否有新的开卡脚本
# 如果发现新的开卡脚本则自动拉库并运行开卡脚本，如果发现已有多个相同开卡脚本时
# 且其中一个开卡脚本已经运行过了或者正在运行，之后更新的开卡脚本将不会再运行

# 填写要监控的GitHub仓库的 用户名/仓库名/分支/脚本关键词
# 监控多个仓库请用 & 隔开
export GitRepoHost="KingRan/KR/main/opencardL&feverrun/my_scripts/main/jd_opencard&smiek2121/scripts/master/opencard&okyyds/yyds/master/lzdz1"
# GitHub Token，可以将访问次数提升到5000次，默认60次
export GitToken="用户名&Token"
# http代理，访问不了github的可以填上
export GitProxy="http://127.0.0.1:8080"
# 运行开卡脚本前禁用开卡脚本定时任务，不填则不禁用，保留原有定时
export opencardDisable="true"

version: 7.29.1
cron: */5 0-3 * * *
new Env('开卡更新检测')
"""

from time import sleep
from notify import send
import requests,json,os,difflib

List=[]
def log(content):
    print(content)
    List.append(content)

def qltoken():
    if os.path.exists("/ql/data"):
        path = "/ql/data"
    else:
        path = "/ql"
    with open(f"{path}/config/auth.json", 'rb') as json_file:
        authjson = json.load(json_file)
    if "token" in authjson:
        token = authjson["token"]
        return token
    else:
        log("青龙Token获取失败")
        return

def qlversion():
    url = qlhost+"/system"
    rsp = session.get(url=url,headers=headers)
    jsons = rsp.json()
    if rsp.status_code == 200:
        if "data" in jsons:
            if "version" in jsons["data"]:
                v = jsons["data"]["version"].split(".")
                log("当前青龙版本："+jsons["data"]["version"])
                if int(v[0])<=2 and int(v[1])>=13: # 大于等于2.13.0，小于3.0.0
                    version = {"path":"/ql/data","api":"/subscriptions","id":"id"}
                elif int(v[0])<=2 and int(v[1])>=12: # 大于等于2.12.0，小于2.13.0
                    version = {"path":"/ql/data","api":"/crons","id":"id"}
                elif int(v[0])<=2 and int(v[1])>=11: # 大于等于2.11.0 小于2.12.0 
                    version = {"path":"/ql","api":"/crons","id":"id"}
                elif int(v[0])<=2 and int(v[1])>=10 and int(v[2])>=3: # 大于等于2.10.3 小于2.11.0
                    version = {"path":"/ql","api":"/crons","id":"_id"}
            else:
                version = {"path":"/ql","api":"/crons","id":"_id"}
            return version
    else:
        log(f'请求青龙失败：{url}')
        if "message" in jsons:
            log(f'错误信息：{jsons["message"]}')
        return False

def qlcron(name,repopath):
    url = qlhost+"/crons?searchValue="+name
    if version["api"]=="/subscriptions" and repopath!="False":
        url = qlhost+version["api"]
    rsp = session.get(url=url, headers=headers)
    jsons = rsp.json()
    if rsp.status_code == 200:
        if len(jsons["data"]):
            if version["api"]=="/subscriptions" and repopath!="False":
                for x in jsons["data"]:
                    if x["alias"]== repopath:
                        log("获取任务成功："+x["name"])
                        return x["name"],[x[version["id"]]]
            else:
                cronID = jsons["data"][0][version["id"]]
                log("获取任务成功："+jsons["data"][0]["name"])
                return jsons["data"][0]["name"],[cronID]
        else:
            log(f"没有找到任务：{name}")
            return False,False
    else:
        log(f'请求青龙失败：{url}')
        if "message" in jsons:
            log(f'错误信息：{jsons["message"]}')
        return False,False

def qlrepo(scriptsName):
    repopath = Repo[0]+"_"+Repo[1]
    if os.path.exists(path+"/scripts/"+repopath):
        if os.path.exists(path+"/scripts/"+repopath+"_"+Repo[2]):
            log(f"存在两个仓库：{repopath}和"+repopath+"_"+Repo[2])
            return
    else:
        repopath = repopath+"_"+Repo[2]
        if not os.path.exists(path+"/scripts/"+repopath):
            log(f"没有找到仓库：{repopath}")
            return
    url = qlhost+version["api"]+"/run"
    RepoName,RepoID = qlcron(GitRepo,repopath)
    if not RepoName:
        log(f"获取仓库任务信息失败：{GitRepo}")
        return
    rsp = session.put(url=url,headers=headers,data=json.dumps(RepoID))
    if rsp.status_code == 200:
        log(f"运行拉库任务：{RepoName}")
        ii=0
        scriptsFile = path+"/scripts/"+repopath+"/"+scriptsName
        while not os.path.exists(scriptsFile):
            if ii>=60:
                log(f"找不到文件：{scriptsFile}")
                return
            sleep(1)
            ii+=1
        else:
            sleep(5)
            return True
    else:
        log(f'请求青龙失败：{url}')
        if "message" in rsp.json():
            log(f'错误信息：{rsp.json()["message"]}')
        return

def qltask(scriptsName):
    TaskName,TaskID = qlcron(scriptsName,"False")
    if not TaskName:
        log(f"获取开卡任务信息失败：{scriptsName}")
        return
    if 'opencardDisable' in os.environ:
        Disable = os.environ['opencardDisable']
        if Disable=="true":
            url = qlhost+"/crons/disable"
            rsp = session.put(url=url,headers=headers,data=json.dumps(TaskID))
            if rsp.status_code == 200:
                log(f"禁用开卡任务：{TaskName}")
            else:
                log(f'请求青龙失败：{url}')
                if "message" in rsp.json():
                    log(f'错误信息：{rsp.json()["message"]}')
                return
    if not os.path.exists(f"./nameCron.json"):
        with open(f"./nameCron.json","w") as f:
            json.dump({},f)
        log(f"没有找到nameCron.json文件！将自动生成")
    with open('./nameCron.json',"r",encoding='UTF-8') as f:
        TaskStr = json.load(f)
    for i in TaskStr:
        if i != Repo[0]:
            for x in TaskStr[i]:
                point = round(difflib.SequenceMatcher(None,TaskName,x).quick_ratio()*100)
                if point>=70:
                    log(f"任务名高度相似：{TaskName}/{x}={point}%")
                    log("放弃运行任务："+TaskName)
                    with open(f"./nameCron.json","w",encoding='UTF-8') as f:
                        json.dump(TaskStr,f)
                        log(f"保存任务名到nameCron.json文件")
                    return
    # 运行开卡任务
    url = qlhost+"/crons/run"
    rsp = session.put(url=url,headers=headers,data=json.dumps(TaskID))
    if rsp.status_code == 200:
        log(f"运行开卡任务：{TaskName}")
        with open(f"./nameCron.json","w",encoding='UTF-8') as f:
            if Repo[0] not in TaskStr:
                # log("未找到key："+Repo[0])
                TaskStr[Repo[0]]=[]
            TaskStr[Repo[0]].append(TaskName)
            json.dump(TaskStr,f)
            log(f"保存任务名到nameCron.json文件")
    else:
        log(f'请求青龙失败：{url}')
        if "message" in rsp.json():
            log(f'错误信息：{rsp.json()["message"]}')

def github():
    log(f"\n监控仓库：https://github.com/{GitRepo}")
    gitapi = f'https://api.github.com/repos/{GitRepo}/git/trees/{GitBranch}'
    if 'GitToken' in os.environ:
        GitToken = os.environ['GitToken'].split("&")
        rsp = session.get(url=gitapi,auth=(GitToken[0],GitToken[1]),headers={"Content-Type":"application/json"},proxies=proxies)
    else:
        rsp = session.get(url=gitapi,headers={"Content-Type":"application/json"},proxies=proxies)
    if rsp.status_code != 200:
        log(f'请求GitHub失败：{gitapi}')
        if "message" in rsp.json():
            log(f'错误信息：{rsp.json()["message"]}')
        return False
    else:
        tree = []
        for x in rsp.json()["tree"]:
            if Repo[3] in x["path"]:
                tree.append(x["path"])
        return tree

def check():
    state = False
    if not os.path.exists(f"./nameScripts.json"):
        with open(f"./nameScripts.json","w") as f:
            json.dump({},f)
        log(f"没有找到nameScripts.json文件！将自动生成")
    with open(f"./nameScripts.json", 'rb') as json_file:
        scriptsJson = json.load(json_file)
        if Repo[0] not in scriptsJson:
            scriptsJson[Repo[0]]=tree
            # log("nameScripts.json中未找到KEY："+Repo[0])
    for scriptsName in tree:
        if scriptsName not in scriptsJson[Repo[0]]:
            log(f"新增开卡脚本：{scriptsName}")
            repoPull = qlrepo(scriptsName)
            if repoPull:
                qltask(scriptsName)
            state = True
            break
    else:
        log("没有新增开卡脚本")
    with open(f"./nameScripts.json","w") as f:
        scriptsJson[Repo[0]]=tree
        json.dump(scriptsJson,f)
        log(f"保存文件名到nameScripts.json文件")
    return state

if 'GitRepoHost' in os.environ:
    RepoHost = os.environ['GitRepoHost'].split("&")
    proxies = {}
    if 'GitProxy' in os.environ:
        log("已设置HTTP代理，将通过代理访问api.github.com")
        proxies['https'] = os.environ['GitProxy']
    session = requests.session()
    qlhost = 'http://127.0.0.1:5700/api'
    token = qltoken()
    headers = {"Content-Type":"application/json","Authorization":"Bearer "+token}
    version = qlversion()
    path = version["path"]
    if path:
        for RepoX in RepoHost:
            Repo = RepoX.split("/")
            GitRepo = Repo[0]+"/"+Repo[1]
            GitBranch = Repo[2]
            tree = github()
            if tree:
                state = check()
                tt = '\n'.join(List)
                if state:
                    send('开卡更新检测', tt)
else:
    log("请查看脚本注释后设置相关变量")
