import subprocess
import sys
import os
import logging
from colorama import Fore, Style
from colorama import init as colorama_init
from datetime import datetime, timedelta, timezone
from tabulate import tabulate
import requests
import time
import json

# 初始化colorama
colorama_init()

# 设置日志记录
logging.basicConfig(filename='check_up.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# 缓存文件路径
CACHE_FILE = 'stars_cache.json'

def load_cache():
    """加载缓存"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """保存缓存"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

# 加载缓存
stars_cache = load_cache()

class GitRepository:
    def __init__(self, path, note=None):
        self.path = path
        self.note = note
        self.checked_successfully = False
        self.remote_last_update_date = None
        self.local_last_update_date = None
        self.days_since_remote_update = None
        self.days_since_local_update = None
        self.unpushed_changes = False
        self.url = self.get_remote_url()
        self.stars = None

    def is_git_repository(self):
        """检查路径是否为GIT仓库"""
        return self.run_git_command(['rev-parse'])

    def has_unpushed_changes(self):
        """检查仓库是否有未推送的更改"""
        if not self.run_git_command(['fetch', '--quiet']):
            return False
        local_head = self.run_git_command(['rev-parse', 'HEAD'], capture_output=True)
        remote_head = self.run_git_command(['rev-parse', '@{u}'], capture_output=True)
        return local_head != remote_head

    def get_last_update_time(self):
        """获取仓库最后更新的时间"""
        output = self.run_git_command(['log', '-1', '--format=%cd'], capture_output=True)
        if output:
            return datetime.strptime(output.strip(), '%a %b %d %H:%M:%S %Y %z')
        return None

    def get_remote_last_update_time(self):
        """获取远程仓库最后更新的时间"""
        output = self.run_git_command(['log', '-1', '--remotes', '--format=%cd'], capture_output=True)
        if output:
            return datetime.strptime(output.strip(), '%a %b %d %H:%M:%S %Y %z')
        return None

    def get_remote_url(self):
        """从.git/config文件中读取远程URL"""
        config_path = os.path.join(self.path, '.git', 'config')
        if os.path.exists(config_path):
            with open(config_path, 'r') as config_file:
                for line in config_file:
                    if line.strip().startswith('url ='):
                        url = line.split('=')[1].strip()
                        if url.endswith('.git'):
                            url = url[:-4]  # 删除末尾的.git
                        return url
        return None

    def get_stars(self, retries=3):
        """获取远程仓库的星标数量，增加重试机制和缓存"""
        if self.url and 'github.com' in self.url:
            repo_path = self.url.split('github.com/')[1]
            if repo_path in stars_cache:
                return stars_cache[repo_path]
            api_url = f'https://api.github.com/repos/{repo_path}'
            headers = {}
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            for attempt in range(retries):
                try:
                    response = requests.get(api_url, headers=headers, timeout=10)  # 设置超时时间为10秒
                    if response.status_code == 200:
                        repo_info = response.json()
                        stars = repo_info.get('stargazers_count', 0)
                        stars_cache[repo_path] = stars
                        save_cache(stars_cache)
                        return stars
                    else:
                        logging.error(f"请求失败: {api_url}, 状态码: {response.status_code}")
                        print(f"{Fore.RED}请求失败: {api_url}, 状态码: {response.status_code}{Style.RESET_ALL}")
                        break  # 如果状态码不是200，直接退出重试
                except requests.Timeout:
                    logging.error(f"请求超时: {api_url}")
                    print(f"{Fore.YELLOW}获取星标数量失败，正在重试 {attempt + 1}/{retries}...{Style.RESET_ALL}")
                time.sleep(2)  # 等待2秒后重试
        return None

    def check_updates(self):
        """检查指定路径的GIT仓库更新"""
        if self.is_git_repository():
            print(f"{Fore.CYAN}正在检查 {self.path} ({self.note})...{Style.RESET_ALL}")
            logging.info(f"正在检查 {self.path} ({self.note})...")
            
            self.unpushed_changes = self.has_unpushed_changes()
            if self.unpushed_changes:
                print(f"{Fore.YELLOW}{self.path} ({self.note}) 有未推送的更改。{Style.RESET_ALL}")
                logging.info(f"{self.path} ({self.note}) 有未推送的更改。")
            
            local_last_update_time = self.get_last_update_time()
            remote_last_update_time = self.get_remote_last_update_time()
            if local_last_update_time and remote_last_update_time:
                local_last_update_time_utc8 = local_last_update_time.astimezone(timezone(timedelta(hours=8)))
                remote_last_update_time_utc8 = remote_last_update_time.astimezone(timezone(timedelta(hours=8)))
                self.remote_last_update_date = remote_last_update_time_utc8.strftime('%Y-%m-%d')
                self.local_last_update_date = local_last_update_time_utc8.strftime('%Y-%m-%d')
                self.days_since_remote_update = (datetime.now(timezone(timedelta(hours=8))) - remote_last_update_time_utc8).days
                self.days_since_local_update = (datetime.now(timezone(timedelta(hours=8))) - local_last_update_time_utc8).days
                print(f"{Fore.GREEN}{self.path} ({self.note}) {Fore.BLUE}远程{Style.RESET_ALL}最后更新时间: {self.remote_last_update_date}, 距今 {Fore.RED}{self.days_since_remote_update}{Fore.GREEN} 天。{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{self.path} ({self.note}) {Fore.YELLOW}本地{Style.RESET_ALL}最后更新时间: {self.local_last_update_date}, 距今 {Fore.RED}{self.days_since_local_update}{Fore.GREEN} 天。{Style.RESET_ALL}")
                logging.info(f"{self.path} ({self.note}) 远程最后更新时间: {self.remote_last_update_date}, 距今 {self.days_since_remote_update} 天。")
                logging.info(f"{self.path} ({self.note}) 本地最后更新时间: {self.local_last_update_date}, 距今 {self.days_since_local_update} 天。")
                self.checked_successfully = True
                if os.getenv('GITHUB_TOKEN'):
                    self.stars = self.get_stars()
                    if self.stars is not None:
                        print(f"{Fore.GREEN}{self.path} ({self.note}) 星标数量: {Fore.RED}{self.stars}{Style.RESET_ALL}")
                        logging.info(f"{self.path} ({self.note}) 星标数量: {self.stars}")

    def run_git_command(self, command, capture_output=False):
        """运行Git命令"""
        try:
            result = subprocess.check_output(['git', '-C', self.path] + command, stderr=subprocess.STDOUT, timeout=10)  # 设置超时时间为10秒
            return result.decode('utf-8') if capture_output else True
        except subprocess.TimeoutExpired:
            print(f"{Fore.RED}Git命令超时: {' '.join(command)}{Style.RESET_ALL}")
            logging.error(f"Git命令超时: {' '.join(command)}")
            return None if capture_output else False
        except subprocess.CalledProcessError as e:
            logging.error(f"Git命令失败: {e}")
            return None if capture_output else False

def check_git_updates(root_path, notes):
    """检查根路径下的所有GIT仓库"""
    repositories = find_repositories(root_path, notes)
    
    total_repos = len(repositories)
    successful_checks = 0
    failed_checks = 0
    results_info = []
    results_status = []

    for index, repo in enumerate(repositories):
        print(f"{Fore.BLUE}检查进度: {index + 1}/{total_repos}{Style.RESET_ALL}")
        repo.check_updates()
        if repo.checked_successfully:
            successful_checks += 1
            stars = str(repo.stars) if repo.stars is not None else "N/A"
            results_info.append([repo.path, stars, repo.note, repo.url])
            days_since_remote_update = repo.days_since_remote_update if repo.days_since_remote_update != 0 else ""
            days_since_local_update = repo.days_since_local_update if repo.days_since_local_update != 0 else ""
            results_status.append([repo.path, repo.remote_last_update_date, days_since_remote_update, repo.local_last_update_date, days_since_local_update, "是" if repo.unpushed_changes else "否"])
        else:
            failed_checks += 1
            results_info.append([repo.path, "获取失败", repo.note, repo.url])
            results_status.append([repo.path, "检查失败", "", "", "", ""])

    print(f"{Fore.MAGENTA}本次检查仓库总数: {total_repos}, 成功: {successful_checks}, 失败: {failed_checks}{Style.RESET_ALL}")
    logging.info(f"本次检查仓库总数: {total_repos}, 成功: {successful_checks}, 失败: {failed_checks}")

    # 按星标数量排序
    results_info.sort(key=lambda x: int(x[1]) if str(x[1]).isdigit() else -1, reverse=True)

    # 将星标数量重新格式化为红色
    for item in results_info:
        if str(item[1]).isdigit():
            item[1] = Fore.RED + str(item[1]) + Style.RESET_ALL

    # 将未推送更改重新格式化为红色
    for item in results_status:
        if item[5] == "是":
            item[5] = Fore.RED + item[5] + Style.RESET_ALL

    headers_info = ["仓库路径", "星标", "备注", "URL"]
    headers_status = ["仓库路径", "远程最后更新日期", "远程距今天数", "本地最后更新日期", "本地距今天数", "未推送更改"]

    print(tabulate(results_info, headers=headers_info, tablefmt="grid"))
    print(tabulate(results_status, headers=headers_status, tablefmt="grid"))

    # 添加文字说明
    additional_info = (
        "\n###\n"
        "1、插件备注放在GitHub，人工进行维护，如果有没显示的备注可以到项目仓库留言，我看到以后会进行更新。\n"
        "2、脚本星标显示功能需要使用到GitHub的个人令牌，如果需要使用到这个功能的请到仓库看指南。\n"
        "（因为使用API获取GitHub星标，公共API限制60次/小时）\n"
        "#\##n"
        "1、如有关于ComfyUI环境冲突、插件冲突咨询的，可以联系我。\n"
        "2、可能收费，但至少能解决您的问题，让你解决掉使用ComfyUI最麻烦的环境和插件冲突问题，专注于插件使用及效果呈现。\n"
        "###\n"
        "1、仓库地址：https://github.com/msola-ht/Comfyui_custom_nodes\n"
        "2、WeChat：Lunare\n"
        "3、小红书：@何老师的AIGC服务(https://s.b1n.net/R890P)\n"
        "###\n"
    )
    print(additional_info)
    logging.info(additional_info)

def find_repositories(root_path, notes):
    """查找根路径下的所有GIT仓库"""
    repositories = []
    if os.path.isdir(root_path):
        for directory_name in os.listdir(root_path):
            path = os.path.join(root_path, directory_name)
            note = notes.get(path, "")
            repo = GitRepository(path, note)
            if repo.is_git_repository() and repo.url is not None:
                repositories.append(repo)
    return repositories

def get_notes_from_url(url):
    """从指定URL读取备注信息"""
    # 添加时间戳参数
    timestamp = int(time.time())
    url_with_timestamp = f"{url}?t={timestamp}"
    try:
        response = requests.get(url_with_timestamp, timeout=10)  # 设置超时时间为10秒
        if response.status_code == 200 and response.content:
            return response.json()
        else:
            print(f"{Fore.RED}无法从URL读取文件: {response.status_code}{Style.RESET_ALL}")
            logging.error(f"无法从URL读取文件: {response.status_code}")
    except requests.Timeout:
        print(f"{Fore.RED}请求超时: {url_with_timestamp}{Style.RESET_ALL}")
        logging.error(f"请求超时: {url_with_timestamp}")
    return {}

# 使用脚本
url = "https://raw.githubusercontent.com/msola-ht/Comfyui_custom_nodes_check/main/notes.json"
notes = get_notes_from_url(url)
check_git_updates('custom_nodes', notes)  # 检查当前目录下的custom_nodes及其第一层子目录