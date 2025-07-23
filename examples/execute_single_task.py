
import asyncio
from pathlib import Path
from agent_orchestrator.core.engine import OrchestratorEngine
from agent_orchestrator.models.task import Task

async def main():
    """
    Executa uma única tarefa de teste.
    """
    engine = OrchestratorEngine()

    task = Task(
        id="TASK-001",
        title="Task TASK-001",
        description="Descrição da task TASK-001",
        user_story_id="US-001",
        agent_type="gemini",  # Forçando o agente gemini
        priority="medium",
        complexity="medium",
        acceptance_criteria=["Funcionalidade implementada conforme especificação"],
    )

    print(f"Executando a tarefa: {task.id} - {task.title}")
    result = await engine.execute_task(task_id=task.id)
    print(f"Resultado da execução: {result.message}")

if __name__ == "__main__":
    asyncio.run(main())
