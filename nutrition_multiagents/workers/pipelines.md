Frontend
   ↓
Upload API
   ↓
Store file (S3/local)
   ↓
DB record created (status=uploaded)
   ↓
Celery task queued (doc_id)
   ↓
Worker fetches file
   ↓
Extraction pipeline runs
   ↓
DB status updates
   ↓
Redis Pub/Sub (optional)
   ↓
SSE pushes updates to UI


===============

Client
  ↓
API (FastAPI)
  ↓
S3 Upload (or local in dev)
  ↓
PostgreSQL (document metadata)
  ↓
Celery Queue (Redis broker)
  ↓
Worker Pool (OCR / extraction pipeline)
  ↓
Redis Pub/Sub (real-time updates)
  ↓
SSE endpoint (frontend listens)