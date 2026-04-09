from fastapi import FastAPI, HTTPException
from fastapi_advanced_rate_limiter import SlidingWindowLogRateLimiter
import redis
from nutrition_multiagents.middleware.rate_limit_service import RateLimitMiddleware

app = FastAPI(title="Multi Nutrition Sync")

app.add_middleware(RateLimitMiddleware)

@app.get("/")
async def greetings():
    print("Logs")
    return {"result": "Greetings"}