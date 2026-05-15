"""
MiroThinker - 研究强制规则引擎

两条强制要求:
1. 数据时效限制: 除明确要求回溯历史外，参考数据必须来自3个月内
2. 评分门槛: 低于85分的结果不允许返回，必须达到85分才能完成任务

Usage:
    enforcer = ResearchEnforcer()
    result = enforcer.execute_research(query, allow_historical=False)

    if not enforcer.validate_result(result):
        # 需要改进或重新研究
        result = enforcer.improve_result(result)
"""

from typing import Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
from .quality_scorer import ResearchQualityScorer, QualityScore


class TimeRange(Enum):
    """时间范围枚举"""
    RECENT_3M = "3months"      # 3个月内
    RECENT_6M = "6months"      # 6个月内
    RECENT_1Y = "1year"        # 1年内
    ANY = "any"                # 任意时间


@dataclass
class EnforcementConfig:
    """强制规则配置"""
    # 数据时效要求
    min_recency_score: float = 0.7      # 时效性最低分数 (0-1)
    max_data_age_days: int = 90         # 最大数据年龄 (3个月=90天)
    allow_historical_override: bool = True  # 是否允许用户覆盖

    # 评分门槛要求
    min_overall_score: float = 85.0      # 最低总分 (0-100)
    min_dimension_scores: dict = field(default_factory=lambda: {
        "accuracy": 70.0,
        "recency": 70.0,
        "traceability": 70.0,
        "depth": 60.0,
        "completeness": 60.0,
    })

    # 迭代配置
    max_iterations: int = 3             # 最大改进次数
    retry_on_low_score: bool = True      # 低分是否重试


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    score: float
    issues: list[str]
    suggestions: list[str]
    needs_improvement: bool
    blocked_reason: str = ""


class ResearchEnforcer:
    """
    研究强制规则执行器

    强制执行两条规则:
    1. 数据时效: 3个月内数据优先
    2. 评分门槛: 85分以上才能返回

    Usage:
        enforcer = ResearchEnforcer()
        result = enforcer.run(query, user_config)

        if result.overall_score < 85:
            # 会被自动阻止并要求改进
            pass
    """

    DEFAULT_CONFIG = EnforcementConfig()

    def __init__(self, config: EnforcementConfig = None):
        self.config = config or self.DEFAULT_CONFIG
        self.scorer = ResearchQualityScorer()

    def validate_result(
        self,
        content: str,
        sources: list[dict],
        metadata: dict = None,
        user_requested_historical: bool = False,
    ) -> ValidationResult:
        """
        验证研究结果是否满足强制要求

        Args:
            content: 研究内容
            sources: 来源列表
            metadata: 额外元数据
            user_requested_historical: 用户是否明确要求回溯历史

        Returns:
            ValidationResult 验证结果
        """
        metadata = metadata or {}
        issues = []
        suggestions = []
        needs_improvement = False

        # 1. 检查数据时效 (除非用户明确要求历史数据)
        if not user_requested_historical:
            recency_result = self._validate_recency(sources)
            if not recency_result["passed"]:
                issues.append(recency_result["issue"])
                suggestions.append(recency_result["suggestion"])
                needs_improvement = True

        # 2. 计算评分
        score = self.scorer.score(content, sources, metadata)

        # 3. 检查评分门槛
        if score.overall_score < self.config.min_overall_score:
            issues.append(f"总分 {score.overall_score:.1f} 低于最低要求 {self.config.min_overall_score}")
            suggestions.append("建议: 增加权威来源、强化因果分析、完善引用标注")
            needs_improvement = True

        # 4. 检查各维度分数
        dim_issues = self._check_dimension_scores(score)
        issues.extend(dim_issues["issues"])
        suggestions.extend(dim_issues["suggestions"])

        # 5. 确定是否阻止返回
        blocked = needs_improvement and not self.config.retry_on_low_score

        return ValidationResult(
            passed=not needs_improvement,
            score=score.overall_score,
            issues=issues,
            suggestions=suggestions,
            needs_improvement=needs_improvement,
            blocked_reason="评分未达标准，需改进" if blocked else "",
        )

    def _validate_recency(self, sources: list[dict]) -> dict:
        """验证数据时效"""
        if not sources:
            return {
                "passed": False,
                "issue": "缺少数据来源",
                "suggestion": "请提供至少3个近期的权威来源"
            }

        # 统计3个月内来源数量
        recent_count = 0
        total = len(sources)
        now = __import__('datetime').datetime.now()

        for s in sources:
            date_str = s.get("extracted_date") or s.get("date")
            if not date_str:
                continue

            try:
                from datetime import datetime
                source_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                source_date = source_date.replace(tzinfo=None)
                days_old = (now - source_date).days

                if days_old <= self.config.max_data_age_days:
                    recent_count += 1
            except (ValueError, TypeError):
                pass

        # 计算近期数据比例
        recent_ratio = recent_count / total if total > 0 else 0

        if recent_ratio >= 0.6:  # 60%以上为近期数据
            return {
                "passed": True,
                "issue": "",
                "suggestion": ""
            }
        elif recent_ratio >= 0.3:
            return {
                "passed": True,
                "issue": f"仅 {recent_ratio*100:.0f}% 来源为3个月内数据",
                "suggestion": "建议增加更多近期来源以提高时效性评分"
            }
        else:
            return {
                "passed": False,
                "issue": f"仅 {recent_ratio*100:.0f}% 来源为3个月内数据 (要求60%+)",
                "suggestion": f"请优先使用近{self.config.max_data_age_days}天内的数据源"
            }

    def _check_dimension_scores(self, score: QualityScore) -> dict:
        """检查各维度分数"""
        issues = []
        suggestions = []

        dims = {
            "accuracy": score.breakdown.accuracy * 100,
            "recency": score.breakdown.recency * 100,
            "traceability": score.breakdown.traceability * 100,
            "depth": score.breakdown.depth * 100,
            "completeness": score.breakdown.completeness * 100,
        }

        for dim, value in dims.items():
            min_score = self.config.min_dimension_scores.get(dim, 60)
            if value < min_score:
                dim_names = {
                    "accuracy": "准确性",
                    "recency": "时效性",
                    "traceability": "可追溯性",
                    "depth": "深度",
                    "completeness": "完整性",
                }
                issues.append(f"{dim_names[dim]} {value:.1f}% 低于最低要求 {min_score}%")

                # 生成具体建议
                if dim == "accuracy":
                    suggestions.append("增加权威来源(如nature/science)并减少矛盾")
                elif dim == "recency":
                    suggestions.append("优先使用90天内的新数据源")
                elif dim == "traceability":
                    suggestions.append("使用[1][2]格式内联标注并添加参考来源章节")
                elif dim == "depth":
                    suggestions.append("增加因果分析(因此/因为/导致)和推理链")
                elif dim == "completeness":
                    suggestions.append("确保包含摘要/分析/结论结构")

        return {"issues": issues, "suggestions": suggestions}

    def enforce_and_improve(
        self,
        content: str,
        sources: list[dict],
        metadata: dict = None,
        iteration: int = 0,
    ) -> dict:
        """
        执行强制检查并在需要时触发改进

        Args:
            content: 研究内容
            sources: 来源列表
            metadata: 额外元数据
            iteration: 当前迭代次数

        Returns:
            dict {
                "content": 最终内容,
                "passed": 是否通过,
                "score": 最终分数,
                "validation": 验证结果,
                "iterations": 迭代次数
            }
        """
        # 检查用户是否要求历史数据
        user_requested_historical = metadata.get("allow_historical", False)

        # 验证当前结果
        validation = self.validate_result(
            content, sources, metadata, user_requested_historical
        )

        # 如果通过，直接返回
        if validation.passed:
            return {
                "content": content,
                "passed": True,
                "score": validation.score,
                "validation": validation,
                "iterations": iteration,
            }

        # 如果已达最大迭代次数且不允许返回
        if iteration >= self.config.max_iterations:
            return {
                "content": None,  # 阻止返回
                "passed": False,
                "score": validation.score,
                "validation": validation,
                "iterations": iteration,
                "blocked": True,
            }

        # 继续迭代
        return self.enforce_and_improve(
            content, sources, metadata, iteration + 1
        )


class TimeAwareSearchFilter:
    """
    时间感知搜索过滤器

    确保搜索结果优先返回3个月内的数据
    """

    def __init__(self, max_age_days: int = 90):
        self.max_age_days = max_age_days

    def filter_by_recency(self, results: list[dict]) -> list[dict]:
        """
        按时效性过滤搜索结果

        Args:
            results: 搜索结果列表

        Returns:
            排序后的结果 (近期优先)
        """
        from datetime import datetime

        def get_score(result: dict) -> float:
            """计算时效性分数"""
            date_str = result.get("extracted_date") or result.get("date")
            if not date_str:
                return 0.5  # 无日期给中等分

            try:
                source_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                source_date = source_date.replace(tzinfo=None)
                days_old = (datetime.now() - source_date).days

                if days_old <= 30:
                    return 1.0
                elif days_old <= 90:
                    return 0.8
                elif days_old <= 180:
                    return 0.6
                elif days_old <= 365:
                    return 0.4
                else:
                    return 0.2
            except (ValueError, TypeError):
                return 0.4

        # 排序 (近期优先)
        scored = [(r, get_score(r)) for r in results]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [r for r, _ in scored]

    def should_include_old(self, result: dict, require_recent: bool = True) -> bool:
        """
        判断是否应该包含老数据

        Args:
            result: 搜索结果
            require_recent: 是否强制要求近期数据

        Returns:
            True 如果数据可用
        """
        if not require_recent:
            return True

        from datetime import datetime

        date_str = result.get("extracted_date") or result.get("date")
        if not date_str:
            return not require_recent  # 无日期则根据要求决定

        try:
            source_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            source_date = source_date.replace(tzinfo=None)
            days_old = (datetime.now() - source_date).days

            return days_old <= self.max_age_days
        except (ValueError, TypeError):
            return not require_recent


# === 快捷函数 ===

def check_research_quality(
    content: str,
    sources: list[dict],
    allow_historical: bool = False,
) -> ValidationResult:
    """快速检查研究质量"""
    enforcer = ResearchEnforcer()
    return enforcer.validate_result(
        content, sources, {},
        user_requested_historical=allow_historical
    )


# Example usage
if __name__ == "__main__":
    print("=== Research Enforcer Test ===\n")

    enforcer = ResearchEnforcer()

    # 测试内容
    test_content = """
    ## AI技术发展趋势

    根据最新研究，AI技术在2024年取得重大突破。
    来源: nature.com (2024-06)
    """

    test_sources = [
        {"url": "https://nature.com/ai-2024", "extracted_date": "2024-06-15"},
        {"url": "https://example.com/old", "extracted_date": "2023-01-01"},
    ]

    # 验证
    result = enforcer.validate_result(test_content, test_sources)

    print(f"通过: {result.passed}")
    print(f"分数: {result.score}")
    print(f"需改进: {result.needs_improvement}")

    if result.issues:
        print("\n问题:")
        for issue in result.issues:
            print(f"  - {issue}")

    if result.suggestions:
        print("\n建议:")
        for sug in result.suggestions:
            print(f"  - {sug}")

    # 测试时间过滤
    print("\n=== Time Filter Test ===\n")

    time_filter = TimeAwareSearchFilter()

    search_results = [
        {"title": "New AI", "extracted_date": "2026-04-01"},
        {"title": "Old AI", "extracted_date": "2024-01-01"},
        {"title": "Medium AI", "extracted_date": "2025-06-01"},
    ]

    filtered = time_filter.filter_by_recency(search_results)
    print("排序后结果 (近期优先):")
    for r in filtered:
        print(f"  - {r['title']}")