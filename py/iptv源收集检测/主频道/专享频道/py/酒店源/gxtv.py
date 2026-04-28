import eventlet
eventlet.monkey_patch()

import time
import datetime
import os
import re
import concurrent.futures
from queue import Queue
import requests

# ===================== 修复接口：光迅专用接口 =====================
def modify_urls(url):
    modified_urls = []
    try:
        ip_start_index = url.find("//") + 2
        ip_end_index = url.find(":", ip_start_index)
        base_url = url[:ip_start_index]
        ip_address = url[ip_start_index:ip_end_index]
        port = url[ip_end_index:]
        ip_end = "/ZHGXTV/Public/json/live_interface.txt"
        for i in range(1, 256):
            modified_ip = f"{ip_address[:-1]}{i}"
            modified_urls.append(f"{base_url}{modified_ip}{port}{ip_end}")
    except:
        pass
    return modified_urls

def is_url_accessible(url):
    try:
        res = requests.get(url, timeout=1.5)
        if res.status_code == 200 and len(res.content) > 100:
            return url
    except:
        return None

# ===================== 读取光迅IP =====================
results = []
urls_all = []

try:
    with open('py/iptv源收集检测/主频道/专享频道/py/酒店源/光迅.ip', 'r', encoding='utf-8') as file:
        for line in file:
            ip = line.strip()
            if ip:
                urls_all.append(f"http://{ip}")
except:
    pass

# 处理IP段
urls = set(urls_all)
x_urls = []
for url in urls:
    try:
        url = url.strip()
        ip_start_index = url.find("//") + 2
        ip_dot_start = url.find(".") + 1
        ip_dot_second = url.find(".", ip_dot_start) + 1
        ip_dot_three = url.find(".", ip_dot_second) + 1
        base_url = url[:ip_start_index]
        ip_address = url[ip_start_index:ip_dot_three]
        port = url[url.find(":", ip_start_index):]
        modified_ip = f"{ip_address}1"
        x_urls.append(f"{base_url}{modified_ip}{port}")
    except:
        continue

# 多线程检测可用服务器
valid_urls = []
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(is_url_accessible, mu) for url in set(x_urls) for mu in modify_urls(url)]
    for fut in concurrent.futures.as_completed(futures):
        res = fut.result()
        if res:
            valid_urls.append(res)

valid_urls = sorted(set(valid_urls))

# ===================== 核心修复：正确解析光迅 txt 格式 =====================
for url in valid_urls:
    try:
        host = url.split("//")[1].split("/")[0]
        resp = requests.get(url, timeout=3)
        content = resp.content.decode('utf-8', errors='ignore')
        
        for line in content.splitlines():
            line = line.strip()
            if not line or 'udp' in line or 'rtp' in line:
                continue
            
            if ',' in line:
                name, src = line.split(',', 1)
                name = name.strip()
                src = src.strip()
                
                # 【修复】正确拼接直播地址（之前完全错误）
                if src.startswith('http'):
                    play_url = src
                else:
                    play_url = f"http://{host}/{src.lstrip('/')}"
                
                # 名称清洗
                name = re.sub(r'高清|超清|标清|频道|测试|HD|\s|-|\(|\)|K\d|W', '', name)
                name = re.sub(r'中央|央视', 'CCTV', name)
                name = re.sub(r'CCTV(\d+)台', r'CCTV\1', name)
                
                if name and play_url and len(name) < 25:
                    results.append(f"{name},{play_url}")
    except:
        continue

# 去重
results = sorted(set(results))

# ===================== 直接输出到 仓库根目录：jiudianyuan.txt =====================
with open('/github/workspace/jiudianyuan.txt', 'w', encoding='utf-8') as f:
    for line in results:
        f.write(line + '\n')

# ===================== 清理所有临时文件 =====================
temp_files = ["gxtv0.txt","gxtv1.txt","3.txt","去重3.txt","a3.txt","b3.txt","z3.txt"]
for fn in temp_files:
    try:
        os.remove(fn)
    except:
        pass

print("="*50)
print(f"✅ 光迅酒店源脚本执行完成！")
print(f"✅ 有效源数量：{len(results)} 个")
print(f"✅ 已输出到：仓库根目录 / jiudianyuan.txt")
print("="*50)
