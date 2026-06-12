from celery import Celery
import time
import redis.asyncio as redis
import json
import asyncio
from nutrition_multiagents.workers.extraction_jobs import extract_pdf_text, simple_chunk_by_heading, LegalTextParser
import os

# Initialize Celery
celery_app = Celery(
    'document_jobs',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Synchronous Redis client for Celery task (since Celery can't use async)
import redis as sync_redis
redis_client = sync_redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

def update_status(task_id: str, status: str, progress: int, result=None):
    """Update job status in Redis (synchronous for Celery)"""
    job_data = {
        "task_id": task_id,
        "status": status,
        "progress": progress
    }
    
    if result:
        job_data["result"] = result
    
    # Store in Redis
    redis_client.setex(
        f"job:{task_id}",
        3600,  # Expire after 1 hour
        json.dumps(job_data)
    )
    
    # Publish for SSE
    redis_client.publish(
        f"job_updates:{task_id}",
        json.dumps(job_data)
    )


@celery_app.task(bind=True, max_retries=3)
def process_document(self, file_path: str, filename: str, doc_id: str):
    task_id = self.request.id

    try:
        # -----------------------------
        # STEP 0: INIT
        # -----------------------------
        update_status(task_id, "started", 0)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # -----------------------------
        # STEP 1: EXTRACT TEXT
        # -----------------------------
        update_status(task_id, "extracting_text", 10)

        raw_text = extract_pdf_text(file_path)

        # -----------------------------
        # STEP 2: CHUNKING
        # -----------------------------
        update_status(task_id, "chunking", 25)

        heading_chunks = simple_chunk_by_heading(raw_text)

        # -----------------------------
        # STEP 3: PARSING
        # -----------------------------
        update_status(task_id, "parsing", 40)

        parser = LegalTextParser()
        all_parsed_chunks = []

        total = len(heading_chunks)

        for i, chunk in enumerate(heading_chunks):
            parsed = parser.parse(chunk["text"])

            for item in parsed:
                item["metadata"]["doc_id"] = doc_id
                item["metadata"]["chunk_index"] = i
                all_parsed_chunks.append(item)

            # progress update per chunk
            progress = 40 + int((i + 1) / total * 50)
            update_status(task_id, f"processing_chunk_{i+1}", progress)

        # -----------------------------
        # STEP 4: FINAL RESULT
        # -----------------------------
        result = {
            "status": "completed",
            "filename": filename,
            "doc_id": doc_id,
            "parsed_chunks": all_parsed_chunks,
            "metadata": {
                "file_size": os.path.getsize(file_path),
                "file_type": filename.split('.')[-1] if '.' in filename else "unknown",
                "total_chunks": len(heading_chunks),
            }
        }

        update_status(task_id, "completed", 100, result)

        return result

    except Exception as e:
        update_status(task_id, "failed", 0, {"error": str(e)})
        raise self.retry(exc=e, countdown=5)