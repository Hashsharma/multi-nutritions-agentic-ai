from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4

from core.context_manager import RequestContextManager
from core.logging import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to every request and set context."""
    
    async def dispatch(self, request: Request, call_next):
        # Get or create request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        
        # Create request context
        context = RequestContextManager.create_context(request_id=request_id)
        
        # Add to request state
        request.state.request_id = request_id
        request.state.context = context
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Clear context
        RequestContextManager.clear_context()
        
        return response