"""
GitHub API 数据拉取模块
负责通过 GitHub Search API 抓取高潜力开源项目，并获取其 README 内容
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from dotenv import load_dotenv

# 加载 .env 环境变量（从项目根目录寻找）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class GitHubFetcher:
    """GitHub 数据拉取器"""

    SEARCH_API_URL = "https://api.github.com/search/repositories"
    REPO_API_URL = "https://api.github.com/repos"

    def __init__(self, token: Optional[str] = None):
        # 优先使用传入的 token，否则从环境变量读取
        self.token = token or os.getenv("GITHUB_TOKEN", "").strip()
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Radar-Bot",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            print("[INFO] 未检测到 GITHUB_TOKEN，已启用匿名请求模式（速率受限为 60次/小时）")

    def fetch_trending_repos(
        self,
        days: int = 7,
        min_stars: int = 50,
        language: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 10,
        fetch_readme: bool = True,
        max_readme_chars: int = 3000,
    ) -> List[Dict[str, Any]]:
        """
        抓取近期创建且 Star 增长迅速的项目
        
        :param days: 追溯天数，默认近 7 天
        :param min_stars: 最小 Star 数，默认 50
        :param language: 编程语言筛选（如 Python, Rust, TypeScript 等）
        :param keyword: 关键词过滤
        :param limit: 获取结果最大数量
        :param fetch_readme: 是否自动拉取 README
        :param max_readme_chars: README 截取最大字符数
        :return: 仓库数据字典列表
        """
        # 计算起止日期
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 组装 query 语句，强制排除 archived 仓库
        query_parts = [
            f"created:>{start_date}",
            f"stars:>={min_stars}",
            "archived:false",
        ]
        if language:
            query_parts.append(f"language:{language}")
        if keyword:
            query_parts.append(keyword)

        query = " ".join(query_parts)
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100),
        }

        print(f"[INFO] 正在请求 GitHub Search API: query='{query}', limit={limit}...")
        try:
            resp = requests.get(
                self.SEARCH_API_URL,
                headers=self.headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] GitHub Search API 请求失败: {e}")
            if resp is not None and resp.status_code == 403:
                print("[WARNING] 可能已触发 GitHub API 速率限制，请在 .env 中配置 GITHUB_TOKEN")
            return []

        raw_items = data.get("items", [])
        total_count = data.get("total_count", 0)
        print(f"[INFO] 匹配到总候选仓库数: {total_count}，当前获取前 {len(raw_items[:limit])} 个")

        repos = []
        for item in raw_items[:limit]:
            full_name = item.get("full_name")
            repo_info: Dict[str, Any] = {
                "repo_name": full_name,
                "url": item.get("html_url"),
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "language": item.get("language") or "Unknown",
                "description": item.get("description") or "",
                "created_at": item.get("created_at"),
                "readme": "",
            }

            if fetch_readme:
                repo_info["readme"] = self.get_repo_readme(
                    full_name, max_chars=max_readme_chars
                )

            repos.append(repo_info)

        return repos

    def get_repo_readme(self, repo_full_name: str, max_chars: int = 3000) -> str:
        """
        获取指定仓库的 README 原始内容并截取前 max_chars 字符
        """
        url = f"{self.REPO_API_URL}/{repo_full_name}/readme"
        headers = dict(self.headers)
        # 请求 raw markdown 文本格式
        headers["Accept"] = "application/vnd.github.raw+json"

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                raw_text = resp.text
                truncated = raw_text[:max_chars]
                return truncated
            elif resp.status_code == 404:
                return "[No README found in repository]"
            else:
                return f"[Failed to fetch README: HTTP {resp.status_code}]"
        except requests.exceptions.Timeout:
            print(f"[WARNING] 获取 {repo_full_name} README 超时")
            return "[Timeout while fetching README]"
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] 获取 {repo_full_name} README 异常: {e}")
            return f"[Error fetching README: {e}]"


if __name__ == "__main__":
    print("=== [Fetcher 模块真实数据抓取测试] ===")
    fetcher = GitHubFetcher()

    # 按照需求测试抓取 3 个真实项目（近 7 天创建且 stars>=50）
    results = fetcher.fetch_trending_repos(
        days=7,
        min_stars=50,
        limit=3,
        fetch_readme=True,
        max_readme_chars=3000,
    )

    print(f"\n成功获取到 {len(results)} 个项目，详情如下：\n" + "-" * 60)
    for idx, repo in enumerate(results, 1):
        print(f"[{idx}] 项目名称: {repo['repo_name']}")
        print(f"    Star 数:   {repo['stars']}")
        print(f"    主要语言:  {repo['language']}")
        print(f"    开源地址:  {repo['url']}")
        print(f"    创建时间:  {repo['created_at']}")
        print(f"    项目简介:  {repo['description']}")
        print(f"    README 截取长度: {len(repo['readme'])} 字符")
        preview = repo['readme'][:150].replace('\n', ' ')
        print(f"    README 前瞻预览: {preview}...")
        print("-" * 60)
    
    print("=== [Fetcher 模块测试完成] ===")
