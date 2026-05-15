"""
MiroThinker - Deep Analysis Phase

Executes the research plan by analyzing each main thread in depth.
Integrates ResearchMemory extraction and ReflectionNode evaluation.

Core changes from the original linear loop:
1. System prompt injects current thread's depth target + memory context
2. Search results are immediately extracted into ResearchMemory
3. ReflectionNode evaluates depth every 5 turns
4. Thread switching when depth target is met
5. No "information saturation" early stop (depth-based instead)
"""

import re
import time

from src.core.config import settings
from src.core.logging_config import logger
from src.services.research_memory import ResearchMemory, MemoryExtractor
from src.services.reflection import ReflectionNode
from src.services.search import ToolClient
from src.services.phases.planning import ResearchPlan


class DeepAnalysisPhase:
    """Deep analysis phase: iterate through main threads with depth tracking."""

    def __init__(
        self,
        tools: ToolClient,
        memory_extractor: MemoryExtractor = None,
        reflection_node: ReflectionNode = None,
    ):
        self.tools = tools
        self.memory_extractor = memory_extractor
        self.reflection_node = reflection_node

    async def execute(
        self,
        plan: ResearchPlan,
        memory: ResearchMemory,
        system_prompt: str,
        query: str,
        domain: str,
        max_turns: int = 18,
        search_model: str = "qwen-turbo",
        temperature: float = 0.7,
        progress_callback=None,
        start_time: float = None,
    ) -> dict:
        """Execute deep analysis phase.

        Args:
            plan: ResearchPlan from PlanningPhase
            memory: ResearchMemory (will be updated in-place)
            system_prompt: Base system prompt (will be enhanced per-thread)
            query: Original research query
            domain: Research domain
            max_turns: Maximum analysis turns
            search_model: Model for search turns
            temperature: LLM temperature
            progress_callback: Optional progress callback
            start_time: Start time for elapsed calculation

        Returns:
            dict with turn_count, metadata, etc.
        """
        from src.services.agent import ResearchAgent

        # Create a minimal agent for LLM calls
        agent = ResearchAgent(enable_quality_enhancement=False, enable_memory=False)

        current_thread_idx = 0
        threads = plan.main_threads
        turn = 0
        research_metadata = {"sources": [], "claims": []}

        # Build messages list for this phase
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": query})

        # Inject initial plan context
        plan_context = self._format_plan_context(plan)
        messages.append({"role": "user", "content": plan_context})

        # Inject memory context if available
        if memory and memory.findings:
            mem_context = memory.get_context_for_next_turn(max_tokens=1500)
            if mem_context:
                messages.append({"role": "user", "content": mem_context})

        consecutive_no_tool = 0

        while turn < max_turns and current_thread_idx < len(threads):
            turn += 1
            current_thread = threads[current_thread_idx]
            thread_title = current_thread.get("title", "")
            target_depth = current_thread.get("target_depth", 3)

            # Update system prompt with current thread focus
            # Dynamic analysis methodology (per-thread, NOT per-domain)
            thread_methodology = ""
            if plan.thread_methodologies and thread_title in plan.thread_methodologies:
                thread_methodology = plan.thread_methodologies[thread_title]

            thread_directive = (
                f"\n\n## 当前分析焦点\n"
                f"正在分析主线: **{thread_title}**\n"
                f"目标深度: L{target_depth}\n"
                f"当前深度: L{memory.main_threads[current_thread_idx].current_depth if current_thread_idx < len(memory.main_threads) else 0}\n"
                f"要求: 每个发现必须追问WHY，不要停留在表象，至少达到L{target_depth}深度\n"
            )
            if thread_methodology:
                thread_directive += f"\n## 本主线分析方法论（根据问题内容动态定义）\n{thread_methodology}\n"
            messages[0]["content"] = system_prompt + thread_directive

            # Inject shallow findings warning
            shallow = memory.get_shallow_findings(depth_below=3)
            if shallow:
                shallow_ids = ", ".join([f.id for f in shallow[:5]])
                thread_directive += f"\n⚠️ 浅层发现需深挖: [{shallow_ids}]"

            # Progress callback
            if progress_callback and start_time:
                try:
                    progress_callback(turn=turn, elapsed=round(time.time() - start_time, 2))
                except Exception:
                    pass

            # Call LLM
            # Keep context window manageable
            context = messages[-12:] if len(messages) > 14 else messages
            message = await agent.call_llm(context, search_model, temperature)
            content = message.get("content", "") or ""
            messages.append({"role": "assistant", "content": content})

            # Record reasoning snapshot for this turn (query → methodology → reasoning chain)
            if memory:
                tools_used = re.findall(
                    r'(google_search\(".*?"\)|scrape_webpage\(".*?"\))', content
                )
                memory.log_reasoning(
                    turn=turn,
                    thread_title=thread_title,
                    raw_analysis=content,
                    depth_level=memory.main_threads[current_thread_idx].current_depth
                    if current_thread_idx < len(memory.main_threads) else 0,
                    tools_used=tools_used,
                )

            # Check for FINAL ANSWER (shouldn't happen in deep analysis, but handle gracefully)
            if "FINAL ANSWER:" in content:
                logger.info(f"DeepAnalysis turn {turn}: LLM tried to give FINAL ANSWER, redirecting to analysis")
                messages.append({
                    "role": "user",
                    "content": "现在是深入分析阶段，不要写FINAL ANSWER。继续针对当前主线深挖分析，追问WHY。"
                })

            # Execute tool calls
            tool_results = await self._execute_tools(content, agent)

            if tool_results:
                consecutive_no_tool = 0
                for tool_name, query_input, output in tool_results:
                    messages.append({"role": "tool", "content": f"{tool_name}: {output[:400]}"})

                    # Track sources
                    if tool_name == "google_search":
                        research_metadata["sources"].append({
                            "url": query_input,
                            "title": query_input,
                        })

                # Phase 1: Extract to memory
                if self.memory_extractor and memory:
                    try:
                        turn_search = []
                        for tn, qi, out in tool_results:
                            if tn == "google_search":
                                turn_search.append({"title": qi, "snippet": out[:200], "link": ""})

                        await self.memory_extractor.extract(
                            raw_output=content,
                            search_results=turn_search,
                            current_memory=memory,
                            domain=domain,
                            turn=turn,
                        )
                    except Exception as e:
                        logger.warning(f"DeepAnalysis turn {turn}: Memory extraction failed: {e}")

                # Phase 2: Reflection every 5 turns
                if (self.reflection_node and memory and memory.findings
                        and turn % 5 == 0 and turn > 0):
                    try:
                        reflection = await self.reflection_node.evaluate(
                            memory=memory, domain=domain, turn=turn,
                        )
                        reflection_msg = self.reflection_node.format_reflection_message(reflection)
                        messages.append({"role": "user", "content": reflection_msg})

                        if reflection.overall_depth_score < 0.3:
                            messages[0]["content"] += (
                                "\n\n[反思评估] 深度严重不足。必须追问WHY至少两层，构建因果链。"
                            )
                    except Exception as e:
                        logger.warning(f"DeepAnalysis turn {turn}: Reflection failed: {e}")

                # Check if current thread has reached target depth
                if current_thread_idx < len(memory.main_threads):
                    mt = memory.main_threads[current_thread_idx]
                    if mt.current_depth >= mt.target_depth:
                        logger.info(f"DeepAnalysis: Thread '{thread_title}' reached L{mt.current_depth}, switching to next")
                        current_thread_idx += 1

            else:
                consecutive_no_tool += 1
                if consecutive_no_tool >= 2:
                    messages.append({
                        "role": "user",
                        "content": "请使用google_search()搜索新信息来深入分析当前主线。"
                    })

        # Check if all threads reached target
        all_complete = all(
            mt.current_depth >= mt.target_depth
            for mt in memory.main_threads
        ) if memory.main_threads else False

        logger.info(f"DeepAnalysis complete: {turn} turns, "
                   f"thread_idx={current_thread_idx}/{len(threads)}, "
                   f"all_complete={all_complete}, "
                   f"memory_tokens≈{memory.estimate_token_count() if memory else 0}")

        return {
            "turn_count": turn,
            "all_threads_complete": all_complete,
            "current_thread_idx": current_thread_idx,
            "metadata": research_metadata,
        }

    async def _execute_tools(self, content: str, agent) -> list[tuple]:
        """Parse and execute tool calls from LLM output."""
        results = []

        # Parse google_search calls
        search_pattern = r'google_search\(["\'](.+?)["\']\)'
        for match in re.finditer(search_pattern, content):
            query = match.group(1)
            try:
                output = await self.tools.google_search(query)
                from src.services.agent import ResearchAgent
                ra = ResearchAgent(enable_quality_enhancement=False, enable_memory=False)
                output_str = ra._format_search_compact(output, max_results=5)
                results.append(("google_search", query, output_str))
            except Exception as e:
                results.append(("google_search", query, f"Error: {str(e)}"))

        # Parse scrape_webpage calls
        scrape_pattern = r'scrape_webpage\(["\'](.+?)["\']\)'
        for match in re.finditer(scrape_pattern, content):
            url = match.group(1)
            try:
                output = await self.tools.scrape_webpage(url)
                results.append(("scrape_webpage", url, output[:1500]))
            except Exception as e:
                results.append(("scrape_webpage", url, f"Error: {str(e)}"))

        return results

    def _format_plan_context(self, plan: ResearchPlan) -> str:
        """Format research plan into context message."""
        parts = ["## 研究计划\n"]

        parts.append("### 主线议题")
        for i, mt in enumerate(plan.main_threads, 1):
            title = mt.get("title", "")
            target = mt.get("target_depth", 3)
            keywords = mt.get("search_keywords", [])
            kw_str = ", ".join(keywords[:5])
            parts.append(f"{i}. **{title}** (目标深度: L{target}, 搜索: {kw_str})")

        if plan.hypotheses:
            parts.append("\n### 初始假设")
            for h in plan.hypotheses:
                stmt = h.get("statement", "")
                priority = h.get("priority", "medium")
                parts.append(f"- [{priority}] {stmt}")

        parts.append("\n请按主线顺序逐一深入分析，每条主线都要达到目标深度。")
        return "\n".join(parts)
