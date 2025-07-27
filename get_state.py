from app.services.mcq_generation import get_question_generation_graph
import asyncio
from dotenv import load_dotenv
load_dotenv()

if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    question_generation_graph = await get_question_generation_graph()
    # Do something with the question_generation_graph

    while True:
        thread_id = input("Thread ID : ")
        if thread_id.lower() == 'exit':
            break
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        state = await question_generation_graph.aget_state(config)
        print(
            f"State for thread {thread_id}:"
        )
        print(
            f"Candidate Graph : {state.values['candidate_graph']}\n"
        )
        print(
            f"Skill Graph : {state.values['skill_graph']}\n"
        )
        print(f"Generated Questions : {state.values['generated_questions']}\n"
              )
        print(f"Current Node : {state.values['current_node']}\n")
        print(f"Candidate Responses : {state.values['candidate_response']}\n")
        print(f"node_queue : {state.values['node_queue']}\n")
        print(f"processed_nodes : {state.values['processed_nodes']}\n")
        print(f"last_node_id : {state.values['last_node_id']}\n")
        print(f"question_queue : {state.values['question_queue']}\n")
        print(f"metadata : {state.values['metadata']}\n")
        print(f"recent_history : {state.values['recent_history']}\n")

asyncio.run(main())
