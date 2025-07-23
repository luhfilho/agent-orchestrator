"""
Core Engine - Agent Orchestrator
Engine principal que orquestra todo o sistema
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models.backlog import Backlog, UserStory
from ..models.task import Task, TaskResult
from ..models.sprint import Sprint
from ..utils.logger import logger
from ..utils.markdown_parser import MarkdownBacklogParser
from .orchestrator import Orchestrator
from .scheduler import TaskScheduler
from .validator import TaskValidator
from .storage import StorageManager, StorageConfig
from .sprint_executor import SprintExecutor
from .backlog_executor import BacklogExecutor
from ..config.advanced_config import ConfigManager


@dataclass
class EngineConfig:
    """Configuração do Core Engine"""
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    default_agent: str = "auto"
    log_level: str = "INFO"
    cache_enabled: bool = True
    retry_attempts: int = 3


class OrchestratorEngine:
    """Engine principal do Agent Orchestrator"""
    
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.orchestrator = Orchestrator()
        self.scheduler = TaskScheduler()
        self.validator = TaskValidator()
        self.logger = logger
        
        # Sistema de storage
        storage_config = StorageConfig()
        self.storage = StorageManager(storage_config)
        
        # Sprint executor
        self.sprint_executor = SprintExecutor(self.orchestrator)
        
        # Backlog executor
        self.backlog_executor = BacklogExecutor(self.orchestrator)
        
        # Config manager
        self.config_manager = ConfigManager()
        
        # Cache para resultados
        self._cache: Dict[str, Any] = {}
        self._execution_history: List[Dict[str, Any]] = []
        
        self.logger.info("🚀 Core Engine inicializado")
    
    async def analyze_backlog(self, file_path: Path) -> Backlog:
        """
        Analisa um arquivo de backlog
        
        Args:
            file_path: Caminho para o arquivo de backlog
            
        Returns:
            Backlog: Objeto backlog analisado
        """
        start_time = time.time()
        self.logger.info(f"🔍 Analisando backlog: {file_path}")
        
        try:
            # Verificar se arquivo existe
            if not file_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Usar parser de markdown para análise real
            from ..utils.markdown_parser import MarkdownBacklogParser, MarkdownBacklogParserError
            
            parser = MarkdownBacklogParser(file_path)
            backlog = await parser.parse()
            
            # Exibir warnings se houver
            if parser.has_warnings():
                self.logger.warning("⚠️ Warnings encontrados durante o parsing:")
                for warning in parser.get_warnings():
                    self.logger.warning(f"  {warning}")
            
            # Validar backlog
            self.validator.validate_backlog(backlog)
            
            # Calcular métricas
            backlog.calculate_total_points()
            
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "analyze_backlog",
                execution_time,
                True,
                file_path=str(file_path),
                stories_count=len(backlog.user_stories),
                total_points=backlog.total_points
            )
            
            self.logger.log_backlog_analysis(
                str(file_path),
                len(backlog.user_stories),
                backlog.total_points
            )
            
            return backlog
            
        except MarkdownBacklogParserError as e:
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "analyze_backlog",
                execution_time,
                False,
                error=str(e)
            )
            self.logger.error(f"❌ Erro no parsing do backlog:\n{str(e)}")
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "analyze_backlog",
                execution_time,
                False,
                error=str(e)
            )
            self.logger.error(f"Erro na análise do backlog: {str(e)}")
            raise
    
    async def generate_sprint(self, backlog: Backlog, max_points: int, 
                            priority: Optional[str] = None) -> Sprint:
        """
        Gera um sprint baseado no backlog
        
        Args:
            backlog: Backlog analisado
            max_points: Máximo de pontos para o sprint
            priority: Prioridade mínima (opcional)
            
        Returns:
            Sprint: Sprint gerado
        """
        start_time = time.time()
        self.logger.info(f"🏃 Gerando sprint com {max_points} pontos")
        
        try:
            # Selecionar stories baseado em critérios
            selected_stories = self._select_stories_for_sprint(
                backlog, max_points, priority
            )
            
            # Validar dependências
            self._validate_sprint_dependencies(selected_stories)
            
            # Calcular data de fim (2 semanas padrão)
            from datetime import timedelta
            start_date = datetime.now()
            end_date = start_date + timedelta(days=14)
            
            # Criar sprint
            sprint = Sprint(
                id=f"SPRINT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                name=f"Sprint {datetime.now().strftime('%Y-%m-%d')}",
                description=f"Sprint gerado automaticamente com {max_points} pontos",
                user_stories=selected_stories,
                max_points=max_points,
                start_date=start_date,
                end_date=end_date,
                status="planned"
            )
            
            # Salvar sprint no storage
            await self.storage.save_sprint(sprint)
            
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "generate_sprint",
                execution_time,
                True,
                sprint_id=sprint.id,
                stories_count=len(selected_stories),
                points=sum(s.story_points for s in selected_stories)
            )
            
            self.logger.log_sprint_generation(
                sprint.id,
                len(selected_stories),
                sum(s.story_points for s in selected_stories)
            )
            
            return sprint
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "generate_sprint",
                execution_time,
                False,
                error=str(e)
            )
            self.logger.error(f"Erro na geração do sprint: {str(e)}")
            raise
    
    async def execute_task(self, task_id: str, sprint: Optional[Sprint] = None,
                          agent_type: Optional[str] = None) -> TaskResult:
        """
        Executa uma tarefa específica
        
        Args:
            task_id: ID da tarefa
            sprint: Sprint para contexto (opcional)
            agent_type: Tipo de agente específico (opcional)
            
        Returns:
            TaskResult: Resultado da execução
        """
        start_time = time.time()
        self.logger.info(f"⚡ Executando task: {task_id}")
        
        try:
            # Encontrar task
            task = self._find_task(task_id, sprint)
            if not task:
                raise ValueError(f"Task {task_id} não encontrada")
            
            # Determinar agente
            if agent_type:
                task.agent_type = agent_type
            
            # Validar task
            self.validator.validate_task(task)
            
            # Iniciar execução
            task.start_execution()
            
            # Executar com orquestrador
            result = await self.orchestrator.execute_task(task)
            
            # Completar task
            task.complete_execution(result)
            
            # Registrar no histórico
            self._execution_history.append({
                "task_id": task_id,
                "execution_time": result.execution_time,
                "success": result.success,
                "agent_used": result.agent_used,
                "timestamp": datetime.now()
            })
            
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "execute_task",
                execution_time,
                result.success,
                task_id=task_id,
                agent_used=result.agent_used
            )
            
            self.logger.log_task_execution(
                task_id,
                "completed" if result.success else "failed",
                result.execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.log_execution(
                "execute_task",
                execution_time,
                False,
                error=str(e)
            )
            self.logger.error(f"Erro na execução da task {task_id}: {str(e)}")
            raise
    
    async def execute_sprint(self, sprint: Sprint, agent_type: str = "auto") -> List[TaskResult]:
        """
        Executa todas as tarefas de um sprint
        
        Args:
            sprint: Sprint a ser executado
            agent_type: Tipo de agente a usar
            
        Returns:
            List[TaskResult]: Resultados das execuções
        """
        self.logger.info(f"🏃 Executando sprint: {sprint.id}")
        
        # Usar sprint executor para execução completa
        return await self.sprint_executor.execute_sprint(sprint, agent_type)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de execução"""
        if not self._execution_history:
            return {"total_executions": 0, "success_rate": 0, "avg_time": 0}
        
        total = len(self._execution_history)
        successful = len([h for h in self._execution_history if h["success"]])
        avg_time = sum(h["execution_time"] for h in self._execution_history) / total
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": (successful / total) * 100,
            "average_execution_time": avg_time,
            "agent_usage": self._get_agent_usage_stats()
        }
    
    def _get_agent_usage_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de uso de agentes"""
        agent_counts = {}
        for execution in self._execution_history:
            agent = execution.get("agent_used", "unknown")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        return agent_counts
    
    def _select_stories_for_sprint(self, backlog: Backlog, max_points: int,
                                 priority: Optional[str] = None) -> List[UserStory]:
        """Seleciona stories para o sprint"""
        stories = backlog.user_stories
        
        # Filtrar por prioridade se especificado
        if priority:
            # Converter prioridade para número para comparação
            priority_map = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
            min_priority_num = priority_map.get(priority, 2)
            stories = [s for s in stories if priority_map.get(s.priority, 2) <= min_priority_num]
        
        # Ordenar por prioridade (P0 primeiro) e depois por pontos (menor primeiro)
        priority_map = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        stories.sort(key=lambda s: (priority_map.get(s.priority, 2), s.story_points))
        
        # Selecionar até atingir max_points, respeitando dependências
        selected = []
        current_points = 0
        selected_ids = set()
        
        # Primeira passada: adicionar stories que cabem completamente
        for story in stories:
            # Verificar se todas as dependências já estão selecionadas
            dependencies_satisfied = all(dep_id in selected_ids for dep_id in story.dependencies)
            
            if dependencies_satisfied and current_points + story.story_points <= max_points:
                selected.append(story)
                selected_ids.add(story.id)
                current_points += story.story_points
            elif not dependencies_satisfied:
                # Pular stories com dependências não satisfeitas
                continue
            else:
                # Pontos excedidos, mas continuar para ver se há stories menores
                continue
        
        # Segunda passada: tentar adicionar stories menores que ainda cabem
        remaining_stories = [s for s in stories if s.id not in selected_ids]
        for story in remaining_stories:
            dependencies_satisfied = all(dep_id in selected_ids for dep_id in story.dependencies)
            
            if dependencies_satisfied and current_points + story.story_points <= max_points:
                selected.append(story)
                selected_ids.add(story.id)
                current_points += story.story_points
        
        return selected
    
    def _validate_sprint_dependencies(self, stories: List[UserStory]) -> None:
        """Valida dependências entre stories"""
        story_ids = {s.id for s in stories}
        
        for story in stories:
            for dep_id in story.dependencies:
                if dep_id not in story_ids:
                    raise ValueError(f"Dependência {dep_id} não satisfeita para {story.id}")
    
    def _find_task(self, task_id: str, sprint: Optional[Sprint] = None) -> Optional[Task]:
        """Encontra task pelo ID"""
        # Buscar task no sprint se fornecido
        if sprint:
            for story in sprint.user_stories:
                if story.id == task_id:
                    return Task(
                        id=task_id,
                        title=story.title,
                        description=story.description,
                        user_story_id=story.id,
                        agent_type="auto"
                    )
        
        # Buscar em storage se não encontrado no sprint
        # Por enquanto, cria task simulada
        return Task(
            id=task_id,
            title=f"Task {task_id}",
            description=f"Descrição da task {task_id}",
            user_story_id="US-001",
            agent_type="auto"
        ) 