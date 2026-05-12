"""
MiroThinker - Research Agent Core
Agent state management and research execution with quality enhancement.
"""

import re
import time

from src.core.config import MODEL_MAP, DOMAIN_CONFIGS, settings
from src.core.logging_config import logger
from src.services.search import ToolClient
from src.services.quality import (
    FixedChannelSearch,
    SourceCredibilityScorer,
    ContradictionDetector,
    QualityCheckPipeline,
)


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


def detect_domain(query: str) -> str:
    """Auto-detect query domain."""
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


async def classify_query(query: str) -> str:
    """
    Classify query into three Tiers using qwen-flash.
    TIER_1: Simple factual (~50 Credits)
    TIER_2: Medium analysis (~500 Credits)
    TIER_3: Deep research (~600 Credits)
    """
    import httpx

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
                f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-flash",  # Cheapest model
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

            # Default to TIER_2 (conservative)
            return "TIER_2"
    except:
        return "TIER_2"  # Default on error


class ResearchAgent:
    """Core research agent with quality enhancement and Tier routing."""

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
        """Call DashScope API with proper response validation."""
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 4096,
                },
                timeout=120,
            )

            if resp.status_code != 200:
                raise Exception(f"LLM API error: {resp.status_code} - {resp.text}")

            data = resp.json()
            
            # Validate response structure
            if "choices" not in data or not data["choices"]:
                raise Exception(f"LLM API returned invalid response: {data}")
            
            choice = data["choices"][0]
            if "message" not in choice:
                raise Exception(f"LLM choice missing message field: {choice}")
            
            message = choice["message"]
            if not isinstance(message, dict):
                raise Exception(f"LLM message is not a dict: {type(message)} - {message}")
            
            return message

    async def run(
        self,
        query: str,
        max_turns: int = 200,
        context_keep: int = 5,
        model: str = "qwen-plus",
        temperature: float = 0.7,
        tier: str = None,
        progress_callback: callable = None,
    ) -> dict:
        """Run the research agent with quality enhancement and Tier routing."""
        start_time = time.time()

        # Tier routing: auto-classify if not specified
        if tier is None:
            tier = await classify_query(query)

        # Adjust max_turns based on Tier
        if tier == "TIER_1":
            max_turns = min(max_turns, 5)  # Simple: max 5 turns
        elif tier == "TIER_2":
            max_turns = min(max_turns, 50)  # Medium: max 50 turns
        else:  # TIER_3
            max_turns = min(max_turns, 125)  # Deep: max 125 turns

        # Detect domain for targeted research
        domain = detect_domain(query) if self.enable_quality else "general"

        # Build enhanced system prompt
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
        consecutive_no_tool = 0  # Smart early stopping counter
        source_saturation = False  # Information saturation flag

        while turn < max_turns:
            turn += 1
            agent_state.turn_count = turn

            # Update progress callback with current turn
            if progress_callback:
                try:
                    progress_callback(turn=turn, elapsed=round(time.time() - start_time, 2))
                except:
                    pass  # Don't let callback errors break the research

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

            # Check for tool calls
            tool_results = await self._execute_tools(content)

            if tool_results:
                consecutive_no_tool = 0  # Reset early stopping counter
                for tool_name, query_input, output in tool_results:
                    agent_state.tool_calls.append({
                        "tool": tool_name,
                        "input": query_input,
                        "output_len": len(str(output))[:100],
                    })
                    # OPTIMIZED: Reduce to 1000 chars in context
                    agent_state.add_message(
                        "tool",
                        f"{tool_name}('{query_input}'):\n{output[:1000]}"
                    )

                    # Extract and score sources for quality tracking
                    if tool_name == "google_search" and self.enable_quality:
                        try:
                            # Parse compact format or JSON
                            if output.startswith("[") or output.startswith("{"):
                                import json
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
                        except Exception as e:
                            logger.debug(f"Failed to parse search results: {e}")

                # Smart early stopping: check information saturation
                if self.enable_quality and len(research_metadata["sources"]) >= 25:
                    # Sufficient sources, prompt LLM to synthesize
                    agent_state.add_message(
                        "user",
                        "Information saturated. Synthesize findings into FINAL ANSWER:"
                    )
                    source_saturation = True
            else:
                consecutive_no_tool += 1

                # Smart early stopping: 3 consecutive turns without tool calls
                if consecutive_no_tool >= 3:
                    agent_state.add_message(
                        "user",
                        "No new tools called. Provide FINAL ANSWER based on current findings:"
                    )

                # Check if agent is stuck
                if not tool_results and "FINAL ANSWER:" not in content and consecutive_no_tool < 3:
                    agent_state.add_message(
                        "user",
                        "Continue researching or provide FINAL ANSWER:"
                    )

        # Max turns reached without final answer - ask for synthesis
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
        """Parse content for tool calls and execute them."""
        results = []

        # Parse google_search calls
        search_pattern = r'google_search\(["\'](.+?)["\']\)'
        for match in re.finditer(search_pattern, content):
            query = match.group(1)
            try:
                output = await self.tools.google_search(query)
                # Use compact text format
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
                # OPTIMIZED: Reduce to 1500 chars
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
