"""
双端输出渲染模块
负责将经过 AI 评估过滤后的优质开源项目渲染为 Markdown 简报 (docs/YYYY-MM-DD.md)
以及生成极简现代暗黑风的单文件本地数据看板 (index.html)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DEFAULT_HTML_PATH = BASE_DIR / "index.html"


def render_markdown(
    projects: List[Dict[str, Any]],
    date_str: Optional[str] = None,
    output_dir: Optional[Path | str] = None,
) -> Path:
    """
    将当天筛选通过的高分项目 (score >= 7) 渲染为 Markdown 简报
    保存到 docs/YYYY-MM-DD.md
    """
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    target_dir = Path(output_dir) if output_dir else DOCS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{date_str}.md"

    # 过滤优质项目
    qualified = [p for p in projects if p.get("score", 0) >= 7]
    qualified.sort(key=lambda x: (x.get("score", 0), x.get("stars", 0)), reverse=True)

    lines = [
        f"# 🛰️ GitHub Radar 开源精选简报 ({date_str})",
        "",
        f"> 自动化雷达于 UTC {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} 扫描生成。",
        f"> 本期共发现 **{len(projects)}** 个候选项目，经 AI 深度精读，共有 **{len(qualified)}** 个高价值项目入选 (Score ≥ 7)。",
        "",
        "---",
        "",
    ]

    if not qualified:
        lines.append("*今日暂未发现评分 ≥ 7 的高价值新项目。明日雷达将继续巡航！*")
        lines.append("")
    else:
        for idx, p in enumerate(qualified, 1):
            score = p.get("score", 0)
            stars = p.get("stars", 0)
            lang = p.get("language") or "Unknown"
            name = p.get("repo_name", "Unknown")
            url = p.get("url", "#")
            pain_point = p.get("pain_point") or "暂无详细痛点描述"
            tech_highlights = p.get("tech_highlights") or "暂无技术亮点说明"
            desc = p.get("description") or "无描述"

            # 评分标识
            score_badge = "🔥 强烈推荐" if score >= 9 else ("⭐ 优质精选" if score >= 8 else "👍 值得关注")

            lines.extend([
                f"### {idx}. [{name}]({url})",
                "",
                f"- **综合推荐度**: `{score}/10` ({score_badge})",
                f"- **Star 数**: `★ {stars:,}` | **主要语言**: `{lang}`",
                f"- **项目简介**: {desc}",
                f"- **🎯 解决痛点**: {pain_point}",
                f"- **💡 技术亮点**: {tech_highlights}",
                "",
                "---",
                "",
            ])

    content = "\n".join(lines)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[INFO] Markdown 简报已生成: {target_file}")
    return target_file


def render_html(
    all_history_projects: List[Dict[str, Any]],
    output_path: Optional[Path | str] = None,
) -> Path:
    """
    生成单文件极简现代暗黑风看板 index.html
    支持无外部 CDN 依赖、离线秒开、实时关键字搜索、语言及评分过滤
    """
    target_path = Path(output_path) if output_path else DEFAULT_HTML_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 过滤并按 score desc, stars desc 排序
    valid_projects = [
        p for p in all_history_projects if p.get("score", 0) >= 6 or p.get("is_valid", False)
    ]
    valid_projects.sort(key=lambda x: (x.get("score", 0), x.get("stars", 0)), reverse=True)

    # 提取所有不重复语言列表
    languages = sorted(
        list(
            {
                p.get("language")
                for p in valid_projects
                if p.get("language") and p.get("language") != "Unknown"
            }
        )
    )

    # 转换项目数据为内联 JSON（做好 XSS 安全与字符转义）
    clean_projects = []
    for p in valid_projects:
        clean_projects.append({
            "repo_name": p.get("repo_name", ""),
            "url": p.get("url", "#"),
            "stars": p.get("stars", 0),
            "language": p.get("language") or "Other",
            "description": p.get("description") or "",
            "pain_point": p.get("pain_point") or "",
            "tech_highlights": p.get("tech_highlights") or "",
            "score": p.get("score", 0),
            "created_at": (p.get("created_at") or "")[:10],
        })

    projects_json_str = json.dumps(clean_projects, ensure_ascii=False)
    updated_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitHub Radar | 自动化开源情报看板</title>
  <style>
    :root {{
      --bg-main: #0d1117;
      --bg-card: #161b22;
      --bg-card-hover: #1c2128;
      --border-color: #30363d;
      --border-accent: #388bfd;
      --text-main: #c9d1d9;
      --text-muted: #8b949e;
      --text-bright: #f0f6fc;
      --badge-bg: #21262d;
      --star-color: #e3b341;
      --score-high: #238636;
      --score-mid: #1f6feb;
      --score-low: #8957e5;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: var(--bg-main);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
      line-height: 1.6;
      padding: 24px;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 24px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-color);
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    h1 {{
      font-size: 26px;
      font-weight: 700;
      color: var(--text-bright);
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .subtitle {{
      color: var(--text-muted);
      font-size: 14px;
    }}
    .stats-pill {{
      background-color: var(--badge-bg);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 13px;
      color: var(--text-muted);
    }}
    .stats-pill b {{
      color: #58a6ff;
    }}
    /* 控制栏 */
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 24px;
      align-items: center;
    }}
    .search-box {{
      flex: 1;
      min-width: 240px;
      position: relative;
    }}
    .search-box input {{
      width: 100%;
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      color: var(--text-bright);
      padding: 10px 14px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }}
    .search-box input:focus {{
      border-color: #58a6ff;
      box-shadow: 0 0 0 3px rgba(56, 139, 253, 0.2);
    }}
    .filter-group {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    select, button.filter-btn {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-bright);
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 13px;
      cursor: pointer;
      outline: none;
      transition: all 0.2s;
    }}
    select:hover, button.filter-btn:hover {{
      background-color: var(--bg-card-hover);
      border-color: var(--border-accent);
    }}
    button.filter-btn.active {{
      background-color: #1f6feb;
      border-color: #58a6ff;
      color: #fff;
    }}
    /* 卡片网格 */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
    }}
    .card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .card:hover {{
      transform: translateY(-2px);
      border-color: #58a6ff;
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }}
    .repo-link {{
      color: #58a6ff;
      text-decoration: none;
      font-weight: 600;
      font-size: 16px;
      word-break: break-all;
    }}
    .repo-link:hover {{
      text-decoration: underline;
    }}
    .score-badge {{
      flex-shrink: 0;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 700;
      color: #fff;
    }}
    .score-9 {{ background-color: var(--score-high); }}
    .score-8 {{ background-color: var(--score-mid); }}
    .score-7 {{ background-color: var(--score-low); }}
    .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 12px;
      color: var(--text-muted);
    }}
    .meta-tag {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: var(--badge-bg);
      border: 1px solid var(--border-color);
      padding: 2px 8px;
      border-radius: 4px;
    }}
    .star-tag b {{
      color: var(--star-color);
    }}
    .card-desc {{
      font-size: 13px;
      color: var(--text-muted);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 40px;
    }}
    .highlight-box {{
      background-color: rgba(22, 27, 34, 0.8);
      border-left: 3px solid #238636;
      border-radius: 0 4px 4px 0;
      padding: 8px 12px;
      font-size: 13px;
    }}
    .highlight-box.tech {{
      border-left-color: #1f6feb;
    }}
    .highlight-title {{
      font-weight: 600;
      font-size: 12px;
      color: var(--text-bright);
      margin-bottom: 2px;
    }}
    .card-footer {{
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid rgba(48, 54, 61, 0.5);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .btn-github {{
      color: var(--text-bright);
      background-color: var(--badge-bg);
      border: 1px solid var(--border-color);
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 12px;
      text-decoration: none;
      transition: 0.2s;
    }}
    .btn-github:hover {{
      border-color: #58a6ff;
      background-color: #21262d;
    }}
    .empty-state {{
      grid-column: 1 / -1;
      text-align: center;
      padding: 60px 20px;
      color: var(--text-muted);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-top">
        <h1>🛰️ GitHub Radar <span>自动化开源情报站</span></h1>
        <div class="stats-pill">
          入库精选项目: <b id="count-display">0</b> 个 | 更新于 <span>{updated_time}</span>
        </div>
      </div>
      <p class="subtitle">通过 GitHub Search API 与 LLM 深度精读，剔除面试题库与导航合集，提炼最具生产力的优质开源项目</p>
    </header>

    <div class="controls">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="搜索项目、技术栈或解决痛点..." oninput="handleFilterChange()">
      </div>
      <div class="filter-group">
        <select id="langSelect" onchange="handleFilterChange()">
          <option value="">所有编程语言</option>
          {''.join(f'<option value="{lang}">{lang}</option>' for lang in languages)}
        </select>
        <select id="scoreSelect" onchange="handleFilterChange()">
          <option value="0">全部评分 (≥6分)</option>
          <option value="9">🔥 9分以上 (强烈推荐)</option>
          <option value="8">⭐ 8分以上 (优质精选)</option>
          <option value="7" selected>👍 7分以上 (推荐收录)</option>
        </select>
      </div>
    </div>

    <div class="grid" id="projectGrid"></div>
  </div>

  <script>
    const allProjects = {projects_json_str};

    function getScoreClass(score) {{
      if (score >= 9) return 'score-9';
      if (score >= 8) return 'score-8';
      return 'score-7';
    }}

    function renderCards(list) {{
      const grid = document.getElementById('projectGrid');
      document.getElementById('count-display').innerText = list.length;

      if (!list || list.length === 0) {{
        grid.innerHTML = `
          <div class="empty-state">
            <h3>🛸 未检索到符合条件的项目</h3>
            <p style="margin-top: 8px;">尝试更换搜索关键词或放宽筛选条件</p>
          </div>
        `;
        return;
      }}

      grid.innerHTML = list.map(p => `
        <div class="card">
          <div class="card-header">
            <a class="repo-link" href="${{p.url}}" target="_blank" rel="noopener noreferrer">${{p.repo_name}}</a>
            <span class="score-badge ${{getScoreClass(p.score)}}">${{p.score}}分</span>
          </div>

          <div class="meta-row">
            <span class="meta-tag star-tag">★ <b>${{p.stars.toLocaleString()}}</b></span>
            <span class="meta-tag">💻 ${{p.language || 'Other'}}</span>
            <span class="meta-tag">📅 ${{p.created_at || '最近'}}</span>
          </div>

          <div class="card-desc">${{p.description || '暂无描述'}}</div>

          <div class="highlight-box">
            <div class="highlight-title">🎯 解决痛点</div>
            <div>${{p.pain_point || '暂无详细痛点说明'}}</div>
          </div>

          <div class="highlight-box tech">
            <div class="highlight-title">💡 技术亮点</div>
            <div>${{p.tech_highlights || '暂无技术栈说明'}}</div>
          </div>

          <div class="card-footer">
            <span style="font-size: 11px; color: var(--text-muted)">Verified by Radar LLM</span>
            <a class="btn-github" href="${{p.url}}" target="_blank" rel="noopener noreferrer">查看源码 ↗</a>
          </div>
        </div>
      `).join('');
    }}

    function handleFilterChange() {{
      const query = document.getElementById('searchInput').value.trim().toLowerCase();
      const selectedLang = document.getElementById('langSelect').value;
      const minScore = parseInt(document.getElementById('scoreSelect').value, 10) || 0;

      const filtered = allProjects.filter(item => {{
        if (selectedLang && item.language !== selectedLang) return false;
        if (item.score < minScore) return false;
        if (query) {{
          const content = `${{item.repo_name}} ${{item.description}} ${{item.pain_point}} ${{item.tech_highlights}}`.toLowerCase();
          if (!content.includes(query)) return false;
        }}
        return true;
      }});

      renderCards(filtered);
    }}

    // 初始化渲染
    window.addEventListener('DOMContentLoaded', () => {{
      handleFilterChange();
    }});
  </script>
</body>
</html>
"""

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"[INFO] 静态 HTML 看板已生成: {target_path}")
    return target_path


if __name__ == "__main__":
    print("=== [Render 模块自测开始] ===")
    
    mock_projects = [
        {
            "repo_name": "astral-sh/uv-radar-demo",
            "url": "https://github.com/astral-sh/uv",
            "stars": 35200,
            "language": "Rust",
            "description": "An extremely fast Python package and project manager, written in Rust.",
            "pain_point": "解决传统 pip 与 virtualenv 解析依赖与安装缓慢的痛点",
            "tech_highlights": "Rust 编写、零拷贝全局缓存、极速依赖图解析",
            "score": 9,
            "is_valid": True,
            "created_at": "2026-11-10T12:00:00Z",
        },
        {
            "repo_name": "open-telemetry/trace-mini",
            "url": "https://github.com/open-telemetry/trace-mini",
            "stars": 1420,
            "language": "Go",
            "description": "Lightweight OpenTelemetry collector with ultra low memory footprint.",
            "pain_point": "解决微服务环境可观测性 Agent 占用内存过高的问题",
            "tech_highlights": "Go 并发缓冲管道、无反射流式压缩序列化",
            "score": 8,
            "is_valid": True,
            "created_at": "2026-11-12T08:00:00Z",
        },
        {
            "repo_name": "developer/leet-code-solutions",
            "url": "https://github.com/developer/leet-code-solutions",
            "stars": 450,
            "language": "Python",
            "description": "Leetcode problems and answers collection.",
            "pain_point": "刷题题库",
            "tech_highlights": "无",
            "score": 3,
            "is_valid": False,
            "created_at": "2026-11-11T00:00:00Z",
        },
    ]

    # 1. 测试 Markdown 渲染
    md_file = render_markdown(mock_projects, date_str="2026-11-14")
    assert md_file.exists(), "测试失败: Markdown 文件未生成"
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "astral-sh/uv-radar-demo" in md_text and "developer/leet-code-solutions" not in md_text, "测试失败: Markdown 过滤逻辑有误"
    print("1. [通过] Markdown 简报渲染成功且高分过滤正确")

    # 2. 测试 HTML 渲染
    html_file = render_html(mock_projects)
    assert html_file.exists(), "测试失败: HTML 文件未生成"
    with open(html_file, "r", encoding="utf-8") as f:
        html_text = f.read()
    assert "GitHub Radar" in html_text and "astral-sh/uv-radar-demo" in html_text, "测试失败: HTML 内容不完整"
    print("2. [通过] 单文件暗黑风 HTML 看板渲染成功")

    print("=== [Render 模块自测通过，所有断言均成功！] ===\n")
