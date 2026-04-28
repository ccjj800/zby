import eventlet
eventlet.monkey_patch()

import time
import datetime
import threading
import os
import re
import concurrent.futures
from queue import Queue
import requests

# ===================== 修复 1：使用最新有效接口 =====================
def modify_urls(url):
    modified_urls = []
    try:
        ip_start_index = url.find("//") + 2
        ip_end_index = url.find(":", ip_start_index)
        base_url = url[:ip_start_index]
        ip_address = url[ip_start_index:ip_end_index]
        port = url[ip_end_index:]
        # 修复接口，去掉失效参数
        ip_end = "/iptv/live/1000.json"
        for i in range(1, 256):
            modified_ip = f"{ip_address[:-1]}{i}"
            modified_url = f"{base_url}{modified_ip}{port}{ip_end}"
            modified_urls.append(modified_url)
    except:
        pass
    return modified_urls

def is_url_accessible(url):
    try:
        response = requests.get(url, timeout=1.5)
        if response.status_code == 200 and len(response.content) > 500:
            return url
    except:
        pass
    return None

results = []
urls_all = []

# 读取你的酒店IP文件
try:
    with open('../../../../../jiudianyuan.txt', 'w', encoding='utf-8') as f:
        lines = file.readlines()
        for line in lines:
            url = line.strip()
            if url and not url.startswith('http'):
                urls_all.append(f"http://{url}")
except:
    pass

urls = list(set(urls_all))
valid_urls = []

# 多线程检测可用IP
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = []
    for url in urls:
        try:
            for murl in modify_urls(url):
                futures.append(executor.submit(is_url_accessible, murl))
        except:
            pass

    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        if res:
            valid_urls.append(res)

# ===================== 修复 2：正确拼接直播地址（之前全错） =====================
for url in valid_urls:
    try:
        base_ip = url.split('//')[1].split('/')[0]
        base_url = f'http://{base_ip}'
        response = requests.get(url, timeout=2)
        json_data = response.json()

        for item in json_data.get('data', []):
            if not isinstance(item, dict):
                continue
            name = item.get('name', '').strip()
            urlx = item.get('url', '') or item.get('uri', '')

            if not name or not urlx or ',' in urlx:
                continue

            # 正确拼接播放地址
            if urlx.startswith('http'):
                play_url = urlx
            else:
                play_url = f"{base_url}/{urlx.lstrip('/')}"

            # 频道名称清洗
            name = re.sub(r'高清|超清|标清|频道|测试|HD| |\(|\)|-|K1|K2|W|w', '', name)
            name = re.sub(r'中央|央视', 'CCTV', name)
            name = re.sub(r'CCTV(\d+)台', r'CCTV\1', name)

            # 只保留有效频道
            if len(name) < 20 and (',' not in play_url):
                results.append(f"{name},{play_url}")
    except:
        continue

# 去重
results = sorted(list(set(results)))

# ===================== 修复 3：直接输出到 根目录 / jiudianyuan.txt =====================
with open('../../../../../jiudianyuan.txt', 'w', encoding='utf-8') as f:
    for line in results:
        f.write(line + '\n')

# 清理临时文件（不影响结果）
temp_files = ["iptv0.txt", "iptv1.txt", "1.txt", "去重1.txt",
              "a1.txt","b1.txt","c1.txt","d1.txt","e1.txt","f1.txt","g1.txt",
              "h1.txt","i1.txt","j1.txt","k1.txt","l1.txt","m1.txt","n1.txt",
              "o1.txt","p1.txt","q1.txt","r1.txt","s1.txt","t1.txt","z1.txt"]
for f in temp_files:
    try:
        os.remove(f)
    except:
        pass

print(f"✅ 脚本运行完成！有效直播源：{len(results)} 个")
print(f"✅ 文件已输出到：仓库根目录 / jiudianyuan.txt")
