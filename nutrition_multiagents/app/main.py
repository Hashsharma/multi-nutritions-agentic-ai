from fastapi import FastAPI, HTTPException
# from fastapi_advanced_rate_limiter import SlidingWindowLogRateLimiter
import redis
# from nutrition_multiagents.middleware.rate_limit_service import RateLimitMiddleware
from nutrition_multiagents.middleware.rate_limit import RedisRateLimitMiddleware
from nutrition_multiagents.middleware.authentication_middleware import JWTAuthMiddleware
from fastapi import FastAPI
import redis.asyncio as redis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Import routers
from nutrition_multiagents.api.v1.router import api_router

app.include_router(api_router, prefix="/api/v1")


# Create Redis client
redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)

# Add middlewares – order matters!

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RedisRateLimitMiddleware,
    redis_client=redis_client,
    default_tier="free",
)
app.add_middleware(JWTAuthMiddleware)   # This will run first


@app.get("/")
async def root():
    return {"message": "Hello, world!"}