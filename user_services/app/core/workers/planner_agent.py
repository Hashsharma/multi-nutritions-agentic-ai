from app.core.rabbitmq.worker import RabbitMQWorker
import json

class PlannerAgent:
    def __init__(self, worker: RabbitMQWorker):
        self.worker = worker
        self._register_handlers()
    
    def _register_handlers(self):
        """Register handlers for different queues"""
        
        @self.worker.handlers.register("planner_queue")
        async def handle_planner_request(data: dict, correlation_id: str = None, reply_to: str = None):
            """Handle planner queue messages"""
            print(f"Worker got: {data}")
            
            # Your business logic here
            result = {
                "answer": f"Processed {data.get('request', data.get('task', 'unknown'))}"
            }
            
            return result  # Will be automatically sent back via send_response
        
        # You can register more handlers for different queues
        @self.worker.handlers.register("another_queue")
        async def handle_another_request(data: dict, correlation_id: str = None, reply_to: str = None):
            # Different handler logic
            return {"status": "processed"}