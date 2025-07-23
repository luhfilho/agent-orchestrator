"""
Advanced Configuration - Agent Orchestrator
Sistema de configuração avançada com YAML e hot reload
"""

import yaml
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..utils.advanced_logger import advanced_logger, LogLevel


class ConfigReloadStrategy(Enum):
    """Estratégias de reload de configuração"""
    MANUAL = "manual"
    AUTO = "auto"
    WATCH = "watch"


@dataclass
class AgentConfig:
    """Configuração de agentes"""
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3.5-sonnet-20241022"
    claude_timeout: int = 300
    claude_max_retries: int = 3
    claude_personas: List[str] = None
    
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_timeout: int = 120
    gemini_max_retries: int = 2
    gemini_mcp_servers: List[str] = None
    
    auto_fallback: bool = True
    preferred_agent: str = "auto"
    
    def __post_init__(self):
        if self.claude_personas is None:
            self.claude_personas = ["dev", "sm", "qa", "pm", "po"]
        if self.gemini_mcp_servers is None:
            self.gemini_mcp_servers = []


@dataclass
class TemplateConfig:
    """Configuração de templates"""
    templates_dir: Path = Path("./templates")
    custom_templates: Dict[str, str] = None
    validation_enabled: bool = True
    auto_validate: bool = True
    
    def __post_init__(self):
        if self.custom_templates is None:
            self.custom_templates = {}


@dataclass
class IntegrationConfig:
    """Configuração de integrações"""
    github_token: Optional[str] = None
    jira_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_password: Optional[str] = None
    slack_webhook: Optional[str] = None
    email_smtp: Optional[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None


@dataclass
class LoggingConfig:
    """Configuração de logging"""
    log_level: str = "INFO"
    log_dir: Path = Path("./logs")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    json_format: bool = True
    console_output: bool = True
    file_output: bool = True
    rotation_enabled: bool = True


@dataclass
class PerformanceConfig:
    """Configuração de performance"""
    max_concurrent_tasks: int = 5
    task_timeout: int = 300
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hora
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class AdvancedConfig:
    """Configuração avançada completa"""
    agents: AgentConfig = None
    templates: TemplateConfig = None
    integrations: IntegrationConfig = None
    logging: LoggingConfig = None
    performance: PerformanceConfig = None
    reload_strategy: ConfigReloadStrategy = ConfigReloadStrategy.MANUAL
    config_file: Path = Path("./config.yaml")
    
    def __post_init__(self):
        if self.agents is None:
            self.agents = AgentConfig()
        if self.templates is None:
            self.templates = TemplateConfig()
        if self.integrations is None:
            self.integrations = IntegrationConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.performance is None:
            self.performance = PerformanceConfig()


class ConfigValidator:
    """Validador de configuração"""
    
    @staticmethod
    def validate_config(config: AdvancedConfig) -> List[str]:
        """Valida configuração e retorna erros"""
        errors = []
        
        # Validar configuração de agentes
        if config.agents.claude_api_key and not config.agents.claude_api_key.startswith("sk-"):
            errors.append("Claude API key deve começar com 'sk-'")
        
        if config.agents.gemini_api_key and not config.agents.gemini_api_key.startswith("AI"):
            errors.append("Gemini API key deve começar com 'AI'")
        
        # Validar timeouts
        if config.agents.claude_timeout < 30:
            errors.append("Claude timeout deve ser pelo menos 30 segundos")
        
        if config.agents.gemini_timeout < 30:
            errors.append("Gemini timeout deve ser pelo menos 30 segundos")
        
        # Validar performance
        if config.performance.max_concurrent_tasks < 1:
            errors.append("max_concurrent_tasks deve ser pelo menos 1")
        
        if config.performance.task_timeout < 60:
            errors.append("task_timeout deve ser pelo menos 60 segundos")
        
        # Validar logging
        if config.logging.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("log_level deve ser um dos: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        return errors


class ConfigManager:
    """Gerenciador de configuração avançada"""
    
    def __init__(self, config_file: Path = Path("./config.yaml")):
        self.config_file = config_file
        self.logger = advanced_logger
        self.config: Optional[AdvancedConfig] = None
        self.observer: Optional[Observer] = None
        self._load_config()
    
    def _load_config(self):
        """Carrega configuração do arquivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.config = self._dict_to_config(data)
            else:
                # Criar configuração padrão
                self.config = AdvancedConfig()
                self._save_config()
            
            # Validar configuração
            errors = ConfigValidator.validate_config(self.config)
            if errors:
                self.logger.log_structured(
                    "config",
                    LogLevel.WARNING,
                    f"Configuração com {len(errors)} erros",
                    data={"errors": errors}
                )
                for error in errors:
                    self.logger.log_structured(
                        "config",
                        LogLevel.ERROR,
                        f"Erro de configuração: {error}"
                    )
            else:
                self.logger.log_structured(
                    "config",
                    LogLevel.INFO,
                    "Configuração carregada com sucesso",
                    data={"config_file": str(self.config_file)}
                )
                
        except Exception as e:
            self.logger.log_error(e, {
                "component": "config_loading",
                "config_file": str(self.config_file)
            })
            # Usar configuração padrão em caso de erro
            self.config = AdvancedConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AdvancedConfig:
        """Converte dicionário para configuração"""
        config = AdvancedConfig()
        
        if "agents" in data:
            agents_data = data["agents"]
            config.agents = AgentConfig(
                claude_api_key=agents_data.get("claude_api_key"),
                claude_model=agents_data.get("claude_model", "claude-3.5-sonnet-20241022"),
                claude_timeout=agents_data.get("claude_timeout", 300),
                claude_max_retries=agents_data.get("claude_max_retries", 3),
                claude_personas=agents_data.get("claude_personas", ["dev", "sm", "qa", "pm", "po"]),
                gemini_api_key=agents_data.get("gemini_api_key"),
                gemini_model=agents_data.get("gemini_model", "gemini-1.5-flash"),
                gemini_timeout=agents_data.get("gemini_timeout", 120),
                gemini_max_retries=agents_data.get("gemini_max_retries", 2),
                gemini_mcp_servers=agents_data.get("gemini_mcp_servers", []),
                auto_fallback=agents_data.get("auto_fallback", True),
                preferred_agent=agents_data.get("preferred_agent", "auto")
            )
        
        if "templates" in data:
            templates_data = data["templates"]
            config.templates = TemplateConfig(
                templates_dir=Path(templates_data.get("templates_dir", "./templates")),
                custom_templates=templates_data.get("custom_templates", {}),
                validation_enabled=templates_data.get("validation_enabled", True),
                auto_validate=templates_data.get("auto_validate", True)
            )
        
        if "integrations" in data:
            integrations_data = data["integrations"]
            config.integrations = IntegrationConfig(
                github_token=integrations_data.get("github_token"),
                jira_url=integrations_data.get("jira_url"),
                jira_username=integrations_data.get("jira_username"),
                jira_password=integrations_data.get("jira_password"),
                slack_webhook=integrations_data.get("slack_webhook"),
                email_smtp=integrations_data.get("email_smtp"),
                email_username=integrations_data.get("email_username"),
                email_password=integrations_data.get("email_password")
            )
        
        if "logging" in data:
            logging_data = data["logging"]
            config.logging = LoggingConfig(
                log_level=logging_data.get("log_level", "INFO"),
                log_dir=Path(logging_data.get("log_dir", "./logs")),
                max_file_size=logging_data.get("max_file_size", 10 * 1024 * 1024),
                backup_count=logging_data.get("backup_count", 5),
                json_format=logging_data.get("json_format", True),
                console_output=logging_data.get("console_output", True),
                file_output=logging_data.get("file_output", True),
                rotation_enabled=logging_data.get("rotation_enabled", True)
            )
        
        if "performance" in data:
            performance_data = data["performance"]
            config.performance = PerformanceConfig(
                max_concurrent_tasks=performance_data.get("max_concurrent_tasks", 5),
                task_timeout=performance_data.get("task_timeout", 300),
                cache_enabled=performance_data.get("cache_enabled", True),
                cache_ttl=performance_data.get("cache_ttl", 3600),
                retry_attempts=performance_data.get("retry_attempts", 3),
                retry_delay=performance_data.get("retry_delay", 1.0)
            )
        
        if "reload_strategy" in data:
            config.reload_strategy = ConfigReloadStrategy(data["reload_strategy"])
        
        return config
    
    def _config_to_dict(self, config: AdvancedConfig) -> Dict[str, Any]:
        """Converte configuração para dicionário"""
        return {
            "agents": asdict(config.agents),
            "templates": {
                "templates_dir": str(config.templates.templates_dir),
                "custom_templates": config.templates.custom_templates,
                "validation_enabled": config.templates.validation_enabled,
                "auto_validate": config.templates.auto_validate
            },
            "integrations": asdict(config.integrations),
            "logging": {
                "log_level": config.logging.log_level,
                "log_dir": str(config.logging.log_dir),
                "max_file_size": config.logging.max_file_size,
                "backup_count": config.logging.backup_count,
                "json_format": config.logging.json_format,
                "console_output": config.logging.console_output,
                "file_output": config.logging.file_output,
                "rotation_enabled": config.logging.rotation_enabled
            },
            "performance": asdict(config.performance),
            "reload_strategy": config.reload_strategy.value
        }
    
    def _save_config(self):
        """Salva configuração no arquivo"""
        try:
            # Criar diretório se não existir
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_to_dict(self.config), f, default_flow_style=False, indent=2)
            
            self.logger.log_structured(
                "config",
                LogLevel.INFO,
                "Configuração salva com sucesso",
                data={"config_file": str(self.config_file)}
            )
            
        except Exception as e:
            self.logger.log_error(e, {
                "component": "config_saving",
                "config_file": str(self.config_file)
            })
    
    def get_config(self) -> AdvancedConfig:
        """Retorna configuração atual"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Atualiza configuração"""
        try:
            # Aplicar atualizações
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                elif hasattr(self.config.agents, key):
                    setattr(self.config.agents, key, value)
                elif hasattr(self.config.templates, key):
                    setattr(self.config.templates, key, value)
                elif hasattr(self.config.integrations, key):
                    setattr(self.config.integrations, key, value)
                elif hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)
                elif hasattr(self.config.performance, key):
                    setattr(self.config.performance, key, value)
            
            # Validar configuração atualizada
            errors = ConfigValidator.validate_config(self.config)
            if errors:
                raise ValueError(f"Configuração inválida: {errors}")
            
            # Salvar configuração
            self._save_config()
            
            self.logger.log_structured(
                "config",
                LogLevel.INFO,
                "Configuração atualizada com sucesso",
                data={"updates": updates}
            )
            
        except Exception as e:
            self.logger.log_error(e, {
                "component": "config_update",
                "updates": updates
            })
            raise
    
    def reload_config(self):
        """Recarrega configuração do arquivo"""
        self.logger.log_structured(
            "config",
            LogLevel.INFO,
            "Recarregando configuração"
        )
        self._load_config()
    
    def start_watch_mode(self):
        """Inicia modo de observação de arquivo"""
        if self.config.reload_strategy == ConfigReloadStrategy.WATCH:
            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, manager):
                    self.manager = manager
                
                def on_modified(self, event):
                    if event.src_path == str(self.manager.config_file):
                        self.manager.logger.log_structured(
                            "config",
                            LogLevel.INFO,
                            "Arquivo de configuração modificado, recarregando..."
                        )
                        self.manager.reload_config()
            
            self.observer = Observer()
            self.observer.schedule(ConfigFileHandler(self), str(self.config_file.parent), recursive=False)
            self.observer.start()
            
            self.logger.log_structured(
                "config",
                LogLevel.INFO,
                "Modo de observação iniciado",
                data={"config_file": str(self.config_file)}
            )
    
    def stop_watch_mode(self):
        """Para modo de observação"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
            self.logger.log_structured(
                "config",
                LogLevel.INFO,
                "Modo de observação parado"
            )
    
    def export_config(self, format: str = "yaml") -> str:
        """Exporta configuração em diferentes formatos"""
        config_dict = self._config_to_dict(self.config)
        
        if format == "yaml":
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        elif format == "json":
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def import_config(self, config_data: str, format: str = "yaml"):
        """Importa configuração de string"""
        try:
            if format == "yaml":
                data = yaml.safe_load(config_data)
            elif format == "json":
                data = json.loads(config_data)
            else:
                raise ValueError(f"Formato não suportado: {format}")
            
            self.config = self._dict_to_config(data)
            self._save_config()
            
            self.logger.log_structured(
                "config",
                LogLevel.INFO,
                "Configuração importada com sucesso",
                data={"format": format}
            )
            
        except Exception as e:
            self.logger.log_error(e, {
                "component": "config_import",
                "format": format
            })
            raise
    
    def validate_config(self) -> List[str]:
        """Valida configuração atual"""
        return ConfigValidator.validate_config(self.config)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Retorna resumo da configuração"""
        return {
            "config_file": str(self.config_file),
            "reload_strategy": self.config.reload_strategy.value,
            "agents_configured": {
                "claude": bool(self.config.agents.claude_api_key),
                "gemini": bool(self.config.agents.gemini_api_key)
            },
            "integrations_configured": {
                "github": bool(self.config.integrations.github_token),
                "jira": bool(self.config.integrations.jira_url),
                "slack": bool(self.config.integrations.slack_webhook),
                "email": bool(self.config.integrations.email_smtp)
            },
            "performance": {
                "max_concurrent_tasks": self.config.performance.max_concurrent_tasks,
                "task_timeout": self.config.performance.task_timeout,
                "cache_enabled": self.config.performance.cache_enabled
            },
            "logging": {
                "level": self.config.logging.log_level,
                "json_format": self.config.logging.json_format,
                "rotation_enabled": self.config.logging.rotation_enabled
            }
        } 