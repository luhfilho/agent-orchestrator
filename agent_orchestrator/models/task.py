"""
Task Models - Agent Orchestrator
Modelos de dados para tasks e resultados
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import re


class TaskResult(BaseModel):
    """Modelo para resultado de execução de task"""
    
    success: bool = Field(..., description="Se a execução foi bem-sucedida")
    message: str = Field(..., description="Mensagem de resultado")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados de resultado")
    error: Optional[str] = Field(None, description="Erro se houver")
    execution_time: Optional[float] = Field(None, description="Tempo de execução em segundos")
    agent_used: Optional[str] = Field(None, description="Agente utilizado")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")


class Task(BaseModel):
    """Modelo para Task"""
    
    id: str = Field(..., description="ID único da task")
    title: str = Field(..., description="Título da task")
    description: str = Field(..., description="Descrição da task")
    user_story_id: str = Field(..., description="ID da user story relacionada")
    agent_type: str = Field(..., description="Tipo de agente (claude, gemini)")
    status: str = Field("pending", description="Status da task")
    result: Optional[TaskResult] = Field(None, description="Resultado da execução")
    error: Optional[str] = Field(None, description="Erro se houver")
    started_at: Optional[datetime] = Field(None, description="Data de início")
    completed_at: Optional[datetime] = Field(None, description="Data de conclusão")
    execution_time: Optional[float] = Field(None, description="Tempo de execução em segundos")
    priority: str = Field("medium", description="Prioridade da task")
    complexity: str = Field("medium", description="Complexidade da task")
    
    @validator('id')
    def validate_id(cls, v):
        """Valida formato do ID"""
        # Se v for um objeto Task, extrair o ID
        if hasattr(v, 'id'):
            v = v.id
        
        # Validar se é uma string
        if not isinstance(v, str):
            raise ValueError('ID deve ser uma string')
        
        # Validar formato (mais flexível)
        if not re.match(r'^[A-Z]+-\d+$', v):
            raise ValueError('ID deve seguir o padrão XXX-XXX (ex: TASK-001, US-001)')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Valida status"""
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'Status deve ser um de: {valid_statuses}')
        return v
    
    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Valida tipo de agente"""
        valid_agents = ['claude', 'gemini', 'auto']
        if v not in valid_agents:
            raise ValueError(f'Tipo de agente deve ser um de: {valid_agents}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Valida prioridade"""
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if v not in valid_priorities:
            raise ValueError(f'Prioridade deve ser uma de: {valid_priorities}')
        return v
    
    @validator('complexity')
    def validate_complexity(cls, v):
        """Valida complexidade"""
        valid_complexities = ['low', 'medium', 'high']
        if v not in valid_complexities:
            raise ValueError(f'Complexidade deve ser uma de: {valid_complexities}')
        return v
    
    def start_execution(self) -> None:
        """Marca início da execução"""
        self.status = "running"
        self.started_at = datetime.now()
    
    def complete_execution(self, result: TaskResult) -> None:
        """Marca conclusão da execução"""
        self.status = "completed" if result.success else "failed"
        self.result = result
        self.completed_at = datetime.now()
        self.execution_time = result.execution_time
        if not result.success:
            self.error = result.error
    
    def fail_execution(self, error: str) -> None:
        """Marca falha na execução"""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now()
    
    def cancel_execution(self) -> None:
        """Cancela execução"""
        self.status = "cancelled"
        self.completed_at = datetime.now()
    
    def is_completed(self) -> bool:
        """Verifica se está completa"""
        return self.status in ['completed', 'failed', 'cancelled']
    
    def is_running(self) -> bool:
        """Verifica se está executando"""
        return self.status == "running"
    
    def is_pending(self) -> bool:
        """Verifica se está pendente"""
        return self.status == "pending"
    
    def get_execution_time(self) -> Optional[float]:
        """Retorna tempo de execução"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return self.execution_time 