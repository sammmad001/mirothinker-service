"""
MiroThinker - Incremental Research Mode
基于缓存的变化检测和增量更新通知。
当缓存的研究有新内容时自动通知用户。
"""

import time
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field
import hashlib
import difflib


@dataclass
class ContentChange:
    """检测到的内容变化"""
    query: str
    change_type: str  # "added", "removed", "modified"
    old_content: str
    new_content: str
    change_summary: str
    timestamp: str
    confidence: float = 1.0


@dataclass
class ResearchSnapshot:
    """研究快照"""
    query: str
    content_hash: str
    content: str
    sources: list[str]
    timestamp: str
    key_findings: list[str] = field(default_factory=list)


class IncrementalResearchTracker:
    """
    增量研究追踪器。

    功能：
    - 缓存研究结果
    - 检测内容变化
    - 生成变更摘要
    - 触发更新通知

    Usage:
        tracker = IncrementalResearchTracker()
        tracker.save_research("AI trends", report_content, sources)

        # 在下次研究时检查变化
        changes = tracker.check_changes("AI trends", new_content)
        if changes:
            notify_user(changes)
    """

    DEFAULT_TTL = 86400 * 7  # 7天

    def __init__(self, ttl_seconds: int = None):
        self.ttl = ttl_seconds or self.DEFAULT_TTL
        self.snapshots: dict[str, ResearchSnapshot] = {}
        self.change_history: dict[str, list[ContentChange]] = {}

    def save_research(
        self,
        query: str,
        content: str,
        sources: list[str] = None,
        key_findings: list[str] = None,
    ):
        """
        保存研究快照。

        Args:
            query: 研究查询
            content: 研究内容
            sources: 来源URL列表
            key_findings: 关键发现列表
        """
        normalized_query = self._normalize_query(query)

        snapshot = ResearchSnapshot(
            query=query,
            content_hash=self._hash_content(content),
            content=content,
            sources=sources or [],
            timestamp=datetime.now().isoformat(),
            key_findings=key_findings or [],
        )

        self.snapshots[normalized_query] = snapshot

    def check_changes(
        self,
        query: str,
        new_content: str,
    ) -> list[ContentChange]:
        """
        检查研究内容是否有变化。

        Args:
            query: 研究查询
            new_content: 新内容

        Returns:
            List of detected changes
        """
        normalized_query = self._normalize_query(query)

        if normalized_query not in self.snapshots:
            return []  # 没有旧快照，无法比较

        old_snapshot = self.snapshots[normalized_query]
        new_hash = self._hash_content(new_content)

        # 检查是否有变化
        if old_snapshot.content_hash == new_hash:
            return []  # 内容相同

        # 检测变化
        changes = self._detect_changes(
            query=query,
            old_content=old_snapshot.content,
            new_content=new_content,
        )

        # 记录变化历史
        if normalized_query not in self.change_history:
            self.change_history[normalized_query] = []
        self.change_history[normalized_query].extend(changes)

        return changes

    def get_update_summary(self, query: str, new_content: str) -> str:
        """
        获取更新摘要（人类可读格式）。

        Args:
            query: 研究查询
            new_content: 新内容

        Returns:
            Markdown格式的更新摘要
        """
        changes = self.check_changes(query, new_content)

        if not changes:
            return "✅ 无变化，上次研究结果仍然有效。"

        lines = ["## 研究更新摘要\n"]

        for i, change in enumerate(changes, 1):
            if change.change_type == "modified":
                lines.append(f"### 更新 {i}: 内容修改\n")
                lines.append(f"- 摘要: {change.change_summary}\n")
            elif change.change_type == "added":
                lines.append(f"### 新增内容\n")
                lines.append(f"- {change.change_summary}\n")

        lines.append(f"\n*检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

        return "\n".join(lines)

    def get_snapshot(self, query: str) -> Optional[ResearchSnapshot]:
        """获取研究快照。"""
        normalized = self._normalize_query(query)
        return self.snapshots.get(normalized)

    def is_cache_valid(self, query: str) -> bool:
        """检查缓存是否有效。"""
        snapshot = self.get_snapshot(query)
        if not snapshot:
            return False

        try:
            snapshot_time = datetime.fromisoformat(snapshot.timestamp)
            age_seconds = (datetime.now() - snapshot_time).total_seconds()
            return age_seconds < self.ttl
        except (ValueError, TypeError):
            return False

    def get_cache_age(self, query: str) -> Optional[int]:
        """获取缓存年龄（小时）。"""
        snapshot = self.get_snapshot(query)
        if not snapshot:
            return None

        try:
            snapshot_time = datetime.fromisoformat(snapshot.timestamp)
            age_seconds = (datetime.now() - snapshot_time).total_seconds()
            return int(age_seconds / 3600)
        except (ValueError, TypeError):
            return None

    def clear_cache(self, query: str = None):
        """清除缓存。"""
        if query:
            normalized = self._normalize_query(query)
            if normalized in self.snapshots:
                del self.snapshots[normalized]
            if normalized in self.change_history:
                del self.change_history[normalized]
        else:
            self.snapshots.clear()
            self.change_history.clear()

    def _normalize_query(self, query: str) -> str:
        """标准化查询（用于字典键）。"""
        return query.strip().lower()[:100]

    def _hash_content(self, content: str) -> str:
        """生成内容哈希。"""
        return hashlib.md5(content.encode()).hexdigest()

    def _detect_changes(
        self,
        query: str,
        old_content: str,
        new_content: str,
    ) -> list[ContentChange]:
        """检测内容变化。"""
        changes = []

        # 计算相似度
        similarity = difflib.SequenceMatcher(
            None,
            old_content[:1000],
            new_content[:1000]
        ).ratio()

        # 简单变化检测
        if similarity < 0.9:
            # 内容有显著变化
            changes.append(ContentChange(
                query=query,
                change_type="modified",
                old_content=old_content[:500],
                new_content=new_content[:500],
                change_summary=self._summarize_change(old_content, new_content),
                timestamp=datetime.now().isoformat(),
                confidence=1.0 - similarity,
            ))

        return changes

    def _summarize_change(self, old: str, new: str) -> str:
        """生成变化摘要。"""
        # 简单实现：比较长度变化
        old_len = len(old)
        new_len = len(new)
        diff_pct = abs(new_len - old_len) / max(old_len, 1) * 100

        if new_len > old_len:
            return f"内容增加约 {diff_pct:.0f}%"
        else:
            return f"内容减少约 {diff_pct:.0f}%"


class ResearchChangeNotifier:
    """
    研究变化通知器。

    集成到研究流程中，当检测到变化时通知用户。
    """

    def __init__(self, tracker: IncrementalResearchTracker):
        self.tracker = tracker
        self.listeners: list[Callable[[ContentChange], None]] = []

    def subscribe(self, callback: Callable[[ContentChange], None]):
        """订阅变化通知。"""
        self.listeners.append(callback)

    def notify(self, change: ContentChange):
        """通知所有订阅者。"""
        for listener in self.listeners:
            try:
                listener(change)
            except Exception as e:
                print(f"Notification error: {e}")

    def check_and_notify(self, query: str, new_content: str):
        """检查变化并通知。"""
        changes = self.tracker.check_changes(query, new_content)
        for change in changes:
            self.notify(change)


# Example usage
if __name__ == "__main__":
    print("=== Incremental Research Test ===\n")

    tracker = IncrementalResearchTracker()

    # 保存初始研究
    initial_report = """
    ## AI发展趋势

    1. 生成式AI正在快速发展
    2. 大模型应用场景不断扩展
    3. 企业采用率持续提升

    结论：AI技术处于快速发展期。
    """
    tracker.save_research(
        query="AI trends 2026",
        content=initial_report,
        sources=["https://example.com/ai-trends"],
        key_findings=["生成式AI快速发展", "大模型应用扩展"]
    )

    print(f"已保存研究，快照数量: {len(tracker.snapshots)}")

    # 检查缓存状态
    is_valid = tracker.is_cache_valid("AI trends 2026")
    print(f"缓存有效: {is_valid}")

    # 模拟新内容（无变化）
    same_report = initial_report
    changes = tracker.check_changes("AI trends 2026", same_report)
    print(f"\n无变化测试: 检测到 {len(changes)} 个变化")

    # 模拟新内容（有变化）
    updated_report = """
    ## AI发展趋势

    1. 生成式AI正在快速发展
    2. 大模型应用场景不断扩展
    3. 企业采用率持续提升
    4. 多模态AI成为新热点

    结论：AI技术处于快速发展期，多模态成为新方向。
    """
    changes = tracker.check_changes("AI trends 2026", updated_report)
    print(f"\n有变化测试: 检测到 {len(changes)} 个变化")

    if changes:
        print(f"  变化类型: {changes[0].change_type}")
        print(f"  摘要: {changes[0].change_summary}")

    # 获取更新摘要
    summary = tracker.get_update_summary("AI trends 2026", updated_report)
    print("\n更新摘要:")
    print(summary)

    # 测试缓存年龄
    print(f"\n缓存年龄: {tracker.get_cache_age('AI trends 2026')} 小时")