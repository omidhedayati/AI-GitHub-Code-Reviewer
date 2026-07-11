from app.services.analyzers.base import AnalysisIssue, IssueSeverity

SEVERITY_PENALTY: dict[IssueSeverity, float] = {
    IssueSeverity.CRITICAL: 15.0,
    IssueSeverity.HIGH: 10.0,
    IssueSeverity.MEDIUM: 5.0,
    IssueSeverity.LOW: 2.0,
    IssueSeverity.INFO: 0.5,
}


def calculate_file_score(issues: list[AnalysisIssue]) -> float:
    penalty = sum(SEVERITY_PENALTY.get(issue.severity, 1.0) for issue in issues)
    return max(0.0, min(100.0, 100.0 - penalty))


def calculate_overall_score(file_scores: list[float]) -> float:
    if not file_scores:
        return 100.0
    return round(sum(file_scores) / len(file_scores), 2)
