"""
AgentTool: Wraps any OpenManus agent as a stateless, MCP-compatible tool.

Each call creates a fresh agent instance, runs it to completion, and cleans up.
This ensures thread safety and predictable concurrent operation.
"""
import asyncio
from typing import Any, Type

from pydantic import Field

from app.logger import logger
from app.tool.base import BaseTool, ToolResult


class AgentTool(BaseTool):
    """
    A generic wrapper that exposes an OpenManus agent as a single-call MCP tool.

    The agent is instantiated fresh on every execute() call, ensuring complete
    isolation between requests. This is the "Agent-as-a-Tool" pattern.
    """

    agent_class: Any = Field(default=None, exclude=True)
    agent_config: dict = Field(default_factory=dict, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, agent_class: Type, **agent_config):
        agent_name = getattr(agent_class, "name", agent_class.__name__).lower()
        # Replace spaces/dashes for a clean tool name
        tool_name = f"run_{agent_name.replace('-', '_').replace(' ', '_')}"
        agent_description = getattr(
            agent_class, "description", "An OpenManus agent."
        )

        super().__init__(
            name=tool_name,
            description=(
                f"{agent_description}\n\n"
                f"Runs the {agent_class.__name__} agent autonomously to completion. "
                f"Provide a detailed natural language prompt describing the task."
            ),
        )
        # Store via object.__setattr__ to bypass pydantic immutability
        object.__setattr__(self, "agent_class", agent_class)
        object.__setattr__(self, "agent_config", agent_config)

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": (
                        "The natural language task description for the agent to execute."
                    ),
                }
            },
            "required": ["prompt"],
        }

    async def execute(self, prompt: str, **kwargs) -> ToolResult:
        """
        Creates a fresh agent instance, runs it with the given prompt,
        and ensures cleanup regardless of success or failure.
        """
        agent_class = object.__getattribute__(self, "agent_class")
        agent_config = object.__getattribute__(self, "agent_config")

        logger.info(f"[AgentTool] Spawning {agent_class.__name__} for prompt: {prompt[:80]}...")
        agent = None
        try:
            # Use async factory .create() if available (e.g., Manus), else direct init
            if hasattr(agent_class, "create") and asyncio.iscoroutinefunction(
                agent_class.create
            ):
                agent = await agent_class.create(**agent_config)
            else:
                agent = agent_class(**agent_config)

            result = await agent.run(prompt)
            logger.info(f"[AgentTool] {agent_class.__name__} completed successfully.")
            return ToolResult(output=result)

        except Exception as e:
            logger.error(f"[AgentTool] {agent_class.__name__} failed: {e}", exc_info=True)
            return ToolResult(output=f"Agent execution failed: {str(e)}", error=str(e))

        finally:
            if agent is not None and hasattr(agent, "cleanup"):
                try:
                    await agent.cleanup()
                except Exception as cleanup_err:
                    logger.warning(
                        f"[AgentTool] Cleanup failed for {agent_class.__name__}: {cleanup_err}"
                    )
