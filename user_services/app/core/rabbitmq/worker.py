import aio_pika
import json
import asyncio
from typing import Dict, Any, Optional
from asyncio import Future
import uuid
from inspect import signature

from .connection import RabbitMQConnection
from .config import RabbitMQConfig
from .handlers import HandlerRegistry


class RabbitMQWorker:
    def __init__(self, config: RabbitMQConfig = None):
        self.config = config or RabbitMQConfig()
        self.connection_mgr = RabbitMQConnection(self.config)
        self.handlers = HandlerRegistry()
        self._response_futures: Dict[str, Future] = {}
        self._deps = None  # Will be initialized when needed
        
    def _get_deps(self):
        """Lazy import of dependencies to avoid circular imports"""
        if self._deps is None:
            from user_services.app.core.rabbitmq.rabbitmq_deps import deps
            self._deps = deps
        return self._deps
        
    async def start_consumer(self):
        """Start worker as consumer (for standalone worker process)"""
        await self.connection_mgr.connect()
        
        for queue_name in self.handlers._handlers.keys():
            queue = await self.connection_mgr.get_queue(queue_name)
            await queue.consume(self._make_consumer_callback(queue_name))
            print(f"✅ Listening on queue: {queue_name}")
    
    async def _resolve_dependencies(self, handler_func, data: dict, correlation_id: str, reply_to: str):
        """Resolve all dependencies for a handler function - AWAITS them"""
        sig = signature(handler_func)
        resolved_args = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'data':
                resolved_args[param_name] = data
            elif param_name == 'correlation_id':
                resolved_args[param_name] = correlation_id
            elif param_name == 'reply_to':
                resolved_args[param_name] = reply_to
            elif hasattr(param.default, '__is_depends__'):
                # This is a dependency - resolve and AWAIT it
                deps = self._get_deps()
                resolved_args[param_name] = await deps.resolve(
                    param.default.dependency, 
                    data,
                    correlation_id=correlation_id,
                    reply_to=reply_to
                )
        
        return resolved_args
    
    def _make_consumer_callback(self, queue_name: str):
        async def callback(message: aio_pika.IncomingMessage):
            try:
                # Parse message
                data = json.loads(message.body.decode())
                print(f"📨 Received on {queue_name}: {data}")
                
                # Get handler function
                handler_func = self.handlers.get_handler(queue_name)
                
                # Resolve dependencies (AWAITED inside)
                resolved_args = await self._resolve_dependencies(
                    handler_func, 
                    data,
                    message.correlation_id,
                    message.reply_to
                )
                
                # Execute handler with resolved dependencies
                result = await handler_func(**resolved_args)
                
                # Send response if reply_to is specified
                if result and message.reply_to:
                    await self.connection_mgr.channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode(),
                            correlation_id=message.correlation_id
                        ),
                        routing_key=message.reply_to
                    )
                
                # Acknowledge message
                await message.ack()
                    
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                import traceback
                traceback.print_exc()
                await message.nack(requeue=False)
        
        return callback
    
    async def send_request(self, queue_name: str, data: Dict, timeout: int = 30) -> Dict:
        """Send request and wait for response"""
        if not self.connection_mgr.connection:
            await self.connection_mgr.connect()
            
        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()
        self._response_futures[correlation_id] = future
        
        # Setup response listener
        response_queue = await self.connection_mgr.get_queue(self.config.response_queue)
        await response_queue.consume(self._handle_response)
        
        # Send request
        queue = await self.connection_mgr.get_queue(queue_name)
        await self.connection_mgr.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                correlation_id=correlation_id,
                reply_to=self.config.response_queue
            ),
            routing_key=queue_name
        )
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._response_futures.pop(correlation_id, None)
            raise TimeoutError(f"Request to {queue_name} timed out after {timeout}s")
        finally:
            self._response_futures.pop(correlation_id, None)
    
    async def _handle_response(self, message: aio_pika.IncomingMessage):
        """Handle responses from workers"""
        async with message.process():
            corr_id = message.correlation_id
            if corr_id and corr_id in self._response_futures:
                data = json.loads(message.body.decode())
                self._response_futures[corr_id].set_result(data)
    
    async def publish(self, queue_name: str, data: Dict, correlation_id: str = None):
        """Fire and forget - no response needed"""
        if not self.connection_mgr.connection:
            await self.connection_mgr.connect()
            
        await self.connection_mgr.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                correlation_id=correlation_id or str(uuid.uuid4())
            ),
            routing_key=queue_name
        )
    
    async def close(self):
        """Graceful shutdown"""
        await self.connection_mgr.close()