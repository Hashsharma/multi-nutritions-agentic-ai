# agent/planner_crewai.py
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
import json

class RabbitMQTool(BaseTool):
    """Tool for agents to communicate via RabbitMQ"""
    name: str = "RabbitMQ Messenger"
    description: str = "Send messages to other agents"
    
    def _run(self, agent_type: str, message: str) -> str:
        # Your RabbitMQ logic here
        return f"Sent to {agent_type}"


async def call_agents():

    llm = LLM(model="custom_model",
            base_url="http://localhost:1234/v1",
            api_key="abcd")



    # Define autonomous agents
    classifier_agent = Agent(
        role="Request Classifier",
        goal="Understand user requests and decide which agents to activate",
        backstory="Expert at breaking down meal planning requests",
        tools=[RabbitMQTool()],
        llm=llm,
        verbose=True
    )

    clinical_agent = Agent(
        role="Clinical Nutritionist",
        goal="Analyze patient health data and provide dietary restrictions",
        backstory="Registered dietitian with 10 years of clinical experience",
        tools=[RabbitMQTool()],
        llm=llm,
        verbose=True
    )

    meal_agent = Agent(
        role="Meal Planner",
        goal="Create delicious, nutritionally-balanced meal plans",
        backstory="Chef and nutritionist who creates practical meal plans",
        tools=[RabbitMQTool()],
        llm=llm,
        verbose=True
    )

    # Define tasks (agents can choose to do these or not)
    classify_task = Task(
        description="Analyze user request and determine what's needed",
        expected_output="JSON with required agents and order",
        agent=classifier_agent
    )

    clinical_task = Task(
        description="If clinical analysis needed, assess patient and return restrictions",
        expected_output="Clinical assessment with dietary restrictions",
        agent=clinical_agent,
        async_execution=True  # Can run in parallel!
    )

    meal_task = Task(
        description="Create meal plan based on clinical assessment if available",
        expected_output="Complete meal plan with breakfast, lunch, dinner, snacks",
        agent=meal_agent,
        dependencies=[clinical_task]  # Only runs after clinical if needed
    )

    # Create crew with hierarchical process (like your orchestrator)
    meal_crew = Crew(
        agents=[],
        tasks=[classify_task, clinical_task, meal_task],
        process=Process.sequential,  # Manager agent coordinates
        manager_llm=llm,
        verbose=True
    )

    # Run
    result = meal_crew.kickoff(inputs={"user_request": "Create diabetic meal plan"})

    return result