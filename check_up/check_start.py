import importlib
import subprocess
import sys

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

# 检测缺失的库
missing_packages = check_packages(required_packages)

if missing_packages:
    print(f"缺失的库: {missing_packages}, 正在执行 package_installer.py")
    run_script('package_installer.py')
    
    # 重新检测库
    missing_packages = check_packages(required_packages)
    if not missing_packages:
        print("所有库都已安装, 正在执行 check_up.py")
        run_script('check_up.py')
    else:
        print(f"仍然缺失的库: {missing_packages}, 请手动安装这些库。")
else:
    print("所有库都已安装, 正在执行 check_up.py")
    run_script('check_up.py')