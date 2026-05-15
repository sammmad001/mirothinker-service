"""
MiroThinker - Depth Quality Pipeline

Evaluates research output for depth quality:
1. Depth distribution: Are findings reaching L3+ depth?
2. Causal chain completeness: Are reasoning chains complete?
3. Hypothesis verification: Are hypotheses properly tested?
4. Logic chain integrity: Does each conclusion have complete derivation?
5. Evidence-Finding linkage: Are findings supported by evidence?

This replaces surface-level quality metrics with depth-aware evaluation.
"""

import re
from dataclasses import dataclass, field

from src.core.config import settings
from src.core.logging_config import logger


@dataclass
class DepthQualityReport:
    """Report from depth quality evaluation."""
    overall_depth_score: float          # 0-1, weighted average
    depth_distribution: dict[str, int]  # L1/L2/L3/L4 → count
    causal_chain_score: float           # 0-1
    hypothesis_verification_score: float # 0-1
    logic_chain_score: float            # 0-1
    evidence_support_score: float       # 0-1
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class DepthQualityPipeline:
    """Evaluate research output for depth quality.

    This pipeline complements the existing QualityCheckPipeline by adding
    depth-specific checks that go beyond surface metrics like source count
    and citation completeness.

    Key insight: A report can have many sources and citations but still
    lack depth if findings are all L1/L2 without causal reasoning.
    """

    def __init__(self):
        self.depth_checks = [
            self._check_depth_distribution,
            self._check_causal_chains,
            self._check_hypothesis_verification,
            self._check_logic_chains,
            self._check_evidence_support,
        ]

    def evaluate(
        self,
        result: str,
        memory=None,
        metadata: dict = None,
    ) -> DepthQualityReport:
        """Evaluate depth quality of research output.

        Args:
            result: The research report text
            memory: Optional ResearchMemory for structured analysis
            metadata: Optional metadata dict with sources

        Returns:
            DepthQualityReport with depth scores and issues
        """
        issues = []
        scores = {}

        for check in self.depth_checks:
            check_result = check(result, memory, metadata)
            issues.extend(check_result.get("issues", []))
            scores[check.__name__] = check_result.get("score", 0)

        # Weighted average: depth distribution and logic chains are most important
        weights = {
            "_check_depth_distribution": 0.30,
            "_check_causal_chains": 0.25,
            "_check_hypothesis_verification": 0.15,
            "_check_logic_chains": 0.20,
            "_check_evidence_support": 0.10,
        }

        weighted_sum = sum(
            scores.get(name, 0) * weight
            for name, weight in weights.items()
        )
        total_weight = sum(weights.values())
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Generate recommendations
        recommendations = self._generate_recommendations(scores, issues)

        # Build depth distribution from memory if available
        depth_dist = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
        if memory and hasattr(memory, 'findings') and memory.findings:
            for f in memory.findings:
                level = f"L{f.depth_level}"
                if level in depth_dist:
                    depth_dist[level] += 1

        report = DepthQualityReport(
            overall_depth_score=round(overall_score, 3),
            depth_distribution=depth_dist,
            causal_chain_score=round(scores.get("_check_causal_chains", 0), 3),
            hypothesis_verification_score=round(scores.get("_check_hypothesis_verification", 0), 3),
            logic_chain_score=round(scores.get("_check_logic_chains", 0), 3),
            evidence_support_score=round(scores.get("_check_evidence_support", 0), 3),
            issues=issues,
            recommendations=recommendations,
        )

        logger.info(f"DepthQuality: overall={report.overall_depth_score:.2f}, "
                   f"distribution={depth_dist}, "
                   f"causal={report.causal_chain_score:.2f}, "
                   f"logic={report.logic_chain_score:.2f}")

        return report

    def _check_depth_distribution(
        self, result: str, memory=None, metadata: dict = None,
    ) -> dict:
        """Check if analysis reaches sufficient depth (L3+).

        Evaluates both the ResearchMemory finding depths and the
        report's language patterns that indicate deep analysis.
        """
        issues = []
        score = 0.3  # Start low

        # Method 1: Check ResearchMemory if available
        if memory and hasattr(memory, 'findings') and memory.findings:
            depth_counts = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}
            for f in memory.findings:
                level = f"L{f.depth_level}"
                if level in depth_counts:
                    depth_counts[level] += 1

            total = sum(depth_counts.values())
            if total > 0:
                l3_plus_ratio = (depth_counts["L3"] + depth_counts["L4"]) / total
                score = max(score, l3_plus_ratio)

                if l3_plus_ratio < 0.3:
                    issues.append(
                        f"深度不足: L3+发现仅占{l3_plus_ratio:.0%}，"
                        f"大部分发现停留在L1/L2表象层面"
                    )
                if depth_counts["L1"] > depth_counts.get("L3", 0) * 2:
                    issues.append("浅层发现(L1)远多于深层发现(L3)，分析深度不够")

        # Method 2: Check report text for depth indicators
        depth_indicators = [
            r"根本原因", r"根因", r"底层逻辑", r"深层次", r"结构性",
            r"系统性", r"因果链", r"传导机制", r"驱动因素",
            r"why", r"为什么", r"归因", r"推导",
        ]
        depth_matches = sum(
            1 for pattern in depth_indicators
            if re.search(pattern, result, re.I)
        )
        depth_text_score = min(depth_matches / 5, 1.0)

        # Combine: if memory available, weight it more; otherwise rely on text
        if memory and hasattr(memory, 'findings') and memory.findings:
            score = score * 0.7 + depth_text_score * 0.3
        else:
            score = depth_text_score

        return {"score": min(score, 1.0), "issues": issues}

    def _check_causal_chains(
        self, result: str, memory=None, metadata: dict = None,
    ) -> dict:
        """Check if causal chains are present and complete.

        A complete causal chain has:
        - At least 3 steps (A→B→C)
        - Each step has reasoning
        - The chain explains WHY, not just WHAT
        """
        issues = []
        score = 0.0

        # Check ResearchMemory for causal chains
        if memory and hasattr(memory, 'causal_chains') and memory.causal_chains:
            total_chains = len(memory.causal_chains)
            complete_chains = sum(
                1 for cc in memory.causal_chains
                if len(cc.steps) >= 2 and cc.strength in ("强", "中等")
            )
            if total_chains > 0:
                score = complete_chains / total_chains

            if total_chains == 0:
                issues.append("没有发现任何因果链，分析缺乏逻辑推导")
            elif complete_chains < total_chains:
                issues.append(f"因果链完整率较低({complete_chains}/{total_chains})，部分链条缺少推理步骤")

        # Check report text for causal chain indicators
        causal_patterns = [
            r"导致", r"引起", r"推动", r"驱动", r"因为.*?所以",
            r"从而", r"进而", r"因此", r"于是", r"结果",
            r"→", r"引起.*?连锁", r"传导",
        ]
        causal_matches = sum(
            1 for p in causal_patterns
            if re.search(p, result)
        )
        text_causal_score = min(causal_matches / 4, 1.0)

        if memory and hasattr(memory, 'causal_chains') and memory.causal_chains:
            score = score * 0.7 + text_causal_score * 0.3
        else:
            score = text_causal_score

        if score < 0.3:
            issues.append("因果推理缺失：报告缺乏'为什么'和'导致'的逻辑推导")

        return {"score": min(score, 1.0), "issues": issues}

    def _check_hypothesis_verification(
        self, result: str, memory=None, metadata: dict = None,
    ) -> dict:
        """Check if hypotheses are properly verified.

        Good research forms hypotheses and then tests them with evidence.
        """
        issues = []
        score = 0.3  # Default: no hypotheses tracked

        if memory and hasattr(memory, 'hypotheses') and memory.hypotheses:
            total = len(memory.hypotheses)
            verified = sum(
                1 for h in memory.hypotheses
                if h.status in ("已验证", "部分验证", "已否定")
            )
            if total > 0:
                score = verified / total

            untested = sum(1 for h in memory.hypotheses if h.status == "待验证")
            if untested > total / 2:
                issues.append(f"{untested}个假设仍待验证，假设验证不充分")

        # Check report text for hypothesis language
        hypothesis_patterns = [
            r"假设", r"推测", r"验证", r"证实", r"证伪", r"否定",
            r"支持.*?观点", r"与.*?一致", r"与.*?矛盾",
        ]
        hypothesis_matches = sum(
            1 for p in hypothesis_patterns
            if re.search(p, result)
        )
        text_hyp_score = min(hypothesis_matches / 3, 1.0)

        if memory and hasattr(memory, 'hypotheses') and memory.hypotheses:
            score = score * 0.7 + text_hyp_score * 0.3
        else:
            score = text_hyp_score

        return {"score": min(score, 1.0), "issues": issues}

    def _check_logic_chains(
        self, result: str, memory=None, metadata: dict = None,
    ) -> dict:
        """Check if conclusions have complete logic derivation chains.

        A complete logic chain for a conclusion looks like:
        Evidence → Reasoning → Intermediate conclusion → Final conclusion

        This checks whether the report shows reasoning, not just conclusions.
        """
        issues = []
        score = 0.0

        # Check for derivation language patterns
        derivation_patterns = [
            r"因为.*?所以",            # because...therefore
            r"基于.*?可以推断",        # based on...we can infer
            r"这表明",                  # this indicates
            r"由此可以得出",            # from this we can conclude
            r"根据.*?数据",            # according to...data
            r"从.*?角度来看",          # from...perspective
            r"推断|推论|推导",          # infer/deduce/derive
            r"综上所述",                # in summary/considering all above
            r"证据表明",                # evidence shows
            r"逻辑是",                  # the logic is
        ]
        derivation_matches = sum(
            1 for p in derivation_patterns
            if re.search(p, result)
        )

        # Check for "naked conclusions" (conclusions without reasoning)
        # Pattern: short bold statements followed by no explanation
        naked_conclusions = re.findall(
            r'\*\*[^*]{5,30}\*\*\s*\n(?!\s*[-*]|\s*\d+\.|因为|基于|根据|这|由此)',
            result
        )
        naked_ratio = len(naked_conclusions) / max(len(re.findall(r'\*\*[^*]{5,30}\*\*', result)), 1)

        # Score: more derivation patterns = better, fewer naked conclusions = better
        derivation_score = min(derivation_matches / 5, 1.0)
        conclusion_score = max(0, 1.0 - naked_ratio)

        score = derivation_score * 0.6 + conclusion_score * 0.4

        if derivation_matches < 3:
            issues.append("逻辑推导语言稀少，结论缺少完整的推导过程")
        if naked_ratio > 0.5:
            issues.append(f"存在{len(naked_conclusions)}个无推导支撑的'裸结论'")

        return {"score": min(score, 1.0), "issues": issues}

    def _check_evidence_support(
        self, result: str, memory=None, metadata: dict = None,
    ) -> dict:
        """Check if findings are supported by specific evidence (not vague references).

        Good evidence: "营收同比增长32.5% (来源: 2026Q1财报)"
        Bad evidence: "有数据支持" / "市场普遍认为"
        """
        issues = []
        score = 0.3

        # Check for specific evidence patterns
        specific_evidence = re.findall(
            r'\d+[\.,]\d+%|\d+[\.,]\d+亿|\d+[\.,]\d+万|'
            r'同比增长|环比增长|同比|环比|'
            r'http[s]?://\S+',
            result
        )

        # Check for vague evidence patterns
        vague_evidence = re.findall(
            r'有数据表明|市场普遍|一般认为|众所周知|'
            r'据统计(?!.*?\d)|有报告称|有分析指出',
            result
        )

        specific_score = min(len(specific_evidence) / 8, 1.0)
        vague_penalty = min(len(vague_evidence) / 5, 0.5)

        score = specific_score - vague_penalty

        if len(vague_evidence) > 3:
            issues.append(f"存在{len(vague_evidence)}处模糊引用，缺少具体数据来源")
        if len(specific_evidence) < 3:
            issues.append("具体数据和事实支撑不足")

        return {"score": max(score, 0.0), "issues": issues}

    def _generate_recommendations(
        self, scores: dict, issues: list[str],
    ) -> list[str]:
        """Generate actionable recommendations based on depth quality scores."""
        recs = []

        if scores.get("_check_depth_distribution", 0) < 0.4:
            recs.append("增加深度分析：对每个关键发现追问WHY至少两层，从表象推进到根因")

        if scores.get("_check_causal_chains", 0) < 0.4:
            recs.append("构建因果链：将分散发现连接为A→B→C的完整推导路径")

        if scores.get("_check_hypothesis_verification", 0) < 0.4:
            recs.append("假设验证：对主要假设搜索支持和反对证据，给出验证结论")

        if scores.get("_check_logic_chains", 0) < 0.4:
            recs.append("完善推导过程：每个结论需展示完整的推理链，不可跳步")

        if scores.get("_check_evidence_support", 0) < 0.4:
            recs.append("加强证据支撑：用具体数据替代模糊引用，标注数据来源和时效性")

        return recs


def integrate_depth_quality(
    quality_report: dict,
    depth_report: DepthQualityReport,
) -> dict:
    """Integrate DepthQualityReport into the standard quality_report dict.

    This function merges depth quality metrics into the existing quality
    report format, adding depth-specific scores and issues.
    """
    # Add depth quality scores to the existing scores dict
    quality_report["scores"]["depth_distribution"] = depth_report.overall_depth_score
    quality_report["scores"]["causal_chain_quality"] = depth_report.causal_chain_score
    quality_report["scores"]["logic_chain_quality"] = depth_report.logic_chain_score
    quality_report["scores"]["hypothesis_verification"] = depth_report.hypothesis_verification_score

    # Add depth-specific issues
    quality_report["issues"].extend(depth_report.issues)

    # Add depth distribution
    quality_report["depth_distribution"] = depth_report.depth_distribution

    # Add recommendations
    quality_report["depth_recommendations"] = depth_report.recommendations

    # Recalculate overall score with depth weight (30% depth, 70% original)
    original_score = quality_report.get("overall_score", 0)
    depth_score = depth_report.overall_depth_score
    quality_report["overall_score"] = round(
        original_score * 0.7 + depth_score * 0.3, 3
    )
    quality_report["passed"] = quality_report["overall_score"] >= 0.70

    return quality_report
