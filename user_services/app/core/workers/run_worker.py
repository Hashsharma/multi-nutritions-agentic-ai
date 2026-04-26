#!/usr/bin/env python3
"""
Standalone RabbitMQ Worker Process
Run this separately: python run_worker.py
"""

import asyncio
import signal
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from user_services.app.core.rabbitmq.worker import RabbitMQWorker
from user_services.app.core.rabbitmq.config import RabbitMQConfig

# Import your existing PlannerAgent or create a simple handler
# If you don't have PlannerAgent, we'll create an inline handler

async def main():
    # Create worker
    worker = RabbitMQWorker(RabbitMQConfig())
    
    # Register handler for planner_queue
    @worker.handlers.register("planner_queue")
    async def planner_handler(data: dict, correlation_id: str = None, reply_to: str = None):
        """Handle planner queue messages"""
        print(f"🤖 Processing planner request: {data}")
        
        # Your business logic here - modify according to your needs
        try:
            # If you have a PlannerAgent class
            # from user_services.app.agents.planner_agent import PlannerAgent
            # result = await PlannerAgent.process_request(data, correlation_id, reply_to)
            
            # Simple processing (temporary solution)
            task = data.get('task', data.get('request', 'unknown'))
            result = {
                "answer": f"Processed '{task}' successfully",
                "session_id": data.get('session_id'),
                "status": "completed",
                "data_received": data
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error in planner_handler: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    # You can register more queues here
    # @worker.handlers.register("email_queue")
    # async def email_handler(data: dict, **kwargs):
    #     # Your email processing logic
    #     return {"status": "email_sent"}
    
    # Start consuming
    await worker.start_consumer()
    
    print("""
    ╔══════════════════════════════════════╗
    ║   RabbitMQ Worker Started            ║
    ║   Listening on: planner_queue        ║
    ║   Press Ctrl+C to stop               ║
    ╚══════════════════════════════════════╝
    """)
    
    # Graceful shutdown
    stop_event = asyncio.Event()
    
    def signal_handler():
        print("\n🛑 Shutting down worker...")
        stop_event.set()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: signal_handler())
    
    await stop_event.wait()
    await worker.close()
    print("✅ Worker stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Worker terminated")
        sys.exit(0)