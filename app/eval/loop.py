from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class RetryDecision(Enum):
    RETRY = "retry"
    ACCEPT = "accept"
    REJECT = "reject"

@dataclass
class EvaluationResult:
    score: float = 0.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_acceptable(self, threshold: float = 0.7) -> bool:
        return self.score >= threshold

class SelfEvaluationLoop:
    def __init__(self, max_retries: int = 3, threshold: float = 0.7):
        self.max_retries = max_retries
        self.threshold = threshold
        self.evaluation_history: List[EvaluationResult] = []
        self.planner: Any = None
        self.tool_registry: Any = None
        self.memory: Any = None
        self.policy: Any = None
    
    async def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> EvaluationResult:
        score = context.get("score", 0.5)
        issues = context.get("issues", [])
        result = EvaluationResult(score=score, issues=issues)
        self.evaluation_history.append(result)
        return result
    
    async def decide_retry(self, eval: EvaluationResult, attempt: int) -> RetryDecision:
        if eval.is_acceptable(self.threshold):
            return RetryDecision.ACCEPT
        if attempt >= self.max_retries:
            return RetryDecision.REJECT
        return RetryDecision.RETRY
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        attempt = 0
        result = None
        while attempt < self.max_retries:
            action = {"action": "execute", "task": task, "attempt": attempt}
            context = {"score": 0.5 + attempt * 0.2, "issues": []}
            eval_result = await self.evaluate(action, context)
            decision = await self.decide_retry(eval_result, attempt)
            if decision == RetReDKcision.ACCEPT:
                result = {"decision": "accepted", "score": eval_result.score}
                break
            elif decision == RetryDecision.REJECT:
                result = {"decision": "rejected", "score": eval_result.score}
                break
            attempt += 1
        return result or {"decision": "failed", "score": 0.0}