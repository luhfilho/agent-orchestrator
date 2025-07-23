"""
Testes para Advanced Configuration
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch

from agent_orchestrator.config.advanced_config import (
    ConfigManager, AdvancedConfig, AgentConfig, TemplateConfig,
    IntegrationConfig, LoggingConfig, PerformanceConfig,
    ConfigReloadStrategy, ConfigValidator
)


class TestAdvancedConfig:
    """Testes para configuração avançada"""
    
    def test_agent_config_creation(self):
        """Testa criação de configuração de agentes"""
        config = AgentConfig(
            claude_api_key="sk-test-key",
            claude_model="claude-3.5-sonnet-20241022",
            claude_timeout=300,
            gemini_api_key="AI-test-key",
            gemini_model="gemini-1.5-flash"
        )
        
        assert config.claude_api_key == "sk-test-key"
        assert config.claude_model == "claude-3.5-sonnet-20241022"
        assert config.claude_timeout == 300
        assert config.gemini_api_key == "AI-test-key"
        assert config.gemini_model == "gemini-1.5-flash"
        assert config.auto_fallback is True
        assert config.preferred_agent == "auto"
        assert config.claude_personas == ["dev", "sm", "qa", "pm", "po"]
        assert config.gemini_mcp_servers == []
    
    def test_template_config_creation(self):
        """Testa criação de configuração de templates"""
        config = TemplateConfig(
            templates_dir=Path("./custom_templates"),
            custom_templates={"custom": "template"},
            validation_enabled=True,
            auto_validate=False
        )
        
        assert config.templates_dir == Path("./custom_templates")
        assert config.custom_templates == {"custom": "template"}
        assert config.validation_enabled is True
        assert config.auto_validate is False
    
    def test_integration_config_creation(self):
        """Testa criação de configuração de integrações"""
        config = IntegrationConfig(
            github_token="ghp-test-token",
            jira_url="https://jira.example.com",
            slack_webhook="https://hooks.slack.com/test"
        )
        
        assert config.github_token == "ghp-test-token"
        assert config.jira_url == "https://jira.example.com"
        assert config.slack_webhook == "https://hooks.slack.com/test"
        assert config.jira_username is None
        assert config.jira_password is None
    
    def test_logging_config_creation(self):
        """Testa criação de configuração de logging"""
        config = LoggingConfig(
            log_level="DEBUG",
            log_dir=Path("./custom_logs"),
            max_file_size=20 * 1024 * 1024,
            backup_count=10,
            json_format=False,
            console_output=False
        )
        
        assert config.log_level == "DEBUG"
        assert config.log_dir == Path("./custom_logs")
        assert config.max_file_size == 20 * 1024 * 1024
        assert config.backup_count == 10
        assert config.json_format is False
        assert config.console_output is False
        assert config.file_output is True
        assert config.rotation_enabled is True
    
    def test_performance_config_creation(self):
        """Testa criação de configuração de performance"""
        config = PerformanceConfig(
            max_concurrent_tasks=10,
            task_timeout=600,
            cache_enabled=False,
            cache_ttl=7200,
            retry_attempts=5,
            retry_delay=2.0
        )
        
        assert config.max_concurrent_tasks == 10
        assert config.task_timeout == 600
        assert config.cache_enabled is False
        assert config.cache_ttl == 7200
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0
    
    def test_advanced_config_creation(self):
        """Testa criação de configuração avançada completa"""
        config = AdvancedConfig(
            reload_strategy=ConfigReloadStrategy.AUTO,
            config_file=Path("./test_config.yaml")
        )
        
        assert config.reload_strategy == ConfigReloadStrategy.AUTO
        assert config.config_file == Path("./test_config.yaml")
        assert config.agents is not None
        assert config.templates is not None
        assert config.integrations is not None
        assert config.logging is not None
        assert config.performance is not None


class TestConfigValidator:
    """Testes para validador de configuração"""
    
    def test_validate_config_success(self):
        """Testa validação de configuração válida"""
        config = AdvancedConfig()
        config.agents.claude_api_key = "sk-valid-key"
        config.agents.claude_timeout = 300
        config.agents.gemini_timeout = 120
        config.performance.max_concurrent_tasks = 5
        config.performance.task_timeout = 300
        config.logging.log_level = "INFO"
        
        errors = ConfigValidator.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_config_invalid_claude_key(self):
        """Testa validação com chave Claude inválida"""
        config = AdvancedConfig()
        config.agents.claude_api_key = "invalid-key"
        
        errors = ConfigValidator.validate_config(config)
        assert len(errors) > 0
        assert any("Claude API key deve começar com 'sk-'" in error for error in errors)
    
    def test_validate_config_invalid_gemini_key(self):
        """Testa validação com chave Gemini inválida"""
        config = AdvancedConfig()
        config.agents.gemini_api_key = "invalid-key"
        
        errors = ConfigValidator.validate_config(config)
        assert len(errors) > 0
        assert any("Gemini API key deve começar com 'AI'" in error for error in errors)
    
    def test_validate_config_invalid_timeouts(self):
        """Testa validação com timeouts inválidos"""
        config = AdvancedConfig()
        config.agents.claude_timeout = 10  # Muito baixo
        config.agents.gemini_timeout = 15  # Muito baixo
        
        errors = ConfigValidator.validate_config(config)
        assert len(errors) > 0
        assert any("Claude timeout deve ser pelo menos 30 segundos" in error for error in errors)
        assert any("Gemini timeout deve ser pelo menos 30 segundos" in error for error in errors)
    
    def test_validate_config_invalid_performance(self):
        """Testa validação com configurações de performance inválidas"""
        config = AdvancedConfig()
        config.performance.max_concurrent_tasks = 0  # Inválido
        config.performance.task_timeout = 30  # Muito baixo
        
        errors = ConfigValidator.validate_config(config)
        assert len(errors) > 0
        assert any("max_concurrent_tasks deve ser pelo menos 1" in error for error in errors)
        assert any("task_timeout deve ser pelo menos 60 segundos" in error for error in errors)
    
    def test_validate_config_invalid_log_level(self):
        """Testa validação com nível de log inválido"""
        config = AdvancedConfig()
        config.logging.log_level = "INVALID_LEVEL"
        
        errors = ConfigValidator.validate_config(config)
        assert len(errors) > 0
        assert any("log_level deve ser um dos" in error for error in errors)


class TestConfigManager:
    """Testes para gerenciador de configuração"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Arquivo de configuração temporário"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "agents": {
                    "claude_api_key": "sk-test-key",
                    "claude_model": "claude-3.5-sonnet-20241022",
                    "claude_timeout": 300,
                    "gemini_api_key": "AI-test-key",
                    "gemini_model": "gemini-1.5-flash",
                    "gemini_timeout": 120
                },
                "templates": {
                    "templates_dir": "./test_templates",
                    "validation_enabled": True,
                    "auto_validate": False
                },
                "logging": {
                    "log_level": "DEBUG",
                    "log_dir": "./test_logs"
                },
                "performance": {
                    "max_concurrent_tasks": 10,
                    "task_timeout": 600
                },
                "reload_strategy": "auto"
            }, f)
            return Path(f.name)
    
    def test_config_manager_initialization(self, temp_config_file):
        """Testa inicialização do config manager"""
        manager = ConfigManager(temp_config_file)
        
        assert manager.config_file == temp_config_file
        assert manager.config is not None
        assert isinstance(manager.config, AdvancedConfig)
    
    def test_load_config_from_file(self, temp_config_file):
        """Testa carregamento de configuração de arquivo"""
        manager = ConfigManager(temp_config_file)
        config = manager.get_config()
        
        assert config.agents.claude_api_key == "sk-test-key"
        assert config.agents.claude_model == "claude-3.5-sonnet-20241022"
        assert config.agents.claude_timeout == 300
        assert config.agents.gemini_api_key == "AI-test-key"
        assert config.agents.gemini_model == "gemini-1.5-flash"
        assert config.agents.gemini_timeout == 120
        assert config.templates.templates_dir == Path("./test_templates")
        assert config.templates.validation_enabled is True
        assert config.templates.auto_validate is False
        assert config.logging.log_level == "DEBUG"
        assert config.logging.log_dir == Path("./test_logs")
        assert config.performance.max_concurrent_tasks == 10
        assert config.performance.task_timeout == 600
        assert config.reload_strategy == ConfigReloadStrategy.AUTO
    
    def test_create_default_config(self):
        """Testa criação de configuração padrão"""
        with tempfile.NamedTemporaryFile(suffix='.yaml') as f:
            config_file = Path(f.name)
            config_file.unlink()  # Remover arquivo
        
        manager = ConfigManager(config_file)
        config = manager.get_config()
        
        # Verificar se configuração padrão foi criada
        assert config.agents.claude_api_key is None
        assert config.agents.gemini_api_key is None
        assert config.agents.claude_model == "claude-3.5-sonnet-20241022"
        assert config.agents.gemini_model == "gemini-1.5-flash"
        assert config.reload_strategy == ConfigReloadStrategy.MANUAL
    
    def test_update_config(self, temp_config_file):
        """Testa atualização de configuração"""
        manager = ConfigManager(temp_config_file)
        
        # Atualizar configuração
        updates = {
            "agents.claude_timeout": 600,
            "agents.gemini_timeout": 300,
            "performance.max_concurrent_tasks": 15,
            "logging.log_level": "WARNING"
        }
        
        manager.update_config(updates)
        config = manager.get_config()
        
        assert config.agents.claude_timeout == 600
        assert config.agents.gemini_timeout == 300
        assert config.performance.max_concurrent_tasks == 15
        assert config.logging.log_level == "WARNING"
    
    def test_export_config_yaml(self, temp_config_file):
        """Testa exportação de configuração em YAML"""
        manager = ConfigManager(temp_config_file)
        
        yaml_data = manager.export_config("yaml")
        
        assert isinstance(yaml_data, str)
        assert "agents:" in yaml_data
        assert "templates:" in yaml_data
        assert "logging:" in yaml_data
        assert "performance:" in yaml_data
    
    def test_export_config_json(self, temp_config_file):
        """Testa exportação de configuração em JSON"""
        manager = ConfigManager(temp_config_file)
        
        json_data = manager.export_config("json")
        
        assert isinstance(json_data, str)
        parsed = json.loads(json_data)
        assert "agents" in parsed
        assert "templates" in parsed
        assert "logging" in parsed
        assert "performance" in parsed
    
    def test_import_config_yaml(self, temp_config_file):
        """Testa importação de configuração YAML"""
        manager = ConfigManager(temp_config_file)
        
        new_config_data = """
agents:
  claude_api_key: "sk-new-key"
  claude_model: "claude-3.5-haiku-20240307"
  claude_timeout: 500
templates:
  templates_dir: "./new_templates"
  validation_enabled: false
logging:
  log_level: "ERROR"
performance:
  max_concurrent_tasks: 20
  task_timeout: 900
"""
        
        manager.import_config(new_config_data, "yaml")
        config = manager.get_config()
        
        assert config.agents.claude_api_key == "sk-new-key"
        assert config.agents.claude_model == "claude-3.5-haiku-20240307"
        assert config.agents.claude_timeout == 500
        assert config.templates.templates_dir == Path("./new_templates")
        assert config.templates.validation_enabled is False
        assert config.logging.log_level == "ERROR"
        assert config.performance.max_concurrent_tasks == 20
        assert config.performance.task_timeout == 900
    
    def test_import_config_json(self, temp_config_file):
        """Testa importação de configuração JSON"""
        manager = ConfigManager(temp_config_file)
        
        new_config_data = json.dumps({
            "agents": {
                "claude_api_key": "sk-json-key",
                "claude_timeout": 400
            },
            "templates": {
                "templates_dir": "./json_templates"
            },
            "logging": {
                "log_level": "CRITICAL"
            }
        })
        
        manager.import_config(new_config_data, "json")
        config = manager.get_config()
        
        assert config.agents.claude_api_key == "sk-json-key"
        assert config.agents.claude_timeout == 400
        assert config.templates.templates_dir == Path("./json_templates")
        assert config.logging.log_level == "CRITICAL"
    
    def test_validate_config(self, temp_config_file):
        """Testa validação de configuração"""
        manager = ConfigManager(temp_config_file)
        
        errors = manager.validate_config()
        assert isinstance(errors, list)
        # Configuração válida não deve ter erros
        assert len(errors) == 0
    
    def test_get_config_summary(self, temp_config_file):
        """Testa obtenção de resumo da configuração"""
        manager = ConfigManager(temp_config_file)
        
        summary = manager.get_config_summary()
        
        assert "config_file" in summary
        assert "reload_strategy" in summary
        assert "agents_configured" in summary
        assert "integrations_configured" in summary
        assert "performance" in summary
        assert "logging" in summary
        
        assert summary["agents_configured"]["claude"] is True
        assert summary["agents_configured"]["gemini"] is True
        assert summary["performance"]["max_concurrent_tasks"] == 10
        assert summary["logging"]["level"] == "DEBUG"
    
    def test_reload_config(self, temp_config_file):
        """Testa recarregamento de configuração"""
        manager = ConfigManager(temp_config_file)
        
        # Modificar arquivo de configuração
        with open(temp_config_file, 'w') as f:
            yaml.dump({
                "agents": {
                    "claude_api_key": "sk-reloaded-key",
                    "claude_timeout": 800
                },
                "logging": {
                    "log_level": "INFO"
                }
            }, f)
        
        # Recarregar configuração
        manager.reload_config()
        config = manager.get_config()
        
        assert config.agents.claude_api_key == "sk-reloaded-key"
        assert config.agents.claude_timeout == 800
        assert config.logging.log_level == "INFO"


if __name__ == "__main__":
    pytest.main([__file__]) 