"""
MiroThinker - Research Quality Scorer
研究内容评分机制 - 基于报告目标的五大维度设计

评分维度:
1. 准确性 (Accuracy)      - 数据准确、来源可靠、无矛盾
2. 时效性 (Recency)       - 数据新鲜、更新时间近
3. 可追溯性 (Traceability) - 引用完整、内联标注、URL可用
4. 深度 (Depth)           - 推理链完整、因果分析深入
5. 完整性 (Completeness)  - 覆盖全面、结构完整

总分 = 加权平均 (各维度 * 权重)

目标: 提升数据准确性、时效性、可追溯性
"""

from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re


class ScoreLevel(Enum):
    """评分等级"""
    EXCELLENT = "A (优秀)"
    GOOD = "B (良好)"
    AVERAGE = "C (一般)"
    POOR = "D (较差)"
    FAIL = "F (不合格)"


@dataclass
class ScoreBreakdown:
    """各项分数明细"""
    accuracy: float = 0.0      # 准确性 (0-1)
    recency: float = 0.0       # 时效性 (0-1)
    traceability: float = 0.0  # 可追溯性 (0-1)
    depth: float = 0.0          # 深度 (0-1)
    completeness: float = 0.0  # 完整性 (0-1)


@dataclass
class QualityScore:
    """完整评分结果"""
    overall_score: float = 0.0          # 总分 (0-100)
    level: ScoreLevel = ScoreLevel.POOR
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)

    # 诊断信息
    issues: list[str] = field(default_factory=list)  # 问题列表
    suggestions: list[str] = field(default_factory=list)  # 改进建议
    strengths: list[str] = field(default_factory=list)  # 优点

    # 详细指标
    source_count: int = 0              # 来源数量
    citation_count: int = 0            # 引用数量
    date_coverage: float = 0.0         # 日期覆盖率
    contradiction_count: int = 0      # 矛盾数量
    verified_facts: int = 0           # 已验证事实数
    unverified_claims: int = 0        # 未验证声明数

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "overall_score": round(self.overall_score, 1),
            "level": self.level.value,
            "breakdown": {
                "accuracy": round(self.breakdown.accuracy * 100, 1),
                "recency": round(self.breakdown.recency * 100, 1),
                "traceability": round(self.breakdown.traceability * 100, 1),
                "depth": round(self.breakdown.depth * 100, 1),
                "completeness": round(self.breakdown.completeness * 100, 1),
            },
            "source_count": self.source_count,
            "citation_count": self.citation_count,
            "issues": self.issues[:5],  # 最多5个
            "suggestions": self.suggestions[:3],  # 最多3个
        }

    def format_markdown(self) -> str:
        """格式化为Markdown报告"""
        lines = [
            "## 研究质量评分报告\n",
            f"### 总分: {self.overall_score:.1f}/100 ({self.level.value})\n",
            "### 各维度得分\n",
            "| 维度 | 得分 | 权重 |",
            "|------|------|------|",
            f"| 准确性 | {self.breakdown.accuracy*100:.1f}% | 30% |",
            f"| 时效性 | {self.breakdown.recency*100:.1f}% | 25% |",
            f"| 可追溯性 | {self.breakdown.traceability*100:.1f}% | 20% |",
            f"| 深度 | {self.breakdown.depth*100:.1f}% | 15% |",
            f"| 完整性 | {self.breakdown.completeness*100:.1f}% | 10% |\n",
        ]

        if self.issues:
            lines.append("### 问题\n")
            for issue in self.issues[:5]:
                lines.append(f"- ⚠️ {issue}\n")

        if self.suggestions:
            lines.append("### 改进建议\n")
            for sug in self.suggestions[:3]:
                lines.append(f"- 💡 {sug}\n")

        if self.strengths:
            lines.append("### 优点\n")
            for strength in self.strengths[:3]:
                lines.append(f"- ✅ {strength}\n")

        return "\n".join(lines)


class ResearchQualityScorer:
    """
    研究内容质量评分器

    评分规则基于报告目标:
    - 提高数据准确性 (权重 30%)
    - 提高数据时效性 (权重 25%)
    - 增强可追溯性 (权重 20%)
    - 保证深度 (权重 15%)
    - 确保完整性 (权重 10%)

    Usage:
        scorer = ResearchQualityScorer()
        score = scorer.score(content, sources, metadata)
        print(f"总分: {score.overall_score}")
    """

    # 权重配置
    WEIGHTS = {
        "accuracy": 0.30,
        "recency": 0.25,
        "traceability": 0.20,
        "depth": 0.15,
        "completeness": 0.10,
    }

    # 阈值配置
    THRESHOLDS = {
        "excellent": 85,  # 85-100
        "good": 70,       # 70-84
        "average": 50,    # 50-69
        "poor": 30,        # 30-49
        "fail": 0,         # 0-29
    }

    def __init__(self):
        """初始化评分器"""
        pass

    def score(
        self,
        content: str,
        sources: list[dict] = None,
        metadata: dict = None,
        config: dict = None,
    ) -> QualityScore:
        """
        对研究内容评分

        Args:
            content: 研究内容文本
            sources: 来源列表 [{url, title, date, extracted_date}]
            metadata: 额外元数据 {矛盾数, 验证状态等}
            config: 可选配置覆盖

        Returns:
            QualityScore 完整评分结果
        """
        sources = sources or []
        metadata = metadata or {}
        config = config or {}

        # 计算各项分数
        accuracy = self._calc_accuracy(content, sources, metadata)
        recency = self._calc_recency(content, sources, metadata)
        traceability = self._calc_traceability(content, sources, metadata)
        depth = self._calc_depth(content, sources, metadata)
        completeness = self._calc_completeness(content, sources, metadata)

        # 加权计算总分
        overall = (
            accuracy * self.WEIGHTS["accuracy"] +
            recency * self.WEIGHTS["recency"] +
            traceability * self.WEIGHTS["traceability"] +
            depth * self.WEIGHTS["depth"] +
            completeness * self.WEIGHTS["completeness"]
        ) * 100

        # 确定等级
        level = self._get_level(overall)

        # 生成诊断信息
        issues, suggestions, strengths = self._diagnose(
            content, sources, metadata,
            accuracy, recency, traceability, depth, completeness
        )

        # 统计信息
        source_count = len(sources)
        citation_count = len(re.findall(r'\[(\d+)\]', content)) or content.count("http")

        # 构建结果
        breakdown = ScoreBreakdown(
            accuracy=accuracy,
            recency=recency,
            traceability=traceability,
            depth=depth,
            completeness=completeness,
        )

        return QualityScore(
            overall_score=round(overall, 1),
            level=level,
            breakdown=breakdown,
            issues=issues,
            suggestions=suggestions,
            strengths=strengths,
            source_count=source_count,
            citation_count=citation_count,
            date_coverage=self._calc_date_coverage(sources),
            contradiction_count=metadata.get("contradiction_count", 0),
            verified_facts=metadata.get("verified_facts", 0),
            unverified_claims=metadata.get("unverified_claims", 0),
        )

    # === 准确性评分 (30%) ===

    def _calc_accuracy(
        self,
        content: str,
        sources: list[dict],
        metadata: dict,
    ) -> float:
        """
        计算准确性分数

        考量因素:
        - 来源权威性 (预定义权重)
        - 矛盾检测结果
        - 事实验证状态
        - 数据支撑密度
        """
        score = 0.5  # 基础分

        # 来源权威性检查
        authoritative_sources = self._count_authoritative_sources(sources)
        if authoritative_sources > 0:
            score += min(authoritative_sources * 0.08, 0.25)

        # 矛盾检测扣分
        contradiction_count = metadata.get("contradiction_count", 0)
        score -= min(contradiction_count * 0.1, 0.3)

        # 事实验证加分
        verified_facts = metadata.get("verified_facts", 0)
        if verified_facts > 0:
            score += min(verified_facts * 0.05, 0.2)

        # 数据支撑密度
        has_data = bool(re.search(r'\d+[\.,]\d+|%|\$|¥', content))
        data_density = len(re.findall(r'\d+', content)) / max(len(content.split()), 1)
        if has_data and data_density > 0.05:
            score += 0.1

        return max(0, min(1, score))

    def _count_authoritative_sources(self, sources: list[dict]) -> int:
        """统计权威来源数量"""
        authoritative_domains = {
            "nature.com", "science.org", "arxiv.org",
            "reuters.com", "apnews.com", "bbc.com",
            "cninfo.com.cn", "sse.com.cn", "szse.cn",
            "worldbank.org", "imf.org", "pubmed.ncbi.nlm.nih.gov",
            "wikipedia.org",
        }
        count = 0
        for s in sources:
            url = s.get("url", "")
            for domain in authoritative_domains:
                if domain in url:
                    count += 1
                    break
        return count

    # === 时效性评分 (25%) ===

    def _calc_recency(
        self,
        content: str,
        sources: list[dict],
        metadata: dict,
    ) -> float:
        """
        计算时效性分数

        考量因素:
        - 来源日期新鲜度
        - 日期覆盖率
        - 是否标注数据时效
        """
        if not sources:
            return 0.3  # 无来源则低分

        scores = []
        now = datetime.now()

        for s in sources:
            date_str = s.get("extracted_date") or s.get("date")
            if not date_str:
                scores.append(0.3)
                continue

            try:
                source_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                source_date = source_date.replace(tzinfo=None)
                days_old = (now - source_date).days

                if days_old <= 90:
                    scores.append(1.0)
                elif days_old <= 365:
                    scores.append(0.7)
                elif days_old <= 730:  # 2年
                    scores.append(0.4)
                else:
                    scores.append(0.2)
            except (ValueError, TypeError):
                scores.append(0.3)

        avg_score = sum(scores) / len(scores) if scores else 0.3

        # 是否有数据时效标注
        has_currency_warning = bool(re.search(
            r'(截至|截止|数据.*?年|年.*?数据)',
            content
        ))
        if not has_currency_warning and avg_score < 0.5:
            avg_score -= 0.1

        return max(0, min(1, avg_score))

    def _calc_date_coverage(self, sources: list[dict]) -> float:
        """计算日期覆盖率"""
        if not sources:
            return 0.0

        dated = sum(1 for s in sources if s.get("extracted_date") or s.get("date"))
        return dated / len(sources)

    # === 可追溯性评分 (20%) ===

    def _calc_traceability(
        self,
        content: str,
        sources: list[dict],
        metadata: dict,
    ) -> float:
        """
        计算可追溯性分数

        考量因素:
        - 引用格式规范 ([1][2] 格式)
        - URL 可用性
        - 引用与内容匹配
        - 证据链完整
        """
        score = 0.4  # 基础分

        # 检查内联引用格式
        inline_citations = len(re.findall(r'\[(\d+)\]', content))
        if inline_citations >= 3:
            score += 0.2
        elif inline_citations >= 1:
            score += 0.1

        # 检查URL存在
        url_count = content.count("http")
        if url_count >= 5:
            score += 0.2
        elif url_count >= 2:
            score += 0.1

        # URL与引用匹配检查
        urls_in_content = re.findall(r'https?://[^\s\)\]"\'<>]+', content)
        if sources:
            source_urls = {s.get("url", s.get("link", "")) for s in sources}
            matched = sum(1 for url in urls_in_content if any(u and url in u for u in source_urls))
            if matched >= len(sources) * 0.5:
                score += 0.1

        # 有参考文献列表
        has_ref_section = bool(re.search(r'(参考|来源|references?sources)', content, re.I))
        if has_ref_section:
            score += 0.1

        return max(0, min(1, score))

    # === 深度评分 (15%) ===

    def _calc_depth(
        self,
        content: str,
        sources: list[dict],
        metadata: dict,
    ) -> float:
        """
        计算深度分数

        考量因素:
        - 因果分析完整性
        - 推理链展示
        - 证据支撑
        - 多角度分析
        """
        score = 0.4  # 基础分

        # 因果分析关键词
        causal_keywords = re.findall(
            r'(因此|所以|导致|因为|由于|result in|lead to|cause|because)',
            content, re.I
        )
        if len(causal_keywords) >= 3:
            score += 0.2
        elif len(causal_keywords) >= 1:
            score += 0.1

        # 推理链完整性 (检测结论-前提结构)
        has_conclusion = bool(re.search(r'(结论|总结|综上所述)', content))
        has_analysis = bool(re.search(r'(分析|原因|因素)', content))
        if has_conclusion and has_analysis:
            score += 0.15

        # 证据支撑密度
        evidence_markers = len(re.findall(r'(据.*显示|数据显示|研究表明)', content))
        if evidence_markers >= 2:
            score += 0.1
        elif evidence_markers >= 1:
            score += 0.05

        # 多角度分析
        perspective_markers = len(re.findall(r'(一方面|另一方面|然而|但是|不过)', content))
        if perspective_markers >= 2:
            score += 0.1
        elif perspective_markers >= 1:
            score += 0.05

        return max(0, min(1, score))

    # === 完整性评分 (10%) ===

    def _calc_completeness(
        self,
        content: str,
        sources: list[dict],
        metadata: dict,
    ) -> float:
        """
        计算完整性分数

        考量因素:
        - 结构完整性 (有标题/章节)
        - 来源数量
        - 关键部分存在
        """
        score = 0.5  # 基础分

        # 结构完整性
        has_headings = bool(re.search(r'^#{1,3}\s+', content, re.M))
        has_structure = bool(re.search(r'(摘要|概述|结论|建议)', content))
        if has_headings and has_structure:
            score += 0.2
        elif has_headings or has_structure:
            score += 0.1

        # 来源数量
        if len(sources) >= 5:
            score += 0.15
        elif len(sources) >= 3:
            score += 0.1

        # 字数充足 (至少500字)
        if len(content) >= 500:
            score += 0.1
        elif len(content) >= 200:
            score += 0.05

        return max(0, min(1, score))

    # === 辅助方法 ===

    def _get_level(self, score: float) -> ScoreLevel:
        """根据分数确定等级"""
        if score >= self.THRESHOLDS["excellent"]:
            return ScoreLevel.EXCELLENT
        elif score >= self.THRESHOLDS["good"]:
            return ScoreLevel.GOOD
        elif score >= self.THRESHOLDS["average"]:
            return ScoreLevel.AVERAGE
        elif score >= self.THRESHOLDS["poor"]:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.FAIL

    def _diagnose(
        self,
        content: str,
        sources: list[dict],
        metadata: dict,
        accuracy: float,
        recency: float,
        traceability: float,
        depth: float,
        completeness: float,
    ) -> tuple[list[str], list[str], list[str]]:
        """生成诊断信息"""
        issues = []
        suggestions = []
        strengths = []

        # 准确性诊断
        if accuracy < 0.5:
            issues.append("来源权威性不足，建议增加权威来源")
            suggestions.append("增加nature/science等权威期刊来源")
        else:
            strengths.append("来源质量可靠")

        # 时效性诊断
        if recency < 0.5:
            issues.append("数据可能过时，部分来源超过1年")
            suggestions.append("优先使用90天内的新数据源")
        else:
            strengths.append("数据来源新鲜")

        # 可追溯性诊断
        if traceability < 0.5:
            issues.append("引用格式不规范或缺少参考文献列表")
            suggestions.append("使用[1][2]内联标注格式并添加参考来源章节")
        else:
            strengths.append("引用归因清晰完整")

        # 深度诊断
        if depth < 0.5:
            issues.append("缺少因果分析和推理链")
            suggestions.append('增加"因此/因为/导致"等推理连接词')
        else:
            strengths.append("推理分析深入")

        # 完整性诊断
        if completeness < 0.5:
            issues.append("内容结构不完整或来源数量不足")
            suggestions.append("确保包含摘要/分析/结论结构")
        else:
            strengths.append("内容结构完整丰富")

        return issues, suggestions, strengths


# === 快捷函数 ===

def quick_score(content: str, sources: list[dict] = None) -> QualityScore:
    """快速评分"""
    scorer = ResearchQualityScorer()
    return scorer.score(content, sources)


# Example usage
if __name__ == "__main__":
    print("=== Research Quality Scorer Test ===\n")

    scorer = ResearchQualityScorer()

    # 测试样本内容
    test_content = """
    ## AI技术发展趋势研究

    ### 摘要
    本研究分析了2024-2025年人工智能技术的发展趋势。

    ### 发现

    1. **生成式AI快速发展**
       据最新数据显示，生成式AI市场规模在2024年增长了25%。
       来源: nature.com 2024-06

    2. **多模态成为新热点**
       因此，多模态AI技术将成为下一代AI的主要方向。
       来源: science.org 2024-08

    ### 分析
    一方面，大型语言模型的能力持续提升。
    另一方面，应用场景不断扩展。

    ### 结论
    综上所述，AI技术正处于快速发展期。
    建议关注生成式AI和多模态技术。

    ### 参考来源
    [1] https://nature.com/ai-trends-2024
    [2] https://science.org/multimodal-ai
    """

    test_sources = [
        {"url": "https://nature.com/ai-trends-2024", "title": "AI Trends 2024", "extracted_date": "2024-06-15"},
        {"url": "https://science.org/multimodal-ai", "title": "Multimodal AI", "extracted_date": "2024-08-20"},
        {"url": "https://example.com/old-news", "title": "Old News", "extracted_date": "2022-03-01"},
    ]

    test_metadata = {
        "verified_facts": 2,
        "contradiction_count": 0,
    }

    # 评分
    score = scorer.score(test_content, test_sources, test_metadata)

    # 输出
    print(f"总分: {score.overall_score}/100")
    print(f"等级: {score.level.value}")
    print(f"\n各维度:")
    print(f"  准确性: {score.breakdown.accuracy*100:.1f}%")
    print(f"  时效性: {score.breakdown.recency*100:.1f}%")
    print(f"  可追溯性: {score.breakdown.traceability*100:.1f}%")
    print(f"  深度: {score.breakdown.depth*100:.1f}%")
    print(f"  完整性: {score.breakdown.completeness*100:.1f}%")

    print(f"\n来源数: {score.source_count}")
    print(f"日期覆盖率: {score.date_coverage*100:.0f}%")

    if score.issues:
        print("\n问题:")
        for issue in score.issues:
            print(f"  ⚠️ {issue}")

    if score.strengths:
        print("\n优点:")
        for s in score.strengths:
            print(f"  ✅ {s}")

    # Markdown格式输出
    print("\n" + "="*50)
    print(score.format_markdown())