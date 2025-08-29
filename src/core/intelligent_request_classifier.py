"""Intelligent Request Classifier - Advanced NLP-based request understanding."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class RequestType(Enum):
    """Enhanced request types with confidence scores."""

    COMMAND = "command"  # /help, /exit, /status
    DEVELOPMENT = "development"  # Code creation, analysis, building
    UTILITY = "utility"  # Git, file operations, terminal
    CONVERSATION = "conversation"  # General AI chat, questions
    LEARNING = "learning"  # Help, tutorials, explanations
    ANALYSIS = "analysis"  # Code review, file analysis


@dataclass
class ClassificationResult:
    """Result of request classification with confidence."""

    request_type: RequestType
    confidence: float
    reasoning: List[str]
    suggested_action: str
    context_hints: Dict[str, any]


class IntelligentRequestClassifier:
    """Advanced request classifier with multilingual NLP understanding."""

    def __init__(self):
        # Enhanced Azerbaijani patterns
        self.az_patterns = {
            "development": [
                # Creation patterns
                "yarad",
                "yarat",
                "hazırla",
                "qur",
                "düzəlt",
                "yaz",
                "kodla",
                "tətbiq et",
                "implement et",
                "build et",
                "inşa et",
                # Analysis patterns
                "təhlil et",
                "yoxla",
                "analiz et",
                "bax",
                "oxu sonra",
                "incələ",
                "araşdır",
                "test et",
                # Fix patterns
                "düzəlt",
                "təmir et",
                "həll et",
                "fix et",
                "debug et",
            ],
            "utility": [
                "git əməliyyatı",
                "commit et",
                "push et",
                "pull et",
                "fayl",
                "qovluq",
                "directory",
                "terminal",
                "komanda",
                "xərc",
                "büdcə",
                "cost",
                "məsrəf",
            ],
            "learning": [
                "öyrət",
                "izah et",
                "nədir",
                "necə",
                "kömək",
                "göstər",
                "nümunə ver",
                "tutorial",
                "başla",
            ],
            "analysis": [
                "təhlil",
                "yoxla",
                "incələ",
                "review et",
                "bax",
                "nə var",
                "problem",
                "səhv",
                "issue",
            ],
        }

        # English patterns (comprehensive)
        self.en_patterns = {
            "development": [
                # Creation
                "create",
                "build",
                "develop",
                "generate",
                "implement",
                "code",
                "make",
                "write",
                "design",
                "setup",
                "initialize",
                "scaffold",
                # Modification
                "modify",
                "update",
                "enhance",
                "improve",
                "refactor",
                "optimize",
                "extend",
                "add feature",
                # Project types
                "app",
                "application",
                "project",
                "system",
                "api",
                "website",
                "database",
                "bot",
                "script",
                "tool",
                "library",
                "package",
            ],
            "utility": [
                "git",
                "commit",
                "push",
                "pull",
                "clone",
                "branch",
                "merge",
                "file",
                "folder",
                "directory",
                "terminal",
                "command",
                "shell",
                "cost",
                "budget",
                "spending",
                "price",
                "limit",
            ],
            "learning": [
                "help",
                "how to",
                "what is",
                "explain",
                "show me",
                "tutorial",
                "learn",
                "teach",
                "guide",
                "example",
                "demo",
                "documentation",
            ],
            "analysis": [
                "analyze",
                "review",
                "check",
                "inspect",
                "examine",
                "audit",
                "find",
                "search",
                "look for",
                "debug",
                "troubleshoot",
            ],
        }

        # Technical context indicators
        self.tech_contexts = {
            "web": ["html", "css", "js", "react", "vue", "angular", "frontend"],
            "backend": ["api", "server", "database", "python", "node", "java"],
            "mobile": ["android", "ios", "flutter", "react native", "swift"],
            "data": ["pandas", "numpy", "analysis", "csv", "json", "database"],
            "devops": ["docker", "kubernetes", "ci/cd", "deployment", "aws"],
        }

        # File extension patterns
        self.file_extensions = {
            "code": [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"],
            "web": [".html", ".css", ".jsx", ".tsx", ".vue"],
            "data": [".json", ".csv", ".xml", ".yaml", ".yml"],
            "config": [".env", ".config", ".ini", ".toml"],
        }

        # Command patterns (exact matches)
        self.command_patterns = {
            r"^/\w+": "COMMAND",  # /help, /exit
            r"^!\w+": "UTILITY",  # !git status
            r"^\w+\s+--\w+": "UTILITY",  # npm install --save
        }

    def classify_request(
        self, user_input: str, context: Optional[Dict] = None
    ) -> ClassificationResult:
        """
        Classify user request with advanced NLP understanding.

        Args:
            user_input: User's input text
            context: Optional context (current directory, files, etc.)

        Returns:
            ClassificationResult with type, confidence, and reasoning
        """
        user_lower = user_input.lower().strip()
        words = user_input.split()

        # Quick command detection
        if user_input.startswith("/"):
            return ClassificationResult(
                request_type=RequestType.COMMAND,
                confidence=1.0,
                reasoning=["Starts with / indicating command"],
                suggested_action="Execute system command",
                context_hints={},
            )

        # Calculate confidence scores for each type
        scores = {}
        reasoning = []

        # Development score
        dev_score, dev_reasons = self._calculate_development_score(user_lower, words)
        scores["development"] = dev_score
        reasoning.extend(dev_reasons)

        # Utility score
        util_score, util_reasons = self._calculate_utility_score(user_lower, words)
        scores["utility"] = util_score
        reasoning.extend(util_reasons)

        # Learning score
        learn_score, learn_reasons = self._calculate_learning_score(user_lower, words)
        scores["learning"] = learn_score
        reasoning.extend(learn_reasons)

        # Analysis score
        analysis_score, analysis_reasons = self._calculate_analysis_score(
            user_lower, words
        )
        scores["analysis"] = analysis_score
        reasoning.extend(analysis_reasons)

        # Context boosting
        if context:
            scores = self._apply_context_boost(scores, context, user_lower)

        # Enhanced decision logic
        best_type = max(scores.items(), key=lambda x: x[1])
        request_type_name, confidence = best_type

        # Pre-check for obvious conversation patterns (high priority)
        conversation_patterns = [
            "salam",
            "hello",
            "hi",
            "necəsən",
            "how are you",
            "weather",
            "what's the weather",
        ]
        if any(pattern in user_lower for pattern in conversation_patterns):
            request_type_name = "conversation"
            confidence = 0.9
            reasoning = ["Greeting or general conversation"]

        # Special handling for other ambiguous cases
        elif confidence < 0.5:
            # Check for specific patterns that should override low confidence

            # "fix" strongly indicates development
            if any(word in user_lower for word in ["fix", "düzəlt", "debug"]):
                request_type_name = "development"
                confidence = 0.7
                reasoning = ["Fix/debug keyword indicates development task"]

            # "analyze" specifically indicates analysis unless it's general conversation
            elif any(word in user_lower for word in ["analyze", "təhlil"]) and any(
                tech in user_lower for tech in ["code", "file", "project", ".py", ".js"]
            ):
                request_type_name = "analysis"
                confidence = 0.75
                reasoning = ["Analysis of technical content"]

            # "explain" with technical terms indicates learning
            elif "explain" in user_lower and any(
                tech in user_lower
                for tech in ["fastapi", "react", "python", "javascript"]
            ):
                request_type_name = "learning"
                confidence = 0.7
                reasoning = ["Explain technical concept indicates learning"]

        # Map to RequestType enum
        type_mapping = {
            "development": RequestType.DEVELOPMENT,
            "utility": RequestType.UTILITY,
            "learning": RequestType.LEARNING,
            "analysis": RequestType.ANALYSIS,
            "conversation": RequestType.CONVERSATION,
        }

        request_type = type_mapping.get(request_type_name, RequestType.CONVERSATION)

        # Final fallback for very low confidence
        if confidence < 0.3:
            request_type = RequestType.CONVERSATION
            confidence = 0.8
            reasoning = ["Low confidence in classification, defaulting to conversation"]

        # Add original text to context hints for handler prioritization
        context_hints = self._extract_context_hints(user_lower)
        context_hints["original_text"] = user_input.lower()

        return ClassificationResult(
            request_type=request_type,
            confidence=confidence,
            reasoning=reasoning[:3],  # Top 3 reasons
            suggested_action=self._get_suggested_action(request_type, user_input),
            context_hints=context_hints,
        )

    def _calculate_development_score(
        self, text: str, words: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate development classification score."""
        score = 0.0
        reasons = []

        # Azerbaijani development patterns
        az_matches = sum(
            1 for pattern in self.az_patterns["development"] if pattern in text
        )
        if az_matches > 0:
            score += az_matches * 0.3
            reasons.append(f"Contains {az_matches} Azerbaijani development terms")

        # English development patterns
        en_matches = sum(
            1 for pattern in self.en_patterns["development"] if pattern in text
        )
        if en_matches > 0:
            score += en_matches * 0.25
            reasons.append(f"Contains {en_matches} English development terms")

        # File extensions
        file_matches = sum(
            1
            for ext in self.file_extensions["code"] + self.file_extensions["web"]
            if ext in text
        )
        if file_matches > 0:
            score += file_matches * 0.4
            reasons.append(f"References {file_matches} code file extensions")

        # Technical contexts
        for context, keywords in self.tech_contexts.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                score += matches * 0.2
                reasons.append(f"Technical context: {context}")

        return min(score, 1.0), reasons

    def _calculate_utility_score(
        self, text: str, words: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate utility classification score."""
        score = 0.0
        reasons = []

        # Direct utility patterns
        az_matches = sum(
            1 for pattern in self.az_patterns["utility"] if pattern in text
        )
        en_matches = sum(
            1 for pattern in self.en_patterns["utility"] if pattern in text
        )

        if az_matches > 0:
            score += az_matches * 0.4
            reasons.append(f"Azerbaijani utility terms: {az_matches}")

        if en_matches > 0:
            score += en_matches * 0.35
            reasons.append(f"English utility terms: {en_matches}")

        # Git patterns (high confidence)
        git_patterns = ["git ", "commit", "push", "pull", "clone", "branch"]
        git_matches = sum(1 for pattern in git_patterns if pattern in text)
        if git_matches > 0:
            score += 0.8
            reasons.append("Git operation detected")

        # Cost management
        cost_patterns = ["cost", "budget", "xərc", "məsrəf", "price", "money"]
        cost_matches = sum(1 for pattern in cost_patterns if pattern in text)
        if cost_matches > 0:
            score += 0.6
            reasons.append("Cost management request")

        return min(score, 1.0), reasons

    def _calculate_learning_score(
        self, text: str, words: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate learning classification score."""
        score = 0.0
        reasons = []

        # Question patterns
        question_patterns = [
            "necə",
            "nədir",
            "niyə",
            "how",
            "what",
            "why",
            "when",
            "where",
        ]
        question_matches = sum(1 for pattern in question_patterns if pattern in text)
        if question_matches > 0:
            score += 0.5
            reasons.append("Question format detected")

        # Help patterns
        help_patterns = ["help", "kömək", "öyrət", "göstər", "tutorial", "guide"]
        help_matches = sum(1 for pattern in help_patterns if pattern in text)
        if help_matches > 0:
            score += 0.6
            reasons.append("Help request detected")

        return min(score, 1.0), reasons

    def _calculate_analysis_score(
        self, text: str, words: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate analysis classification score."""
        score = 0.0
        reasons = []

        # Analysis patterns
        analysis_patterns = ["təhlil", "yoxla", "analyze", "review", "check", "inspect"]
        matches = sum(1 for pattern in analysis_patterns if pattern in text)
        if matches > 0:
            score += matches * 0.4
            reasons.append(f"Analysis terms: {matches}")

        # File analysis indicators
        if any(ext in text for ext in self.file_extensions["code"]):
            if any(word in text for word in ["oxu", "read", "bax", "look"]):
                score += 0.6
                reasons.append("File analysis request")

        return min(score, 1.0), reasons

    def _apply_context_boost(
        self, scores: Dict[str, float], context: Dict, text: str
    ) -> Dict[str, float]:
        """Apply context-based score boosting."""
        # If in a git repository, boost utility for git commands
        if context.get("is_git_repo") and any(
            cmd in text for cmd in ["git", "commit", "push"]
        ):
            scores["utility"] = min(scores["utility"] + 0.3, 1.0)

        # If code files present, boost development
        if context.get("has_code_files"):
            if any(word in text for word in ["create", "yarad", "build", "develop"]):
                scores["development"] = min(scores["development"] + 0.2, 1.0)

        return scores

    def _get_suggested_action(self, request_type: RequestType, user_input: str) -> str:
        """Get suggested action for the request type."""
        actions = {
            RequestType.COMMAND: "Execute system command",
            RequestType.DEVELOPMENT: "Route to orchestrator for multi-agent development",
            RequestType.UTILITY: "Process through utility handlers",
            RequestType.CONVERSATION: "Handle with AI conversation",
            RequestType.LEARNING: "Provide educational response",
            RequestType.ANALYSIS: "Perform code/file analysis",
        }
        return actions.get(request_type, "Process as general request")

    def _extract_context_hints(self, text: str) -> Dict[str, any]:
        """Extract context hints from the text."""
        hints = {}

        # Technical stack detection
        for stack, keywords in self.tech_contexts.items():
            if any(keyword in text for keyword in keywords):
                hints["tech_stack"] = stack
                break

        # File type hints
        for file_type, extensions in self.file_extensions.items():
            if any(ext in text for ext in extensions):
                hints["file_type"] = file_type
                break

        # Urgency indicators
        urgent_words = ["urgent", "asap", "quickly", "fast", "tez", "cəld"]
        if any(word in text for word in urgent_words):
            hints["urgency"] = "high"

        return hints


# Global classifier instance
_classifier = None


def get_intelligent_classifier() -> IntelligentRequestClassifier:
    """Get global intelligent classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = IntelligentRequestClassifier()
    return _classifier
