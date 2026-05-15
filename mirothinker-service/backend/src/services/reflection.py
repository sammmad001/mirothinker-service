"""
MiroThinker - Reflection Node

Evaluates research depth and direction every N turns.
Uses qwen-flash (cheap, fast) to assess whether analysis is deep enough
and whether the search strategy needs adjustment.
"""

import json
import re
from dataclasses import dataclass, field

from src.core.config import settings
from src.core.logging_config import logger
from src.services.research_memory import ResearchMemory


@dataclass
class ReflectionReport:
    """Report from reflection evaluation."""
    depth_assessment: dict[str, dict]   # thread_id → {current_depth, target_depth, sufficient}
    gaps: list[str]                     # Logic gap descriptions
    adjustments: list[str]              # Search direction adjustments needed
    priority_questions: list[str]       # Questions to prioritize in next 5 turns
    shallow_findings: list[str]         # Finding IDs with depth < 3
    overall_depth_score: float          # 0-1, overall depth score
    issues: list[str] = field(default_factory=list)


class ReflectionNode:
    """Evaluates research depth and direction using qwen-flash.

    Called every 5 turns to assess:
    1. Whether each main thread has reached target depth
    2. Whether causal chains have logical gaps
    3. Whether hypotheses are being properly verified
    4. Whether finding depth distribution is healthy
    """

    REFLECTION_PROMPT = """你是研究深度评估员。评估当前研究的深度和方向。

## 当前研究记忆
{memory_summary}

## 主线深度目标
{depth_targets}

## 浅层发现列表 (depth < 3)
{shallow_findings}

## 评估要求

请评估以下维度并输出JSON：

1. **深度评估**: 每条主线的当前深度是否达到目标？L1/L2占比过高扣分
2. **逻辑缺口**: 因果链中是否有断裂？假设验证是否有停滞？
3. **搜索调整**: 需要换什么搜索方向才能深挖？
4. **优先问题**: 下5轮应该优先解决什么问题？

```json
{{
  "depth_assessment": {{
    "MT001": {{
      "current_depth": 2,
      "target_depth": 4,
      "sufficient": false
    }}
  }},
  "gaps": ["因果链'A→B→C'中B→C缺乏证据支撑", "假设H001无任何验证进展"],
  "adjustments": ["搜索'比亚迪 竞争对手 比较分析'以深入竞争格局", "搜索'新能源补贴政策变化 2026'以验证政策影响"],
  "priority_questions": ["补贴退坡对销量的实际影响量化数据是什么？"],
  "shallow_findings": ["F001", "F003"],
  "overall_depth_score": 0.4,
  "issues": ["L1+L2发现占比过高(67%)", "因果链缺少中间环节证据"]
}}
```

注意：
1. overall_depth_score: 0=完全没有深度分析, 1=所有主线达到L3+且有完整因果链
2. adjustments必须给出具体的搜索关键词建议，不要泛泛说"加深分析"
3. shallow_findings列出所有depth_level < 3的Finding ID"""

    async def evaluate(
        self,
        memory: ResearchMemory,
        domain: str,
        turn: int,
    ) -> ReflectionReport:
        """Evaluate current research depth and direction.

        Args:
            memory: Current ResearchMemory state
            domain: Research domain
            turn: Current turn number

        Returns:
            ReflectionReport with depth assessment, gaps, and adjustments
        """
        import httpx

        # Build memory summary
        memory_summary = memory.get_context_for_next_turn(max_tokens=1500)

        # Build depth targets
        depth_targets_lines = []
        for mt in memory.main_threads:
            depth_targets_lines.append(
                f"- {mt.id} '{mt.title}': 当前L{mt.current_depth}/目标L{mt.target_depth}"
            )
        depth_targets = "\n".join(depth_targets_lines) if depth_targets_lines else "未设置主线"

        # Build shallow findings list
        shallow = memory.get_shallow_findings(depth_below=3)
        shallow_lines = []
        for f in shallow:
            shallow_lines.append(f"- [{f.id}] L{f.depth_level}: {f.content[:60]}")
        shallow_findings = "\n".join(shallow_lines) if shallow_lines else "无浅层发现"

        prompt = self.REFLECTION_PROMPT.format(
            memory_summary=memory_summary,
            depth_targets=depth_targets,
            shallow_findings=shallow_findings,
        )

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "qwen-flash",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 1024,
                    },
                    timeout=30,
                )

                if resp.status_code != 200:
                    logger.warning(f"ReflectionNode API error: {resp.status_code}")
                    return self._default_report(memory)

                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON response
                parsed = self._parse_json_response(content)

                report = ReflectionReport(
                    depth_assessment=parsed.get("depth_assessment", {}),
                    gaps=parsed.get("gaps", []),
                    adjustments=parsed.get("adjustments", []),
                    priority_questions=parsed.get("priority_questions", []),
                    shallow_findings=parsed.get("shallow_findings", []),
                    overall_depth_score=parsed.get("overall_depth_score", 0.5),
                    issues=parsed.get("issues", []),
                )

                # Update main thread depths from assessment
                for thread_id, assessment in report.depth_assessment.items():
                    if isinstance(assessment, dict):
                        current = assessment.get("current_depth", 0)
                        if isinstance(current, (int, float)):
                            memory.update_main_thread_depth(thread_id, int(current))

                logger.info(f"Reflection turn {turn}: depth_score={report.overall_depth_score:.2f}, "
                          f"gaps={len(report.gaps)}, adjustments={len(report.adjustments)}, "
                          f"shallow_findings={len(report.shallow_findings)}")

                return report

        except Exception as e:
            logger.warning(f"ReflectionNode failed (graceful degradation): {e}")
            return self._default_report(memory)

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

    def _default_report(self, memory: ResearchMemory) -> ReflectionReport:
        """Generate a default report when reflection fails."""
        shallow = [f.id for f in memory.get_shallow_findings(depth_below=3)]
        total = len(memory.findings) if memory.findings else 1
        shallow_ratio = len(shallow) / total if total > 0 else 0
        depth_score = max(0, 1.0 - shallow_ratio * 0.5)

        return ReflectionReport(
            depth_assessment={},
            gaps=["反思节点未能完成评估"],
            adjustments=[],
            priority_questions=[q.question for q in memory.get_unresolved_questions(limit=3)],
            shallow_findings=shallow,
            overall_depth_score=depth_score,
            issues=["反思评估降级：API调用失败"],
        )

    def format_reflection_message(self, report: ReflectionReport) -> str:
        """Format reflection report into a message to inject into the conversation.

        This message tells the LLM what needs deeper analysis.
        """
        parts = ["## 反思评估结果"]

        if report.overall_depth_score < 0.5:
            parts.append("\n⚠️ **当前分析深度不足，需要进一步深挖**")

        # Shallow findings that need deeper analysis
        if report.shallow_findings:
            parts.append(f"\n### 需要深挖的浅层发现")
            parts.append(f"以下发现停留在L1/L2层面，需要追问WHY继续深入：")
            for fid in report.shallow_findings[:5]:
                parts.append(f"- {fid}")

        # Logic gaps
        if report.gaps:
            parts.append(f"\n### 逻辑缺口")
            for gap in report.gaps[:3]:
                parts.append(f"- {gap}")

        # Search adjustments
        if report.adjustments:
            parts.append(f"\n### 建议搜索方向")
            for adj in report.adjustments[:5]:
                parts.append(f"- {adj}")

        # Priority questions
        if report.priority_questions:
            parts.append(f"\n### 优先解答问题")
            for q in report.priority_questions[:3]:
                parts.append(f"- {q}")

        parts.append(f"\n深度评分: {report.overall_depth_score:.1f}/1.0")
        parts.append("请针对以上不足，继续深挖分析，不要停留在表象。")

        return "\n".join(parts)
