<div align="center">

# 🛰️ GitHub Radar (开源雷达)

**基于大语言模型的自动化开源情报流水线 · 每日甄选真正具备工程生产力的高价值开源项目**

[![GitHub Actions Workflow](https://img.shields.io/github/actions/workflow/status/Cuo-WeiQing/github-radar/daily_radar.yml?branch=main&label=Daily%20Radar&logo=githubactions)](https://github.com/Cuo-WeiQing/github-radar/actions)
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python)](https://www.python.org/)
[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-success?logo=githubpages)](https://cuo-weiqing.github.io/github-radar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <a href="https://cuo-weiqing.github.io/github-radar/"><b>🌐 在线交互看板</b></a> •
  <a href="./docs/"><b>📑 每日简报归档</b></a> •
  <a href="#-快速部署指南3分钟托管"><b>🚀 3分钟快速部署</b></a> •
  <a href="#-本地运行与开发"><b>💻 本地运行</b></a>
</p>

</div>

---

## 💡 为什么需要 GitHub Radar？

在 GitHub Trending 或各种热搜榜单上，我们经常看到：
- 大量 LeetCode 刷题题解与校招面试笔记；
- 动辄几千 Star 但只是收录链接的 `awesome-*` 导航合集；
- 恶搞玩具或无实质性工程代码的套壳项目。

**GitHub Radar** 旨在打造一个完全自主可控、极低运行成本的开源情报过滤器。它通过定时嗅探近 7 天内新建且 Star 增速迅猛的仓库，结合大模型（LLM）以**硬核技术评估员**的视角深度解析其 README，自动剔除噪音，提炼核心痛点与架构亮点，并生成结构化的暗黑风看板与每日简报。

---

## 🌟 核心特性

- 🔍 **智能增量嗅探**：通过 GitHub Search API 自动化拉取近期创建的高增长黑马项目，自动排除已归档（archived）仓库。
- 🧠 **LLM 深度精读与打分**：兼容 OpenAI 标准协议（完美适配 DeepSeek、GPT-4o、Moonshot 等），针对痛点与技术栈生成严苛评分（1-10分），坚决剔除刷题合集与纯链接导航。
- 💾 **本地增量去重引擎**：基于轻量级 SQLite (`data/radar_history.db`) 追踪历史项目，永久去重，杜绝大模型 Token 的二次消耗。
- 📊 **双端输出成果**：
  - **每日简报**：生成结构清晰的 Markdown 归档文件（收录在 [`docs/`](./docs/)）。
  - **单文件数据看板**：生成极简现代暗黑风的 [`index.html`](./index.html)，零外部 CDN 依赖，支持按语言筛选、评分过滤与实时模糊搜索。
- ⚡ **零服务器成本云端托管**：借助 GitHub Actions 定时执行，数据自动提交回版本库，通过 GitHub Pages 免费发布在线看板。

---

## 🖥️ 在线情报看板预览

> **在线访问地址**：👉 [https://cuo-weiqing.github.io/github-radar/](https://cuo-weiqing.github.io/github-radar/)

- 🎨 **GitHub Dark 原生暗黑质感**，自适应移动端与桌面端。
- ⚡ **零外部 CDN**：纯原生 HTML+CSS+JS 内联渲染，断网也能秒级打开。
- 🔎 **实时搜索与筛选**：毫秒级响应，按技术栈、语言、评分和关键字即时过滤。

---

## 🚀 快速部署指南（3分钟托管你自己的雷达）

你完全无需自备服务器，只需按照以下步骤 Fork 本项目即可在 GitHub 免费托管：

### 1. Fork 本仓库
点击本页面右上角 **Fork** 按钮，将本项目复制到你的个人 GitHub 账号下。

### 2. 配置 GitHub Actions Secrets
进入你的 Fork 仓库，依次点击 **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**，添加以下环境变量：

| Secret 变量名 | 说明 | 示例值 |
| :--- | :--- | :--- |
| `LLM_API_KEY` | **必需**。大语言模型 API 密钥 | `sk-xxxxxxxxxxxxxxxxxxxxxxxx` |
| `LLM_BASE_URL` | **必需**。模型服务端点 (需保留 `/v1`) | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | **必需**。使用的模型名称 | `deepseek-chat` 或 `gpt-4o-mini` |
| `GH_PAT` | *可选*。GitHub 个人访问令牌，用于提升 API 速率 | `ghp_xxxxxxxxxxxxxxxxxxxxxxxx` |

### 3. 开启 GitHub Pages 在线看板
1. 进入仓库的 **Settings** -> **Pages**。
2. 在 **Build and deployment** 下的 **Source** 选择 `Deploy from a branch`。
3. 分支选择 `main`，目录选择 `/ (root)`，点击 **Save**。
4. 几分钟后即可通过 `https://<你的用户名>.github.io/<仓库名>/` 访问你的专属情报站！

### 4. 自动化运行节奏
- 每日云端巡航已在 [`.github/workflows/daily_radar.yml`](./.github/workflows/daily_radar.yml) 中配置为 **每天 UTC 0:00 (北京时间 08:00)** 自动触发。
- 你也可以在 **Actions** 页面随时点击 **Daily GitHub Radar Pipeline** -> **Run workflow** 手动触发单次立即巡航。

---

## 💻 本地运行与开发

如果你想在本地环境中运行或二次开发：

```bash
# 1. 克隆项目到本地
git clone https://github.com/Cuo-WeiQing/github-radar.git
cd github-radar

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置本地环境变量
cp .env.example .env
# 使用编辑器修改 .env，填入你的 LLM_API_KEY 等配置
```

在本地运行完整流水线：
```bash
python main.py
```
执行完毕后，直接双击根目录下的 `index.html` 即可在本地浏览器预览看板。

---

## 📁 项目结构说明

```text
github-radar/
├── data/
│   └── radar_history.db           # SQLite 历史数据库与查重持久层
├── docs/
│   ├── DEV_SPEC.md                # 架构设计规范与开发者约束文档
│   └── YYYY-MM-DD.md              # 每日 AI 评估简报归档
├── src/
│   ├── fetcher.py                 # GitHub Search API 抓取与 README 截取
│   ├── filter.py                  # 大模型结构化评审与 Prompt 过滤
│   ├── storage.py                 # SQLite 增量查重与存储交互
│   └── render.py                  # Markdown 日报与 HTML 看板双端生成器
├── .github/
│   └── workflows/
│       └── daily_radar.yml        # GitHub Actions 自动化定时任务
├── .env.example                   # 环境变量配置模板
├── index.html                     # 现代暗黑风静态交互看板
├── main.py                        # 全流程主调度程序
├── requirements.txt               # 运行依赖包清单
└── README.md                      # 正式项目说明文档
```

---

## 📄 协议与归档

- 本项目采用 [MIT License](./LICENSE) 开源。
- 更多详细模块设计与内部规范，请参阅内部文档 [docs/DEV_SPEC.md](./docs/DEV_SPEC.md)。
- 欢迎提 Issue 或 PR 贡献更多有趣的项目过滤规则！
