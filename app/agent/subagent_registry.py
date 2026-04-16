from typing import Any, Dict, List, Optional


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
    def _normalize_prompt(self, prompt: Any) -> str:
        return " ".join(str(prompt or "").strip().split())

    def _infer_topic(self, text: str) -> str:
        t = text.lower()
        if any(x in t for x in [
            "roadmap", "quarter", "quarterly", "milestone", "priority", "prioritization",
            "yol haritası", "yol haritasi", "çeyrek", "ceyrek", "öncelik", "oncelik", "önceliklendirme", "onceliklendirme"
        ]):
            return "roadmap"
        if any(x in t for x in [
            "workflow", "process", "team", "handoff", "operation", "ops",
            "iş akışı", "is akisi", "iş akisi", "sureç", "süreç", "ekip", "devir"
        ]):
            return "workflow"
        if any(x in t for x in [
            "strategy", "long term", "long-term", "vision", "positioning",
            "strateji", "uzun vadeli", "vizyon", "konumlandırma", "konumlandirma"
        ]):
            return "strategy"
        if any(x in t for x in [
            "launch", "rollout", "release", "deploy", "go live",
            "yayın", "yayin", "yayına al", "yayina al", "sürüm", "surum", "dağıtım", "dagitim"
        ]):
            return "rollout"
        if any(x in t for x in [
            "risk", "safer", "safe", "security", "production",
            "riskli", "güvenli", "guvenli", "güvenlik", "guvenlik", "canlı", "canli", "prod"
        ]):
            return "risk"
        return "general"

    def _infer_risk(self, text: str) -> str:
        t = text.lower()
        high_words = [
            "delete", "drop", "wipe", "shutdown", "production", "prod",
            "payment", "billing", "credential", "secret", "token",
            "security", "legal", "customer data",
            "sil", "kaldır", "kaldir", "canlı", "canli", "ödeme", "odeme", "müşteri verisi", "musteri verisi"
        ]
        medium_words = [
            "strategy", "roadmap", "workflow", "rollout", "budget",
            "team", "launch", "migration", "change",
            "strateji", "yol haritası", "yol haritasi", "iş akışı", "is akisi",
            "ekip", "yayın", "yayin", "geçiş", "gecis", "değişim", "degisim", "çeyrek", "ceyrek"
        ]
        if any(x in t for x in high_words):
            return "high"
        if any(x in t for x in medium_words):
            return "medium"
        return "low"

    def _default_plan(self, topic: str) -> List[str]:
        plans = {
            "roadmap": [
                "Define target outcome and constraints",
                "List candidate initiatives",
                "Prioritize by impact, effort, and urgency",
                "Sequence work into staged milestones",
                "Assign owners, risks, and success metrics",
            ],
            "workflow": [
                "Map the current workflow end to end",
                "Identify bottlenecks, delays, and unclear ownership",
                "Propose a simpler workflow with explicit handoffs",
                "Define measurable operating rules and metrics",
                "Roll out in stages and review weekly",
            ],
            "strategy": [
                "Clarify the long-term objective",
                "Compare the main strategic options and trade-offs",
                "Choose the safest staged direction",
                "Define execution milestones and checkpoints",
                "Track leading indicators and revisit assumptions",
            ],
            "rollout": [
                "Define rollout scope and non-goals",
                "Identify dependencies and failure points",
                "Create a phased rollout plan",
                "Add rollback and monitoring checkpoints",
                "Review results before wider release",
            ],
            "risk": [
                "Identify the highest-risk actions",
                "Reduce blast radius with staged execution",
                "Add validation and rollback checks",
                "Define stop conditions before execution",
                "Document owners and escalation path",
            ],
            "general": [
                "Clarify the desired result",
                "Break the work into safe, ordered steps",
                "Choose the highest-value first action",
                "Define validation criteria",
                "Review outcome and adjust",
            ],
        }
        return plans.get(topic, plans["general"])

    def _clean_plan(self, plan: Any, topic: str) -> List[str]:
        if not isinstance(plan, list):
            return self._default_plan(topic)

        cleaned = []
        for item in plan:
            text = " ".join(str(item).strip().split())
            if text:
                cleaned.append(text)

        generic = {"Analyze general", "Execute general", "Validate"}
        if not cleaned or set(cleaned) == generic:
            return self._default_plan(topic)

        return cleaned[:5]

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._normalize_prompt(task.get("prompt", ""))
        intent = self._normalize_prompt(task.get("intent", "general")) or "general"
        topic = self._infer_topic(prompt)
        plan = self._clean_plan(task.get("plan"), topic)
        risk_level = self._infer_risk(prompt)

        summary = (
            f"Request classified as {topic}. "
            f"Goal: {prompt or 'unspecified task'}. "
            f"Recommended approach is staged and structured."
        )

        return {
            "status": "success",
            "agent": self.name,
            "action": "general_reasoning",
            "summary": summary,
            "next_steps": plan,
            "risk_level": risk_level,
            "task": {
                "prompt": prompt,
                "intent": intent,
                "plan": plan,
            },
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

    def list_agents(self) -> List[str]:
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
