"""
Orchestrator - Agent Orchestrator
Orquestrador que gerencia a execução de tasks
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..models.task import Task, TaskResult
from ..utils.logger import logger
from ..agents.factory import AgentFactory, AgentType


class Orchestrator:
    """Orquestrador de execução de tasks"""
    
    def __init__(self):
        self.logger = logger
        self.agent_factory = AgentFactory()
        self.execution_history: List[Dict[str, Any]] = []
        self.validator = None  # Será inicializado pelo engine
        
    async def execute_task(self, task: Task) -> TaskResult:
        """
        Executa uma task usando o agente apropriado
        
        Args:
            task: Task a ser executada
            
        Returns:
            TaskResult: Resultado da execução
        """
        start_time = time.time()
        self.logger.info(f"⚡ Executando task: {task.id}")
        
        try:
            # Validar task (se validator estiver disponível)
            if self.validator:
                self.validator.validate_task(task)
            
            # Selecionar agente
            agent_type = self._select_agent(task)
            self.logger.info(f"🤖 Executando task {task.id} com agente {agent_type}")
            
            # Obter agente da factory
            agent = self.agent_factory.get_agent(agent_type)
            
            # Preparar contexto da task
            task_context = self._prepare_task_data(task)
            
            # Executar com agente
            result = await agent.execute_task(task, task_context)
            
            # Registrar execução
            self._record_execution(task, result, agent_type)
            
            execution_time = time.time() - start_time
            self.logger.info(f"✅ Task {task.id}: {'success' if result.success else 'failed'} em {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Erro na execução da task {task.id}: {str(e)}")
            
            return TaskResult(
                success=False,
                message=f"Erro na execução: {str(e)}",
                error=str(e),
                execution_time=execution_time,
                agent_used="unknown"
            )
    
    def _select_agent(self, task: Task) -> str:
        """Seleciona o agente mais apropriado para a task"""
        if task.agent_type != "auto":
            return task.agent_type
        
        # Usar factory para seleção automática
        return self.agent_factory.select_agent_for_task(task)
    
    def _prepare_task_data(self, task: Task) -> Dict[str, Any]:
        """Prepara dados da task para execução"""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "user_story_id": task.user_story_id,
            "priority": task.priority,
            "complexity": task.complexity,
            "acceptance_criteria": self._get_acceptance_criteria(task),
            "context": self._get_task_context(task)
        }
    
    def _get_acceptance_criteria(self, task: Task) -> List[str]:
        """Extrai critérios de aceite da task"""
        # Extrair critérios reais da user story se disponível
        if hasattr(task, 'user_story') and task.user_story:
            return task.user_story.acceptance_criteria
        elif hasattr(task, 'description') and task.description:
            # Tentar extrair critérios da descrição
            lines = task.description.split('\n')
            criteria = []
            for line in lines:
                line = line.strip()
                if line.startswith(('-', '•', '*', '✓', '☐')):
                    criteria.append(line.lstrip('-•*✓☐ '))
                elif 'critério' in line.lower() or 'criteria' in line.lower():
                    criteria.append(line)
            return criteria if criteria else ["Funcionalidade implementada conforme especificação"]
        else:
            return ["Funcionalidade implementada conforme especificação"]
    
    def _get_task_context(self, task: Task) -> Dict[str, Any]:
        """Obtém contexto da task"""
        return {
            "user_story": task.user_story_id,
            "priority": task.priority,
            "complexity": task.complexity,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades dos agentes disponíveis"""
        return self.agent_factory.get_all_capabilities()
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos agentes"""
        return self.agent_factory.get_all_stats()
    
    def _record_execution(self, task: Task, result: TaskResult, agent_type: str):
        """Registra execução no histórico"""
        self.execution_history.append({
            "task_id": task.id,
            "agent_type": agent_type,
            "success": result.success,
            "execution_time": result.execution_time,
            "timestamp": datetime.now()
        })
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de execução"""
        if not self.execution_history:
            return {"total_executions": 0, "success_rate": 0}
        
        total = len(self.execution_history)
        successful = len([h for h in self.execution_history if h["success"]])
        
        agent_stats = {}
        for execution in self.execution_history:
            agent = execution["agent_type"]
            if agent not in agent_stats:
                agent_stats[agent] = {"count": 0, "success": 0}
            agent_stats[agent]["count"] += 1
            if execution["success"]:
                agent_stats[agent]["success"] += 1
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": (successful / total) * 100 if total > 0 else 0,
            "agent_stats": agent_stats
        } 