# messaging/rpc_client.py

import asyncio
import json
import uuid
import aio_pika
from aio_pika import Message, DeliveryMode, IncomingMessage

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.publish_channel = None
        self.consume_channel = None
        self.callback_queue = None
        self.pending_requests = {}
        self.semaphore = asyncio.Semaphore(100)

    async def connect(self, url: str):
        if self.connection:
            return

        self.connection = await aio_pika.connect_robust(url)

        self.publish_channel = await self.connection.channel()
        self.consume_channel = await self.connection.channel()

        self.callback_queue = await self.consume_channel.declare_queue(
            exclusive=True
        )

        await self.callback_queue.consume(self.on_response)

    async def on_response(self, message: IncomingMessage):
        async with message.process():
            corr_id = message.correlation_id

            if corr_id not in self.pending_requests:
                return

            future = self.pending_requests.pop(corr_id)

            if not future.done():
                future.set_result(json.loads(message.body))

    async def call(self, queue: str, payload: dict, timeout: int = 5):
        async with self.semaphore:
            corr_id = str(uuid.uuid4())
            loop = asyncio.get_event_loop()
            future = loop.create_future()

            self.pending_requests[corr_id] = future

            try:
                message = Message(
                    body=json.dumps(payload).encode(),
                    correlation_id=corr_id,
                    reply_to=self.callback_queue.name,
                    delivery_mode=DeliveryMode.PERSISTENT,
                )

                await self.publish_channel.default_exchange.publish(
                    message,
                    routing_key=queue
                )

                result = await asyncio.wait_for(future, timeout=timeout)

                if result.get("status") == "error":
                    raise Exception(result.get("error"))

                return result

            except asyncio.TimeoutError:
                self.pending_requests.pop(corr_id, None)
                raise Exception("Request timeout")

            finally:
                self.pending_requests.pop(corr_id, None)

    async def close(self):
        if self.connection:
            await self.connection.close()


# GLOBAL INSTANCE
rpc_client = RabbitMQClient()