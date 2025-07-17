"""
This graph is used to generate skill DAG (Directed Acyclic Graph) from job description
"""
from app.services.skill_graph_generation.state import State, SkillGraph, SkillNode, Configuration
from langgraph.graph import StateGraph, END, START
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

# Use string annotations for forward references
# JobDescriptionFields will be passed as a dictionary to avoid import issues

load_dotenv()

# Define prompts directly to avoid import issues
DAG_SYSTEM_PROMPT = """
You are a skill graph architect. Your job is to create a directed acyclic graph (DAG) representing the conceptual breakdown of a technical skill.

Given a target root skill (e.g., "React"), generate a structured DAG where:
- The root node is the skill itself.
- Each subskill represents a prerequisite concept or component needed to understand or use the parent skill.
- Subskills may have their own subskills, creating a recursive structure.
- Avoid unnecessary depth unless required by the skill's complexity.

Structure:
Each node contains:
- skill: The name of the skill or subskill.
- priority: H (High), M (Medium), L (Low) based on importance to the job
- subskills: A list of nested nodes for concepts that must be understood before or to master this skill.

Be as concise and accurate as possible. Do not invent unrelated skills. Focus on fundamentals and dependencies.

Only return a valid JSON object matching the schema. Do not include explanations or Markdown.
"""

SKILL_GRAPH_GENERATION_PROMPT = """
You are an AI assistant helping build a skill graph from a job description.

Given the following JD, extract skills and subskills and assign each a priority:
- "H" for High (core to the job)
- "M" for Medium (important but secondary)
- "L" for Low (nice to have)

Return the graph in recursive JSON format like this:

{{
  "root_nodes": [
    {{
      "skill": "CI/CD",
      "priority": "H",
      "subskills": [
        {{
          "skill": "Jenkins",
          "priority": "H",
          "subskills": []
        }}
      ]
    }}
  ]
}}

JD:
\"\"\"
{jd_text}
\"\"\"

Return only valid JSON matching the SkillGraph schema.
"""


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
    )


def generate_skill_graph_from_raw_jd(state: State) -> State:
    """Generate skill graph from raw job description text."""
    try:
        llm = get_llm()
        if not state.raw_job_description:
            raise ValueError("No raw job description provided")

        # Use structured output with the SkillGraph model
        # structured_llm = llm.with_structured_output(SkillGraph)

        # Format the prompt with job description text
        formatted_prompt = SKILL_GRAPH_GENERATION_PROMPT.format(
            jd_text=state.raw_job_description
        )

        messages = [
            SystemMessage(content=DAG_SYSTEM_PROMPT),
            HumanMessage(content=formatted_prompt)
        ]

        # Get structured output
        result = llm.invoke(messages)
        raw_json = result.content[0] if isinstance(
            result.content, list) else result.content
        if isinstance(raw_json, dict):
            raw_json = str(raw_json)

        if raw_json.startswith("```json"):
            raw_json = raw_json.removeprefix(
                "```json").removesuffix("```").strip()
        elif raw_json.startswith("```"):
            raw_json = raw_json.removeprefix("```").removesuffix("```").strip()

        parsed_json = json.loads(raw_json)
        print("[DEBUG] Parsed JSON from LLM:", json.dumps(parsed_json, indent=2))  # Debug print
        # Ensure we get a SkillGraph instance

        result = SkillGraph(**parsed_json)
        return State(
            raw_job_description=state.raw_job_description,
            skill_graph=result,
            error=None
        )

    except Exception as e:
        return State(
            raw_job_description=state.raw_job_description,
            skill_graph=None,
            error=str(e)
        )


def handle_error(state: State) -> State:
    """Handle cases where no valid input is provided."""
    return State(
        raw_job_description=state.raw_job_description,
        skill_graph=None,
        error="No valid job description input provided (neither raw nor parsed)"
    )


def create_skill_graph_generation_graph():
    """Create and return the skill graph generation graph."""
    workflow = StateGraph(State, config_schema=Configuration)

    workflow.add_node("generate_from_raw", generate_skill_graph_from_raw_jd)

    workflow.add_edge(START, "generate_from_raw")
    workflow.add_edge("generate_from_raw", END)

    return workflow.compile()


# Create the graph instance
# skill_graph_generation_graph = create_skill_graph_generation_graph()
graph = create_skill_graph_generation_graph()

# Helper function to print skill graph in a readable format


def print_skill_graph(skill_graph: SkillGraph, indent: int = 0) -> None:
    """Print the skill graph in a readable tree format."""
    for node in skill_graph.root_nodes:
        print_skill_node(node, indent)


def print_skill_node(node: SkillNode, indent: int = 0) -> None:
    """Print a skill node and its subskills recursively."""
    prefix = "  " * indent
    priority_emoji = {"H": "🔴", "M": "🟡", "L": "🟢"}
    emoji = priority_emoji.get(node.priority, "⚪")

    print(f"{prefix}{emoji} {node.skill} (Priority: {node.priority})")

    for subskill in node.subskills:
        print_skill_node(subskill, indent + 1)
