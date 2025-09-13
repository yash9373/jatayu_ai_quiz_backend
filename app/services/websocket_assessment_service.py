"""
WebSocket Assessment Service - Updated for proper graph state management
Integrates MCQ generation graph with WebSocket communication for real-time assessments
"""

import asyncio
import json
import logging
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.jd_parsing.state import JobDescriptionFields
from app.services.resume_parsing.state import ResumeFields
from app.services.mcq_generation.state import AgentState, Question, Response
from app.services.skill_graph_generation.state import SkillGraph
from app.models.test import Test
from app.models.assessment import AssessmentStatus, Assessment
from app.repositories.test_repo import TestRepository
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from app.repositories.assessment_repo import AssessmentRepository
from app.services.mcq_generation.graph import get_question_generation_graph

logger = logging.getLogger(__name__)


class StateEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'model_dump'):
            return o.model_dump()
        elif hasattr(o, 'dict'):
            return o.dict()
        elif isinstance(o, datetime):
            return o.isoformat()
        return str(o)


class AssessmentGraphService:
    """
    Service for managing MCQ generation graph in WebSocket assessments
    Handles graph state, question generation, and answer processing with proper thread ID management

    Key Principles:
    - Each assessment gets a unique thread_id (same as assessment_id)
    - Graph state is persistent and recoverable using thread_id
    - Never reinitialize graph with existing thread_id to preserve state
    - Use Command(resume=...) for all graph interactions after initialization
    """

    def __init__(self):
        self.graph = None
        self.initialized_threads: Dict[str, bool] = {}
        # New: per-thread async locks to prevent concurrent graph operations
        self._thread_locks: Dict[str, asyncio.Lock] = {}
        # New: finalize guard to avoid duplicate finalize notifications (races with scheduler / timers)
        self._finalized_threads: Dict[str, bool] = {}

    def _get_thread_lock(self, thread_id: str) -> asyncio.Lock:
        lock = self._thread_locks.get(thread_id)
        if lock is None:
            lock = asyncio.Lock()
            self._thread_locks[thread_id] = lock
        return lock

    async def _get_graph(self):
        """Get or create the MCQ generation graph"""
        if not self.graph:
            # get_question_generation_graph is async, so we must await to obtain compiled graph
            self.graph = await get_question_generation_graph()
        return self.graph

    async def initialize_assessment_graph(
        self,
        connection_id: str,
        test: Test,
        assessment_id: int,
        user_id: int,
        db: AsyncSession
    ):
        """
        Initialize MCQ generation graph for an assessment session

        CRITICAL: This method should only be called once per assessment_id (thread_id).
        If called again with the same thread_id, it will check for existing state
        and recover instead of reinitializing.

        Args:
            connection_id: WebSocket connection identifier
            test: Test model instance
            assessment_id: Assessment instance ID (used as thread_id)
            user_id: User taking the assessment
            db: Database session

        Returns:
            bool: True if initialization/recovery successful, False otherwise
        """
        try:
            thread_id = str(assessment_id)
            if not test:
                logger.error(f"Test not found for ID {test.test_id}")
                return None

            # Check if we've already initialized this thread
            if thread_id in self.initialized_threads:
                logger.info(
                    f"Thread {thread_id} already initialized, checking for existing state")
                recoverd_state = await self._check_and_recover_existing_state(thread_id, connection_id)
                return recoverd_state

            graph = await self._get_graph()

            # Check if graph already has state for this thread_id
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )

            existing_state = await graph.aget_state(config)
            if existing_state.values:
                logger.info(
                    f"Found existing graph state for thread {thread_id}, recovering")
                self.initialized_threads[thread_id] = True
                return existing_state.values  # type:ignore

            # No existing state, initialize new assessment
            logger.info(
                f"Initializing new assessment graph for thread {thread_id}")

            # Fetch candidate application
            candidate_application = await CandidateApplicationRepository.get_by_user_and_test(
                db, user_id, test.test_id  # type: ignore
            )

            if not candidate_application:
                logger.error(
                    f"Candidate application not found for user {user_id}")
                return None

            # Prepare initial state data
            parsed_jd = JobDescriptionFields.model_validate_json(
                test.parsed_job_description)  # type: ignore
            parsed_resume = ResumeFields.model_validate_json(
                candidate_application.parsed_resume)  # type: ignore
            skill_graph = SkillGraph.model_validate_json(
                test.skill_graph)  # type: ignore
            questions_per_difficulty = {
                "H": int(getattr(test, 'high_priority_questions')) if getattr(test, 'high_priority_questions') is not None else 5,
                "M": int(getattr(test, 'medium_priority_questions')) if getattr(test, 'medium_priority_questions') is not None else 5,
                "L": int(getattr(test, 'low_priority_questions')) if getattr(test, 'low_priority_questions') is not None else 3,
            }
            # Create initial agent state
            agent_state = AgentState(
                parsed_jd=parsed_jd,
                parsed_resume=parsed_resume,
                skill_graph=skill_graph,
                questions_per_difficulty=questions_per_difficulty,
            )

            # Initialize the graph with agent state
            state = await graph.ainvoke(agent_state, config=config)

            # Mark as initialized
            self.initialized_threads[thread_id] = True

            logger.info(
                f"Successfully initialized assessment graph for thread {thread_id}")
            return state  # type: ignore

        except Exception as e:
            logger.error(
                f"Error initializing assessment graph: {str(e)}", exc_info=True)
            return None

    async def _check_and_recover_existing_state(self, thread_id: str, connection_id: str) -> AgentState | None:
        """
        Check if existing state is valid and recoverable

        Args:
            thread_id: Thread ID to check
            connection_id: Connection requesting recovery

        Returns:
            bool: True if state is recoverable, False otherwise
        """
        try:
            graph = await self._get_graph()
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )

            state = await graph.aget_state(config)
            if state.values:
                logger.info(f"Recovered existing state for thread {thread_id}")
                return state.values  # type:ignore
            else:
                logger.warning(
                    f"No recoverable state found for thread {thread_id}")
                return None

        except Exception as e:
            logger.error(
                f"Error recovering state for thread {thread_id}: {str(e)}")
            return None

    async def _auto_finalize_if_deadline_passed(self, thread_id: str, db: AsyncSession) -> bool:
        """If test deadline passed finalize assessment, notify client, and close connection.
        Returns True if finalized now or already completed.
        Sends both a system_message (deadline notice) and assessment_completed payload, then closes socket."""
        try:
            assessment_id = int(thread_id)
            assessment_repo = AssessmentRepository(db)
            assessment = await assessment_repo.get_assessment_by_id(assessment_id)
            if not assessment:
                return False
            test_id = getattr(assessment, 'test_id', None)
            if not test_id:
                return False
            test_repo = TestRepository(db)
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                return False
            deadline = getattr(test, 'assessment_deadline', None)
            if not deadline:
                return False
            now = datetime.now(timezone.utc)
            if now >= deadline:
                # Guard: prevent duplicate finalize attempts
                if self._finalized_threads.get(thread_id):
                    return True
                self._finalized_threads[thread_id] = True
                finalize_result: Optional[Dict[str, Any]] = None
                previously_completed = getattr(
                    assessment, 'status', None) == AssessmentStatus.COMPLETED.value
                if not previously_completed:
                    finalize_result = await self.finalize_assessment_by_id(assessment_id, db)
                # Notify any active websocket connection(s)
                try:
                    from app.websocket.connection_manager import connection_manager
                    from app.websocket.handler import WebSocketMessageType
                    targets = [
                        cid for cid, state in connection_manager.active_connections.items()  # type: ignore
                        if getattr(state, 'assessment_id', None) == assessment_id
                    ]
                    if targets:
                        system_notice = {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "data": {
                                "message": "Assessment deadline reached. Auto-submitting your answers...",
                                "reason": "deadline_passed",
                                "assessment_id": assessment_id,
                                "test_id": test_id,
                                "thread_id": thread_id,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                        completion_payload = {
                            "type": WebSocketMessageType.ASSESSMENT_COMPLETED,
                            "data": {
                                "assessment_id": assessment_id,
                                "test_id": test_id,
                                "thread_id": thread_id,
                                "reason": "deadline_passed",
                                "finalized": True,
                                "final_percentage_score": (finalize_result or {}).get("final_percentage_score"),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                        for cid in targets:
                            # Send system notice then completion
                            await connection_manager.send_personal_message(cid, system_notice)
                            await connection_manager.send_personal_message(cid, completion_payload)
                            await asyncio.sleep(0)  # allow send buffer flush
                            # End assessment session & disconnect
                            try:
                                await connection_manager.end_assessment_session(cid)
                            except Exception:
                                pass
                            try:
                                await connection_manager.disconnect(cid)
                            except Exception:
                                pass
                        # Cleanup initialization tracker
                        self.initialized_threads.pop(thread_id, None)
                except Exception as notify_err:
                    logger.warning(
                        f"Failed to notify websocket for auto-finalized assessment {assessment_id}: {notify_err}")
                return True
        except Exception as e:
            logger.error(
                f"Auto finalize check failed for thread {thread_id}: {e}")
            return False

    async def finalize_assessment_by_id(self, assessment_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Finalize using assessment_id directly (used by auto finalize helper)."""
        thread_id = str(assessment_id)
        if self._finalized_threads.get(thread_id):
            return {"assessment_id": assessment_id, "status": AssessmentStatus.COMPLETED.value}
        lock = self._get_thread_lock(thread_id)
        async with lock:
            if self._finalized_threads.get(thread_id):
                return {"assessment_id": assessment_id, "status": AssessmentStatus.COMPLETED.value}
            try:
                assessment_repo = AssessmentRepository(db)
                existing = await assessment_repo.get_assessment_by_id(assessment_id)
                if existing and getattr(existing, 'status', None) == AssessmentStatus.COMPLETED.value:
                    self._finalized_threads[thread_id] = True
                    self.initialized_threads.pop(thread_id, None)
                    return {"assessment_id": assessment_id, "status": AssessmentStatus.COMPLETED.value}
                graph = await self._get_graph()
                thread_id = str(assessment_id)
                config = RunnableConfig(configurable={"thread_id": thread_id})
                try:
                    await graph.ainvoke(Command(resume={"type": "exit"}), config=config)
                except Exception:
                    pass
                state = await graph.aget_state(config)
                if not state.values:
                    logger.warning(
                        f"No state for assessment {assessment_id} during auto finalize")
                    candidate_graph = []
                    state_values = {}
                else:
                    state_values = json.loads(
                        json.dumps(state.values, cls=StateEncoder))
                    candidate_graph = state_values.get("candidate_graph", [])
                skill_weights = {"H": 3, "M": 2, "L": 1}
                skill_scores: Dict[str, List[float]] = {}
                for node in candidate_graph:
                    priority = node.get("priority")
                    score = node.get("score")
                    if priority and score is not None:
                        skill_scores.setdefault(priority, []).append(score)
                level_scores: Dict[str, float] = {}
                for priority, scores in skill_scores.items():
                    if scores:
                        level_scores[priority] = (
                            sum(scores) / len(scores)) * 100
                if level_scores:
                    numerator = sum(
                        level_scores[p] * skill_weights[p] for p in level_scores)
                    denominator = sum(skill_weights[p] for p in level_scores)
                    final_percentage_score = numerator / denominator
                else:
                    final_percentage_score = 0.0
                current_time = datetime.now(timezone.utc)
                result = {
                    "candidate_graph": candidate_graph,
                    "generated_questions": state_values.get("generated_questions", {}),
                    "candidate_response": state_values.get("candidate_response", {})
                }
                success = await assessment_repo.update_assessment_status(
                    assessment_id=assessment_id,
                    status=AssessmentStatus.COMPLETED.value,
                    percentage_score=final_percentage_score,
                    end_time=current_time,
                    result=result
                )
                if not success:
                    return None
                self._finalized_threads[thread_id] = True
                self.initialized_threads.pop(thread_id, None)
                return {"assessment_id": assessment_id, "status": AssessmentStatus.COMPLETED.value, "final_percentage_score": final_percentage_score}
            except Exception as e:
                logger.error(
                    f"Error finalize_assessment_by_id {assessment_id}: {e}")
                return None

    async def generate_question(self, connection_id: str, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        from app.websocket.connection_manager import connection_manager
        thread_id = connection_manager.get_connection_thread_id(connection_id)
        if not thread_id:
            logger.error(f"No thread_id found for connection {connection_id}")
            return None
        if self._finalized_threads.get(thread_id):
            return None
        lock = self._get_thread_lock(thread_id)

        async with lock:
            if db is not None:
                finalized = await self._auto_finalize_if_deadline_passed(thread_id, db)
                if finalized:
                    logger.info(
                        f"Deadline passed; skipping question generation for thread {thread_id}")
                    return None
            graph = await self._get_graph()
            config = RunnableConfig(configurable={"thread_id": thread_id})
            # Check current state
            current_state = await graph.aget_state(config)
            if not current_state.values:
                logger.error(f"No state found for thread {thread_id}")
                return None
            # Use Command to request question generation
            command = Command(resume={"type": "generate_question"})
            # Invoke graph with command
            result = await graph.ainvoke(command, config=config)
            # Get updated state to check for generated questions
            updated_state = await graph.aget_state(config)
            generated_questions = updated_state.values.get(
                "generated_questions", {})
            if not generated_questions:
                logger.warning(
                    f"No questions generated for thread {thread_id}")
                return None
            question_queue = updated_state.values.get("question_queue", [])
            if not question_queue:
                logger.warning(f"No questions in queue for thread {thread_id}")
                return None
            latest_question_id = question_queue[0]
            latest_question = generated_questions[latest_question_id]
            return {
                "question_id": latest_question_id,
                "question": latest_question.model_dump() if hasattr(latest_question, 'model_dump') else latest_question,
                "thread_id": thread_id
            }
        # except Exception as e:
        #     logger.error(
        #         f"Error generating question for connection {connection_id}: {str(e)}", exc_info=True)
        #     return None

    async def process_answer(
        self,
        connection_id: str,
        question_id: str,
        selected_option: str,
        db: Optional[AsyncSession] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process candidate's answer using MCQ graph
        (Now enforces deadline auto-finalization per message.)

        Args:
            connection_id: WebSocket connection identifier
            question_id: ID of the question being answered
            selected_option: Candidate's selected option

        Returns:
            Dict containing feedback and progress data or None if processing failed
        """
        try:
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)
            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None
            if self._finalized_threads.get(thread_id):
                return None
            lock = self._get_thread_lock(thread_id)
            async with lock:
                # Deadline check
                if db is not None:
                    finalized = await self._auto_finalize_if_deadline_passed(thread_id, db)
                    if finalized:
                        logger.info(
                            f"Deadline passed; rejecting answer processing for thread {thread_id}")
                        return None
                graph = await self._get_graph()
                config = RunnableConfig(
                    configurable={"thread_id": thread_id}
                )
                current_state = await graph.aget_state(config)
                generated_questions = current_state.values.get(
                    "generated_questions", {})
                if question_id not in generated_questions:
                    logger.error(
                        f"Question {question_id} not found in thread {thread_id}")
                    return None
                command = Command(resume={
                    "type": "submit_response",
                    "payload": {
                        "question_id": question_id,
                        "selected_option": selected_option
                    }
                })
                await graph.ainvoke(command, config=config)
                updated_state = await graph.aget_state(config)
                processed_nodes = updated_state.values.get(
                    "processed_nodes", [])
                candidate_graph = updated_state.values.get(
                    "candidate_graph", [])
                total_nodes = len(candidate_graph)
                completed_nodes = len(processed_nodes)
                progress = (completed_nodes / (total_nodes or 1)) * 100
                return {
                    "question_id": question_id,
                    "feedback": self._generate_feedback(question_id, selected_option, generated_questions),
                    "progress": {
                        "completed_nodes": completed_nodes,
                        "total_nodes": total_nodes,
                        "percentage_complete": progress
                    },
                    "thread_id": thread_id
                }
        except Exception as e:
            logger.error(
                f"Error processing answer for connection {connection_id}: {str(e)}", exc_info=True)
            return None

    async def get_assessment_progress(self, connection_id: str, db: Optional[AsyncSession] = None) -> Optional[Dict[str, Any]]:
        """Get current assessment progress with deadline auto-finalization."""
        try:
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)
            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None
            if db is not None:
                finalized = await self._auto_finalize_if_deadline_passed(thread_id, db)
                if finalized:
                    logger.info(
                        f"Deadline passed; progress request for finalized thread {thread_id}")
                    return None
            graph = await self._get_graph()
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )
            updated_state = await graph.aget_state(config)
            processed_nodes = updated_state.values.get("processed_nodes", [])
            candidate_graph = updated_state.values.get("candidate_graph", [])
            total_nodes = len(candidate_graph)
            completed_nodes = len(processed_nodes)
            progress = (completed_nodes / (total_nodes or 1)) * 100
            return {
                "total_nodes": total_nodes,
                "processed_nodes": processed_nodes,
                "percentage_complete": progress,
                "thread_id": thread_id
            }
        except Exception as e:
            logger.error(
                f"Error getting progress for connection {connection_id}: {str(e)}")
            return None

    async def get_assessment_state(self, thread_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get current assessment state, auto-finalizing if deadline passed."""
        try:
            if await self._auto_finalize_if_deadline_passed(thread_id, db):
                logger.info(
                    f"Deadline passed; state request after finalization for thread {thread_id}")
                return None
            graph = await self._get_graph()
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )
            state = await graph.aget_state(config)
            serialized_state = json.loads(
                json.dumps(state.values, cls=StateEncoder))
            if not state.values:
                logger.error(f"No state found for thread {thread_id}")
                return None
            return {"state": serialized_state}
        except Exception as e:
            logger.error(
                f"Error getting assessment state for thread {thread_id}: {str(e)}")
            return None

    async def finalize_assessment(self, connection_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Finalize assessment and save results to database

        Idempotent: if already completed, returns existing result summary.
        Always runs graph exit command before reading state.
        Uses AssessmentStatus enum consistently.
        """
        try:
            from app.websocket.connection_manager import connection_manager
            thread_id = connection_manager.get_connection_thread_id(
                connection_id)
            if not thread_id:
                logger.error(
                    f"No thread_id found for connection {connection_id}")
                return None
            lock = self._get_thread_lock(thread_id)
            async with lock:
                if self._finalized_threads.get(thread_id):
                    assessment_id = int(thread_id)
                    return {"assessment_id": assessment_id, "thread_id": thread_id, "status": AssessmentStatus.COMPLETED.value}
                assessment_id = int(thread_id)
                assessment_repo = AssessmentRepository(db)
                existing = await assessment_repo.get_assessment_by_id(assessment_id)
                if existing is not None and getattr(existing, 'status', None) == AssessmentStatus.COMPLETED.value:
                    end_time_val = getattr(existing, 'end_time', None)
                    self._finalized_threads[thread_id] = True
                    self.initialized_threads.pop(thread_id, None)
                    logger.info(
                        f"Assessment {assessment_id} already completed - idempotent finalize call")
                    return {
                        "assessment_id": assessment_id,
                        "thread_id": thread_id,
                        "status": AssessmentStatus.COMPLETED.value,
                        "final_percentage_score": getattr(existing, 'percentage_score', None),
                        "completion_time": end_time_val.isoformat() if end_time_val else None,
                    }
                graph = await self._get_graph()
                config = RunnableConfig(configurable={"thread_id": thread_id})
                # Ensure exit node runs (safe even if already run)
                try:
                    await graph.ainvoke(Command(resume={"type": "exit"}), config=config)
                except Exception as e:
                    logger.warning(
                        f"Graph exit command failed or already executed for thread {thread_id}: {e}")

                state = await graph.aget_state(config)
                if not state.values:
                    logger.error(f"No state found for thread {thread_id}")
                    return None
                state_values = json.loads(
                    json.dumps(state.values, cls=StateEncoder))

                candidate_graph = state_values.get("candidate_graph", [])
                if not candidate_graph:
                    logger.warning(
                        f"Empty candidate_graph for thread {thread_id}; proceeding with zero score")

                # Scoring
                skill_weights = {"H": 3, "M": 2, "L": 1}
                skill_scores: Dict[str, List[float]] = {}
                for node in candidate_graph:
                    priority = node.get("priority")
                    score = node.get("score")
                    if priority and score is not None:
                        skill_scores.setdefault(priority, []).append(score)
                level_scores: Dict[str, float] = {}
                for priority, scores in skill_scores.items():
                    if scores:
                        level_scores[priority] = (
                            sum(scores) / len(scores)) * 100
                if level_scores:
                    numerator = sum(
                        level_scores[p] * skill_weights[p] for p in level_scores)
                    denominator = sum(skill_weights[p] for p in level_scores)
                    final_percentage_score = numerator / denominator
                else:
                    final_percentage_score = 0.0

                current_time = datetime.now(timezone.utc)
                result = {
                    "candidate_graph": candidate_graph,
                    "generated_questions": state_values.get("generated_questions", {}),
                    "candidate_response": state_values.get("candidate_response", {})
                }

                success = await assessment_repo.update_assessment_status(
                    assessment_id=assessment_id,
                    status=AssessmentStatus.COMPLETED.value,
                    percentage_score=final_percentage_score,
                    end_time=current_time,
                    result=result
                )
                if not success:
                    logger.error(
                        f"Failed to update assessment {assessment_id}")
                    return None

                # After success:
                self._finalized_threads[thread_id] = True
                if thread_id in self.initialized_threads:
                    del self.initialized_threads[thread_id]

                skill_breakdown: Dict[str, Any] = {}
                total_questions = 0
                total_correct = 0
                for node in candidate_graph:
                    priority = node.get("priority")
                    score = node.get("score", 0)
                    node_id = node.get("node_id")
                    asked_questions = node.get("asked_questions", [])
                    if priority not in skill_breakdown:
                        skill_breakdown[priority] = {
                            "nodes": [], "total_questions": 0, "average_score": 0}
                    node_questions = len(asked_questions)
                    node_correct = int(
                        score * node_questions) if score and node_questions > 0 else 0
                    skill_breakdown[priority]["nodes"].append({
                        "skill": node_id,
                        "score": score * 100 if score else 0,
                        "questions_asked": node_questions,
                        "correct_answers": node_correct
                    })
                    skill_breakdown[priority]["total_questions"] += node_questions
                    total_questions += node_questions
                    total_correct += node_correct
                for priority in skill_breakdown:
                    nodes = skill_breakdown[priority]["nodes"]
                    if nodes:
                        skill_breakdown[priority]["average_score"] = sum(
                            n["score"] for n in nodes) / len(nodes)

                logger.info(
                    f"Finalized assessment {assessment_id} (thread {thread_id}) score {final_percentage_score:.2f}%")
                return {
                    "assessment_id": assessment_id,
                    "thread_id": thread_id,
                    "final_percentage_score": round(final_percentage_score, 2),
                    "total_questions": total_questions,
                    "total_correct": total_correct,
                    "skill_breakdown": skill_breakdown,
                    "level_scores": {k: round(v, 2) for k, v in level_scores.items()},
                    "completion_time": current_time.isoformat(),
                    "status": AssessmentStatus.COMPLETED.value
                }
        except Exception as e:
            logger.error(
                f"Error finalizing assessment for connection {connection_id}: {str(e)}", exc_info=True)
            return None

    def cleanup_connection(self, connection_id: str):
        logger.info(
            f"Cleaning up assessment resources for connection {connection_id}")
        # Note: Graph state persists via thread_id in langgraph's persistence layer

    def _generate_feedback(self, question_id: str, selected_option: str, questions: Dict) -> Dict[str, Any]:
        """Generate feedback for the submitted answer (restored method)."""
        question = questions.get(question_id)
        if not question:
            return {"message": "Question not found"}
        correct_answer = getattr(question, 'correct_option', None) or getattr(
            question, 'correct_answer', None)
        is_correct = selected_option == correct_answer
        return {
            "correct": is_correct,
            "selected_option": selected_option,
            "correct_answer": correct_answer,
            "message": "Correct answer!" if is_correct else f"Incorrect. The correct answer is {correct_answer}"
        }


# Global assessment service instance
assessment_graph_service = AssessmentGraphService()
