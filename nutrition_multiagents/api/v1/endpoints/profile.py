from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import APIRouter
import aio_pika
import json
from uuid import uuid4
import asyncio

SECRET_KEY = "your-very-secret-key"  # Store in environment variables!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()

class UserLogin(BaseModel):
    email: str
    password: str

# Simulate user lookup (replace with your DB)
def authenticate_user(email: str, password: str):
    # This is just an example – check against your DB
    if email == "alice@example.com" and password == "secret":
        return {"user_id": 123, "name": "Alice", "tier": "pro"}
    return None

@router.post("/login")
async def login(login_data: UserLogin):
    user = authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT payload
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user["user_id"]),
        "name": user["name"],
        "tier": user["tier"],          # ← tier claim
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/call-agent")
async def send_request():
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@127.0.0.1:5672/"
    )

    channel = await connection.channel()

    callback_queue = await channel.declare_queue(exclusive=True)

    future = asyncio.get_event_loop().create_future()

    corr_id = str(uuid4())

    async def on_response(message: aio_pika.IncomingMessage):
        async with message.process():
            if message.correlation_id == corr_id:
                future.set_result(
                    json.loads(message.body.decode())
                )

    await callback_queue.consume(on_response)

    request = {
        "user_id": 1,
        "request": "Make meal plan"
    }

    message = aio_pika.Message(
        body=json.dumps(request).encode(),
        reply_to=callback_queue.name,
        correlation_id=corr_id
    )

    await channel.default_exchange.publish(
        message,
        routing_key="planner_queue"
    )

    result = await future

    await connection.close()

    return result

