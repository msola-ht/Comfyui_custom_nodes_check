import json
import os
import requests

# 读取 notes.json 文件
print("正在读取 notes.json 文件...")
with open('notes.json', 'r', encoding='utf-8') as file:
    notes_data = json.load(file)
print("notes.json 文件读取完毕。")

# 从给定的URL下载并解析 custom-node-list-cleaned.json 文件
url = "https://raw.githubusercontent.com/msola-ht/Comfyui_custom_nodes_check/main/custom-node-list-cleaned/custom-node-list-cleaned.json"
print(f"正在从 {url} 下载 custom-node-list-cleaned.json 文件...")
response = requests.get(url)
custom_nodes_data = response.json()
print("custom-node-list-cleaned.json 文件下载并解析完毕。")

# 从环境变量中读取 GitHub API 令牌 (可选)
github_token = os.getenv("GITHUB_TOKEN")

# 缓存星标数的字典
stars_cache = {}

# 获取 GitHub 仓库的星标数
def get_github_stars(repo_url):
    if repo_url in stars_cache:
        print(f"从缓存中获取星标数: {repo_url}")
        return stars_cache[repo_url]
    
    headers = {'Authorization': f'token {github_token}'} if github_token else {}
    api_url = repo_url.replace("https://github.com", "https://api.github.com/repos")
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        repo_info = response.json()
        stars = repo_info.get('stargazers_count', 0)
        stars_cache[repo_url] = stars
        return stars
    else:
        return 0

# 初始化结果数据
output_data = {}

# 遍历 notes_data 中的每个字段
print("正在处理 notes_data 中的字段...")
for field, translation_field in notes_data.items():
    print(f"正在处理字段: {field}")
    matched_files = []
    stars = 0
    # 查找 custom_nodes_data 中对应的文件链接
    for item in custom_nodes_data:
        if item.get("name") == field.split("\\")[-1]:  # 只匹配字段中的名称部分
            matched_files = item.get("files")
            break

    # 获取第一个匹配文件的星标数
    if matched_files:
        print(f"找到匹配文件: {matched_files[0]}")
        stars = get_github_stars(matched_files[0])
        print(f"获取到的星标数: {stars}")
    else:
        print("未找到匹配文件。")

    # 生成新的 JSON 数据，分割提取的文件链接、原始翻译内容和星标数
    output_data[field] = {
        "translation": translation_field,
        "files": matched_files if matched_files else [],
        "stars": stars
    }

print("字段处理完毕。")

# 打印结果
print("输出结果数据:")
print(json.dumps(output_data, ensure_ascii=False, indent=4))

# 保存结果数据到 custom_nodes_list.json 文件
print("正在将结果数据保存到 custom_nodes_list.json 文件...")
with open('custom_nodes_list.json', 'w', encoding='utf-8') as file:
    json.dump(output_data, file, ensure_ascii=False, indent=4)
print("结果数据保存完毕。")
