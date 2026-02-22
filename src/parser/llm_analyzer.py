import json
import logging

from openai import AsyncAzureOpenAI

from src.models.sop import (
    SOPBranch,
    SOPDecision,
    SOPDocument,
    SOPElement,
    SOPElementType,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert at analyzing Standard Operating Procedure (SOP) documents and extracting their structure.

Given the raw text of an SOP, you must return a JSON object that represents the structured flow.

Rules:
1. Identify sequential steps in the SOP.
2. Detect decision points — steps that check a condition and branch into different paths (if/then, check if, etc.).
3. For each decision, extract the condition question and all branches with their condition labels and action steps.
4. Steps that follow after all branches of a decision have concluded are regular steps (they come after the decision converges).
5. Keep step text concise but faithful to the original.

Return ONLY valid JSON matching this exact schema (no markdown, no explanation):

{
  "title": "string — a short title for the SOP process",
  "elements": [
    {
      "type": "step",
      "text": "string — the step description"
    },
    {
      "type": "decision",
      "text": "string — the decision/check description",
      "decision": {
        "question": "string — the question being evaluated",
        "branches": [
          {
            "condition_label": "string — e.g. 'Yes', 'No', 'Billing-related'",
            "steps": [
              {
                "type": "step",
                "text": "string — action for this branch"
              }
            ]
          }
        ]
      }
    }
  ]
}

Important:
- Every element must have "type" as either "step" or "decision".
- Decision elements MUST have a "decision" field with "question" and "branches".
- Branch steps can themselves be decisions (for nested if/then).
- Do NOT wrap the JSON in markdown code fences. Return raw JSON only.
"""


class LLMSOPAnalyzer:
    """Uses Azure OpenAI API to analyze SOP text and return a structured SOPDocument."""

    def __init__(
        self,
        api_key: str,
        azure_endpoint: str,
        api_version: str = "2024-02-01",
        model: str = "gpt-4o",
    ) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        self._model = model

    async def analyze(self, sop_text: str) -> SOPDocument:
        """Send SOP text to Azure OpenAI and parse the structured JSON response."""
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this SOP and return the structured JSON:\n\n{sop_text}",
                },
            ],
        )

        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # remove closing fence
            raw_text = "\n".join(lines)

        logger.debug("LLM response: %s", raw_text)

        data = json.loads(raw_text)
        return self._parse_response(data)

    def _parse_response(self, data: dict) -> SOPDocument:
        """Convert the JSON dict into SOPDocument dataclasses."""
        title = data.get("title", "Untitled SOP")
        elements = [self._parse_element(e) for e in data.get("elements", [])]
        return SOPDocument(title=title, elements=elements)

    def _parse_element(self, elem: dict) -> SOPElement:
        """Recursively parse a single element from the JSON response."""
        elem_type = elem.get("type", "step")

        if elem_type == "decision":
            decision_data = elem.get("decision", {})
            branches = []
            for b in decision_data.get("branches", []):
                branch_steps = [self._parse_element(s) for s in b.get("steps", [])]
                branches.append(
                    SOPBranch(
                        condition_label=b.get("condition_label", ""),
                        steps=branch_steps,
                    )
                )
            decision = SOPDecision(
                question=decision_data.get("question", elem.get("text", "")),
                branches=branches,
            )
            return SOPElement(
                element_type=SOPElementType.DECISION,
                text=elem.get("text", ""),
                decision=decision,
            )

        return SOPElement(
            element_type=SOPElementType.STEP,
            text=elem.get("text", ""),
        )
