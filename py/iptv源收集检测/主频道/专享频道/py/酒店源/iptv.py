import time
import datetime
import threading
import os
import re
import concurrent.futures
from queue import Queue
import requests

# ===================== 接口定义 =====================
def modify_urls(url):
    modified_urls = []
    try:
        ip_start_index = url.find("//") + 2
        ip_end_index = url.find(":", ip_start_index)
        base_url = url[:ip_start_index]
        ip_address = url[ip_start_index:ip_end_index]
        port = url[ip_end_index:]
        ip_end = "/iptv/live/1000.json"
        for i in range(1, 256):
            modified_ip = f"{ip_address[:-1]}{i}"
            modified_urls.append(f"{base_url}{modified_ip}{port}{ip_end}")
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

# ===================== 读取 IP 文件夹 =====================
results = []
urls_all = []
folder_path = 'ip'

if not os.path.exists(folder_path):
    folder_path = '.'

for file_name in os.listdir(folder_path):
    if file_name.endswith('.txt'):
        file_path = os.path.join(folder_path, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('http'):
                        urls_all.append(f"http://{ip}")
        except:
            continue

# ===================== 扫描可用服务器 =====================
urls = list(set(urls_all))
valid_urls = []

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

# ===================== 解析直播源 =====================
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

            if urlx.startswith('http'):
                play_url = urlx
            else:
                play_url = f"{base_url}/{urlx.lstrip('/')}"

            name = re.sub(r'高清|超清|标清|频道|测试|HD| |\(|\)|-|K\d|W|w', '', name)
            name = re.sub(r'中央|央视', 'CCTV', name)
            name = re.sub(r'CCTV(\d+)台', r'CCTV\1', name)

            if len(name) < 20:
                results.append(f"{name},{play_url}")
    except:
        continue

# ===================== 输出到仓库根目录 =====================
output_path = os.path.abspath('../../../../../jiudianyuan.txt')
results = sorted(list(set(results)))

with open(output_path, 'w', encoding='utf-8') as f:
    for line in results:
        f.write(line + '\n')

# ===================== 清理临时文件 =====================
temp_files = ["iptv0.txt", "iptv1.txt", "1.txt", "去重1.txt",
              "a1.txt","b1.txt","c1.txt","d1.txt","e1.txt","f1.txt","g1.txt",
              "h1.txt","i1.txt","j1.txt","k1.txt","l1.txt","m1.txt","n1.txt",
              "o1.txt","p1.txt","q1.txt","r1.txt","s1.txt","t1.txt","z1.txt"]
for f in temp_files:
    try:
        os.remove(f)
    except:
        pass

print("✅ 脚本运行完成！")
print(f"✅ 有效直播源：{len(results)} 个")
