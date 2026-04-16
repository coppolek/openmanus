"""Intent router for classifying and routing user intents."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.logger import logger


class Intent(BaseModel):
    """Represents a classified user intent."""
    
    category: str = Field(description="Intent category")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    entities: Dict[str, str] = Field(default_factory=dict)
    requires_planning: bool = Field(default=False)


class IntentRouter(BaseModel):
    """Routes user inputs to appropriate handlers based on intent."""
    
    intent_categories: List[str] = Field(
        default_factory=lambda: [
            "code_generation",
            "web_search",
            "file_operation",
            "data_analysis",
            "general_query",
            "system_command"
        ]
    )
    
    def classify_intent(self, user_input: str) -> Intent:
        """Classify user input into an intent category."""
        # Simple keyword-based classification for now
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["write", "code", "function", "class", "implement"]):
            return Intent(
                category="code_generation",
                confidence=0.8,
                requires_planning=True
            )
        elif any(keyword in user_input_lower for keyword in ["search", "find", "google", "web"]):
            return Intent(
                category="web_search",
                confidence=0.7
            )
        elif any(keyword in user_input_lower for keyword in ["file", "create", "edit", "delete", "read"]):
            return Intent(
                category="file_operation",
                confidence=0.7,
                requires_planning=True
            )
        elif any(keyword in user_input_lower for keyword in ["analyze", "data", "plot", "chart", "graph"]):
            return Intent(
                category="data_analysis",
                confidence=0.7,
                requires_planning=True
            )
        elif any(keyword in user_input_lower for keyword in ["exit", "quit", "stop", "terminate"]):
            return Intent(
                category="system_command",
                confidence=0.9
            )
        else:
            return Intent(
                category="general_query",
                confidence=0.5
            )
    
    def route(self, user_input: str) -> Dict[str, any]:
        """Route user input to appropriate handler."""
        intent = self.classify_intent(user_input)
        logger.info(f"Classified intent: {intent.category} (confidence: {intent.confidence})")
        
        return {
            "intent": intent,
            "original_input": user_input,
            "requires_planning": intent.requires_planning
        }
