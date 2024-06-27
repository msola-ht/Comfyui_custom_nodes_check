import importlib
import subprocess
import sys
import requests

# 需要检测的库
required_packages = ['colorama', 'tabulate', 'requests']

# 检测库是否已安装
def check_packages(packages):
    missing_packages = []
    for package in packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    return missing_packages

# 执行脚本
def run_script(script_name):
    try:
        subprocess.check_call([sys.executable, script_name])
    except subprocess.CalledProcessError as e:
        print(f"执行脚本 {script_name} 失败: {e}")
        sys.exit(1)

# 检测 GitHub 上的最新版本
def check_github_updates(repo_url, current_version):
    try:
        response = requests.get(repo_url)
        response.raise_for_status()
        latest_version = response.json()['tag_name']
        if latest_version != current_version:
            print(f"检测到新版本 {latest_version}, 当前版本为 {current_version}。")
            print("请更新脚本以获取最新功能。")
            return True
    except requests.RequestException as e:
        print(f"检查更新时出错: {e}")
    return False

# 读取当前版本号
def get_current_version(version_file):
    try:
        with open(version_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"版本文件 {version_file} 未找到。")
        sys.exit(1)

# 检测缺失的库
missing_packages = check_packages(required_packages)

if missing_packages:
    print(f"缺失的库: {missing_packages}, 正在执行 package_installer.py")
    run_script('package_installer.py')
    
    # 重新检测库
    missing_packages = check_packages(required_packages)
    if not missing_packages:
        print("所有库都已安装, 正在执行 check_up.py")
        current_version = get_current_version('version.txt')
        if not check_github_updates('https://api.github.com/repos/msola-ht/Comfyui_custom_nodes_check/releases/latest', current_version):
            run_script('check_up.py')
    else:
        print(f"仍然缺失的库: {missing_packages}, 请手动安装这些库。")
else:
    print("所有库都已安装, 正在执行 check_up.py")
    current_version = get_current_version('version.txt')
    if not check_github_updates('https://api.github.com/repos/msola-ht/Comfyui_custom_nodes_check/releases/latest', current_version):
        run_script('check_up.py')
