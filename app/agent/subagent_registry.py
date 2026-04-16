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
            "yönlendirme", "yonlendirme", "ajan", "registry"
        ]):
            return "agent_routing"
        if any(x in t for x in [
            "refactor", "cleanup", "simplify", "stabilize",
            "temizle", "sadeleştir", "sadelestir", "stabilize"
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

    def _primary_target_file(self, focus: str, suspected_files: List[str]) -> str:
        preferred = {
            "build_fix": "app/agent/master_agent.py",
            "test_fix": "app/agent/subagent_registry.py",
            "agent_routing": "app/agent/master_agent.py",
            "refactor": "app/agent/subagent_registry.py",
            "general_dev": "app/agent/subagent_registry.py",
        }
        target = preferred.get(focus)
        if target:
            return target
        return suspected_files[0] if suspected_files else "app/agent/subagent_registry.py"

    def _next_steps(self, focus: str) -> List[str]:
        plans = {
            "build_fix": [
                "Read the failing area and identify the exact break point",
                "Inspect the most likely Python file and imports",
                "Prepare the smallest safe code change",
                "Run syntax/build validation",
                "Review output and stop unless clearly needed",
            ],
            "test_fix": [
                "Read the failing test and isolate the expectation",
                "Inspect the implementation used by that test",
                "Prepare the smallest logic correction",
                "Run the relevant validation command",
                "Stop if the change spreads beyond the target file",
            ],
            "agent_routing": [
                "Inspect intent mapping and route selection",
                "Identify where classification or handoff fails",
                "Prepare a minimal routing-only patch",
                "Run focused routing validation",
                "Confirm specialized agents still behave correctly",
            ],
            "refactor": [
                "Identify duplicated or unstable logic",
                "Choose the smallest structural cleanup",
                "Preserve external behavior",
                "Run focused validation after cleanup",
                "Stop if behavior changes unexpectedly",
            ],
            "general_dev": [
                "Clarify the engineering outcome",
                "Inspect the primary target file",
                "Prepare a minimal single-file patch",
                "Define validation before applying",
                "Stop if the edit grows beyond scope",
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
            "sil", "canlı", "canli", "gizli", "kimlik"
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
            "build_fix": "Limit edits to imports, references, and small dependency-related fixes in one file.",
            "test_fix": "Limit edits to the failing logic path while preserving external behavior.",
            "agent_routing": "Limit edits to intent mapping, route selection, and agent handoff logic in one file first.",
            "refactor": "Prefer the smallest cleanup that reduces duplication without changing public behavior.",
            "general_dev": "Prefer the smallest local edit with explicit validation before any broader change.",
        }
        return strategies.get(focus, strategies["general_dev"])

    def _allowed_operations(self, focus: str) -> List[str]:
        ops = [
            "targeted_replace",
            "small_logic_adjustment",
            "import_fix",
            "mapping_fix",
        ]
        if focus == "refactor":
            ops.append("small_cleanup")
        return ops

    def _preflight_checks(self, target_file: str) -> List[str]:
        return [
            f"test -f {target_file}",
            f"python3 -m py_compile {target_file}" if target_file.endswith(".py") else "true",
        ]

    def _postflight_checks(self, focus: str) -> List[str]:
        checks = []
        if focus in {"build_fix", "agent_routing", "general_dev", "refactor", "test_fix"}:
            checks.extend([
                "python3 -m py_compile app/agent/subagent_registry.py",
                "python3 -m py_compile app/agent/master_agent.py",
            ])
        if focus == "test_fix":
            checks.append("pytest -q")
        return checks

    def _rollback_plan(self, target_file: str) -> Dict[str, str]:
        return {
            "backup_style": "copy_before_edit",
            "backup_file": f"{target_file}.bak",
            "restore_command": f"cp {target_file}.bak {target_file}",
        }

    def _stop_conditions(self, risk_level: str) -> List[str]:
        base = [
            "Stop if more than one primary source file needs editing",
            "Stop if validation fails before patching",
            "Stop if the requested fix implies broad refactoring",
            "Stop if the target file is unclear",
        ]
        if risk_level == "high":
            base.extend([
                "Stop before any production-facing or credential-related action",
                "Stop if rollback is not clearly available",
            ])
        return base

    def _single_file_patch_plan(self, focus: str, target_file: str) -> Dict[str, str]:
        plans = {
            "build_fix": {
                "target_file": target_file,
                "edit_intent": "Fix imports, references, or small build-breaking logic in a single file.",
                "apply_mode": "single_file_only",
            },
            "test_fix": {
                "target_file": target_file,
                "edit_intent": "Adjust the smallest failing logic path in a single file.",
                "apply_mode": "single_file_only",
            },
            "agent_routing": {
                "target_file": target_file,
                "edit_intent": "Fix routing or intent mapping in a single file before considering any second file.",
                "apply_mode": "single_file_only",
            },
            "refactor": {
                "target_file": target_file,
                "edit_intent": "Apply the smallest structural cleanup without changing public behavior.",
                "apply_mode": "single_file_only",
            },
            "general_dev": {
                "target_file": target_file,
                "edit_intent": "Prepare the smallest safe patch in one file.",
                "apply_mode": "single_file_only",
            },
        }
        return plans.get(focus, plans["general_dev"])

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._normalize(task.get("prompt", ""))
        intent = self._normalize(task.get("intent", "development")) or "development"
        plan = task.get("plan") if isinstance(task.get("plan"), list) else []

        focus = self._infer_dev_focus(prompt)
        suspected_files = self._suspected_files(focus)
        primary_target_file = self._primary_target_file(focus, suspected_files)
        next_steps = self._next_steps(focus)
        validation_commands = self._validation_commands(focus)
        risk_level = self._risk_level(prompt)
        patch_strategy = self._patch_strategy(focus)
        allowed_operations = self._allowed_operations(focus)
        preflight_checks = self._preflight_checks(primary_target_file)
        postflight_checks = self._postflight_checks(focus)
        rollback_plan = self._rollback_plan(primary_target_file)
        stop_conditions = self._stop_conditions(risk_level)
        single_file_patch_plan = self._single_file_patch_plan(focus, primary_target_file)

        summary = (
            f"Development request classified as {focus}. "
            f"Goal: {prompt or 'unspecified development task'}. "
            f"This agent is now preparing a controlled single-file patch plan."
        )

        return {
            "status": "success",
            "agent": self.name,
            "action": "build_or_fix",
            "summary": summary,
            "focus": focus,
            "execution_mode": "controlled_single_file_patch_plan",
            "primary_target_file": primary_target_file,
            "suspected_files": suspected_files,
            "patch_strategy": patch_strategy,
            "allowed_operations": allowed_operations,
            "single_file_patch_plan": single_file_patch_plan,
            "preflight_checks": preflight_checks,
            "postflight_checks": postflight_checks,
            "rollback_plan": rollback_plan,
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
