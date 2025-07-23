"""
Task Scheduler - Agent Orchestrator
Scheduler para gerenciar execução de tasks
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..models.task import Task, TaskResult
from ..utils.logger import logger


@dataclass
class SchedulerConfig:
    """Configuração do scheduler"""
    max_concurrent_tasks: int = 5
    retry_attempts: int = 3
    retry_delay: int = 5  # segundos
    timeout_seconds: int = 300


class TaskScheduler:
    """Scheduler para execução de tasks"""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.logger = logger
        self.running_tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[TaskResult] = []
        
    async def schedule_task(self, task: Task) -> str:
        """
        Agenda uma task para execução
        
        Args:
            task: Task a ser agendada
            
        Returns:
            str: ID da execução agendada
        """
        self.logger.info(f"📅 Agendando task: {task.id}")
        
        # Adicionar à fila
        self.task_queue.append(task)
        
        # Se não há tasks rodando, iniciar execução
        if len(self.running_tasks) < self.config.max_concurrent_tasks:
            asyncio.create_task(self._process_queue())
        
        return f"exec-{task.id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    async def schedule_multiple_tasks(self, tasks: List[Task]) -> List[str]:
        """
        Agenda múltiplas tasks
        
        Args:
            tasks: Lista de tasks
            
        Returns:
            List[str]: IDs das execuções agendadas
        """
        execution_ids = []
        
        for task in tasks:
            execution_id = await self.schedule_task(task)
            execution_ids.append(execution_id)
        
        return execution_ids
    
    async def _process_queue(self):
        """Processa a fila de tasks"""
        while self.task_queue and len(self.running_tasks) < self.config.max_concurrent_tasks:
            task = self.task_queue.pop(0)
            
            # Marcar como rodando
            self.running_tasks[task.id] = task
            
            # Executar task
            asyncio.create_task(self._execute_task_with_retry(task))
    
    async def _execute_task_with_retry(self, task: Task):
        """Executa task com retry em caso de falha"""
        attempts = 0
        
        while attempts < self.config.retry_attempts:
            try:
                self.logger.info(f"🔄 Executando task {task.id} (tentativa {attempts + 1})")
                
                # Simular execução da task
                result = await self._execute_single_task(task)
                
                # Se sucesso, sair do loop
                if result.success:
                    self.completed_tasks.append(result)
                    self.logger.success(f"✅ Task {task.id} executada com sucesso")
                    break
                else:
                    self.logger.warning(f"⚠️ Task {task.id} falhou: {result.error}")
                    attempts += 1
                    
                    if attempts < self.config.retry_attempts:
                        await asyncio.sleep(self.config.retry_delay)
                
            except Exception as e:
                self.logger.error(f"❌ Erro na execução da task {task.id}: {str(e)}")
                attempts += 1
                
                if attempts < self.config.retry_attempts:
                    await asyncio.sleep(self.config.retry_delay)
        
        # Remover da lista de tasks rodando
        if task.id in self.running_tasks:
            del self.running_tasks[task.id]
        
        # Processar próxima task na fila
        if self.task_queue:
            asyncio.create_task(self._process_queue())
    
    async def _execute_single_task(self, task: Task) -> TaskResult:
        """Executa uma única task"""
        import time
        start_time = time.time()
        
        try:
            # Simular execução
            await asyncio.sleep(2)  # Simular tempo de processamento
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                success=True,
                message=f"Task {task.id} executada com sucesso",
                data={
                    "files_created": 2,
                    "code_generated": True,
                    "tests_passed": True
                },
                execution_time=execution_time,
                agent_used="claude"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                success=False,
                message=f"Erro na execução da task {task.id}",
                error=str(e),
                execution_time=execution_time,
                agent_used="unknown"
            )
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Retorna status da fila de tasks"""
        return {
            "queue_length": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "max_concurrent": self.config.max_concurrent_tasks
        }
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """Retorna lista de tasks rodando"""
        return [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "started_at": task.started_at
            }
            for task in self.running_tasks.values()
        ]
    
    def get_completed_tasks(self) -> List[TaskResult]:
        """Retorna lista de tasks completadas"""
        return self.completed_tasks.copy()
    
    def clear_queue(self):
        """Limpa a fila de tasks"""
        self.task_queue.clear()
        self.logger.info("🗑️ Fila de tasks limpa")
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancela uma task
        
        Args:
            task_id: ID da task a ser cancelada
            
        Returns:
            bool: True se cancelada com sucesso
        """
        # Remover da fila
        for i, task in enumerate(self.task_queue):
            if task.id == task_id:
                del self.task_queue[i]
                self.logger.info(f"❌ Task {task_id} cancelada da fila")
                return True
        
        # Se está rodando, marcar como cancelada
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel_execution()
            del self.running_tasks[task_id]
            self.logger.info(f"❌ Task {task_id} cancelada durante execução")
            return True
        
        return False 