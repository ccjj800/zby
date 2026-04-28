# ！！！已经彻底删除 eventlet，不会再报任何模块错误！！！

import time
import os
import re
import concurrent.futures
import requests

# ========================= 接口生成 =========================
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
        res = requests.get(url, timeout=1.3)
        if res.status_code == 200 and len(res.content) > 500:
            return url
    except:
        return None

# ========================= 读取 IP 文件夹 =========================
results = []
urls_all = []
folder_path = 'ip'

if not os.path.exists(folder_path):
    folder_path = '.'

for file_name in os.listdir(folder_path):
    if file_name.endswith('.txt'):
        fp = os.path.join(folder_path, file_name)
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith('http'):
                        urls_all.append(f"http://{ip}")
        except:
            continue

# ========================= 扫描可用服务器 =========================
valid_urls = []
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(is_url_accessible, mu) for url in set(urls_all) for mu in modify_urls(url)]
    for fut in concurrent.futures.as_completed(futures):
        res = fut.result()
        if res:
            valid_urls.append(res)

# ========================= 解析直播源 =========================
for url in valid_urls:
    try:
        base_ip = url.split('//')[1].split('/')[0]
        base = f"http://{base_ip}"
        data = requests.get(url, timeout=2).json()

        for item in data.get('data', []):
            if not isinstance(item, dict):
                continue
            name = str(item.get('name', '')).strip()
            u = item.get('url', '') or item.get('uri', '')

            if not name or not u or ',' in u:
                continue

            if u.startswith('http'):
                play_url = u
            else:
                play_url = f"{base}/{u.lstrip('/')}"

            name = re.sub(r'高清|超清|标清|频道|测试|HD|\s|-|\(|\)|K\d|W', '', name)
            name = re.sub(r'中央|央视', 'CCTV', name)
            name = re.sub(r'CCTV(\d+)台', r'\1', name)

            if len(name) < 22:
                results.append(f"{name},{play_url}")
    except:
        continue

# ========================= 输出到根目录 =========================
final = sorted(list(set(results)))

# 重要：
# 第一个脚本 iptv.py 使用 'w'
# 第二个脚本 iptv2.py 使用 'a'
# 第三个脚本 gxtv.py 使用 'a'

with open('/home/runner/work/zby/zby/jiudianyuan.txt', 'a', encoding='utf-8') as f:
    for line in final:
        f.write(line + '\n')

# ========================= 清理 =========================
print("="*50)
print(f"✅ 脚本运行完成！")
print(f"✅ 有效直播源：{len(final)} 个")
print("="*50)
