"""Tool Registry for dynamic tool management."""

from typing import Dict, List, Optional, Set, Type
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from enum import Enum

from app.tool.base import BaseTool
from app.logger import logger


class ToolStatus(Enum):
    """Tool availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class ToolMetadata:
    """Metadata for registered tools."""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "system"
    tags: Set[str] = field(default_factory=set)
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: ToolStatus = ToolStatus.AVAILABLE
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    source: str = "local"  # local, mcp, plugin
    server_id: Optional[str] = None  # For MCP tools


class ToolRegistry:
    """Central registry for all tools in the system."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the registry."""
        if self._initialized:
            return
            
        async with self._lock:
            if not self._initialized:
                # Register built-in tools
                await self._register_builtin_tools()
                self._initialized = True
                logger.info("Tool registry initialized")
    
    async def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        # Import built-in tools
        try:
            from app.tool.python_execute import PythonExecute
            from app.tool.browser_use_tool import BrowserUseTool
            from app.tool.str_replace_editor import StrReplaceEditor
            from app.tool.ask_human import AskHuman
            from app.tool import Terminate
            
            builtin_tools = [
                (PythonExecute, {"tags": {"code", "execution"}, "capabilities": ["python"]}),
                (BrowserUseTool, {"tags": {"browser", "web"}, "capabilities": ["web_browsing"]}),
                (StrReplaceEditor, {"tags": {"editor", "file"}, "capabilities": ["file_editing"]}),
                (AskHuman, {"tags": {"interaction", "human"}, "capabilities": ["human_interaction"]}),
                (Terminate, {"tags": {"control", "system"}, "capabilities": ["termination"]}),
            ]
            
            for tool_class, extra_metadata in builtin_tools:
                await self.register_tool_class(tool_class, **extra_metadata)
                
        except ImportError as e:
            logger.error(f"Failed to import built-in tools: {e}")
    
    async def register_tool_class(
        self,
        tool_class: Type[BaseTool],
        **metadata_kwargs
    ) -> bool:
        """Register a tool class for later instantiation."""
        try:
            tool_name = tool_class.__name__
            
            async with self._lock:
                if tool_name in self._tool_classes:
                    logger.warning(f"Tool class {tool_name} already registered")
                    return False
                
                self._tool_classes[tool_name] = tool_class
                
                # Create metadata
                tool_instance = tool_class()
                metadata = ToolMetadata(
                    name=tool_instance.name,
                    description=tool_instance.description,
                    **metadata_kwargs
                )
                self._metadata[tool_instance.name] = metadata
                
                logger.info(f"Registered tool class: {tool_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register tool class {tool_class}: {e}")
            return False
    
    async def register_tool(
        self,
        tool: BaseTool,
        **metadata_kwargs
    ) -> bool:
        """Register a tool instance."""
        try:
            async with self._lock:
                if tool.name in self._tools:
                    logger.warning(f"Tool {tool.name} already registered")
                    return False
                
                self._tools[tool.name] = tool
                
                # Create or update metadata
                if tool.name not in self._metadata:
                    metadata = ToolMetadata(
                        name=tool.name,
                        description=tool.description,
                        **metadata_kwargs
                    )
                    self._metadata[tool.name] = metadata
                else:
                    # Update existing metadata
                    for key, value in metadata_kwargs.items():
                        if hasattr(self._metadata[tool.name], key):
                            setattr(self._metadata[tool.name], key, value)
                
                logger.info(f"Registered tool: {tool.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {e}")
            return False
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        async with self._lock:
            if tool_name in self._tools:
                del self._tools[tool_name]
                if tool_name in self._metadata:
                    del self._metadata[tool_name]
                logger.info(f"Unregistered tool: {tool_name}")
                return True
            return False
    
    async def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        async with self._lock:
            tool = self._tools.get(tool_name)
            
            # Try to instantiate from class if not found
            if not tool:
                for class_name, tool_class in self._tool_classes.items():
                    try:
                        instance = tool_class()
                        if instance.name == tool_name:
                            self._tools[tool_name] = instance
                            tool = instance
                            break
                    except Exception as e:
                        logger.error(f"Failed to instantiate {class_name}: {e}")
            
            # Update usage metadata
            if tool and tool_name in self._metadata:
                self._metadata[tool_name].usage_count += 1
                self._metadata[tool_name].last_used = datetime.now()
            
            return tool
    
    async def get_tools_by_tag(self, tag: str) -> List[BaseTool]:
        """Get all tools with a specific tag."""
        async with self._lock:
            tools = []
            for tool_name, metadata in self._metadata.items():
                if tag in metadata.tags and tool_name in self._tools:
                    tools.append(self._tools[tool_name])
            return tools
    
    async def get_tools_by_capability(self, capability: str) -> List[BaseTool]:
        """Get all tools with a specific capability."""
        async with self._lock:
            tools = []
            for tool_name, metadata in self._metadata.items():
                if capability in metadata.capabilities and tool_name in self._tools:
                    tools.append(self._tools[tool_name])
            return tools
    
    async def get_available_tools(self) -> List[BaseTool]:
        """Get all available tools."""
        async with self._lock:
            available = []
            for tool_name, tool in self._tools.items():
                if tool_name in self._metadata:
                    if self._metadata[tool_name].status == ToolStatus.AVAILABLE:
                        available.append(tool)
            return available
    
    async def update_tool_status(
        self,
        tool_name: str,
        status: ToolStatus,
        error_msg: Optional[str] = None
    ) -> bool:
        """Update tool status."""
        async with self._lock:
            if tool_name in self._metadata:
                self._metadata[tool_name].status = status
                if status == ToolStatus.ERROR:
                    self._metadata[tool_name].error_count += 1
                    if error_msg:
                        logger.error(f"Tool {tool_name} error: {error_msg}")
                return True
            return False
    
    async def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a tool."""
        async with self._lock:
            return self._metadata.get(tool_name)
    
    async def list_tools(self) -> Dict[str, ToolMetadata]:
        """List all registered tools with their metadata."""
        async with self._lock:
            return self._metadata.copy()
    
    async def cleanup(self) -> None:
        """Clean up registry resources."""
        async with self._lock:
            self._tools.clear()
            self._metadata.clear()
            self._tool_classes.clear()
            self._initialized = False
            logger.info("Tool registry cleaned up")


# Global registry instance
_registry: Optional[ToolRegistry] = None


async def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        await _registry.initialize()
    return _registry
