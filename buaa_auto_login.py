#!/usr/bin/env python3
'''
@Description: login gw.buaa.edu.cn in Command line mode
    based on https://github.com/luoboganer 2019-09-01
    based on https://coding.net/u/huxiaofan1223/p/jxnu_srun/git
    based on https://blog.csdn.net/qq_41797946/article/details/89417722

'''


import requests
import socket
import time
import math
import hmac
import hashlib
import getpass
import json
import urllib3
import os
import random

#修改网关信息、clash信息等

#你的北航统一认证网关密码
username = 'by2106106'
password = 'beihang654321'

#是否开启断网重连时自动关闭clash的全局代理功能。如【电脑中没有安装clash，或clash没有运行，务必将该项设置为False】。该项默认为False，如有需要请手动更改为True
if_close_clash_proxy=True
#你的clash软件的API port和secret
clash_secret='3db5c5ca-22cf-47dc-ae80-3445ffb3bdca'
clash_port='1317'
#该功能仅在windows 11下进行测试，目测win10可用。
#默认情况下secret信息与port信息在 C:\Users\[YOUR_USERNAME]\.config\clash\config.yaml中，可自行复制，当然也可自行修改。
#使用该功能请务必将clash的Random Controller Port关闭，否则会出现端口冲突，导致无法正常使用。该选项位于clash的设置->general->Random Controller Port



#在我的测试环境里同一个网站ping多了会请求超时，但网站还是能访问，因此这里采用随机ping一个网站的方式来试图缓解这种情况。但其实我并没有搞清楚是否是网站本身对ping的请求做了限制，欢迎对该部分的处理提出意见。
ping_list=['www.baidu.com','www.163.com','www.taobao.com','www.jd.com','weibo.com']
ping_index=0
#当然，最优雅的方式还是直接从网关里面获取是否成功连接的信息。不过网关获取信息也并非一劳永逸，因为开启全局代理时，无法从网关直接获取信息。

#如果采用直接从网关里获取是否成功连接的信息，则ping_list与下面两个变量都可以省掉。目前的处理方式确实不够优雅。主要是中秋将近，不想写了，之后有空再改。
#time interval to check the network connection
time_interval=30

#login when the number of failed attempts more than reconnect_threshold. We use the length of ping_list as the default value of the threshold.
reconnect_threshold=ping_list.__len__()





urllib3.disable_warnings()

def check_internet():
    ping_site=ping_list[ping_index]
    ping_index=(ping_index+1)%len(ping_list)
    # 尝试ping一个常用的网站，如baidu.com
    ping_cmd = "ping %s" % ping_site
    result = os.system(ping_cmd)
    print(result)
    # 如果返回值为0，说明ping成功，返回True
    if result == 0:
        return True
    # 如果返回值不为0，说明ping失败，返回False
    else:
        return False


def get_jsonp(url, params):
    """
    Send jsonp request and decode response

    About jsonp: https://stackoverflow.com/questions/2067472/what-is-jsonp-and-why-was-it-created
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/76.0.3809.100 Chrome/76.0.3809.100 Safari/537.36",
    }
    callback_name = "jQuery112406951885120277062_" + str(int(time.time() * 1000))
    params['callback'] = callback_name
    resp = requests.get(url, params=params, headers=headers, verify=False)
    return json.loads(resp.text[len(callback_name) + 1:-1])


def get_IP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]


def get_ip_token(username):
    get_challenge_url = "https://gw.buaa.edu.cn/cgi-bin/get_challenge"
    get_challenge_params = {
        "username": username,
        "ip": '0.0.0.0',
        "_": int(time.time() * 1000)
    }
    res = get_jsonp(get_challenge_url, get_challenge_params)
    return res["client_ip"], res["challenge"],


def get_info(username, password, ip):
    params = {
        'username': username,
        'password': password,
        'ip': ip,
        'acid': '1',
        "enc_ver": 'srun_bx1'
    }
    info = json.dumps(params)
    return info


def force(msg):
    ret = []
    for w in msg:
        ret.append(ord(w))
    return bytes(ret)


def ordat(msg, idx):
    if len(msg) > idx:
        return ord(msg[idx])
    return 0


def sencode(msg, key):
    l = len(msg)
    pwd = []
    for i in range(0, l, 4):
        pwd.append(
            ordat(msg, i) | ordat(msg, i + 1) << 8 | ordat(msg, i + 2) << 16
            | ordat(msg, i + 3) << 24)
    if key:
        pwd.append(l)
    return pwd


def lencode(msg, key):
    l = len(msg)
    ll = (l - 1) << 2
    if key:
        m = msg[l - 1]
        if m < ll - 3 or m > ll:
            return
        ll = m
    for i in range(0, l):
        msg[i] = chr(msg[i] & 0xff) + chr(msg[i] >> 8 & 0xff) + chr(
            msg[i] >> 16 & 0xff) + chr(msg[i] >> 24 & 0xff)
    if key:
        return "".join(msg)[0:ll]
    return "".join(msg)


def get_xencode(msg, key):
    if msg == "":
        return ""
    pwd = sencode(msg, True)
    pwdk = sencode(key, False)
    if len(pwdk) < 4:
        pwdk = pwdk + [0] * (4 - len(pwdk))
    n = len(pwd) - 1
    z = pwd[n]
    y = pwd[0]
    c = 0x86014019 | 0x183639A0
    m = 0
    e = 0
    p = 0
    q = math.floor(6 + 52 / (n + 1))
    d = 0
    while 0 < q:
        d = d + c & (0x8CE0D9BF | 0x731F2640)
        e = d >> 2 & 3
        p = 0
        while p < n:
            y = pwd[p + 1]
            m = z >> 5 ^ y << 2
            m = m + ((y >> 3 ^ z << 4) ^ (d ^ y))
            m = m + (pwdk[(p & 3) ^ e] ^ z)
            pwd[p] = pwd[p] + m & (0xEFB8D130 | 0x10472ECF)
            z = pwd[p]
            p = p + 1
        y = pwd[0]
        m = z >> 5 ^ y << 2
        m = m + ((y >> 3 ^ z << 4) ^ (d ^ y))
        m = m + (pwdk[(p & 3) ^ e] ^ z)
        pwd[n] = pwd[n] + m & (0xBB390742 | 0x44C6F8BD)
        z = pwd[n]
        q = q - 1
    return lencode(pwd, False)


_PADCHAR = "="
_ALPHA = "LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA"


def _getbyte(s, i):
    x = ord(s[i])
    if (x > 255):
        print("INVALID_CHARACTER_ERR: DOM Exception 5")
        exit(0)
    return x


def get_base64(s):
    i = 0
    b10 = 0
    x = []
    imax = len(s) - len(s) % 3
    if len(s) == 0:
        return s
    for i in range(0, imax, 3):
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8) | _getbyte(s, i + 2)
        x.append(_ALPHA[(b10 >> 18)])
        x.append(_ALPHA[((b10 >> 12) & 63)])
        x.append(_ALPHA[((b10 >> 6) & 63)])
        x.append(_ALPHA[(b10 & 63)])
    i = imax
    if len(s) - imax == 1:
        b10 = _getbyte(s, i) << 16
        x.append(_ALPHA[(b10 >> 18)] +
                 _ALPHA[((b10 >> 12) & 63)] + _PADCHAR + _PADCHAR)
    elif len(s) - imax == 2:
        b10 = (_getbyte(s, i) << 16) | (_getbyte(s, i + 1) << 8)
        x.append(_ALPHA[(b10 >> 18)] + _ALPHA[((b10 >> 12) & 63)] + _ALPHA[((b10 >> 6) & 63)] + _PADCHAR)
    return "".join(x)


def get_md5(password, token):
    return hmac.new(token.encode(), password.encode(), hashlib.md5).hexdigest()


def get_sha1(value):
    return hashlib.sha1(value.encode()).hexdigest()


def login(username, password):
    srun_portal_url = "https://gw.buaa.edu.cn/cgi-bin/srun_portal"
    ip, token = get_ip_token(username)
    info = get_info(username, password, ip)

    # import IPython
    # IPython.embed()
    data = {
        "action": "login",
        "username": username,
        "password": "{MD5}" + get_md5(password, token),
        "ac_id": 1,
        "ip": ip,
        "info": "{SRBX1}" + get_base64(get_xencode(info, token)),
        "n": "200",
        "type": "1",
        "os": "Linux.Hercules",
        "name": "Linux",
        "double_stack": '',
        "_": int(time.time() * 1000)
    }
    chkstr = token + username
    chkstr += token + get_md5(password, token)
    chkstr += token + '1'
    chkstr += token + ip
    chkstr += token + '200'
    chkstr += token + '1'
    chkstr += token + "{SRBX1}" + get_base64(get_xencode(info, token))
    data['chksum'] = get_sha1(chkstr)

    return get_jsonp(srun_portal_url, data)


if __name__ == "__main__":
    fail_count=0
    print('gw.buaa.edu.cn portal login...')
    #create a loop to check if the network is connected
    while True:
        try:
            #check if the network is connected
            #check the network connection
            if check_internet():
                print('Network is connected')
                #sleep 5 seconds
                time.sleep(time_interval)
            else:
                #raise an exception
                fail_count=fail_count+1
                if fail_count>reconnect_threshold:
                    fail_count=0
                    raise Exception('Network is disconnected')
                else:
                    continue
            
        except:
                try:
                    #set system proxy to false
                    #secret and port could be found/set in C:\Users\[YOUR_USERNAME]\.config\clash\config.yaml, 
                    #NOTICE:Random Controller Port should be closed!! Find in settings->general->Random Controller Port. 
                    #correct command to check proxies:curl -H "Authorization: Bearer [secret]"  http://127.0.0.1:[port]/proxies  
                    #correct command to set proxy:curl -X PUT -H "Authorization: Bearer [secret]}" --data "{\"name\":\"DIRECT\"}" http://127.0.0.1:[port]/proxies/GLOBAL
                    if if_close_clash_proxy:
                        os.system('curl -X PUT -H \"Authorization: Bearer '+clash_secret+'\" --data \"{\\\"name\\\":\\\"DIRECT\\\"}\" http://127.0.0.1:'+clash_port+'/proxies/GLOBAL')
                    login_info = login(username, password)
                    print(json.dumps(login_info, indent=4, ensure_ascii=False))
                    time.sleep(time_interval)
                except:
                    #print exception
                    print('login failed')
                    time.sleep(time_interval)
                    continue
                
                



