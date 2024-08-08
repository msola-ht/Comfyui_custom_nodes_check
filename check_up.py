import sys
import subprocess
import importlib

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 检查并安装所需的库
required_packages = ['requests', 'pytz', 'prettytable', 'colorama']
all_installed = True

for package in required_packages:
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"{package} 未安装，正在安装...")
        install(package)
        print(f"{package} 安装完成")
        all_installed = False

if all_installed:
    print("所有必需的库已经安装。")

# 现在导入所需的库
import os
import requests
import json
from datetime import datetime
import pytz
from prettytable import PrettyTable
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)

# 下载备注信息并解析
def get_notes(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# 检查 GIT 仓库，最多重试 3 次
def is_git_repo(directory, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'], cwd=directory).strip().decode('utf-8')
            return True
        except subprocess.CalledProcessError:
            attempt += 1
    return False

# 获取 GIT 仓库的最后更新时间
def get_last_update_time(directory, remote=False):
    try:
        if remote:
            command = ['git', 'log', '-1', '--format=%cd', 'origin/HEAD']
        else:
            command = ['git', 'log', '-1', '--format=%cd']
        
        last_update = subprocess.check_output(command, cwd=directory).strip().decode('utf-8')
        last_update_datetime = datetime.strptime(last_update, "%a %b %d %H:%M:%S %Y %z")
        # 转换为 +8 时区
        last_update_datetime = last_update_datetime.astimezone(pytz.timezone('Asia/Shanghai'))
        return last_update_datetime.strftime("%Y-%m-%d")
    except subprocess.CalledProcessError:
        return "获取失败"

# 检查本地是否已经推送以及是否最新
def check_git_status(directory):
    try:
        # 获取状态
        status = subprocess.check_output(['git', 'status', '-sb'], cwd=directory).strip().decode('utf-8')
        
        if "ahead" in status:
            return Fore.YELLOW + "未推送" + Style.RESET_ALL, False
        elif "behind" in status:
            return Fore.RED + "未更新" + Style.RESET_ALL, False
        else:
            return "", True
    except subprocess.CalledProcessError:
        return Fore.RED + "检查失败" + Style.RESET_ALL, False

# 获取远程仓库 URL
def get_remote_url(directory):
    try:
        remote_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], cwd=directory).strip().decode('utf-8')
        return remote_url
    except subprocess.CalledProcessError:
        return "获取失败"

def main():
    # GIT 备注信息 URL
    notes_url = "https://raw.githubusercontent.com/msola-ht/Comfyui_custom_nodes_check/main/custom_nodes_list.json"
    notes = get_notes(notes_url)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    custom_nodes_dir = os.path.join(base_dir, 'custom_nodes')

    if not os.path.isdir(custom_nodes_dir):
        print(Fore.RED + f"{custom_nodes_dir} 不存在或不是一个目录" + Style.RESET_ALL)
        return

    table = PrettyTable()
    table.field_names = ["目录路径", "备注", "GitHub链接", "Stars"]
    table.align["目录路径"] = "l"
    table.align["备注"] = "l"
    table.align["GitHub链接"] = "l"
    table.align["Stars"] = "r"

    total = 0
    success = 0
    failed_paths = []
    table_data = []

    for item in os.listdir(custom_nodes_dir):
        item_path = os.path.join(custom_nodes_dir, item)
        if os.path.isdir(item_path):
            original_item = item
            if item.endswith('.disabled'):
                item = item.replace('.disabled', '')
                print(Fore.YELLOW + f"发现.disabled后缀，处理后目录名称: {item}" + Style.RESET_ALL)  # 调试输出

            total += 1
            if is_git_repo(item_path):
                relative_path = f"custom_nodes\\{item}"  # 使用双反斜杠
                note_info = notes.get(relative_path, {"translation": "无备注信息", "files": [], "stars": 0})
                translation = note_info.get("translation", "无备注信息")
                files = note_info.get("files", [])
                stars = note_info.get("stars", 0)
                github_link = files[0] if files else "无链接"

                table_data.append([relative_path.replace("custom_nodes\\", "").replace("\\", "/"), translation, github_link, stars])
                success += 1

                print(Fore.CYAN + f"检查目录: {item_path}" + Style.RESET_ALL)
                print(Fore.GREEN + f"  成功：{relative_path}({translation})" + Style.RESET_ALL)
                print(Fore.BLUE + f"  GitHub链接：{github_link}" + Style.RESET_ALL)  # 在终端显示链接
            else:
                print(Fore.CYAN + f"检查目录: {item_path}" + Style.RESET_ALL)
                print(Fore.RED + f"  失败：{item_path} 不是一个GIT仓库" + Style.RESET_ALL)
                failed_paths.append(item_path.replace("custom_nodes\\", "").replace("\\", "/"))
    
    # 按 Stars 排序
    table_data.sort(key=lambda x: x[3] if isinstance(x[3], int) else 0, reverse=True)

    for row in table_data:
        table.add_row(row)

    failed = total - success
    print("\n" + Style.BRIGHT + "检查结果汇总：" + Style.RESET_ALL)
    print(table)

    print(f"\n总共检查了 {total} 个目录，成功 {success} 个，失败 {failed} 个。")
    if failed_paths:
        print("失败的目录路径如下：")
        for path in failed_paths:
            print(Fore.RED + path + Style.RESET_ALL)

    # 构建Markdown格式的表格（不显示 GitHub链接）
    markdown_table = ["| 目录路径 | 备注 | Stars |",
                      "| --- | --- | --- |"]
    
    for row in table_data:
        markdown_table.append("| " + " | ".join(map(str, row[:2] + [row[3]])) + " |")  # 只保留目录路径、备注和Stars
    
    markdown_content = "\n".join(markdown_table)
    
    # 添加数量统计信息
    markdown_content += f"\n\n总共检查了 {total} 个目录，成功 {success} 个，失败 {failed} 个。"
    if failed_paths:
        markdown_content += "\n\n失败的目录路径如下："
        for path in failed_paths:
            markdown_content += f"\n- {path}"

    with open('check_up.md', 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_content)
    
    print(Fore.GREEN + "Markdown格式的表格已经保存到 check_up.md" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
