"""
Testes para Integrações Externas - Agent Orchestrator
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from agent_orchestrator.integrations.integration_manager import IntegrationManager, IntegrationStatus
from agent_orchestrator.integrations.github_integration import GitHubIntegration, GitHubIssue
from agent_orchestrator.integrations.jira_integration import JiraIntegration, JiraIssue
from agent_orchestrator.integrations.slack_integration import SlackIntegration


class TestIntegrationManager:
    """Testes para o gerenciador de integrações"""
    
    def test_init(self):
        """Testa inicialização do gerenciador"""
        manager = IntegrationManager()
        assert manager.integrations == {}
        assert manager.status == {}
    
    def test_register_github(self):
        """Testa registro de integração GitHub"""
        manager = IntegrationManager()
        
        with patch('agent_orchestrator.integrations.github_integration.GitHubIntegration') as mock_github:
            mock_github.return_value = Mock()
            
            result = manager.register_github("token", "owner", "repo")
            
            assert result is True
            assert "github" in manager.integrations
            assert "github" in manager.status
            assert manager.status["github"].name == "GitHub"
            assert manager.status["github"].enabled is True
    
    def test_register_jira(self):
        """Testa registro de integração Jira"""
        manager = IntegrationManager()
        
        with patch('agent_orchestrator.integrations.jira_integration.JiraIntegration') as mock_jira:
            mock_jira.return_value = Mock()
            
            result = manager.register_jira("url", "user", "pass", "PROJ")
            
            assert result is True
            assert "jira" in manager.integrations
            assert "jira" in manager.status
            assert manager.status["jira"].name == "Jira"
            assert manager.status["jira"].enabled is True
    
    def test_register_slack(self):
        """Testa registro de integração Slack"""
        manager = IntegrationManager()
        
        with patch('agent_orchestrator.integrations.slack_integration.SlackIntegration') as mock_slack:
            mock_slack.return_value = Mock()
            
            result = manager.register_slack("webhook", "#channel")
            
            assert result is True
            assert "slack" in manager.integrations
            assert "slack" in manager.status
            assert manager.status["slack"].name == "Slack"
            assert manager.status["slack"].enabled is True
    
    @pytest.mark.asyncio
    async def test_test_all_connections(self):
        """Testa teste de todas as conexões"""
        manager = IntegrationManager()
        
        # Mock das integrações
        mock_github = Mock()
        mock_github.test_connection = AsyncMock(return_value=True)
        
        mock_jira = Mock()
        mock_jira.test_connection = AsyncMock(return_value=False)
        
        manager.integrations = {
            "github": mock_github,
            "jira": mock_jira
        }
        
        manager.status = {
            "github": IntegrationStatus("GitHub", True, False, datetime.now(), 0),
            "jira": IntegrationStatus("Jira", True, False, datetime.now(), 0)
        }
        
        results = await manager.test_all_connections()
        
        assert results["github"] is True
        assert results["jira"] is False
        assert manager.status["github"].connected is True
        assert manager.status["jira"].connected is False
    
    @pytest.mark.asyncio
    async def test_notify_task_completion_success(self):
        """Testa notificação de conclusão de task com sucesso"""
        manager = IntegrationManager()
        
        # Mock do Slack
        mock_slack = Mock()
        mock_slack.send_task_completion = AsyncMock(return_value=True)
        
        manager.integrations["slack"] = mock_slack
        manager.status["slack"] = IntegrationStatus("Slack", True, True, datetime.now(), 0)
        
        result = await manager.notify_task_completion("TASK-001", "Test Task", "success", 10.5)
        
        assert result is True
        mock_slack.send_task_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_task_completion_failure_with_github(self):
        """Testa notificação de falha de task com GitHub"""
        manager = IntegrationManager()
        
        # Mock do GitHub
        mock_github = Mock()
        mock_github.create_issue = AsyncMock(return_value=Mock())
        
        manager.integrations["github"] = mock_github
        manager.status["github"] = IntegrationStatus("GitHub", True, True, datetime.now(), 0)
        
        result = await manager.notify_task_completion("TASK-001", "Test Task", "failed", 10.5)
        
        assert result is True
        mock_github.create_issue.assert_called_once()
    
    def test_get_integration_status(self):
        """Testa obtenção de status das integrações"""
        manager = IntegrationManager()
        
        status = IntegrationStatus("Test", True, True, datetime.now(), 0)
        manager.status["test"] = status
        
        result = manager.get_integration_status()
        
        assert "test" in result
        assert result["test"] == status
    
    def test_is_integration_available(self):
        """Testa verificação de disponibilidade de integração"""
        manager = IntegrationManager()
        
        # Integração não registrada
        assert manager.is_integration_available("nonexistent") is False
        
        # Integração registrada mas não conectada
        manager.status["test"] = IntegrationStatus("Test", True, False, datetime.now(), 0)
        assert manager.is_integration_available("test") is False
        
        # Integração registrada e conectada
        manager.status["test"].connected = True
        # Também precisa estar no dicionário de integrações
        manager.integrations["test"] = Mock()
        assert manager.is_integration_available("test") is True
        
        # Integração desabilitada
        manager.status["test"].enabled = False
        assert manager.is_integration_available("test") is False


class TestGitHubIntegration:
    """Testes para integração GitHub"""
    
    def test_init(self):
        """Testa inicialização da integração GitHub"""
        integration = GitHubIntegration("token", "owner", "repo")
        
        assert integration.token == "token"
        assert integration.owner == "owner"
        assert integration.repo == "repo"
        assert "Authorization" in integration.headers


class TestJiraIntegration:
    """Testes para integração Jira"""
    
    def test_init(self):
        """Testa inicialização da integração Jira"""
        integration = JiraIntegration("url", "user", "pass", "PROJ")
        
        assert integration.url == "url"
        assert integration.username == "user"
        assert integration.password == "pass"
        assert integration.project_key == "PROJ"


class TestSlackIntegration:
    """Testes para integração Slack"""
    
    def test_init(self):
        """Testa inicialização da integração Slack"""
        integration = SlackIntegration("webhook", "#channel")
        
        assert integration.webhook_url == "webhook"
        assert integration.default_channel == "#channel"
    
    @pytest.mark.asyncio
    async def test_send_task_completion(self):
        """Testa envio de notificação de conclusão de task"""
        integration = SlackIntegration("webhook", "#channel")
        
        with patch.object(integration, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await integration.send_task_completion("TASK-001", "Test Task", "success", 10.5)
            
            assert result is True
            mock_send.assert_called_once()
    
    def test_create_rich_table(self):
        """Testa criação de tabela rica"""
        integration = SlackIntegration("webhook", "#channel")
        
        data = [
            {"Name": "John", "Age": 30},
            {"Name": "Jane", "Age": 25}
        ]
        
        table = integration.create_rich_table("Test Table", data)
        
        assert "Test Table" in table
        assert "Name" in table
        assert "Age" in table
        assert "John" in table
        assert "Jane" in table 