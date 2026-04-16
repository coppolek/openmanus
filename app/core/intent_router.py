"""Intent router for classifying and routing user requests."""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.llm import LLM
from app.logger import logger
import json


class IntentType(str, Enum):
    """Types of intents that can be classified."""
    
    CODING = "coding"  # Code generation, debugging, refactoring
    ANALYSIS = "analysis"  # Data analysis, research, investigation
    CREATIVE = "creative"  # Writing, design, content creation
    SYSTEM = "system"  # File operations, system commands
    BROWSER = "browser"  # Web browsing, scraping, automation
    CONVERSATION = "conversation"  # General chat, Q&A
    PLANNING = "planning"  # Task planning, project management
    UNKNOWN = "unknown"  # Cannot determine intent


class Intent(BaseModel):
    """Represents a classified intent with metadata."""
    
    type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = ""
    entities: Dict[str, Any] = Field(default_factory=dict)
    suggested_tools: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    complexity: str = "simple"  # simple, moderate, complex
    

class IntentRouter:
    """Routes user requests based on intent classification."""
    
    def __init__(self, llm: Optional[LLM] = None):
        """Initialize the intent router.
        
        Args:
            llm: Language model for intent classification. If None, uses default.
        """
        self.llm = llm or LLM()
        self.intent_history: List[Intent] = []
        
    async def classify_intent(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """Classify the intent of a user input.
        
        Args:
            user_input: The user's request or query
            context: Optional context about the conversation or environment
            
        Returns:
            Classified Intent object
        """
        classification_prompt = self._build_classification_prompt(user_input, context)
        
        try:
            response = await self.llm.aask(
                classification_prompt,
                system="You are an intent classification system. Analyze user requests and classify them accurately."
            )
            
            # Parse the LLM response
            intent = self._parse_classification_response(response, user_input)
            
            # Store in history
            self.intent_history.append(intent)
            
            logger.info(f"Classified intent: {intent.type} (confidence: {intent.confidence})")
            return intent
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                description=f"Failed to classify: {str(e)}"
            )
    
    def _build_classification_prompt(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the prompt for intent classification."""
        
        context_str = ""
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"
        
        return f"""Classify the following user request into one of these intent types:
- CODING: Code generation, debugging, refactoring, programming tasks
- ANALYSIS: Data analysis, research, investigation, insights
- CREATIVE: Writing, design, content creation, artistic tasks
- SYSTEM: File operations, system commands, environment management
- BROWSER: Web browsing, scraping, online research, automation
- CONVERSATION: General chat, Q&A, explanations
- PLANNING: Task planning, project management, strategy
- UNKNOWN: Cannot determine clear intent

User Request: {user_input}{context_str}

Provide your classification in JSON format:
{{
    "intent_type": "<type>",
    "confidence": <0.0-1.0>,
    "description": "<brief description of what the user wants>",
    "entities": {{"key": "value"}},  // Extract relevant entities (files, URLs, data, etc.)
    "suggested_tools": ["tool1", "tool2"],  // Suggest relevant tools
    "requires_approval": <true/false>,  // Does this need user approval?
    "complexity": "<simple/moderate/complex>"  // Task complexity
}}

Respond ONLY with valid JSON."""
    
    def _parse_classification_response(self, response: str, original_input: str) -> Intent:
        """Parse the LLM's classification response."""
        
        try:
            # Clean the response to extract JSON
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response)
            
            # Map the intent type string to enum
            intent_type_str = data.get("intent_type", "UNKNOWN").upper()
            try:
                intent_type = IntentType[intent_type_str]
            except KeyError:
                intent_type = IntentType.UNKNOWN
            
            return Intent(
                type=intent_type,
                confidence=float(data.get("confidence", 0.5)),
                description=data.get("description", original_input[:100]),
                entities=data.get("entities", {}),
                suggested_tools=data.get("suggested_tools", []),
                requires_approval=data.get("requires_approval", False),
                complexity=data.get("complexity", "simple")
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse classification response: {e}")
            # Fallback to basic heuristic classification
            return self._heuristic_classification(original_input)
    
    def _heuristic_classification(self, user_input: str) -> Intent:
        """Simple heuristic-based classification as fallback."""
        
        input_lower = user_input.lower()
        
        # Simple keyword-based classification
        if any(word in input_lower for word in ["code", "debug", "function", "class", "implement", "fix"]):
            return Intent(type=IntentType.CODING, confidence=0.6, description="Likely a coding task")
        elif any(word in input_lower for word in ["analyze", "data", "statistics", "research", "investigate"]):
            return Intent(type=IntentType.ANALYSIS, confidence=0.6, description="Likely an analysis task")
        elif any(word in input_lower for word in ["write", "create", "design", "compose", "draft"]):
            return Intent(type=IntentType.CREATIVE, confidence=0.6, description="Likely a creative task")
        elif any(word in input_lower for word in ["file", "folder", "directory", "system", "command"]):
            return Intent(type=IntentType.SYSTEM, confidence=0.6, description="Likely a system task")
        elif any(word in input_lower for word in ["browse", "web", "website", "url", "search online"]):
            return Intent(type=IntentType.BROWSER, confidence=0.6, description="Likely a browser task")
        elif any(word in input_lower for word in ["plan", "organize", "schedule", "project", "task"]):
            return Intent(type=IntentType.PLANNING, confidence=0.6, description="Likely a planning task")
        elif any(word in input_lower for word in ["what", "why", "how", "explain", "tell me"]):
            return Intent(type=IntentType.CONVERSATION, confidence=0.6, description="Likely a conversation")
        else:
            return Intent(type=IntentType.UNKNOWN, confidence=0.3, description="Could not determine intent")
    
    def get_recommended_agent(self, intent: Intent) -> str:
        """Get the recommended agent type for an intent.
        
        Args:
            intent: The classified intent
            
        Returns:
            Name of the recommended agent type
        """
        agent_mapping = {
            IntentType.CODING: "CodeAgent",
            IntentType.ANALYSIS: "DataAnalysisAgent",
            IntentType.CREATIVE: "CreativeAgent",
            IntentType.SYSTEM: "SystemAgent",
            IntentType.BROWSER: "BrowserAgent",
            IntentType.CONVERSATION: "ConversationAgent",
            IntentType.PLANNING: "PlannerAgent",
            IntentType.UNKNOWN: "GeneralAgent"
        }
        
        return agent_mapping.get(intent.type, "GeneralAgent")
    
    def should_escalate(self, intent: Intent) -> bool:
        """Determine if an intent should be escalated to a human or higher-level agent.
        
        Args:
            intent: The classified intent
            
        Returns:
            True if escalation is recommended
        """
        # Escalate if confidence is too low or approval is required
        if intent.confidence < 0.4:
            return True
        if intent.requires_approval:
            return True
        if intent.type == IntentType.UNKNOWN:
            return True
        if intent.complexity == "complex" and intent.confidence < 0.7:
            return True
        
        return False
    
    def get_intent_history(self, limit: Optional[int] = None) -> List[Intent]:
        """Get the history of classified intents.
        
        Args:
            limit: Maximum number of intents to return (most recent first)
            
        Returns:
            List of Intent objects
        """
        if limit:
            return self.intent_history[-limit:][::-1]
        return self.intent_history[::-1]
    
    def clear_history(self) -> None:
        """Clear the intent history."""
        self.intent_history.clear()
        logger.info("Intent history cleared")
