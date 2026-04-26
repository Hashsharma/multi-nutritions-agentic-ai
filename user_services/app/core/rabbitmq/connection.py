import aio_pika
from typing import Optional
from .config import RabbitMQConfig
from .exceptions import ConnectionError

class RabbitMQConnection:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self._queues = {}
        
    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(
                self.config.url,
                timeout=self.config.connection_timeout
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.config.prefetch_count)
        except Exception as e:
            raise ConnectionError(f"Failed to connect: {e}")
    
    async def get_queue(self, queue_name: str) -> aio_pika.Queue:
        if queue_name not in self._queues:
            self._queues[queue_name] = await self.channel.declare_queue(
                queue_name, 
                durable=self.config.durable
            )
        return self._queues[queue_name]
    
    async def close(self) -> None:
        if self.connection:
            await self.connection.close()