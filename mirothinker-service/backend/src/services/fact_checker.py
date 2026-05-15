"""
MiroThinker - Bailian Fact Checker
Zero-cost fact verification using qwen-flash.
Supports both numeric and qualitative claim verification.
"""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class VerificationStatus(Enum):
    """Verification result status."""
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


@dataclass
class VerificationResult:
    """Result of fact verification."""
    status: VerificationStatus
    claim: str
    verdict: str
    details: str
    confidence: float
    sources: list[str]
    suggestions: str = ""

    def format_markdown(self) -> str:
        """Format result as markdown."""
        status_icon = {
            VerificationStatus.VERIFIED: "✅",
            VerificationStatus.CONTRADICTED: "❌",
            VerificationStatus.UNCERTAIN: "❓",
            VerificationStatus.UNSUPPORTED: "⚠️",
            VerificationStatus.ERROR: "🚫"
        }.get(self.status, "❓")

        lines = [
            f"### {status_icon} {self.status.value.upper()}\n",
            f"**声明**: {self.claim}\n",
            f"**判断**: {self.verdict}\n",
            f"**置信度**: {self.confidence:.0%}\n",
            f"**详情**: {self.details}\n",
        ]

        if self.sources:
            lines.append(f"**参考来源**: {', '.join(self.sources)}\n")

        if self.suggestions:
            lines.append(f"**建议**: {self.suggestions}\n")

        return "\n".join(lines)


class BailianFactChecker:
    """
    Fact verification using Bailian (qwen-flash).

    Features:
    - Claim verification (supports/ncontradicts)
    - Numeric claim validation
    - Qualitative claim analysis
    - Source citation checking

    Usage:
        checker = BailianFactChecker(api_key="your-key")
        result = checker.verify("AI market will grow 25% in 2024", context="AI industry")
    """

    MODEL = "qwen-flash"
    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Pricing
    PRICE_PER_1K_TOKENS = 0.2  # ¥0.2 per 1000 tokens (very cheap)

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: DASHSCOPE_API_KEY. Falls back to env var.
        """
        if OpenAI is None:
            raise ImportError("openai package required: pip install openai")

        import os
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not set")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL
        )

    def verify(
        self,
        claim: str,
        context: str = None,
        sources: list[str] = None
    ) -> VerificationResult:
        """
        Verify a claim against provided context/sources.

        Args:
            claim: The claim to verify
            context: Optional context information
            sources: Optional list of source URLs or text

        Returns:
            VerificationResult with status, verdict, and confidence
        """
        prompt = self._build_verification_prompt(claim, context, sources)

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "你是一个事实核查专家。请根据提供的信息核查声明的准确性。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            return self._parse_verification_result(claim, result_text, sources)

        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                claim=claim,
                verdict="验证失败",
                details=str(e),
                confidence=0.0,
                sources=sources or []
            )

    def verify_batch(
        self,
        claims: list[str],
        contexts: list[str] = None,
        sources_list: list[list[str]] = None
    ) -> list[VerificationResult]:
        """
        Verify multiple claims in batch.

        Args:
            claims: List of claims to verify
            contexts: Optional list of contexts (one per claim)
            sources_list: Optional list of sources (one per claim)

        Returns:
            List of VerificationResults
        """
        results = []
        for i, claim in enumerate(claims):
            context = contexts[i] if contexts and i < len(contexts) else None
            sources = sources_list[i] if sources_list and i < len(sources_list) else None

            result = self.verify(claim, context, sources)
            results.append(result)

        return results

    def _build_verification_prompt(
        self,
        claim: str,
        context: Optional[str],
        sources: list[str] = None
    ) -> str:
        """Build verification prompt."""
        prompt = f"""请核查以下声明的准确性：

声明：{claim}
"""

        if context:
            prompt += f"\n背景信息：{context}\n"

        if sources:
            prompt += f"\n参考来源：\n"
            for i, source in enumerate(sources, 1):
                prompt += f"{i}. {source}\n"

        prompt += """
请输出以下格式的核查结果：
1. 状态：verified（已证实）/ contradicted（已证伪）/ uncertain（不确定）/ unsupported（信息不足）
2. 判断：简要的核查结论
3. 置信度：0-100%
4. 详情：详细的核查说明
5. 建议：后续行动建议（如需要）

请用中文回复。
"""
        return prompt

    def _parse_verification_result(
        self,
        claim: str,
        result_text: str,
        sources: list[str] = None
    ) -> VerificationResult:
        """Parse LLM response into structured result."""
        # Simple keyword matching for status
        status = VerificationStatus.UNCERTAIN
        if "已证实" in result_text or "verified" in result_text.lower():
            status = VerificationStatus.VERIFIED
        elif "已证伪" in result_text or "contradicted" in result_text.lower():
            status = VerificationStatus.CONTRADICTED
        elif "信息不足" in result_text or "unsupported" in result_text.lower():
            status = VerificationStatus.UNSUPPORTED

        # Extract confidence
        confidence = 0.5
        conf_match = re.search(r'(\d+)%', result_text)
        if conf_match:
            confidence = int(conf_match.group(1)) / 100

        # Extract verdict
        verdict = "无法确定"
        for line in result_text.split('\n'):
            if '判断' in line or '结论' in line:
                verdict = line.split('：')[-1].split('：')[-1].strip()
                break

        # Extract details
        details = result_text

        # Extract suggestions
        suggestions = ""
        if '建议' in result_text:
            parts = result_text.split('建议')
            if len(parts) > 1:
                suggestions = parts[1].strip()

        return VerificationResult(
            status=status,
            claim=claim,
            verdict=verdict,
            details=details,
            confidence=confidence,
            sources=sources or [],
            suggestions=suggestions
        )

    def verify_numeric_claim(
        self,
        claim: str,
        expected_range: tuple[float, float] = None
    ) -> VerificationResult:
        """
        Verify a numeric claim.

        Args:
            claim: Numeric claim like "X increased by 25%"
            expected_range: Optional (min, max) tuple for expected value

        Returns:
            VerificationResult
        """
        # First try structured verification
        result = self.verify(claim)

        # If uncertain and expected range provided, do numeric check
        if result.status == VerificationStatus.UNCERTAIN and expected_range:
            # Extract numbers from claim
            numbers = re.findall(r'[-+]?\d+(?:\.\d+)?', claim)
            if numbers:
                try:
                    value = float(numbers[0])
                    if expected_range[0] <= value <= expected_range[1]:
                        result.status = VerificationStatus.VERIFIED
                        result.verdict = f"数值在预期范围内 ({expected_range[0]}-{expected_range[1]})"
                        result.confidence = 0.8
                    else:
                        result.status = VerificationStatus.CONTRADICTED
                        result.verdict = f"数值超出预期范围 ({expected_range[0]}-{expected_range[1]})"
                        result.confidence = 0.8
                except ValueError:
                    pass

        return result

    def estimate_cost(self, claim: str) -> float:
        """Estimate cost for verification."""
        tokens = len(claim) / 4  # Rough estimate
        return tokens / 1000 * self.PRICE_PER_1K_TOKENS


class InlineFactChecker:
    """
    Inline fact checker for research output enhancement.
    Can be integrated into the research pipeline.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.checker = BailianFactChecker(api_key)

    def check_claims_in_text(
        self,
        text: str,
        min_confidence: float = 0.6
    ) -> list[VerificationResult]:
        """
        Check all fact-like claims in text.

        Args:
            text: Research output text
            min_confidence: Minimum confidence threshold for flagging issues

        Returns:
            List of verification results for flagged claims
        """
        # Extract potential claims (sentences with numbers or strong statements)
        claims = self._extract_claims(text)

        results = []
        for claim in claims:
            result = self.checker.verify(claim)
            if result.confidence < min_confidence or result.status == VerificationStatus.CONTRADICTED:
                results.append(result)

        return results

    def _extract_claims(self, text: str) -> list[str]:
        """Extract potential claims from text."""
        # Split into sentences
        sentences = re.split(r'[。！？\n]', text)
        claims = []

        for sentence in sentences:
            # Check if sentence contains fact-like indicators
            has_number = bool(re.search(r'\d+', sentence))
            has_claim_word = bool(re.search(r'(增长|下降|提高|减少|是|为|占)', sentence))
            is_long_enough = len(sentence) > 10

            if has_number and has_claim_word and is_long_enough:
                claims.append(sentence.strip())

        return claims[:10]  # Limit to 10 claims


# Example usage
if __name__ == "__main__":
    import os

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("DASHSCOPE_API_KEY not set, skipping live test")
    else:
        print("=== Bailian Fact Checker Test ===\n")

        checker = BailianFactChecker(api_key)

        # Test cases
        claims = [
            "人工智能市场在2024年增长了25%",
            "深度学习技术在图像识别任务上达到95%以上的准确率",
            "全球智能手机出货量同比下降10%"
        ]

        for claim in claims:
            print(f"Claim: {claim}")
            print(f"Cost estimate: ¥{checker.estimate_cost(claim):.6f}")

            result = checker.verify(claim)
            print(f"Status: {result.status.value}")
            print(f"Verdict: {result.verdict}")
            print(f"Confidence: {result.confidence:.0%}")
            print()

        # Test inline checker
        print("\n=== Inline Checker Test ===\n")
        inline_checker = InlineFactChecker(api_key)

        test_text = """
        根据最新研究，人工智能市场在2024年增长了25%。
        深度学习模型在图像识别任务上的准确率达到95%。
        全球智能手机出货量同比下降10%。
        """

        print("Checking claims in text...")
        results = inline_checker.check_claims_in_text(test_text)
        print(f"Found {len(results)} claims needing review")