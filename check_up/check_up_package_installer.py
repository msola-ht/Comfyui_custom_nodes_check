import subprocess
import sys
import importlib.metadata

required_packages = {'colorama', 'tabulate', 'requests'}

def install_packages(packages):
    """安装所需的包"""
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError as e:
            print(f"安装 {package} 失败: {e}")
            sys.exit(1)

def main():
    installed_packages = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
    missing_packages = required_packages - installed_packages

    if missing_packages:
        print(f"缺失的包: {missing_packages}, 正在安装...")
        install_packages(missing_packages)
    else:
        print("所有必需的包都已安装。")

if __name__ == "__main__":
    main()
