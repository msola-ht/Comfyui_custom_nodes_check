import json
import re
import requests

# 远程 JSON 文件的 URL
url = 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/custom-node-list.json'

# 使用 requests 获取远程文件内容
response = requests.get(url)
response.raise_for_status()  # 确保请求成功

# 解析 JSON 数据
data = response.json()

# 整理数据
cleaned_data = []
for item in data['custom_nodes']:
    # 从 URL 中提取名称
    url = item['reference']
    match = re.search(r'github\.com/[^/]+/([^/]+)', url)
    if match:
        name = match.group(1)
    else:
        name = "Unknown"
    
    # 如果 name 为 Unknown，则跳过该项
    if name == "Unknown":
        continue
    
    # 使用描述作为备注
    description = item['description']
    
    # 保留原始的 files 字段内容
    files = item['files']
    
    # 只保留 name、note 和 files 字段
    cleaned_item = {
        "name": name,
        "note": description,
        "files": files
    }
    cleaned_data.append(cleaned_item)

# 保存整理后的数据到新的 JSON 文件
with open('custom-node-list-cleaned.json', 'w', encoding='utf-8') as file:
    json.dump(cleaned_data, file, indent=4)

print("数据整理完成并保存到 custom-node-list-cleaned.json")
