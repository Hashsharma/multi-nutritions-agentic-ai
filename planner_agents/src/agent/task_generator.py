# agent/task_generator.py
import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from .prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

class TaskGenerator:
    """Generates task sequences using LLM API"""
    
    def __init__(self):
        # Initialize your LLM client (OpenAI, Anthropic, or local)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        
    async def generate_tasks(self, user_request: str, context: Dict = None) -> List[Dict]:
        """
        Generate task sequence from user request
        Returns list of tasks like:
        [
            {"agent": "clinical", "action": "assess_patient", "input_data": {...}},
            {"agent": "meal_planner", "action": "generate_plan", "input_data": {...}}
        ]
        """
        context_str = json.dumps(context) if context else "{}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    user_request=user_request,
                    context=context_str
                )}
            ],
            temperature=0.3,  # Lower temperature for consistent JSON output
            response_format={"type": "json_object"}  # If using OpenAI
        )
        
        tasks_json = response.choices[0].message.content
        tasks_data = json.loads(tasks_json)
        
        # Handle both {"tasks": [...]} and direct array formats
        if isinstance(tasks_data, dict) and "tasks" in tasks_data:
            return tasks_data["tasks"]
        elif isinstance(tasks_data, list):
            return tasks_data
        else:
            return [tasks_data]