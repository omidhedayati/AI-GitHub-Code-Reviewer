AI_REVIEW_SYSTEM_PROMPT = """You are a senior software engineer performing a code review.
Analyze the provided source files and return findings as structured JSON only.
Focus on bugs, security risks, maintainability, complexity, and missing documentation.
Be specific about file paths and line numbers from the numbered snippets.
Do not invent files or lines that are not in the input."""

AI_REVIEW_JSON_SCHEMA = """{
  "summary": "string — concise overall assessment",
  "issues": [
    {
      "file_path": "string — relative path exactly as provided",
      "line_start": "integer >= 1",
      "line_end": "integer or null",
      "category": "bug|security|code_smell|complexity|long_method|bad_naming|dead_code|missing_documentation|duplicated_code|unused_import",
      "severity": "critical|high|medium|low|info",
      "confidence": "float 0.0-1.0",
      "title": "string — short issue title",
      "explanation": "string — why this matters",
      "suggestion": "string — actionable fix"
    }
  ]
}"""


def build_ai_review_prompt(
    repository_name: str,
    file_snippets: list[tuple[str, str]],
) -> str:
    sections: list[str] = [
        f"Review the repository `{repository_name}`.",
        "Return JSON matching this schema exactly:",
        AI_REVIEW_JSON_SCHEMA,
        "",
        "Source files:",
    ]
    for file_path, snippet in file_snippets:
        sections.append(f"--- FILE: {file_path} ---")
        sections.append(snippet)
        sections.append("")
    sections.append(
        "Respond with valid JSON only. Include an empty issues array if no problems found."
    )
    return "\n".join(sections)
