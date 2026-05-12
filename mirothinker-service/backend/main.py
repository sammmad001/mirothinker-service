"""
MiroThinker Online Service - FastAPI Backend
Integrates Alibaba Bailian LLM with MCP tools for deep research.
Quality-enhanced version with fixed channels, credibility scoring,
contradiction detection, and quality check pipeline.
"""

import asyncio
import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# === Configuration ===
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
JINA_API_KEY = os.getenv("JINA_API_KEY", "")

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
SERPER_BASE_URL = "https://google.serper.dev"
JINA_BASE_URL = "https://r.jina.ai"

# Model mapping
MODEL_MAP = {
    "qwen-turbo": "qwen-turbo",
    "qwen-flash": "qwen-flash",
    "qwen-plus": "qwen-plus",
    "qwen-max": "qwen-max",
}

# === Fixed Information Channels ===
CORE_SOURCES = {
    "academic": {
        "name": "学术信源",
        "search_template": "site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov {query}",
        "priority": "highest",
    },
    "tech": {
        "name": "技术信源",
        "search_template": "site:github.com OR site:stackoverflow.com OR site:docs.python.org {query}",
        "priority": "high",
    },
    "news": {
        "name": "新闻信源",
        "search_template": "site:reuters.com OR site:apnews.com OR site:bbc.com/news {query}",
        "priority": "high",
    },
    "data": {
        "name": "数据信源",
        "search_template": "site:data.worldbank.org OR site:imf.org OR site:data.stats.gov.cn {query}",
        "priority": "medium",
    },
}

# === Domain Configurations ===
DOMAIN_CONFIGS = {
    "tech": {
        "name": "技术/科技",
        "core_sources": ["github.com", "stackoverflow.com", "arxiv.org"],
        "keywords": ["AI", "机器学习", "深度学习", "Python", "软件", "算法", "区块链", "AI/ML", "software", "algorithm"],
        "prompt_variant": "technical",
    },
    "finance": {
        "name": "金融/经济",
        "core_sources": ["reuters.com", "bloomberg.com", "imf.org", "worldbank.org"],
        "keywords": ["经济", "金融", "GDP", "通胀", "投资", "股市", "市场", "economy", "finance", "investment", "market"],
        "prompt_variant": "data_driven",
    },
    "health": {
        "name": "医疗/健康",
        "core_sources": ["pubmed.ncbi.nlm.nih.gov", "nature.com", "who.int"],
        "keywords": ["医疗", "健康", "疾病", "药物", "治疗", "疫苗", "临床", "medical", "health", "disease", "treatment"],
        "prompt_variant": "evidence_based",
    },
    "general": {
        "name": "综合",
        "core_sources": [],
        "keywords": [],
        "prompt_variant": "general",
    },
}


# === Quality Enhancement Modules ===
class FixedChannelSearch:
    """固定渠道搜索引擎"""

    def __init__(self, tool_client):
        self.tools = tool_client

    async def search_with_channels(self, query: str, domain: str = None) -> list[dict]:
        """
        按优先级搜索固定渠道
        1. 先搜索核心信源 (L1)
        2. 结果不足时搜索扩展信源 (L2)
        3. 最后用通用搜索兜底 (L3)
        """
        results = []

        # Phase 1: 核心信源
        for source_name, source_config in CORE_SOURCES.items():
            source_query = source_config["search_template"].format(query=query)
            source_results = await self.tools.google_search(source_query, num_results=5)
            results.extend([
                {**r, "source_tier": "L1", "source_name": source_config["name"], "source_category": source_name}
                for r in source_results
            ])

        # 如果核心信源结果不足，用通用搜索补充
        if len(results) < 10:
            general_results = await self.tools.google_search(query, num_results=10)
            results.extend([
                {**r, "source_tier": "L3", "source_name": "通用搜索", "source_category": "general"}
                for r in general_results
            ])

        return results


class SourceCredibilityScorer:
    """信源可信度评分器"""

    def __init__(self):
        # 预定义信源权重
        self.source_weights = {
            "nature.com": 0.95,
            "science.org": 0.95,
            "arxiv.org": 0.85,
            "reuters.com": 0.90,
            "apnews.com": 0.90,
            "bbc.com": 0.85,
            "github.com": 0.80,
            "wikipedia.org": 0.70,
            "stackoverflow.com": 0.75,
            "medium.com": 0.50,
            "zhihu.com": 0.45,
            "worldbank.org": 0.90,
            "imf.org": 0.90,
            "pubmed.ncbi.nlm.nih.gov": 0.95,
        }

    def score(self, url: str, content: str, metadata: dict = None) -> dict:
        """综合评分信源可信度"""
        domain = self._extract_domain(url)

        # 1. 基础权重
        base_weight = self.source_weights.get(domain, 0.50)

        # 2. 内容质量评分
        content_score = self._evaluate_content(content)

        # 3. 时效性评分
        recency_score = self._evaluate_recency(metadata)

        # 4. 引用完整性
        citation_score = self._evaluate_citations(content)

        # 综合评分
        final_score = (
            base_weight * 0.4 +
            content_score * 0.3 +
            recency_score * 0.15 +
            citation_score * 0.15
        )

        return {
            "score": round(final_score, 3),
            "level": self._score_to_level(final_score),
            "breakdown": {
                "base_weight": round(base_weight, 3),
                "content_score": round(content_score, 3),
                "recency_score": round(recency_score, 3),
                "citation_score": round(citation_score, 3),
            }
        }

    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        match = re.search(r'://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url

    def _evaluate_content(self, content: str) -> float:
        """评估内容质量"""
        score = 0.5

        # 有数据支撑
        has_data = bool(re.search(r'\d+[\.,]\d+|%|\$', content))
        if has_data:
            score += 0.15

        # 有引用
        has_citations = bool(re.search(r'\[\d+\]|\(.*?et al\.|according to', content, re.I))
        if has_citations:
            score += 0.15

        # 长度适中
        word_count = len(content.split())
        if 200 < word_count < 3000:
            score += 0.1

        # 有明确作者/机构
        has_author = bool(re.search(r'by \w+|authored by|published by', content, re.I))
        if has_author:
            score += 0.1

        return min(score, 1.0)

    def _evaluate_recency(self, metadata: dict) -> float:
        """评估时效性"""
        if not metadata or "date" not in metadata:
            return 0.5

        try:
            date = datetime.fromisoformat(metadata["date"])
            days_old = (datetime.now() - date).days

            if days_old < 30:
                return 1.0
            elif days_old < 365:
                return 0.8
            elif days_old < 3 * 365:
                return 0.6
            else:
                return 0.3
        except:
            return 0.5

    def _evaluate_citations(self, content: str) -> float:
        """评估引用完整性"""
        score = 0.5
        citation_count = len(re.findall(r'\[\d+\]|http[s]?://', content))

        if citation_count > 5:
            score += 0.3
        elif citation_count > 2:
            score += 0.15

        return min(score, 1.0)

    def _score_to_level(self, score: float) -> str:
        """评分转等级"""
        if score >= 0.85:
            return "A (权威)"
        elif score >= 0.70:
            return "B (可靠)"
        elif score >= 0.50:
            return "C (一般)"
        else:
            return "D (谨慎)"


class ContradictionDetector:
    """矛盾检测器"""

    def detect(self, claims: list[dict]) -> list[dict]:
        """检测多个主张之间的矛盾"""
        contradictions = []

        # 按主题分组
        topics = self._group_by_topic(claims)

        for topic, topic_claims in topics.items():
            if len(topic_claims) < 2:
                continue

            # 检测数值矛盾
            numeric_conflicts = self._detect_numeric_conflicts(topic_claims)
            if numeric_conflicts:
                contradictions.append({
                    "topic": topic,
                    "type": "numeric_conflict",
                    "details": numeric_conflicts,
                    "resolution": "需人工判断或寻找第三方来源验证"
                })

            # 检测定性矛盾
            qualitative_conflicts = self._detect_qualitative_conflicts(topic_claims)
            if qualitative_conflicts:
                contradictions.append({
                    "topic": topic,
                    "type": "qualitative_conflict",
                    "details": qualitative_conflicts,
                    "resolution": "报告中需明确说明矛盾双方观点"
                })

        return contradictions

    def _group_by_topic(self, claims: list[dict]) -> dict:
        """按主题分组主张"""
        topics = {}
        for claim in claims:
            topic = claim.get("topic", "general")
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(claim)
        return topics

    def _detect_numeric_conflicts(self, claims: list[dict]) -> list[dict]:
        """检测数值矛盾"""
        conflicts = []
        numbers = []

        for claim in claims:
            nums = re.findall(r'(\d+(?:\.\d+)?)\s*(%|million|billion|万|亿)?', claim.get("text", ""))
            for num, unit in nums:
                numbers.append({
                    "value": float(num),
                    "unit": unit,
                    "source": claim.get("source", ""),
                    "credibility": claim.get("credibility_score", 0)
                })

        # 相同单位但数值差异 > 20%
        for i, n1 in enumerate(numbers):
            for n2 in numbers[i+1:]:
                if n1["unit"] == n2["unit"] and n1["value"] > 0:
                    diff = abs(n1["value"] - n2["value"]) / n1["value"]
                    if diff > 0.20:
                        conflicts.append({
                            "claim1": n1,
                            "claim2": n2,
                            "difference": f"{diff:.0%}"
                        })

        return conflicts

    def _detect_qualitative_conflicts(self, claims: list[dict]) -> list[dict]:
        """检测定性矛盾"""
        conflicts = []

        # 简单的对立词检测
        oppositions = [
            ("increase", "decrease"),
            ("rise", "fall"),
            ("positive", "negative"),
            ("支持", "反对"),
            ("增长", "下降"),
            ("优点", "缺点"),
        ]

        for i, c1 in enumerate(claims):
            for c2 in claims[i+1:]:
                text1 = c1.get("text", "").lower()
                text2 = c2.get("text", "").lower()

                for word1, word2 in oppositions:
                    if (word1.lower() in text1 and word2.lower() in text2) or \
                       (word2.lower() in text1 and word1.lower() in text2):
                        conflicts.append({
                            "claim1": c1.get("source", ""),
                            "claim2": c2.get("source", ""),
                            "opposition": (word1, word2)
                        })
                        break

        return conflicts


class QualityCheckPipeline:
    """研究结果质量检查流水线"""

    def __init__(self):
        self.checks = [
            self._check_source_count,
            self._check_citation_completeness,
            self._check_data_support,
            self._check_contradictions,
            self._check_structure,
            self._check_language_quality,
        ]

    def run(self, result: str, metadata: dict) -> dict:
        """运行所有质量检查"""
        issues = []
        scores = {}

        for check in self.checks:
            check_result = check(result, metadata)
            issues.extend(check_result.get("issues", []))
            scores[check.__name__] = check_result.get("score", 0)

        overall_score = sum(scores.values()) / len(scores) if scores else 0

        return {
            "overall_score": round(overall_score, 3),
            "passed": overall_score >= 0.70,
            "scores": scores,
            "issues": issues,
            "recommendation": self._get_recommendation(overall_score),
        }

    def _check_source_count(self, result: str, metadata: dict) -> dict:
        """检查引用来源数量"""
        url_count = result.count("http")
        score = min(url_count / 10, 1.0)
        issues = []
        if url_count < 5:
            issues.append(f"引用来源过少 ({url_count}个)，建议至少 10 个")
        return {"score": score, "issues": issues}

    def _check_citation_completeness(self, result: str, metadata: dict) -> dict:
        """检查引用完整性"""
        complete_citations = len(re.findall(r'http.*?\d{4}', result))
        total_citations = result.count("http")
        completeness = complete_citations / max(total_citations, 1)
        issues = []
        if completeness < 0.5:
            issues.append(f"引用不完整，{int((1-completeness)*100)}% 的引用缺少日期信息")
        return {"score": completeness, "issues": issues}

    def _check_data_support(self, result: str, metadata: dict) -> dict:
        """检查数据支撑"""
        has_data = bool(re.search(r'\d+[\.,]\d+|%|\$', result))
        data_density = len(re.findall(r'\d+', result)) / max(len(result.split()), 1)
        score = min(data_density * 100, 1.0) if has_data else 0.3
        issues = []
        if not has_data:
            issues.append("缺少数据支撑，多为定性描述")
        return {"score": score, "issues": issues}

    def _check_contradictions(self, result: str, metadata: dict) -> dict:
        """检查矛盾处理"""
        has_contradictions_section = "矛盾" in result or "contradiction" in result.lower()
        has_debate_section = "debate" in result.lower() or "分歧" in result
        score = 0.7 if (has_contradictions_section or has_debate_section) else 0.4
        issues = []
        if not has_contradictions_section and not has_debate_section:
            issues.append("未明确标注来源之间的矛盾")
        return {"score": score, "issues": issues}

    def _check_structure(self, result: str, metadata: dict) -> dict:
        """检查结构完整性"""
        required_sections = ["summary", "finding", "source"]
        present = [s for s in required_sections if s in result.lower()]
        score = len(present) / len(required_sections)
        missing = [s for s in required_sections if s not in result.lower()]
        issues = [f"缺少必要章节: {', '.join(missing)}"] if missing else []
        return {"score": score, "issues": issues}

    def _check_language_quality(self, result: str, metadata: dict) -> dict:
        """检查语言质量"""
        sentences = re.split(r'[.!?。！？]', result)
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        has_transitions = bool(re.search(r'however|therefore|moreover|然而|因此|此外', result, re.I))
        score = 0.6
        if 10 < avg_length < 30:
            score += 0.2
        if has_transitions:
            score += 0.2
        return {"score": min(score, 1.0), "issues": []}

    def _get_recommendation(self, score: float) -> str:
        if score >= 0.85:
            return "质量优秀，可直接交付"
        elif score >= 0.70:
            return "质量良好，建议人工复核"
        elif score >= 0.50:
            return "质量一般，建议重新研究或大幅修改"
        else:
            return "质量较差，建议重新执行研究流程"


def detect_domain(query: str) -> str:
    """自动识别查询领域"""
    score = {"tech": 0, "finance": 0, "health": 0}

    for kw in DOMAIN_CONFIGS["tech"]["keywords"]:
        if kw.lower() in query.lower():
            score["tech"] += 1
    for kw in DOMAIN_CONFIGS["finance"]["keywords"]:
        if kw.lower() in query.lower():
            score["finance"] += 1
    for kw in DOMAIN_CONFIGS["health"]["keywords"]:
        if kw.lower() in query.lower():
            score["health"] += 1

    max_domain = max(score, key=score.get)
    return max_domain if score[max_domain] > 0 else "general"

# === App Setup ===
app = FastAPI(title="MiroThinker Online Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# === Task Storage ===
task_results: dict = {}

# === Concurrency Control (适配 2核2G) ===
# 限制同时进行的研究任务数量，避免内存溢出
research_semaphore = asyncio.Semaphore(2)  # 最多 2 个并发任务


# === Request/Response Models ===
class ResearchRequest(BaseModel):
    query: str
    max_turns: int = 200
    context_keep: int = 5
    model: str = "qwen-plus"
    temperature: float = 0.7


class TaskResponse(BaseModel):
    task_id: str
    status: str = "running"
    turn_count: int = 0
    elapsed_time: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None
    domain: Optional[str] = None
    quality_report: Optional[dict] = None
    metadata: Optional[dict] = None


# === MCP Tool Clients ===
class ToolClient:
    """自研搜索和抓取 - 零成本方案 (DuckDuckGo + Trafilatura)"""

    def __init__(self):
        # 不再需要 API keys，使用免费开源库
        pass

    async def google_search(self, query: str, num_results: int = 10) -> list[dict]:
        """使用 DuckDuckGo 免费搜索"""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=min(num_results, 5))]
            
            return [{
                "title": r.get("title", ""),
                "link": r.get("href", ""),
                "snippet": r.get("body", "")[:150]
            } for r in results]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    async def scrape_webpage(self, url: str) -> str:
        """使用 Trafilatura 轻量抓取"""
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded, include_comments=False)
                return (content or "")[:800]
            return f"Failed to fetch {url}"
        except Exception as e:
            return f"Scrape failed: {str(e)}"


# === Agent Core ===
class AgentState:
    """Maintains agent conversation state - OPTIMIZED for token efficiency."""

    def __init__(self, system_prompt: str, model: str, temperature: float):
        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]
        self.model = MODEL_MAP.get(model, "qwen-plus")
        self.temperature = temperature
        self.turn_count = 0
        self.tool_calls: list[dict] = []
        # OPTIMIZED: Track summarized history
        self.tool_summaries: list[str] = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        
        # OPTIMIZED: Keep compact summary of tool results
        if role == "tool":
            # Extract just the first 100 chars as summary
            summary = content[:100].replace('\n', ' ')
            self.tool_summaries.append(summary)

    def get_context_window(self, context_keep: int) -> list[dict]:
        """Return OPTIMIZED context window - reduces tokens by ~40%."""
        if context_keep <= 0:
            return self.messages

        # Always keep system prompt + user query
        base = [self.messages[0]]  # system prompt

        # Find user query
        for msg in self.messages[1:]:
            if msg["role"] == "user" and len(base) == 1:
                base.append(msg)
                break

        # OPTIMIZED: Keep last K assistant/tool exchanges, but compress tool results
        recent = []
        tool_results = [m for m in self.messages if m.get("role") in ("assistant", "tool")]

        if context_keep > 0 and len(tool_results) > context_keep:
            tool_results = tool_results[-context_keep:]
            # OPTIMIZED: Compress tool messages to first 500 chars
            for msg in tool_results:
                if msg["role"] == "tool" and len(msg["content"]) > 500:
                    compressed = msg["content"][:500] + "\n...(truncated)"
                    recent.append({"role": msg["role"], "content": compressed})
                else:
                    recent.append(msg)
        else:
            recent = tool_results

        return base + recent

    def get_recent_tool_results(self, context_keep: int) -> list[dict]:
        """Get recent tool results for context display."""
        tool_msgs = [m for m in self.messages if m.get("role") == "tool"]
        if context_keep > 0 and len(tool_msgs) > context_keep:
            return tool_msgs[-context_keep:]
        return tool_msgs


def build_system_prompt(max_turns: int, domain: str = "general") -> str:
    """Build OPTIMIZED system prompt - reduced from ~800 to ~250 tokens."""
    
    # Ultra-compact domain instructions
    domain_extras = {
        "tech": "Focus on: code examples, official docs, version compatibility, alternatives comparison.",
        "finance": "Focus on: data with dates, official sources, nominal vs real values, historical context.",
        "health": "Focus on: peer-reviewed studies only, correlation≠causation, sample sizes, evidence levels.",
        "general": ""
    }
    
    extra = domain_extras.get(domain, "")
    extra = f"\n{extra}" if extra else ""
    
    return f"""You are MiroThinker, a deep research agent.

## Tools
1. google_search(query) - Search web, returns title/link/snippet
2. scrape_webpage(url) - Extract webpage content as markdown

## Process
1. Break question into sub-questions
2. Search broadly, then scrape key pages
3. Cross-reference sources, note contradictions
4. Synthesize comprehensive report

## Rules
- Max {max_turns} turns
- Cite sources with URLs and dates
- Respond with "FINAL ANSWER:" when done
- Prioritize authoritative sources
- Consider multiple perspectives{extra}

## Output Format
# [Title]
## Executive Summary
## Research Findings (with citations)
## Analysis
## Contradictions & Debates
## Conclusion
## Sources (URLs with dates)
"""


# === Tier Routing ===
async def classify_query(query: str) -> str:
    """
    使用 qwen-flash 快速分类查询为三个 Tier
    TIER_1: 简单事实型 (直答，~50 Credits)
    TIER_2: 中等分析 (Phase 1+2, ~500 Credits)
    TIER_3: 深度研究 (完整三阶段, ~600 Credits)
    """
    routing_prompt = f"""Classify this query into one of three tiers:

TIER_1 (Simple): Factual question, can be answered directly
Examples: "What is Python?", "Who invented the telephone?"

TIER_2 (Medium): Requires some research, but straightforward
Examples: "Compare Python vs Rust", "What are the benefits of solar energy?"

TIER_3 (Complex): Deep research needed, multiple sources, analysis
Examples: "Analyze the economic impact of AI on healthcare by 2030", "Deep dive into optical module industry"

Query: {query}
Return only: TIER_1, TIER_2, or TIER_3"""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{DASHSCOPE_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-flash",  # 使用最便宜的模型
                    "messages": [{"role": "user", "content": routing_prompt}],
                    "temperature": 0.1,
                    "max_tokens": 20,
                },
                timeout=30,
            )
            
            if resp.status_code == 200:
                data = resp.json()
                classification = data["choices"][0]["message"]["content"].strip()
                if classification in ["TIER_1", "TIER_2", "TIER_3"]:
                    return classification
            
            # 默认返回 TIER_2 (保守策略)
            return "TIER_2"
    except:
        return "TIER_2"  # 出错时默认中等研究


class ResearchAgent:
    """Core research agent implementation with quality enhancement."""

    def __init__(self, enable_quality_enhancement: bool = True):
        self.tools = ToolClient()
        self.enable_quality = enable_quality_enhancement
        
        # Initialize quality modules
        if self.enable_quality:
            self.channel_search = FixedChannelSearch(self.tools)
            self.credibility_scorer = SourceCredibilityScorer()
            self.contradiction_detector = ContradictionDetector()
            self.quality_pipeline = QualityCheckPipeline()

    async def call_llm(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
    ) -> dict:
        """Call DashScope API."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{DASHSCOPE_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=120,
            )

            if resp.status_code != 200:
                raise Exception(f"LLM API error: {resp.status_code} - {resp.text}")

            data = resp.json()
            return data["choices"][0]["message"]

    async def run(
        self,
        query: str,
        max_turns: int = 200,
        context_keep: int = 5,
        model: str = "qwen-plus",
        temperature: float = 0.7,
        tier: str = None,  # 新增: Tier 参数
    ) -> dict:
        """Run the research agent with quality enhancement and Tier routing."""
        start_time = time.time()
        
        # Tier 路由：如果未指定，自动分类
        if tier is None:
            tier = await classify_query(query)
        
        # 根据 Tier 调整 max_turns
        if tier == "TIER_1":
            max_turns = min(max_turns, 5)  # 简单问题最多 5 轮
        elif tier == "TIER_2":
            max_turns = min(max_turns, 50)  # 中等研究最多 50 轮
        else:  # TIER_3
            max_turns = min(max_turns, 125)  # 深度研究最多 125 轮
        
        # Detect domain for targeted research
        domain = detect_domain(query) if self.enable_quality else "general"
        
        # Build enhanced system prompt with domain-specific instructions
        system_prompt = build_system_prompt(max_turns, domain)
        agent_state = AgentState(system_prompt, model, temperature)
        agent_state.add_message("user", query)
        
        # Track research metadata for quality checking
        research_metadata = {
            "query": query,
            "domain": domain,
            "sources": [],
            "claims": [],
        }

        turn = 0
        consecutive_no_tool = 0  # 智能早停：连续无工具调用计数
        source_saturation = False  # 智能早停：信息饱和标志
        
        while turn < max_turns:
            turn += 1
            agent_state.turn_count = turn

            # Get context window
            context = agent_state.get_context_window(context_keep)

            # Call LLM
            message = await self.call_llm(context, agent_state.model, agent_state.temperature)
            content = message.get("content", "") or ""
            agent_state.add_message("assistant", content)

            # Check for FINAL ANSWER
            if "FINAL ANSWER:" in content:
                result = content.split("FINAL ANSWER:", 1)[1].strip()
                
                # Run quality checks if enabled
                quality_report = None
                if self.enable_quality:
                    quality_report = self.quality_pipeline.run(result, research_metadata)
                    
                    # Detect contradictions in claims
                    contradictions = self.contradiction_detector.detect(research_metadata["claims"])
                
                return {
                    "result": result,
                    "turn_count": turn,
                    "elapsed_time": round(time.time() - start_time, 2),
                    "domain": domain,
                    "quality_report": quality_report,
                    "metadata": research_metadata,
                    "tier": tier,
                }

            # Check for tool calls (look for function call patterns)
            tool_results = await self._execute_tools(content)

            if tool_results:
                consecutive_no_tool = 0  # 重置早停计数器
                for tool_name, query_input, output in tool_results:
                    agent_state.tool_calls.append({
                        "tool": tool_name,
                        "input": query_input,
                        "output_len": len(str(output))[:100],
                    })
                    # OPTIMIZED: Reduce from 3000 to 1000 chars in context
                    agent_state.add_message(
                        "tool",
                        f"{tool_name}('{query_input}'):\n{output[:1000]}"
                    )
                    
                    # Extract and score sources for quality tracking
                    if tool_name == "google_search" and self.enable_quality:
                        try:
                            # OPTIMIZED: Parse compact format or JSON
                            if output.startswith("[") or output.startswith("{"):
                                search_results = json.loads(output)
                            else:
                                # Parse compact text format
                                search_results = self._parse_compact_results(output)
                            
                            for item in search_results:
                                if "link" in item or "url" in item:
                                    url = item.get("link") or item.get("url", "")
                                    title = item.get("title", "")
                                    snippet = item.get("snippet", "")
                                    score = self.credibility_scorer.score(
                                        url, 
                                        snippet,
                                        {"date": None}
                                    )
                                    research_metadata["sources"].append({
                                        "url": url,
                                        "title": title,
                                        "credibility_score": score["score"],
                                        "credibility_level": score["level"],
                                    })
                        except:
                            pass
                
                # 智能早停：检查信息饱和
                if self.enable_quality and len(research_metadata["sources"]) >= 25:
                    # 已有足够信源，提示 LLM 总结
                    agent_state.add_message(
                        "user",
                        "Information saturated. Synthesize findings into FINAL ANSWER:"
                    )
                    source_saturation = True
            else:
                consecutive_no_tool += 1
                
                # 智能早停：连续 3 轮无工具调用 → 信息已充分
                if consecutive_no_tool >= 3:
                    agent_state.add_message(
                        "user",
                        "No new tools called. Provide FINAL ANSWER based on current findings:"
                    )
                
                # Check if agent is stuck or not making progress
                if not tool_results and "FINAL ANSWER:" not in content and consecutive_no_tool < 3:
                    # OPTIMIZED: Shorter prompt
                    agent_state.add_message(
                        "user",
                        "Continue researching or provide FINAL ANSWER:"
                    )

        # If max turns reached without final answer
        # Ask for synthesis
        agent_state.add_message(
            "user",
            "Max turns reached. Synthesize findings into FINAL ANSWER:"
        )

        synthesis = await self.call_llm(
            agent_state.get_context_window(context_keep),
            agent_state.model,
            agent_state.temperature,
        )
        result = synthesis.get("content", "")
        
        # Run quality checks
        quality_report = None
        if self.enable_quality:
            quality_report = self.quality_pipeline.run(result, research_metadata)
            contradictions = self.contradiction_detector.detect(research_metadata["claims"])

        return {
            "result": result,
            "turn_count": turn,
            "elapsed_time": round(time.time() - start_time, 2),
            "domain": domain,
            "quality_report": quality_report,
            "metadata": research_metadata,
            "tier": tier,
        }

    async def _execute_tools(self, content: str) -> list[tuple]:
        """Parse content for tool calls and execute them - OPTIMIZED for token efficiency."""
        results = []

        # Parse google_search calls
        search_pattern = r'google_search\(["\'](.+?)["\']\)'
        for match in re.finditer(search_pattern, content):
            query = match.group(1)
            try:
                output = await self.tools.google_search(query)
                # OPTIMIZED: Use compact text format instead of JSON
                output_str = self._format_search_compact(output, max_results=5)
                results.append(("google_search", query, output_str))
            except Exception as e:
                results.append(("google_search", query, f"Error: {str(e)}"))

        # Parse scrape_webpage calls
        scrape_pattern = r'scrape_webpage\(["\'](.+?)["\']\)'
        for match in re.finditer(scrape_pattern, content):
            url = match.group(1)
            try:
                output = await self.tools.scrape_webpage(url)
                # OPTIMIZED: Reduce from 3000 to 1500 chars
                results.append(("scrape_webpage", url, output[:1500]))
            except Exception as e:
                results.append(("scrape_webpage", url, f"Error: {str(e)}"))

        return results

    def _format_search_compact(self, results: list[dict], max_results: int = 5) -> str:
        """Format search results in compact text - saves ~50% tokens vs JSON."""
        lines = []
        for i, r in enumerate(results[:max_results], 1):
            title = r.get('title', '')[:80]
            snippet = r.get('snippet', '')[:100]
            link = r.get('link', '')
            lines.append(f"{i}. [{title}] {link}")
            if snippet:
                lines.append(f"   {snippet}")
        return "\n".join(lines) if lines else "No results found."
    
    def _parse_compact_results(self, text: str) -> list[dict]:
        """Parse compact search results back to dict format."""
        results = []
        lines = text.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Match pattern: "1. [Title] URL"
            match = re.match(r'\d+\.\s*\[(.+?)\]\s*(https?://\S+)', line)
            if match:
                title = match.group(1)
                url = match.group(2)
                snippet = ""
                # Next line might be snippet
                if i + 1 < len(lines) and lines[i+1].strip().startswith("   "):
                    snippet = lines[i+1].strip()[3:]
                    i += 1
                results.append({
                    "title": title,
                    "link": url,
                    "snippet": snippet
                })
            i += 1
        return results if results else []


# === API Routes ===
@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")


@app.post("/api/research", response_model=TaskResponse)
async def create_research_task(req: ResearchRequest):
    """Create a new research task."""
    task_id = str(uuid.uuid4())[:8]
    task_results[task_id] = {
        "status": "running",
        "turn_count": 0,
        "elapsed_time": 0.0,
        "result": None,
        "error": None,
        "start_time": time.time(),
    }

    # Run research in background
    asyncio.create_task(_run_research(task_id, req))

    return TaskResponse(task_id=task_id)


@app.get("/api/research/{task_id}", response_model=TaskResponse)
async def get_research_status(task_id: str):
    """Get research task status."""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_results[task_id]

    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        turn_count=task.get("turn_count", 0),
        elapsed_time=round(time.time() - task["start_time"], 2) if task["start_time"] else 0,
        result=task["result"],
        error=task["error"],
        domain=task.get("domain"),
        quality_report=task.get("quality_report"),
        metadata=task.get("metadata"),
    )


async def _run_research(task_id: str, req: ResearchRequest):
    """Background task to run research with concurrency control and Tier routing."""
    async with research_semaphore:
        # 更新状态为排队中（如果信号量已满）
        if research_semaphore.locked():
            task_results[task_id]["status"] = "queued"
        
        try:
            if not DASHSCOPE_API_KEY:
                raise ValueError("DASHSCOPE_API_KEY not configured")

            # Tier 路由：先分类查询
            tier = await classify_query(req.query)
            task_results[task_id]["tier"] = tier
            
            # Enable quality enhancement by default
            agent = ResearchAgent(enable_quality_enhancement=True)
            result = await agent.run(
                query=req.query,
                max_turns=req.max_turns,
                context_keep=req.context_keep,
                model=req.model,
                temperature=req.temperature,
                tier=tier,  # 传入 Tier 参数
            )

            task_results[task_id].update({
                "status": "completed",
                "turn_count": result["turn_count"],
                "elapsed_time": result["elapsed_time"],
                "result": result["result"],
                "domain": result.get("domain", "general"),
                "quality_report": result.get("quality_report"),
                "metadata": result.get("metadata"),
            })

        except Exception as e:
            task_results[task_id].update({
                "status": "failed",
                "error": str(e),
            })


# === Health Check ===
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "dashscope_configured": bool(DASHSCOPE_API_KEY),
        "search_available": True,  # DuckDuckGo 免费，无需 API Key
        "scrape_available": True,  # Trafilatura 免费，无需 API Key
        "serper_configured": bool(SERPER_API_KEY),  # 可选，向后兼容
        "jina_configured": bool(JINA_API_KEY),      # 可选，向后兼容
        "concurrency": {
            "max": 2,
            "available": research_semaphore._value,
            "locked": research_semaphore.locked(),
        },
    }


# === System Status ===
@app.get("/api/status")
async def system_status():
    """Get detailed system status including resource usage."""
    import os
    
    # Get process memory info
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = {
            "rss_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "vms_mb": round(process.memory_info().vms / 1024 / 1024, 2),
        }
    except ImportError:
        memory_info = {"note": "psutil not installed, install with: pip install psutil"}
    
    return {
        "service": "MiroThinker Online Service",
        "version": "2.0",
        "memory": memory_info,
        "concurrency": {
            "max_concurrent_tasks": 2,
            "current_running": 2 - research_semaphore._value,
            "available_slots": research_semaphore._value,
        },
        "tasks": {
            "total": len(task_results),
            "running": sum(1 for t in task_results.values() if t["status"] == "running"),
            "completed": sum(1 for t in task_results.values() if t["status"] == "completed"),
            "failed": sum(1 for t in task_results.values() if t["status"] == "failed"),
        },
    }


# === Entrypoint ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
