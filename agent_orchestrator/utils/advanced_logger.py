"""
Advanced Logger - Agent Orchestrator
Sistema de logs detalhados com rotação e níveis configuráveis
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .logger import logger as base_logger


class LogLevel(Enum):
    """Níveis de log disponíveis"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogConfig:
    """Configuração do sistema de logs"""
    log_dir: Path = Path("./logs")
    log_level: LogLevel = LogLevel.INFO
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = True
    console_output: bool = True
    file_output: bool = True
    rotation_enabled: bool = True


class AdvancedLogger:
    """Sistema de logs avançado com rotação e níveis configuráveis"""
    
    def __init__(self, config: Optional[LogConfig] = None):
        self.config = config or LogConfig()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        # Criar diretório de logs
        self.config.log_dir.mkdir(exist_ok=True)
        
        # Configurar logger raiz
        self._setup_root_logger()
        
        # Configurar loggers específicos
        self._setup_agent_logger()
        self._setup_execution_logger()
        self._setup_performance_logger()
    
    def _setup_root_logger(self):
        """Configura o logger raiz"""
        root_logger = logging.getLogger("agent_orchestrator")
        root_logger.setLevel(self.config.log_level.value)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Adicionar handlers baseados na configuração
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self._get_formatter())
            root_logger.addHandler(console_handler)
        
        if self.config.file_output:
            file_handler = self._get_file_handler("agent_orchestrator.log")
            root_logger.addHandler(file_handler)
    
    def _setup_agent_logger(self):
        """Configura logger para agentes"""
        agent_logger = logging.getLogger("agent_orchestrator.agents")
        agent_logger.setLevel(self.config.log_level.value)
        
        if self.config.file_output:
            file_handler = self._get_file_handler("agents.log")
            agent_logger.addHandler(file_handler)
        
        self.loggers["agents"] = agent_logger
    
    def _setup_execution_logger(self):
        """Configura logger para execução de tasks"""
        execution_logger = logging.getLogger("agent_orchestrator.execution")
        execution_logger.setLevel(self.config.log_level.value)
        
        if self.config.file_output:
            file_handler = self._get_file_handler("execution.log")
            execution_logger.addHandler(file_handler)
        
        self.loggers["execution"] = execution_logger
    
    def _setup_performance_logger(self):
        """Configura logger para métricas de performance"""
        performance_logger = logging.getLogger("agent_orchestrator.performance")
        performance_logger.setLevel(self.config.log_level.value)
        
        if self.config.file_output:
            file_handler = self._get_file_handler("performance.log")
            performance_logger.addHandler(file_handler)
        
        self.loggers["performance"] = performance_logger
    
    def _get_formatter(self) -> logging.Formatter:
        """Retorna o formatter configurado"""
        return logging.Formatter(self.config.log_format)
    
    def _get_file_handler(self, filename: str) -> logging.Handler:
        """Cria handler de arquivo com rotação"""
        log_file = self.config.log_dir / filename
        
        if self.config.rotation_enabled:
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
        else:
            handler = logging.FileHandler(log_file)
        
        handler.setFormatter(self._get_formatter())
        return handler
    
    def log_structured(self, logger_name: str, level: LogLevel, message: str, 
                      data: Optional[Dict[str, Any]] = None, 
                      context: Optional[Dict[str, Any]] = None):
        """
        Registra log estruturado em JSON
        
        Args:
            logger_name: Nome do logger
            level: Nível do log
            message: Mensagem principal
            data: Dados adicionais
            context: Contexto da execução
        """
        logger = self.loggers.get(logger_name, logging.getLogger(logger_name))
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "logger": logger_name
        }
        
        if data:
            log_entry["data"] = data
        
        if context:
            log_entry["context"] = context
        
        if self.config.json_format:
            log_message = json.dumps(log_entry, ensure_ascii=False)
        else:
            log_message = f"{log_entry['timestamp']} - {level.value} - {message}"
        
        logger.log(getattr(logging, level.value), log_message)
    
    def log_agent_execution(self, agent_type: str, task_id: str, 
                           execution_time: float, success: bool,
                           data: Optional[Dict[str, Any]] = None):
        """Registra execução de agente"""
        self.log_structured(
            "agents",
            LogLevel.INFO,
            f"Agent execution completed",
            data={
                "agent_type": agent_type,
                "task_id": task_id,
                "execution_time": execution_time,
                "success": success,
                **(data or {})
            },
            context={
                "component": "agent_execution",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_task_execution(self, task_id: str, agent_type: str,
                          execution_time: float, success: bool,
                          error: Optional[str] = None):
        """Registra execução de task"""
        self.log_structured(
            "execution",
            LogLevel.INFO,
            f"Task execution completed",
            data={
                "task_id": task_id,
                "agent_type": agent_type,
                "execution_time": execution_time,
                "success": success,
                "error": error
            },
            context={
                "component": "task_execution",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float,
                              unit: str = "seconds", context: Optional[Dict[str, Any]] = None):
        """Registra métrica de performance"""
        self.log_structured(
            "performance",
            LogLevel.INFO,
            f"Performance metric recorded",
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit
            },
            context=context or {}
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Registra erro com stack trace"""
        import traceback
        
        self.log_structured(
            "execution",
            LogLevel.ERROR,
            f"Error occurred: {str(error)}",
            data={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc()
            },
            context=context or {}
        )
    
    def log_sprint_progress(self, sprint_id: str, completed_tasks: int, 
                           total_tasks: int, progress_percentage: float):
        """Registra progresso do sprint"""
        self.log_structured(
            "execution",
            LogLevel.INFO,
            f"Sprint progress updated",
            data={
                "sprint_id": sprint_id,
                "completed_tasks": completed_tasks,
                "total_tasks": total_tasks,
                "progress_percentage": progress_percentage
            },
            context={
                "component": "sprint_progress",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_log_files(self) -> List[Path]:
        """Retorna lista de arquivos de log"""
        log_files = []
        for file in self.config.log_dir.glob("*.log*"):
            log_files.append(file)
        return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos logs"""
        log_files = self.get_log_files()
        total_size = sum(f.stat().st_size for f in log_files)
        
        return {
            "total_files": len(log_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "oldest_file": min(log_files, key=lambda x: x.stat().st_mtime).name if log_files else None,
            "newest_file": max(log_files, key=lambda x: x.stat().st_mtime).name if log_files else None
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove logs antigos"""
        import time
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        removed_count = 0
        for log_file in self.get_log_files():
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                removed_count += 1
        
        if removed_count > 0:
            self.log_structured(
                "execution",
                LogLevel.INFO,
                f"Cleaned up {removed_count} old log files"
            )
        
        return removed_count


# Instância global do logger avançado
advanced_logger = AdvancedLogger() 