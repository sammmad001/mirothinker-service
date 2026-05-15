"""
MiroThinker - Research Memory Layer

Structured knowledge base independent of conversation history.
Accumulates findings, causal chains, hypotheses, evidence, and open questions
across research turns, replacing destructive assistant message summarization.

This is the single cross-phase information carrier for the deep reasoning architecture.
"""

import re
import json
from dataclasses import dataclass, field
from datetime import datetime

from src.core.config import settings
from src.core.logging_config import logger


# === Data Models ===

@dataclass
class Finding:
    id: str                      # "F001", "F002", ...
    content: str                 # Complete finding narrative (200-500 chars, NOT compressed)
    depth_level: int             # 1=surface, 2=direct_cause, 3=root_cause, 4=systemic
    evidence_ids: list[str]      # Linked evidence IDs
    source_urls: list[str]       # Source URLs
    topic: str                   # Belonging main thread topic
    confidence: str              # "已确认" / "推测" / "有争议"
    created_turn: int            # Turn when created


@dataclass
class CausalStep:
    finding_id: str
    reasoning: str               # Why from previous step to this step


@dataclass
class CausalChain:
    id: str                      # "CC001"
    title: str                   # e.g. "补贴退坡→需求下滑→产能过剩→价格战"
    steps: list[CausalStep]
    strength: str                # "强" / "中等" / "弱"


@dataclass
class Hypothesis:
    id: str                      # "H001"
    statement: str
    status: str                  # "待验证" / "部分验证" / "已验证" / "已否定"
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    priority: str                # "high" / "medium" / "low"


@dataclass
class Evidence:
    id: str                      # "E001"
    content: str                 # Complete content (300-800 chars)
    source_url: str
    source_title: str
    source_credibility: float
    evidence_type: str           # "数据" / "事实" / "观点" / "预测"


@dataclass
class OpenQuestion:
    id: str                      # "Q001"
    question: str
    priority: str                # "critical" / "important" / "supplementary"
    related_findings: list[str]
    resolved: bool


@dataclass
class MainThread:
    id: str                      # "MT001"
    title: str                   # Main thread title
    finding_sequence: list[str]  # Ordered Finding ID list
    target_depth: int            # Target depth level
    current_depth: int           # Current achieved depth


@dataclass
class ResearchMemory:
    """Structured knowledge base that persists across research turns.

    Replaces the destructive assistant message summarization.
    Each turn's output is extracted into structured knowledge
    (Finding, CausalChain, Hypothesis, Evidence, OpenQuestion)
    and accumulated here.

    Also stores the complete "query → methodology → reasoning" chain
    for future convergence and enrichment.
    """
    findings: list[Finding] = field(default_factory=list)
    causal_chains: list[CausalChain] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    evidence_map: dict[str, list[Evidence]] = field(default_factory=dict)
    open_questions: list[OpenQuestion] = field(default_factory=list)
    main_threads: list[MainThread] = field(default_factory=list)

    # === Session metadata: query + methodology + reasoning chain ===
    query: str = ""                           # Original research question
    domain: str = ""                          # Detected domain
    thread_methodologies: dict[str, str] = field(default_factory=dict)  # thread_title → methodology
    reasoning_log: list[dict] = field(default_factory=list)  # Per-turn reasoning snapshot
    created_at: str = ""                      # ISO timestamp
    completed_at: str = ""                    # ISO timestamp

    # ID counters
    _id_counters: dict[str, int] = field(default_factory=lambda: {
        "F": 0, "CC": 0, "H": 0, "E": 0, "Q": 0, "MT": 0
    })

    def next_id(self, prefix: str) -> str:
        """Generate next ID for a given prefix."""
        self._id_counters[prefix] = self._id_counters.get(prefix, 0) + 1
        return f"{prefix}{self._id_counters[prefix]:03d}"

    def add_finding(self, content: str, depth_level: int, topic: str,
                    source_urls: list[str] = None, confidence: str = "推测",
                    evidence_ids: list[str] = None, turn: int = 0) -> Finding:
        """Add a new finding to memory."""
        finding = Finding(
            id=self.next_id("F"),
            content=content,
            depth_level=depth_level,
            evidence_ids=evidence_ids or [],
            source_urls=source_urls or [],
            topic=topic,
            confidence=confidence,
            created_turn=turn,
        )
        self.findings.append(finding)
        return finding

    def add_causal_chain(self, title: str, steps: list[dict],
                         strength: str = "中等") -> CausalChain:
        """Add a new causal chain."""
        chain = CausalChain(
            id=self.next_id("CC"),
            title=title,
            steps=[CausalStep(**s) for s in steps],
            strength=strength,
        )
        self.causal_chains.append(chain)
        return chain

    def add_hypothesis(self, statement: str, priority: str = "medium") -> Hypothesis:
        """Add a new hypothesis."""
        hyp = Hypothesis(
            id=self.next_id("H"),
            statement=statement,
            status="待验证",
            supporting_evidence=[],
            contradicting_evidence=[],
            priority=priority,
        )
        self.hypotheses.append(hyp)
        return hyp

    def add_evidence(self, content: str, source_url: str, source_title: str,
                     credibility: float, evidence_type: str, topic: str = "") -> Evidence:
        """Add new evidence."""
        ev = Evidence(
            id=self.next_id("E"),
            content=content,
            source_url=source_url,
            source_title=source_title,
            source_credibility=credibility,
            evidence_type=evidence_type,
        )
        if topic:
            if topic not in self.evidence_map:
                self.evidence_map[topic] = []
            self.evidence_map[topic].append(ev)
        return ev

    def add_open_question(self, question: str, priority: str = "important",
                          related_findings: list[str] = None) -> OpenQuestion:
        """Add a new open question."""
        q = OpenQuestion(
            id=self.next_id("Q"),
            question=question,
            priority=priority,
            related_findings=related_findings or [],
            resolved=False,
        )
        self.open_questions.append(q)
        return q

    def add_main_thread(self, title: str, target_depth: int = 3) -> MainThread:
        """Add a new main thread."""
        mt = MainThread(
            id=self.next_id("MT"),
            title=title,
            finding_sequence=[],
            target_depth=target_depth,
            current_depth=0,
        )
        self.main_threads.append(mt)
        return mt

    def init_from_plan(self, plan: dict):
        """Initialize memory from a ResearchPlan (Phase 3 PlanningPhase output).

        Args:
            plan: dict with main_threads, hypotheses, search_strategy, depth_targets
        """
        for mt_data in plan.get("main_threads", []):
            mt = self.add_main_thread(
                title=mt_data.get("title", ""),
                target_depth=mt_data.get("target_depth", 3),
            )
            # Store the ID mapping for later reference
            mt_data["_memory_id"] = mt.id

        for hyp_data in plan.get("hypotheses", []):
            self.add_hypothesis(
                statement=hyp_data.get("statement", ""),
                priority=hyp_data.get("priority", "medium"),
            )

    def set_session_metadata(self, query: str, domain: str = "",
                             thread_methodologies: dict[str, str] = None):
        """Store the original query and dynamic thread methodologies.

        This forms the head of the "query → methodology → reasoning" chain
        that enables future convergence and enrichment.
        """
        self.query = query
        self.domain = domain
        if thread_methodologies:
            self.thread_methodologies.update(thread_methodologies)
        from datetime import datetime
        self.created_at = datetime.now().isoformat()

    def log_reasoning(self, turn: int, thread_title: str, raw_analysis: str,
                      depth_level: int = 0, tools_used: list[str] = None):
        """Record a reasoning snapshot for this turn.

        Captures the raw analysis output and context, enabling future
        review of how conclusions were derived.
        """
        from datetime import datetime
        self.reasoning_log.append({
            "turn": turn,
            "thread": thread_title,
            "timestamp": datetime.now().isoformat(),
            "analysis": raw_analysis[:2000] if raw_analysis else "",  # Truncate for storage
            "depth_level": depth_level,
            "tools_used": tools_used or [],
        })

    def update_main_thread_depth(self, thread_id: str, new_depth: int):
        """Update a main thread's current depth."""
        for mt in self.main_threads:
            if mt.id == thread_id:
                mt.current_depth = max(mt.current_depth, new_depth)
                return

    def get_context_for_next_turn(self, max_tokens: int = 2000) -> str:
        """Generate structured summary to inject into next turn's context.

        Output format is designed for LLM comprehension:
        ## 研究进展摘要
        ### 已确认发现
        - [F001] L3: xxx (证据: E001, E002)
        ### 因果链
        - [CC001] A→B→C (强度: 强)
        ### 待验证假设
        - [H001] xxx (支持:1 反对:0)
        ### 未解答问题
        - [Q001] xxx (优先级: critical)
        ### 主线进度
        - [MT001] 当前L2/目标L4
        """
        parts = ["## 研究进展摘要"]

        # 1. Findings grouped by confidence
        confirmed = [f for f in self.findings if f.confidence == "已确认"]
        speculative = [f for f in self.findings if f.confidence == "推测"]
        controversial = [f for f in self.findings if f.confidence == "有争议"]

        if confirmed:
            parts.append("\n### 已确认发现")
            for f in confirmed[-8:]:  # Last 8 to stay within budget
                depth_label = self._depth_label(f.depth_level)
                ev_ids = ", ".join(f.evidence_ids[:3]) if f.evidence_ids else "无"
                parts.append(f"- [{f.id}] {depth_label}: {f.content[:100]} (证据: {ev_ids})")

        if speculative:
            parts.append("\n### 推测性发现")
            for f in speculative[-4:]:
                depth_label = self._depth_label(f.depth_level)
                parts.append(f"- [{f.id}] {depth_label}: {f.content[:80]}")

        if controversial:
            parts.append("\n### 争议点")
            for f in controversial[-3:]:
                parts.append(f"- [{f.id}]: {f.content[:80]}")

        # 2. Causal chains
        if self.causal_chains:
            parts.append("\n### 因果链")
            for cc in self.causal_chains[-5:]:
                parts.append(f"- [{cc.id}] {cc.title} (强度: {cc.strength})")

        # 3. Hypotheses
        active_hypotheses = [h for h in self.hypotheses if h.status in ("待验证", "部分验证")]
        if active_hypotheses:
            parts.append("\n### 待验证假设")
            for h in active_hypotheses[:5]:
                sup = len(h.supporting_evidence)
                con = len(h.contradicting_evidence)
                parts.append(f"- [{h.id}] {h.statement[:80]} (支持:{sup} 反对:{con} 状态:{h.status})")

        # 4. Open questions
        unresolved = [q for q in self.open_questions if not q.resolved]
        if unresolved:
            parts.append("\n### 未解答问题")
            for q in sorted(unresolved, key=lambda x: {"critical": 0, "important": 1, "supplementary": 2}.get(x.priority, 3))[:5]:
                parts.append(f"- [{q.id}] {q.question[:80]} (优先级: {q.priority})")

        # 5. Main thread progress
        if self.main_threads:
            parts.append("\n### 主线进度")
            for mt in self.main_threads:
                current = self._depth_label(mt.current_depth)
                target = self._depth_label(mt.target_depth)
                sufficient = "✓" if mt.current_depth >= mt.target_depth else "✗"
                parts.append(f"- [{mt.id}] {mt.title[:40]} 当前{current}/目标{target} {sufficient}")

        result = "\n".join(parts)

        # Truncate if exceeding max_tokens (rough estimate: 1 token ≈ 2 chars for Chinese)
        max_chars = max_tokens * 2
        if len(result) > max_chars:
            result = result[:max_chars] + "\n...(摘要截断)"

        return result

    def get_shallow_findings(self, depth_below: int = 3) -> list[Finding]:
        """Find findings that are not deep enough (for reflection node)."""
        return [f for f in self.findings if f.depth_level < depth_below]

    def get_unresolved_questions(self, limit: int = 5) -> list[OpenQuestion]:
        """Get unresolved key questions."""
        unresolved = [q for q in self.open_questions if not q.resolved]
        return sorted(unresolved, key=lambda x: {"critical": 0, "important": 1, "supplementary": 2}.get(x.priority, 3))[:limit]

    def to_synthesis_context(self) -> str:
        """Provide complete memory context for synthesis phase (no token limit).

        This is used at the final synthesis step, where we need all accumulated
        knowledge rather than the compressed summary.
        Includes the full query → methodology → reasoning chain.
        """
        parts = ["# 完整研究记忆"]

        # Original query and domain
        if self.query:
            parts.append(f"\n## 研究问题\n{self.query}")
        if self.domain:
            parts.append(f"\n领域: {self.domain}")

        # Dynamic thread methodologies (the "methodology" part of the chain)
        if self.thread_methodologies:
            parts.append("\n## 各主线分析方法论（动态定义）")
            for title, methodology in self.thread_methodologies.items():
                parts.append(f"\n### {title}\n{methodology}")

        # Reasoning log (the "reasoning" part of the chain)
        if self.reasoning_log:
            parts.append(f"\n## 推理过程记录（{len(self.reasoning_log)}轮）")
            for entry in self.reasoning_log:
                parts.append(
                    f"\n- 轮次{entry['turn']} [{entry['thread']}] "
                    f"深度L{entry['depth_level']} "
                    f"工具: {len(entry['tools_used'])}个"
                )

        # Findings by topic
        if self.findings:
            by_topic = {}
            for f in self.findings:
                topic = f.topic or "其他"
                if topic not in by_topic:
                    by_topic[topic] = []
                by_topic[topic].append(f)

            for topic, findings in by_topic.items():
                parts.append(f"\n## {topic}")
                for f in findings:
                    depth_label = self._depth_label(f.depth_level)
                    parts.append(f"### [{f.id}] {depth_label} | 置信度: {f.confidence}")
                    parts.append(f.content)
                    if f.source_urls:
                        parts.append(f"来源: {', '.join(f.source_urls[:3])}")
                    parts.append("")

        # Causal chains (full detail)
        if self.causal_chains:
            parts.append("\n## 因果链分析")
            for cc in self.causal_chains:
                parts.append(f"\n### [{cc.id}] {cc.title} (强度: {cc.strength})")
                for i, step in enumerate(cc.steps, 1):
                    parts.append(f"{i}. [{step.finding_id}] {step.reasoning}")

        # Hypotheses (full status)
        if self.hypotheses:
            parts.append("\n## 假设验证状态")
            for h in self.hypotheses:
                parts.append(f"\n### [{h.id}] {h.statement}")
                parts.append(f"状态: {h.status} | 优先级: {h.priority}")
                if h.supporting_evidence:
                    parts.append(f"支持证据: {', '.join(h.supporting_evidence)}")
                if h.contradicting_evidence:
                    parts.append(f"反对证据: {', '.join(h.contradicting_evidence)}")

        # Evidence summary
        all_evidence = []
        for ev_list in self.evidence_map.values():
            all_evidence.extend(ev_list)
        if all_evidence:
            parts.append("\n## 关键证据汇总")
            for ev in all_evidence:
                cred_label = "高" if ev.source_credibility >= 0.7 else "中" if ev.source_credibility >= 0.5 else "低"
                parts.append(f"- [{ev.id}] [{ev.evidence_type}] 可信度{cred_label}: {ev.content[:150]} | 来源: {ev.source_title}")

        # Open questions
        unresolved = [q for q in self.open_questions if not q.resolved]
        if unresolved:
            parts.append("\n## 未解答问题")
            for q in unresolved:
                parts.append(f"- [{q.id}] ({q.priority}) {q.question}")

        return "\n".join(parts)

    def to_session_snapshot(self) -> dict:
        """Export the complete analysis session as a serializable snapshot.

        This captures the full "query → methodology → reasoning → findings" chain,
        enabling future convergence, pattern recognition, and methodology enrichment.
        """
        return {
            "query": self.query,
            "domain": self.domain,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "thread_methodologies": self.thread_methodologies,
            "reasoning_log": self.reasoning_log,
            "findings": [
                {
                    "id": f.id, "content": f.content, "depth_level": f.depth_level,
                    "topic": f.topic, "confidence": f.confidence,
                    "created_turn": f.created_turn, "source_urls": f.source_urls,
                }
                for f in self.findings
            ],
            "causal_chains": [
                {
                    "id": cc.id, "title": cc.title, "strength": cc.strength,
                    "steps": [{"finding_id": s.finding_id, "reasoning": s.reasoning} for s in cc.steps],
                }
                for cc in self.causal_chains
            ],
            "hypotheses": [
                {
                    "id": h.id, "statement": h.statement, "status": h.status,
                    "priority": h.priority,
                    "supporting_evidence": h.supporting_evidence,
                    "contradicting_evidence": h.contradicting_evidence,
                }
                for h in self.hypotheses
            ],
            "main_threads": [
                {
                    "id": mt.id, "title": mt.title,
                    "target_depth": mt.target_depth, "current_depth": mt.current_depth,
                    "finding_sequence": mt.finding_sequence,
                }
                for mt in self.main_threads
            ],
            "metrics": {
                "finding_count": len(self.findings),
                "l3_plus_ratio": sum(1 for f in self.findings if f.depth_level >= 3) / max(len(self.findings), 1),
                "chain_count": len(self.causal_chains),
                "hypothesis_verified_ratio": sum(1 for h in self.hypotheses if h.status in ("已验证", "部分验证")) / max(len(self.hypotheses), 1),
                "reasoning_turns": len(self.reasoning_log),
            },
        }

    def estimate_token_count(self) -> int:
        """Estimate total token count of memory content."""
        total_chars = 0
        for f in self.findings:
            total_chars += len(f.content)
        for cc in self.causal_chains:
            total_chars += len(cc.title) + sum(len(s.reasoning) for s in cc.steps)
        for h in self.hypotheses:
            total_chars += len(h.statement)
        for ev_list in self.evidence_map.values():
            for ev in ev_list:
                total_chars += len(ev.content)
        for q in self.open_questions:
            total_chars += len(q.question)
        # Rough: 1 token ≈ 2 chars for Chinese
        return total_chars // 2

    @staticmethod
    def _depth_label(level: int) -> str:
        """Convert depth level to readable label."""
        labels = {0: "L0", 1: "L1表象", 2: "L2直接原因", 3: "L3根因", 4: "L4系统理解"}
        return labels.get(level, f"L{level}")


# === Memory Extractor ===

class MemoryExtractor:
    """Extracts structured knowledge from each turn's output into ResearchMemory.

    Uses qwen-flash (cheap, fast) to parse LLM output and search results
    into structured Finding, CausalChain, Hypothesis, Evidence, and OpenQuestion.
    """

    EXTRACTION_PROMPT = """你是研究记忆提取器。从研究输出和搜索结果中提取结构化知识。

## 当前记忆状态
{memory_summary}

## 本轮研究输出
{raw_output}

## 本轮搜索结果
{search_results}

## 提取要求
请提取以下结构化知识，输出JSON格式：

```json
{{
  "new_findings": [
    {{
      "content": "发现的完整叙述(100-300字符)",
      "depth_level": 1-4,
      "topic": "所属主线",
      "confidence": "已确认/推测/有争议",
      "source_urls": ["url1"]
    }}
  ],
  "new_causal_chains": [
    {{
      "title": "A→B→C 因果链标题",
      "steps": [
        {{"finding_id": "自动", "reasoning": "为什么从上一步到这一步"}}
      ],
      "strength": "强/中等/弱"
    }}
  ],
  "new_hypotheses": [
    {{
      "statement": "假设陈述",
      "priority": "high/medium/low"
    }}
  ],
  "new_evidence": [
    {{
      "content": "证据内容(100-300字符)",
      "source_url": "来源URL",
      "source_title": "来源标题",
      "evidence_type": "数据/事实/观点/预测",
      "topic": "关联议题"
    }}
  ],
  "new_questions": [
    {{
      "question": "需要进一步解答的问题",
      "priority": "critical/important/supplementary"
    }}
  ],
  "updated_hypotheses": [
    {{
      "id": "H001",
      "new_status": "部分验证/已验证/已否定",
      "new_evidence_id": "支持或反对的证据ID"
    }}
  ]
}}
```

注意：
1. depth_level: 1=表象观察, 2=直接原因, 3=根因, 4=系统理解
2. 只提取有意义的新发现，不要重复已有记忆
3. 因果链必须包含至少2个步骤，每步都有reasoning
4. 证据的content必须包含具体数据或事实，不要只写"有数据支持"
5. 如果没有某类新知识，该字段返回空数组
6. 必须输出合法JSON"""

    async def extract(
        self,
        raw_output: str,
        search_results: list[dict],
        current_memory: ResearchMemory,
        domain: str,
        turn: int,
    ) -> dict:
        """Extract structured knowledge from turn output.

        Args:
            raw_output: The LLM's raw response text
            search_results: List of search result dicts from this turn
            current_memory: Current ResearchMemory state
            domain: Research domain (finance/tech/health/general)
            turn: Current turn number

        Returns:
            Dict with extraction results: {
                new_findings, new_causal_chains, new_hypotheses,
                new_evidence, new_questions, updated_hypotheses
            }
        """
        import httpx

        # Build memory summary for context
        memory_summary = current_memory.get_context_for_next_turn(max_tokens=1000)

        # Format search results
        search_str = ""
        for r in search_results[:5]:
            title = r.get("title", "")[:60]
            snippet = r.get("snippet", "")[:100]
            url = r.get("link", r.get("url", ""))[:80]
            search_str += f"- {title}: {snippet} ({url})\n"

        prompt = self.EXTRACTION_PROMPT.format(
            memory_summary=memory_summary[:800],
            raw_output=raw_output[:2000],
            search_results=search_str[:1500],
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
                        "max_tokens": 2048,
                    },
                    timeout=30,
                )

                if resp.status_code != 200:
                    logger.warning(f"MemoryExtractor API error: {resp.status_code}")
                    return {"new_findings": [], "new_causal_chains": [], "new_hypotheses": [],
                            "new_evidence": [], "new_questions": [], "updated_hypotheses": []}

                data = resp.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON from response
                parsed = self._parse_json_response(content)

                # Apply to memory
                applied = self._apply_to_memory(parsed, current_memory, search_results, turn)

                logger.info(f"MemoryExtractor turn {turn}: +{applied['findings_added']} findings, "
                          f"+{applied['chains_added']} chains, +{applied['hypotheses_added']} hypotheses, "
                          f"+{applied['evidence_added']} evidence, +{applied['questions_added']} questions")

                return applied

        except Exception as e:
            logger.warning(f"MemoryExtractor failed (will degrade gracefully): {e}")
            return {"new_findings": [], "new_causal_chains": [], "new_hypotheses": [],
                    "new_evidence": [], "new_questions": [], "updated_hypotheses": []}

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract JSON from code block
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try parsing entire content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Fallback: return empty structure
        logger.warning("MemoryExtractor: Failed to parse JSON response")
        return {
            "new_findings": [], "new_causal_chains": [], "new_hypotheses": [],
            "new_evidence": [], "new_questions": [], "updated_hypotheses": [],
        }

    def _apply_to_memory(
        self,
        parsed: dict,
        memory: ResearchMemory,
        search_results: list[dict],
        turn: int,
    ) -> dict:
        """Apply parsed extraction results to ResearchMemory."""
        # Build URL set from search results for evidence linking
        result_urls = {r.get("link", r.get("url", "")) for r in search_results}

        # Add findings
        findings_added = 0
        for f_data in parsed.get("new_findings", []):
            if not f_data.get("content"):
                continue
            # Extract URLs from source_urls that match our search results
            source_urls = [u for u in f_data.get("source_urls", []) if u]
            memory.add_finding(
                content=f_data["content"],
                depth_level=min(max(f_data.get("depth_level", 1), 1), 4),
                topic=f_data.get("topic", ""),
                source_urls=source_urls,
                confidence=f_data.get("confidence", "推测"),
                turn=turn,
            )
            findings_added += 1

        # Add causal chains
        chains_added = 0
        for cc_data in parsed.get("new_causal_chains", []):
            if not cc_data.get("title") or not cc_data.get("steps"):
                continue
            memory.add_causal_chain(
                title=cc_data["title"],
                steps=cc_data["steps"],
                strength=cc_data.get("strength", "中等"),
            )
            chains_added += 1

        # Add hypotheses
        hypotheses_added = 0
        for h_data in parsed.get("new_hypotheses", []):
            if not h_data.get("statement"):
                continue
            memory.add_hypothesis(
                statement=h_data["statement"],
                priority=h_data.get("priority", "medium"),
            )
            hypotheses_added += 1

        # Add evidence
        evidence_added = 0
        for e_data in parsed.get("new_evidence", []):
            if not e_data.get("content"):
                continue
            memory.add_evidence(
                content=e_data["content"],
                source_url=e_data.get("source_url", ""),
                source_title=e_data.get("source_title", ""),
                credibility=0.5,
                evidence_type=e_data.get("evidence_type", "事实"),
                topic=e_data.get("topic", ""),
            )
            evidence_added += 1

        # Add questions
        questions_added = 0
        for q_data in parsed.get("new_questions", []):
            if not q_data.get("question"):
                continue
            memory.add_open_question(
                question=q_data["question"],
                priority=q_data.get("priority", "important"),
            )
            questions_added += 1

        # Update existing hypotheses
        for uh_data in parsed.get("updated_hypotheses", []):
            hyp_id = uh_data.get("id")
            if not hyp_id:
                continue
            for h in memory.hypotheses:
                if h.id == hyp_id:
                    new_status = uh_data.get("new_status")
                    if new_status:
                        h.status = new_status
                    new_evidence_id = uh_data.get("new_evidence_id")
                    if new_evidence_id:
                        # Determine if supporting or contradicting based on context
                        if new_status in ("已验证", "部分验证"):
                            h.supporting_evidence.append(new_evidence_id)
                        elif new_status == "已否定":
                            h.contradicting_evidence.append(new_evidence_id)
                    break

        # Update main thread depths based on new findings
        for f in memory.findings:
            if f.topic and f.created_turn == turn:
                for mt in memory.main_threads:
                    if f.topic in mt.title or mt.title in f.topic:
                        if f.depth_level > mt.current_depth:
                            mt.current_depth = f.depth_level
                        if f.id not in mt.finding_sequence:
                            mt.finding_sequence.append(f.id)

        return {
            "new_findings": [f for f in memory.findings if f.created_turn == turn],
            "new_causal_chains": memory.causal_chains[-chains_added:] if chains_added else [],
            "new_hypotheses": memory.hypotheses[-hypotheses_added:] if hypotheses_added else [],
            "new_evidence": [],
            "new_questions": memory.open_questions[-questions_added:] if questions_added else [],
            "updated_hypotheses": parsed.get("updated_hypotheses", []),
            "findings_added": findings_added,
            "chains_added": chains_added,
            "hypotheses_added": hypotheses_added,
            "evidence_added": evidence_added,
            "questions_added": questions_added,
        }
