import asyncio
import json
from uuid import uuid4
from fastapi import FastAPI
import aio_pika
from contextlib import asynccontextmanager

app = FastAPI()

# store futures for responses
futures = {}


# ----------------------------
# Planner Agent
# ----------------------------
class PlannerAgent:

    async def process_request(self, session_id: str, user_request: dict):
        print("Planner received:", user_request)

        correlation_id = str(uuid4())

        # send task to worker
        await publish_task("worker_queue", {
            "session_id": session_id,
            "request": user_request
        }, correlation_id)

        # wait for result
        result = await wait_for_result(correlation_id)

        print("Final result:", result)
        return result


# ----------------------------
# RabbitMQ helpers
# ----------------------------
async def publish_task(queue_name, data, correlation_id):
    await app.state.channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(data).encode(),
            correlation_id=correlation_id,
            reply_to="response_queue"
        ),
        routing_key=queue_name
    )


async def wait_for_result(correlation_id):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    futures[correlation_id] = future
    return await future


# ----------------------------
# Lifespan
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    connection = await aio_pika.connect_robust("amqp://guest:guest@127.0.0.1:5672/")

    channel = await connection.channel()

    # queues
    worker_queue = await channel.declare_queue("planner_queue", durable=True)
    response_queue = await channel.declare_queue("response_queue", durable=True)

    planner = PlannerAgent()

    # ----------------------------
    # Worker (simulated agent)
    # ----------------------------
    async def worker_handler(message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())

            print("Worker got:", data)

            result = {
                "answer": f"Processed {data['request']}"
            }

            # 🔥 SINGLE LINE RESPONSE (your requirement)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(result).encode(),
                    correlation_id=message.correlation_id
                ),
                routing_key=message.reply_to
            )

    await worker_queue.consume(worker_handler)

    # ----------------------------
    # Response listener
    # ----------------------------
    async def on_response(message: aio_pika.IncomingMessage):
        async with message.process():
            corr_id = message.correlation_id
            if corr_id in futures:
                futures[corr_id].set_result(
                    json.loads(message.body.decode())
                )

    # await response_queue.consume(on_response)

    # store
    app.state.connection = connection
    app.state.channel = channel
    app.state.planner = planner

    yield

    await connection.close()


app = FastAPI(lifespan=lifespan)


# ----------------------------
# API
# ----------------------------
@app.get("/call")
async def call():
    session_id = str(uuid4())

    result = await app.state.planner.process_request(
        session_id,
        {"task": "meal plan"}
    )

    return result



from .agent.planner_crewai import call_agents

@app.get("/call-agent")
async def call():
    result = await call_agents()   # <-- FIX HERE
    return result
