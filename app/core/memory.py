"""Memory layer for storing and retrieving context, history, and knowledge."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from app.logger import logger


class MemoryEntry(BaseModel):
    """Single memory entry with metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str  # 'user_input', 'tool_call', 'tool_result', 'agent_thought', 'plan', 'intent'
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    relevance_score: float = 1.0


class MemoryStore(BaseModel):
    """In-memory storage for conversation and execution history."""
    
    entries: List[MemoryEntry] = Field(default_factory=list)
    max_entries: int = 1000
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    
    def add(self, 
            type: str, 
            content: Any, 
            metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        """Add a new memory entry."""
        entry = MemoryEntry(
            type=type,
            content=content,
            metadata=metadata or {},
            session_id=self.session_id
        )
        
        self.entries.append(entry)
        
        # Trim if exceeding max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        logger.debug(f"Added memory entry: type={type}, id={entry.id}")
        return entry
    
    def get_recent(self, 
                   n: int = 10, 
                   types: Optional[List[str]] = None) -> List[MemoryEntry]:
        """Get n most recent entries, optionally filtered by type."""
        filtered = self.entries
        if types:
            filtered = [e for e in self.entries if e.type in types]
        
        return filtered[-n:]
    
    def get_by_type(self, type: str) -> List[MemoryEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.type == type]
    
    def get_context_window(self, 
                          window_size: int = 5,
                          include_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get a context window for LLM consumption."""
        include_types = include_types or ['user_input', 'tool_result', 'agent_thought']
        recent = self.get_recent(window_size, include_types)
        
        context = []
        for entry in recent:
            context_item = {
                'timestamp': entry.timestamp.isoformat(),
                'type': entry.type,
                'content': entry.content
            }
            if entry.metadata:
                context_item['metadata'] = entry.metadata
            context.append(context_item)
        
        return context
    
    def clear(self) -> None:
        """Clear all memory entries."""
        self.entries.clear()
        logger.debug("Memory store cleared")
    
    def search(self, 
               query: str, 
               limit: int = 5,
               types: Optional[List[str]] = None) -> List[MemoryEntry]:
        """Simple text search in memory entries."""
        results = []
        query_lower = query.lower()
        
        for entry in self.entries:
            if types and entry.type not in types:
                continue
            
            # Simple substring search in content
            content_str = str(entry.content).lower()
            if query_lower in content_str:
                results.append(entry)
            
            # Also search in metadata
            metadata_str = str(entry.metadata).lower()
            if query_lower in metadata_str:
                if entry not in results:
                    results.append(entry)
        
        # Sort by timestamp (most recent first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]


class WorkingMemory(BaseModel):
    """Working memory for current task execution."""
    
    current_intent: Optional[str] = None
    current_plan: Optional[List[str]] = None
    current_step: int = 0
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    def update_intent(self, intent: str) -> None:
        """Update current intent."""
        self.current_intent = intent
        logger.debug(f"Working memory: intent updated to '{intent}'")
    
    def update_plan(self, plan: List[str]) -> None:
        """Update current plan."""
        self.current_plan = plan
        self.current_step = 0
        logger.debug(f"Working memory: plan updated with {len(plan)} steps")
    
    def advance_step(self) -> Optional[str]:
        """Move to next step in plan."""
        if not self.current_plan:
            return None
        
        if self.current_step < len(self.current_plan):
            step = self.current_plan[self.current_step]
            self.current_step += 1
            return step
        return None
    
    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """Store tool execution result."""
        self.tool_results[tool_name] = result
        logger.debug(f"Working memory: stored result for tool '{tool_name}'")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current working memory state."""
        return {
            'intent': self.current_intent,
            'plan': self.current_plan,
            'current_step': self.current_step,
            'completed_steps': self.current_step if self.current_plan else 0,
            'total_steps': len(self.current_plan) if self.current_plan else 0,
            'tool_results': self.tool_results,
            'context': self.context
        }
    
    def reset(self) -> None:
        """Reset working memory."""
        self.current_intent = None
        self.current_plan = None
        self.current_step = 0
        self.tool_results.clear()
        self.context.clear()
        logger.debug("Working memory reset")


class MemoryManager(BaseModel):
    """Main memory management system."""
    
    long_term: MemoryStore = Field(default_factory=MemoryStore)
    working: WorkingMemory = Field(default_factory=WorkingMemory)
    
    def store_user_input(self, input_text: str, metadata: Optional[Dict] = None) -> None:
        """Store user input in memory."""
        self.long_term.add('user_input', input_text, metadata)
    
    def store_tool_call(self, tool_name: str, args: Dict, metadata: Optional[Dict] = None) -> None:
        """Store tool call in memory."""
        content = {'tool': tool_name, 'args': args}
        self.long_term.add('tool_call', content, metadata)
    
    def store_tool_result(self, tool_name: str, result: Any, metadata: Optional[Dict] = None) -> None:
        """Store tool result in memory."""
        content = {'tool': tool_name, 'result': result}
        self.long_term.add('tool_result', content, metadata)
        self.working.add_tool_result(tool_name, result)
    
    def store_agent_thought(self, thought: str, metadata: Optional[Dict] = None) -> None:
        """Store agent's thought or reasoning."""
        self.long_term.add('agent_thought', thought, metadata)
    
    def store_intent(self, intent: str, metadata: Optional[Dict] = None) -> None:
        """Store identified intent."""
        self.long_term.add('intent', intent, metadata)
        self.working.update_intent(intent)
    
    def store_plan(self, plan: List[str], metadata: Optional[Dict] = None) -> None:
        """Store execution plan."""
        self.long_term.add('plan', plan, metadata)
        self.working.update_plan(plan)
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history for context."""
        return self.long_term.get_context_window(limit)
    
    def get_relevant_context(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Get relevant context based on query."""
        return self.long_term.search(query, limit)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of current execution."""
        return {
            'session_id': self.long_term.session_id,
            'total_memories': len(self.long_term.entries),
            'working_state': self.working.get_current_state(),
            'recent_tools': [e.content['tool'] for e in self.long_term.get_recent(5, ['tool_call'])],
            'recent_results': [e.content for e in self.long_term.get_recent(3, ['tool_result'])]
        }
    
    def reset_session(self) -> None:
        """Start a new session."""
        self.long_term.clear()
        self.long_term.session_id = str(uuid4())
        self.working.reset()
        logger.info(f"Memory manager reset with new session: {self.long_term.session_id}")


# Global memory manager instance
memory_manager = MemoryManager()
