# worker/router.py

from worker.handlers import user, email, task
from worker.core.logger import logger

ROUTES = {
    "user.create": user.create_user,
    "email.send": email.send_email,
    "task.process": task.process_task,
}


async def route_message(queue_name: str, payload: dict):
    handler = ROUTES.get(queue_name)

    if not handler:
        logger.error(f"No handler for queue: {queue_name}")
        return

    try:
        await handler(payload)

    except Exception as e:
        logger.exception(
            f"Error in handler for {queue_name}"
        )
        raise  # propagate to consumer for DLQ