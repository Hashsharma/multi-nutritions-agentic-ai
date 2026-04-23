from fastapi import FastAPI, APIRouter
import sys
import os

# Get the parent directory (project root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')) # This goes up three levels
sys.path.insert(0, project_root) # Adds to the beginning of the search path

from user_services.app.api.v1.endpoints.user_routes import router as user_router
# from user_services.app.api.v1.endpoints.address_routes import router as address_router

router = APIRouter()
from user_services.app.utils.config import settings
# Include each sub-router
router.include_router(user_router, prefix="/api/v1", tags=["Auth"])
# router.include_router(address_router, prefix="/api/v1/address", tags=["Address"])

app = FastAPI(title="Auth Service")

# app.include_router(auth_router, prefix="/api/v1")
app.include_router(router)




@app.on_event("startup")
async def startup_event():
    if settings.DEBUG:
        print("Starting Auth Service in DEBUG mode")

@app.get("/")
async def greetings():
    return {"Greetings"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
