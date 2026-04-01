import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union

from pydantic import BaseModel, Field

from app.utils.logger import logger


# class BaseTool(ABC, BaseModel):
#     name: str
#     description: str
#     parameters: Optional[dict] = None

#     class Config:
#         arbitrary_types_allowed = True

#     async def __call__(self, **kwargs) -> Any:
#         """Execute the tool with given parameters."""
#         return await self.execute(**kwargs)

#     @abstractmethod
#     async def execute(self, **kwargs) -> Any:
#         """Execute the tool with given parameters."""

#     def to_param(self) -> Dict:
#         """Convert tool to function call format."""
#         return {
#             "type": "function",
#             "function": {
#                 "name": self.name,
#                 "description": self.description,
#                 "parameters": self.parameters,
#             },
#         }


class ToolResult(BaseModel):
    """Represents the result of a tool execution."""

    output: Any = Field(default=None)
    error: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)
    system: Optional[str] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __bool__(self):
        return any(getattr(self, field) for field in self.__fields__)

    def __add__(self, other: "ToolResult"):
        def combine_fields(
            field: Optional[str], other_field: Optional[str], concatenate: bool = True
        ):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
            system=combine_fields(self.system, other.system),
        )

    def __str__(self):
        return f"Error: {self.error}" if self.error else self.output

    def replace(self, **kwargs):
        """Returns a new ToolResult with the given fields replaced."""
        # return self.copy(update=kwargs)
        return type(self)(**{**self.dict(), **kwargs})

class GuardrailCheckResult(BaseModel):
    """Represents the result of a guardrail check before tool execution."""

    allowed: bool = Field(description="Whether the tool call is allowed")
    reason: Optional[str] = Field(
        default=None,
        description="Reason for denial (if not allowed) or informational message (if allowed)",
    )

    def __bool__(self):
        return self.allowed


class GuardrailProvider(Protocol):
    """
    Protocol for pluggable guardrail providers.

    Implement this protocol to add custom authorization logic
    before a tool is executed. For example:
    - Allowlist/blocklist-based filtering
    - Rate limiting
    - Cost estimation
    - Audit logging

    Example:
        class AllowlistGuardrail:
            async def check(self, tool_name: str, args: dict) -> GuardrailCheckResult:
                if tool_name in self.allowed_tools:
                    return GuardrailCheckResult(allowed=True, reason="Tool is allowed")
                return GuardrailCheckResult(allowed=False, reason=f"Tool '{tool_name}' is not allowed")
    """

    async def check(self, tool_name: str, args: dict) -> GuardrailCheckResult:
        """Check if the tool call is authorized.

        Args:
            tool_name: Name of the tool being called
            args: Arguments passed to the tool

        Returns:
            GuardrailCheckResult indicating whether the call should proceed
        """
        ...


class AllowlistGuardrail:
    """
    Built-in allowlist-based guardrail provider.

    Simple implementation that maintains a list of allowed tool names.
    All other tools are denied by default.
    """

    def __init__(self, allowed_tools: Optional[List[str]] = None):
        """
        Initialize the allowlist guardrail.

        Args:
            allowed_tools: List of tool names that are allowed to execute.
                          If None, all tools are allowed.
        """
        self.allowed_tools: Optional[List[str]] = allowed_tools

    async def check(self, tool_name: str, args: dict) -> GuardrailCheckResult:
        """Check if the tool is in the allowlist."""
        if self.allowed_tools is None:
            return GuardrailCheckResult(
                allowed=True,
                reason="AllowlistGuardrail: no restriction (allowed_tools is None)",
            )
        if tool_name in self.allowed_tools:
            return GuardrailCheckResult(
                allowed=True,
                reason=f"Tool '{tool_name}' is in the allowlist",
            )
        return GuardrailCheckResult(
            allowed=False,
            reason=f"Tool '{tool_name}' is not in the allowlist. Allowed tools: {self.allowed_tools}",
        )


class BaseTool(ABC, BaseModel):
    """Consolidated base class for all tools combining BaseModel and Tool functionality.

    Provides:
    - Pydantic model validation
    - Schema registration
    - Standardized result handling
    - Abstract execution interface
    - Pre-execution guardrail authorization (optional)

    Attributes:
        name (str): Tool name
        description (str): Tool description
        parameters (dict): Tool parameters schema
        guardrail_provider (Optional[GuardrailProvider]): Authorization hook called before execute().
            If None, all calls are allowed by default. Default: None.
        _schemas (Dict[str, List[ToolSchema]]): Registered method schemas
    """

    name: str
    description: str
    parameters: Optional[dict] = None
    guardrail_provider: Optional[GuardrailProvider] = Field(default=None, exclude=True)
    # _schemas: Dict[str, List[ToolSchema]] = {}

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = False

    # def __init__(self, **data):
    #     """Initialize tool with model validation and schema registration."""
    #     super().__init__(**data)
    #     logger.debug(f"Initializing tool class: {self.__class__.__name__}")
    #     self._register_schemas()

    # def _register_schemas(self):
    #     """Register schemas from all decorated methods."""
    #     for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
    #         if hasattr(method, 'tool_schemas'):
    #             self._schemas[name] = method.tool_schemas
    #             logger.debug(f"Registered schemas for method '{name}' in {self.__class__.__name__}")

    async def __call__(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        return await self.execute(**kwargs)

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters.

        Subclasses should override this method with their actual tool logic.
        The guardrail check (if configured) is called automatically by this base class.
        """

    async def _execute(self, **kwargs) -> ToolResult:
        """
        Internal execution method that runs after guardrail check passes.

        Override this in subclasses instead of `execute()` if you want
        the guardrail check to be applied automatically.
        """
        result = await self.execute(**kwargs)
        if isinstance(result, ToolResult):
            return result
        return self.success_response(result)

    async def _run_with_guardrail(self, **kwargs) -> ToolResult:
        """Execute with guardrail authorization check.

        This method checks the guardrail before executing the tool.
        Returns a denied ToolResult if the guardrail rejects the call.
        """
        if self.guardrail_provider is not None:
            check_result = await self.guardrail_provider.check(self.name, kwargs)
            if not check_result.allowed:
                from app.utils.logger import logger

                logger.warning(
                    f"Guardrail denied tool '{self.name}': {check_result.reason}"
                )
                return ToolResult(
                    error=f"Tool call denied by guardrail: {check_result.reason}"
                )
        return await self._execute(**kwargs)

    def to_param(self) -> Dict:
        """Convert tool to function call format.

        Returns:
            Dictionary with tool metadata in OpenAI function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    # def get_schemas(self) -> Dict[str, List[ToolSchema]]:
    #     """Get all registered tool schemas.

    #     Returns:
    #         Dict mapping method names to their schema definitions
    #     """
    #     return self._schemas

    def success_response(self, data: Union[Dict[str, Any], str]) -> ToolResult:
        """Create a successful tool result.

        Args:
            data: Result data (dictionary or string)

        Returns:
            ToolResult with success=True and formatted output
        """
        if isinstance(data, str):
            text = data
        else:
            text = json.dumps(data, indent=2)
        logger.debug(f"Created success response for {self.__class__.__name__}")
        return ToolResult(output=text)

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with guardrail check.

        This base implementation applies the guardrail check and then
        delegates to the subclass's actual execution logic.
        Subclasses should override `_execute()` for their logic.
        """
        return await self._run_with_guardrail(**kwargs)

    def fail_response(self, msg: str) -> ToolResult:
        """Create a failed tool result.

        Args:
            msg: Error message describing the failure

        Returns:
            ToolResult with success=False and error message
        """
        logger.debug(f"Tool {self.__class__.__name__} returned failed result: {msg}")
        return ToolResult(error=msg)


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""


class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""
