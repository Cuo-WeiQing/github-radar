"""
SQLite 存储模块
负责 radar_history.db 的初始化、去重检查与项目数据持久化
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

# 默认数据库路径：指向项目根目录下的 data/radar_history.db
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "radar_history.db"


def get_db_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    """获取数据库连接并配置 Row 工厂以支持字典形式访问"""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path | str] = None) -> None:
    """初始化数据库表结构"""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with get_db_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repos (
                repo_name TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                stars INTEGER DEFAULT 0,
                language TEXT,
                description TEXT,
                pain_point TEXT,
                tech_highlights TEXT,
                score REAL DEFAULT 0.0,
                created_at TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def is_repo_exists(repo_name: str, db_path: Optional[Path | str] = None) -> bool:
    """检查指定仓库是否已存在于数据库中（用于去重）"""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM repos WHERE repo_name = ? LIMIT 1", (repo_name,))
        return cursor.fetchone() is not None


def save_repo(repo_data: Dict[str, Any], db_path: Optional[Path | str] = None) -> bool:
    """
    保存或更新仓库信息到数据库
    repo_data 应包含字段：
    repo_name (必需), url (必需), stars, language, description,
    pain_point, tech_highlights, score, created_at
    """
    init_db(db_path)
    if "repo_name" not in repo_data or "url" not in repo_data:
        raise ValueError("repo_data 必须包含 'repo_name' 和 'url' 字段")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO repos (
                repo_name, url, stars, language, description,
                pain_point, tech_highlights, score, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                repo_data.get("repo_name"),
                repo_data.get("url"),
                repo_data.get("stars", 0),
                repo_data.get("language"),
                repo_data.get("description"),
                repo_data.get("pain_point"),
                repo_data.get("tech_highlights"),
                repo_data.get("score", 0.0),
                repo_data.get("created_at"),
            ),
        )
        conn.commit()
    return True


def get_repo(repo_name: str, db_path: Optional[Path | str] = None) -> Optional[Dict[str, Any]]:
    """根据 repo_name 获取仓库详情"""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repos WHERE repo_name = ?", (repo_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_all_repos(min_score: int = 0, db_path: Optional[Path | str] = None) -> List[Dict[str, Any]]:
    """获取所有评分大于等于 min_score 的已入库项目"""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM repos WHERE score >= ? ORDER BY score DESC, stars DESC",
            (min_score,),
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_repo(repo_name: str, db_path: Optional[Path | str] = None) -> bool:
    """删除指定仓库记录（用于测试清理脏数据等）"""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repos WHERE repo_name = ?", (repo_name,))
        conn.commit()
        return cursor.rowcount > 0


if __name__ == "__main__":
    print("=== [Storage 模块自测开始] ===")
    
    # 1. 初始化数据库测试
    init_db()
    print("1. 数据库初始化: 成功 [data/radar_history.db]")
    
    # 测试用 mock 数据
    test_repo_name = "test-owner/test-radar-repo"
    mock_data = {
        "repo_name": test_repo_name,
        "url": "https://github.com/test-owner/test-radar-repo",
        "stars": 128,
        "language": "Python",
        "description": "A lightweight automated radar tool for GitHub trending repos.",
        "pain_point": "解决开发者无法及时获知新发布的高潜力开源项目的问题",
        "tech_highlights": "自动化拉取、LLM总结、轻量级SQLite存储",
        "score": 8.5,
        "created_at": "2026-11-01T00:00:00Z"
    }

    # 2. 查重测试（写入前）
    exists_before = is_repo_exists(test_repo_name)
    print(f"2. 写入前查重: is_repo_exists = {exists_before} (预期: False)")
    assert not exists_before, "测试失败: 数据写入前查重应为 False"

    # 3. 写入测试
    save_result = save_repo(mock_data)
    print(f"3. 写入数据: save_repo = {save_result} (预期: True)")
    assert save_result, "测试失败: 写入应返回 True"

    # 4. 查重测试（写入后）与读取验证
    exists_after = is_repo_exists(test_repo_name)
    print(f"4. 写入后查重: is_repo_exists = {exists_after} (预期: True)")
    assert exists_after, "测试失败: 数据写入后查重应为 True"

    fetched = get_repo(test_repo_name)
    print(f"5. 读取验证: repo_name={fetched['repo_name']}, stars={fetched['stars']}, score={fetched['score']}")
    assert fetched["stars"] == 128 and fetched["score"] == 8.5, "测试失败: 读取出的数据不匹配"

    # 6. 清理测试脏数据
    cleaned = delete_repo(test_repo_name)
    exists_clean = is_repo_exists(test_repo_name)
    print(f"6. 清理测试数据: delete_repo = {cleaned}, 清理后查重 is_repo_exists = {exists_clean} (预期: False)")
    assert not exists_clean, "测试失败: 测试数据清理失败"

    print("=== [Storage 模块自测通过，所有断言均成功！] ===\n")
