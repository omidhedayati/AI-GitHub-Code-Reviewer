import re
from dataclasses import dataclass
from pathlib import Path

from app.services.analyzers.base import (
    AnalysisIssue,
    IssueCategory,
    IssueSeverity,
)
from app.services.analyzers.common import analyze_common_patterns

FUNCTION_PATTERN = re.compile(
    r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|"
    r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{)",
)


@dataclass(frozen=True)
class RegexRule:
    rule_id: str
    pattern: re.Pattern[str]
    category: IssueCategory
    severity: IssueSeverity
    confidence: float
    title: str
    explanation: str
    suggestion: str


JAVASCRIPT_RULES: list[RegexRule] = [
    RegexRule(
        rule_id="js-eval",
        pattern=re.compile(r"\beval\s*\("),
        category=IssueCategory.SECURITY,
        severity=IssueSeverity.CRITICAL,
        confidence=0.95,
        title="Use of eval() detected",
        explanation="eval() executes arbitrary strings as code.",
        suggestion="Avoid eval(); parse JSON with JSON.parse() when needed.",
    ),
    RegexRule(
        rule_id="js-inner-html",
        pattern=re.compile(r"\.innerHTML\s*="),
        category=IssueCategory.SECURITY,
        severity=IssueSeverity.HIGH,
        confidence=0.85,
        title="Direct innerHTML assignment",
        explanation="innerHTML can introduce XSS vulnerabilities.",
        suggestion="Use textContent or sanitize HTML before assignment.",
    ),
    RegexRule(
        rule_id="js-document-write",
        pattern=re.compile(r"\bdocument\.write\s*\("),
        category=IssueCategory.SECURITY,
        severity=IssueSeverity.MEDIUM,
        confidence=0.8,
        title="Use of document.write()",
        explanation="document.write can block rendering and enable XSS.",
        suggestion="Use DOM APIs such as createElement and appendChild.",
    ),
    RegexRule(
        rule_id="js-console-log",
        pattern=re.compile(r"\bconsole\.(log|debug|info)\s*\("),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.INFO,
        confidence=0.7,
        title="Console logging statement",
        explanation="Console statements are often left from debugging.",
        suggestion="Remove console logging or use a structured logger.",
    ),
    RegexRule(
        rule_id="js-var-keyword",
        pattern=re.compile(r"\bvar\s+\w+"),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.LOW,
        confidence=0.75,
        title="Use of var keyword",
        explanation="var has function scope and can cause subtle bugs.",
        suggestion="Prefer const or let for block-scoped declarations.",
    ),
    RegexRule(
        rule_id="js-any-type",
        pattern=re.compile(r":\s*any\b"),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.LOW,
        confidence=0.8,
        title="Explicit any type in TypeScript",
        explanation="any disables TypeScript type checking for that value.",
        suggestion="Use a specific type or unknown with narrowing.",
    ),
    RegexRule(
        rule_id="js-empty-catch",
        pattern=re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}"),
        category=IssueCategory.BUG,
        severity=IssueSeverity.MEDIUM,
        confidence=0.85,
        title="Empty catch block",
        explanation="Errors are swallowed without handling or logging.",
        suggestion="Handle the error or rethrow with context.",
    ),
]

JAVA_RULES: list[RegexRule] = [
    RegexRule(
        rule_id="java-system-out",
        pattern=re.compile(r"\bSystem\.(out|err)\.print"),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.LOW,
        confidence=0.85,
        title="Direct System.out/err usage",
        explanation="Production code should use a logging framework.",
        suggestion="Replace with SLF4J, Log4j, or java.util.logging.",
    ),
    RegexRule(
        rule_id="java-empty-catch",
        pattern=re.compile(r"catch\s*\([^)]+\)\s*\{\s*\}"),
        category=IssueCategory.BUG,
        severity=IssueSeverity.MEDIUM,
        confidence=0.85,
        title="Empty catch block",
        explanation="Exceptions are ignored silently.",
        suggestion="Log or handle the exception appropriately.",
    ),
    RegexRule(
        rule_id="java-thread-stop",
        pattern=re.compile(r"\.stop\s*\("),
        category=IssueCategory.BUG,
        severity=IssueSeverity.HIGH,
        confidence=0.7,
        title="Deprecated Thread.stop() usage",
        explanation="Thread.stop() is deprecated and unsafe.",
        suggestion="Use interruption flags and cooperative shutdown.",
    ),
]

GO_RULES: list[RegexRule] = [
    RegexRule(
        rule_id="go-fmt-println",
        pattern=re.compile(r"\bfmt\.Println\s*\("),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.INFO,
        confidence=0.7,
        title="fmt.Println debug output",
        explanation="Println is typically used for debugging.",
        suggestion="Use structured logging for production services.",
    ),
    RegexRule(
        rule_id="go-panic",
        pattern=re.compile(r"\bpanic\s*\("),
        category=IssueCategory.BUG,
        severity=IssueSeverity.MEDIUM,
        confidence=0.75,
        title="panic() call detected",
        explanation="panic crashes the goroutine unless recovered.",
        suggestion="Return errors instead of panicking in library code.",
    ),
    RegexRule(
        rule_id="go-empty-err-check",
        pattern=re.compile(r",\s*_\s*:="),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.LOW,
        confidence=0.65,
        title="Ignored error return value",
        explanation="Errors may be discarded with the blank identifier.",
        suggestion="Check and handle returned errors explicitly.",
    ),
]

RUST_RULES: list[RegexRule] = [
    RegexRule(
        rule_id="rust-unwrap",
        pattern=re.compile(r"\.unwrap\s*\("),
        category=IssueCategory.BUG,
        severity=IssueSeverity.MEDIUM,
        confidence=0.8,
        title="unwrap() may panic",
        explanation="unwrap() panics on None or Err values.",
        suggestion="Use match, if let, or expect with a clear message.",
    ),
    RegexRule(
        rule_id="rust-expect",
        pattern=re.compile(r"\.expect\s*\("),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.LOW,
        confidence=0.7,
        title="expect() used for error handling",
        explanation="expect() still panics on failure.",
        suggestion="Propagate errors with ? operator where possible.",
    ),
    RegexRule(
        rule_id="rust-unsafe",
        pattern=re.compile(r"\bunsafe\s*\{"),
        category=IssueCategory.SECURITY,
        severity=IssueSeverity.HIGH,
        confidence=0.9,
        title="unsafe block detected",
        explanation="unsafe bypasses Rust safety guarantees.",
        suggestion="Minimize unsafe code and document invariants clearly.",
    ),
]

CSHARP_RULES: list[RegexRule] = [
    RegexRule(
        rule_id="csharp-empty-catch",
        pattern=re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}"),
        category=IssueCategory.BUG,
        severity=IssueSeverity.MEDIUM,
        confidence=0.85,
        title="Empty catch block",
        explanation="Exceptions are swallowed without handling.",
        suggestion="Log the exception or handle it explicitly.",
    ),
    RegexRule(
        rule_id="csharp-console-write",
        pattern=re.compile(r"\bConsole\.(WriteLine|Write)\s*\("),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.INFO,
        confidence=0.75,
        title="Console output in application code",
        explanation="Console logging is usually for debugging only.",
        suggestion="Use ILogger or your logging framework.",
    ),
]

CPP_RULES: list[RegexRule] = [
    RegexRule(
        rule_id="cpp-using-namespace-std",
        pattern=re.compile(r"using\s+namespace\s+std\s*;"),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.LOW,
        confidence=0.9,
        title="using namespace std in header scope",
        explanation="Pollutes the global namespace and can cause ADL issues.",
        suggestion="Qualify std symbols or use using declarations locally.",
    ),
    RegexRule(
        rule_id="cpp-malloc-free",
        pattern=re.compile(r"\b(malloc|free)\s*\("),
        category=IssueCategory.CODE_SMELL,
        severity=IssueSeverity.MEDIUM,
        confidence=0.85,
        title="C-style memory management",
        explanation="Manual malloc/free is error-prone in C++ code.",
        suggestion="Prefer RAII containers and smart pointers.",
    ),
    RegexRule(
        rule_id="cpp-strcpy",
        pattern=re.compile(r"\b(strcpy|strcat|sprintf|gets)\s*\("),
        category=IssueCategory.SECURITY,
        severity=IssueSeverity.HIGH,
        confidence=0.9,
        title="Unsafe C string function",
        explanation="These functions do not bound-check buffer sizes.",
        suggestion="Use strncpy, snprintf, or std::string alternatives.",
    ),
]


def _apply_regex_rules(
    content: str,
    relative_path: str,
    rules: list[RegexRule],
) -> list[AnalysisIssue]:
    issues: list[AnalysisIssue] = []
    lines = content.splitlines()
    for index, line in enumerate(lines, start=1):
        for rule in rules:
            if rule.pattern.search(line):
                issues.append(
                    AnalysisIssue(
                        file_path=relative_path,
                        line_start=index,
                        line_end=index,
                        category=rule.category,
                        severity=rule.severity,
                        confidence=rule.confidence,
                        rule_id=rule.rule_id,
                        title=rule.title,
                        explanation=rule.explanation,
                        suggestion=rule.suggestion,
                    )
                )
    return issues


def _detect_long_functions(content: str, relative_path: str) -> list[AnalysisIssue]:
    issues: list[AnalysisIssue] = []
    lines = content.splitlines()
    function_starts: list[tuple[int, str]] = []

    for index, line in enumerate(lines, start=1):
        match = FUNCTION_PATTERN.search(line)
        if match:
            name = next(group for group in match.groups() if group)
            function_starts.append((index, name))

    for start_line, name in function_starts:
        brace_depth = 0
        started = False
        end_line = start_line
        for offset, line in enumerate(lines[start_line - 1 :], start=start_line):
            brace_depth += line.count("{") - line.count("}")
            if "{" in line:
                started = True
            end_line = offset
            if started and brace_depth <= 0:
                break
        length = end_line - start_line + 1
        if length > 50:
            issues.append(
                AnalysisIssue(
                    file_path=relative_path,
                    line_start=start_line,
                    line_end=end_line,
                    category=IssueCategory.LONG_METHOD,
                    severity=IssueSeverity.MEDIUM,
                    confidence=0.7,
                    rule_id="long-function-heuristic",
                    title=f"Function '{name}' appears too long",
                    explanation=f"Function spans approximately {length} lines.",
                    suggestion="Split the function into smaller units.",
                )
            )
    return issues


class RegexAnalyzer:
    def __init__(self, language: str, rules: list[RegexRule]) -> None:
        self.language = language
        self._rules = rules

    def analyze(
        self, file_path: Path, content: str, relative_path: str
    ) -> list[AnalysisIssue]:
        issues = analyze_common_patterns(file_path, content, relative_path)
        issues.extend(_apply_regex_rules(content, relative_path, self._rules))
        if self.language in {"javascript", "typescript"}:
            issues.extend(_detect_long_functions(content, relative_path))
        return issues


class JavaScriptAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("javascript", JAVASCRIPT_RULES)


class TypeScriptAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("typescript", JAVASCRIPT_RULES)


class JavaAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("java", JAVA_RULES)


class GoAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("go", GO_RULES)


class RustAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("rust", RUST_RULES)


class CSharpAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("csharp", CSHARP_RULES)


class CppAnalyzer(RegexAnalyzer):
    def __init__(self) -> None:
        super().__init__("cpp", CPP_RULES)
