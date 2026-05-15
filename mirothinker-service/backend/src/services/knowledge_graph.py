"""
MiroThinker - Knowledge Graph
NetworkX-based in-memory knowledge graph for entity-relationship modeling.
Zero-cost solution for multi-hop reasoning and causal chain traversal.
"""

from typing import Optional, list
from dataclasses import dataclass, field
from enum import Enum

try:
    import networkx as nx
except ImportError:
    nx = None


class EntityType(Enum):
    """Entity type classification."""
    PERSON = "person"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    EVENT = "event"
    LOCATION = "location"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    METRIC = "metric"
    UNKNOWN = "unknown"


class RelationType(Enum):
    """Relationship type classification."""
    CAUSES = "causes"
    ENABLES = "enables"
    INHIBITS = "inhibits"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    BELONGS_TO = "belongs_to"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    SIMILAR_TO = "similar_to"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Represents a knowledge graph entity."""
    id: str
    name: str
    entity_type: EntityType
    properties: dict = field(default_factory=dict)
    confidence: float = 1.0

    def __hash__(self):
        return hash(self.id)


@dataclass
class Relation:
    """Represents a relationship between entities."""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: dict = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)


class KnowledgeGraph:
    """
    In-memory knowledge graph using NetworkX.

    Features:
    - Entity extraction and storage
    - Relationship modeling
    - Multi-hop reasoning
    - Causal chain traversal
    - Subgraph extraction

    Usage:
        kg = KnowledgeGraph()
        kg.add_entity("AI", EntityType.CONCEPT)
        kg.add_entity("ML", EntityType.CONCEPT)
        kg.add_relation("AI", "ML", RelationType.ENABLES)
        paths = kg.find_paths("AI", "ML", max_hops=3)
    """

    def __init__(self):
        if nx is None:
            raise ImportError("networkx required: pip install networkx")

        self.graph = nx.DiGraph()
        self.entity_properties: dict[str, dict] = {}
        self.relation_evidence: dict[tuple, list[str]] = {}

    # === Entity Operations ===

    def add_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: EntityType = EntityType.UNKNOWN,
        properties: dict = None
    ) -> Entity:
        """
        Add an entity to the graph.

        Args:
            entity_id: Unique identifier
            name: Entity name
            entity_type: Entity type classification
            properties: Optional properties dict

        Returns:
            Created Entity object
        """
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            properties=properties or {}
        )

        self.graph.add_node(entity_id, **{
            "name": name,
            "type": entity_type.value,
            "properties": properties or {}
        })
        self.entity_properties[entity_id] = properties or {}

        return entity

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Get entity by ID."""
        if entity_id in self.graph.nodes:
            return self.graph.nodes[entity_id]
        return None

    def get_entities_by_type(self, entity_type: EntityType) -> list[dict]:
        """Get all entities of a specific type."""
        return [
            self.graph.nodes[node]
            for node in self.graph.nodes
            if self.graph.nodes[node].get("type") == entity_type.value
        ]

    def update_entity(self, entity_id: str, properties: dict):
        """Update entity properties."""
        if entity_id in self.graph.nodes:
            self.graph.nodes[entity_id]["properties"].update(properties)
            self.entity_properties[entity_id].update(properties)

    # === Relation Operations ===

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType = RelationType.RELATED_TO,
        weight: float = 1.0,
        evidence: list[str] = None,
        properties: dict = None
    ) -> Relation:
        """
        Add a relation between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship
            weight: Relation weight (0-1)
            evidence: List of evidence texts
            properties: Optional properties

        Returns:
            Created Relation object
        """
        relation = Relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            evidence=evidence or [],
            properties=properties or {}
        )

        # Add edge to graph
        self.graph.add_edge(
            source_id,
            target_id,
            type=relation_type.value,
            weight=weight,
            evidence=evidence or [],
            properties=properties or {}
        )

        # Store evidence by edge tuple
        edge = (source_id, target_id)
        if edge not in self.relation_evidence:
            self.relation_evidence[edge] = []
        if evidence:
            self.relation_evidence[edge].extend(evidence)

        return relation

    def get_relations(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> list[dict]:
        """
        Get relations for an entity.

        Args:
            entity_id: Entity ID
            direction: "out" (outgoing), "in" (incoming), or "both"

        Returns:
            List of relation dicts
        """
        relations = []

        if direction in ("out", "both"):
            for _, target, data in self.graph.out_edges(entity_id, data=True):
                relations.append({
                    "source": entity_id,
                    "target": target,
                    "type": data.get("type"),
                    "weight": data.get("weight", 1.0),
                    "direction": "out"
                })

        if direction in ("in", "both"):
            for source, _, data in self.graph.in_edges(entity_id, data=True):
                relations.append({
                    "source": source,
                    "target": entity_id,
                    "type": data.get("type"),
                    "weight": data.get("weight", 1.0),
                    "direction": "in"
                })

        return relations

    # === Query Operations ===

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 3
    ) -> list[list[str]]:
        """
        Find paths between two entities.

        Args:
            source_id: Start entity ID
            target_id: End entity ID
            max_hops: Maximum path length

        Returns:
            List of paths (each path is list of entity IDs)
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []

        try:
            # Use BFS for shortest path
            path = nx.shortest_path(self.graph, source_id, target_id)
            return [path]
        except nx.NetworkXNoPath:
            # Try to find all simple paths up to max_hops
            return list(nx.all_simple_paths(
                self.graph,
                source_id,
                target_id,
                cutoff=max_hops
            ))

    def find_hop_neighbors(
        self,
        entity_id: str,
        hops: int = 1,
        relation_type: RelationType = None
    ) -> list[str]:
        """
        Find entities within N hops.

        Args:
            entity_id: Starting entity
            hops: Number of hops
            relation_type: Optional filter by relation type

        Returns:
            List of entity IDs within N hops
        """
        if entity_id not in self.graph:
            return []

        neighbors = set()
        current = {entity_id}
        visited = {entity_id}

        for _ in range(hops):
            next_layer = set()
            for node in current:
                # Get neighbors based on relation type filter
                for _, neighbor, data in self.graph.out_edges(node, data=True):
                    if neighbor not in visited:
                        if relation_type is None or data.get("type") == relation_type.value:
                            neighbors.add(neighbor)
                            next_layer.add(neighbor)
                        visited.add(neighbor)

                # Also check incoming edges
                for predecessor, _, data in self.graph.in_edges(node, data=True):
                    if predecessor not in visited:
                        if relation_type is None or data.get("type") == relation_type.value:
                            neighbors.add(predecessor)
                            next_layer.add(predecessor)
                        visited.add(predecessor)

            current = next_layer

        return list(neighbors)

    def get_subgraph(
        self,
        entity_ids: list[str],
        depth: int = 1
    ) -> nx.DiGraph:
        """
        Get a subgraph centered on given entities.

        Args:
            entity_ids: Central entity IDs
            depth: Depth of connections to include

        Returns:
            Subgraph DiGraph
        """
        # Collect nodes within depth
        nodes_to_include = set(entity_ids)

        for entity_id in entity_ids:
            nodes_to_include.update(
                self.find_hop_neighbors(entity_id, hops=depth)
            )

        # Create subgraph
        return self.graph.subgraph(nodes_to_include).copy()

    def find_causal_chain(
        self,
        source_id: str,
        target_id: str
    ) -> list[dict]:
        """
        Find causal chains between two entities.

        Args:
            source_id: Start entity
            target_id: End entity

        Returns:
            List of causal chain steps with evidence
        """
        paths = self.find_paths(source_id, target_id, max_hops=5)

        chains = []
        for path in paths:
            chain = []
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]

                edge_data = self.graph.edges[source, target]
                evidence = self.relation_evidence.get(
                    (source, target),
                    edge_data.get("evidence", [])
                )

                chain.append({
                    "from": source,
                    "to": target,
                    "relation": edge_data.get("type"),
                    "weight": edge_data.get("weight", 1.0),
                    "evidence": evidence
                })

            chains.append(chain)

        return chains

    def query_by_keywords(self, keywords: list[str]) -> list[dict]:
        """
        Query entities by keyword matching.

        Args:
            keywords: List of keywords

        Returns:
            List of matching entities
        """
        results = []

        for node in self.graph.nodes:
            node_data = self.graph.nodes[node]
            name = node_data.get("name", "").lower()
            properties = str(node_data.get("properties", {})).lower()

            matches = sum(1 for kw in keywords if kw.lower() in name or kw.lower() in properties)

            if matches > 0:
                results.append({
                    "entity": node_data,
                    "relevance": matches / len(keywords)
                })

        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results

    # === Graph Analysis ===

    def get_stats(self) -> dict:
        """Get graph statistics."""
        return {
            "entity_count": self.graph.number_of_nodes(),
            "relation_count": self.graph.number_of_edges(),
            "entity_types": self._count_entity_types(),
            "relation_types": self._count_relation_types(),
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(1, self.graph.number_of_nodes()),
            "density": nx.density(self.graph)
        }

    def _count_entity_types(self) -> dict:
        """Count entities by type."""
        counts = {}
        for node in self.graph.nodes:
            entity_type = self.graph.nodes[node].get("type", "unknown")
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts

    def _count_relation_types(self) -> dict:
        """Count relations by type."""
        counts = {}
        for _, _, data in self.graph.edges(data=True):
            rel_type = data.get("type", "unknown")
            counts[rel_type] = counts.get(rel_type, 0) + 1
        return counts

    # === Serialization ===

    def to_dict(self) -> dict:
        """Export graph as dict."""
        return {
            "entities": [
                {"id": node, **self.graph.nodes[node]}
                for node in self.graph.nodes
            ],
            "relations": [
                {"source": u, "target": v, **d}
                for u, v, d in self.graph.edges(data=True)
            ]
        }

    def from_dict(self, data: dict):
        """Import graph from dict."""
        self.graph.clear()
        self.entity_properties.clear()
        self.relation_evidence.clear()

        for entity in data.get("entities", []):
            entity_id = entity.pop("id")
            self.add_entity(entity_id, **entity)

        for relation in data.get("relations", []):
            source = relation.pop("source")
            target = relation.pop("target")
            self.add_relation(source, target, **relation)

    def clear(self):
        """Clear all entities and relations."""
        self.graph.clear()
        self.entity_properties.clear()
        self.relation_evidence.clear()


# Example usage
if __name__ == "__main__":
    print("=== Knowledge Graph Test ===\n")

    kg = KnowledgeGraph()

    # Add entities
    kg.add_entity("AI", "人工智能", EntityType.CONCEPT)
    kg.add_entity("ML", "机器学习", EntityType.CONCEPT)
    kg.add_entity("DL", "深度学习", EntityType.CONCEPT)
    kg.add_entity("NLP", "自然语言处理", EntityType.TECHNOLOGY)
    kg.add_entity("CV", "计算机视觉", EntityType.TECHNOLOGY)
    kg.add_entity("AlphaFold", "AlphaFold", EntityType.PRODUCT)
    kg.add_entity("Google", "Google", EntityType.ORGANIZATION)

    # Add relations
    kg.add_relation("AI", "ML", RelationType.ENABLES, evidence=["AI enables ML development"])
    kg.add_relation("ML", "DL", RelationType.ENABLES, evidence=["ML enables DL"])
    kg.add_relation("DL", "NLP", RelationType.ENABLES, evidence=["DL powers NLP"])
    kg.add_relation("DL", "CV", RelationType.ENABLES, evidence=["DL powers CV"])
    kg.add_relation("DL", "AlphaFold", RelationType.CAUSES, evidence=["DL enables AlphaFold"])
    kg.add_relation("Google", "AlphaFold", RelationType.CREATES, evidence=["Google created AlphaFold"])

    # Stats
    print("Graph Stats:")
    stats = kg.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Find paths
    print("\nFind paths AI -> AlphaFold:")
    paths = kg.find_paths("AI", "AlphaFold", max_hops=5)
    print(f"Found {len(paths)} paths")
    for path in paths:
        print(f"  {' -> '.join(path)}")

    # Get neighbors
    print("\n1-hop neighbors of DL:")
    neighbors = kg.find_hop_neighbors("DL", hops=1)
    print(f"  {neighbors}")

    # Query
    print("\nQuery by 'learning':")
    results = kg.query_by_keywords(["learning"])
    for r in results:
        print(f"  {r['entity'].get('name')} (relevance: {r['relevance']:.2f})")