import asyncio
from typing import Dict, Any
from app.agent.manus import Manus
from app.logger import logger
from app.agent.subagent_registry import init_registry, get_registry

class IntentRouter:
    def __init__(self):
        self.routes = {
            "dev": "development","ads": "advertising","web": "website",
            "content": "content_creation","memory": "memory_management"
        }
    def route(self, text: str) -> str:
        for k, v in self.routes.items():
            if k in text.lower(): return v
        return "general"

class Planner:
    def __init__(self):
        self.plans = []
    def plan(self, intent: str, context: Dict) -> list:
        self.plans = [f"Analyze {intent}", f"Execute {intent}", "Validate"]
        return self.plans

class Memory:
    def __init__(self):
        self.store = {}
    def save(self, key: str, value: Any): self.store[key] = value
    def get(self, key: str): return self.store.get(key)

class ToolRegistry:
    def __init__(self):
        self.tools = {}
    def register(self, name: str, tool: Any): self.tools[name] = tool
    def get(self, name: str): return self.tools.get(name)

class ApprovalPolicy:
    def check(self, action: str) -> bool:
        return "delete" not in action.lower() and "remove" not in action.lower()

class SelfEvaluator:
    def evaluate(self, result: Any) -> float:
        return 0.8 if result else 0.2

class MasterAgent:
    def __init__(self):
        self.router = IntentRouter()
        self.planner = Planner()
        self.memory = Memory()
        self.tools = ToolRegistry()
        self.approval = ApprovalPolicy()
        self.evaluator = SelfEvaluator()
        self.manus = None
    
    async def initialize(self):
        self.manus = await Manus.create()
        self.tools.register("manus", self.manus)
        init_registry()
        logger.info("MasterAgent initialized")
    
    async def run(self, prompt: str) -> Any:
        intent = self.router.route(prompt)
        self.memory.save("last_intent", intent)
        route_name = {
            "content_creation": "content",
            "memory_management": "memory"
        }.get(intent, intent)
        subagent = get_registry().get(route_name)
        self.memory.save("last_subagent", route_name if subagent else "general")
        
        plans = self.planner.plan(intent, {"prompt": prompt})
        if subagent and route_name != "general":
            result = await subagent.execute({
                "prompt": prompt,
                "intent": intent,
                "plan": plans,
            })
            score = self.evaluator.evaluate(result)
            self.memory.save("last_score", score)
            self.memory.save("last_result_source", route_name)
            return result if score > 0.5 else None

        for step in plans:
            if not self.approval.check(step):
                logger.warning(f"Step rejected: {step}")
                continue
            if self.manus:
                result = await self.manus.run(step)
                score = self.evaluator.evaluate(result)
                self.memory.save("last_score", score)
                self.memory.save("last_result_source", "manus")
                if score > 0.5:
                    return result
        return None
    
    async def cleanup(self):
        if self.manus: await self.manus.cleanup()

async def main():
    agent = MasterAgent()
    await agent.initialize()
    try:
        prompt = input("Enter your prompt: ")
        await agent.run(prompt)
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())