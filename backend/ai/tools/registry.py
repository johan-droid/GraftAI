"""
Tool Registry System

Manages agent tools with:
- Tool registration and discovery
- Parameter validation
- Execution tracking
- Error handling
- Tool selection for LLM
"""

from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import functools
import inspect

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ToolCategory(Enum):
    """Categories of tools"""
    COMMUNICATION = "communication"
    SCHEDULING = "scheduling"
    CRM = "crm"
    DATA_ANALYSIS = "data_analysis"
    QUERY = "query"


class ToolPriority(Enum):
    """Priority levels for tool execution"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ToolDefinition:
    """Definition of a tool that agents can use"""
    name: str
    description: str
    function: Callable
    category: ToolCategory
    parameters: Dict[str, Any]  # JSON Schema
    required_params: List[str]
    examples: List[Dict[str, Any]] = field(default_factory=list)
    priority: ToolPriority = ToolPriority.MEDIUM
    is_async: bool = True
    requires_auth: bool = True
    rate_limit: Optional[int] = None  # Calls per minute
    timeout_seconds: int = 30
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }


@dataclass
class ToolExecution:
    """Record of a tool execution"""
    tool_name: str
    parameters: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    success: bool = False
    execution_time_ms: float = 0.0
    retry_count: int = 0


class ToolRegistry:
    """
    Central registry for all agent tools
    
    Features:
    - Tool registration with decorators
    - Automatic parameter extraction
    - Execution tracking and metrics
    - Tool selection based on context
    - Batch execution support
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executions: List[ToolExecution] = []
        self._category_map: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
        self._lock = asyncio.Lock()
    
    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: ToolCategory = ToolCategory.QUERY,
        priority: ToolPriority = ToolPriority.MEDIUM,
        examples: Optional[List[Dict]] = None,
        timeout: int = 30
    ):
        """
        Decorator to register a function as a tool
        
        Example:
            @tool_registry.register(
                name="send_email",
                description="Send an email to a recipient",
                category=ToolCategory.COMMUNICATION
            )
            async def send_email(to: str, subject: str, body: str):
                ...
        """
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or f"Execute {tool_name}"
            
            # Extract parameters from function signature
            sig = inspect.signature(func)
            params_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'cls']:
                    continue
                
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_type = "object"
                
                params_schema["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    params_schema["required"].append(param_name)
            
            tool_def = ToolDefinition(
                name=tool_name,
                description=tool_desc,
                function=func,
                category=category,
                parameters=params_schema,
                required_params=params_schema["required"],
                examples=examples or [],
                priority=priority,
                is_async=asyncio.iscoroutinefunction(func),
                timeout_seconds=timeout
            )
            
            self._tools[tool_name] = tool_def
            self._category_map[category].append(tool_name)
            
            logger.info(f"Registered tool: {tool_name} ({category.value})")
            
            return func
        
        return decorator
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name"""
        return self._tools.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[ToolDefinition]:
        """List all tools or tools in a category"""
        if category:
            return [
                self._tools[name]
                for name in self._category_map[category]
                if name in self._tools
            ]
        return list(self._tools.values())
    
    def get_tools_for_llm(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get tools formatted for LLM function calling"""
        tools = []
        for tool_def in self._tools.values():
            if format == "openai":
                tools.append(tool_def.to_openai_function())
            elif format == "anthropic":
                tools.append(tool_def.to_anthropic_tool())
        return tools
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        max_retries: int = 2
    ) -> ToolExecution:
        """Execute a tool with retry logic"""
        tool_def = self._tools.get(tool_name)
        
        if not tool_def:
            return ToolExecution(
                tool_name=tool_name,
                parameters=parameters,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                error=f"Tool '{tool_name}' not found",
                success=False
            )
        
        execution = ToolExecution(
            tool_name=tool_name,
            parameters=parameters,
            start_time=datetime.utcnow()
        )
        
        # Validate parameters
        missing_params = [
            p for p in tool_def.required_params
            if p not in parameters
        ]
        
        if missing_params:
            execution.end_time = datetime.utcnow()
            execution.error = f"Missing required parameters: {missing_params}"
            return execution
        
        # Execute with retry
        for attempt in range(max_retries + 1):
            try:
                execution.retry_count = attempt
                
                if tool_def.is_async:
                    result = await asyncio.wait_for(
                        tool_def.function(**parameters),
                        timeout=tool_def.timeout_seconds
                    )
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        functools.partial(tool_def.function, **parameters)
                    )
                
                execution.result = result
                execution.success = True
                break
                
            except asyncio.TimeoutError:
                if attempt == max_retries:
                    execution.error = f"Tool execution timed out after {tool_def.timeout_seconds}s"
                else:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                if attempt == max_retries:
                    execution.error = str(e)
                    logger.error(f"Tool {tool_name} failed: {e}")
                else:
                    await asyncio.sleep(0.5 * (attempt + 1))
        
        execution.end_time = datetime.utcnow()
        execution.execution_time_ms = (
            execution.end_time - execution.start_time
        ).total_seconds() * 1000
        
        # Record execution
        async with self._lock:
            self._executions.append(execution)
        
        return execution
    
    async def execute_batch(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolExecution]:
        """Execute multiple tools in parallel"""
        tasks = [
            self.execute(
                call.get("tool_name"),
                call.get("parameters", {})
            )
            for call in tool_calls
        ]
        
        return await asyncio.gather(*tasks)
    
    def get_tool_suggestions(
        self,
        context: str,
        intent: str,
        n_suggestions: int = 3
    ) -> List[ToolDefinition]:
        """Suggest relevant tools based on context and intent"""
        # Simple keyword matching (can be enhanced with embeddings)
        suggestions = []
        context_lower = context.lower()
        intent_lower = intent.lower()
        
        for tool_def in self._tools.values():
            score = 0
            
            # Check description match
            desc_words = set(tool_def.description.lower().split())
            context_words = set(context_lower.split())
            intent_words = set(intent_lower.split())
            
            desc_match = len(desc_words & context_words)
            intent_match = len(desc_words & intent_words)
            
            score += desc_match * 2
            score += intent_match * 3
            
            # Boost by priority
            if tool_def.priority == ToolPriority.CRITICAL:
                score += 5
            elif tool_def.priority == ToolPriority.HIGH:
                score += 3
            
            if score > 0:
                suggestions.append((score, tool_def))
        
        # Sort by score and return top N
        suggestions.sort(key=lambda x: x[0], reverse=True)
        return [tool for _, tool in suggestions[:n_suggestions]]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool execution metrics"""
        if not self._executions:
            return {"total_executions": 0}
        
        total = len(self._executions)
        successful = sum(1 for e in self._executions if e.success)
        failed = total - successful
        
        avg_time = sum(
            e.execution_time_ms for e in self._executions
        ) / total if total > 0 else 0
        
        # Tool-specific stats
        tool_stats = {}
        for tool_name in self._tools.keys():
            tool_execs = [e for e in self._executions if e.tool_name == tool_name]
            if tool_execs:
                tool_success = sum(1 for e in tool_execs if e.success)
                tool_stats[tool_name] = {
                    "total": len(tool_execs),
                    "success": tool_success,
                    "failure": len(tool_execs) - tool_success,
                    "avg_time_ms": sum(e.execution_time_ms for e in tool_execs) / len(tool_execs)
                }
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "avg_execution_time_ms": avg_time,
            "tool_stats": tool_stats
        }
    
    async def clear_executions(self):
        """Clear execution history"""
        async with self._lock:
            self._executions.clear()


# Global registry instance
tool_registry = ToolRegistry()

# Convenience functions
def register_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: ToolCategory = ToolCategory.QUERY,
    priority: ToolPriority = ToolPriority.MEDIUM,
    examples: Optional[List[Dict]] = None,
    timeout: int = 30
):
    """Decorator to register a tool"""
    return tool_registry.register(
        name=name,
        description=description,
        category=category,
        priority=priority,
        examples=examples,
        timeout=timeout
    )


def get_tool(name: str) -> Optional[ToolDefinition]:
    """Get a tool by name"""
    return tool_registry.get_tool(name)


def list_tools(category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
    """List registered tools"""
    return tool_registry.list_tools(category)


async def execute_tool(
    name: str,
    parameters: Dict[str, Any],
    max_retries: int = 2
) -> ToolExecution:
    """Execute a tool"""
    return await tool_registry.execute(name, parameters, max_retries)


async def execute_tools_batch(
    tool_calls: List[Dict[str, Any]]
) -> List[ToolExecution]:
    """Execute multiple tools in parallel"""
    return await tool_registry.execute_batch(tool_calls)
