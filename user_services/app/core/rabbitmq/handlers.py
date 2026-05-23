from typing import Callable, Dict, Any
from .exceptions import HandlerNotFoundError, MessageProcessingError

class HandlerRegistry:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, queue_name: str):
        def decorator(func: Callable):
            self._handlers[queue_name] = func
            return func
        return decorator
    
    def get_handler(self, queue_name: str) -> Callable:
        if queue_name not in self._handlers:
            raise HandlerNotFoundError(f"No handler for queue: {queue_name}")
        return self._handlers[queue_name]
    
    async def process(self, queue_name: str, data: dict, **kwargs) -> Any:
        handler = self.get_handler(queue_name)
        try:
            return await handler(data, **kwargs)
        except Exception as e:
            raise MessageProcessingError(f"Handler error: {e}")