"""
MiroThinker - Research Memory Enhanced with Knowledge Graph
Adds NetworkX-based knowledge graph capabilities to ResearchMemory.
Enables causal chain traversal and multi-hop reasoning.
"""

from typing import Optional, list
from .research_memory import ResearchMemory as BaseResearchMemory
from .knowledge_graph import KnowledgeGraph, EntityType, RelationType


class ResearchMemoryEnhanced(BaseResearchMemory):
    """
    ResearchMemory with integrated KnowledgeGraph capabilities.

    Extends BaseResearchMemory with:
    - KnowledgeGraph integration for causal chain traversal
    - Entity-relation storage alongside findings
    - Multi-hop reasoning queries
    - Incremental graph updates

    Usage:
        memory = ResearchMemoryEnhanced()
        memory.set_session_metadata(query="AI trends", domain="tech")

        # Add findings (automatically updates graph)
        memory.add_finding(..., topic="AI发展")

        # Query graph
        paths = memory.find_causal_paths("AI", "Productivity")
        entities = memory.get_entities_by_type(EntityType.TECHNOLOGY)
    """

    def __init__(self, *args, **kwargs):
        """Initialize with KnowledgeGraph integration."""
        super().__init__(*args, **kwargs)
        # Initialize knowledge graph for entity-relation modeling
        self.knowledge_graph = KnowledgeGraph()
        # Map from finding IDs to entity IDs
        self._finding_to_entity: dict[str, str] = {}
        # Map from entity IDs to finding IDs
        self._entity_to_finding: dict[str, str] = {}

    def add_finding_with_entity(
        self,
        content: str,
        depth_level: int,
        topic: str,
        source_urls: list[str] = None,
        confidence: str = "推测",
        evidence_ids: list[str] = None,
        turn: int = 0,
        entities: list[dict] = None,
        relations: list[dict] = None,
    ):
        """
        Add a finding with associated entity-relation data.

        Args:
            entities: List of dicts with 'name', 'type' keys
            relations: List of dicts with 'source', 'target', 'type' keys
        """
        # Add the finding (parent method)
        finding = super().add_finding(
            content=content,
            depth_level=depth_level,
            topic=topic,
            source_urls=source_urls,
            confidence=confidence,
            evidence_ids=evidence_ids,
            turn=turn,
        )

        # Add entities to knowledge graph
        if entities:
            for ent in entities:
                entity_id = self._normalize_entity_id(ent.get("name", ""))
                entity_type = self._parse_entity_type(ent.get("type", "concept"))

                self.knowledge_graph.add_entity(
                    entity_id=entity_id,
                    name=ent.get("name", ""),
                    entity_type=entity_type,
                    properties={
                        "finding_id": finding.id,
                        "description": ent.get("description", ""),
                        "source_urls": source_urls or [],
                    }
                )
                self._entity_to_finding[entity_id] = finding.id
                self._finding_to_entity[finding.id] = entity_id

        # Add relations to knowledge graph
        if relations:
            for rel in relations:
                source_id = self._normalize_entity_id(rel.get("source", ""))
                target_id = self._normalize_entity_id(rel.get("target", ""))
                rel_type = self._parse_relation_type(rel.get("type", "related_to"))

                # Only add if both entities exist
                if self.knowledge_graph.get_entity(source_id) and self.knowledge_graph.get_entity(target_id):
                    self.knowledge_graph.add_relation(
                        source_id=source_id,
                        target_id=target_id,
                        relation_type=rel_type,
                        weight=0.8,
                        evidence=[f"From finding {finding.id}: {content[:100]}"],
                    )

        return finding

    def add_causal_chain_with_graph(
        self,
        title: str,
        steps: list[dict],
        strength: str = "中等",
    ):
        """
        Add a causal chain and build graph connections.

        Also creates graph edges for causal relationships.
        """
        chain = super().add_causal_chain(title=title, steps=steps, strength=strength)

        # Build graph edges for causal chain
        for i in range(len(steps) - 1):
            source_step = steps[i]
            target_step = steps[i + 1]

            source_id = self._normalize_entity_id(source_step.get("finding_id", f"step_{i}"))
            target_id = self._normalize_entity_id(target_step.get("finding_id", f"step_{i + 1}"))

            # Add nodes if they don't exist
            if not self.knowledge_graph.get_entity(source_id):
                self.knowledge_graph.add_entity(
                    entity_id=source_id,
                    name=f"因果节点: {source_step.get('finding_id', '')}",
                    entity_type=EntityType.CONCEPT,
                )

            if not self.knowledge_graph.get_entity(target_id):
                self.knowledge_graph.add_entity(
                    entity_id=target_id,
                    name=f"因果节点: {target_step.get('finding_id', '')}",
                    entity_type=EntityType.CONCEPT,
                )

            # Add causal relation
            self.knowledge_graph.add_relation(
                source_id=source_id,
                target_id=target_id,
                relation_type=RelationType.CAUSES,
                weight=1.0 if strength == "强" else 0.7,
                evidence=[f"Causal chain: {title}"],
            )

        return chain

    def find_causal_paths(
        self,
        entity1: str,
        entity2: str,
        max_hops: int = 3,
    ) -> list[dict]:
        """
        Find causal paths between two entities.

        Args:
            entity1: Start entity name or ID
            entity2: End entity name or ID
            max_hops: Maximum path length

        Returns:
            List of path dicts with entities and relations
        """
        id1 = self._normalize_entity_id(entity1)
        id2 = self._normalize_entity_id(entity2)

        paths = self.knowledge_graph.find_paths(id1, id2, max_hops)

        # Convert to readable format
        readable_paths = []
        for path in paths:
            steps = []
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]

                entity_data = self.knowledge_graph.get_entity(source)
                steps.append({
                    "from": entity_data.get("name", source) if entity_data else source,
                    "from_id": source,
                    "relation": "causes",
                    "to": target,
                    "to_id": path[i + 1],
                })
            readable_paths.append({"steps": steps, "hop_count": len(path) - 1})

        return readable_paths

    def get_hop_neighbors(self, entity: str, hops: int = 1) -> list[dict]:
        """
        Get entities within N hops of a given entity.

        Args:
            entity: Entity name or ID
            hops: Number of hops

        Returns:
            List of neighboring entities with relation info
        """
        entity_id = self._normalize_entity_id(entity)

        neighbor_ids = self.knowledge_graph.find_hop_neighbors(entity_id, hops=hops)

        results = []
        for neighbor_id in neighbor_ids:
            entity_data = self.knowledge_graph.get_entity(neighbor_id)
            relations = self.knowledge_graph.get_relations(neighbor_id)

            results.append({
                "entity": entity_data,
                "id": neighbor_id,
                "relations": relations,
            })

        return results

    def query_by_keywords(self, keywords: list[str]) -> list[dict]:
        """
        Query entities and findings by keywords.

        Args:
            keywords: List of keywords to search

        Returns:
            Combined results from graph and memory
        """
        # Query knowledge graph
        graph_results = self.knowledge_graph.query_by_keywords(keywords)

        # Query findings
        findings_results = []
        for kw in keywords:
            for f in self.findings:
                if kw.lower() in f.content.lower() or kw.lower() in f.topic.lower():
                    findings_results.append({
                        "finding": f,
                        "relevance": 1.0,
                    })

        # Merge and deduplicate
        all_results = []

        for gr in graph_results:
            all_results.append({
                "type": "entity",
                "entity": gr["entity"],
                "relevance": gr["relevance"],
            })

        for fr in findings_results:
            # Check if finding already included via entity
            finding_id = fr["finding"].id
            if finding_id not in self._finding_to_entity:
                all_results.append({
                    "type": "finding",
                    "finding": fr["finding"],
                    "relevance": fr["relevance"],
                })

        return all_results

    def get_entities_by_type(self, entity_type: EntityType) -> list[dict]:
        """Get all entities of a specific type."""
        return self.knowledge_graph.get_entities_by_type(entity_type)

    def get_graph_stats(self) -> dict:
        """Get combined stats for memory and graph."""
        base_stats = {
            "finding_count": len(self.findings),
            "causal_chain_count": len(self.causal_chains),
            "hypothesis_count": len(self.hypotheses),
            "evidence_count": sum(len(ev) for ev in self.evidence_map.values()),
            "question_count": len(self.open_questions),
        }

        graph_stats = self.knowledge_graph.get_stats()

        return {
            **base_stats,
            **graph_stats,
            "entity_finding_links": len(self._finding_to_entity),
        }

    def export_with_graph(self) -> dict:
        """Export complete state including graph."""
        snapshot = self.to_session_snapshot()
        snapshot["knowledge_graph"] = self.knowledge_graph.to_dict()
        snapshot["entity_finding_mapping"] = {
            "finding_to_entity": self._finding_to_entity,
            "entity_to_finding": self._entity_to_finding,
        }
        return snapshot

    def import_from_snapshot(self, snapshot: dict):
        """Import state from snapshot including graph."""
        # Import base memory state
        self.findings = [
            self._dict_to_finding(f) for f in snapshot.get("findings", [])
        ]
        self.causal_chains = [
            self._dict_to_causal_chain(cc) for cc in snapshot.get("causal_chains", [])
        ]
        self.hypotheses = [
            self._dict_to_hypothesis(h) for h in snapshot.get("hypotheses", [])
        ]
        self.main_threads = [
            self._dict_to_main_thread(mt) for mt in snapshot.get("main_threads", [])
        ]

        # Import knowledge graph
        kg_data = snapshot.get("knowledge_graph", {})
        self.knowledge_graph.from_dict(kg_data)

        # Import entity-finding mapping
        mapping = snapshot.get("entity_finding_mapping", {})
        self._finding_to_entity = mapping.get("finding_to_entity", {})
        self._entity_to_finding = mapping.get("entity_to_finding", {})

    # === Helper methods ===

    @staticmethod
    def _normalize_entity_id(name: str) -> str:
        """Normalize entity name to ID."""
        import re
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)
        return normalized.lower()[:50]

    @staticmethod
    def _parse_entity_type(type_str: str) -> EntityType:
        """Parse entity type string."""
        type_map = {
            "person": EntityType.PERSON, "人物": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION, "组织": EntityType.ORGANIZATION,
            "concept": EntityType.CONCEPT, "概念": EntityType.CONCEPT,
            "event": EntityType.EVENT, "事件": EntityType.EVENT,
            "location": EntityType.LOCATION, "地点": EntityType.LOCATION,
            "product": EntityType.PRODUCT, "产品": EntityType.PRODUCT,
            "technology": EntityType.TECHNOLOGY, "技术": EntityType.TECHNOLOGY,
            "metric": EntityType.METRIC, "指标": EntityType.METRIC,
        }
        return type_map.get(type_str.lower(), EntityType.UNKNOWN)

    @staticmethod
    def _parse_relation_type(type_str: str) -> RelationType:
        """Parse relation type string."""
        type_map = {
            "causes": RelationType.CAUSES, "导致": RelationType.CAUSES,
            "enables": RelationType.ENABLES, "促进": RelationType.ENABLES,
            "inhibits": RelationType.INHIBITS, "抑制": RelationType.INHIBITS,
            "related_to": RelationType.RELATED_TO, "相关": RelationType.RELATED_TO,
            "part_of": RelationType.PART_OF, "属于": RelationType.PART_OF,
            "precedes": RelationType.PRECEDES, "先于": RelationType.PRECEDES,
            "similar_to": RelationType.SIMILAR_TO, "相似": RelationType.SIMILAR_TO,
            "contradicts": RelationType.CONTRADICTS, "矛盾": RelationType.CONTRADICTS,
        }
        return type_map.get(type_str.lower(), RelationType.UNKNOWN)

    # === Type conversion helpers ===

    @staticmethod
    def _dict_to_finding(d: dict):
        """Convert dict to Finding (import helper)."""
        from dataclasses import replace
        from .research_memory import Finding

        return Finding(
            id=d["id"], content=d["content"], depth_level=d["depth_level"],
            evidence_ids=d.get("evidence_ids", []), source_urls=d.get("source_urls", []),
            topic=d.get("topic", ""), confidence=d.get("confidence", "推测"),
            created_turn=d.get("created_turn", 0),
        )

    @staticmethod
    def _dict_to_causal_chain(d: dict):
        """Convert dict to CausalChain (import helper)."""
        from .research_memory import CausalChain, CausalStep

        return CausalChain(
            id=d["id"], title=d["title"], strength=d.get("strength", "中等"),
            steps=[CausalStep(**s) for s in d.get("steps", [])],
        )

    @staticmethod
    def _dict_to_hypothesis(d: dict):
        """Convert dict to Hypothesis (import helper)."""
        from .research_memory import Hypothesis

        return Hypothesis(
            id=d["id"], statement=d["statement"], status=d.get("status", "待验证"),
            priority=d.get("priority", "medium"),
            supporting_evidence=d.get("supporting_evidence", []),
            contradicting_evidence=d.get("contradicting_evidence", []),
        )

    @staticmethod
    def _dict_to_main_thread(d: dict):
        """Convert dict to MainThread (import helper)."""
        from .research_memory import MainThread

        return MainThread(
            id=d["id"], title=d["title"], target_depth=d.get("target_depth", 3),
            current_depth=d.get("current_depth", 0),
            finding_sequence=d.get("finding_sequence", []),
        )


# Example usage
if __name__ == "__main__":
    print("=== ResearchMemory Enhanced Test ===\n")

    memory = ResearchMemoryEnhanced()
    memory.set_session_metadata(query="AI impact on productivity", domain="tech")

    # Add findings with entity data
    memory.add_finding_with_entity(
        content="AI技术在各行业提升生产效率30%以上",
        depth_level=1,
        topic="AI发展",
        source_urls=["https://example.com/ai-productivity"],
        confidence="已确认",
        entities=[
            {"name": "AI", "type": "technology"},
            {"name": "生产效率", "type": "metric"},
        ],
        relations=[
            {"source": "AI", "target": "生产效率", "type": "causes"},
        ],
        turn=1,
    )

    memory.add_finding_with_entity(
        content="深度学习推动计算机视觉准确率突破95%",
        depth_level=2,
        topic="深度学习",
        source_urls=["https://example.com/dl-vision"],
        confidence="已确认",
        entities=[
            {"name": "深度学习", "type": "technology"},
            {"name": "计算机视觉", "type": "technology"},
        ],
        relations=[
            {"source": "深度学习", "target": "计算机视觉", "type": "enables"},
        ],
        turn=2,
    )

    # Add causal chain
    memory.add_causal_chain_with_graph(
        title="AI技术→效率提升→行业变革",
        steps=[
            {"finding_id": "深度学习", "reasoning": "深度学习技术发展"},
            {"finding_id": "计算机视觉", "reasoning": "推动计算机视觉进步"},
            {"finding_id": "生产效率", "reasoning": "提升整体生产效率"},
        ],
        strength="强",
    )

    # Stats
    print("Memory + Graph Stats:")
    stats = memory.get_graph_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Query
    print("\nQuery 'AI':")
    results = memory.query_by_keywords(["AI"])
    for r in results:
        print(f"  - {r['type']}: {r.get('entity', {}).get('name') or r.get('finding', {}).content[:50]}")

    # Find paths
    print("\nFind paths AI -> 生产效率:")
    paths = memory.find_causal_paths("AI", "生产效率")
    print(f"  Found {len(paths)} paths")
    for p in paths:
        print(f"    Steps: {[s['from'] for s in p['steps']]}")