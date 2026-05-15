"""
MiroThinker - Entity Extractor
Uses Bailian LLM (qwen-plus) for entity and relation extraction.
Part of Phase 2 Knowledge Enhancement.
"""

from typing import Optional, list
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .knowledge_graph import KnowledgeGraph, EntityType, RelationType


class BailianEntityExtractor:
    """
    Entity and relation extraction using Bailian LLM.

    Features:
    - Named entity recognition (NER)
    - Relation extraction between entities
    - Type classification
    - Confidence scoring

    Usage:
        extractor = BailianEntityExtractor()
        kg = extractor.extract_from_text(text)
        entities = kg.get_entities_by_type(EntityType.ORGANIZATION)
    """

    MODEL = "qwen-plus"
    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Bailian API."""
        if OpenAI is None:
            raise ImportError("openai package required: pip install openai")

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not set")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL
        )

    def extract(self, text: str, max_entities: int = 20) -> KnowledgeGraph:
        """
        Extract entities and relations from text.

        Args:
            text: Input text for extraction
            max_entities: Maximum number of entities to extract

        Returns:
            KnowledgeGraph with extracted entities and relations
        """
        kg = KnowledgeGraph()

        prompt = self._build_extraction_prompt(text, max_entities)

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "你是一个实体关系抽取专家。请从文本中抽取实体和关系。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            self._parse_extraction_result(kg, result_text, text)

        except Exception as e:
            print(f"Extraction error: {e}")

        return kg

    def _build_extraction_prompt(self, text: str, max_entities: int) -> str:
        """Build extraction prompt."""
        return f"""请从以下文本中抽取实体和关系，并以JSON格式输出：

文本：
{text[:3000]}

请输出以下JSON格式（不要添加其他内容）：
{{
  "entities": [
    {{"name": "实体名称", "type": "person/organization/concept/event/location/product/technology/metric", "description": "简单描述"}},
    ...
  ],
  "relations": [
    {{"source": "实体A", "target": "实体B", "type": "causes/enables/inhibits/related_to/part_of/precedes/similar_to/contradicts", "evidence": "文本中的证据"}},
    ...
  ]
}}

实体数量不超过{max_entities}个。
请仅输出JSON，不要添加任何解释。
"""

    def _parse_extraction_result(self, kg: KnowledgeGraph, result_text: str, source_text: str):
        """Parse LLM response into knowledge graph."""
        import json
        import re

        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if not json_match:
            return

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return

        # Add entities
        entity_map = {}
        for ent_data in data.get("entities", []):
            entity_id = self._normalize_id(ent_data.get("name", ""))
            entity_type = self._parse_entity_type(ent_data.get("type", "unknown"))

            kg.add_entity(
                entity_id=entity_id,
                name=ent_data.get("name", ""),
                entity_type=entity_type,
                properties={"description": ent_data.get("description", "")}
            )
            entity_map[ent_data.get("name", "")] = entity_id

        # Add relations
        for rel_data in data.get("relations", []):
            source_name = rel_data.get("source", "")
            target_name = rel_data.get("target", "")

            if source_name in entity_map and target_name in entity_map:
                rel_type = self._parse_relation_type(rel_data.get("type", "related_to"))
                kg.add_relation(
                    source_id=entity_map[source_name],
                    target_id=entity_map[target_name],
                    relation_type=rel_type,
                    weight=0.8,
                    evidence=[rel_data.get("evidence", "")]
                )

    def _normalize_id(self, name: str) -> str:
        """Normalize entity name to ID."""
        import re
        # Remove special chars, lowercase
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)
        return normalized.lower()[:50]

    def _parse_entity_type(self, type_str: str) -> EntityType:
        """Parse entity type string."""
        type_map = {
            "person": EntityType.PERSON,
            "人物": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "组织": EntityType.ORGANIZATION,
            "公司": EntityType.ORGANIZATION,
            "concept": EntityType.CONCEPT,
            "概念": EntityType.CONCEPT,
            "event": EntityType.EVENT,
            "事件": EntityType.EVENT,
            "location": EntityType.LOCATION,
            "地点": EntityType.LOCATION,
            "product": EntityType.PRODUCT,
            "产品": EntityType.PRODUCT,
            "technology": EntityType.TECHNOLOGY,
            "技术": EntityType.TECHNOLOGY,
            "metric": EntityType.METRIC,
            "指标": EntityType.METRIC,
        }
        return type_map.get(type_str.lower(), EntityType.UNKNOWN)

    def _parse_relation_type(self, type_str: str) -> RelationType:
        """Parse relation type string."""
        type_map = {
            "causes": RelationType.CAUSES,
            "导致": RelationType.CAUSES,
            "enables": RelationType.ENABLES,
            "促进": RelationType.ENABLES,
            "inhibits": RelationType.INHIBITS,
            "抑制": RelationType.INHIBITS,
            "related_to": RelationType.RELATED_TO,
            "相关": RelationType.RELATED_TO,
            "part_of": RelationType.PART_OF,
            "属于": RelationType.PART_OF,
            "precedes": RelationType.PRECEDES,
            "先于": RelationType.PRECEDES,
            "similar_to": RelationType.SIMILAR_TO,
            "相似": RelationType.SIMILAR_TO,
            "contradicts": RelationType.CONTRADICTS,
            "矛盾": RelationType.CONTRADICTS,
        }
        return type_map.get(type_str.lower(), RelationType.UNKNOWN)


class EntityExtractorWithMemory:
    """
    Entity extractor with incremental memory.
    Accumulates knowledge across research sessions.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.extractor = BailianEntityExtractor(api_key)
        self.memory_graph = KnowledgeGraph()

    def extract_and_merge(self, text: str, source: str = "") -> KnowledgeGraph:
        """
        Extract entities and merge into cumulative memory.

        Args:
            text: New text to extract from
            source: Source identifier (e.g., URL)

        Returns:
            Updated knowledge graph with new entities merged
        """
        # Extract from new text
        new_kg = self.extractor.extract(text)

        # Merge into memory
        for node in new_kg.graph.nodes:
            node_data = new_kg.graph.nodes[node]
            # Check if entity already exists
            if self.memory_graph.get_entity(node) is None:
                self.memory_graph.add_entity(
                    entity_id=node,
                    name=node_data.get("name", node),
                    entity_type=EntityType[node_data.get("type", "UNKNOWN").upper()],
                    properties={**node_data.get("properties", {}), "source": source}
                )

        # Merge relations
        for source, target, data in new_kg.graph.edges(data=True):
            if not self.memory_graph.graph.has_edge(source, target):
                rel_type = RelationType[data.get("type", "RELATED_TO").upper()]
                self.memory_graph.add_relation(
                    source_id=source,
                    target_id=target,
                    relation_type=rel_type,
                    evidence=[source]
                )

        return self.memory_graph

    def query_entities(self, keywords: list[str]) -> list[dict]:
        """Query memory by keywords."""
        return self.memory_graph.query_by_keywords(keywords)

    def find_paths(self, entity1: str, entity2: str, max_hops: int = 3) -> list[list[str]]:
        """Find paths between entities in memory."""
        return self.memory_graph.find_paths(entity1, entity2, max_hops)

    def get_stats(self) -> dict:
        """Get memory statistics."""
        return self.memory_graph.get_stats()


# Example usage
if __name__ == "__main__":
    import os

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("DASHSCOPE_API_KEY not set, skipping live test")
    else:
        print("=== Entity Extraction Test ===\n")

        extractor = BailianEntityExtractor(api_key)

        test_text = """
        人工智能（AI）技术正在快速发展。机器学习（ML）是AI的核心组成部分，
        深度学习（DL）作为ML的子领域，在计算机视觉和自然语言处理领域取得突破。
        Google开发的AlphaFold在蛋白质结构预测领域取得重大进展。
        这些技术正在被广泛应用于医疗、金融、教育等行业。
        """

        print("Extracting entities...")
        kg = extractor.extract(test_text)

        print(f"\nExtracted {kg.graph.number_of_nodes()} entities")
        print(f"Extracted {kg.graph.number_of_edges()} relations")

        print("\nEntities:")
        for node in kg.graph.nodes:
            data = kg.graph.nodes[node]
            print(f"  - {data.get('name')} ({data.get('type')})")

        print("\nRelations:")
        for u, v, data in kg.graph.edges(data=True):
            print(f"  - {u} --[{data.get('type')}]--> {v}")

        print("\nStats:", kg.get_stats())