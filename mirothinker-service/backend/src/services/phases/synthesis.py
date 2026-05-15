"""
MiroThinker - Synthesis Phase

Produces the final research report using complete ResearchMemory context.
Unlike the legacy synthesis (which used last-3-messages), this phase
leverages the full accumulated knowledge: findings, causal chains,
hypothesis verification status, and evidence.

Uses the synthesis model (qwen3.6-plus) for maximum output quality.
"""

import json
import re
from dataclasses import dataclass

from src.core.config import settings
from src.core.logging_config import logger
from src.services.research_memory import ResearchMemory
from src.services.phases.planning import ResearchPlan


@dataclass
class SynthesisResult:
    """Output of the Synthesis phase."""
    report: str                     # Complete research report
    depth_achieved: dict[str, int]  # thread_title → achieved depth
    findings_count: int
    causal_chains_count: int
    hypotheses_verified: int
    token_estimate: int


class SynthesisPhase:
    """Synthesize all accumulated research memory into a coherent report.

    Key differences from legacy synthesis:
    1. Uses complete ResearchMemory instead of last-3-messages
    2. Structure follows logical main threads (not fixed templates)
    3. Every conclusion must have complete derivation chain
    4. Causal chains are fully presented, not just mentioned
    """

    SYNTHESIS_PROMPT = """你是MiroThinker研究综合分析师。基于完整研究记忆，撰写深度研究报告。

## 研究问题
{query}

## 研究计划主线
{plan_summary}

## 完整研究记忆
{memory_context}

## 综合分析要求

请撰写完整的深度研究报告，遵循以下原则：

### 1. 结构：逻辑主线驱动
- 报告结构由研究主线的逻辑关系决定（非固定模板）
- 每条主线按「发现→因果推导→结论」展开
- 主线之间如果有逻辑关联，需明确指出

### 2. 深度：完整推导链
- 每个关键结论必须展示完整推导过程（A→B→C→结论）
- 不要只给结论，必须展示"为什么"
- 对每个关键判断标注置信度和支撑证据

### 3. 证据：事实链支撑
- 每个声明必须有具体数据/事实/来源支撑
- 数据点必须标明来源和时效性
- 有争议的结论需呈现不同观点及各自证据

### 4. 因果链：完整呈现
- 发现的因果链必须完整呈现（不要压缩为"存在因果链"）
- 每个因果环节都要有推理依据
- 标注因果链强度（强/中等/弱）

### 5. 假设验证
- 已验证假设：呈现验证过程和关键证据
- 已否定假设：呈现否定理由
- 未完全验证假设：呈现当前进展和待解答问题

## 输出格式 (FINAL ANSWER)

用简体中文撰写报告，包含以下要素（结构根据内容自然组织）：

- **标题**：体现核心发现
- **核心判断**：2-3个最重要的结论（附完整推导链）
- **主线分析**：按逻辑主线展开，每个结论展示完整推导过程
- **因果链分析**：呈现发现的因果链及推理依据
- **争议与不确定性**：有争议的观点及各方论据
- **关键数据**：支撑结论的核心数据和来源
- **结论与展望**：基于证据的综合判断

重要：每个结论都需要展示完整的逻辑推导过程，不要跳步。"""

    async def execute(
        self,
        query: str,
        plan: ResearchPlan,
        memory: ResearchMemory,
        domain: str,
        synthesis_model: str = "qwen3.6-plus",
        temperature: float = 0.7,
        quality_pipeline=None,
        research_metadata: dict = None,
    ) -> SynthesisResult:
        """Execute synthesis phase.

        Args:
            query: Original research query
            plan: ResearchPlan from PlanningPhase
            memory: Complete ResearchMemory from DeepAnalysisPhase
            domain: Research domain
            synthesis_model: Model for synthesis (qwen3.6-plus recommended)
            temperature: LLM temperature
            quality_pipeline: Optional QualityCheckPipeline for quality checks
            research_metadata: Optional metadata for source tracking

        Returns:
            SynthesisResult with complete report and metrics
        """
        import httpx

        # Build plan summary
        plan_summary = self._format_plan_summary(plan)

        # Get full memory context (no token limit for synthesis)
        memory_context = memory.to_synthesis_context() if memory and memory.findings else "研究记忆为空"

        # Truncate memory context if extremely large (safety valve: ~40k chars ≈ 20k tokens)
        if len(memory_context) > 40000:
            memory_context = memory_context[:40000] + "\n\n...(记忆内容过长，已截断)"

        prompt = self.SYNTHESIS_PROMPT.format(
            query=query,
            plan_summary=plan_summary,
            memory_context=memory_context,
        )

        # Build messages for synthesis call
        messages = [
            {"role": "system", "content": self._build_synthesis_system(domain)},
            {"role": "user", "content": prompt},
        ]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": synthesis_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": 8192,  # Extended for complete report
                    },
                    timeout=180,
                )

                if resp.status_code != 200:
                    logger.warning(f"SynthesisPhase API error: {resp.status_code}")
                    return self._fallback_synthesis(query, memory)

                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                # Extract FINAL ANSWER if present
                if "FINAL ANSWER:" in content:
                    content = content.split("FINAL ANSWER:", 1)[1].strip()

                # Run quality check if pipeline available
                if quality_pipeline and research_metadata:
                    try:
                        quality_report = quality_pipeline.run(content, research_metadata, domain)
                        logger.info(f"Synthesis quality: {quality_report.get('overall_score', 0):.2f}")
                    except Exception as e:
                        logger.warning(f"Synthesis quality check failed: {e}")

                # Calculate metrics
                depth_achieved = {}
                if memory and memory.main_threads:
                    for mt in memory.main_threads:
                        depth_achieved[mt.title] = mt.current_depth

                hypotheses_verified = 0
                if memory and memory.hypotheses:
                    hypotheses_verified = sum(
                        1 for h in memory.hypotheses
                        if h.status in ("已验证", "部分验证")
                    )

                token_estimate = memory.estimate_token_count() if memory else 0

                result = SynthesisResult(
                    report=content,
                    depth_achieved=depth_achieved,
                    findings_count=len(memory.findings) if memory else 0,
                    causal_chains_count=len(memory.causal_chains) if memory else 0,
                    hypotheses_verified=hypotheses_verified,
                    token_estimate=token_estimate,
                )

                logger.info(f"SynthesisPhase complete: report={len(content)} chars, "
                          f"findings={result.findings_count}, chains={result.causal_chains_count}, "
                          f"hypotheses_verified={result.hypotheses_verified}, "
                          f"memory_tokens≈{token_estimate}")

                return result

        except Exception as e:
            logger.warning(f"SynthesisPhase failed: {e}")
            return self._fallback_synthesis(query, memory)

    def _build_synthesis_system(self, domain: str) -> str:
        """Build system prompt for synthesis call."""
        return (
            f"你是MiroThinker深度研究综合分析师，擅长{domain}领域。"
            f"你的任务是将分散的研究发现综合成逻辑严密、推导完整的深度报告。"
            f"每个结论必须有完整推导链路，不可跳步。用简体中文输出。"
        )

    def _format_plan_summary(self, plan: ResearchPlan) -> str:
        """Format research plan as summary for synthesis prompt."""
        lines = []
        for i, mt in enumerate(plan.main_threads, 1):
            title = mt.get("title", "")
            target = mt.get("target_depth", 3)
            lines.append(f"{i}. {title} (目标深度: L{target})")

        if plan.hypotheses:
            lines.append("\n初始假设:")
            for h in plan.hypotheses:
                stmt = h.get("statement", "")
                lines.append(f"- {stmt}")

        return "\n".join(lines) if lines else "未制定研究计划"

    def _fallback_synthesis(self, query: str, memory: ResearchMemory) -> SynthesisResult:
        """Generate a minimal fallback synthesis when API fails."""
        findings_text = ""
        if memory and memory.findings:
            for f in memory.findings[:10]:
                findings_text += f"- [{f.id}] {f.content[:100]}\n"
        else:
            findings_text = "- 无结构化发现\n"

        report = (
            f"# 关于「{query}」的研究报告\n\n"
            f"## 研究发现\n{findings_text}\n"
            f"## 说明\n"
            f"综合分析阶段遇到技术问题，以上为已收集的结构化发现摘要。"
        )

        return SynthesisResult(
            report=report,
            depth_achieved={},
            findings_count=len(memory.findings) if memory else 0,
            causal_chains_count=len(memory.causal_chains) if memory else 0,
            hypotheses_verified=0,
            token_estimate=memory.estimate_token_count() if memory else 0,
        )
