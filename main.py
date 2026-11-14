"""
GitHub-Radar 主程序入口
负责串联数据抓取、去重检查、大模型评估与双端渲染全流程
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# 引入核心功能模块
from src.storage import init_db, is_repo_exists, save_repo, get_all_repos
from src.fetcher import GitHubFetcher
from src.filter import LLMFilter
from src.render import render_markdown, render_html


def run_pipeline(
    days: int = 7,
    min_stars: int = 50,
    fetch_limit: int = 20,
    language: str = None,
    keyword: str = None,
):
    """运行 GitHub Radar 主流水线"""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print("=" * 65)
    print(f"🛰️  GitHub-Radar 自动化开源情报流水线启动 [{today_str}]")
    print("=" * 65)

    # 1. 初始化数据库
    print("\n[Step 1/5] 初始化本地 SQLite 数据库...")
    init_db()
    print("✓ 数据库结构已就绪 (data/radar_history.db)")

    # 2. 抓取候选开源项目
    print(f"\n[Step 2/5] 正在通过 GitHub API 检索高增长项目 (近 {days} 天, Stars>={min_stars})...")
    fetcher = GitHubFetcher()
    candidates = fetcher.fetch_trending_repos(
        days=days,
        min_stars=min_stars,
        language=language,
        keyword=keyword,
        limit=fetch_limit,
        fetch_readme=True,
        max_readme_chars=3000,
    )
    print(f"✓ 成功获取候选项目: {len(candidates)} 个")

    if not candidates:
        print("[WARN] 未抓取到符合条件的候选项目，流水线结束。")
        return

    # 3. 历史增量去重
    print("\n[Step 3/5] 执行数据库历史增量去重 (节约 Token)...")
    new_candidates = []
    skipped_count = 0
    for repo in candidates:
        repo_name = repo["repo_name"]
        if is_repo_exists(repo_name):
            print(f"  - [跳过] {repo_name} 已存在于历史库中")
            skipped_count += 1
        else:
            new_candidates.append(repo)

    print(f"✓ 去重结果: 历史已处理 {skipped_count} 个，待深度评估新项目 {len(new_candidates)} 个")

    # 4. LLM 智能精读与质量打分
    print("\n[Step 4/5] 启动 AI 硬核技术评估与价值提炼...")
    llm_filter = LLMFilter()
    if not llm_filter.is_configured:
        print("[NOTICE] 当前未配置有效的 LLM_API_KEY。如需体验大模型完整过滤，请在 .env 中填写 key。")

    evaluated_today = []
    for idx, repo in enumerate(new_candidates, 1):
        repo_name = repo["repo_name"]
        print(f"  [{idx}/{len(new_candidates)}] 评估中: {repo_name} (★{repo['stars']})...", end=" ", flush=True)

        eval_result = llm_filter.evaluate_repo(repo)
        
        # 将评估结果回填至仓库信息
        repo["is_valid"] = eval_result.get("is_valid", False)
        repo["pain_point"] = eval_result.get("pain_point", "")
        repo["tech_highlights"] = eval_result.get("tech_highlights", "")
        repo["score"] = eval_result.get("score", 0)

        # 无论分数高低均持久化入库，避免未来重复消耗 Token 评估
        save_repo(repo)
        evaluated_today.append(repo)

        status_flag = "✓ 入选" if repo["score"] >= 7 else "✗ 淘汰"
        print(f"-> 评分: {repo['score']}/10 [{status_flag}]")

    # 5. 双端渲染 (Markdown 简报 + 现代暗黑风静态看板)
    print("\n[Step 5/5] 生成双端成果输出...")
    # 生成当日 Markdown 简报
    md_file = render_markdown(evaluated_today, date_str=today_str)
    
    # 从数据库获取所有历史优质项目 (Score >= 6) 生成静态看板
    all_quality_repos = get_all_repos(min_score=6)
    html_file = render_html(all_quality_repos)

    print("\n" + "=" * 65)
    print("🎉 GitHub Radar 流水线执行完毕！")
    print(f"• 候选项目总量: {len(candidates)}")
    print(f"• 历史去重过滤: {skipped_count}")
    print(f"• 今日新评估数: {len(new_candidates)}")
    print(f"• 今日高分入选: {len([p for p in evaluated_today if p.get('score', 0) >= 7])}")
    print(f"• 每日精选简报: {md_file}")
    print(f"• 本地数据看板: {html_file}")
    print("=" * 65)


if __name__ == "__main__":
    # 支持默认参数运行，可在此调节追溯天数和限制
    run_pipeline(days=7, min_stars=50, fetch_limit=10)
