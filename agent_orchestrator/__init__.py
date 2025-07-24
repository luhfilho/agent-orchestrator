"""
Agent Orchestrator
Orquestrador de Agentes de IA para Desenvolvimento de Software
"""

__version__ = "2.0.0"
__author__ = "Agent Orchestrator Team"
__email__ = "team@agent-orchestrator.dev"

from .core.engine import OrchestratorEngine, EngineConfig
from .core.orchestrator import Orchestrator
from .core.scheduler import TaskScheduler, SchedulerConfig
from .core.validator import TaskValidator
from .models.backlog import Backlog, UserStory
from .models.sprint import Sprint
from .models.task import Task, TaskResult
from .utils.logger import logger

__all__ = [
    "OrchestratorEngine",
    "EngineConfig",
    "Orchestrator",
    "TaskScheduler",
    "SchedulerConfig", 
    "TaskValidator",
    "Backlog",
    "UserStory",
    "Sprint",
    "Task",
    "TaskResult",
    "logger",
] 