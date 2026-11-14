# GitHub-Radar: 自动化开源情报与精读流水线

## 项目定位
本项目旨在构建一个完全本地化、低成本的 GitHub 优质开源项目发现工具。通过结合 GitHub Search API 与 LLM（大语言模型），实现增量项目的自动化抓取、垃圾过滤、核心价值提炼，并最终生成结构化的本地数据看板。

## 目录结构规范
Agent 在执行代码编写与文件创建时，必须严格遵守以下目录层级，不得随意在项目根目录堆砌零散文件：

```text
github-radar/
├── data/                 # 存储 SQLite 数据库及本地抓取缓存
│   └── radar_history.db  # 历史去重与项目元数据库
├── docs/                 # 存放每日生成的 Markdown 简报
├── src/                  # 核心源代码目录
│   ├── fetcher.py        # GitHub API 数据拉取模块 (处理分页与速率限制)
│   ├── filter.py         # LLM 摘要与清洗模块 (基于 README 内容进行打分与总结)
│   ├── storage.py        # SQLite 数据库初始化与读写交互逻辑
│   └── render.py         # 静态 HTML 看板或 Markdown 渲染模块
├── .github/
│   └── workflows/        # GitHub Actions 定时任务配置 (daily_radar.yml)
├── .env.example          # 环境变量配置模板 (API Key / Base URL / Token)
├── main.py               # 主程序入口，负责按序调度 src 下的各个模块
├── requirements.txt      # 依赖清单 (如 requests, openai, python-dotenv 等)
└── README.md             # 本规范及说明文档