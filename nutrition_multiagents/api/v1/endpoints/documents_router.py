from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from celery.result import AsyncResult
import redis.asyncio as redis
import json
import asyncio
from nutrition_multiagents.services.file_storage_services import AsyncStorageClient
from pathlib import Path
import os
from nutrition_multiagents.core.config import LOCAL_STORAGE_PATH

from nutrition_multiagents.workers.document_jobs import (
    celery_app,
    process_document,
)

router = APIRouter()

# Async Redis clients
redis_status = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
redis_pubsub = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)

# ---------------------------
# Health check
# ---------------------------
@router.get("/greet")
async def greet():
    return {"Working": "well"}


# ---------------------------
# Upload endpoint
# ---------------------------

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # ---------------------------
        # 1. FILE SIZE CHECK FIRST
        # ---------------------------
        content = await file.read()

        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

        # reset stream (important if reused)
        file.file.seek(0)

        # ---------------------------
        # 2. STORAGE INIT
        # ---------------------------
        base_dir = Path(LOCAL_STORAGE_PATH) / "documents"

        storage = AsyncStorageClient(base_dir=str(base_dir))

        # ---------------------------
        # 3. STORE FILE
        # ---------------------------
        file_key, url, document_id = await storage.upload_file(
            file_obj=file.file,
            filename=file.filename,
            user_id="user_123",
            content_type=file.content_type
        )

        file_path = str(base_dir / file_key)

        # ---------------------------
        # 4. TRIGGER CELERY (PASS PATH)
        # ---------------------------
        task = process_document.delay(
            doc_id=document_id,
            file_path=file_path,
            filename=file.filename
        )

        # ---------------------------
        # 5. RESPONSE
        # ---------------------------
        return {
            "task_id": task.id,
            "document_id": document_id,
            "status": "queued",
            "file_key": file_key,
            "file_path": file_path,
            "message": f"{file.filename} queued",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# Polling fallback endpoint
# ---------------------------
@router.get("/status/{task_id}")
async def get_status(task_id: str):
    job_data = await redis_status.get(f"job:{task_id}")

    if job_data:
        return json.loads(job_data)

    # fallback to Celery
    task = AsyncResult(task_id, app=celery_app)

    if task.state == "PENDING":
        return {"task_id": task_id, "status": "queued", "progress": 0}

    elif task.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(task.info),
        }

    elif task.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "result": task.result,
        }

    return {"task_id": task_id, "status": task.state, "progress": 50}


# ---------------------------
# SSE stream endpoint
# ---------------------------
@router.get("/stream/{task_id}")
async def stream_status(task_id: str):
    async def event_stream():
        pubsub = redis_pubsub.pubsub()
        await pubsub.subscribe(f"job_updates:{task_id}")

        try:
            # Send initial state
            initial_status = await redis_status.get(f"job:{task_id}")
            if initial_status:
                yield f"event: update\ndata: {initial_status}\n\n"

            # Listen for updates
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                data = message["data"]
                yield f"event: update\ndata: {data}\n\n"

                parsed = json.loads(data)

                # Stop when finished
                if parsed.get("status") in ["completed", "failed"]:
                    break

                # small delay to prevent tight loop
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            print(f"Client disconnected: {task_id}")

        finally:
            await pubsub.unsubscribe(f"job_updates:{task_id}")
            await pubsub.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ---------------------------
# Final results endpoint
# ---------------------------
@router.get("/results/{task_id}")
async def get_results(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    if task.state == "SUCCESS":
        return task.result

    elif task.state == "FAILURE":
        raise HTTPException(status_code=400, detail=str(task.info))

    raise HTTPException(
        status_code=404,
        detail=f"Not completed. Current status: {task.state}",
    )