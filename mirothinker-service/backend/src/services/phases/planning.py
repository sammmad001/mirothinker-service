"""
MiroThinker - Planning Phase

Analyzes the query, identifies 2-4 main threads, forms initial hypotheses,
and creates a ResearchPlan that guides the Deep Analysis phase.

Uses qwen3.6-plus for strong reasoning capability.
"""

import json
import re
from dataclasses import dataclass, field

from src.core.config import settings
from src.core.logging_config import logger
from src.services.research_memory import MainThread


@dataclass
class ResearchPlan:
    """Output of the Planning phase — guides the entire research process.

    Analysis methodology is DYNAMIC per main thread (not fixed per domain).
    The LLM decides the appropriate analytical framework based on the
    specific question content, not a rigid domain template.
    """
    main_threads: list[dict]          # [{title, target_depth, search_keywords}]
    hypotheses: list[dict]            # [{statement, priority}]
    search_strategy: dict[str, list[str]]  # thread_title → search keywords
    depth_targets: dict[str, int]     # thread_title → target depth level
    thread_methodologies: dict[str, str] = None  # thread_title → analysis methodology


class PlanningPhase:
    """Plan research: identify main threads and form initial hypotheses."""

    PLANNING_PROMPT = """你是研究规划师。分析以下研究问题，制定研究计划。

## 研究问题
{query}

## 领域信息
- 领域: {domain}
- 子类型: {subtype}

## 预搜索结果
{pre_search_summary}

## 规划要求

请制定研究计划，输出JSON格式：

1. 识别2-4条主线议题（根据问题内容自然产生，不要套用固定框架）
2. 每条主线设定目标深度（L3=根因 或 L4=系统理解）
3. 为每条主线生成3-5个搜索关键词
4. 为每条主线定义专属分析方法论（根据该主线的内容特点决定）
5. 提出2-3个初始假设

```json
{{
  "main_threads": [
    {{
      "title": "主线议题名称",
      "target_depth": 3,
      "search_keywords": ["关键词1", "关键词2", "关键词3"],
      "analysis_methodology": "该主线的专属分析方法论。示例：'从财务数据→业务驱动因素→行业竞争格局→估值合理性' 或 '从政策文本→利益相关方分析→执行可行性→实际影响评估'。必须根据该主线的具体内容特点来定义，不可泛泛而谈。"
    }}
  ],
  "hypotheses": [
    {{
      "statement": "初始假设陈述",
      "priority": "high"
    }}
  ]
}}
```

注意：
1. 主线议题和分析方法论都应根据问题内容自然产生，不要机械套用固定框架
2. target_depth: 一般话题用3(根因)，系统性话题用4(系统理解)
3. 搜索关键词要具体，包含中英文关键词
4. 假设应可验证，不是模糊的猜测
5. analysis_methodology 必须针对该主线的具体内容，不能写成通用方法论"""

    async def execute(
        self,
        query: str,
        domain: str,
        subtype: str,
        pre_search_results: list[dict],
    ) -> ResearchPlan:
        """Execute planning phase.

        Args:
            query: Original research query
            domain: Research domain (finance/tech/health/general)
            subtype: Entity subtype from classification
            pre_search_results: Pre-search results for context

        Returns:
            ResearchPlan with main threads, hypotheses, and search strategy
        """
        import httpx

        # Format pre-search summary
        pre_search_summary = self._format_pre_search(pre_search_results)

        # === METHODOLOGY ENRICHMENT: Retrieve similar historical sessions ===
        historical_methodologies = self._get_historical_methodologies(query, domain)

        # Build enriched prompt with historical reference
        prompt = self.PLANNING_PROMPT.format(
            query=query,
            domain=domain,
            subtype=subtype or "未指定",
            pre_search_summary=pre_search_summary,
        )

        if historical_methodologies:
            prompt += f"\n\n## 历史相似问题的方法论参考（供灵感，不要照搬）\n{historical_methodologies}\n"
            prompt += "\n注意：以上仅为历史参考，你应根据当前问题的具体内容自主决定分析方法论。"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "qwen3.6-plus",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 2048,
                    },
                    timeout=60,
                )

                if resp.status_code != 200:
                    logger.warning(f"PlanningPhase API error: {resp.status_code}")
                    return self._default_plan(query)

                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON response
                parsed = self._parse_json_response(content)
                plan = self._build_plan(parsed)

                logger.info(f"PlanningPhase: {len(plan.main_threads)} threads, "
                          f"{len(plan.hypotheses)} hypotheses")

                return plan

        except Exception as e:
            logger.warning(f"PlanningPhase failed: {e}")
            return self._default_plan(query)

    def _format_pre_search(self, results: list[dict]) -> str:
        """Format pre-search results for planning prompt."""
        if not results:
            return "无预搜索结果"

        lines = []
        for r in results[:8]:
            title = r.get("title", "")[:60]
            snippet = r.get("snippet", "")[:100]
            if snippet:
                lines.append(f"- {title}: {snippet}")
            else:
                lines.append(f"- {title}")

        return "\n".join(lines)

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from LLM response."""
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        return {}

    def _build_plan(self, parsed: dict) -> ResearchPlan:
        """Build ResearchPlan from parsed JSON."""
        main_threads = parsed.get("main_threads", [])
        hypotheses = parsed.get("hypotheses", [])

        # Build mappings: search_strategy, depth_targets, thread_methodologies
        search_strategy = {}
        depth_targets = {}
        thread_methodologies = {}
        for mt in main_threads:
            title = mt.get("title", "未知主线")
            search_strategy[title] = mt.get("search_keywords", [])
            depth_targets[title] = min(max(mt.get("target_depth", 3), 2), 4)
            # Dynamic analysis methodology per thread (not per domain)
            methodology = mt.get("analysis_methodology", "").strip()
            if methodology:
                thread_methodologies[title] = methodology

        # Validate: at least 1 main thread
        if not main_threads:
            main_threads = [{"title": "综合分析", "target_depth": 3, "search_keywords": []}]
            search_strategy = {"综合分析": []}
            depth_targets = {"综合分析": 3}
            thread_methodologies = {"综合分析": "从现象描述→直接原因→根本原因→系统影响的逐层推导"}

        return ResearchPlan(
            main_threads=main_threads,
            hypotheses=hypotheses,
            search_strategy=search_strategy,
            depth_targets=depth_targets,
            thread_methodologies=thread_methodologies if thread_methodologies else None,
        )

    def _default_plan(self, query: str) -> ResearchPlan:
        """Generate a default plan when planning fails."""
        title = f"关于{query[:20]}的综合分析"
        return ResearchPlan(
            main_threads=[{
                "title": title,
                "target_depth": 3,
                "search_keywords": [query],
            }],
            hypotheses=[{
                "statement": f"{query}存在值得深入分析的关键议题",
                "priority": "medium",
            }],
            search_strategy={title: [query]},
            depth_targets={title: 3},
            thread_methodologies={title: "从现象描述→直接原因→根本原因→系统影响的逐层推导"},
        )

    def _get_historical_methodologies(self, query: str, domain: str) -> str:
        """Retrieve methodology patterns from similar historical sessions.

        This is the core of "methodology enrichment" — learning from past
        analysis approaches to improve new ones.
        """
        try:
            from src.core.session_store import find_similar_sessions, get_methodology_patterns

            # 1. Find similar sessions by query keywords
            keywords = [w for w in query.replace("的", " ").replace("是", " ").split()
                       if len(w) > 1][:5]
            similar = find_similar_sessions(keywords, domain=domain, limit=3)

            # 2. Get top methodology patterns for this domain
            patterns = get_methodology_patterns(domain=domain, min_usage=1, limit=5)

            parts = []

            if similar:
                parts.append("### 历史相似问题的分析框架")
                for i, s in enumerate(similar[:3], 1):
                    snap = s.get("snapshot", {})
                    meths = snap.get("thread_methodologies", {})
                    if meths:
                        parts.append(f"{i}. **{s.get('query', '未知问题')[:40]}**")
                        for title, meth in list(meths.items())[:2]:
                            parts.append(f"   - {title}: {meth[:80]}")

            if patterns:
                parts.append("\n### 该领域高频使用的方法论模式")
                for i, p in enumerate(patterns[:5], 1):
                    parts.append(f"{i}. **{p.get('thread_title', '未命名')}** (使用{p.get('usage_count', 0)}次, 深度分{p.get('avg_depth_score', 0):.2f})")
                    parts.append(f"   {p.get('methodology', '')[:100]}")

            return "\n".join(parts) if parts else ""

        except Exception as e:
            logger.debug(f"Historical methodology retrieval failed: {e}")
            return ""
