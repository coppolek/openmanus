from typing import Any, Dict, Optional

class SubAgentBase:
    def __init__(self, name: str):
        self.name = name
        self.config: Dict[str, Any] = {}

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "agent": self.name, "task": task}

class DevAgent(SubAgentBase):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": self.name,
            "action": "build_or_fix",
            "task": task,
        }

class AdsAgent(SubAgentBase):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": self.name,
            "action": "analyze_ads",
            "task": task,
        }

class WebAgent(SubAgentBase):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": self.name,
            "action": "research_web",
            "task": task,
        }

class ContentAgent(SubAgentBase):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": self.name,
            "action": "create_content",
            "task": task,
        }

class MemoryAgent(SubAgentBase):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": self.name,
            "action": "manage_memory",
            "task": task,
        }

class GeneralAgent(SubAgentBase):
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(task.get("prompt", "")).strip()
        intent = str(task.get("intent", "general")).strip() or "general"
        plan = task.get("plan") or []

        text = prompt.lower()
        risk_level = "low"
        if any(x in text for x in ["delete", "drop", "shutdown", "wipe", "production"]):
            risk_level = "high"
        elif any(x in text for x in ["strategy", "roadmap", "prioritization", "workflow", "budget"]):
            risk_level = "medium"

        summary = (
            f"General reasoning created for '{prompt or 'unspecified task'}' "
            f"under intent '{intent}'."
        )

        next_steps = []
        if plan:
            next_steps = [f"Follow plan step: {step}" for step in plan[:3]]
        else:
            next_steps = [
                "Clarify outcome",
                "Break task into steps",
                "Execute safest first action",
            ]

        return {
            "status": "success",
            "agent": self.name,
            "action": "general_reasoning",
            "summary": summary,
            "next_steps": next_steps,
            "risk_level": risk_level,
            "task": task,
        }

class SubAgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.routes: Dict[str, str] = {
            "/dev": "dev",
            "/ads": "ads",
            "/web": "web",
            "/content": "content",
            "/memory": "memory",
            "/general": "general",
        }

    def register(self, name: str, agent: Any) -> None:
        self.agents[name] = agent

    def get(self, name: str) -> Optional[Any]:
        return self.agents.get(name)

    def resolve_route(self, path: str) -> Optional[str]:
        for route, agent_name in self.routes.items():
            if path.startswith(route):
                return agent_name
        return None

    def route_to_agent(self, path: str) -> Optional[Any]:
        agent_name = self.resolve_route(path)
        return self.get(agent_name) if agent_name else None

    def list_agents(self) -> list[str]:
        return list(self.agents.keys())

registry = SubAgentRegistry()

def init_registry() -> SubAgentRegistry:
    defaults = {
        "dev": DevAgent("dev"),
        "ads": AdsAgent("ads"),
        "web": WebAgent("web"),
        "content": ContentAgent("content"),
        "memory": MemoryAgent("memory"),
        "general": GeneralAgent("general"),
    }
    for name, agent in defaults.items():
        registry.register(name, agent)
    return registry

def get_registry() -> SubAgentRegistry:
    return registry
