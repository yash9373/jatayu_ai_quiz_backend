"""
This graph is used to extend skill graphs with specific skills
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
import json

# Import SkillNode and SkillGraph from skill_graph_generation
# We'll redefine them here to avoid import issues
from typing import Literal


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
    )


# Define priority type
Priority = Literal["H", "M", "L"]


class SkillNode(BaseModel):
    """Represents a skill node in the DAG with subskills and priority."""
    skill: str = Field(description="The name of the skill")
    priority: Priority = Field(
        description="Priority level: H (High), M (Medium), L (Low)")
    subskills: List["SkillNode"] = Field(
        default_factory=list, description="List of subskills")
    score: int = Field(default=0, description="Current score for this skill")
    total: int = Field(
        default=0, description="Total possible points for this skill")
    passed: bool = Field(
        default=False, description="Whether this skill assessment is passed")

    class Config:
        arbitrary_types_allowed = True


# Update forward references for recursive model
SkillNode.model_rebuild()


class SkillGraph(BaseModel):
    """Represents the complete skill graph with root nodes."""
    root_nodes: List[SkillNode] = Field(description="List of root skill nodes")


class ExtensionNode(BaseModel):
    """Represents a new L-priority node to be added to the skill graph."""
    skill: str = Field(description="The name of the new skill")
    priority: Literal["L"] = Field(
        description="Priority level (always L for extensions)")
    parent_skill: str = Field(
        description="The parent skill to attach this node to")
    subskills: List[str] = Field(default_factory=list,
                                 description="Always empty for new L-nodes")


class ExtensionResult(BaseModel):
    """Result containing new L-priority nodes to be added."""
    new_nodes: List[ExtensionNode] = Field(
        default_factory=list,
        description="List of new L-priority nodes to be added to the skill graph"
    )


# Skill graph extension prompt
SKILL_GRAPH_EXTENSION_SYSTEM_PROMPT = """
You are an AI assistant extending a skill graph based on a candidate's resume.

Your task is to:
1. Analyze the candidate's resume for HIGH-LEVEL TECHNICAL SKILLS that are NOT already present in the existing skill graph
2. Identify which new skills would be valuable additions based on the job description context
3. Map each new skill to the most appropriate parent skill from the existing graph
4. Return only new L-priority nodes that should be added

FOCUS ONLY ON:
- Programming languages (Python, JavaScript, Java, C++, etc.)
- Frameworks (React, Django, FastAPI, Angular, etc.)
- Libraries (NumPy, Pandas, TensorFlow, etc.)
- Tools and platforms (Docker, Kubernetes, AWS, Git, etc.)
- Databases (PostgreSQL, MongoDB, Redis, etc.)
- Technologies (REST APIs, GraphQL, microservices, etc.)

EXCLUDE:
- Soft skills (communication, leadership, etc.)
- General concepts (problem-solving, analytical thinking, etc.)
- Domain knowledge without specific technical implementation
- Certifications or methodologies unless they're specific technical tools

Guidelines:
- Only identify technical skills that are completely missing from the current graph
- Do not duplicate any skills already present at any level
- Be highly selective - only include concrete technical skills with clear implementation value
- Attach new skills to the most logical parent in the existing hierarchy
- All new nodes should have priority "L" (Low) since they're resume-specific additions
- Maximum 5-8 technical skills to avoid clutter

Return format: List of extension nodes with skill name, priority "L", and parent skill name.
"""


@dataclass
class Configuration:
    """Configuration for the skill graph extension."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1


@dataclass
class State:
    """State for the skill graph extension."""
    jd_text: str = ""
    resume_text: str = ""
    original_skill_graph: Optional[SkillGraph] = None
    extended_skill_graph: Optional[SkillGraph] = None
    extension_nodes: Optional[ExtensionResult] = None
    error: Optional[str] = None


def identify_extension_nodes(state: State) -> State:
    """Identify new L-priority nodes to add to the skill graph."""
    try:
        jd_text = state.jd_text
        resume_text = state.resume_text
        skill_graph = state.original_skill_graph

        if not jd_text or not resume_text or not skill_graph:
            return State(
                jd_text=state.jd_text,
                resume_text=state.resume_text,
                original_skill_graph=state.original_skill_graph,
                extended_skill_graph=None,
                extension_nodes=None,
                error="Missing required input data (JD, resume, or skill graph)"
            )

        # Create the extension prompt
        extension_prompt = f"""
You are an AI assistant extending a skill graph based on the candidate's resume.

You are given:
1. A job description (JD)
2. A parsed resume
3. The original skill graph that includes only High (H) and Moderate (M) priority nodes.

Your task is to:
- Identify HIGH-LEVEL TECHNICAL SKILLS in the resume that are NOT already in the skill graph.
- Focus ONLY on: programming languages, frameworks, libraries, tools, databases, and specific technologies
- Map them to appropriate parent skills from the existing graph.
- Attach them as L-priority nodes under the most relevant parent.
- Do not duplicate skills already present.
- Do not return any H or M nodes — only new L-nodes.
- Be highly selective and only include concrete technical skills.
- Maximum 5-8 skills to avoid clutter.

JD:
\"\"\"
{jd_text}
\"\"\"

Resume:
\"\"\"
{resume_text}
\"\"\"

Existing Skill Graph (H and M only):
\"\"\"
{json.dumps(skill_graph.model_dump() if hasattr(skill_graph, 'model_dump') else skill_graph, indent=2)}
\"\"\"

Identify new HIGH-LEVEL TECHNICAL SKILLS from the resume that would be valuable additions to this skill graph.
"""

        llm = get_llm()
        extractor_llm = llm.with_structured_output(ExtensionResult)

        messages = [
            {"role": "system", "content": SKILL_GRAPH_EXTENSION_SYSTEM_PROMPT},
            {"role": "user", "content": extension_prompt}
        ]

        result = extractor_llm.invoke(messages)

        # Ensure we get an ExtensionResult instance
        if isinstance(result, dict):
            result = ExtensionResult(**result)

        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=None,
            extension_nodes=result,
            error=None
        )

    except Exception as e:
        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=None,
            extension_nodes=None,
            error=str(e)
        )


def extend_skill_graph(state: State) -> State:
    """Extend the skill graph with the identified L-priority nodes."""
    try:
        if state.error or not state.extension_nodes or not state.original_skill_graph:
            return State(
                jd_text=state.jd_text,
                resume_text=state.resume_text,
                original_skill_graph=state.original_skill_graph,
                # Return original if no extensions
                extended_skill_graph=state.original_skill_graph,
                extension_nodes=state.extension_nodes,
                error=state.error or "No extension nodes to process"
            )

        # Create a deep copy of the original skill graph
        extended_graph = SkillGraph.model_validate(
            state.original_skill_graph.model_dump() if hasattr(state.original_skill_graph, 'model_dump') else state.original_skill_graph)

        def attach_to_parent(graph_nodes: List[SkillNode], parent_name: str, new_node: SkillNode) -> bool:
            """Recursively find and attach new node to parent."""
            for node in graph_nodes:
                if node.skill.lower() == parent_name.lower():
                    node.subskills.append(new_node)
                    return True
                if attach_to_parent(node.subskills, parent_name, new_node):
                    return True
            return False

        def ensure_other_category(graph_nodes: List[SkillNode]) -> SkillNode:
            """Ensure there's an 'Other' category at the root level."""
            for node in graph_nodes:
                if node.skill.lower() == "other":
                    return node

            # Create new "Other" category
            other_node = SkillNode(
                skill="Other",
                priority="M",
                subskills=[],
                score=0,
                total=0,
                passed=False
            )
            graph_nodes.append(other_node)
            return other_node

        # Process each extension node
        attachment_failures = []
        for ext_node in state.extension_nodes.new_nodes:
            new_skill_node = SkillNode(
                skill=ext_node.skill,
                priority="L",
                subskills=[],
                score=0,
                total=0,
                passed=False
            )

            attached = attach_to_parent(
                extended_graph.root_nodes, ext_node.parent_skill, new_skill_node)

            if not attached:
                # If parent not found, attach to "Other" category
                other_node = ensure_other_category(extended_graph.root_nodes)
                other_node.subskills.append(new_skill_node)
                attachment_failures.append(
                    f"Parent '{ext_node.parent_skill}' not found for skill '{ext_node.skill}', attached to 'Other'")

        # Note any attachment failures but don't treat as complete error
        error_msg = None
        if attachment_failures:
            error_msg = f"Some attachments failed: {'; '.join(attachment_failures)}"

        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=extended_graph,
            extension_nodes=state.extension_nodes,
            error=error_msg
        )

    except Exception as e:
        return State(
            jd_text=state.jd_text,
            resume_text=state.resume_text,
            original_skill_graph=state.original_skill_graph,
            extended_skill_graph=None,
            extension_nodes=state.extension_nodes,
            error=str(e)
        )


def create_skill_graph_extension_graph():
    """Create the skill graph extension graph."""
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("identify_extension_nodes", identify_extension_nodes)
    workflow.add_node("extend_skill_graph", extend_skill_graph)

    # Add edges
    workflow.add_edge(START, "identify_extension_nodes")
    workflow.add_edge("identify_extension_nodes", "extend_skill_graph")
    workflow.add_edge("extend_skill_graph", END)

    return workflow.compile()


# Export the graph
graph = create_skill_graph_extension_graph()
