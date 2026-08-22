from typing import List, Dict, Any, Optional


class AnswerGenerator:
    """
    Generates grounded answers using retrieved evidence.

    The LLM is intentionally abstracted behind _call_llm()
    so we can plug in Gemini/OpenAI/local models later.
    """

    def __init__(self):
        pass

    def build_context(
        self,
        results: List[Dict[str, Any]],
    ) -> str:
        """
        Convert retrieved chunks into grounded context.
        """

        context_parts = []

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})

            source = metadata.get("source", "Unknown")
            page = metadata.get("page", "Unknown")
            authority = metadata.get("authority", "Unknown")
            account_id = metadata.get("account_id", "Global")

            text = result.get("text", "").strip()

            context_parts.append(
                f"""
SOURCE {i}
Document: {source}
Page: {page}
Authority: {authority}
Account: {account_id}

CONTENT:
{text}
"""
            )

        return "\n".join(context_parts)

    def build_prompt(
        self,
        question: str,
        results: List[Dict[str, Any]],
        account_id: Optional[str] = None,
    ) -> str:
        """
        Build a grounded LLM prompt.
        """

        context = self.build_context(results)

        account_context = (
            f"The customer account is {account_id}."
            if account_id
            else "No specific customer account was provided."
        )

        return f"""
You are CalQuity, an enterprise operations assistant.

{account_context}

Answer the user's question using ONLY the evidence provided below.

IMPORTANT RULES:

1. Do not invent facts.
2. Do not use outside knowledge.
3. Prefer CURRENT operational policies over deprecated policies.
4. If an account-specific contract exists, use it when relevant.
5. Account-specific terms override generic policy when the evidence explicitly says so.
6. If the evidence is insufficient, clearly say that there is not enough evidence.
7. If documents conflict, explain the conflict instead of guessing.
8. Do not claim that an action was performed.
9. Keep the answer concise and operationally useful.
10. Include the supporting source documents.

USER QUESTION:
{question}

EVIDENCE:
{context}

Return your answer in this structure:

ANSWER:
<direct answer>

REASONING:
<short explanation based only on evidence>

SOURCES:
- <document name>, page <page>
- <document name>, page <page>
"""

    def _call_llm(self, prompt: str) -> str:
        """
        Placeholder for the actual LLM.

        We will connect Gemini/OpenAI here next.
        """

        raise NotImplementedError(
            "LLM provider is not connected yet."
        )

    def generate(
        self,
        question: str,
        results: List[Dict[str, Any]],
        account_id: Optional[str] = None,
    ):
        """
        Generate a grounded answer.
        """

        if not results:
            return {
                "answer": (
                    "I could not find sufficient evidence "
                    "to answer this question."
                ),
                "sources": [],
                "confidence": 0.0,
            }

        prompt = self.build_prompt(
            question=question,
            results=results,
            account_id=account_id,
        )

        answer = self._call_llm(prompt)

        sources = []

        for result in results:
            metadata = result.get("metadata", {})

            sources.append(
                {
                    "document": metadata.get("source"),
                    "page": metadata.get("page"),
                    "authority": metadata.get("authority"),
                    "account_id": metadata.get("account_id"),
                }
            )

        # Simple initial confidence calculation.
        scores = [
            float(result.get("score", 0))
            for result in results
        ]

        confidence = (
            sum(scores) / len(scores)
            if scores
            else 0.0
        )

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 3),
            "prompt": prompt,
        }