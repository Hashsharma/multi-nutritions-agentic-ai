from contextvars import ContextVar
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# from core.logging import request_id_var, user_id_var, agent_name_var, logger


@dataclass
class RequestContext:
    """Complete request context for tracing."""
    request_id: str
    user_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    parent_span_id: Optional[str] = None
    span_id: str = field(default_factory=lambda: str(uuid4()))
    start_time: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_execution_order: list = field(default_factory=list)
    
    def add_agent_execution(self, agent_name: str):
        """Record agent execution in order."""
        self.agent_execution_order.append({
            "agent": agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "span_id": str(uuid4()),
        })
    
    def get_execution_time_ms(self) -> int:
        """Get total execution time in milliseconds."""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        return int(elapsed)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "duration_ms": self.get_execution_time_ms(),
            "agent_execution_order": self.agent_execution_order,
        }


# Context variable for request context
request_context_var: ContextVar[Optional[RequestContext]] = ContextVar("request_context", default=None)


class RequestContextManager:
    """Manager for request context lifecycle."""
    
    @staticmethod
    def create_context(
        request_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        **metadata
    ) -> RequestContext:
        """Create new request context."""
        context = RequestContext(
            request_id=request_id or str(uuid4()),
            user_id=user_id,
            metadata=metadata,
        )
        
        # Set context variables
        request_id_var.set(context.request_id)
        if user_id:
            user_id_var.set(user_id)
        
        # Store full context
        request_context_var.set(context)
        
        logger.info("Request context created", **context.to_dict())
        return context
    
    @staticmethod
    def get_current_context() -> Optional[RequestContext]:
        """Get current request context."""
        return request_context_var.get()
    
    @staticmethod
    def set_agent_context(agent_name: str):
        """Set current agent context."""
        agent_name_var.set(agent_name)
        
        context = request_context_var.get()
        if context:
            context.add_agent_execution(agent_name)
    
    @staticmethod
    def clear_context():
        """Clear current context."""
        request_id_var.set(None)
        user_id_var.set(None)
        agent_name_var.set(None)
        request_context_var.set(None)


class AgentContext:
    """Context manager for agent execution."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.previous_agent = None
    
    def __enter__(self):
        self.previous_agent = agent_name_var.get()
        RequestContextManager.set_agent_context(self.agent_name)
        return self
    
    def __exit__(self, *args):
        if self.previous_agent:
            agent_name_var.set(self.previous_agent)
        else:
            agent_name_var.set(None)


async def with_request_context(func, request_id: Optional[str] = None, user_id: Optional[UUID] = None):
    """Decorator to run function with request context."""
    context = RequestContextManager.create_context(request_id=request_id, user_id=user_id)
    try:
        return await func(context)
    finally:
        RequestContextManager.clear_context()