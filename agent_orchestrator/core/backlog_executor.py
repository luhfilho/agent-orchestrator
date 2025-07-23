"""
Backlog Executor - Agent Orchestrator
Executor de backlog completo com organização automática em sprints
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.backlog import Backlog
from ..models.sprint import Sprint
from ..models.task import Task, TaskResult
from ..core.orchestrator import Orchestrator
from ..core.sprint_executor import SprintExecutor
from ..utils.advanced_logger import advanced_logger, LogLevel
from ..reporting.progress_reporter import ProgressReporter, ReportFormat


class BacklogExecutionStatus(Enum):
    """Status de execução do backlog"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class BacklogExecutionState:
    """Estado da execução do backlog"""
    backlog_id: str
    status: BacklogExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_sprints: int = 0
    completed_sprints: int = 0
    failed_sprints: int = 0
    current_sprint: Optional[str] = None
    sprint_results: List[Dict[str, Any]] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    estimated_completion: Optional[datetime] = None
    
    def __post_init__(self):
        if self.sprint_results is None:
            self.sprint_results = []


class BacklogExecutor:
    """Executor de backlog completo"""
    
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.sprint_executor = SprintExecutor(orchestrator)
        self.logger = advanced_logger
        self.reporter = ProgressReporter()
        self.execution_states: Dict[str, BacklogExecutionState] = {}
    
    async def execute_backlog(self, backlog: Backlog, 
                            max_points_per_sprint: int = 20,
                            agent_type: str = "auto",
                            enable_rollback: bool = True,
                            pause_on_failure: bool = True,
                            estimate_time: bool = True) -> Dict[str, Any]:
        """
        Executa backlog completo
        
        Args:
            backlog: Backlog a ser executado
            max_points_per_sprint: Pontos máximos por sprint
            agent_type: Tipo de agente a usar
            enable_rollback: Habilitar rollback em caso de falha
            pause_on_failure: Pausar em caso de falha
            estimate_time: Estimar tempo de conclusão
            
        Returns:
            Dict[str, Any]: Resultados da execução
        """
        # Inicializar estado de execução
        execution_state = BacklogExecutionState(
            backlog_id=backlog.id,
            status=BacklogExecutionStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        self.execution_states[backlog.id] = execution_state
        
        self.logger.log_structured(
            "execution",
            LogLevel.INFO,
            f"Backlog execution started: {backlog.id}",
            data={
                "backlog_id": backlog.id,
                "total_stories": len(backlog.user_stories),
                "total_points": backlog.total_points,
                "max_points_per_sprint": max_points_per_sprint,
                "agent_type": agent_type,
                "enable_rollback": enable_rollback
            }
        )
        
        try:
            # Organizar backlog em sprints
            sprints = await self._organize_backlog_into_sprints(
                backlog, max_points_per_sprint
            )
            execution_state.total_sprints = len(sprints)
            execution_state.total_tasks = sum(len(s.user_stories) for s in sprints)
            
            # Estimar tempo de conclusão
            if estimate_time:
                estimated_time = self._estimate_completion_time(sprints, agent_type)
                execution_state.estimated_completion = estimated_time
                
                self.logger.log_structured(
                    "execution",
                    LogLevel.INFO,
                    f"Estimated completion time: {estimated_time}",
                    data={
                        "backlog_id": backlog.id,
                        "estimated_completion": estimated_time.isoformat()
                    }
                )
            
            # Executar sprints sequencialmente
            results = await self._execute_sprints_sequentially(
                sprints, agent_type, execution_state, enable_rollback, pause_on_failure
            )
            
            # Finalizar execução
            execution_state.end_time = datetime.now()
            execution_state.completed_sprints = len([r for r in results if r["success"]])
            execution_state.failed_sprints = len([r for r in results if not r["success"]])
            execution_state.completed_tasks = sum(r["completed_tasks"] for r in results)
            execution_state.failed_tasks = sum(r["failed_tasks"] for r in results)
            
            # Determinar status final
            if execution_state.failed_sprints == 0:
                execution_state.status = BacklogExecutionStatus.COMPLETED
            elif execution_state.status == BacklogExecutionStatus.PAUSED:
                # Manter status pausado
                pass
            else:
                execution_state.status = BacklogExecutionStatus.FAILED
            
            # Gerar relatório final
            await self._generate_backlog_report(backlog, sprints, results, execution_state)
            
            # Log de conclusão
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Backlog execution completed: {backlog.id}",
                data={
                    "status": execution_state.status.value,
                    "completed_sprints": execution_state.completed_sprints,
                    "failed_sprints": execution_state.failed_sprints,
                    "completed_tasks": execution_state.completed_tasks,
                    "failed_tasks": execution_state.failed_tasks,
                    "total_time": (execution_state.end_time - execution_state.start_time).total_seconds()
                }
            )
            
            return {
                "backlog_id": backlog.id,
                "status": execution_state.status.value,
                "sprints": results,
                "total_sprints": execution_state.total_sprints,
                "completed_sprints": execution_state.completed_sprints,
                "failed_sprints": execution_state.failed_sprints,
                "total_tasks": execution_state.total_tasks,
                "completed_tasks": execution_state.completed_tasks,
                "failed_tasks": execution_state.failed_tasks,
                "execution_time": (execution_state.end_time - execution_state.start_time).total_seconds()
            }
            
        except Exception as e:
            execution_state.status = BacklogExecutionStatus.FAILED
            execution_state.end_time = datetime.now()
            
            self.logger.log_error(e, {
                "backlog_id": backlog.id,
                "component": "backlog_executor"
            })
            
            raise
    
    async def _organize_backlog_into_sprints(self, backlog: Backlog, 
                                           max_points_per_sprint: int) -> List[Sprint]:
        """Organiza backlog em sprints"""
        sprints = []
        current_sprint_stories = []
        current_points = 0
        sprint_number = 1
        
        # Ordenar stories por prioridade e pontos
        sorted_stories = sorted(
            backlog.user_stories,
            key=lambda s: (s.priority, -s.story_points)
        )
        
        for story in sorted_stories:
            # Verificar se a story cabe no sprint atual
            if current_points + story.story_points <= max_points_per_sprint:
                current_sprint_stories.append(story)
                current_points += story.story_points
            else:
                # Criar sprint atual
                if current_sprint_stories:
                    sprint = Sprint(
                        id=f"SPRINT-{backlog.id}-{sprint_number:03d}",
                        name=f"Sprint {sprint_number}",
                        description=f"Sprint {sprint_number} do backlog {backlog.id}",
                        user_stories=current_sprint_stories,
                        max_points=max_points_per_sprint,
                        status="planned",
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(days=14)
                    )
                    sprints.append(sprint)
                    sprint_number += 1
                
                # Iniciar novo sprint
                current_sprint_stories = [story]
                current_points = story.story_points
        
        # Adicionar último sprint se houver stories
        if current_sprint_stories:
            sprint = Sprint(
                id=f"SPRINT-{backlog.id}-{sprint_number:03d}",
                name=f"Sprint {sprint_number}",
                description=f"Sprint {sprint_number} do backlog {backlog.id}",
                user_stories=current_sprint_stories,
                max_points=max_points_per_sprint,
                status="planned",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=14)
            )
            sprints.append(sprint)
        
        self.logger.log_structured(
            "execution",
            LogLevel.INFO,
            f"Backlog organized into {len(sprints)} sprints",
            data={
                "backlog_id": backlog.id,
                "total_sprints": len(sprints),
                "max_points_per_sprint": max_points_per_sprint
            }
        )
        
        return sprints
    
    def _estimate_completion_time(self, sprints: List[Sprint], agent_type: str) -> datetime:
        """Estima tempo de conclusão baseado em sprints"""
        # Estimativa baseada em experiência (pode ser refinada)
        avg_time_per_sprint = 30  # minutos por sprint
        total_minutes = len(sprints) * avg_time_per_sprint
        
        return datetime.now() + timedelta(minutes=total_minutes)
    
    async def _execute_sprints_sequentially(self, sprints: List[Sprint], 
                                          agent_type: str,
                                          execution_state: BacklogExecutionState,
                                          enable_rollback: bool,
                                          pause_on_failure: bool) -> List[Dict[str, Any]]:
        """Executa sprints sequencialmente"""
        results = []
        
        for i, sprint in enumerate(sprints):
            # Atualizar sprint atual
            execution_state.current_sprint = sprint.id
            
            # Log de progresso
            progress_percentage = (i / len(sprints)) * 100
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Executing sprint {i+1}/{len(sprints)}: {sprint.id}",
                data={
                    "sprint_id": sprint.id,
                    "sprint_number": i + 1,
                    "total_sprints": len(sprints),
                    "progress_percentage": progress_percentage
                }
            )
            
            try:
                # Executar sprint
                task_results = await self.sprint_executor.execute_sprint(
                    sprint, agent_type, enable_rollback, True
                )
                
                # Calcular métricas do sprint
                completed_tasks = len([r for r in task_results if r.success])
                failed_tasks = len([r for r in task_results if not r.success])
                
                sprint_result = {
                    "sprint_id": sprint.id,
                    "success": failed_tasks == 0,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "total_tasks": len(task_results),
                    "task_results": [r.__dict__ for r in task_results],
                    "execution_time": sum(r.execution_time for r in task_results)
                }
                
                results.append(sprint_result)
                execution_state.sprint_results.append(sprint_result)
                
                # Verificar se deve pausar em caso de falha
                if failed_tasks > 0 and pause_on_failure:
                    execution_state.status = BacklogExecutionStatus.PAUSED
                    
                    self.logger.log_structured(
                        "execution",
                        LogLevel.WARNING,
                        f"Backlog execution paused due to sprint failure: {sprint.id}",
                        data={
                            "sprint_id": sprint.id,
                            "failed_tasks": failed_tasks,
                            "total_tasks": len(task_results)
                        }
                    )
                    
                    # Perguntar ao usuário se deve continuar
                    # Em implementação real, seria uma interface interativa
                    break
                
                # Pausa entre sprints
                if i < len(sprints) - 1:
                    await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.log_error(e, {
                    "sprint_id": sprint.id,
                    "backlog_id": execution_state.backlog_id
                })
                
                sprint_result = {
                    "sprint_id": sprint.id,
                    "success": False,
                    "completed_tasks": 0,
                    "failed_tasks": len(sprint.user_stories),
                    "total_tasks": len(sprint.user_stories),
                    "task_results": [],
                    "execution_time": 0,
                    "error": str(e)
                }
                
                results.append(sprint_result)
                execution_state.sprint_results.append(sprint_result)
                
                if pause_on_failure:
                    execution_state.status = BacklogExecutionStatus.PAUSED
                    break
        
        return results
    
    async def _generate_backlog_report(self, backlog: Backlog, sprints: List[Sprint],
                                     results: List[Dict[str, Any]],
                                     execution_state: BacklogExecutionState):
        """Gera relatório final do backlog"""
        try:
            report_file = self.reporter.output_dir / f"backlog_report_{backlog.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write(f"# Relatório de Execução - Backlog {backlog.id}\n\n")
                f.write(f"**Data do Relatório:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Resumo executivo
                f.write("## 📊 Resumo Executivo\n\n")
                f.write(f"- **Backlog:** {backlog.title}\n")
                f.write(f"- **Status:** {execution_state.status.value}\n")
                f.write(f"- **Sprints:** {execution_state.completed_sprints}/{execution_state.total_sprints}\n")
                f.write(f"- **Tasks:** {execution_state.completed_tasks}/{execution_state.total_tasks}\n")
                f.write(f"- **Tempo Total:** {(execution_state.end_time - execution_state.start_time).total_seconds():.2f}s\n\n")
                
                # Detalhes dos sprints
                f.write("## 🏃 Detalhes dos Sprints\n\n")
                f.write("| Sprint | Status | Tasks | Tempo |\n")
                f.write("|--------|--------|-------|-------|\n")
                
                for result in results:
                    status = "✅ Sucesso" if result["success"] else "❌ Falha"
                    f.write(f"| {result['sprint_id']} | {status} | {result['completed_tasks']}/{result['total_tasks']} | {result['execution_time']:.2f}s |\n")
                
                f.write("\n")
                
                # Recomendações
                f.write("## 💡 Recomendações\n\n")
                if execution_state.failed_sprints > 0:
                    f.write("- Revisar sprints que falharam\n")
                    f.write("- Verificar dependências entre tasks\n")
                    f.write("- Considerar ajustar pontos por sprint\n")
                else:
                    f.write("- Backlog executado com sucesso\n")
                    f.write("- Manter configurações atuais\n")
                
                f.write("\n")
            
            self.logger.log_structured(
                "execution",
                LogLevel.INFO,
                f"Backlog report generated: {report_file}",
                data={
                    "report_path": str(report_file),
                    "backlog_id": backlog.id
                }
            )
            
        except Exception as e:
            self.logger.log_error(e, {
                "component": "backlog_report_generation",
                "backlog_id": backlog.id
            })
    
    def get_execution_status(self, backlog_id: str) -> Optional[BacklogExecutionState]:
        """Retorna status da execução de um backlog"""
        return self.execution_states.get(backlog_id)
    
    def get_all_execution_statuses(self) -> Dict[str, BacklogExecutionState]:
        """Retorna status de todas as execuções"""
        return self.execution_states.copy()
    
    def pause_backlog_execution(self, backlog_id: str) -> bool:
        """Pausa execução de um backlog"""
        if backlog_id in self.execution_states:
            execution_state = self.execution_states[backlog_id]
            if execution_state.status == BacklogExecutionStatus.IN_PROGRESS:
                execution_state.status = BacklogExecutionStatus.PAUSED
                
                self.logger.log_structured(
                    "execution",
                    LogLevel.WARNING,
                    f"Backlog execution paused: {backlog_id}",
                    data={
                        "backlog_id": backlog_id,
                        "completed_sprints": execution_state.completed_sprints,
                        "failed_sprints": execution_state.failed_sprints
                    }
                )
                return True
        return False
    
    def resume_backlog_execution(self, backlog_id: str) -> bool:
        """Retoma execução de um backlog pausado"""
        if backlog_id in self.execution_states:
            execution_state = self.execution_states[backlog_id]
            if execution_state.status == BacklogExecutionStatus.PAUSED:
                execution_state.status = BacklogExecutionStatus.IN_PROGRESS
                
                self.logger.log_structured(
                    "execution",
                    LogLevel.INFO,
                    f"Backlog execution resumed: {backlog_id}"
                )
                return True
        return False
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de execução de backlogs"""
        total_executions = len(self.execution_states)
        completed_executions = len([
            s for s in self.execution_states.values() 
            if s.status == BacklogExecutionStatus.COMPLETED
        ])
        failed_executions = len([
            s for s in self.execution_states.values() 
            if s.status == BacklogExecutionStatus.FAILED
        ])
        paused_executions = len([
            s for s in self.execution_states.values() 
            if s.status == BacklogExecutionStatus.PAUSED
        ])
        
        total_sprints = sum(s.total_sprints for s in self.execution_states.values())
        completed_sprints = sum(s.completed_sprints for s in self.execution_states.values())
        failed_sprints = sum(s.failed_sprints for s in self.execution_states.values())
        
        return {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "paused_executions": paused_executions,
            "success_rate": (completed_executions / total_executions * 100) if total_executions > 0 else 0,
            "total_sprints": total_sprints,
            "completed_sprints": completed_sprints,
            "failed_sprints": failed_sprints,
            "sprint_success_rate": (completed_sprints / total_sprints * 100) if total_sprints > 0 else 0
        } 