from typing import Any, Dict, List, Optional


class SubAgentBase:
    def __init__(self, name: str):
        self.name = name
        self.config: Dict[str, Any] = {}

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "agent": self.name, "task": task}


class DevAgent(SubAgentBase):
    def _normalize(self, value: Any) -> str:
        return " ".join(str(value or "").strip().split())

    def _infer_dev_focus(self, prompt: str) -> str:
        t = prompt.lower()
        if any(x in t for x in [
            "build", "compile", "syntax", "import", "module", "dependency",
            "derleme", "import hatası", "import hatasi", "bağımlılık", "bagimlilik"
        ]):
            return "build_fix"
        if any(x in t for x in [
            "test", "failing test", "assert", "pytest", "unit test",
            "test hatası", "test hatasi", "başarısız test", "basarisiz test"
        ]):
            return "test_fix"
        if any(x in t for x in [
            "route", "routing", "agent", "intent", "registry",
            "yönlendirme", "yonlendirme", "ajan", "intent", "registry"
        ]):
            return "agent_routing"
        if any(x in t for x in [
            "refactor", "cleanup", "simplify", "stabilize",
            "refactor", "temizle", "sadeleştir", "sadelestir", "stabilize"
        ]):
            return "refactor"
        return "general_dev"

    def _suspected_files(self, focus: str) -> List[str]:
        mapping = {
            "build_fix": [
                "app/agent/master_agent.py",
                "app/agent/subagent_registry.py",
                "requirements.txt",
                "pyproject.toml",
            ],
            "test_fix": [
                "tests/",
                "app/agent/master_agent.py",
                "app/agent/subagent_registry.py",
            ],
            "agent_routing": [
                "app/agent/master_agent.py",
                "app/agent/subagent_registry.py",
            ],
            "refactor": [
                "app/agent/master_agent.py",
                "app/agent/subagent_registry.py",
            ],
            "general_dev": [
                "app/agent/master_agent.py",
                "app/agent/subagent_registry.py",
            ],
        }
        return mapping.get(focus, mapping["general_dev"])

    def _next_steps(self, focus: str) -> List[str]:
        plans = {
            "build_fix": [
                "Read the failing area and identify the exact break point",
                "Inspect the most likely Python files and imports",
                "Prepare the smallest safe code change",
                "Run syntax/build validation",
                "Review output and iterate only if needed",
            ],
            "test_fix": [
                "Read the failing test and isolate the expectation",
                "Inspect the implementation used by that test",
                "Apply the smallest logic correction",
                "Run the relevant test subset",
                "Review regressions before broader validation",
            ],
            "agent_routing": [
                "Inspect intent mapping and subagent routing flow",
                "Identify where the prompt is misclassified or dropped",
                "Patch the routing logic with minimal blast radius",
                "Run focused routing prompts as validation",
                "Confirm specialized agents still behave correctly",
            ],
            "refactor": [
                "Identify duplicated or unstable logic",
                "Choose the smallest structural cleanup",
                "Preserve external behavior while simplifying internals",
                "Run focused validation after cleanup",
                "Stop if behavior changes unexpectedly",
            ],
            "general_dev": [
                "Clarify the requested engineering outcome",
                "Inspect the most relevant source files",
                "Prepare a minimal safe patch plan",
                "Define validation commands before editing",
                "Apply and verify in small steps",
            ],
        }
        return plans.get(focus, plans["general_dev"])

    def _validation_commands(self, focus: str) -> List[str]:
        base = [
            "python3 -m py_compile app/agent/subagent_registry.py",
            "python3 -m py_compile app/agent/master_agent.py",
        ]
        if focus == "agent_routing":
            base.append("/root/OpenManusOfficial/.venv/bin/python - <<'PY' ... routing smoke test ... PY")
        elif focus == "test_fix":
            base.append("pytest -q")
        return base

    def _risk_level(self, prompt: str) -> str:
        t = prompt.lower()
        high_words = [
            "delete", "drop", "wipe", "production", "secret", "token", "auth", "security",
            "sil", "canlı", "canli", "token", "gizli", "kimlik"
        ]
        medium_words = [
            "routing", "agent", "build", "dependency", "test", "refactor",
            "yönlendirme", "yonlendirme", "ajan", "derleme", "bağımlılık", "bagimlilik", "test"
        ]
        if any(x in t for x in high_words):
            return "high"
        if any(x in t for x in medium_words):
            return "medium"
        return "low"

    def _patch_strategy(self, focus: str) -> str:
        strategies = {
            "build_fix": "Limit changes to imports, references, and minimal dependency-related edits.",
            "test_fix": "Limit changes to the failing logic path and preserve external behavior.",
            "agent_routing": "Limit changes to intent mapping, route selection, and registry wiring only.",
            "refactor": "Prefer structural cleanup without changing public behavior.",
            "general_dev": "Prefer the smallest local edit with explicit validation before any broader change.",
        }
        return strategies.get(focus, strategies["general_dev"])

    def _edit_scope(self, focus: str) -> Dict[str, Any]:
        return {
            "mode": "dry_run",
            "max_files": 2 if focus in {"agent_routing", "refactor", "general_dev"} else 3,
            "allow_new_files": False,
            "allow_delete": False,
            "allow_network": False,
            "allow_secrets_access": False,
        }

    def _stop_conditions(self, risk_level: str) -> List[str]:
        base = [
            "Stop if more than the expected files need to change",
            "Stop if validation fails before edit planning is complete",
            "Stop if the requested change implies broad refactoring",
        ]
        if risk_level == "high":
            base.extend([
                "Stop before any production-facing or credential-related action",
                "Stop if rollback is not clearly defined",
            ])
        return base

    def _dry_run_patch_plan(self, focus: str, suspected_files: List[str]) -> List[Dict[str, str]]:
        first = suspected_files[0] if suspected_files else "app/agent/subagent_registry.py"
        plans = {
            "build_fix": [
                {
                    "target_file": first,
                    "change_type": "inspect_imports_and_references",
                    "reason": "Build issues are usually caused by broken imports, names, or dependency assumptions."
                }
            ],
            "test_fix": [
                {
                    "target_file": first,
                    "change_type": "inspect_failing_logic_path",
                    "reason": "The smallest safe change is usually close to the failing assertion path."
                }
            ],
            "agent_routing": [
                {
                    "target_file": "app/agent/master_agent.py",
                    "change_type": "inspect_intent_mapping",
                    "reason": "Routing bugs often originate in intent-to-agent mapping."
                },
                {
                    "target_file": "app/agent/subagent_registry.py",
                    "change_type": "inspect_registry_and_agent_contracts",
                    "reason": "Routing can fail if registry names or returned structures drift."
                }
            ],
            "refactor": [
                {
                    "target_file": first,
                    "change_type": "inspect_duplicate_or_unstable_logic",
                    "reason": "Refactor work should start from the smallest repeated or fragile section."
                }
            ],
            "general_dev": [
                {
                    "target_file": first,
                    "change_type": "inspect_primary_execution_path",
                    "reason": "Start with the most likely file before considering wider edits."
                }
            ],
        }
        return plans.get(focus, plans["general_dev"])

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._normalize(task.get("prompt", ""))
        intent = self._normalize(task.get("intent", "development")) or "development"
        plan = task.get("plan") if isinstance(task.get("plan"), list) else []

        focus = self._infer_dev_focus(prompt)
        suspected_files = self._suspected_files(focus)
        next_steps = self._next_steps(focus)
        validation_commands = self._validation_commands(focus)
        risk_level = self._risk_level(prompt)
        patch_strategy = self._patch_strategy(focus)
        edit_scope = self._edit_scope(focus)
        stop_conditions = self._stop_conditions(risk_level)
        dry_run_patch_plan = self._dry_run_patch_plan(focus, suspected_files)

        summary = (
            f"Development request classified as {focus}. "
            f"Goal: {prompt or 'unspecified development task'}. "
            f"This agent is currently in dry-run mode and will only prepare a safe patch plan."
        )

        return {
            "status": "success",
            "agent": self.name,
            "action": "build_or_fix",
            "summary": summary,
            "focus": focus,
            "execution_mode": "dry_run",
            "suspected_files": suspected_files,
            "patch_strategy": patch_strategy,
            "dry_run_patch_plan": dry_run_patch_plan,
            "edit_scope": edit_scope,
            "next_steps": next_steps,
            "validation_commands": validation_commands,
            "stop_conditions": stop_conditions,
            "risk_level": risk_level,
            "task": {
                "prompt": prompt,
                "intent": intent,
                "plan": plan,
            },
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
