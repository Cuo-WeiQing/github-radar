"""
LLM 摘要与价值打分模块
使用 OpenAI SDK 兼容接口，对候选项目进行严格质量审查与核心价值提炼
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 配置
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

SYSTEM_PROMPT = """你是一名经验极其丰富的硬核技术评估专家与开源项目架构师。你的任务是对候选开源项目进行严格、挑剔的质量评估与价值提炼。

【严格过滤准则】
1. 坚决剔除（is_valid 设为 false，score 为 1~4）：
   - 纯面试题库、LeetCode 刷题合集、面经整理；
   - awesome-* 类型的资源导航汇总列表、纯链接收集；
   - 纯技术教程、学习笔记、中文翻译搬运、电子书、纯文档项目；
   - 没有实质性代码实现的空壳仓库、无任何技术壁垒的套壳项目；
   - 刷 Star 倾向或无实际工程价值的玩具仓库。

2. 推荐准则（is_valid 设为 true，score 为 7~10）：
   - 具备独立完整的代码工程实现，解决真实且具体的开发者痛点或生产难题；
   - 核心技术栈亮眼、系统设计优良、代码质量高或具备创新突破；
   - 实用性强、可部署、文档说明健全。

【输出要求】
必须直接输出合法的单行或多行 JSON 字符串，严禁包含任何前缀、问候语或额外解释。
输出格式严格如下：
{
  "is_valid": true,
  "pain_point": "一句话说明解决什么实际痛点（简练客观，50字以内）",
  "tech_highlights": "核心技术栈与工程亮点（突出架构、关键库与设计特色，80字以内）",
  "score": 8
}
"""


class LLMFilter:
    """基于大模型的开源项目评估过滤器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = (api_key or os.getenv("LLM_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).strip()
        self.model = (model or os.getenv("LLM_MODEL", "gpt-4o-mini")).strip()

        # 判断 API KEY 是否有效（排除占位符）
        self.is_configured = bool(
            self.api_key and self.api_key != "your_api_key_here"
        )
        if self.is_configured:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def clean_json_response(self, text: str) -> str:
        """剥离 Markdown 代码块标记（```json ... ``` 或 ``` ... ```），提取纯 JSON 字符串"""
        if not text:
            return ""
        stripped = text.strip()
        # 移除 ```json 和 ``` 标记
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # 匹配首个 { 到最后一个 }
        first_brace = stripped.find("{")
        last_brace = stripped.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return stripped[first_brace : last_brace + 1].strip()
        return stripped

    def evaluate_repo(self, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估单个仓库
        
        :param repo_info: 包含 repo_name, url, description, language, readme 等字段的字典
        :return: 评估结果字典，格式包含 is_valid, pain_point, tech_highlights, score
        """
        repo_name = repo_info.get("repo_name", "Unknown")
        if not self.is_configured or self.client is None:
            print(f"[WARN] 未配置有效 LLM_API_KEY，跳过对 {repo_name} 的大模型评估，返回安全兜底值")
            return {
                "is_valid": False,
                "pain_point": "未配置 LLM API KEY，未能完成评估",
                "tech_highlights": "",
                "score": 0,
            }

        user_content = (
            f"项目名称: {repo_name}\n"
            f"项目地址: {repo_info.get('url', '')}\n"
            f"主要语言: {repo_info.get('language', 'Unknown')}\n"
            f"项目简介: {repo_info.get('description', '')}\n"
            f"README 片段 (前3000字符):\n{repo_info.get('readme', '')}\n"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                timeout=30,
            )
            raw_text = response.choices[0].message.content or ""
            return self._parse_and_validate(raw_text, repo_name)
        except Exception as e:
            print(f"[ERROR] 评估项目 {repo_name} 时发生异常: {e}")
            return {
                "is_valid": False,
                "pain_point": f"评估异常: {str(e)[:60]}",
                "tech_highlights": "",
                "score": 0,
            }

    def _parse_and_validate(self, raw_text: str, repo_name: str = "") -> Dict[str, Any]:
        """清洗并解析大模型返回的内容"""
        cleaned = self.clean_json_response(raw_text)
        try:
            data = json.loads(cleaned)
            is_valid = bool(data.get("is_valid", False))
            pain_point = str(data.get("pain_point", "")).strip()
            tech_highlights = str(data.get("tech_highlights", "")).strip()
            score = int(data.get("score", 0))
            score = max(0, min(10, score))  # 限制在 0~10 分

            return {
                "is_valid": is_valid,
                "pain_point": pain_point,
                "tech_highlights": tech_highlights,
                "score": score,
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"[ERROR] 解析 {repo_name} 评估结果 JSON 失败: {e}\n原始输出: {raw_text[:200]}")
            return {
                "is_valid": False,
                "pain_point": "模型返回数据解析失败",
                "tech_highlights": "",
                "score": 0,
            }


if __name__ == "__main__":
    print("=== [Filter 模块自测开始] ===")
    filter_instance = LLMFilter()

    # 1. 测试 JSON 清洗逻辑
    print("1. 测试 Markdown 代码块清洗与 JSON 提取逻辑:")
    dirty_json_1 = "```json\n{\"is_valid\": true, \"pain_point\": \"测试痛点\", \"tech_highlights\": \"Rust+Tokio\", \"score\": 9}\n```"
    parsed_1 = filter_instance._parse_and_validate(dirty_json_1, "test/repo-1")
    assert parsed_1["is_valid"] is True and parsed_1["score"] == 9, "测试 1 失败: 无法正确解析 ```json 代码块"
    print(f"   [通过] 带 ```json 标记清洗成功: is_valid={parsed_1['is_valid']}, score={parsed_1['score']}")

    dirty_json_2 = "这是一段前置问候：\n```\n{\"is_valid\": false, \"pain_point\": \"纯面试题\", \"tech_highlights\": \"无\", \"score\": 2}\n```\n谢谢！"
    parsed_2 = filter_instance._parse_and_validate(dirty_json_2, "test/repo-2")
    assert parsed_2["is_valid"] is False and parsed_2["score"] == 2, "测试 2 失败: 无法处理前后夹带文本的代码块"
    print(f"   [通过] 混合文本清洗成功: is_valid={parsed_2['is_valid']}, score={parsed_2['score']}")

    # 2. 测试异常格式兜底逻辑
    print("2. 测试异常格式与畸形数据兜底逻辑:")
    bad_json = "这是完全无法解析的内容，没有JSON"
    parsed_bad = filter_instance._parse_and_validate(bad_json, "test/repo-bad")
    assert parsed_bad["is_valid"] is False and parsed_bad["score"] == 0, "测试 3 失败: 畸形数据兜底异常"
    print(f"   [通过] 畸形数据安全兜底成功: is_valid={parsed_bad['is_valid']}, score={parsed_bad['score']}")

    # 3. 检查当前是否配置了有效 LLM_API_KEY
    if filter_instance.is_configured:
        print("3. 检测到有效 LLM_API_KEY，进行真实 API 连通性测试...")
        sample_repo = {
            "repo_name": "example/fast-proxy",
            "url": "https://github.com/example/fast-proxy",
            "language": "Go",
            "description": "A high performance reverse proxy written in Go",
            "readme": "# Fast-Proxy\nA high-performance reverse proxy built with Go and epoll.",
        }
        res = filter_instance.evaluate_repo(sample_repo)
        print(f"   [真实 API 返回结果]: {res}")
    else:
        print("3. 当前 .env 为初始模板 (未配置有效 LLM_API_KEY)，自动进入 Mock 模拟数据流测试:")
        mock_sample = {
            "repo_name": "mock/high-performance-db",
            "url": "https://github.com/mock/high-performance-db",
            "language": "Rust",
            "description": "Embedded transactional KV store written in Rust",
            "readme": "# Mock DB\nHigh-performance concurrent B+Tree storage engine.",
        }
        res = filter_instance.evaluate_repo(mock_sample)
        print(f"   [未配置 Key 时安全降级返回值]: {res}")
        assert res["is_valid"] is False and "未配置" in res["pain_point"], "测试 4 失败: 安全降级返回值不符合预期"
        print("   [通过] 降级与兜底保护机制正常运行")

    print("=== [Filter 模块自测通过，所有断言均成功！] ===\n")
