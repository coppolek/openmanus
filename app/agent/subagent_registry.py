from typing import Dict, Optional, Any

class SubAgentRegistry:
    """Minimal subagent registry for managing and routing to subagents"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.routes: Dict[str, str] = {
            "/dev": "dev",
            "/ads": "ads",
            "/web": "web",
            "/content": "content",
            "/memory": "memory"
        }
    
    def register(self, name: str, agent: Any) -> None:
        """Register a subagent"""
        self.agents[name] = agent
    
    def get(self, name: str) -> Optional[Any]:
        """Get a registered subagent"""
        return self.agents.get(name)
    
    def resolve_route(self, path: str) -> Optional[str]:
        """Resolve path to subagent name"""
        for route, agent_name in self.routes.items():
            if path.startswith(route):
                return agent_name
        return None
    
    def route_to_agent(self, path: str) -> Optional[Any]:
        """Route path to appropriate subagent"""
        agent_name = self.resolve_route(path)
        if agent_name:
            return self.get(agent_name)
        return None
    
    def list_agents(self) -> list: 
        """List all registered agents"""
        return list(self.agents.keys())

class SubAgentBase:
    """Base class for subagents"""
    
    def __init__(self, name: str):
        self.name = name
        self.config: Dict[str, Any] = {}
    
    async def execute(self, task: Dict[Any, Any]) -> Dict[Any, Any]:
        """Execute task"""
        return {"status": "success", "agent": self.name, "task": task}

# Global registry instance
registry = SubAgentRegistry()

def init_registry() -> SubAgentRegistry:
    """Initialize registry with default agents"""
    for name in ["dev", "ads", "web", "content", "memory"]:
        registry.register(name, SubAgentBase(name))
    return registry

def get_registry() -> SubAgentRegistry:
    """Get global registry instance"""
    return registry