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
                "app/agent/subagent_registry.py",
                "app/agent/master_agent.py",
                "tests/",
            ],
            "agent_routing": [
                "app/agent/master_agent.py",
                "app/agent/subagent_registry.py",
            ],
            "refactor": [
                "app/agent/subagent_registry.py",
                "app/agent/master_agent.py",
            ],
            "general_dev": [
                "app/agent/subagent_registry.py",
                "app/agent/master_agent.py",
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
        return preferred.get(focus) or (suspected_files[0] if suspected_files else "app/agent/subagent_registry.py")

    def _next_steps(self, focus: str) -> List[str]:
        plans = {
            "build_fix": [
                "Read the failing area and identify the exact break point",
                "Inspect the primary target file and related imports",
                "Prepare the smallest safe single-file change",
                "Run syntax/build validation",
                "Stop unless a second file is clearly necessary",
            ],
            "test_fix": [
                "Read the failing expectation",
                "Inspect the implementation path in the primary target file",
                "Prepare the smallest safe logic change",
                "Run focused validation",
                "Rollback immediately if the result regresses",
            ],
            "agent_routing": [
                "Inspect route selection and intent mapping",
                "Locate the smallest routing-only fix",
                "Limit the first attempt to one file",
                "Run focused routing validation",
                "Stop if a wider refactor seems necessary",
            ],
            "refactor": [
                "Identify the smallest unstable section",
                "Keep the cleanup local to one file",
                "Preserve public behavior",
                "Run validation after change",
                "Rollback if behavior drifts",
            ],
            "general_dev": [
                "Clarify the engineering outcome",
                "Inspect the primary target file",
                "Prepare a minimal one-file edit",
                "Validate before and after change",
                "Stop if scope expands",
            ],
        }
        return plans.get(focus, plans["general_dev"])

    def _validation_commands(self, focus: str) -> List[str]:
        base = [
            "python3 -m py_compile app/agent/subagent_registry.py",
            "python3 -m py_compile app/agent/master_agent.py",
        ]
        if focus == "test_fix":
            base.append("pytest -q")
        if focus == "agent_routing":
            base.append("/root/OpenManusOfficial/.venv/bin/python - <<'PY' ... routing smoke test ... PY")
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
            "build_fix": "Limit edits to imports, references, and small build-breaking fixes in one file.",
            "test_fix": "Limit edits to the smallest failing logic path while preserving external behavior.",
            "agent_routing": "Limit edits to routing, intent mapping, or handoff logic in one file first.",
            "refactor": "Prefer the smallest cleanup that reduces duplication without changing behavior.",
            "general_dev": "Prefer the smallest local edit with explicit validation and rollback.",
        }
        return strategies.get(focus, strategies["general_dev"])

    def _allowed_operations(self, focus: str) -> List[str]:
        ops = ["targeted_replace", "small_logic_adjustment", "import_fix", "mapping_fix"]
        if focus == "refactor":
            ops.append("small_cleanup")
        return ops

    def _preflight_checks(self, target_file: str) -> List[str]:
        checks = [f"test -f {target_file}"]
        if target_file.endswith(".py"):
            checks.append(f"python3 -m py_compile {target_file}")
        return checks

    def _postflight_checks(self, focus: str) -> List[str]:
        checks = [
            "python3 -m py_compile app/agent/subagent_registry.py",
            "python3 -m py_compile app/agent/master_agent.py",
        ]
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

    def _executor_contract(self, target_file: str, risk_level: str) -> Dict[str, Any]:
        return {
            "executor_type": "python_targeted_replace",
            "target_file": target_file,
            "requires_backup": True,
            "replace_mode": "exact_text_once",
            "max_replacements": 1,
            "rollback_on_failure": True,
            "validation_after_write": True,
            "placeholders": {
                "old_text": "<EXACT_OLD_TEXT>",
                "new_text": "<NEW_TEXT>",
            },
            "risk_level": risk_level,
        }

    def _auto_apply_guardrails(self, risk_level: str) -> List[str]:
        rules = [
            "Only one file may be edited in the first pass",
            "Only exact-text replacement is allowed",
            "Only one replacement may be applied",
            "A backup file must be created first",
            "Validation must run immediately after write",
        ]
        if risk_level == "high":
            rules.extend([
                "Do not auto-apply high-risk production or credential changes",
                "Require manual review before execution",
            ])
        return rules

    def _apply_loop(self, target_file: str, focus: str) -> Dict[str, Any]:
        backup_file = f"{target_file}.bak"
        commands = [
            f"cp {target_file} {backup_file}",
            f"# replace <EXACT_OLD_TEXT> with <NEW_TEXT> exactly once in {target_file}",
        ]
        if target_file.endswith(".py"):
            commands.append(f"python3 -m py_compile {target_file}")
        commands.extend(self._postflight_checks(focus))
        return {
            "mode": "targeted_replace_executor_ready",
            "target_file": target_file,
            "backup_file": backup_file,
            "commands": commands,
            "failure_action": f"cp {backup_file} {target_file}",
        }


    def _proposal_id(self, prompt: str, focus: str, target_file: str) -> str:
        import hashlib
        raw = f"{prompt}|{focus}|{target_file}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def _build_patch_proposal(
        self,
        prompt: str,
        focus: str,
        target_file: str,
        task: Dict[str, Any],
        risk_level: str,
        patch_strategy: str,
    ) -> Dict[str, Any]:
        old_text = task.get("old_text") if isinstance(task.get("old_text"), str) else "<EXACT_OLD_TEXT>"
        new_text = task.get("new_text") if isinstance(task.get("new_text"), str) else "<NEW_TEXT>"

        ready_to_apply = (
            isinstance(old_text, str) and old_text not in {"", "<EXACT_OLD_TEXT>"}
            and isinstance(new_text, str) and new_text != "<NEW_TEXT>"
        )

        proposal_id = self._proposal_id(prompt, focus, target_file)

        return {
            "proposal_id": proposal_id,
            "review_required": True,
            "review_status": "pending",
            "target_file": target_file,
            "focus": focus,
            "change_summary": f"{focus} için tek dosyalı exact-text replacement önerisi.",
            "patch_strategy": patch_strategy,
            "old_text": old_text,
            "new_text": new_text,
            "exact_match_required": True,
            "max_replacements": 1,
            "ready_to_apply": ready_to_apply,
            "risk_level": risk_level,
            "review_checklist": [
                "Hedef dosya doğru mu?",
                "old_text tam ve eksiksiz mi?",
                "new_text istenen son hali temsil ediyor mu?",
                "Değişiklik yalnızca tek eşleşme üretir mi?",
                "Rollback planı yeterli mi?",
            ],
        }

    def _apply_exact_text_once(self, target_file: str, old_text: str, new_text: str) -> Dict[str, Any]:
        from pathlib import Path
        import shutil
        import py_compile

        if not isinstance(old_text, str) or not old_text:
            return {
                "status": "blocked",
                "applied": False,
                "reason": "old_text must be a non-empty string",
            }

        if not isinstance(new_text, str):
            return {
                "status": "blocked",
                "applied": False,
                "reason": "new_text must be a string",
            }

        path = Path(target_file)
        backup = Path(f"{target_file}.bak")

        if not path.exists():
            return {
                "status": "blocked",
                "applied": False,
                "reason": f"target file not found: {target_file}",
            }

        original = path.read_text(encoding="utf-8")
        count = original.count(old_text)

        if count != 1:
            return {
                "status": "blocked",
                "applied": False,
                "reason": f"old_text must match exactly once, found {count}",
                "target_file": target_file,
            }

        shutil.copy2(path, backup)

        try:
            updated = original.replace(old_text, new_text, 1)
            path.write_text(updated, encoding="utf-8")

            if path.suffix == ".py":
                py_compile.compile(str(path), doraise=True)

            return {
                "status": "success",
                "applied": True,
                "target_file": target_file,
                "backup_file": str(backup),
                "match_count": count,
                "validation": "py_compile_passed" if path.suffix == ".py" else "write_passed",
            }
        except Exception as e:
            if backup.exists():
                shutil.copy2(backup, path)
            return {
                "status": "rolled_back",
                "applied": False,
                "target_file": target_file,
                "backup_file": str(backup),
                "error": str(e),
            }

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
        executor_contract = self._executor_contract(primary_target_file, risk_level)
        auto_apply_guardrails = self._auto_apply_guardrails(risk_level)
        apply_loop = self._apply_loop(primary_target_file, focus)
        patch_proposal = self._build_patch_proposal(
            prompt=prompt,
            focus=focus,
            target_file=primary_target_file,
            task=task,
            risk_level=risk_level,
            patch_strategy=patch_strategy,
        )

        result = {
            "status": "success",
            "agent": self.name,
            "action": "build_or_fix",
            "summary": (
                f"Development request classified as {focus}. "
                f"Goal: {prompt or 'unspecified development task'}. "
                f"This agent now produces a patch proposal and requires review approval before execution."
            ),
            "focus": focus,
            "execution_mode": "proposal_review_gate_ready",
            "primary_target_file": primary_target_file,
            "suspected_files": suspected_files,
            "patch_strategy": patch_strategy,
            "allowed_operations": allowed_operations,
            "single_file_patch_plan": single_file_patch_plan,
            "executor_contract": executor_contract,
            "auto_apply_guardrails": auto_apply_guardrails,
            "patch_proposal": patch_proposal,
            "preflight_checks": preflight_checks,
            "postflight_checks": postflight_checks,
            "rollback_plan": rollback_plan,
            "apply_loop": apply_loop,
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

        if task.get("apply_targeted_replace") is True:
            if risk_level == "high":
                result["execution_result"] = {
                    "status": "blocked",
                    "applied": False,
                    "reason": "high-risk requests require manual review before execution",
                }
                return result

            if task.get("review_approved") is not True:
                result["execution_result"] = {
                    "status": "blocked",
                    "applied": False,
                    "reason": "review approval required before execution",
                    "proposal_id": patch_proposal["proposal_id"],
                }
                return result

            provided_proposal_id = task.get("proposal_id")
            if provided_proposal_id and provided_proposal_id != patch_proposal["proposal_id"]:
                result["execution_result"] = {
                    "status": "blocked",
                    "applied": False,
                    "reason": "proposal_id mismatch",
                    "proposal_id": patch_proposal["proposal_id"],
                    "provided_proposal_id": provided_proposal_id,
                }
                return result

            target_file = task.get("target_file") or primary_target_file
            if target_file != primary_target_file:
                result["execution_result"] = {
                    "status": "blocked",
                    "applied": False,
                    "reason": "first pass must use the primary_target_file only",
                    "target_file": target_file,
                    "primary_target_file": primary_target_file,
                }
                return result

            old_text = task.get("old_text")
            new_text = task.get("new_text")
            result["execution_result"] = self._apply_exact_text_once(
                target_file=target_file,
                old_text=old_text,
                new_text=new_text,
            )

        return result


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
