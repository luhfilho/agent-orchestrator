"""
Sprint Executor - Agent Orchestrator
Executor de sprint completo com execução sequencial e rollback
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.sprint import Sprint
from ..models.task import Task, TaskResult
from ..core.orchestrator import Orchestrator
from ..utils.advanced_logger import advanced_logger, LogLevel
from ..reporting.progress_reporter import ProgressReporter, ReportFormat


class ExecutionStatus(Enum):
    """Status de execução"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class SprintExecutionState:
    """Estado da execução do sprint"""
    sprint_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0
    current_task: Optional[str] = None
    task_results: List[TaskResult] = None
    rollback_stack: List[str] = None
    
    def __post_init__(self):
        if self.task_results is None:
            self.task_results = []
        if self.rollback_stack is None:
            self.rollback_stack = []


class SprintExecutor:
    """Executor de sprint completo"""
    
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.logger = advanced_logger
        self.reporter = ProgressReporter()
        self.execution_states: Dict[str, SprintExecutionState] = {}
    
    async def execute_sprint(self, sprint: Sprint, 
                           agent_type: str = "auto",
                           enable_rollback: bool = True,
                           notify_progress: bool = True) -> List[TaskResult]:
        """
        Executa sprint completo
        
        Args:
            sprint: Sprint a ser executado
            agent_type: Tipo de agente a usar
            enable_rollback: Habilitar rollback em caso de falha
            notify_progress: Notificar progresso durante execução
            
        Returns:
            List[TaskResult]: Resultados das tasks
        """
        # Inicializar estado de execução
        execution_state = SprintExecutionState(
            sprint_id=sprint.id,
            status=ExecutionStatus.IN_PROGRESS,
            start_time=datetime.now(),
            total_tasks=len(sprint.user_stories)
        )
        self.execution_states[sprint.id] = execution_state
        
        self.logger.log_structured(
            "execution",
            LogLevel.INFO,
            f"Sprint execution started: {sprint.id}",
            data={
                "sprint_id": sprint.id,
                "total_tasks": execution_state.total_tasks,
                "agent_type": agent_type,
                "enable_rollback": enable_rollback
            }
        )
        
        try:
            # Executar tasks sequencialmente
            task_results = await self._execute_tasks_sequentially(
                sprint, agent_type, execution_state, notify_progress
            )
            
            # Verificar se todas as tasks foram bem-sucedidas
            failed_tasks = [r for r in task_results if not r.success]
            
            if failed_tasks and enable_rollback:
                self.logger.log_structured(
                    "execution",
                    LogLevel.WARNING,
                    f"Rollback triggered due to {len(failed_tasks)} failed tasks"
                )
                await self._rollback_sprint(sprint, task_results, execution_state)
                execution_state.status = ExecutionStatus.ROLLED_BACK
            elif failed_tasks:
                execution_state.status = ExecutionStatus.FAILED
            else:
                execution_state.status = ExecutionStatus.COMPLETED
            
            # Finalizar execução
            execution_state.end_time = datetime.now()
            execution_state.completed_tasks = len([r for r in task_results if r.success])
            execution_state.failed_tasks = len([r for r in task_results if not r.success])
            
            # Gerar relatório
            await self._generate_execution_report(sprint, task_results, execution_state)
            
            # Log de conclusão
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Sprint execution completed: {sprint.id}",
                data={
                    "status": execution_state.status.value,
                    "completed_tasks": execution_state.completed_tasks,
                    "failed_tasks": execution_state.failed_tasks,
                    "total_time": (execution_state.end_time - execution_state.start_time).total_seconds()
                }
            )
            
            return task_results
            
        except Exception as e:
            execution_state.status = ExecutionStatus.FAILED
            execution_state.end_time = datetime.now()
            
            self.logger.log_error(e, {
                "sprint_id": sprint.id,
                "component": "sprint_executor"
            })
            
            if enable_rollback:
                await self._rollback_sprint(sprint, execution_state.task_results, execution_state)
            
            raise
    
    async def _execute_tasks_sequentially(self, sprint: Sprint, agent_type: str,
                                         execution_state: SprintExecutionState,
                                         notify_progress: bool) -> List[TaskResult]:
        """Executa tasks sequencialmente"""
        task_results = []
        
        for i, user_story in enumerate(sprint.user_stories):
            # Atualizar task atual
            execution_state.current_task = user_story.id
            
            # Notificar progresso
            if notify_progress:
                progress_percentage = (i / len(sprint.user_stories)) * 100
                self.logger.log_sprint_progress(
                    sprint.id, i, len(sprint.user_stories), progress_percentage
                )
            
            # Converter ID da user story para formato de task
            task_id = f"TASK-{user_story.id.replace('US-', '').zfill(3)}"
            
            # Converter prioridade para formato esperado
            priority_map = {
                "P1": "critical",
                "P2": "high", 
                "P3": "medium",
                "P4": "low"
            }
            task_priority = priority_map.get(user_story.priority, "medium")
            
            # Criar task
            task = Task(
                id=task_id,
                title=user_story.title,
                description=user_story.description,
                user_story_id=user_story.id,
                agent_type=agent_type,
                priority=task_priority,
                complexity="high" if user_story.story_points > 8 else "medium"
            )
            
            # Executar task
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Executing task: {task.id}",
                data={
                    "task_id": task.id,
                    "task_number": i + 1,
                    "total_tasks": len(sprint.user_stories),
                    "agent_type": agent_type
                }
            )
            
            try:
                result = await self.orchestrator.execute_task(task)
                task_results.append(result)
                
                # Log de resultado
                self.logger.log_task_execution(
                    task.id, result.agent_used, result.execution_time, 
                    result.success, result.error
                )
                
                # Adicionar ao rollback stack se bem-sucedido
                if result.success and hasattr(self, '_rollback_enabled'):
                    execution_state.rollback_stack.append(task.id)
                
                # Pausa entre tasks para evitar sobrecarga
                if i < len(sprint.user_stories) - 1:
                    await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.log_error(e, {
                    "task_id": task.id,
                    "sprint_id": sprint.id
                })
                
                # Criar resultado de falha
                failed_result = TaskResult(
                    success=False,
                    message=f"Task failed: {str(e)}",
                    error=str(e),
                    execution_time=0.0,
                    agent_used=agent_type
                )
                task_results.append(failed_result)
        
        return task_results
    
    async def _rollback_sprint(self, sprint: Sprint, task_results: List[TaskResult],
                              execution_state: SprintExecutionState):
        """Executa rollback do sprint"""
        self.logger.log_structured(
            "execution",
            LogLevel.WARNING,
            f"Starting rollback for sprint: {sprint.id}",
            data={
                "sprint_id": sprint.id,
                "rollback_stack_size": len(execution_state.rollback_stack)
            }
        )
        
        # Por enquanto, apenas log do rollback
        # Em implementação real, seria necessário desfazer mudanças
        for task_id in reversed(execution_state.rollback_stack):
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Rolling back task: {task_id}",
                data={"task_id": task_id}
            )
        
        self.logger.log_structured(
            "execution",
            LogLevel.INFO,
            f"Rollback completed for sprint: {sprint.id}"
        )
    
    async def _generate_execution_report(self, sprint: Sprint, 
                                       task_results: List[TaskResult],
                                       execution_state: SprintExecutionState):
        """Gera relatório de execução"""
        try:
            report_path = self.reporter.generate_sprint_report(
                sprint, task_results, ReportFormat.MARKDOWN
            )
            
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Execution report generated: {report_path}",
                data={
                    "report_path": str(report_path),
                    "sprint_id": sprint.id
                }
            )
            
        except Exception as e:
            self.logger.log_error(e, {
                "component": "report_generation",
                "sprint_id": sprint.id
            })
    
    def get_execution_status(self, sprint_id: str) -> Optional[SprintExecutionState]:
        """Retorna status da execução de um sprint"""
        return self.execution_states.get(sprint_id)
    
    def get_all_execution_statuses(self) -> Dict[str, SprintExecutionState]:
        """Retorna status de todas as execuções"""
        return self.execution_states.copy()
    
    def cancel_sprint_execution(self, sprint_id: str) -> bool:
        """Cancela execução de um sprint"""
        if sprint_id in self.execution_states:
            execution_state = self.execution_states[sprint_id]
            if execution_state.status == ExecutionStatus.IN_PROGRESS:
                execution_state.status = ExecutionStatus.FAILED
                execution_state.end_time = datetime.now()
                
                self.logger.log_structured(
                    "execution",
                    LogLevel.WARNING,
                    f"Sprint execution cancelled: {sprint_id}",
                    data={
                        "sprint_id": sprint_id,
                        "completed_tasks": execution_state.completed_tasks,
                        "failed_tasks": execution_state.failed_tasks
                    }
                )
                return True
        return False
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de execução"""
        total_executions = len(self.execution_states)
        completed_executions = len([
            s for s in self.execution_states.values() 
            if s.status == ExecutionStatus.COMPLETED
        ])
        failed_executions = len([
            s for s in self.execution_states.values() 
            if s.status in [ExecutionStatus.FAILED, ExecutionStatus.ROLLED_BACK]
        ])
        
        total_tasks = sum(s.total_tasks for s in self.execution_states.values())
        completed_tasks = sum(s.completed_tasks for s in self.execution_states.values())
        failed_tasks = sum(s.failed_tasks for s in self.execution_states.values())
        
        return {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "success_rate": (completed_executions / total_executions * 100) if total_executions > 0 else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "task_success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        } 