# agent/decision_maker.py
from typing import Dict, Any, List
import json

class DecisionMaker:
    """Makes decisions based on agent results to determine next steps"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
    async def should_continue(self, task_result: Dict, current_plan: List[Dict]) -> bool:
        """
        Decide if we should continue with remaining tasks
        Returns True if we should proceed, False to stop
        """
        # Simple rule-based decision first
        if task_result.get("status") == "error":
            # Don't continue if critical agent failed
            critical_agents = ["clinical", "meal_planner"]
            if task_result.get("agent") in critical_agents:
                return False
        
        # Always continue unless we have a critical failure
        return True
    
    async def adapt_plan(self, original_plan: List[Dict], 
                        completed_results: List[Dict]) -> List[Dict]:
        """
        Adapt remaining tasks based on intermediate results
        Example: If clinical returns "no restrictions", skip certain steps
        """
        # Start with original plan
        adapted_plan = original_plan.copy()
        
        # Check if clinical assessment found restrictions
        clinical_result = next(
            (r for r in completed_results if r.get("agent") == "clinical"), 
            None
        )
        
        if clinical_result:
            restrictions = clinical_result.get("data", {}).get("restrictions", [])
            
            # If no restrictions, we might simplify the plan
            if not restrictions:
                # Remove any extra validation tasks if they exist
                adapted_plan = [t for t in adapted_plan 
                              if t.get("action") != "validate_restrictions"]
        
        return adapted_plan
    
    async def compose_response(self, user_request: str, 
                               all_results: List[Dict]) -> Dict:
        """
        Compose final response from all agent results
        """
        # Simple composition first (can be enhanced with LLM later)
        response = {
            "status": "success",
            "user_request": user_request,
            "agents_called": [r.get("agent") for r in all_results],
            "data": {}
        }
        
        # Organize data by agent type
        for result in all_results:
            agent = result.get("agent")
            data = result.get("data", {})
            
            if agent == "clinical":
                response["data"]["clinical_assessment"] = data
            elif agent == "meal_planner":
                response["data"]["meal_plan"] = data
            elif agent == "recipe":
                response["data"]["recipes"] = data
            elif agent == "grocery":
                response["data"]["shopping_list"] = data
        
        # Add summary
        response["summary"] = self._generate_summary(all_results)
        
        return response
    
    def _generate_summary(self, results: List[Dict]) -> str:
        """Generate a human-readable summary"""
        agents_used = [r.get("agent") for r in results if r.get("status") == "success"]
        
        if not agents_used:
            return "Unable to process request."
        
        summaries = []
        for result in results:
            if result.get("agent") == "meal_planner" and result.get("status") == "success":
                plan_data = result.get("data", {})
                summaries.append(f"Created meal plan with {plan_data.get('total_calories', 0)} calories")
            elif result.get("agent") == "recipe" and result.get("status") == "success":
                recipe_data = result.get("data", {})
                summaries.append(f"Provided {len(recipe_data.get('recipes', []))} recipes")
        
        return ". ".join(summaries) if summaries else "Request processed successfully."